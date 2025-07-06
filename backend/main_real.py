"""
MedExtract UI - Real Backend with Ollama
Backend that actually calls Ollama for extraction
"""

import asyncio
import io
import json
import time
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import uuid
import tempfile
import os

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Import the unified extractor
from core.unified_extractor import UnifiedExtractor


# Request/Response models
class DatapointConfig(BaseModel):
    name: str
    instruction: str
    query: Optional[str] = None
    default_value: Optional[str] = "NR"
    valid_values: Optional[List[str]] = None
    few_shots: Optional[List[Dict[str, str]]] = None


class ExtractionRequest(BaseModel):
    text_column: str = "Report Text"
    ground_truth_column: Optional[str] = None
    datapoint_configs: List[DatapointConfig]
    llm_model: str = "phi4:latest"
    use_rag: bool = False
    temperature: float = 0.1
    top_k: int = 40
    top_p: float = 0.9
    num_ctx: Optional[int] = 4096
    extraction_strategy: str = "single_call"
    chunk_size: int = 800
    chunk_overlap: int = 150
    retriever_type: str = "hybrid"
    reranker_top_n: Optional[int] = 3
    use_few_shots: bool = True
    batch_size: int = 5
    save_intermediate: Optional[bool] = True
    save_frequency: Optional[int] = 10
    store_metadata: bool = False
    output_directory: Optional[str] = None


class ExtractionProgress(BaseModel):
    session_id: str
    status: str  # "processing", "completed", "failed"
    current_row: int
    total_rows: int
    percentage: float
    message: Optional[str] = None
    error: Optional[str] = None


class ExtractionResult(BaseModel):
    session_id: str
    status: str
    rows_processed: int
    datapoints_extracted: List[str]
    metrics: Optional[Dict[str, Any]] = None
    download_url: str


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, Any]
    llm_status: Dict[str, Any]
    active_jobs: int
    version: str


class ModelListResponse(BaseModel):
    available_models: List[str]
    default_model: str
    model_info: Dict[str, Any]


# Global state
active_extractions: Dict[str, Dict[str, Any]] = {}
websocket_connections: Dict[str, WebSocket] = {}


