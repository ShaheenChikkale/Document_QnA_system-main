"""
Application Configuration
Manages all environment variables and settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    groq_api_key: str
    pinecone_api_key: str
    
    # Pinecone Configuration
    pinecone_environment: str = "gcp-starter"
    pinecone_index_name: str = "document-qa-index"
    
    # Model Configuration
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    llm_model: str = "llama-3.3-70b-versatile"
    
    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 100
    
    # Retrieval Configuration
    top_k_retrieval: int = 10
    top_k_rerank: int = 5
    
    # Cache Configuration
    cache_size: int = 100
    
    # Conversation Configuration
    max_conversation_history: int = 10
    
    # File Upload Configuration
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: str = "pdf,docx,txt,png,jpg,jpeg"
    
    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get list of allowed file extensions"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
