from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from dateutil import parser as date_parser
from app.models.user import User
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AcuityEmbedResponse,
    VideoRoomResponse,
    AcuityWebhookPayload
)
from app.api.v1.endpoints.auth import get_current_user
from app.crud.user import get_user, get_user_by_email
from app.services.acuity_service import acuity_service
from app.services.daily_service import daily_service
from app.services.doctor_supabase_service import doctor_supabase_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# IMPORTANT: More specific routes must come before generic parameter routes
# e.g., /doctors/{id}/... must come before /{appointment_id}


@router.get("/doctors")
async def get_doctors(
    search: Optional[str] = Query(None, description="Search query for filtering doctors"),
    offset: int = Query(0, ge=0, description="Number of doctors to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of doctors to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available doctors for appointments with search functionality
    
    Returns list of doctors with their profiles from Supabase
    """
    try:
        from app.websocket.connection_manager import manager
        
        # Query all doctors (role = "doctor")
        doctors_query = db.query(User).filter(
            User.role == "DOCTOR",
            User.is_active == True
        )

        print('!!!!!!!!!!!!!!!!!!!!!!!!!');
        
        # Apply search filter if provided (search by email or name)
        if search and search.strip():
            search_term = f"%{search.strip().lower()}%"
            doctors_query = doctors_query.filter(
                User.email.ilike(search_term)
            )
        
        # Apply pagination and order by email
        doctors = doctors_query.offset(offset).limit(limit).all()
        
        # Get online users list once for efficiency
        online_users = await manager.get_online_users()
        
        # Format response with profile data from doctor's Supabase
        result = []
        for doctor in doctors:
            try:
                # Fetch doctor profile from doctor's Supabase
                profile = {}
                specialty = None
                full_name = None
                acuity_calendar_id = None
                acuity_owner_id = None
                
                # Get Acuity owner ID from backend environment variable (shared across all doctors)
                acuity_owner_id = settings.ACUITY_USER_ID if settings.ACUITY_USER_ID else None

                if doctor.supabase_user_id:
                    try:
                        # Get doctor profile from doctor_profiles table (includes acuity_calendar_id if available)
                        profile = await doctor_supabase_service.get_doctor_profile(doctor.supabase_user_id, include_acuity_calendar=True) or {}
                        logger.debug(f"Doctor {doctor.id} (email: {doctor.email}, supabase_user_id: {doctor.supabase_user_id}): Profile found: {bool(profile)}, Keys: {list(profile.keys()) if profile else []}")
                        
                        specialty = profile.get("specialty")
                        full_name = profile.get("full_name")
                        acuity_calendar_id = profile.get("acuity_calendar_id")  # Get from profile (fetched together)
                        
                        if acuity_calendar_id:
                            logger.debug(f"✅ Found Acuity calendar ID {acuity_calendar_id} for doctor {doctor.id} (email: {doctor.email})")
                        else:
                            logger.debug(f"⚠️ No Acuity calendar ID in profile for doctor {doctor.id} (email: {doctor.email})")
                    except Exception as e:
                        logger.error(f"❌ Failed to fetch doctor profile for user {doctor.id} (email: {doctor.email}, supabase_user_id: {doctor.supabase_user_id}): {e}", exc_info=True)
                        profile = {}
                else:
                    logger.warning(f"⚠️ Doctor {doctor.id} (email: {doctor.email}) has no supabase_user_id - cannot fetch profile or calendar")
                    profile = {}
                
                # Build display name
                if full_name and full_name.strip():
                    display_name = full_name.strip()
                    name_parts = full_name.strip().split()
                    first_name = name_parts[0] if name_parts else ""
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                else:
                    # Fallback to email
                    email_parts = doctor.email.split('@')
                    display_name = email_parts[0].replace('.', ' ').replace('_', ' ').title()
                    first_name = email_parts[0].split('.')[0].title() if '.' in email_parts[0] else email_parts[0].title()
                    last_name = ""
                
                # Check if user is online using WebSocket status
                is_online = doctor.id in online_users
                
                result.append({
                    "id": str(doctor.id),
                    "name": display_name,
                    "firstName": first_name,
                    "lastName": last_name,
                    "specialty": specialty,
                    "avatar": profile.get("avatar_url"),
                    "isOnline": is_online,
                    "email": doctor.email,
                    "acuityCalendarId": acuity_calendar_id,
                    "acuityOwnerId": acuity_owner_id
                })
            except Exception as e:
                logger.error(f"Error processing doctor {doctor.id}: {e}")
                # Add doctor with fallback data
                email_parts = doctor.email.split('@')
                display_name = email_parts[0].replace('.', ' ').replace('_', ' ').title()
                result.append({
                    "id": str(doctor.id),
                    "name": display_name,
                    "firstName": email_parts[0].split('.')[0].title() if '.' in email_parts[0] else email_parts[0].title(),
                    "lastName": "",
                    "specialty": None,
                    "avatar": None,
                    "isOnline": doctor.id in online_users,
                    "email": doctor.email,
                    "acuityCalendarId": None,
                    "acuityOwnerId": None
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting doctors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching doctors: {str(e)}"
        )


@router.get("/doctors/{professional_id}/acuity-embed", response_model=AcuityEmbedResponse)
async def get_acuity_embed(
    professional_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Acuity embed URL for a specific doctor
    
    Returns embed URL and iframe src for displaying Acuity scheduling widget
    """
    logger.info(f"get_acuity_embed called for professional_id={professional_id}")
    # Get doctor from database
    doctor = get_user(db, professional_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    if doctor.role.value != "doctor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a doctor"
        )
    
    # Get doctor's Supabase user ID
    if not doctor.supabase_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor does not have a Supabase profile linked"
        )
    
    # Get Acuity owner ID from doctor's Supabase profile
    acuity_owner_id = await doctor_supabase_service.get_acuity_owner_id(doctor.supabase_user_id)
    
    if not acuity_owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor does not have Acuity account configured. Please contact administrator."
        )
    
    # Get doctor profile to get the doctor_id (UUID from user_profiles.id)
    doctor_profile = await doctor_supabase_service.get_doctor_profile(doctor.supabase_user_id)
    doctor_id = doctor_profile.get("id") if doctor_profile else None
    
    if not doctor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor profile not found. Please contact administrator."
        )
    
    # Get calendar ID from acuity_calendars table by doctor_id
    acuity_calendar_id = await doctor_supabase_service.get_acuity_calendar_id(
        supabase_user_id=doctor.supabase_user_id,
        doctor_id=doctor_id
    )
    
    if not acuity_calendar_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No calendar assigned for this doctor. Please contact administrator."
        )
    
    # Generate embed URL
    embed_url = acuity_service.generate_embed_url(
        owner_id=acuity_owner_id,
        calendar_id=acuity_calendar_id,
        ref="embedded_csp"
    )
    
    return AcuityEmbedResponse(
        embed_url=embed_url,
        iframe_src=embed_url,
        owner_id=acuity_owner_id,
        calendar_id=acuity_calendar_id
    )