# Create FastAPI app
app = FastAPI(
    title="MedExtract Real API",
    description="Real backend for MedExtract UI with Ollama",
    version="1.0.0",
    # Increase max upload size to 500MB
    max_upload_size=500 * 1024 * 1024
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple test endpoint
@app.get("/test")
async def test():
    """Simple test endpoint"""
    return {"status": "ok", "message": "Backend is running"}


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check system health"""
    # Check if Ollama is available
    ollama_status = "unknown"
    available_models = []
    
    try:
        import ollama
        import os
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        print(f"Health check: Connecting to Ollama at {ollama_host}")
        ollama_client = ollama.Client(host=ollama_host)
        models = ollama_client.list()
        available_models = [m['name'] for m in models.get('models', [])]
        ollama_status = "healthy" if available_models else "no_models"
        print(f"Health check: Ollama status = {ollama_status}, models = {available_models}")
    except Exception as e:
        ollama_status = f"error: {str(e)}"
        print(f"Health check: Ollama error = {ollama_status}")
    
    # Determine overall health status
    # API is working, so always show healthy
    # The app is functional even without Ollama immediately available
    overall_status = "healthy"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(),
        components={
            "api": True,
            "ollama": ollama_status == "healthy",
            "models_available": len(available_models) > 0
        },
        llm_status={
            "status": ollama_status,
            "models": available_models,
            "message": "No models installed. Please pull a model first." if ollama_status == "no_models" else None
        },
        active_jobs=len(active_extractions),
        version="1.0.0"
    )


# Model endpoints
@app.get("/models", response_model=ModelListResponse)
async def list_models():
    """List available LLM models"""
    try:
        import ollama
        import os
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        ollama_client = ollama.Client(host=ollama_host)
        models = ollama_client.list()
        available_models = [m['name'] for m in models.get('models', [])]
        
        model_info = {}
        for model in models.get('models', []):
            model_info[model['name']] = {
                'size': model.get('size', 0),
                'available': True,
                'details': model.get('details', {})
            }
        
        return ModelListResponse(
            available_models=available_models,
            default_model=available_models[0] if available_models else "phi4:latest",
            model_info=model_info
        )
    except Exception as e:
        # Return empty list if Ollama not available
        return ModelListResponse(
            available_models=[],
            default_model="phi4:latest",
            model_info={}
        )


class ModelPullRequest(BaseModel):
    model_name: str


class ModelPullResponse(BaseModel):
    status: str
    message: str
    model_name: str


class ModelPullProgress(BaseModel):
    status: str
    progress: Optional[float] = None
    total: Optional[float] = None
    completed: Optional[float] = None
    message: str


@app.post("/models/pull", response_model=ModelPullResponse)
async def pull_model(request: ModelPullRequest):
    """Pull a new model from Ollama"""
    try:
        import ollama
        import os
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        ollama_client = ollama.Client(host=ollama_host)
        
        # Pull the model - this returns a generator with progress updates
        print(f"Pulling model: {request.model_name}")
        
        # Process the generator properly
        last_status = ""
        for progress in ollama_client.pull(request.model_name):
            if isinstance(progress, dict) and 'status' in progress:
                last_status = progress.get('status', '')
                print(f"Pull progress: {last_status}")
                # Could send this via websocket for real-time updates
            elif isinstance(progress, str):
                print(f"Pull update: {progress}")
        
        return ModelPullResponse(
            status="success",
            message=f"Model {request.model_name} pulled successfully",
            model_name=request.model_name
        )
    except Exception as e:
        print(f"Error pulling model: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pull model: {str(e)}"
        )


class ModelDeleteRequest(BaseModel):
    model_name: str


class ModelDeleteResponse(BaseModel):
    status: str
    message: str
    model_name: str


@app.delete("/models/{model_name}", response_model=ModelDeleteResponse)
async def delete_model(model_name: str):
    """Delete a model from Ollama"""
    try:
        import ollama
        import os
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        ollama_client = ollama.Client(host=ollama_host)
        
        # Delete the model
        print(f"Deleting model: {model_name}")
        ollama_client.delete(model_name)
        
        return ModelDeleteResponse(
            status="success",
            message=f"Model {model_name} deleted successfully",
            model_name=model_name
        )
    except Exception as e:
        print(f"Error deleting model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete model: {str(e)}"
        )


# WebSocket for model pull progress
@app.websocket("/ws/models/pull/{model_name}")
async def websocket_model_pull(websocket: WebSocket, model_name: str):
    """WebSocket endpoint for real-time model pull progress"""
    await websocket.accept()
    
    try:
        import ollama
        import os
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        ollama_client = ollama.Client(host=ollama_host)
        
        # Start pulling
        await websocket.send_json({
            "status": "starting",
            "message": f"Starting to pull {model_name}..."
        })
        
        for progress in ollama_client.pull(model_name):
            if isinstance(progress, dict):
                await websocket.send_json({
                    "status": progress.get('status', 'pulling'),
                    "digest": progress.get('digest', ''),
                    "total": progress.get('total', 0),
                    "completed": progress.get('completed', 0),
                    "progress": (progress.get('completed', 0) / progress.get('total', 1) * 100) if progress.get('total') else 0
                })
        
        await websocket.send_json({
            "status": "completed",
            "message": f"Successfully pulled {model_name}"
        })
        
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()


# Preset endpoints
@app.get("/presets")
async def list_presets():
    """List available configuration presets"""
    return {
        "presets": [
            {
                "id": "indications_impressions",
                "name": "Indications & Impressions",
                "description": "Extract indications and impressions from medical reports",
                "datapoints": 2
            },
            {
                "id": "btrads",
                "name": "BT-RADS Assessment",
                "description": "Extract medication status and calculate BT-RADS scores",
                "datapoints": 2
            },
            {
                "id": "nih_grants",
                "name": "NIH Grant Analysis",
                "description": "Extract disease, organ, and AI technique information",
                "datapoints": 3
            }
        ]
    }


@app.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get a specific preset configuration"""
    presets = {
        "indications_impressions": {
            "id": "indications_impressions",
            "name": "Indications & Impressions",
            "description": "Extract indications and impressions from medical reports",
            "datapoint_configs": [
                {
                    "name": "indications",
                    "instruction": "Locate the INDICATION section and extract all mentioned indications",
                    "query": "indication reason for exam history dx",
                    "default_value": "NR",
                    "few_shots": []
                },
                {
                    "name": "impressions",
                    "instruction": "Locate the IMPRESSION section and extract all findings",
                    "query": "impression conclusion summary findings",
                    "default_value": "NR",
                    "few_shots": []
                }
            ],
            "default_settings": {
                "use_rag": True,
                "temperature": 0.1,
                "top_k": 40,
                "top_p": 0.9
            }
        }
    }
    
    if preset_id not in presets:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    return presets[preset_id]


# File preview endpoint
@app.post("/preview")
async def preview_file(file: UploadFile = File(...)):
    """Preview uploaded file (first 10 rows)"""
    try:
        # For large files, read in chunks to avoid memory issues
        MAX_PREVIEW_SIZE = 50 * 1024 * 1024  # 50MB for preview
        
        # Check file size first
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        print(f"Preview file: {file.filename}, size: {file_size / 1024 / 1024:.2f}MB")
        
        if file_size > MAX_PREVIEW_SIZE:
            # For large files, only read the first part for preview
            content = await file.read(MAX_PREVIEW_SIZE)
        else:
            content = await file.read()
        
        if file.filename.endswith('.csv'):
            # Try multiple encodings for Windows compatibility
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            total_df = None
            last_error = None
            
            for encoding in encodings:
                try:
                    # For preview, only read first 10 rows
                    df = pd.read_csv(io.BytesIO(content), nrows=10, encoding=encoding)
                    
                    # For total row count, use a more memory-efficient approach
                    if file_size > MAX_PREVIEW_SIZE:
                        # Estimate row count for very large files
                        avg_row_size = len(content) / 10 if len(df) > 0 else 1000
                        estimated_rows = int(file_size / avg_row_size)
                        total_rows = estimated_rows
                        print(f"Large file detected, estimated rows: {estimated_rows}")
                    else:
                        # For smaller files, get exact count
                        total_df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                        total_rows = len(total_df)
                    
                    print(f"Successfully read CSV with encoding: {encoding}")
                    break
                except (UnicodeDecodeError, UnicodeError) as e:
                    last_error = e
                    continue
            
            if df is None:
                raise ValueError(f"Unable to decode CSV file. Last error: {last_error}")
                
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content), nrows=10)
            if file_size > MAX_PREVIEW_SIZE:
                # For large Excel files, just use the preview rows
                total_rows = -1  # Indicate unknown for large Excel files
                print(f"Large Excel file detected, exact row count not available")
            else:
                total_df = pd.read_excel(io.BytesIO(content))
                total_rows = len(total_df)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please use CSV or Excel files.")
        
        return {
            "columns": list(df.columns),
            "rows": df.to_dict('records'),
            "total_rows": total_rows if 'total_rows' in locals() else len(total_df)
        }
    except Exception as e:
        print(f"Preview error for file {file.filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Preview failed: {str(e)}")


