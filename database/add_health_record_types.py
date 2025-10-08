#!/usr/bin/env python3

from app.core.database import get_db
from app.models.health_record import HealthRecordType
from datetime import datetime

def main():
    db = next(get_db())
    
    # Check if health record type with ID 1 exists
    existing = db.query(HealthRecordType).filter(HealthRecordType.id == 1).first()
    if existing:
        print(f"Health record type with ID 1 already exists: {existing.name}")
        return
    
    # Create health record type with ID 1
    hrt = HealthRecordType(
        id=1,
        name='analysis',
        display_name='Analysis',
        description='Health analysis and AI insights',
        is_active=True,
        created_at=datetime.utcnow(),
        created_by=3  # Admin user ID
    )
    
    db.add(hrt)
    db.commit()
    print("Created health record type with ID 1: Analysis")
    
    # Also create other common health record types
    health_record_types = [
        (2, 'vitals', 'Vitals', 'Vital signs and measurements'),
        (3, 'body', 'Body Composition', 'Body composition measurements'),
        (4, 'lifestyle', 'Lifestyle', 'Lifestyle and behavioral data'),
        (5, 'exams', 'Exams', 'Medical examinations and tests')
    ]
    
    for id_val, name, display_name, description in health_record_types:
        existing = db.query(HealthRecordType).filter(HealthRecordType.id == id_val).first()
        if not existing:
            hrt = HealthRecordType(
                id=id_val,
                name=name,
                display_name=display_name,
                description=description,
                is_active=True,
                created_at=datetime.utcnow(),
                created_by=3  # Admin user ID
            )
            db.add(hrt)
            print(f"Created health record type with ID {id_val}: {display_name}")
    
    db.commit()
    print("All health record types created successfully!")

if __name__ == "__main__":
    main()
