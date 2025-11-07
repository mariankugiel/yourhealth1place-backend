from sqlalchemy.orm import Session
from app.models.health_record import HealthRecordType
from app.models.user import User, UserRole
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def init_health_record_types(db: Session, force: bool = False):
    """
    Initialize health record types if they don't exist.
    
    This function ensures all required health record types are available in the database.
    It's idempotent - safe to run multiple times.
    
    Args:
        db: Database session
        force: If True, update existing records. If False, only create missing ones.
    
    Returns:
        tuple: (created_count, updated_count) - Number of records created and updated
    """
    try:
        # Get admin user (or use first user if no admin exists)
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        
        if not admin_user:
            any_user = db.query(User).first()
            if not any_user:
                logger.warning("No users found in database. Cannot create health record types.")
                return (0, 0)
            admin_id = any_user.id
            logger.info(f"No admin user found. Using user {admin_id} as creator for health record types.")
        else:
            admin_id = admin_user.id
        
        # Define required health record types
        # These are essential system types that must exist for the app to function
        health_record_types = [
            {
                "id": 1,
                "name": "analysis",
                "display_name": "Analysis",
                "description": "Health analysis and AI insights",
                "is_active": True
            },
            {
                "id": 2,
                "name": "vitals",
                "display_name": "Vitals",
                "description": "Vital signs and measurements",
                "is_active": True
            },
            {
                "id": 3,
                "name": "body",
                "display_name": "Body Composition",
                "description": "Body composition measurements",
                "is_active": True
            },
            {
                "id": 4,
                "name": "lifestyle",
                "display_name": "Lifestyle",
                "description": "Lifestyle and behavioral data",
                "is_active": True
            },
            {
                "id": 5,
                "name": "exams",
                "display_name": "Exams",
                "description": "Medical examinations and tests",
                "is_active": True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for type_data in health_record_types:
            # Check if type already exists
            existing = db.query(HealthRecordType).filter(
                HealthRecordType.id == type_data["id"]
            ).first()
            
            if not existing:
                # Create new health record type
                hrt = HealthRecordType(
                    id=type_data["id"],
                    name=type_data["name"],
                    display_name=type_data["display_name"],
                    description=type_data["description"],
                    is_active=type_data["is_active"],
                    created_at=datetime.utcnow(),
                    created_by=admin_id
                )
                db.add(hrt)
                created_count += 1
                logger.info(f"✓ Created health record type: {type_data['display_name']} (ID: {type_data['id']})")
            elif force:
                # Update existing record (if force=True)
                existing.display_name = type_data["display_name"]
                existing.description = type_data["description"]
                existing.is_active = type_data["is_active"]
                existing.updated_at = datetime.utcnow()
                if hasattr(existing, 'updated_by'):
                    existing.updated_by = admin_id
                updated_count += 1
                logger.info(f"✓ Updated health record type: {type_data['display_name']} (ID: {type_data['id']})")
            else:
                logger.debug(f"Health record type {type_data['display_name']} (ID: {type_data['id']}) already exists")
        
        if created_count > 0 or updated_count > 0:
            db.commit()
            logger.info(f"Initialized health record types: {created_count} created, {updated_count} updated")
        else:
            logger.debug("All health record types already exist - no changes needed")
        
        return (created_count, updated_count)
            
    except Exception as e:
        logger.error(f"Failed to initialize health record types: {e}", exc_info=True)
        db.rollback()
        # Return counts but don't raise - allow app to start even if initialization fails
        return (0, 0)

