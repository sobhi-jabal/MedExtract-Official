"""
Pydantic models for MedExtract UI
Comprehensive data models for configuration, jobs, and results
"""

from .configuration import (
    OutputFormat,
    RetrievalStrategy,
    ExtractionStrategy,
    DatapointConfig,
    FewShotExample,
    ProcessingConfig,
    RAGConfig,
    LLMConfig,
    EvaluationConfig,
    ExtractionConfig
)

from .jobs import (
    JobStatus,
    ExtractionJob,
    JobProgress,
    JobMetrics
)

from .requests import (
    FileUploadResponse,
    ExtractionRequest,
    JobResponse,
    JobStatusResponse
)

__all__ = [
    # Enums
    "OutputFormat",
    "RetrievalStrategy", 
    "ExtractionStrategy",
    
    # Configuration models
    "DatapointConfig",
    "FewShotExample", 
    "ProcessingConfig",
    "RAGConfig",
    "LLMConfig",
    "EvaluationConfig",
    "ExtractionConfig",
    
    # Job models
    "JobStatus",
    "ExtractionJob",
    "JobProgress",
    "JobMetrics",
    
    # Request/Response models
    "FileUploadResponse",
    "ExtractionRequest",
    "JobResponse",
    "JobStatusResponse"
]