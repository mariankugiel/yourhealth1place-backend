from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import Response
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
    AppointmentPhoneUpdateRequest,
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
    consultation_type: str,
    location: Optional[str] = None,
    phone: Optional[str] = None,
    virtual_meeting_url: Optional[str] = None,
    note: Optional[str] = None,
    is_doctor_email: bool = False
):
    """Send appointment confirmation email to patient or doctor"""
    try:
        queue_url = os.environ.get('SQS_EMAIL_QUEUE_URL') or settings.SQS_EMAIL_QUEUE_URL
        if not queue_url:
            logger.warning("SQS_EMAIL_QUEUE_URL not configured, skipping email")
            return False
        
        # Build email content based on consultation type
        additional_info = []
        if consultation_type == "virtual" and virtual_meeting_url:
            additional_info.append(f"Virtual Meeting: {virtual_meeting_url}")
        elif consultation_type == "in-person" and location:
            additional_info.append(f"Location: {location}")
        elif consultation_type == "phone" and phone:
            additional_info.append(f"Phone Number: {phone}")
        
        additional_info_text = "\n".join(additional_info) if additional_info else "None"
        
        # Different subject and greeting for doctor vs patient
        if is_doctor_email:
            subject = f"New Appointment Scheduled - {patient_name}"
            greeting_name = doctor_name
            recipient_type = "doctor"
        else:
            subject = f"Appointment Confirmation - {doctor_name}"
            greeting_name = patient_name
            recipient_type = "patient"
        
        # Build email message
        if is_doctor_email:
            message = f"""Dear Dr. {doctor_name},

A new appointment has been scheduled with you. Here are the details:

Appointment Details:
- Patient: {patient_name}
- Date & Time: {appointment_datetime}
- Type: {consultation_type.title()}

Additional Information:
{additional_info_text}
"""
        else:
            message = f"""Dear {patient_name},

Your appointment has been confirmed. Here is additional information:

Appointment Details:
- Doctor: {doctor_name}
- Date & Time: {appointment_datetime}
- Type: {consultation_type.title()}

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
            <h3>{'New Appointment Scheduled' if is_doctor_email else 'Appointment Confirmation'}</h3>
            <p>Dear {'Dr. ' + doctor_name if is_doctor_email else patient_name},</p>
            <p>{'A new appointment has been scheduled with you.' if is_doctor_email else 'Your appointment has been confirmed. Here is additional information:'}</p>
            
            <div class="info-section">
                <h4>Appointment Details:</h4>
                {f'<p><strong>Patient:</strong> {patient_name}</p>' if is_doctor_email else f'<p><strong>Doctor:</strong> {doctor_name}</p>'}
                <p><strong>Date & Time:</strong> {appointment_datetime}</p>
                <p><strong>Type:</strong> {consultation_type.title()}</p>
            </div>
            
            <div class="info-section">
                <h4>Additional Information:</h4>
"""
        
        if consultation_type == "virtual" and virtual_meeting_url:
            html_message += f"""
                <p><strong>Virtual Meeting:</strong></p>
                <a href="{virtual_meeting_url}" class="button">Join Video Call</a>
                <p style="font-size: 12px; color: #666;">Or copy this link: {virtual_meeting_url}</p>
"""
        elif consultation_type == "in-person" and location:
            html_message += f'<p><strong>Location:</strong> {location}</p>'
        elif consultation_type == "phone" and phone:
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
                'consultation_type': consultation_type,
                'doctor_name': doctor_name,
                'patient_name': patient_name,
                'appointment_datetime': appointment_datetime,
                'location': location,
                'phone': phone,
                'virtual_meeting_url': virtual_meeting_url,
                'recipient_type': recipient_type
            }
        }
        
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageGroupId=f"appointment-{email}",
            MessageDeduplicationId=f"appointment-{email}-{datetime.utcnow().isoformat()}"
        )
        
        logger.info(f"✅ Sent appointment confirmation email to {email} ({recipient_type})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send appointment confirmation email to {email}: {e}")
        return False

# IMPORTANT: More specific routes must come before generic parameter routes
# e.g., /doctors/{id}/... must come before /{appointment_id}