@router.get("/{appointment_id}/video-room", response_model=VideoRoomResponse)
async def get_video_room(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Daily.co video room URL and token for an appointment
    """
    # Get appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Verify user has access to this appointment
    if current_user.role.value == "patient" and appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this appointment"
        )
    
    if current_user.role.value == "doctor" and appointment.professional_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this appointment"
        )
    
    # Check if appointment has video room
    if not appointment.virtual_meeting_url or appointment.virtual_meeting_platform != "daily_co":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment does not have a video room"
        )
    
    # Get room name from virtual_meeting_id
    room_name = appointment.virtual_meeting_id or f"appointment-{appointment_id}"
    
    # Generate tokens
    patient_token = daily_service.create_meeting_token(
        room_name=room_name,
        user_id=f"patient-{appointment.patient_id}",
        is_owner=False,
        user_name="Patient"
    )
    
    professional_token = None
    if current_user.role.value == "doctor":
        professional_token = daily_service.create_meeting_token(
            room_name=room_name,
            user_id=f"professional-{appointment.professional_id}",
            is_owner=True,
            user_name="Professional"
        )
    
    if not patient_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate video room token"
        )
    
    return VideoRoomResponse(
        room_url=appointment.virtual_meeting_url,
        room_name=room_name,
        patient_token=patient_token,
        professional_token=professional_token
    )


@router.post("/webhooks/acuity")
async def acuity_webhook(
    payload: AcuityWebhookPayload,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive appointment events from Acuity
    
    This endpoint should be configured in Acuity settings.
    Acuity will POST appointment data here when appointments are created/updated/canceled.
    """
    try:
        logger.info(f"Received Acuity webhook: appointment_id={payload.id}, canceled={payload.canceled}, calendarID={payload.calendarID}")
        
        # Parse appointment datetime
        scheduled_at = None
        if payload.datetime:
            try:
                scheduled_at = date_parser.parse(payload.datetime)
            except Exception as e:
                logger.error(f"Error parsing datetime {payload.datetime}: {e}")
                scheduled_at = datetime.utcnow()
        
        # Find existing appointment by acuity_appointment_id
        existing_appointment = db.query(Appointment).filter(
            Appointment.acuity_appointment_id == payload.id
        ).first()
        
        # If canceled, update status and cleanup
        if payload.canceled:
            if existing_appointment:
                existing_appointment.status = "CANCELLED"
                # Delete Daily.co room if exists
                if existing_appointment.virtual_meeting_id and existing_appointment.virtual_meeting_platform == "daily_co":
                    daily_service.delete_room(existing_appointment.virtual_meeting_id)
                db.commit()
                logger.info(f"Appointment {payload.id} cancelled")
            return {"status": "processed", "action": "cancelled", "appointment_id": payload.id}
        
        # Find patient by email
        if not payload.email:
            logger.warning(f"No email in Acuity payload for appointment {payload.id}")
            return {"status": "error", "message": "No email provided"}
        
        patient = get_user_by_email(db, payload.email)
        if not patient:
            logger.warning(f"Patient not found for email: {payload.email}")
            return {"status": "error", "message": f"Patient not found for email: {payload.email}"}
        
        # Find professional by calendar ID
        # Get doctor_id directly from acuity_calendars table by calendar_id
        doctor_id = await doctor_supabase_service.get_doctor_id_by_calendar_id(payload.calendarID)
        
        professional = None
        
        if doctor_id:
            # Get the Supabase user_id (auth.users.id) from doctor_id
            supabase_user_id = await doctor_supabase_service.get_supabase_user_id_by_doctor_id(doctor_id)
            
            if supabase_user_id:
                # Find the local User record by matching supabase_user_id
                professional = db.query(User).filter(
                    User.role == "doctor",
                    User.supabase_user_id == supabase_user_id
                ).first()
        
        if not professional:
            logger.warning(f"Professional not found for calendarID: {payload.calendarID}")
            return {"status": "error", "message": f"Professional not found for calendar: {payload.calendarID}"}
        
        # Get professional location (use first location or create default)
        from app.models.professional_locations import ProfessionalLocation
        location = db.query(ProfessionalLocation).filter(
            ProfessionalLocation.practice_id == professional.id
        ).first()
        
        if not location:
            logger.warning(f"No location found for professional {professional.id}, using default")
            # For now, we'll need to handle this case - might need to create a default location
            return {"status": "error", "message": f"No location configured for professional"}
        
        # Determine consultation type (virtual, in-person, phone)
        # Check appointment type or notes to determine if virtual
        # For now, assume virtual if appointment type name contains "virtual" or "video"
        consultation_type = "in_person"  # default
        is_virtual = False
        
        if payload.appointmentTypeID:
            # Try to get appointment type details from Acuity to determine type
            # For now, check notes or use a heuristic
            if payload.notes:
                notes_lower = payload.notes.lower()
                if "virtual" in notes_lower or "video" in notes_lower or "online" in notes_lower:
                    consultation_type = "virtual"
                    is_virtual = True
                elif "phone" in notes_lower or "telephone" in notes_lower:
                    consultation_type = "phone"
        
        # Get default appointment type and pricing
        from app.models.appointment_types import AppointmentType, AppointmentTypePricing
        appointment_type = db.query(AppointmentType).filter(
            AppointmentType.professional_id == professional.id
        ).first()
        
        if not appointment_type:
            logger.warning(f"No appointment type found for professional {professional.id}")
            return {"status": "error", "message": "No appointment type configured for professional"}
        
        pricing = db.query(AppointmentTypePricing).filter(
            AppointmentTypePricing.appointment_type_id == appointment_type.id
        ).first()
        
        if not pricing:
            logger.warning(f"No pricing found for appointment type {appointment_type.id}")
            return {"status": "error", "message": "No pricing configured for appointment type"}
        
        # Create or update appointment
        if existing_appointment:
            # Update existing appointment
            existing_appointment.scheduled_at = scheduled_at or existing_appointment.scheduled_at
            existing_appointment.status = "SCHEDULED"
            existing_appointment.consultation_type = consultation_type
            existing_appointment.reason = payload.notes or existing_appointment.reason
            existing_appointment.acuity_calendar_id = payload.calendarID
            appointment = existing_appointment
            logger.info(f"Updated existing appointment {existing_appointment.id} for Acuity appointment {payload.id}")
        else:
            # Create new appointment
            appointment = Appointment(
                appointment_type_id=appointment_type.id,
                patient_id=patient.id,
                professional_id=professional.id,
                location_id=location.id,
                consultation_type=consultation_type,
                scheduled_at=scheduled_at or datetime.utcnow(),
                duration_minutes=30,  # Default, could be fetched from Acuity
                timezone=payload.timezone or payload.calendarTimezone or "UTC",
                status="SCHEDULED",
                appointment_category="consultation",
                appointment_type_pricing_id=pricing.id,
                cost=pricing.base_fee or 0,
                currency="USD",
                payment_status="PENDING",
                acuity_appointment_id=payload.id,
                acuity_calendar_id=payload.calendarID,
                booked_by=patient.id,
                booked_at=datetime.utcnow(),
                reason=payload.notes,
                created_by=patient.id
            )
            db.add(appointment)
            db.flush()  # Get the appointment ID
        
        # Create Daily.co room if virtual appointment
        if is_virtual and consultation_type == "virtual":
            try:
                # Get patient and professional names
                from app.core.supabase_client import supabase_service
                patient_profile = await supabase_service.get_user_profile(patient.supabase_user_id)
                professional_profile = await doctor_supabase_service.get_doctor_profile(professional.supabase_user_id)
                
                patient_name = f"{payload.firstName or ''} {payload.lastName or ''}".strip() or patient_profile.get("full_name", "Patient") if patient_profile else "Patient"
                professional_name = professional_profile.get("full_name", "Professional") if professional_profile else "Professional"
                
                # Create Daily.co room
                room_data = daily_service.create_room(
                    appointment_id=appointment.id,
                    patient_name=patient_name,
                    professional_name=professional_name,
                    scheduled_time=scheduled_at or datetime.utcnow(),
                    duration_minutes=30
                )
                
                if room_data:
                    appointment.virtual_meeting_url = room_data.get("room_url")
                    appointment.virtual_meeting_id = room_data.get("room_name") or room_data.get("id")
                    appointment.virtual_meeting_platform = "daily_co"
                    logger.info(f"Created Daily.co room for appointment {appointment.id}: {room_data.get('room_name')}")
            except Exception as e:
                logger.error(f"Error creating Daily.co room: {e}")
                # Continue without video room - appointment still created
        
        db.commit()
        db.refresh(appointment)
        
        logger.info(f"Successfully processed Acuity webhook for appointment {payload.id} -> local appointment {appointment.id}")
        return {
            "status": "processed",
            "action": "created" if not existing_appointment else "updated",
            "appointment_id": payload.id,
            "local_appointment_id": appointment.id
        }
        
    except Exception as e:
        logger.error(f"Error processing Acuity webhook: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/", response_model=AppointmentResponse)
def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new appointment"""
    # Implementation would go here
    # Note: In practice, appointments are created via Acuity webhook
    # This endpoint might be used for manual appointment creation
    pass


@router.get("/", response_model=List[AppointmentResponse])
def read_appointments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get appointments based on user role"""
    # Implementation would go here
    if current_user.role.value == "patient":
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == current_user.id
        ).offset(skip).limit(limit).all()
    elif current_user.role.value == "doctor":
        appointments = db.query(Appointment).filter(
            Appointment.professional_id == current_user.id
        ).offset(skip).limit(limit).all()
    else:
        appointments = db.query(Appointment).offset(skip).limit(limit).all()
    
    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def read_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get appointment by ID"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Verify user has access
    if current_user.role.value == "patient" and appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this appointment"
        )
    
    if current_user.role.value == "doctor" and appointment.professional_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this appointment"
        )
    
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Verify user has access
    if current_user.role.value == "patient" and appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this appointment"
        )
    
    # Update appointment in Acuity if it has acuity_appointment_id
    if appointment.acuity_appointment_id:
        acuity_updates = {}
        if appointment_data.appointment_date:
            acuity_updates["datetime"] = appointment_data.appointment_date.isoformat()
        if appointment_data.duration_minutes:
            acuity_updates["duration"] = appointment_data.duration_minutes
        
        if acuity_updates:
            acuity_service.update_appointment(appointment.acuity_appointment_id, acuity_updates)
    
    # Update local database
    update_data = appointment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)
    
    db.commit()
    db.refresh(appointment)
    
    return appointment


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel/delete appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Verify user has access
    if current_user.role.value == "patient" and appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this appointment"
        )
    
    # Cancel in Acuity if it has acuity_appointment_id
    if appointment.acuity_appointment_id:
        acuity_service.cancel_appointment(appointment.acuity_appointment_id)
    
    # Delete Daily.co room if virtual
    if appointment.virtual_meeting_id and appointment.virtual_meeting_platform == "daily_co":
        daily_service.delete_room(appointment.virtual_meeting_id)
    
    # Update status locally
    appointment.status = "CANCELLED"
    db.commit()
    
    return {"message": "Appointment cancelled successfully"} 