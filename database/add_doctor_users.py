#!/usr/bin/env python3
"""
Script to add doctor user records to the main database.
These records link to doctor profiles in the separate Supabase project via supabase_user_id.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file BEFORE importing app modules
from dotenv import load_dotenv

# Get the project root directory (parent of database folder)
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

# Load .env file if it exists
if env_file.exists():
    load_dotenv(env_file, override=True)
    print(f"✅ Loaded environment variables from {env_file}")
else:
    print(f"⚠️  Warning: .env file not found at {env_file}")
    print("   Attempting to load from environment variables...")
    # Try loading from project root if script is run from different directory
    load_dotenv(override=True)

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(project_root))

from app.core.database import get_db
from app.models.user import User, UserRole
from app.crud.user import user_crud

# Doctor data from Supabase profiles
DOCTORS = [
    {
        "supabase_user_id": "7a69a0da-95e0-457c-be8b-b2a4f4d52142",
        "email": "okisahandsome@gmail.com",
        "name": "Dr. Sarah Johnson",
        "specialty": "Cardiology",
    },
    {
        "supabase_user_id": "89dd4d34-2dda-49ae-a68a-8931ab662fc1",
        "email": "krystian.djk@gmail.com",
        "name": "Dr. Michael Chen",
        "specialty": "Dermatology",
    },
    {
        "supabase_user_id": "973ab625-08d0-4f15-aae7-6dbdad0c1233",
        "email": "kdajka98@gmail.com",
        "name": "Dr. Emily Rodriguez",
        "specialty": "Pediatrics",
    },
    {
        "supabase_user_id": "9816f018-9f17-40fe-9389-09cc835d3c97",
        "email": "mariankugiel819@gmail.com",
        "name": "Dr. James Wilson",
        "specialty": "Orthopedic Surgery",
    },
    {
        "supabase_user_id": "9e7500be-7a02-40aa-b991-62f740e1e4fe",
        "email": "yourhealth1place@gmail.com",
        "name": "Dr. Lisa Anderson",
        "specialty": "Psychiatry",
    },
    {
        "supabase_user_id": "acc6b520-7ff6-4719-b1ce-762e4abf339a",
        "email": "damian.nowa@gmail.com",
        "name": "Dr. Robert Taylor",
        "specialty": "General Practice",
    },
]


def main():
    """Add doctor users to the main database"""
    db = next(get_db())
    
    try:
        created_count = 0
        error_count = 0
        
        for doctor_data in DOCTORS:
            # Try to create new user record - attempt creation for all records
            # Database will enforce unique constraints (email, supabase_user_id)
            try:
                user_data = {
                    "supabase_user_id": doctor_data["supabase_user_id"],
                    "email": doctor_data["email"],
                    "role": UserRole.DOCTOR,
                    "is_active": True,
                }
                
                new_user = user_crud.create(db, user_data)
                print(f"✅ Created doctor user: {doctor_data['name']} (ID: {new_user.id}, Email: {doctor_data['email']}, Supabase ID: {doctor_data['supabase_user_id']})")
                created_count += 1
            except Exception as e:
                # Log error but continue processing other records
                # Database constraint violations will be logged but won't stop the script
                from sqlalchemy.exc import IntegrityError
                
                if isinstance(e, IntegrityError):
                    print(f"⚠️  Constraint violation for {doctor_data['name']}: {str(e)}")
                else:
                    print(f"❌ Error creating doctor user {doctor_data['name']}: {e}")
                
                error_count += 1
                db.rollback()  # Rollback the failed transaction and continue
        
        print(f"\n📊 Summary:")
        print(f"   Created: {created_count}")
        print(f"   Errors: {error_count}")
        print(f"   Total: {len(DOCTORS)}")
        print(f"\n✅ Doctor users processing completed!")
        
    except Exception as e:
        print(f"❌ Error adding doctor users: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

