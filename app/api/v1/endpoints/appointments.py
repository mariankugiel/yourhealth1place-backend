from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.config import settings
from dateutil import parser as date_parser
import pytz
from app.models.user import User
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AcuityEmbedResponse,
    VideoRoomResponse,
    AcuityWebhookPayload,
    AppointmentBookRequest,
    AppointmentRescheduleRequest,
)
from app.api.v1.endpoints.auth import get_current_user
from app.crud.user import get_user, get_user_by_email
from app.services.acuity_service import acuity_service
from app.services.daily_service import daily_service
from app.services.doctor_supabase_service import doctor_supabase_service
from app.core.supabase_client import supabase_service
import logging
import boto3
import json
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize SQS client for email queue
sqs_client = boto3.client('sqs', region_name=settings.AWS_REGION) if settings.AWS_REGION else None


def send_appointment_confirmation_email(
    email: str,
    patient_name: str,
    doctor_name: str,
    appointment_datetime: str,
    appointment_type: str,
    location: Optional[str] = None,
    phone: Optional[str] = None,
    virtual_meeting_url: Optional[str] = None,
    note: Optional[str] = None
):
    """Send secondary appointment confirmation email with additional information"""
    try:
        queue_url = os.environ.get('SQS_EMAIL_QUEUE_URL') or settings.SQS_EMAIL_QUEUE_URL
        if not queue_url:
            logger.warning("SQS_EMAIL_QUEUE_URL not configured, skipping email")
            return False
        
        # Build email content based on appointment type
        additional_info = []
        if appointment_type == "virtual" and virtual_meeting_url:
            additional_info.append(f"Virtual Meeting: {virtual_meeting_url}")
        elif appointment_type == "in-person" and location:
            additional_info.append(f"Location: {location}")
        elif appointment_type == "phone" and phone:
            additional_info.append(f"Phone Number: {phone}")
        
        additional_info_text = "\n".join(additional_info) if additional_info else "None"
        
        # Build email message
        subject = f"Additional Appointment Information - {doctor_name}"
        message = f"""Dear {patient_name},

Your appointment has been confirmed. Here is additional information:

Appointment Details:
- Doctor: {doctor_name}
- Date & Time: {appointment_datetime}
- Type: {appointment_type.title()}

Additional Information:
{additional_info_text}
"""
        if note:
            message += f"\nNote: {note}\n"
        
        message += """
Best regards,
YourHealth1Place Team
"""
        
        # Build HTML email
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info-section {{ margin: 15px 0; padding: 15px; background-color: white; border-left: 4px solid #4CAF50; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>YourHealth1Place</h2>
        </div>
        <div class="content">
            <h3>Additional Appointment Information</h3>
            <p>Dear {patient_name},</p>
            <p>Your appointment has been confirmed. Here is additional information:</p>
            
            <div class="info-section">
                <h4>Appointment Details:</h4>
                <p><strong>Doctor:</strong> {doctor_name}</p>
                <p><strong>Date & Time:</strong> {appointment_datetime}</p>
                <p><strong>Type:</strong> {appointment_type.title()}</p>
            </div>
            
            <div class="info-section">
                <h4>Additional Information:</h4>
"""
        
        if appointment_type == "virtual" and virtual_meeting_url:
            html_message += f"""
                <p><strong>Virtual Meeting:</strong></p>
                <a href="{virtual_meeting_url}" class="button">Join Video Call</a>
                <p style="font-size: 12px; color: #666;">Or copy this link: {virtual_meeting_url}</p>
"""
        elif appointment_type == "in-person" and location:
            html_message += f'<p><strong>Location:</strong> {location}</p>'
        elif appointment_type == "phone" and phone:
            html_message += f'<p><strong>Phone Number:</strong> {phone}</p>'
        
        html_message += """
            </div>
"""
        
        if note:
            html_message += f"""
            <div class="info-section">
                <p><strong>Note:</strong> {note}</p>
            </div>
"""
        
        html_message += """
        </div>
        <div class="footer">
            <p>Best regards,<br>YourHealth1Place Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        message_body = {
            'email_address': email,
            'title': subject,
            'message': message,
            'html_message': html_message,
            'notification_type': 'appointment_confirmation',
            'priority': 'normal',
            'metadata': {
                'appointment_type': appointment_type,
                'doctor_name': doctor_name,
                'appointment_datetime': appointment_datetime,
                'location': location,
                'phone': phone,
                'virtual_meeting_url': virtual_meeting_url
            }
        }
        
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageGroupId=f"appointment-{email}",
            MessageDeduplicationId=f"appointment-{email}-{datetime.utcnow().isoformat()}"
        )
        
        logger.info(f"✅ Sent appointment confirmation email to {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send appointment confirmation email: {e}")
        return False

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
        
        # Preload Acuity calendars to enrich response with timezone/location
        calendars_by_id: Dict[str, Dict] = {}
        calendars = acuity_service.list_calendars()
        if calendars:
            calendars_by_id = {
                str(calendar.get("id")): calendar
                for calendar in calendars
                if calendar and calendar.get("id") is not None
            }

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
                calendar_timezone = None
                
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
                            calendar_timezone = (
                                profile.get("calendar_timezone")
                                or profile.get("timezone")
                                or profile.get("time_zone")
                            )
                            if not calendar_timezone:
                                calendar_info = calendars_by_id.get(str(acuity_calendar_id))
                                if calendar_info:
                                    calendar_timezone = calendar_info.get("timezone")
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
                    "acuityOwnerId": acuity_owner_id,
                    "timezone": calendar_timezone
                })
            except Exception as e:
                logger.error(f"Error processing doctor {doctor.id}: {e}")
                # Add doctor with fallback data
                email_parts = doctor.email.split('@')
                display_name = email_parts[0].replace('.', ' ').replace('_', ' ').title()
                fallback_timezone = None
                calendar_info = calendars_by_id.get(str(acuity_calendar_id)) if acuity_calendar_id else None
                if calendar_info:
                    fallback_timezone = calendar_info.get("timezone")
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
                    "acuityOwnerId": None,
                    "timezone": fallback_timezone
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
        
        # Get default appointment type and pricing
        from app.models.appointment_types import AppointmentType, AppointmentTypePricing
        appointment_type = db.query(AppointmentType).filter(
            AppointmentType.professional_id == professional.id
        ).first()
        
        # Determine consultation type (virtual, in-person, phone)
        # Check appointment type name, notes, or use default
        consultation_type = "in_person"  # default
        is_virtual = False
        
        # Check appointment type name first (if available)
        if appointment_type and appointment_type.name:
            type_name_lower = appointment_type.name.lower()
            if "virtual" in type_name_lower or "video" in type_name_lower or "online" in type_name_lower:
                consultation_type = "virtual"
                is_virtual = True
            elif "phone" in type_name_lower or "telephone" in type_name_lower:
                consultation_type = "phone"
        
        # Also check notes if consultation type not determined yet
        if consultation_type == "in_person" and payload.notes:
            notes_lower = payload.notes.lower()
            if "virtual" in notes_lower or "video" in notes_lower or "online" in notes_lower:
                consultation_type = "virtual"
                is_virtual = True
            elif "phone" in notes_lower or "telephone" in notes_lower:
                consultation_type = "phone"
        
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
        logger.info(f"Checking if appointment is virtual: is_virtual={is_virtual}, consultation_type={consultation_type}")
        if is_virtual and consultation_type == "virtual":
            logger.info(f"Creating Daily.co room for virtual appointment {appointment.id}")
            try:
                # Get patient and professional names
                from app.core.supabase_client import supabase_service
                patient_profile = await supabase_service.get_user_profile(patient.supabase_user_id)
                professional_profile = await doctor_supabase_service.get_doctor_profile(professional.supabase_user_id)
                
                patient_name = f"{payload.firstName or ''} {payload.lastName or ''}".strip() or patient_profile.get("full_name", "Patient") if patient_profile else "Patient"
                professional_name = professional_profile.get("full_name", "Professional") if professional_profile else "Professional"
                
                logger.info(f"Creating Daily.co room: appointment_id={appointment.id}, patient={patient_name}, professional={professional_name}")
                
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
                    logger.info(f"✅ Created Daily.co room for appointment {appointment.id}: room_name={room_data.get('room_name')}, url={room_data.get('room_url')}")
                else:
                    logger.warning(f"⚠️ Daily.co room creation returned None for appointment {appointment.id}")
            except Exception as e:
                logger.error(f"❌ Error creating Daily.co room for appointment {appointment.id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue without video room - appointment still created
        else:
            logger.info(f"Skipping Daily.co room creation: is_virtual={is_virtual}, consultation_type={consultation_type}")
        
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


@router.get("/availability/dates")
async def get_availability_dates(
    calendar_id: str = Query(..., description="Acuity calendar ID"),
    appointment_type_id: int = Query(0, description="Appointment type ID"),
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    current_user: User = Depends(get_current_user)
):
    """Get available dates for a calendar"""
    try:
        effective_type_id = appointment_type_id if appointment_type_id else 0
        dates = acuity_service.get_availability_dates(
            calendar_id=calendar_id,
            appointment_type_id=effective_type_id,
            month=month
        )
        
        if dates is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch available dates from Acuity"
            )
        
        return {"dates": dates}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available dates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch available dates: {str(e)}"
        )


