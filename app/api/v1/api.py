from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, patients, appointments, health_records, medications, messages, professionals, health_plans, patient_insights, professional_documents

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(health_records.router, prefix="/health-records", tags=["health-records"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])

# Professional-related endpoints
api_router.include_router(professionals.router, prefix="/professionals", tags=["professionals"])
api_router.include_router(health_plans.router, prefix="/health-plans", tags=["health-plans"])
api_router.include_router(patient_insights.router, prefix="/patient-insights", tags=["patient-insights"])
api_router.include_router(professional_documents.router, prefix="/professional-documents", tags=["professional-documents"]) 