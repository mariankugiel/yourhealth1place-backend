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
from app.core.database import engine, SessionLocal
from app.models import Base
from app.core.init_db import init_health_record_types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize default data (health record types)
# This ensures essential system data exists on startup
try:
    db = SessionLocal()
    try:
        created, updated = init_health_record_types(db, force=False)
        if created > 0:
            logger.info(f"✓ Database initialization: {created} health record types created")
        elif updated > 0:
            logger.info(f"✓ Database initialization: {updated} health record types updated")
        else:
            logger.debug("✓ Database initialization: All health record types already exist")
    except Exception as e:
        logger.error(f"Database initialization warning: {e}", exc_info=True)
    finally:
        db.close()
except Exception as e:
    logger.error(f"Database initialization error: {e}", exc_info=True)
    # Continue anyway - the app can still start

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

# Set up CORS - Use configured origins from settings
# Note: When allow_credentials=True, you cannot use "*" - must specify exact origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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