@router.get("/doctors")
async def get_doctors(
    search: Optional[str] = Query(None, description="Search query for filtering doctors by name or email"),
    location: Optional[str] = Query(None, description="Location filter (city, state, or country)"),
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
        
        # Note: We'll apply name and location filters after fetching profiles
        # since they're stored in Supabase, not the local database
        # For now, we can still filter by email in the database query
        if search and search.strip():
            search_term = f"%{search.strip().lower()}%"
            doctors_query = doctors_query.filter(
                User.email.ilike(search_term)
            )
        
        # Get all doctors first (we'll filter by name/location after fetching profiles)
        all_doctors = doctors_query.all()
        
        if not all_doctors:
            return []
        
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

        # Collect all supabase_user_ids for bulk fetch
        supabase_user_ids = [doc.supabase_user_id for doc in all_doctors if doc.supabase_user_id]
        
        # Bulk fetch all doctor profiles in one query
        profiles_dict = await doctor_supabase_service.get_doctor_profiles_bulk(supabase_user_ids)
        
        # Collect all doctor_ids for bulk calendar fetch
        doctor_ids = []
        for profile in profiles_dict.values():
            doctor_id = profile.get("id") or profile.get("user_id")
            if doctor_id:
                doctor_ids.append(doctor_id)
        
        # Bulk fetch all Acuity calendar IDs in one query
        calendars_dict = await doctor_supabase_service.get_acuity_calendars_bulk(doctor_ids)
        
        # Add calendar IDs to profiles
        for doctor_id, calendar_id in calendars_dict.items():
            if doctor_id in profiles_dict:
                profiles_dict[doctor_id]["acuity_calendar_id"] = calendar_id

        # Format response with profile data from doctor's Supabase
        # Apply name and location filters after fetching profiles
        result = []
        search_term_lower = search.strip().lower() if search and search.strip() else None
        location_filter_lower = location.strip().lower() if location and location.strip() else None
        
        # Get Acuity owner ID from backend environment variable (shared across all doctors)
        acuity_owner_id = settings.ACUITY_USER_ID if settings.ACUITY_USER_ID else None
        
        for doctor in all_doctors:
            try:
                # Get profile from bulk fetched data
                profile = profiles_dict.get(doctor.supabase_user_id, {}) if doctor.supabase_user_id else {}
                
                specialty = profile.get("specialty")
                full_name = profile.get("full_name")
                address = profile.get("address")
                acuity_calendar_id = profile.get("acuity_calendar_id")
                calendar_timezone = None
                
                # Get timezone from profile or calendar
                if acuity_calendar_id:
                    calendar_timezone = (
                        profile.get("calendar_timezone")
                        or profile.get("timezone")
                        or profile.get("time_zone")
                    )
                    if not calendar_timezone:
                        calendar_info = calendars_by_id.get(str(acuity_calendar_id))
                        if calendar_info:
                            calendar_timezone = calendar_info.get("timezone")
                
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
                
                # Apply name search filter (if provided)
                if search_term_lower:
                    # Check if search matches email, name, or specialty
                    email_match = search_term_lower in doctor.email.lower()
                    name_match = full_name and search_term_lower in full_name.lower()
                    specialty_match = specialty and search_term_lower in specialty.lower()
                    if not (email_match or name_match or specialty_match):
                        continue  # Skip this doctor if no match
                
                # Apply location filter (if provided)
                if location_filter_lower and address:
                    address_lower = address.lower()
                    # Check if location filter matches any part of the address
                    if location_filter_lower not in address_lower:
                        continue  # Skip this doctor if address doesn't match
                elif location_filter_lower and not address:
                    # If location filter is provided but doctor has no address, skip
                    continue
                
                # Check if user is online using WebSocket status
                is_online = doctor.id in online_users
                
                result.append({
                    "id": str(doctor.id),
                    "name": display_name,
                    "firstName": first_name,
                    "lastName": last_name,
                    "specialty": specialty,
                    "avatar": profile.get("avatar_url"),
                    "address": address,
                    "isOnline": is_online,
                    "email": doctor.email,
                    "acuityCalendarId": acuity_calendar_id,
                    "acuityOwnerId": acuity_owner_id,
                    "timezone": calendar_timezone,
                    "appointmentTypes": [
                        {
                            "id": str(apt_type.get("id") or apt_type.get("appointmentTypeID")),
                            "name": apt_type.get("name"),
                            "description": apt_type.get("description"),
                            "duration": apt_type.get("duration"),
                            "price": apt_type.get("price"),
                            "type": apt_type.get("type"),
                            "category": apt_type.get("category")
                        }
                        for apt_type in acuity_service.get_appointment_types_for_calendar(str(acuity_calendar_id))
                    ] if acuity_calendar_id else []
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
                    "timezone": fallback_timezone,
                    "appointmentTypes": []
                })
        
        # Apply pagination after filtering
        paginated_result = result[offset:offset + limit]
        
        return paginated_result
        
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
    if not appointment.virtual_meeting_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment does not have a video room"
        )
    
    # Get room name from acuity_appointment_id
    room_name = f"appointment-{appointment.acuity_appointment_id}" if appointment.acuity_appointment_id else f"appointment-{appointment_id}"
    
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
                # Construct room name from Acuity appointment ID (format: appointment-{acuity_appointment_id})
                room_name_to_delete = None
                if existing_appointment.acuity_appointment_id:
                    room_name_to_delete = f"appointment-{existing_appointment.acuity_appointment_id}"
                
                if room_name_to_delete:
                    try:
                        deleted = daily_service.delete_room(room_name_to_delete)
                        if deleted:
                            logger.info(f"✅ Deleted Daily.co room: {room_name_to_delete}")
                        else:
                            logger.warning(f"⚠️ Failed to delete Daily.co room: {room_name_to_delete}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting Daily.co room {room_name_to_delete}: {e}")
                
                db.commit()
                logger.info(f"Appointment {payload.id} cancelled")
            else:
                # Appointment not in local DB, but still try to delete Daily.co room if it exists
                # Room name format: appointment-{acuity_appointment_id}
                room_name_to_delete = f"appointment-{payload.id}"
                try:
                    deleted = daily_service.delete_room(room_name_to_delete)
                    if deleted:
                        logger.info(f"✅ Deleted Daily.co room for canceled appointment: {room_name_to_delete}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not delete Daily.co room {room_name_to_delete}: {e}")
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
        
        # Get doctor's address for location field
        doctor_address = None
        try:
            doctor_id = await doctor_supabase_service.get_doctor_id_by_calendar_id(payload.calendarID)
            if doctor_id:
                profile_response = supabase_service.client.table("doctor_profiles").select("address").eq("id", doctor_id).limit(1).execute()
                if profile_response.data and profile_response.data[0].get("address"):
                    doctor_address = profile_response.data[0].get("address")
        except Exception as e:
            logger.warning(f"Could not fetch doctor address for calendar {payload.calendarID}: {e}")
        
        # Determine consultation type from appointment type category (Virtual, Phone, Person)
        consultation_type = "in-person"  # default
        is_virtual = False
        virtual_meeting_url = None
        
        # Get virtual meeting URL from existing DB appointment if it exists
        if existing_appointment:
            virtual_meeting_url = existing_appointment.virtual_meeting_url
        
        # Get category from appointment type
        appointment_type_id = payload.appointmentTypeID
        if appointment_type_id:
            appointment_types_lookup = acuity_service.get_appointment_types_map()
            if appointment_types_lookup:
                appointment_type_info = appointment_types_lookup.get(str(appointment_type_id))
                if appointment_type_info:
                    category = appointment_type_info.get("category", "Person")
                    category_lower = category.lower() if category else "person"
                    if category_lower == "virtual":
                        consultation_type = "virtual"
                        is_virtual = True
                    elif category_lower == "phone":
                        consultation_type = "phone"
                    else:
                        consultation_type = "in-person"
        
        # Get default cost from Acuity appointment type if available
        cost = 0
        if appointment_type_id:
            appointment_types_lookup = acuity_service.get_appointment_types_map()
            if appointment_types_lookup:
                appointment_type_info = appointment_types_lookup.get(str(appointment_type_id))
                if appointment_type_info and appointment_type_info.get("price"):
                    try:
                        cost = float(appointment_type_info.get("price"))
                    except (TypeError, ValueError):
                        cost = 0
        
        # Get location for in-person appointments
        location_for_db = None
        if consultation_type == "in-person" and doctor_address:
            location_for_db = doctor_address
        
        # Create or update appointment
        if existing_appointment:
            # Update existing appointment
            existing_appointment.scheduled_at = scheduled_at or existing_appointment.scheduled_at
            existing_appointment.status = "SCHEDULED"
            existing_appointment.consultation_type = consultation_type
            existing_appointment.notes = payload.notes or existing_appointment.notes
            existing_appointment.acuity_calendar_id = payload.calendarID
            existing_appointment.acuity_appointment_type_id = str(appointment_type_id) if appointment_type_id else None
            existing_appointment.location = location_for_db
            appointment = existing_appointment
            logger.info(f"Updated existing appointment {existing_appointment.id} for Acuity appointment {payload.id}")
        else:
            # Create new appointment
            appointment = Appointment(
                patient_id=patient.id,
                professional_id=professional.id,
                consultation_type=consultation_type,
                scheduled_at=scheduled_at or datetime.utcnow(),
                duration_minutes=30,  # Default, could be fetched from Acuity
                timezone=payload.timezone or payload.calendarTimezone or "UTC",
                status="SCHEDULED",
                cost=cost,
                currency="USD",
                payment_status="PENDING",
                acuity_appointment_id=payload.id,
                acuity_calendar_id=payload.calendarID,
                acuity_appointment_type_id=str(appointment_type_id) if appointment_type_id else None,
                location=location_for_db,
                notes=payload.notes,
                created_by=patient.id
            )
            db.add(appointment)
            db.flush()  # Get the appointment ID
        
        # virtual_meeting_url is already set from existing_appointment if it exists
        
        # Create Daily.co room if virtual appointment
        logger.info(f"Checking if appointment is virtual: is_virtual={is_virtual}, consultation_type={consultation_type}")
        if is_virtual and consultation_type == "virtual" and not virtual_meeting_url:
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
                    virtual_meeting_url = room_data.get("room_url")
                    appointment.virtual_meeting_url = virtual_meeting_url
                    logger.info(f"✅ Created Daily.co room for appointment {appointment.id}: url={virtual_meeting_url}")
                else:
                    logger.warning(f"⚠️ Daily.co room creation returned None for appointment {appointment.id}")
            except Exception as e:
                logger.error(f"❌ Error creating Daily.co room for appointment {appointment.id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue without video room - appointment still created
        else:
            logger.info(f"Skipping Daily.co room creation: is_virtual={is_virtual}, consultation_type={consultation_type}")
        
        # Check if appointment is completed (past datetime) and delete Daily.co room
        if scheduled_at and scheduled_at < datetime.utcnow():
            # Appointment is in the past, mark as completed and delete room if virtual
            if consultation_type == "virtual":
                room_name_to_delete = None
                if appointment.acuity_appointment_id:
                    room_name_to_delete = f"appointment-{appointment.acuity_appointment_id}"
                
                if room_name_to_delete:
                    try:
                        deleted = daily_service.delete_room(room_name_to_delete)
                        if deleted:
                            logger.info(f"✅ Deleted Daily.co room for completed appointment: {room_name_to_delete}")
                        else:
                            logger.warning(f"⚠️ Failed to delete Daily.co room for completed appointment: {room_name_to_delete}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting Daily.co room for completed appointment {room_name_to_delete}: {e}")
            
            # Update status to completed
            appointment.status = "COMPLETED"
        
        db.commit()
        db.refresh(appointment)
        
        # Send confirmation emails for new appointments only
        if not existing_appointment:
            try:
                # Get patient and professional names (already fetched above for Daily.co room)
                patient_name = f"{payload.firstName or ''} {payload.lastName or ''}".strip()
                if not patient_name:
                    patient_profile = await supabase_service.get_user_profile(patient.supabase_user_id)
                    patient_name = patient_profile.get("full_name", "Patient") if patient_profile else "Patient"
                
                professional_name = "Doctor"
                if professional.supabase_user_id:
                    professional_profile = await doctor_supabase_service.get_doctor_profile(professional.supabase_user_id)
                    professional_name = professional_profile.get("full_name", "Doctor") if professional_profile else "Doctor"
                
                # Format appointment datetime for email display
                try:
                    if scheduled_at:
                        formatted_datetime = scheduled_at.strftime("%B %d, %Y at %I:%M %p")
                    else:
                        formatted_datetime = payload.datetime or "TBD"
                except:
                    formatted_datetime = payload.datetime or "TBD"
                
                # Get location address from appointment or doctor profile
                location_address = appointment.location if appointment.location else doctor_address
                
                # Send email to patient
                if patient.email:
                    send_appointment_confirmation_email(
                        email=patient.email,
                        patient_name=patient_name,
                        doctor_name=professional_name,
                        appointment_datetime=formatted_datetime,
                        consultation_type=consultation_type,
                        location=location_address if consultation_type == "in-person" else None,
                        phone=payload.phone if consultation_type == "phone" else None,
                        virtual_meeting_url=appointment.virtual_meeting_url,
                        note=payload.notes,
                        is_doctor_email=False
                    )
                
                # Send email to doctor
                if professional.email:
                    send_appointment_confirmation_email(
                        email=professional.email,
                        patient_name=patient_name,
                        doctor_name=professional_name,
                        appointment_datetime=formatted_datetime,
                        consultation_type=consultation_type,
                        location=location_address if consultation_type == "in-person" else None,
                        phone=payload.phone if consultation_type == "phone" else None,
                        virtual_meeting_url=appointment.virtual_meeting_url,
                        note=payload.notes,
                        is_doctor_email=True
                    )
            except Exception as email_error:
                logger.error(f"Failed to send confirmation emails for appointment {appointment.id}: {email_error}")
                # Don't fail the webhook if email sending fails
        
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
        # Validate that appointment_type_id belongs to the calendar if provided
        effective_type_id = 0
        if appointment_type_id and appointment_type_id > 0:
            # Get appointment types for this calendar
            appointment_types = acuity_service.get_appointment_types_for_calendar(calendar_id)
            type_ids = [str(apt_type.get("id") or apt_type.get("appointmentTypeID")) for apt_type in appointment_types]
            if str(appointment_type_id) not in type_ids:
                logger.warning(
                    f"Appointment type {appointment_type_id} does not belong to calendar {calendar_id}. "
                    f"Available types: {type_ids}. Using default appointment type."
                )
                # Use default (0) if invalid
                effective_type_id = 0
            else:
                effective_type_id = appointment_type_id
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
        # Validate that appointment_type_id belongs to the calendar if provided
        effective_type_id = None
        if appointment_type_id and appointment_type_id > 0:
            # Get appointment types for this calendar
            appointment_types = acuity_service.get_appointment_types_for_calendar(calendar_id)
            type_ids = [str(apt_type.get("id") or apt_type.get("appointmentTypeID")) for apt_type in appointment_types]
            if str(appointment_type_id) not in type_ids:
                logger.warning(
                    f"Appointment type {appointment_type_id} does not belong to calendar {calendar_id}. "
                    f"Available types: {type_ids}. Using no appointment type filter."
                )
                # Don't use the invalid appointment type ID
                effective_type_id = None
            else:
                effective_type_id = appointment_type_id
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

        # Validate that appointment_type_id belongs to the calendar if provided
        effective_type_id = None
        if appointment_type_id and appointment_type_id > 0:
            # Get appointment types for this calendar
            appointment_types = acuity_service.get_appointment_types_for_calendar(calendar_id)
            type_ids = [str(apt_type.get("id") or apt_type.get("appointmentTypeID")) for apt_type in appointment_types]
            if str(appointment_type_id) not in type_ids:
                logger.warning(
                    f"Appointment type {appointment_type_id} does not belong to calendar {calendar_id}. "
                    f"Available types: {type_ids}. Using no appointment type filter."
                )
                # Don't use the invalid appointment type ID
                effective_type_id = None
            else:
                effective_type_id = appointment_type_id
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
        virtual_meeting_url = None
        effective_appointment_type_id = appointment.appointment_type_id
        
        # Determine appointment type ID if not provided
        if not effective_appointment_type_id:
            effective_appointment_type_id = acuity_service.get_default_appointment_type_id()
        
        # Get appointment type info to determine category (Virtual, Phone, or Person)
        appointment_category = "Person"  # default
        if effective_appointment_type_id:
            appointment_types_lookup = acuity_service.get_appointment_types_map()
            if appointment_types_lookup:
                appointment_type_info = appointment_types_lookup.get(str(effective_appointment_type_id))
                if appointment_type_info:
                    appointment_category = appointment_type_info.get("category", "Person")
                    logger.info(f"Appointment type {effective_appointment_type_id} has category: {appointment_category}")
        
        # Normalize category to lowercase for comparison
        category_lower = appointment_category.lower() if appointment_category else "person"

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
            fields=None  # No longer using custom fields
        )
        
        if not acuity_appointment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create appointment in Acuity"
            )
        
        # Get Acuity appointment ID for room creation
        acuity_appointment_id = str(acuity_appointment.get("id", ""))
        
        # Get doctor name, email, and address from calendar ID
        doctor_name = "Doctor"
        doctor_email = None
        doctor_address = None
        try:
            # Find doctor by calendar ID
            doctor_id = await doctor_supabase_service.get_doctor_id_by_calendar_id(appointment.calendar_id)
            if doctor_id:
                # Get doctor profile for name and address
                profile_response = supabase_service.client.table("doctor_profiles").select("full_name,address").eq("id", doctor_id).limit(1).execute()
                if profile_response.data:
                    doctor_name = profile_response.data[0].get("full_name", doctor_name)
                    doctor_address = profile_response.data[0].get("address")
                
                # Get doctor's Supabase user_id to find the User record
                supabase_user_id = await doctor_supabase_service.get_supabase_user_id_by_doctor_id(doctor_id)
                if supabase_user_id:
                    # Find the User record to get email
                    professional = db.query(User).filter(
                        User.role == "doctor",
                        User.supabase_user_id == supabase_user_id
                    ).first()
                    if professional and professional.email:
                        doctor_email = professional.email
                        logger.info(f"Found doctor email: {doctor_email} for calendar {appointment.calendar_id}")
        except Exception as e:
            logger.warning(f"Could not fetch doctor information for calendar {appointment.calendar_id}: {e}")
        
        # Handle virtual appointments - create Daily.co room AFTER getting Acuity appointment ID
        # Check category from appointment type (Virtual, Phone, Person)
        is_virtual = category_lower == "virtual"
        is_phone = category_lower == "phone"
        
        if is_virtual:
            try:
                # Get patient information
                patient_profile = await supabase_service.get_user_profile(current_user.supabase_user_id)
                patient_name = patient_profile.get("full_name", f"{appointment.first_name} {appointment.last_name}") if patient_profile else f"{appointment.first_name} {appointment.last_name}"
                
                # Parse datetime for Daily.co room creation
                apt_datetime = date_parser.parse(appointment.datetime)
                
                # Get duration from appointment type or default to 30 minutes
                duration_minutes = 30
                if effective_appointment_type_id:
                    appointment_types_lookup = acuity_service.get_appointment_types_map()
                    if appointment_types_lookup:
                        appointment_type_info = appointment_types_lookup.get(str(effective_appointment_type_id))
                        if appointment_type_info and appointment_type_info.get("duration"):
                            try:
                                duration_minutes = int(appointment_type_info.get("duration"))
                            except (TypeError, ValueError):
                                duration_minutes = 30
                
                # Create Daily.co room using Acuity appointment ID
                room_data = daily_service.create_room(
                    acuity_appointment_id=acuity_appointment_id,
                    patient_name=patient_name,
                    professional_name=doctor_name,
                    scheduled_time=apt_datetime,
                    duration_minutes=duration_minutes
                )
                
                if room_data and room_data.get("room_url"):
                    virtual_meeting_url = room_data.get("room_url")
                    logger.info(f"Created Daily.co room: {virtual_meeting_url}")
            except Exception as e:
                logger.error(f"Error creating Daily.co room: {e}")
                # Continue without video room - appointment still created
        
        # Format appointment datetime for email display
        try:
            apt_dt = date_parser.parse(appointment_datetime)
            formatted_datetime = apt_dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            formatted_datetime = appointment_datetime
        
        # Send confirmation emails to both patient and doctor
        patient_name = f"{appointment.first_name} {appointment.last_name}"
        
        # Map category to consultation_type for email (backward compatibility)
        consultation_type_for_email = "in-person"  # default
        if is_virtual:
            consultation_type_for_email = "virtual"
        elif is_phone:
            consultation_type_for_email = "phone"
        
        # Send email to patient
        send_appointment_confirmation_email(
            email=appointment.email,
            patient_name=patient_name,
            doctor_name=doctor_name,
            appointment_datetime=formatted_datetime,
            consultation_type=consultation_type_for_email,
            location=None,
            phone=appointment.phone if is_phone else None,
            virtual_meeting_url=virtual_meeting_url,
            note=appointment.note,
            is_doctor_email=False
        )
        
        # Send email to doctor if email is available
        if doctor_email:
            send_appointment_confirmation_email(
                email=doctor_email,
                patient_name=patient_name,
                doctor_name=doctor_name,
                appointment_datetime=formatted_datetime,
                consultation_type=consultation_type_for_email,
                location=None,
                phone=appointment.phone if is_phone else None,
                virtual_meeting_url=virtual_meeting_url,
                note=appointment.note,
                is_doctor_email=True
            )
        else:
            logger.warning(f"Doctor email not found for calendar {appointment.calendar_id}, skipping doctor notification email")
        
        # Save appointment to database
        try:
            # Find professional (doctor) by calendar ID
            professional = None
            doctor_id = await doctor_supabase_service.get_doctor_id_by_calendar_id(appointment.calendar_id)
            if doctor_id:
                supabase_user_id = await doctor_supabase_service.get_supabase_user_id_by_doctor_id(doctor_id)
                if supabase_user_id:
                    professional = db.query(User).filter(
                        User.role == "doctor",
                        User.supabase_user_id == supabase_user_id
                    ).first()
            
            if not professional:
                logger.warning(f"Professional not found for calendar {appointment.calendar_id}, skipping DB save")
            else:
                # Location is not required - we get it from Acuity if needed
                if True:
                    # Get cost from Acuity appointment type
                    cost = 0
                    if effective_appointment_type_id:
                        appointment_types_lookup = acuity_service.get_appointment_types_map()
                        if appointment_types_lookup:
                            appointment_type_info = appointment_types_lookup.get(str(effective_appointment_type_id))
                            if appointment_type_info and appointment_type_info.get("price"):
                                try:
                                    cost = float(appointment_type_info.get("price"))
                                except (TypeError, ValueError):
                                    cost = 0
                    
                    if True:  # Always create appointment if we have professional and location
                            # Parse scheduled_at datetime
                            scheduled_at = datetime.utcnow()
                            try:
                                scheduled_at = date_parser.parse(appointment_datetime)
                            except:
                                pass
                            
                            # Get duration from appointment type
                            duration_minutes = 30
                            if effective_appointment_type_id:
                                appointment_types_lookup = acuity_service.get_appointment_types_map()
                                if appointment_types_lookup:
                                    appointment_type_info = appointment_types_lookup.get(str(effective_appointment_type_id))
                                    if appointment_type_info and appointment_type_info.get("duration"):
                                        try:
                                            duration_minutes = int(appointment_type_info.get("duration"))
                                        except (TypeError, ValueError):
                                            duration_minutes = 30
                            
                            # Map category to consultation_type
                            consultation_type_db = "in-person"
                            if is_virtual:
                                consultation_type_db = "virtual"
                            elif is_phone:
                                consultation_type_db = "phone"
                            
                            # Create or update appointment in DB
                            existing_db_appointment = db.query(Appointment).filter(
                                Appointment.acuity_appointment_id == acuity_appointment_id
                            ).first()
                            
                            # Get doctor address for location field
                            doctor_address_for_db = None
                            if consultation_type_db == "in-person" and doctor_address:
                                doctor_address_for_db = doctor_address
                            
                            if existing_db_appointment:
                                # Update existing
                                existing_db_appointment.scheduled_at = scheduled_at
                                existing_db_appointment.duration_minutes = duration_minutes
                                existing_db_appointment.consultation_type = consultation_type_db
                                existing_db_appointment.virtual_meeting_url = virtual_meeting_url
                                existing_db_appointment.acuity_appointment_type_id = str(effective_appointment_type_id) if effective_appointment_type_id else None
                                existing_db_appointment.location = doctor_address_for_db
                                existing_db_appointment.notes = appointment.note
                                existing_db_appointment.status = "SCHEDULED"
                                db.commit()
                                logger.info(f"Updated DB appointment {existing_db_appointment.id} for Acuity appointment {acuity_appointment_id}")
                            else:
                                # Create new
                                db_appointment = Appointment(
                                    patient_id=current_user.id,
                                    professional_id=professional.id,
                                    consultation_type=consultation_type_db,
                                    scheduled_at=scheduled_at,
                                    duration_minutes=duration_minutes,
                                    timezone=appointment.timezone or "UTC",
                                    status="SCHEDULED",
                                    cost=cost,
                                    currency="USD",
                                    payment_status="PENDING",
                                    acuity_appointment_id=acuity_appointment_id,
                                    acuity_calendar_id=appointment.calendar_id,
                                    acuity_appointment_type_id=str(effective_appointment_type_id) if effective_appointment_type_id else None,
                                    virtual_meeting_url=virtual_meeting_url,
                                    location=doctor_address_for_db,
                                    notes=appointment.note,
                                    created_by=current_user.id
                                )
                                db.add(db_appointment)
                                db.commit()
                                logger.info(f"Created DB appointment {db_appointment.id} for Acuity appointment {acuity_appointment_id}")
        except Exception as e:
            logger.error(f"Error saving appointment to database: {e}", exc_info=True)
            # Don't fail the request if DB save fails - Acuity appointment is already created
        
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
        
        appointment_types_lookup = acuity_service.get_appointment_types_map()

        # Get DB appointments for virtual meeting URLs
        acuity_appointment_ids = [str(apt.get("id")) for apt in acuity_appointments if apt.get("id")]
        db_appointments = {}
        if acuity_appointment_ids:
            db_appts = db.query(Appointment).filter(
                Appointment.acuity_appointment_id.in_(acuity_appointment_ids)
            ).all()
            db_appointments = {str(apt.acuity_appointment_id): apt for apt in db_appts if apt.acuity_appointment_id}
        
        # Parse and enrich appointments
        # Collect all unique calendar IDs for bulk fetching
        unique_calendar_ids = set()
        for apt in acuity_appointments:
            calendar_id = apt.get("calendarID")
            if calendar_id:
                unique_calendar_ids.add(str(calendar_id))
        
        # Bulk fetch all doctor IDs by calendar IDs
        calendar_to_doctor_id: Dict[str, str] = {}
        if unique_calendar_ids:
            calendar_to_doctor_id = await doctor_supabase_service.get_doctor_ids_by_calendar_ids_bulk(list(unique_calendar_ids))
        
        # Collect all unique doctor IDs for bulk profile fetching
        unique_doctor_ids = set(calendar_to_doctor_id.values())
        
        # Bulk fetch all doctor profiles
        doctor_profiles_dict: Dict[str, Dict] = {}
        if unique_doctor_ids:
            # Use existing bulk method but we need to get profiles by doctor_id (UUID)
            # The get_doctor_profiles_bulk expects supabase_user_ids, but we have doctor_ids
            # So we'll use a direct query here
            try:
                client = supabase_service.client
                profile_response = client.table("doctor_profiles").select("id,full_name,specialty").in_("id", list(unique_doctor_ids)).execute()
                if profile_response.data:
                    for profile in profile_response.data:
                        doctor_id = profile.get("id")
                        if doctor_id:
                            doctor_profiles_dict[doctor_id] = profile
            except Exception as e:
                logger.error(f"Error bulk fetching doctor profiles: {e}", exc_info=True)
        
        result = []
        for apt in acuity_appointments:
            acuity_appt_id = str(apt.get("id", ""))
            
            # Get virtual meeting URL and location from DB instead of Acuity custom fields
            virtual_meeting_url = None
            location_address = None
            db_appointment = db_appointments.get(acuity_appt_id)
            if db_appointment:
                virtual_meeting_url = db_appointment.virtual_meeting_url
                location_address = db_appointment.location
            
            # Get phone from Acuity appointment data
            phone_number = apt.get("phone")
            
            # Get consultation type from appointment type category
            consultation_type = "in-person"  # default
            appointment_type_id = apt.get("appointmentTypeID")
            if appointment_type_id and appointment_types_lookup:
                appointment_type_info = appointment_types_lookup.get(str(appointment_type_id))
                if appointment_type_info:
                    category = appointment_type_info.get("category", "Person")
                    category_lower = category.lower() if category else "person"
                    if category_lower == "virtual":
                        consultation_type = "virtual"
                    elif category_lower == "phone":
                        consultation_type = "phone"
                    else:
                        consultation_type = "in-person"
            
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
            
            # Get doctor information from calendar ID (using bulk-fetched data)
            calendar_id = apt.get("calendarID")
            doctor_name = "Unknown Doctor"
            doctor_specialty = None
            timezone = apt.get("timezone") or apt.get("calendarTimezone")

            if calendar_id:
                calendar_id_str = str(calendar_id)
                doctor_id = calendar_to_doctor_id.get(calendar_id_str)
                if doctor_id:
                    profile = doctor_profiles_dict.get(doctor_id)
                    if profile:
                        doctor_name = profile.get("full_name", doctor_name)
                        doctor_specialty = profile.get("specialty")

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
            appointment_type_info = appointment_types_lookup.get(str(appointment_type_id)) if appointment_type_id is not None else None

            appointment_type_price = None
            if appointment_type_info:
                price_value = appointment_type_info.get("price")
                if price_value is not None:
                    try:
                        appointment_type_price = float(price_value)
                    except (TypeError, ValueError):
                        appointment_type_price = None

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

            if price_value is None and appointment_type_price is not None:
                price_value = appointment_type_price

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
                "confirmation_page": apt.get("confirmationPage"),  # Acuity confirmation/reschedule/cancel page
                # Video meeting fields
                "virtual_meeting_url": virtual_meeting_url,
                "consultation_type": consultation_type,
                # Doctor information
                "doctor_name": doctor_name,
                "doctor_specialty": doctor_specialty,
                "timezone": timezone,
                "cost": price_value,
                "amount_paid": amount_paid_value,
                "is_paid": apt.get("paid") == "yes",
                "appointment_type_id": appointment_type_id,
                "appointment_type_name": appointment_type_info.get("name") if appointment_type_info else None,
                "appointment_type_duration": appointment_type_info.get("duration") if appointment_type_info else None,
                "appointment_type_price": appointment_type_price,
                # Phone and location for display
                "phone": phone_number,
                "location": location_address,
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

    if appointment_data.appointment_type_id is not None:
        updates["appointmentTypeID"] = appointment_data.appointment_type_id

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


@router.options("/{appointment_id}/phone")
async def options_update_appointment_phone():
    """Handle OPTIONS preflight request for PATCH endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
    )


@router.patch("/{appointment_id}/phone")
async def update_appointment_phone(
    appointment_id: str,
    phone_data: AppointmentPhoneUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update phone number for an appointment in Acuity.
    """
    try:
        # Get appointment from local DB to verify access
        appointment = db.query(Appointment).filter(
            Appointment.acuity_appointment_id == appointment_id
        ).first()
        
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
        
        # Update phone number in Acuity
        updates = {"phone": phone_data.phone}
        acuity_response = acuity_service.update_appointment(appointment_id, updates)
        
        if acuity_response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update appointment phone number in Acuity."
            )
        
        return {
            "message": "Phone number updated successfully",
            "appointment": acuity_response
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment phone number: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update phone number: {str(e)}"
        )


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