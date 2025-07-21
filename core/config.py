from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)
    print(f"Loaded .env file from: {env_file}")
else:
    print("No .env file found")

# Debug: Print key env variables
print("ENV SECRET_KEY:", os.environ.get("SECRET_KEY"))
print("ENV GOOGLE_CLIENT_ID:", os.environ.get("GOOGLE_CLIENT_ID"))
print("ENV GOOGLE_CLIENT_SECRET:", os.environ.get("GOOGLE_CLIENT_SECRET"))

class Settings(BaseSettings):
    # Application Settings
    PROJECT_NAME: str = "Internal Docs Q&A API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    
    # Hugging Face
    HUGGINGFACE_API_TOKEN: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Model Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings() 