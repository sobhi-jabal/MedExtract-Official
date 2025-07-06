"""
Unified Medical Text Extraction Pipeline
Combines best features from all example scripts for a simplified, direct extraction approach
"""

import pandas as pd
import numpy as np
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path
import asyncio
from tqdm import tqdm

# LangChain imports
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain.retrievers.document_compressors.base import BaseDocumentCompressor
from langchain.callbacks.manager import Callbacks
from sentence_transformers import CrossEncoder

# Ollama for LLM
import ollama
from ollama import Options


class MedicalReranker(BaseDocumentCompressor):
    """Medical-specific reranker using BGE model"""
    model_name: str = "BAAI/bge-reranker-v2-m3"
    top_n: int = 3
    
    def __init__(self, top_n: int = 3):
        self.top_n = top_n
        try:
            self.model = CrossEncoder(self.model_name)
        except Exception as e:
            print(f"Warning: reranker unavailable – {e}")
            self.model = None
    
    def medical_rerank(self, query: str, docs: List[str]) -> List[Tuple[int, float]]:
        if self.model is None:
            return [(i, 0.5) for i in range(min(len(docs), self.top_n))]
        scores = self.model.predict([[query, d] for d in docs])
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:self.top_n]
    
    def compress_documents(
        self,
        documents: List[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> List[Document]:
        if not documents:
            return []
        docs = list(documents)
        ranking = self.medical_rerank(query, [d.page_content for d in docs])
        out: List[Document] = []
        for idx, score in ranking:
            d = docs[idx]
            d.metadata["relevance_score"] = score
            out.append(d)
        return out


class UnifiedExtractor:
    """
    Unified extraction pipeline that supports:
    - Multiple datapoints (single or multiple LLM calls)
    - RAG with smart medical chunking
    - Checkpointing for large files
    - Real-time progress updates
    - Ground truth comparison
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_model = config.get('llm_model', 'phi4:latest')
        self.use_rag = config.get('use_rag', False)
        self.temperature = config.get('temperature', 0.1)
        self.top_k = config.get('top_k', 40)
        self.top_p = config.get('top_p', 0.9)
        self.batch_size = config.get('batch_size', 10)
        self.checkpoint_frequency = config.get('checkpoint_frequency', 10)
        self.save_intermediate = config.get('save_intermediate', True)
        self.checkpoint_path = config.get('checkpoint_path', 'checkpoint.csv')
        self.num_ctx = config.get('num_ctx', 4096)
        
        # RAG configuration
        self.chunk_size = config.get('chunk_size', 800)
        self.chunk_overlap = config.get('chunk_overlap', 150)
        self.retriever_type = config.get('retriever_type', 'hybrid')
        
        # Extraction strategy
        self.extraction_strategy = config.get('extraction_strategy', 'single_call')  # or 'multi_call'
        
        # Initialize components
        self.embeddings = None
        self.reranker = None
        if self.use_rag:
            self._initialize_rag_components()
    
    def _initialize_rag_components(self):
        """Initialize RAG components"""
        try:
            self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
            self.reranker = MedicalReranker(top_n=3)
        except Exception as e:
            print(f"Error initializing RAG components: {e}")
            self.use_rag = False
    
    @staticmethod
    def preprocess_text(text: str) -> str:
        """Clean and normalize text"""
        if not text or pd.isna(text):
            return ""
        text = str(text)
        # Normalize quotes and dashes
        text = (
            text.replace('"', '"')
            .replace("''", "'")
            .replace("''", "'")
            .replace("–", "-")
            .replace("—", "-")
            .replace("…", "...")
        )
        # Remove non-printable characters
        text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\t\r")
        # Normalize excessive newlines
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()
    
    @staticmethod
    def detect_medical_sections(text: str) -> List[Tuple[str, int, int]]:
        """Detect common medical report sections"""
        patterns = [
            (r"Chief Complaint:", "chief_complaint"),
            (r"History of Present Illness:", "present_illness"),
            (r"Past Medical History:", "past_medical"),
            (r"Medications:", "medications"),
            (r"Allergies:", "allergies"),
            (r"Social History:", "social_history"),
            (r"Review of Systems:", "review_systems"),
            (r"Physical Exam:", "physical_exam"),
            (r"Laboratory:", "laboratory"),
            (r"Imaging:", "imaging"),
            (r"Assessment:", "assessment"),
            (r"Plan:", "plan"),
            (r"Impression:", "impression"),
            (r"Findings:", "findings"),
            (r"Indication:", "indication"),
        ]
        
        sections = []
        for pattern, name in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                sections.append((name, match.start(), match.end()))
        
        sections.sort(key=lambda x: x[1])
        
        # Merge overlapping sections and set proper boundaries
        final_sections = []
        for i, (name, start, _) in enumerate(sections):
            end = sections[i + 1][1] if i < len(sections) - 1 else len(text)
            final_sections.append((name, start, end))
        
        return final_sections
    
    def smart_medical_chunker(self, text: str) -> List[Document]:
        """Create smart chunks based on medical sections"""
        cleaned = self.preprocess_text(text)
        sections = self.detect_medical_sections(cleaned)
        chunks = []
        chunk_id = 0
        
        if not sections:
            # No sections detected, use regular chunking
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", ".", " "],
            )
            for i, chunk_text in enumerate(splitter.split_text(cleaned)):
                chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata={
                            "chunk_id": i,
                            "section": "unknown",
                            "source_type": "regular_chunk",
                        }
                    )
                )
            return chunks
        
        # Process each section
        for name, start, end in sections:
            section_text = cleaned[start:end]
            
            if len(section_text) <= self.chunk_size:
                # Section fits in one chunk
                chunks.append(
                    Document(
                        page_content=section_text,
                        metadata={
                            "chunk_id": chunk_id,
                            "section": name,
                            "source_type": "section_chunk",
                        }
                    )
                )
                chunk_id += 1
            else:
                # Section needs to be split
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=["\n\n", "\n", ". ", ".", " "],
                )
                for i, chunk_text in enumerate(splitter.split_text(section_text)):
                    chunks.append(
                        Document(
                            page_content=chunk_text,
                            metadata={
                                "chunk_id": chunk_id,
                                "section": name,
                                "section_part": i,
                                "source_type": "section_subchunk",
                            }
                        )
                    )
                    chunk_id += 1
        
        return chunks
    
    def retrieve_context(self, text: str, query: str) -> Tuple[str, List[Dict]]:
        """Retrieve relevant context using RAG"""
        if not self.use_rag:
            # Return full text (truncated if needed)
            max_chars = 65000  # ~16k tokens
            context = text[:max_chars]
            return context, [{
                "chunk_id": -1,
                "section": "full_text",
                "relevance_score": 1.0,
                "source_type": "full_text",
            }]
        
        # Create chunks
        chunks = self.smart_medical_chunker(text)
        if not chunks:
            return text[:2000], [{"error": "no chunks created"}]
        
        # Build retriever
        try:
            # Vector store
            vector_store = FAISS.from_documents(chunks, self.embeddings)
            semantic_retriever = vector_store.as_retriever(
                search_type="similarity", 
                search_kwargs={"k": 5}
            )
            
            if self.retriever_type == "semantic":
                retriever = semantic_retriever
            elif self.retriever_type == "keyword":
                retriever = BM25Retriever.from_documents(chunks, k=5)
            else:  # hybrid
                keyword_retriever = BM25Retriever.from_documents(chunks, k=5)
                ensemble = EnsembleRetriever(
                    retrievers=[semantic_retriever, keyword_retriever],
                    weights=[0.6, 0.4]
                )
                if self.reranker:
                    retriever = ContextualCompressionRetriever(
                        base_compressor=self.reranker,
                        base_retriever=ensemble
                    )
                else:
                    retriever = ensemble
            
            # Retrieve documents
            retrieved_docs = retriever.invoke(query)
            
            # Build context and source info
            context_parts = []
            source_info = []
            
            for i, doc in enumerate(retrieved_docs):
                context_parts.append(f"[CHUNK {i+1}]\n{doc.page_content}")
                source_info.append({
                    "chunk_id": doc.metadata.get("chunk_id", i),
                    "section": doc.metadata.get("section", "unknown"),
                    "relevance_score": doc.metadata.get("relevance_score", 0.0),
                    "source_type": doc.metadata.get("source_type", "retrieved"),
                })
            
            return "\n\n".join(context_parts), source_info
            
        except Exception as e:
            print(f"Retrieval error: {e}")
            # Fallback to first few chunks
            fallback_chunks = chunks[:3]
            context = "\n\n---\n\n".join(c.page_content for c in fallback_chunks)
            return context[:2000], [{
                "chunk_id": i,
                "section": c.metadata.get("section", "unknown"),
                "relevance_score": 0.5,
                "source_type": "fallback",
            } for i, c in enumerate(fallback_chunks)]
    
    def construct_prompt(
        self, 
        context: str, 
        datapoint_configs: List[Dict[str, Any]],
        source_info: List[Dict] = None
    ) -> List[Dict[str, str]]:
        """Construct prompt for extraction"""
        # System message
        system_content = (
            "You are an expert medical data extractor with extreme attention to detail. "
            "Follow the instructions precisely and extract data accurately from medical reports. "
            "Return only what is asked in JSON format."
        )
        
        if source_info:
            system_content += (
                f"\n\nCONTEXT ANALYSIS:\n"
                f"{len(source_info)} sections retrieved.\n" +
                "\n".join(
                    f"- Chunk {i+1}: {s['section']} (score {s.get('relevance_score', 0):.2f})"
                    for i, s in enumerate(source_info)
                ) +
                "\n\nINSTRUCTIONS:\n"
                "- Read all context carefully\n"
                "- Focus on relevant and recent information\n"
                "- Output valid JSON exactly as requested"
            )
        
        messages = [{"role": "system", "content": system_content}]
        
        # Add few-shot examples if provided
        if self.config.get('use_few_shots', True):
            for dp_config in datapoint_configs:
                few_shots = dp_config.get('few_shots', [])
                messages.extend(few_shots)
        
        # User message with extraction instructions
        if self.extraction_strategy == 'single_call':
            # Single call for all datapoints
            instructions_text = []
            for dp_config in datapoint_configs:
                instructions_text.append(
                    f"**{dp_config['name']}**: {dp_config['instruction']}"
                )
            
            all_keys = [dp['name'] for dp in datapoint_configs]
            
            user_content = (
                f"Context:\n{context}\n\n"
                f"Task: Extract the following data points and return a single JSON with keys: "
                f"{', '.join(all_keys)}\n\n"
                "Instructions for each key:\n\n" +
                "\n\n".join(instructions_text) +
                "\n\nReturn exactly one valid JSON object containing all keys."
            )
        else:
            # Multi-call strategy - construct prompt for first datapoint
            dp_config = datapoint_configs[0]
            user_content = (
                f"Context:\n{context}\n\n"
                f"Task: {dp_config['instruction']}\n\n"
                f"Return JSON in format: {{{dp_config['name']}: <extracted_value>}}"
            )
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    async def call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call Ollama LLM"""
        try:
            # Set Ollama host to connect to container
            import os
            ollama_host = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
            ollama_client = ollama.Client(host=ollama_host)
            
            response = await asyncio.to_thread(
                ollama_client.chat,
                model=self.llm_model,
                messages=messages,
                format="json",
                options=Options(
                    temperature=self.temperature,
                    top_k=self.top_k,
                    top_p=self.top_p,
                    num_ctx=self.num_ctx,
                    num_predict=512,
                    seed=42,
                )
            )
            return response['message']['content']
        except Exception as e:
            print(f"LLM error: {e}")
            return ""
    
    def parse_extraction_result(self, raw_output: str, datapoint_configs: List[Dict]) -> Dict[str, Any]:
        """Parse LLM output into structured result"""
        result = {}
        
        # Initialize with default values
        for dp_config in datapoint_configs:
            result[dp_config['name']] = dp_config.get('default_value', 'NR')
        
        if not raw_output:
            return result
        
        try:
            # Try to parse JSON
            cleaned = raw_output.strip()
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = cleaned[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                # Extract values for each datapoint
                for dp_config in datapoint_configs:
                    key = dp_config['name']
                    if key in parsed:
                        value = parsed[key]
                        # Validate if needed
                        valid_values = dp_config.get('valid_values')
                        if valid_values and value not in valid_values:
                            result[key] = dp_config.get('default_value', 'invalid')
                        else:
                            result[key] = value
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            # Try fallback parsing with regex
            for dp_config in datapoint_configs:
                key = dp_config['name']
                patterns = [
                    rf'"{key}"\s*:\s*"([^"]+)"',
                    rf"'{key}'\s*:\s*'([^']+)'",
                    rf"{key}\s*:\s*([^\s,}}]+)",
                ]
                for pattern in patterns:
                    match = re.search(pattern, raw_output, re.IGNORECASE)
                    if match:
                        result[key] = match.group(1)
                        break
        
        return result
    
    async def extract_from_row(
        self, 
        text: str, 
        datapoint_configs: List[Dict[str, Any]],
        row_index: int = 0
    ) -> Dict[str, Any]:
        """Extract datapoints from a single row of text"""
        # Preprocess text
        cleaned_text = self.preprocess_text(text)
        
        if not cleaned_text:
            return {dp['name']: dp.get('default_value', 'NR') for dp in datapoint_configs}
        
        result = {"_original_text": text[:200] + "..." if len(text) > 200 else text}
        
        if self.extraction_strategy == 'single_call':
            # Extract all datapoints in one call
            # Build query for retrieval
            query = " ".join([dp.get('query', dp['name']) for dp in datapoint_configs])
            context, source_info = self.retrieve_context(cleaned_text, query)
            
            # Construct prompt
            messages = self.construct_prompt(context, datapoint_configs, source_info)
            
            # Call LLM
            raw_output = await self.call_llm(messages)
            
            # Parse result
            extracted = self.parse_extraction_result(raw_output, datapoint_configs)
            result.update(extracted)
            
            # Add metadata
            result["_raw_output"] = raw_output
            result["_source_info"] = source_info
            
        else:
            # Multi-call strategy - extract each datapoint separately
            for dp_config in datapoint_configs:
                query = dp_config.get('query', dp_config['name'])
                context, source_info = self.retrieve_context(cleaned_text, query)
                
                # Construct prompt for this datapoint
                messages = self.construct_prompt(context, [dp_config], source_info)
                
                # Call LLM
                raw_output = await self.call_llm(messages)
                
                # Parse result
                extracted = self.parse_extraction_result(raw_output, [dp_config])
                result[dp_config['name']] = extracted.get(dp_config['name'], dp_config.get('default_value', 'NR'))
                
                # Store raw output and source info
                result[f"_{dp_config['name']}_raw"] = raw_output
                result[f"_{dp_config['name']}_sources"] = source_info
        
        return result
    
    async def extract(
        self,
        df: pd.DataFrame,
        text_column: str,
        datapoint_configs: List[Dict[str, Any]],
        ground_truth_column: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> pd.DataFrame:
        """
        Extract datapoints from a DataFrame
        
        Args:
            df: Input DataFrame
            text_column: Column containing text to extract from
            datapoint_configs: List of datapoint configurations
            ground_truth_column: Optional column for evaluation
            progress_callback: Optional callback for progress updates
            
        Returns:
            DataFrame with extracted datapoints
        """
        # Validate inputs
        if text_column not in df.columns:
            raise ValueError(f"Text column '{text_column}' not found in DataFrame")
        
        # Filter out rows with empty text
        valid_mask = df[text_column].notna() & (df[text_column] != '')
        working_df = df[valid_mask].copy()
        
        if len(working_df) == 0:
            raise ValueError("No valid text found in the specified column")
        
        print(f"Processing {len(working_df)} rows with {len(datapoint_configs)} datapoints...")
        
        # Initialize result columns
        for dp_config in datapoint_configs:
            working_df[dp_config['name']] = None
        
        # Process rows for real-time updates
        total_rows = len(working_df)
        
        # Process row by row for real-time progress updates
        for i, idx in enumerate(working_df.index):
            text = working_df.loc[idx, text_column]
            
            # Extract from this row
            result = await self.extract_from_row(text, datapoint_configs, idx)
            
            # Update DataFrame with results
            for dp_config in datapoint_configs:
                working_df.loc[idx, dp_config['name']] = result.get(dp_config['name'])
            
            # Store metadata if requested
            if self.config.get('store_metadata', False):
                working_df.loc[idx, '_raw_output'] = result.get('_raw_output', '')
                working_df.loc[idx, '_source_info'] = json.dumps(result.get('_source_info', []))
            
            # Update progress after each row
            current_row = i + 1
            if progress_callback:
                progress_callback(current_row, total_rows)
            
            # Allow other async operations to run
            await asyncio.sleep(0)
            
            # Checkpoint if needed
            processed = current_row
            if self.save_intermediate and (processed % self.checkpoint_frequency == 0 or processed == total_rows):
                from pathlib import Path
                
                # Save checkpoint (single file that gets overwritten)
                checkpoint_df = working_df.copy()
                # Add metadata columns
                checkpoint_df['_checkpoint_row'] = processed
                checkpoint_df['_checkpoint_total'] = total_rows
                
                # Save to the checkpoint path (overwrite existing)
                checkpoint_path = Path(self.checkpoint_path)
                checkpoint_df.to_csv(checkpoint_path, index=False)
                print(f"Checkpoint saved: {checkpoint_path.name} (row {processed}/{total_rows})")
        
        # Merge results back to original DataFrame
        result_df = df.copy()
        for col in working_df.columns:
            if col not in df.columns:
                result_df[col] = None
                result_df.loc[valid_mask, col] = working_df[col]
        
        # Calculate metrics if ground truth provided
        if ground_truth_column and ground_truth_column in df.columns:
            metrics = self.calculate_metrics(result_df, datapoint_configs, ground_truth_column)
            print("\nExtraction Metrics:")
            for dp_name, dp_metrics in metrics.items():
                print(f"\n{dp_name}:")
                for metric, value in dp_metrics.items():
                    print(f"  {metric}: {value}")
        
        return result_df
    
    def calculate_metrics(
        self, 
        df: pd.DataFrame, 
        datapoint_configs: List[Dict],
        ground_truth_column: str
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate extraction metrics"""
        metrics = {}
        
        for dp_config in datapoint_configs:
            dp_name = dp_config['name']
            if dp_name not in df.columns:
                continue
            
            # Get valid rows (where both extraction and ground truth exist)
            valid_mask = df[dp_name].notna() & df[ground_truth_column].notna()
            valid_df = df[valid_mask]
            
            if len(valid_df) == 0:
                metrics[dp_name] = {"error": "No valid data for comparison"}
                continue
            
            # Calculate basic metrics
            extracted = valid_df[dp_name]
            ground_truth = valid_df[ground_truth_column]
            
            # Exact match accuracy
            exact_matches = (extracted == ground_truth).sum()
            accuracy = exact_matches / len(valid_df)
            
            # Count different types of extractions
            total_extracted = len(valid_df)
            empty_extractions = (extracted == '').sum()
            nr_extractions = (extracted == 'NR').sum()
            invalid_extractions = (extracted == 'invalid').sum()
            
            metrics[dp_name] = {
                "total_extracted": total_extracted,
                "accuracy": round(accuracy, 3),
                "exact_matches": exact_matches,
                "empty_extractions": empty_extractions,
                "nr_extractions": nr_extractions,
                "invalid_extractions": invalid_extractions,
            }
        
        return metrics
    
    def save_results(self, df: pd.DataFrame, output_path: str, format: str = 'csv'):
        """Save extraction results"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'csv':
            df.to_csv(output_path, index=False)
        elif format == 'excel':
            df.to_excel(output_path, index=False)
        elif format == 'json':
            df.to_json(output_path, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"Results saved to {output_path}")


# Convenience function for sync usage
def extract_medical_data(
    df: pd.DataFrame,
    text_column: str,
    datapoint_configs: List[Dict[str, Any]],
    config: Dict[str, Any],
    ground_truth_column: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> pd.DataFrame:
    """
    Synchronous wrapper for medical data extraction
    
    Example usage:
        config = {
            'llm_model': 'phi4:latest',
            'use_rag': True,
            'temperature': 0.1,
            'extraction_strategy': 'single_call',
            'batch_size': 5,
            'checkpoint_frequency': 10,
        }
        
        datapoint_configs = [
            {
                'name': 'diagnosis',
                'instruction': 'Extract the primary diagnosis from the report',
                'query': 'diagnosis disease condition',
                'default_value': 'NR',
                'few_shots': [...]
            },
            {
                'name': 'medications',
                'instruction': 'Extract all medications mentioned',
                'query': 'medications drugs prescriptions',
                'default_value': 'NR',
            }
        ]
        
        result_df = extract_medical_data(
            df, 
            'report_text', 
            datapoint_configs, 
            config
        )
    """
    extractor = UnifiedExtractor(config)
    
    # Run async extraction in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            extractor.extract(
                df, 
                text_column, 
                datapoint_configs,
                ground_truth_column,
                progress_callback
            )
        )
        return result
    finally:
        loop.close()