@router.get("/availability/times")
async def get_availability_times(
    calendar_id: str = Query(..., description="Acuity calendar ID"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    appointment_type_id: int = Query(0, description="Appointment type ID"),
    current_user: User = Depends(get_current_user)
):
    """Get available time slots for a calendar on a specific date"""
    try:
        effective_type_id = appointment_type_id if appointment_type_id else None
        times = acuity_service.get_available_times(
            calendar_id=calendar_id,
            appointment_type_id=effective_type_id,
            date=date
        )
        
        if times is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch available times from Acuity"
            )
        
        return {"times": times}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available times: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch available times: {str(e)}"
        )


@router.get("/availability/week")
async def get_availability_week(
    calendar_id: str = Query(..., description="Acuity calendar ID"),
    start_date: str = Query(..., description="Week start date in YYYY-MM-DD format"),
    appointment_type_id: int = Query(0, description="Appointment type ID"),
    current_user: User = Depends(get_current_user)
):
    """Get available time slots for each day in the week starting at start_date"""
    try:
        try:
            week_start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be in YYYY-MM-DD format"
            )

        effective_type_id = appointment_type_id if appointment_type_id else None
        weekly_map: Dict[str, List[Dict]] = {}
        for offset in range(7):
            current_day = (week_start + timedelta(days=offset)).strftime("%Y-%m-%d")
            try:
                day_slots = acuity_service.get_available_times(
                    calendar_id=calendar_id,
                    appointment_type_id=effective_type_id,
                    date=current_day,
                )
                if not day_slots:
                    weekly_map[current_day] = []
                else:
                    weekly_map[current_day] = day_slots
            except Exception as day_error:
                logger.error(f"Failed to fetch time slots for {current_day}: {day_error}")
                weekly_map[current_day] = []

        response_days = []
        for offset in range(7):
            current_day = (week_start + timedelta(days=offset)).strftime("%Y-%m-%d")
            response_days.append({
                "date": current_day,
                "slots": weekly_map.get(current_day, [])
            })

        return {"week": response_days}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching weekly availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weekly availability: {str(e)}"
        )


