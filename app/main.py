from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import logging
import time

from app.core.config import settings
from app.api.v1.api import api_router
from app.websocket.websocket_endpoints import router as websocket_router
from app.core.database import engine
from app.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        # Log incoming request
        if "/messages" in str(request.url) or "/conversations" in str(request.url):
            print("=" * 80)
            print(f"📥 [MIDDLEWARE] Incoming request: {request.method} {request.url}")
            print(f"📥 [MIDDLEWARE] Headers: {dict(request.headers)}")
            print(f"📥 [MIDDLEWARE] Query params: {dict(request.query_params)}")
            print("=" * 80)
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        if "/messages" in str(request.url) or "/conversations" in str(request.url):
            print(f"📤 [MIDDLEWARE] Response: {response.status_code} (took {process_time:.3f}s)")
            print("=" * 80)
        
        return response

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="YourHealth1Place Management System API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Add request logging middleware (before CORS)
app.add_middleware(RequestLoggingMiddleware)

# Set up CORS - Allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # Allow frontend origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include WebSocket router
app.include_router(websocket_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "YourHealth1Place API is running",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/cors-test")
async def cors_test():
    return {"message": "CORS is working", "origin": "allowed"} 