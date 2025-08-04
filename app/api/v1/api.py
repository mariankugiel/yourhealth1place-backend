from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, patients, appointments, health_records, medications, messages

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(health_records.router, prefix="/health-records", tags=["health-records"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"]) 