@router.post("/")
async def create_appointment(
    appointment: AppointmentBookRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new appointment via Acuity API"""
    try:
        # Build fields array
        fields = []
        
        # Always include appointment type
        if settings.ACUITY_FIELD_ID_APPOINTMENT_TYPE:
            fields.append({
                "id": settings.ACUITY_FIELD_ID_APPOINTMENT_TYPE,
                "value": appointment.appointment_type
            })
        
        virtual_meeting_url = None
        effective_appointment_type_id = appointment.appointment_type_id
        
        # Handle virtual appointments - create Daily.co room first
        if appointment.appointment_type == "virtual":
            try:
                # Get patient and doctor information
                patient_profile = await supabase_service.get_user_profile(current_user.supabase_user_id)
                patient_name = patient_profile.get("full_name", f"{appointment.first_name} {appointment.last_name}") if patient_profile else f"{appointment.first_name} {appointment.last_name}"
                
                # Get doctor name from calendar ID
                doctor_name = "Doctor"
                try:
                    doctor_id = await doctor_supabase_service.get_doctor_id_by_calendar_id(appointment.calendar_id)
                    if doctor_id:
                        profile_response = supabase_service.client.table("doctor_profiles").select("full_name").eq("id", doctor_id).limit(1).execute()
                        if profile_response.data:
                            doctor_name = profile_response.data[0].get("full_name", doctor_name)
                except Exception as e:
                    logger.warning(f"Could not fetch doctor name for Daily.co room: {e}")
                
                # Parse datetime for Daily.co room creation
                apt_datetime = date_parser.parse(appointment.datetime)
                
                # Create Daily.co room
                room_data = daily_service.create_room(
                    appointment_id=0,  # We don't have appointment ID yet
                    patient_name=patient_name,
                    professional_name=doctor_name,
                    scheduled_time=apt_datetime,
                    duration_minutes=30
                )
                
                if room_data and room_data.get("room_url"):
                    virtual_meeting_url = room_data.get("room_url")
                    if settings.ACUITY_FIELD_ID_VIRTUAL_MEETING_URL:
                        fields.append({
                            "id": settings.ACUITY_FIELD_ID_VIRTUAL_MEETING_URL,
                            "value": virtual_meeting_url
                        })
                    logger.info(f"Created Daily.co room: {virtual_meeting_url}")
            except Exception as e:
                logger.error(f"Error creating Daily.co room: {e}")
                # Continue without video room - appointment still created
        
        # Determine appointment type ID if not provided
        if not effective_appointment_type_id:
            effective_appointment_type_id = acuity_service.get_default_appointment_type_id()

        # Format datetime with timezone for Acuity API
        # Acuity expects: YYYY-MM-DDTHH:MM:SS-TZ:TZ (e.g., 2024-01-15T10:00:00-0500)
        appointment_datetime = appointment.datetime
        if appointment.timezone:
            try:
                # Parse the datetime string (assumes it's in the user's timezone)
                dt = date_parser.parse(appointment.datetime)
                # If datetime is naive, localize it to the user's timezone
                if dt.tzinfo is None:
                    user_tz = pytz.timezone(appointment.timezone)
                    dt = user_tz.localize(dt)
                # Format for Acuity API: YYYY-MM-DDTHH:MM:SS-TZ:TZ
                appointment_datetime = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
                # Format timezone offset as -0500 instead of -05:00
                if len(appointment_datetime) > 19 and appointment_datetime[-3] == ":":
                    appointment_datetime = appointment_datetime[:-3] + appointment_datetime[-2:]
            except Exception as e:
                logger.warning(f"Error formatting datetime with timezone: {e}, using original datetime")
                # Fallback to original datetime
                appointment_datetime = appointment.datetime
        
        # Create appointment in Acuity
        acuity_appointment = acuity_service.create_appointment(
            calendar_id=appointment.calendar_id,
            appointment_type_id=effective_appointment_type_id,
            datetime=appointment_datetime,
            firstName=appointment.first_name,
            lastName=appointment.last_name,
            email=appointment.email,
            phone=appointment.phone,
            notes=appointment.note,  # No "Note: " prefix
            fields=fields if fields else None
        )
        
        if not acuity_appointment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create appointment in Acuity"
            )
        
        # Get doctor name from calendar ID for email
        doctor_name = "Doctor"
        try:
            # Find doctor by calendar ID
            doctor_id = await doctor_supabase_service.get_doctor_id_by_calendar_id(appointment.calendar_id)
            if doctor_id:
                profile_response = supabase_service.client.table("doctor_profiles").select("full_name").eq("id", doctor_id).limit(1).execute()
                if profile_response.data:
                    doctor_name = profile_response.data[0].get("full_name", doctor_name)
        except Exception as e:
            logger.warning(f"Could not fetch doctor name for calendar {appointment.calendar_id}: {e}")
        
        # Format appointment datetime for email display
        try:
            apt_dt = date_parser.parse(appointment_datetime)
            formatted_datetime = apt_dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            formatted_datetime = appointment_datetime
        
        # Send secondary confirmation email
        patient_name = f"{appointment.first_name} {appointment.last_name}"
        send_appointment_confirmation_email(
            email=appointment.email,
            patient_name=patient_name,
            doctor_name=doctor_name,
            appointment_datetime=formatted_datetime,
            appointment_type=appointment.appointment_type,
            location=None,
            phone=appointment.phone if appointment.appointment_type == "phone" else None,
            virtual_meeting_url=virtual_meeting_url,
            note=appointment.note
        )
        
        # Return created appointment
        return {
            "id": acuity_appointment.get("id"),
            "status": "created",
            "acuity_appointment": acuity_appointment
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}"
        )


@router.get("/")
async def read_appointments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get appointments from Acuity API based on user role"""
    try:
        # Get user email for filtering
        user_email = current_user.email
        if not user_email:
            logger.warning(f"No email found for user {current_user.id}")
            return []
        
        # Fetch appointments from Acuity API
        acuity_appointments = acuity_service.get_appointments(email=user_email)
        
        if not acuity_appointments:
            logger.info(f"No appointments found for user {user_email}")
            return []
        
        # Parse and enrich appointments
        doctor_profile_cache: Dict[str, Dict] = {}
        result = []
        for apt in acuity_appointments:
            # Parse fields array to extract custom data
            appointment_type = "in-person"  # default
            virtual_meeting_url = None
            
            if apt.get("fields"):
                for field in apt["fields"]:
                    field_id = field.get("id")
                    field_value = field.get("value")
                    
                    if field_id == settings.ACUITY_FIELD_ID_APPOINTMENT_TYPE:
                        appointment_type = field_value or "in-person"
                    elif field_id == settings.ACUITY_FIELD_ID_VIRTUAL_MEETING_URL:
                        virtual_meeting_url = field_value
            
            # Map status to frontend format
            canceled = apt.get("canceled", False)
            if canceled:
                frontend_status = "cancelled"
            else:
                # Check if appointment is in the past
                apt_datetime = apt.get("datetime")
                if apt_datetime:
                    try:
                        apt_dt = date_parser.parse(apt_datetime)
                        if apt_dt < datetime.now(apt_dt.tzinfo) if apt_dt.tzinfo else apt_dt.replace(tzinfo=None) < datetime.utcnow():
                            frontend_status = "completed"
                        else:
                            frontend_status = "upcoming"
                    except:
                        frontend_status = "upcoming"
                else:
                    frontend_status = "upcoming"
            
            # Get doctor information from calendar ID
            calendar_id = apt.get("calendarID")
            doctor_name = "Unknown Doctor"
            doctor_specialty = None
            timezone = apt.get("timezone") or apt.get("calendarTimezone")

            if calendar_id:
                try:
                    doctor_id = await doctor_supabase_service.get_doctor_id_by_calendar_id(str(calendar_id))
                    if doctor_id:
                        if doctor_id in doctor_profile_cache:
                            profile = doctor_profile_cache[doctor_id]
                        else:
                            profile_response = supabase_service.client.table("doctor_profiles").select("full_name,specialty").eq("id", doctor_id).limit(1).execute()
                            profile = profile_response.data[0] if profile_response.data else {}
                            doctor_profile_cache[doctor_id] = profile

                        if profile:
                            doctor_name = profile.get("full_name", doctor_name)
                            doctor_specialty = profile.get("specialty")
                except Exception as e:
                    logger.warning(f"Could not fetch doctor info for calendar {calendar_id}: {e}")

            # Duration and appointment type
            duration_raw = apt.get("duration") or apt.get("durationMinutes")
            try:
                duration_minutes = int(duration_raw) if duration_raw is not None else 30
            except (TypeError, ValueError):
                duration_minutes = 30

            appointment_type_id = apt.get("appointmentTypeID")
            try:
                appointment_type_id = int(appointment_type_id) if appointment_type_id is not None else None
            except (TypeError, ValueError):
                appointment_type_id = None

            created_at_raw = apt.get("dateCreated")
            if created_at_raw:
                try:
                    created_at = date_parser.parse(created_at_raw).isoformat()
                except Exception:
                    created_at = created_at_raw
            else:
                created_at = None

            updated_at_raw = apt.get("lastModified")
            if updated_at_raw:
                try:
                    updated_at = date_parser.parse(updated_at_raw).isoformat()
                except Exception:
                    updated_at = updated_at_raw
            else:
                updated_at = None

            # Build response
            # Cost information
            price_raw = apt.get("price") or apt.get("amount")
            amount_paid_raw = apt.get("amountPaid")
            try:
                price_value = float(price_raw)
            except (TypeError, ValueError):
                price_value = None

            try:
                amount_paid_value = float(amount_paid_raw)
            except (TypeError, ValueError):
                amount_paid_value = None

            appointment_data = {
                "id": apt.get("id"),
                "patient_id": current_user.id,  # Current user is the patient
                "professional_id": 0,  # Will need to map from calendar ID
                "appointment_date": apt.get("datetime"),
                "scheduled_at": apt.get("datetime"),
                "duration_minutes": duration_minutes,
                "appointment_type": appointment_type_id or 0,
                "status": "CANCELLED" if canceled else "SCHEDULED",
                "frontend_status": frontend_status,
                "notes": apt.get("notes"),
                "created_at": created_at,
                "updated_at": updated_at,
                # Acuity integration fields
                "acuity_appointment_id": str(apt.get("id", "")),
                "acuity_calendar_id": str(calendar_id) if calendar_id else None,
                # Video meeting fields
                "virtual_meeting_url": virtual_meeting_url,
                "consultation_type": appointment_type,
                # Doctor information
                "doctor_name": doctor_name,
                "doctor_specialty": doctor_specialty,
                "timezone": timezone,
                "cost": price_value,
                "amount_paid": amount_paid_value,
                "is_paid": apt.get("paid") == "yes",
            }
            result.append(appointment_data)
        
        # Sort by scheduled_at descending
        result.sort(key=lambda x: x.get("scheduled_at") or "", reverse=True)
        
        # Apply pagination
        return result[skip:skip + limit]
        
    except Exception as e:
        logger.error(f"Error fetching appointments from Acuity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch appointments: {str(e)}"
        )


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


@router.put("/{appointment_id}")
async def reschedule_appointment(
    appointment_id: str,
    appointment_data: AppointmentRescheduleRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Reschedule an appointment managed by Acuity.
    """
    updates: Dict[str, str] = {}

    if appointment_data.appointment_date:
        updates["datetime"] = appointment_data.appointment_date.isoformat()

    if appointment_data.calendar_id:
        updates["calendarID"] = appointment_data.calendar_id

    if appointment_data.timezone:
        updates["timezone"] = appointment_data.timezone

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided to reschedule appointment.",
        )

    acuity_response = acuity_service.reschedule_appointment(appointment_id, updates)

    if acuity_response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reschedule appointment in Acuity.",
        )

    return {
        "message": "Appointment rescheduled successfully",
        "appointment": acuity_response,
    }


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel/delete appointment"""
    try:
        acuity_service.cancel_appointment(str(appointment_id))
        return {"message": "Appointment cancelled successfully"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        ) 