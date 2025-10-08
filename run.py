#!/usr/bin/env python3
"""
Simple script to run the FastAPI application
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    # Enable reload only in development environment
    is_development = settings.ENVIRONMENT.lower() == "development"
    
    # Set log level based on DEBUG setting
    log_level = "debug" if settings.DEBUG else "info"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=is_development,
        log_level=log_level
    ) 