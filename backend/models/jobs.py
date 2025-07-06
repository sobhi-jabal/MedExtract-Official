"""
Job management models for extraction pipeline
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .configuration import ExtractionConfig, ProcessingConfig


class JobStatus(str, Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    DATA_UPLOADED = "data_uploaded"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobProgress(BaseModel):
    """Job progress tracking"""
    total_rows: int = Field(default=0, description="Total number of rows to process")
    processed_rows: int = Field(default=0, description="Number of rows processed")
    current_row: int = Field(default=0, description="Current row being processed")
    
    # Datapoint progress (for multi-call strategy)
    total_datapoints: int = Field(default=0, description="Total number of datapoints")
    current_datapoint: int = Field(default=0, description="Current datapoint being processed")
    current_datapoint_name: Optional[str] = Field(default=None, description="Name of current datapoint")
    
    # Error tracking
    error_count: int = Field(default=0, description="Number of errors encountered")
    warning_count: int = Field(default=0, description="Number of warnings")
    
    # Time estimates
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")
    
    @property
    def percentage(self) -> float:
        """Calculate overall completion percentage"""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100
    
    @property
    def datapoint_percentage(self) -> float:
        """Calculate datapoint completion percentage"""
        if self.total_datapoints == 0:
            return 0.0
        return (self.current_datapoint / self.total_datapoints) * 100


class JobMetrics(BaseModel):
    """Job metrics and evaluation results"""
    
    # Overall metrics
    total_processed: int = Field(default=0, description="Total rows processed successfully")
    total_errors: int = Field(default=0, description="Total rows with errors")
    total_warnings: int = Field(default=0, description="Total warnings")
    
    # Processing time
    processing_time_seconds: float = Field(default=0.0, description="Total processing time")
    average_time_per_row: float = Field(default=0.0, description="Average time per row")
    
    # Extraction metrics per datapoint
    datapoint_metrics: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Metrics per datapoint"
    )
    
    # Evaluation metrics (if ground truth provided)
    evaluation_metrics: Optional[Dict[str, float]] = Field(
        default=None, 
        description="Evaluation metrics against ground truth"
    )
    
    # Confusion matrix data (if evaluation enabled)
    confusion_matrix: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Confusion matrix data"
    )
    
    # Resource usage
    peak_memory_mb: Optional[float] = Field(default=None, description="Peak memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(default=None, description="Average CPU usage")
    
    # Quality metrics
    invalid_extractions: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of invalid extractions per datapoint"
    )
    empty_extractions: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of empty extractions per datapoint"
    )


class JobCheckpoint(BaseModel):
    """Job checkpoint for recovery"""
    job_id: str = Field(..., description="Job ID")
    last_processed_row: int = Field(..., description="Last successfully processed row")
    current_datapoint_index: int = Field(default=0, description="Current datapoint index")
    partial_results_path: Optional[str] = Field(default=None, description="Path to partial results")
    checkpoint_timestamp: datetime = Field(default_factory=datetime.now, description="Checkpoint timestamp")
    
    # State information
    extracted_data: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Extracted data so far"
    )
    
    # Error information
    errors_encountered: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Errors encountered so far"
    )


class ExtractionJob(BaseModel):
    """Main extraction job model"""
    
    # Job identification
    job_id: str = Field(..., description="Unique job identifier")
    name: Optional[str] = Field(default=None, description="Human-readable job name")
    description: Optional[str] = Field(default=None, description="Job description")
    
    # Job configuration
    config: ExtractionConfig = Field(..., description="Extraction configuration")
    file_id: str = Field(..., description="Uploaded file identifier")
    text_column: str = Field(default="Report Text", description="Text column name")
    
    # Job status and timing
    status: JobStatus = Field(default=JobStatus.QUEUED, description="Current job status")
    created_at: datetime = Field(default_factory=datetime.now, description="Job creation time")
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion time")
    
    # Progress tracking
    progress: JobProgress = Field(default_factory=JobProgress, description="Job progress")
    
    # Results and metrics
    metrics: Optional[JobMetrics] = Field(default=None, description="Job metrics")
    output_file_path: Optional[str] = Field(default=None, description="Path to output file")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed error information")
    
    # Checkpoint information
    checkpoint: Optional[JobCheckpoint] = Field(default=None, description="Checkpoint for recovery")
    last_checkpoint_at: Optional[datetime] = Field(default=None, description="Last checkpoint time")
    
    # Resource information
    worker_id: Optional[str] = Field(default=None, description="Worker processing this job")
    priority: int = Field(default=0, description="Job priority (higher = more priority)")
    
    # Cancellation
    cancel_requested: bool = Field(default=False, description="Whether cancellation was requested")
    cancelled_by: Optional[str] = Field(default=None, description="Who cancelled the job")
    
    # Configuration overrides
    processing_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Runtime processing parameter overrides"
    )
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration in seconds"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_active(self) -> bool:
        """Check if job is actively running"""
        return self.status in [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.PAUSED]
    
    @property
    def is_complete(self) -> bool:
        """Check if job is completed (success or failure)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    def update_progress(self, processed_rows: int, current_row: int = None, 
                       current_datapoint: int = None, current_datapoint_name: str = None):
        """Update job progress"""
        self.progress.processed_rows = processed_rows
        if current_row is not None:
            self.progress.current_row = current_row
        if current_datapoint is not None:
            self.progress.current_datapoint = current_datapoint
        if current_datapoint_name is not None:
            self.progress.current_datapoint_name = current_datapoint_name
    
    def add_error(self, error_message: str, row_index: int = None, datapoint: str = None):
        """Add an error to the job"""
        self.progress.error_count += 1
        
        if not self.checkpoint:
            self.checkpoint = JobCheckpoint(job_id=self.job_id, last_processed_row=0)
        
        error_info = {
            "timestamp": datetime.now(),
            "message": error_message,
            "row_index": row_index,
            "datapoint": datapoint
        }
        
        self.checkpoint.errors_encountered.append(error_info)
    
    def create_checkpoint(self, last_processed_row: int, extracted_data: Dict = None):
        """Create a checkpoint for recovery"""
        self.checkpoint = JobCheckpoint(
            job_id=self.job_id,
            last_processed_row=last_processed_row,
            current_datapoint_index=self.progress.current_datapoint,
            extracted_data=extracted_data or {}
        )
        self.last_checkpoint_at = datetime.now()