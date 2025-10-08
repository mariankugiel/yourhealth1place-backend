from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, appointments, health_records, medications, messages, 
    health_plans, patient_insights, professional_documents, 
    health_record_permissions, health_record_analytics, 
    ai_analysis, medication_reminders, notifications, websocket_status
)
from app.websocket.websocket_endpoints import router as websocket_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
# Patients router removed - data now stored in Supabase user metadata
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(health_records.router, prefix="/health-records", tags=["health-records"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])

# Medication Reminders (includes check-due endpoint for Lambda)
api_router.include_router(medication_reminders.router, prefix="/medication-reminders", tags=["medication-reminders"])

# Notifications
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

api_router.include_router(messages.router, prefix="/messages", tags=["messages"])

# Professional-related endpoints
# Professionals router removed - data now stored in Supabase user metadata
api_router.include_router(health_plans.router, prefix="/health-plans", tags=["health-plans"])
api_router.include_router(patient_insights.router, prefix="/patient-insights", tags=["patient-insights"])
api_router.include_router(professional_documents.router, prefix="/professional-documents", tags=["professional-documents"])

# Lab document analysis endpoints
# Lab documents router removed - functionality moved to health records

# Centralized Document Management endpoints
# Documents router removed - functionality moved to health records

# Health Record Permission Management endpoints
api_router.include_router(health_record_permissions.router, prefix="/health-record-permissions", tags=["health-record-permissions"])

# Health Record Analytics endpoints
api_router.include_router(health_record_analytics.router, prefix="/health-record-analytics", tags=["health-record-analytics"])

# AI Analysis endpoints
api_router.include_router(ai_analysis.router, prefix="/ai-analysis", tags=["ai-analysis"])

# WebSocket endpoints for real-time communication
api_router.include_router(websocket_router, tags=["websocket"])

# WebSocket status endpoints
api_router.include_router(websocket_status.router, prefix="/websocket", tags=["websocket-status"])

# Surgery & Hospitalization endpoints are now integrated into health_records router
