"""Configuration settings using Pydantic"""
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    
    # Database
    DB_USER: str = "root"
    DB_PASS: str = ""
    DB_NAME: str = "multiagent_db"
    DB_HOST: str = "localhost"
    INSTANCE_CONNECTION_NAME: Optional[str] = None
    
    # JWT
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_BUCKET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()