"""
Message Integration Service
Handles integration between different systems (medication reminders, appointments, lab results) 
and the messages system
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.crud.message import MessageCRUD
from app.models.message import MessageType, MessagePriority, SenderType
from app.models.medication_reminder import MedicationReminder
from app.models.appointment import Appointment
from app.websocket.message_service import message_websocket_service
import logging

logger = logging.getLogger(__name__)

class MessageIntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self.message_crud = MessageCRUD(db)

    async def create_medication_reminder_message(
        self, 
        user_id: int, 
        medication_reminder: MedicationReminder,
        medication_name: str,
        dosage: str
    ) -> bool:
        """Create a medication reminder message"""
        try:
            # Create or get conversation with system
            conversation = self._get_or_create_system_conversation(user_id, "Medication Reminders")
            
            # Create message metadata
            metadata = {
                "medication_id": medication_reminder.medication_id,
                "medication_name": medication_name,
                "dosage": dosage,
                "scheduled_time": medication_reminder.reminder_time.isoformat(),
                "action_required": True,
                "action_url": f"/medications/{medication_reminder.medication_id}",
                "action_text": "Mark as Taken"
            }
            
            # Create message
            message_data = {
                "conversation_id": conversation.id,
                "content": f"Time to take your {medication_name} ({dosage})",
                "message_type": MessageType.MEDICATION_REMINDER,
                "priority": MessagePriority.HIGH,
                "metadata": metadata
            }
            
            message = self.message_crud.create_message(message_data, user_id)
            
            # Broadcast via WebSocket
            await message_websocket_service.broadcast_medication_reminder(user_id, metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating medication reminder message: {e}")
            return False

    async def create_appointment_reminder_message(
        self, 
        user_id: int, 
        appointment: Appointment,
        doctor_name: str,
        location: str
    ) -> bool:
        """Create an appointment reminder message"""
        try:
            # Create or get conversation with system
            conversation = self._get_or_create_system_conversation(user_id, "Appointment Reminders")
            
            # Create message metadata
            metadata = {
                "appointment_id": str(appointment.id),
                "appointment_date": appointment.appointment_time.isoformat(),
                "doctor_name": doctor_name,
                "location": location,
                "action_required": True,
                "action_url": f"/appointments/{appointment.id}",
                "action_text": "Confirm Appointment"
            }
            
            # Create message
            message_data = {
                "conversation_id": conversation.id,
                "content": f"Reminder: You have an appointment with {doctor_name} on {appointment.appointment_time.strftime('%B %d, %Y at %I:%M %p')}",
                "message_type": MessageType.APPOINTMENT_REMINDER,
                "priority": MessagePriority.HIGH,
                "metadata": metadata
            }
            
            message = self.message_crud.create_message(message_data, user_id)
            
            # Broadcast via WebSocket
            await message_websocket_service.broadcast_appointment_reminder(user_id, metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating appointment reminder message: {e}")
            return False

    async def create_lab_results_message(
        self, 
        user_id: int, 
        lab_result_id: str,
        test_name: str,
        is_abnormal: bool = False
    ) -> bool:
        """Create a lab results message"""
        try:
            # Create or get conversation with system
            conversation = self._get_or_create_system_conversation(user_id, "Lab Results")
            
            # Create message metadata
            metadata = {
                "lab_result_id": lab_result_id,
                "test_name": test_name,
                "result_date": datetime.utcnow().isoformat(),
                "is_abnormal": is_abnormal,
                "action_required": is_abnormal,
                "action_url": f"/lab-results/{lab_result_id}",
                "action_text": "View Results" if not is_abnormal else "Schedule Follow-up"
            }
            
            # Create message content based on results
            if is_abnormal:
                content = f"Your {test_name} results are available and show abnormal values. Please review and consider scheduling a follow-up with your doctor."
                priority = MessagePriority.URGENT
            else:
                content = f"Your {test_name} results are available and show normal values."
                priority = MessagePriority.NORMAL
            
            # Create message
            message_data = {
                "conversation_id": conversation.id,
                "content": content,
                "message_type": MessageType.LAB_RESULTS,
                "priority": priority,
                "metadata": metadata
            }
            
            message = self.message_crud.create_message(message_data, user_id)
            
            # Broadcast via WebSocket
            await message_websocket_service.broadcast_lab_results(user_id, metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating lab results message: {e}")
            return False

    async def create_health_plan_support_message(
        self, 
        user_id: int, 
        support_ticket_id: Optional[str],
        category: str,
        content: str,
        action_required: bool = False,
        action_url: Optional[str] = None
    ) -> bool:
        """Create a health plan support message"""
        try:
            # Create or get conversation with support
            conversation = self._get_or_create_system_conversation(user_id, "Health Plan Support")
            
            # Create message metadata
            metadata = {
                "support_ticket_id": support_ticket_id,
                "category": category,
                "action_required": action_required,
                "action_url": action_url,
                "action_text": "View Details" if action_url else None
            }
            
            # Create message
            message_data = {
                "conversation_id": conversation.id,
                "content": content,
                "message_type": MessageType.HEALTH_PLAN_SUPPORT,
                "priority": MessagePriority.NORMAL,
                "metadata": metadata
            }
            
            message = self.message_crud.create_message(message_data, user_id)
            
            # Broadcast via WebSocket
            await message_websocket_service.send_to_user(user_id, {
                "type": "health_plan_support",
                "data": {
                    "support_ticket_id": support_ticket_id,
                    "category": category,
                    "content": content,
                    "action_required": action_required,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating health plan support message: {e}")
            return False

    async def create_system_announcement(
        self, 
        user_ids: list, 
        title: str,
        content: str,
        priority: str = "normal",
        action_required: bool = False,
        action_url: Optional[str] = None
    ) -> bool:
        """Create a system announcement for multiple users"""
        try:
            announcement_data = {
                "title": title,
                "content": content,
                "priority": priority,
                "action_required": action_required,
                "action_url": action_url
            }
            
            # Create messages for each user
            for user_id in user_ids:
                conversation = self._get_or_create_system_conversation(user_id, "System Announcements")
                
                message_data = {
                    "conversation_id": conversation.id,
                    "content": f"{title}\n\n{content}",
                    "message_type": MessageType.SYSTEM_ANNOUNCEMENT,
                    "priority": MessagePriority.HIGH if priority == "high" else MessagePriority.NORMAL,
                    "metadata": {
                        "title": title,
                        "action_required": action_required,
                        "action_url": action_url
                    }
                }
                
                self.message_crud.create_message(message_data, user_id)
            
            # Broadcast to all users
            await message_websocket_service.broadcast_system_announcement(user_ids, announcement_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating system announcement: {e}")
            return False

    def _get_or_create_system_conversation(self, user_id: int, conversation_name: str):
        """Get or create a system conversation for a user"""
        # Look for existing system conversation
        conversations = self.message_crud.get_conversations_by_user(user_id)
        
        for conversation in conversations:
            if (conversation.contact_type == SenderType.SYSTEM and 
                conversation.contact_name == conversation_name):
                return conversation
        
        # Create new system conversation
        conversation_data = {
            "contact_id": 0,  # System user
            "contact_name": conversation_name,
            "contact_role": "System",
            "contact_avatar": None,
            "contact_type": SenderType.SYSTEM,
            "tags": ["system"]
        }
        
        return self.message_crud.create_conversation(conversation_data, user_id)

    async def handle_medication_action(
        self, 
        user_id: int, 
        message_id: int, 
        action: str,
        medication_id: int
    ) -> bool:
        """Handle medication action (taken, snooze)"""
        try:
            # Create action record
            action_data = {
                "action": action,
                "medication_id": medication_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.message_crud.create_message_action(message_id, user_id, action, action_data)
            
            # Update medication reminder if needed
            if action == "taken":
                # Mark medication as taken in the medication system
                # This would integrate with your medication tracking system
                pass
            elif action == "snooze":
                # Snooze the medication reminder
                # This would integrate with your reminder system
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling medication action: {e}")
            return False

    async def handle_appointment_action(
        self, 
        user_id: int, 
        message_id: int, 
        action: str,
        appointment_id: int
    ) -> bool:
        """Handle appointment action (confirm, reschedule, cancel)"""
        try:
            # Create action record
            action_data = {
                "action": action,
                "appointment_id": appointment_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.message_crud.create_message_action(message_id, user_id, action, action_data)
            
            # Update appointment status if needed
            # This would integrate with your appointment system
            if action == "confirm":
                pass
            elif action == "reschedule":
                pass
            elif action == "cancel":
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling appointment action: {e}")
            return False
