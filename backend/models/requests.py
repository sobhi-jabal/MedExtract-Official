"""
Request and response models for the API
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .configuration import ExtractionConfig
from .jobs import JobStatus, JobProgress, JobMetrics


class FileUploadResponse(BaseModel):
    """Response for file upload"""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    rows: int = Field(..., description="Number of rows in the file")
    columns: List[str] = Field(..., description="Column names")
    
    # Text column detection
    text_entries: int = Field(..., description="Number of non-empty text entries")
    requires_column_mapping: bool = Field(..., description="Whether column mapping is required")
    suggested_text_column: Optional[str] = Field(default=None, description="Suggested text column")
    
    # File preview
    preview: List[Dict[str, Any]] = Field(..., description="Preview of first few rows")
    
    # File information
    file_size_mb: float = Field(..., description="File size in MB")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="Upload timestamp")


class ExtractionRequest(BaseModel):
    """Request to start an extraction job"""
    file_id: str = Field(..., description="File identifier from upload")
    config: ExtractionConfig = Field(..., description="Extraction configuration")
    
    # Optional overrides
    text_column: Optional[str] = Field(default=None, description="Override text column name")
    job_name: Optional[str] = Field(default=None, description="Human-readable job name")
    job_description: Optional[str] = Field(default=None, description="Job description")
    priority: int = Field(default=0, description="Job priority")


class JobResponse(BaseModel):
    """Response for job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Initial job status")
    message: str = Field(default="Job created successfully", description="Response message")
    estimated_duration_minutes: Optional[float] = Field(default=None, description="Estimated duration")


class JobStatusResponse(BaseModel):
    """Response for job status query"""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: JobProgress = Field(..., description="Job progress information")
    
    # Timing information
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion time")
    
    # Results and metrics
    metrics: Optional[JobMetrics] = Field(default=None, description="Job metrics")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed error information")
    
    # Output information
    output_available: bool = Field(default=False, description="Whether output file is available")
    output_file_size_mb: Optional[float] = Field(default=None, description="Output file size in MB")
    
    # Runtime information
    duration_seconds: Optional[float] = Field(default=None, description="Job duration in seconds")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")


class ModelListResponse(BaseModel):
    """Response for available models query"""
    available_models: List[str] = Field(..., description="List of available model names")
    default_model: str = Field(..., description="Default model name")
    model_info: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Additional model information"
    )


class TemplateResponse(BaseModel):
    """Response for datapoint templates"""
    templates: Dict[str, Dict[str, Any]] = Field(..., description="Available templates")
    categories: List[str] = Field(..., description="Template categories")


class ValidationResponse(BaseModel):
    """Response for configuration validation"""
    valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class JobListResponse(BaseModel):
    """Response for job list query"""
    jobs: List[Dict[str, Any]] = Field(..., description="List of jobs")
    total_jobs: int = Field(..., description="Total number of jobs")
    active_jobs: int = Field(..., description="Number of active jobs")
    completed_jobs: int = Field(..., description="Number of completed jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")


class MetricsResponse(BaseModel):
    """Response for job metrics"""
    job_id: str = Field(..., description="Job identifier")
    metrics: JobMetrics = Field(..., description="Comprehensive job metrics")
    
    # Visualizations (base64 encoded images)
    confusion_matrix_image: Optional[str] = Field(default=None, description="Confusion matrix plot")
    accuracy_chart_image: Optional[str] = Field(default=None, description="Accuracy chart")
    
    # Export options
    export_formats: List[str] = Field(default=["csv", "xlsx", "json"], description="Available export formats")


class SystemStatusResponse(BaseModel):
    """Response for system status"""
    status: str = Field(..., description="Overall system status")
    
    # System resources
    cpu_usage_percent: float = Field(..., description="Current CPU usage")
    memory_usage_mb: float = Field(..., description="Current memory usage")
    disk_usage_mb: float = Field(..., description="Current disk usage")
    
    # Job queue status
    queued_jobs: int = Field(..., description="Number of queued jobs")
    running_jobs: int = Field(..., description="Number of running jobs")
    
    # Service status
    ollama_available: bool = Field(..., description="Whether Ollama service is available")
    models_loaded: List[str] = Field(..., description="Currently loaded models")
    
    # Uptime
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    last_restart: datetime = Field(..., description="Last restart time")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier for debugging")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="System health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    components: Dict[str, bool] = Field(default_factory=dict, description="Component status")
    llm_status: Dict[str, Any] = Field(default_factory=dict, description="LLM service status")
    active_jobs: int = Field(default=0, description="Number of active jobs")
    version: str = Field(default="1.0.0", description="Application version")


class ConfigValidationRequest(BaseModel):
    """Request for configuration validation"""
    datapoint_configs: List[Dict[str, Any]] = Field(..., description="Datapoint configurations")
    processing_config: Dict[str, Any] = Field(..., description="Processing configuration")
    llm_config: Optional[Dict[str, Any]] = Field(default=None, description="LLM configuration")
    rag_config: Optional[Dict[str, Any]] = Field(default=None, description="RAG configuration")


class ProcessDataFrameRequest(BaseModel):
    """Request for processing a dataframe"""
    job_id: str = Field(..., description="Job identifier")
    text_column: str = Field(..., description="Text column name")
    datapoint_configs: List[Dict[str, Any]] = Field(..., description="Datapoint configurations")
    processing_config: Dict[str, Any] = Field(..., description="Processing configuration")
    llm_config: Optional[Dict[str, Any]] = Field(default=None, description="LLM configuration")
    rag_config: Optional[Dict[str, Any]] = Field(default=None, description="RAG configuration")


class JobRequest(BaseModel):
    """Request to create a new job"""
    name: str = Field(..., description="Job name")
    datapoint_configs: List[Dict[str, Any]] = Field(..., description="Datapoint configurations")
    processing_config: Dict[str, Any] = Field(..., description="Processing configuration")
    llm_config: Optional[Dict[str, Any]] = Field(default=None, description="LLM configuration")
    rag_config: Optional[Dict[str, Any]] = Field(default=None, description="RAG configuration")
    text_column: str = Field(..., description="Text column name")
    ground_truth_column: Optional[str] = Field(default=None, description="Ground truth column name")