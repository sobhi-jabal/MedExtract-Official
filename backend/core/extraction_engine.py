"""
Comprehensive extraction engine for medical text
Generalizes patterns from all provided extraction examples
"""

import asyncio
import json
import re
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
from tqdm.asyncio import tqdm

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.configuration import (
    ExtractionConfig, DatapointConfig, ExtractionStrategy, 
    RAGConfig, LLMConfig, ProcessingConfig
)
from models.jobs import ExtractionJob, JobStatus, JobMetrics, JobProgress
from core.rag_engine import RAGEngine  
from core.llm_wrapper import LLMWrapper
from utils.text_processing import TextProcessor
from utils.metrics import MetricsCalculator
from utils.checkpoint import CheckpointManager


class ExtractionEngine:
    """
    Comprehensive extraction engine that supports all extraction patterns:
    - Single-call extraction (all datapoints in one LLM call)
    - Multi-call extraction (separate call per datapoint)  
    - Complex workflow extraction (multi-step decision trees)
    """
    
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.llm_wrapper = LLMWrapper()
        self.text_processor = TextProcessor()
        self.metrics_calculator = MetricsCalculator()
        self.checkpoint_manager = CheckpointManager()
        
        self.active_jobs: Dict[str, ExtractionJob] = {}
        
    async def initialize(self):
        """Initialize the extraction engine"""
        await self.llm_wrapper.initialize()
        await self.rag_engine.initialize()
    
    async def process_dataframe(
        self, 
        df: pd.DataFrame,
        text_column: str,
        datapoint_configs: List[DatapointConfig],
        processing_config: ProcessingConfig,
        job: ExtractionJob,
        llm_config: LLMConfig = None,
        rag_config: RAGConfig = None
    ) -> pd.DataFrame:
        """
        Process dataframe with specified configuration
        """
        try:
            # Initialize job tracking
            self.active_jobs[job.job_id] = job
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            # Setup progress tracking
            total_rows = min(len(df), processing_config.batch_size) if not processing_config.process_all else len(df)
            job.progress.total_rows = total_rows
            job.progress.total_datapoints = len(datapoint_configs)
            
            # Initialize result dataframe
            result_df = df.copy()
            
            # Add columns for extraction results
            for dp_config in datapoint_configs:
                result_df[f"{dp_config.name}_raw"] = ""
                result_df[f"{dp_config.name}_cleaned"] = ""
                result_df[f"{dp_config.name}_confidence"] = 0.0
            
            # Determine extraction strategy
            strategy = job.config.strategy
            
            if strategy == ExtractionStrategy.SINGLE_CALL:
                result_df = await self._process_single_call(
                    result_df, text_column, datapoint_configs, 
                    processing_config, job, llm_config, rag_config
                )
            elif strategy == ExtractionStrategy.MULTI_CALL:
                result_df = await self._process_multi_call(
                    result_df, text_column, datapoint_configs,
                    processing_config, job, llm_config, rag_config
                )
            elif strategy == ExtractionStrategy.WORKFLOW:
                result_df = await self._process_workflow(
                    result_df, text_column, datapoint_configs,
                    processing_config, job, llm_config, rag_config
                )
            
            # Calculate final metrics
            if job.config.evaluation_config.enabled:
                job.metrics = await self._calculate_job_metrics(
                    result_df, datapoint_configs, job.config.evaluation_config.ground_truth_column
                )
            
            # Update job status
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress.processed_rows = total_rows
            
            return result_df
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.error_details = {
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now()
            }
            job.completed_at = datetime.now()
            raise
        finally:
            # Cleanup
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
    
    async def _process_single_call(
        self,
        df: pd.DataFrame,
        text_column: str, 
        datapoint_configs: List[DatapointConfig],
        processing_config: ProcessingConfig,
        job: ExtractionJob,
        llm_config: LLMConfig,
        rag_config: RAGConfig
    ) -> pd.DataFrame:
        """
        Process using single-call strategy (like nih_ai_rad_all.py)
        Extract all datapoints in one LLM call per row
        """
        
        # Build combined prompt for all datapoints
        combined_instruction = self._build_combined_instruction(datapoint_configs)
        combined_few_shots = self._combine_few_shots(datapoint_configs)
        
        rows_to_process = min(len(df), processing_config.batch_size) if not processing_config.process_all else len(df)
        
        # Process rows with progress tracking
        async for i in tqdm(range(rows_to_process), desc="Processing rows"):
            if job.cancel_requested:
                break
                
            try:
                text = df.iloc[i][text_column]
                if pd.isna(text) or not text.strip():
                    continue
                
                # Check for checkpoint recovery
                if job.checkpoint and i <= job.checkpoint.last_processed_row:
                    continue
                
                # Preprocess text
                processed_text = self.text_processor.preprocess(text)
                
                # Apply RAG if enabled
                context = processed_text
                if rag_config and rag_config.enabled:
                    context = await self.rag_engine.retrieve_context(
                        processed_text, rag_config, combined_instruction
                    )
                
                # Build messages for LLM
                messages = self._build_single_call_messages(
                    context, combined_instruction, combined_few_shots
                )
                
                # Call LLM
                raw_response = await self.llm_wrapper.generate(
                    messages, llm_config
                )
                
                # Parse and clean response
                parsed_results = self._parse_single_call_response(
                    raw_response, datapoint_configs
                )
                
                # Store results in dataframe
                for dp_config in datapoint_configs:
                    result = parsed_results.get(dp_config.json_key, "invalid")
                    df.at[i, f"{dp_config.name}_raw"] = raw_response
                    df.at[i, f"{dp_config.name}_cleaned"] = result
                    df.at[i, f"{dp_config.name}_confidence"] = self._calculate_confidence(result, dp_config)
                
                # Update progress
                job.update_progress(i + 1, i)
                
                # Create checkpoint
                if i % processing_config.save_frequency == 0:
                    job.create_checkpoint(i, {})
                
            except Exception as e:
                job.add_error(f"Row {i}: {str(e)}", i)
                if not processing_config.skip_errors:
                    raise
                if job.progress.error_count >= processing_config.max_errors:
                    raise Exception(f"Maximum errors ({processing_config.max_errors}) exceeded")
        
        return df
    
    async def _process_multi_call(
        self,
        df: pd.DataFrame,
        text_column: str,
        datapoint_configs: List[DatapointConfig], 
        processing_config: ProcessingConfig,
        job: ExtractionJob,
        llm_config: LLMConfig,
        rag_config: RAGConfig
    ) -> pd.DataFrame:
        """
        Process using multi-call strategy (like original medextract.py)
        Separate LLM call for each datapoint
        """
        
        rows_to_process = min(len(df), processing_config.batch_size) if not processing_config.process_all else len(df)
        
        # Process each row
        for i in range(rows_to_process):
            if job.cancel_requested:
                break
                
            text = df.iloc[i][text_column]
            if pd.isna(text) or not text.strip():
                continue
            
            # Check for checkpoint recovery
            if job.checkpoint and i <= job.checkpoint.last_processed_row:
                continue
            
            # Preprocess text
            processed_text = self.text_processor.preprocess(text)
            
            # Process each datapoint
            for dp_idx, dp_config in enumerate(datapoint_configs):
                if job.cancel_requested:
                    break
                
                try:
                    job.progress.current_datapoint = dp_idx
                    job.progress.current_datapoint_name = dp_config.name
                    
                    # Apply RAG if enabled
                    context = processed_text
                    if rag_config and rag_config.enabled:
                        # Use datapoint-specific query for better retrieval
                        query = self._build_datapoint_query(dp_config)
                        context = await self.rag_engine.retrieve_context(
                            processed_text, rag_config, query
                        )
                    
                    # Build messages for this specific datapoint
                    messages = self._build_datapoint_messages(context, dp_config)
                    
                    # Call LLM
                    raw_response = await self.llm_wrapper.generate(
                        messages, llm_config
                    )
                    
                    # Parse and clean response
                    cleaned_result = self._parse_datapoint_response(
                        raw_response, dp_config
                    )
                    
                    # Store results
                    df.at[i, f"{dp_config.name}_raw"] = raw_response
                    df.at[i, f"{dp_config.name}_cleaned"] = cleaned_result
                    df.at[i, f"{dp_config.name}_confidence"] = self._calculate_confidence(cleaned_result, dp_config)
                    
                except Exception as e:
                    job.add_error(f"Row {i}, Datapoint {dp_config.name}: {str(e)}", i, dp_config.name)
                    if not processing_config.skip_errors:
                        raise
            
            # Update progress
            job.update_progress(i + 1, i)
            
            # Create checkpoint
            if i % processing_config.save_frequency == 0:
                job.create_checkpoint(i, {})
        
        return df
    
    async def _process_workflow(
        self,
        df: pd.DataFrame,
        text_column: str,
        datapoint_configs: List[DatapointConfig],
        processing_config: ProcessingConfig, 
        job: ExtractionJob,
        llm_config: LLMConfig,
        rag_config: RAGConfig
    ) -> pd.DataFrame:
        """
        Process using workflow strategy (like ds_btrads_c1_6.py)
        Complex multi-step decision trees and workflows
        """
        
        # This would implement complex workflow logic
        # For now, fall back to multi-call strategy
        # In a full implementation, this would handle workflow-specific logic
        
        return await self._process_multi_call(
            df, text_column, datapoint_configs, processing_config,
            job, llm_config, rag_config
        )
    
    def _build_combined_instruction(self, datapoint_configs: List[DatapointConfig]) -> str:
        """Build combined instruction for single-call extraction"""
        instructions = []
        for dp_config in datapoint_configs:
            instructions.append(f"**{dp_config.json_key}**: {dp_config.instruction}")
        
        all_keys = [dp.json_key for dp in datapoint_configs]
        
        return f"""Extract the following data points from the clinical text:

{chr(10).join(instructions)}

Return a single JSON object with all keys: {', '.join(all_keys)}
Do not include any additional commentary. Provide only the JSON."""
    
    def _combine_few_shots(self, datapoint_configs: List[DatapointConfig]) -> List[Dict[str, str]]:
        """Combine few-shot examples from all datapoints"""
        combined_examples = []
        for dp_config in datapoint_configs:
            for example in dp_config.few_shots:
                combined_examples.append({
                    "role": example.role,
                    "content": example.content
                })
        return combined_examples
    
    def _build_single_call_messages(
        self, 
        context: str, 
        instruction: str, 
        few_shots: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Build messages for single-call extraction"""
        messages = [
            {
                "role": "system",
                "content": "You are an expert medical data extraction assistant. Extract the requested information accurately and return only valid JSON."
            }
        ]
        
        # Add few-shot examples
        messages.extend(few_shots)
        
        # Add main instruction
        messages.append({
            "role": "user", 
            "content": f"Context:\n{context}\n\nTask: {instruction}"
        })
        
        return messages
    
    def _build_datapoint_query(self, dp_config: DatapointConfig) -> str:
        """Build RAG query for specific datapoint"""
        # Extract key terms from instruction for better retrieval
        return f"{dp_config.name} {dp_config.instruction[:100]}"
    
    def _build_datapoint_messages(
        self, 
        context: str, 
        dp_config: DatapointConfig
    ) -> List[Dict[str, str]]:
        """Build messages for single datapoint extraction"""
        messages = []
        
        # System message
        system_msg = dp_config.system_message or "You are an expert medical data extraction assistant."
        messages.append({"role": "system", "content": system_msg})
        
        # Few-shot examples
        for example in dp_config.few_shots:
            messages.append({
                "role": example.role,
                "content": example.content
            })
        
        # Main instruction
        messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nTask: {dp_config.instruction}"
        })
        
        return messages
    
    def _parse_single_call_response(
        self, 
        raw_response: str, 
        datapoint_configs: List[DatapointConfig]
    ) -> Dict[str, Any]:
        """Parse response from single-call extraction"""
        try:
            # Try to parse as JSON
            start_idx = raw_response.find("{")
            end_idx = raw_response.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = raw_response[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                # Validate and clean results
                results = {}
                for dp_config in datapoint_configs:
                    value = parsed.get(dp_config.json_key, "invalid")
                    results[dp_config.json_key] = self._validate_result(value, dp_config)
                
                return results
        except json.JSONDecodeError:
            pass
        
        # Fallback: return invalid for all datapoints
        return {dp.json_key: "invalid" for dp in datapoint_configs}
    
    def _parse_datapoint_response(
        self, 
        raw_response: str, 
        dp_config: DatapointConfig
    ) -> str:
        """Parse response from single datapoint extraction"""
        if dp_config.output_format.value == "json":
            try:
                start_idx = raw_response.find("{")
                end_idx = raw_response.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = raw_response[start_idx:end_idx]
                    parsed = json.loads(json_str)
                    value = parsed.get(dp_config.json_key, "invalid")
                    return self._validate_result(value, dp_config)
            except json.JSONDecodeError:
                pass
            return "invalid"
        else:
            # Text format
            cleaned = raw_response.strip()
            return self._validate_result(cleaned, dp_config)
    
    def _validate_result(self, value: Any, dp_config: DatapointConfig) -> str:
        """Validate extraction result against datapoint configuration"""
        if dp_config.valid_values and value not in dp_config.valid_values:
            return "invalid"
        
        if dp_config.validation_regex:
            import re
            if not re.match(dp_config.validation_regex, str(value)):
                return "invalid"
        
        return str(value)
    
    def _calculate_confidence(self, result: str, dp_config: DatapointConfig) -> float:
        """Calculate confidence score for extraction result"""
        if result == "invalid":
            return 0.0
        elif result in ["NR", "unknown", ""]:
            return 0.3
        elif dp_config.valid_values and result in dp_config.valid_values:
            return 0.9
        else:
            return 0.7
    
    async def _calculate_job_metrics(
        self, 
        df: pd.DataFrame, 
        datapoint_configs: List[DatapointConfig],
        ground_truth_column: str
    ) -> JobMetrics:
        """Calculate comprehensive job metrics"""
        metrics = JobMetrics()
        
        # Basic processing metrics
        metrics.total_processed = len(df)
        
        # Per-datapoint metrics
        for dp_config in datapoint_configs:
            cleaned_col = f"{dp_config.name}_cleaned"
            if cleaned_col in df.columns:
                # Count invalid/empty extractions
                invalid_count = (df[cleaned_col] == "invalid").sum()
                empty_count = (df[cleaned_col].isin(["", "NR", "unknown"])).sum()
                
                metrics.invalid_extractions[dp_config.name] = int(invalid_count)
                metrics.empty_extractions[dp_config.name] = int(empty_count)
                
                # If ground truth available, calculate accuracy metrics
                if ground_truth_column and ground_truth_column in df.columns:
                    accuracy_metrics = self.metrics_calculator.calculate_accuracy(
                        df[ground_truth_column], df[cleaned_col]
                    )
                    metrics.datapoint_metrics[dp_config.name] = accuracy_metrics
        
        return metrics
    
    def get_available_models(self) -> List[str]:
        """Get list of available LLM models"""
        return self.llm_wrapper.get_available_models()
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.cancel_requested = True
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            return True
        return False