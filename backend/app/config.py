from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    redis_decode_responses: bool = True
    redis_required: bool = True
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000  # Default port
    debug: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override port with environment variable for Cloud Run
        if "PORT" in os.environ:
            self.api_port = int(os.environ["PORT"])
            print(f"🔧 Config: Using PORT from environment: {self.api_port}")
        else:
            print(f"🔧 Config: Using default port: {self.api_port}")
        # Override debug based on environment
        if os.getenv("ENVIRONMENT") == "production":
            self.debug = False
            print(f"🔧 Config: Production mode - debug disabled")
        else:
            print(f"🔧 Config: Development mode - debug enabled")
    
    # OpenAI Configuration (optional)
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # File Upload Configuration
    max_file_size: int = 50 * 1024 * 1024  # 50MB (increased for larger documents)
    allowed_extensions: set = {".pdf", ".txt", ".docx", ".doc", ".md", ".rtf"}
    upload_dir: str = "uploads"
    
    # Text Processing Configuration
    max_chunk_size: int = 1000  # Maximum characters per chunk
    min_chunk_size: int = 100   # Minimum characters per chunk
    chunk_overlap: int = 50     # Overlap between chunks
    
    # Cache Configuration
    cache_ttl: int = 3600  # 1 hour
    max_search_results: int = 50
    
    # Embedding Configuration
    embedding_method: str = "auto"  # "openai", "local", or "auto"
    embedding_batch_size: int = 10
    embedding_max_text_length: int = 8192
    
    # Vector Search Configuration
    vector_similarity_threshold: float = 0.7
    vector_search_limit: int = 50
    
    # Semantic Search Configuration
    enable_search_cache: bool = True
    search_cache_ttl: int = 1800  # 30 minutes
    search_result_limit: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
