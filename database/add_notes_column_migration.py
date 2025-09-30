#!/usr/bin/env python3
"""
Migration script to add notes column to health_record_images table
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def run_migration():
    """Add notes column to health_record_images table"""
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # Check if notes column already exists
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'health_record_images' 
                AND column_name = 'notes'
            """))
            
            if result.fetchone():
                print("✅ Notes column already exists in health_record_images table")
                return
            
            # Add notes column
            print("🔄 Adding notes column to health_record_images table...")
            db.execute(text("""
                ALTER TABLE health_record_images 
                ADD COLUMN notes TEXT
            """))
            
            db.commit()
            print("✅ Successfully added notes column to health_record_images table")
            
    except Exception as e:
        print(f"❌ Error adding notes column: {e}")
        raise

if __name__ == "__main__":
    run_migration()