# Main extraction endpoint
@app.post("/extract", response_model=ExtractionResult)
async def start_extraction(
    file: UploadFile = File(...),
    config: str = Form(...)
):
    """Start a new extraction process"""
    try:
        # Parse configuration
        extraction_config = ExtractionRequest.parse_raw(config)
        
        # For large files, save to temporary file first
        temp_file = None
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                temp_file = tmp.name
                # Write in chunks to handle large files
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    tmp.write(chunk)
            
            # Get file size
            file_size = os.path.getsize(temp_file)
            print(f"Processing file: {file.filename}, size: {file_size / 1024 / 1024:.2f}MB")
            
            if file.filename.endswith('.csv'):
                # Try multiple encodings for Windows compatibility
                encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
                df = None
                last_error = None
                
                for encoding in encodings:
                    try:
                        # Use chunksize for very large files
                        if file_size > 100 * 1024 * 1024:  # 100MB
                            df = pd.read_csv(temp_file, encoding=encoding, low_memory=False)
                        else:
                            df = pd.read_csv(temp_file, encoding=encoding)
                        print(f"Successfully read CSV for extraction with encoding: {encoding}")
                        break
                    except (UnicodeDecodeError, UnicodeError) as e:
                        last_error = e
                        continue
                
                if df is None:
                    raise ValueError(f"Unable to decode CSV file. Last error: {last_error}")
                    
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(temp_file)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Please use CSV or Excel files.")
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        # Validate columns
        if extraction_config.text_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Text column '{extraction_config.text_column}' not found"
            )
        
        # Create session
        session_id = str(uuid.uuid4())
        # Use custom output directory if provided, otherwise use default
        base_output_dir = extraction_config.output_directory or "./output"
        output_dir = Path(base_output_dir) / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store extraction info
        active_extractions[session_id] = {
            "status": "processing",
            "config": extraction_config.dict(),
            "start_time": datetime.now(),
            "output_dir": str(output_dir),
            "filename": file.filename,
            "total_rows": len(df),
            "current_row": 0,
            "percentage": 0
        }
        
        # Start real extraction in background
        asyncio.create_task(
            run_real_extraction(session_id, df, extraction_config, output_dir)
        )
        
        return ExtractionResult(
            session_id=session_id,
            status="processing",
            rows_processed=0,
            datapoints_extracted=[dp.name for dp in extraction_config.datapoint_configs],
            download_url=f"/results/{session_id}/download"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Extraction error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


async def run_real_extraction(
    session_id: str,
    df: pd.DataFrame,
    config: ExtractionRequest,
    output_dir: Path
):
    """Run real extraction using UnifiedExtractor"""
    try:
        # Convert config to dict for UnifiedExtractor
        extractor_config = {
            'llm_model': config.llm_model,
            'use_rag': config.use_rag,
            'temperature': config.temperature,
            'top_k': config.top_k,
            'top_p': config.top_p,
            'num_ctx': config.num_ctx if hasattr(config, 'num_ctx') else 4096,
            'batch_size': config.batch_size,
            'chunk_size': config.chunk_size,
            'chunk_overlap': config.chunk_overlap,
            'retriever_type': config.retriever_type,
            'reranker_top_n': config.reranker_top_n if hasattr(config, 'reranker_top_n') else 3,
            'extraction_strategy': config.extraction_strategy,
            'use_few_shots': config.use_few_shots,
            'store_metadata': config.store_metadata,
            'checkpoint_frequency': config.save_frequency if hasattr(config, 'save_frequency') else 10,
            'save_intermediate': config.save_intermediate if hasattr(config, 'save_intermediate') else True,
            'checkpoint_path': str(output_dir / "checkpoint.csv")
        }
        
        # Initialize extractor
        extractor = UnifiedExtractor(extractor_config)
        
        # Progress callback
        def progress_callback(current: int, total: int, message: str = ""):
            # Check if stop was requested
            if active_extractions[session_id].get("stop_requested", False):
                raise Exception("Extraction stopped by user")
                
            active_extractions[session_id]["current_row"] = current
            active_extractions[session_id]["percentage"] = (current / total) * 100
            
            # Log progress for debugging
            print(f"Progress: {current}/{total} ({(current/total)*100:.1f}%)")
            
            # Send websocket update if connected
            if session_id in websocket_connections:
                ws = websocket_connections[session_id]
                try:
                    # Create a new event loop for the thread if needed
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Send update
                    asyncio.run_coroutine_threadsafe(
                        ws.send_json({
                            "status": "processing",
                            "current_row": current,
                            "total_rows": total,
                            "percentage": (current / total) * 100,
                            "message": message or f"Processing row {current} of {total}"
                        }),
                        loop
                    ).result(timeout=0.5)  # Add timeout to avoid blocking
                except Exception as e:
                    print(f"WebSocket update error: {e}")
        
        # Run extraction
        results_df = await extractor.extract(
            df=df,
            text_column=config.text_column,
            datapoint_configs=[dp.dict() for dp in config.datapoint_configs],
            ground_truth_column=config.ground_truth_column,
            progress_callback=progress_callback
        )
        
        # Save results with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"results_{timestamp}.csv"
        results_df.to_csv(output_path, index=False)
        
        excel_path = output_dir / f"results_{timestamp}.xlsx"
        results_df.to_excel(excel_path, index=False)
        
        # Calculate metrics if ground truth provided
        metrics = None
        if config.ground_truth_column and config.ground_truth_column in df.columns:
            metrics = {}
            for dp in config.datapoint_configs:
                extracted_col = f"{dp.name}_extracted"
                if extracted_col in results_df.columns:
                    # Simple accuracy calculation
                    matches = (results_df[extracted_col] == results_df[config.ground_truth_column]).sum()
                    accuracy = matches / len(results_df)
                    metrics[dp.name] = {
                        "accuracy": accuracy,
                        "precision": accuracy,  # Simplified for now
                        "recall": accuracy,
                        "f1_score": accuracy
                    }
        
        # Update extraction info
        active_extractions[session_id].update({
            "status": "completed",
            "end_time": datetime.now(),
            "rows_processed": len(results_df),
            "metrics": metrics,
            "output_files": {
                "csv": str(output_path),
                "excel": str(excel_path)
            }
        })
        
        # Notify websocket if connected
        if session_id in websocket_connections:
            ws = websocket_connections[session_id]
            try:
                await ws.send_json({
                    "status": "completed",
                    "current_row": len(results_df),
                    "total_rows": len(results_df),
                    "percentage": 100,
                    "message": "Extraction completed"
                })
            except:
                pass
        
    except Exception as e:
        print(f"Real extraction error: {e}")
        traceback.print_exc()
        active_extractions[session_id].update({
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now()
        })
        
        # Notify websocket if connected
        if session_id in websocket_connections:
            ws = websocket_connections[session_id]
            try:
                await ws.send_json({
                    "status": "failed",
                    "error": str(e)
                })
            except:
                pass


# Progress endpoint
@app.get("/extract/{session_id}/progress", response_model=ExtractionProgress)
async def get_extraction_progress(session_id: str):
    """Get extraction progress"""
    if session_id not in active_extractions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    extraction = active_extractions[session_id]
    
    return ExtractionProgress(
        session_id=session_id,
        status=extraction["status"],
        current_row=extraction.get("current_row", 0),
        total_rows=extraction.get("total_rows", 0),
        percentage=extraction.get("percentage", 0),
        message=f"Processing {extraction.get('filename', 'file')}...",
        error=extraction.get("error")
    )


# Results endpoint
@app.get("/extract/{session_id}/results")
async def get_extraction_results(session_id: str):
    """Get extraction results metadata"""
    if session_id not in active_extractions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    extraction = active_extractions[session_id]
    
    if extraction["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Extraction is {extraction['status']}")
    
    return {
        "session_id": session_id,
        "status": "completed",
        "filename": extraction["filename"],
        "rows_processed": extraction["rows_processed"],
        "datapoints_extracted": len(extraction["config"]["datapoint_configs"]),
        "metrics": extraction.get("metrics"),
        "processing_time": (
            extraction["end_time"] - extraction["start_time"]
        ).total_seconds() if "end_time" in extraction else None,
        "download_formats": ["csv", "excel"]
    }


# Stop endpoint
@app.post("/extract/{session_id}/stop")
async def stop_extraction(session_id: str):
    """Stop a running extraction"""
    if session_id not in active_extractions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    extraction = active_extractions[session_id]
    
    if extraction["status"] != "processing":
        raise HTTPException(status_code=400, detail=f"Extraction is already {extraction['status']}")
    
    # Set stop flag
    extraction["stop_requested"] = True
    extraction["status"] = "stopped"
    
    return {
        "message": "Stop requested",
        "last_processed_row": extraction.get("current_row", 0)
    }


# Download endpoint
@app.get("/extract/{session_id}/download")
async def download_results(session_id: str, format: str = "csv"):
    """Download extraction results"""
    if session_id not in active_extractions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    extraction = active_extractions[session_id]
    
    if extraction["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Extraction is {extraction['status']}")
    
    if format not in ["csv", "excel"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'excel'")
    
    file_path = extraction["output_files"][format]
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    filename = f"{extraction['filename'].rsplit('.', 1)[0]}_extracted.{format}"
    
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


# WebSocket for real-time progress
@app.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    websocket_connections[session_id] = websocket
    
    try:
        while True:
            if session_id not in active_extractions:
                await websocket.send_json({
                    "error": "Session not found"
                })
                break
            
            extraction = active_extractions[session_id]
            
            await websocket.send_json({
                "status": extraction["status"],
                "current_row": extraction.get("current_row", 0),
                "total_rows": extraction.get("total_rows", 0),
                "percentage": extraction.get("percentage", 0),
                "message": f"Processing {extraction.get('filename', 'file')}..."
            })
            
            if extraction["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "error": str(e)
            })
        except:
            pass
    finally:
        if session_id in websocket_connections:
            del websocket_connections[session_id]
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    uvicorn.run(
        "main_real:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )