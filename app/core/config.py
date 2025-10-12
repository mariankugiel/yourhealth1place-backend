from typing import List
from pydantic_settings import BaseSettings
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
    AWS_ATHENA_DATABASE: str = "yourhealth1place_analytics"
    AWS_ATHENA_WORKGROUP: str = "primary"
    SQS_EMAIL_QUEUE_URL: str = "your-sqs-email-queue-url"
    LAMBDA_API_TOKEN: str = "your-lambda-webhook-token"
    
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
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = "your-openai-api-key"
    
    # Application
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "YourHealth1Place API"
    VERSION: str = "1.0.0"

    # OpenAI Configuration (if needed for future features)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 4000
    
    # Lambda Webhook Configuration
    LAMBDA_WEBHOOK_TOKEN: str = "your-lambda-webhook-token"
    OPENAI_TEMPERATURE: float = 0.1
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 