from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Configuration
    API_KEY: str = "default-secret-key"
    ENABLE_TELEMETRY: bool = False

    # Model Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_MODEL_PATH: str = "models/vicuna-7b-v1.5.Q4_0.gguf"

    # Groq API Configuration (for cloud-based LLM)
    USE_GROQ: bool = True  # Set to True to use Groq API instead of local LLM
    GROQ_API_KEY: str = ""  # Set your Groq API key here or in .env
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # or "mixtral-8x7b-32768"
    GROQ_TEMPERATURE: float = 0.7
    GROQ_MAX_TOKENS: int = 1024

    # Resource Limits
    MAX_UPLOAD_SIZE_MB: int = 50
    EMBEDDING_BATCH_SIZE: int = 32
    LLM_CONTEXT_SIZE: int = 2048
    LLM_MAX_TOKENS: int = 512
    LLM_THREADS: int = 4
    LLM_TEMPERATURE: float = 0.7

    # Storage Configuration
    DATA_DIR: str = "data"
    FAISS_INDEX_PATH: str = "data/faiss_index"
    UPLOAD_DIR: str = "data/uploads"
    PROCESSED_DIR: str = "data/processed"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create directories
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)