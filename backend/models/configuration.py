"""
Configuration models for extraction pipeline
Based on patterns from all provided extraction examples
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


class OutputFormat(str, Enum):
    """Output format for extraction"""
    JSON = "json"
    TEXT = "text"


class RetrievalStrategy(str, Enum):
    """RAG retrieval strategies"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword" 
    ENSEMBLE = "ensemble"
    HYBRID = "hybrid"
    SEQUENTIAL = "sequential"


class ExtractionStrategy(str, Enum):
    """Extraction strategy types"""
    SINGLE_CALL = "single_call"  # Extract all datapoints in one LLM call
    MULTI_CALL = "multi_call"    # Separate LLM call per datapoint
    WORKFLOW = "workflow"        # Complex multi-step workflow (like BT-RADS)


class FewShotExample(BaseModel):
    """Few-shot example for prompt engineering"""
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Example content")


class DatapointConfig(BaseModel):
    """Configuration for a single datapoint extraction"""
    name: str = Field(..., description="Unique name for this datapoint")
    instruction: str = Field(..., description="Extraction instruction/prompt")
    json_key: str = Field(..., description="JSON key for the extracted value")
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="Output format")
    valid_values: Optional[List[str]] = Field(default=None, description="Valid values for validation")
    few_shots: List[FewShotExample] = Field(default_factory=list, description="Few-shot examples")
    system_message: Optional[str] = Field(default=None, description="Custom system message")
    
    # Advanced options
    required: bool = Field(default=True, description="Whether this datapoint is required")
    validation_regex: Optional[str] = Field(default=None, description="Regex for validation")
    post_processing: Optional[str] = Field(default=None, description="Post-processing function name")


class RAGConfig(BaseModel):
    """RAG (Retrieval-Augmented Generation) configuration"""
    enabled: bool = Field(default=False, description="Whether to enable RAG")
    
    # Chunking configuration
    chunk_size: int = Field(default=1000, description="Text chunk size for retrieval")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    
    # Retrieval strategy
    strategy: RetrievalStrategy = Field(default=RetrievalStrategy.SEMANTIC, description="Retrieval strategy")
    top_k: int = Field(default=3, description="Number of chunks to retrieve")
    
    # Embeddings configuration
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")
    
    # Reranking
    use_reranker: bool = Field(default=False, description="Whether to use reranking")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", description="Reranker model")
    reranker_top_n: int = Field(default=2, description="Top N after reranking")
    
    # Ensemble weights (for ensemble strategy)
    semantic_weight: float = Field(default=0.6, description="Weight for semantic retrieval")
    keyword_weight: float = Field(default=0.4, description="Weight for keyword retrieval")


class LLMConfig(BaseModel):
    """LLM configuration"""
    model_name: str = Field(..., description="LLM model name")
    
    # Sampling parameters
    temperature: float = Field(default=0.0, description="Sampling temperature")
    top_k: int = Field(default=40, description="Top-k sampling")
    top_p: float = Field(default=0.95, description="Top-p sampling")
    
    # Generation parameters
    max_tokens: Optional[int] = Field(default=512, description="Maximum tokens to generate")
    num_ctx: int = Field(default=4096, description="Context window size")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")
    
    # Advanced parameters
    repeat_penalty: float = Field(default=1.1, description="Repetition penalty")
    mirostat_tau: Optional[float] = Field(default=None, description="Mirostat tau parameter")
    
    # Timeout and retry
    timeout: int = Field(default=120, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class ProcessingConfig(BaseModel):
    """Processing configuration"""
    batch_size: int = Field(default=100, description="Number of rows to process")
    process_all: bool = Field(default=False, description="Process all rows in dataset")
    
    # Performance settings
    concurrent_jobs: int = Field(default=1, description="Number of concurrent extraction jobs")
    save_frequency: int = Field(default=10, description="Save checkpoint every N rows")
    
    # Error handling
    timeout_duration: int = Field(default=120, description="Timeout per extraction in seconds")
    skip_errors: bool = Field(default=True, description="Skip rows with errors and continue")
    max_errors: int = Field(default=50, description="Maximum errors before stopping")
    
    # Verbose output
    verbose: bool = Field(default=False, description="Enable verbose logging")
    debug: bool = Field(default=False, description="Enable debug mode")


class EvaluationConfig(BaseModel):
    """Evaluation configuration for ground truth comparison"""
    enabled: bool = Field(default=False, description="Whether to enable evaluation")
    ground_truth_column: Optional[str] = Field(default=None, description="Ground truth column name")
    
    # Metrics to calculate
    calculate_accuracy: bool = Field(default=True, description="Calculate accuracy")
    calculate_precision: bool = Field(default=True, description="Calculate precision")
    calculate_recall: bool = Field(default=True, description="Calculate recall") 
    calculate_f1: bool = Field(default=True, description="Calculate F1 score")
    
    # Confusion matrix
    generate_confusion_matrix: bool = Field(default=True, description="Generate confusion matrix")
    
    # Custom evaluation
    custom_metrics: List[str] = Field(default_factory=list, description="Custom metric function names")


class ExtractionConfig(BaseModel):
    """Main extraction configuration"""
    
    # Datapoints to extract
    datapoints: List[DatapointConfig] = Field(..., description="List of datapoints to extract")
    
    # Extraction strategy
    strategy: ExtractionStrategy = Field(default=ExtractionStrategy.SINGLE_CALL, description="Extraction strategy")
    
    # LLM configuration
    llm_config: LLMConfig = Field(..., description="LLM configuration")
    
    # RAG configuration
    rag_config: RAGConfig = Field(default_factory=RAGConfig, description="RAG configuration")
    
    # Processing configuration  
    processing_config: ProcessingConfig = Field(default_factory=ProcessingConfig, description="Processing configuration")
    
    # Evaluation configuration
    evaluation_config: EvaluationConfig = Field(default_factory=EvaluationConfig, description="Evaluation configuration")
    
    # File configuration
    text_column: str = Field(default="Report Text", description="Column name containing text to extract from")
    
    # Advanced options
    use_checkpoints: bool = Field(default=True, description="Enable checkpoint/resume functionality")
    cleanup_on_completion: bool = Field(default=True, description="Clean up temporary files on completion")

    @validator('datapoints')
    def validate_datapoints(cls, v):
        """Validate datapoints configuration"""
        if not v:
            raise ValueError("At least one datapoint must be configured")
        
        # Check for unique names and json_keys
        names = [dp.name for dp in v]
        json_keys = [dp.json_key for dp in v]
        
        if len(names) != len(set(names)):
            raise ValueError("Datapoint names must be unique")
        
        if len(json_keys) != len(set(json_keys)):
            raise ValueError("JSON keys must be unique")
        
        return v
    
    @validator('strategy')
    def validate_strategy_compatibility(cls, v, values):
        """Validate strategy is compatible with configuration"""
        if v == ExtractionStrategy.WORKFLOW:
            # Workflow strategy requires specific datapoint configurations
            # This would be validated based on specific workflow requirements
            pass
        return v