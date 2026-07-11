import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings(BaseSettings):
    # API Configurations
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
    
    # Graph Database Configurations
    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USERNAME: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="")
    
    # Vector Database Configurations
    CHROMA_PERSIST_DIR: str = Field(default=str(Path(__file__).parent.parent / "data" / "chroma_db"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Instantiate settings
settings = Settings()

def validate_settings():
    """Helper to check if required keys are configured."""
    missing = []
    if not settings.OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not settings.NEO4J_PASSWORD:
        missing.append("NEO4J_PASSWORD")
    return missing
