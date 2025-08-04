from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
import os

class Settings(BaseSettings):
    # Supabase Configuration (Auth, Personal Info, Lightweight Metadata)
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_ANON_KEY: str = "your-supabase-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "your-supabase-service-role-key"
    
    # AWS Configuration (Sensitive Health Data)
    AWS_ACCESS_KEY_ID: str = "your-aws-access-key"
    AWS_SECRET_ACCESS_KEY: str = "your-aws-secret-key"
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "yourhealth1place-documents"
    AWS_DYNAMODB_TABLE: str = "yourhealth1place-health-data"
    AWS_ATHENA_DATABASE: str = "yourhealth1place_analytics"
    AWS_ATHENA_WORKGROUP: str = "primary"
    
    # Akeyless Configuration (Encryption Keys)
    AKEYLESS_ACCESS_ID: str = "your-akeyless-access-id"
    AKEYLESS_ACCESS_KEY: str = "your-akeyless-access-key"
    AKEYLESS_URL: str = "https://api.akeyless.io"
    
    # Database (for internal linkage and non-sensitive data)
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/yourhealth1place_db"
    DATABASE_TEST_URL: str = "postgresql://username:password@localhost:5432/yourhealth1place_test_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-make-it-long-and-random"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    
    # Application
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "YourHealth1Place API"
    VERSION: str = "1.0.0"
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 