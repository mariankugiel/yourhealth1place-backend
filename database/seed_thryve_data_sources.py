#!/usr/bin/env python3
"""
Seed script for Thryve data sources
Reads from thryve_data_sources.csv and populates the database
"""
import csv
import sys
import os
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file in project root BEFORE importing app modules
from dotenv import load_dotenv
env_path = project_root / ".env"

# Load .env file if it exists
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️  Warning: .env file not found at {env_path}")
    print("   Attempting to load from environment variables...")
    # Try loading from project root if script is run from different directory
    load_dotenv(override=True)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.thryve_data_source import ThryveDataSource
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verify DATABASE_URL is loaded
if "username" in settings.DATABASE_URL or "password" in settings.DATABASE_URL:
    logger.warning("⚠️  DATABASE_URL appears to have placeholder values. Please check your .env file.")
    logger.warning(f"   Current DATABASE_URL: {settings.DATABASE_URL.split('@')[0]}@...")
else:
    logger.info(f"✅ Database connection configured (host: {settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'unknown'})")


def seed_thryve_data_sources(db: Session) -> tuple[int, int]:
    """
    Seed Thryve data sources from CSV file
    Returns: (created_count, updated_count)
    """
    csv_path = Path(__file__).parent / "thryve_data_sources.csv"
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return (0, 0)
    
    created_count = 0
    updated_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                data_source_id = int(row['id'])
                name = row['name']
                data_source_type = row['data_source_type']
                retrieval_method = row['retrieval_method']
                historic_data = row['historic_data'].lower() == 'yes'
                shared_oauth_client = row['shared_oauth_client']
                
                # Check if exists
                existing = db.query(ThryveDataSource).filter(
                    ThryveDataSource.id == data_source_id
                ).first()
                
                if existing:
                    # Update existing
                    existing.name = name
                    existing.data_source_type = data_source_type
                    existing.retrieval_method = retrieval_method
                    existing.historic_data = historic_data
                    existing.shared_oauth_client = shared_oauth_client
                    existing.is_active = True
                    updated_count += 1
                    logger.debug(f"Updated data source: {name} (ID: {data_source_id})")
                else:
                    # Create new - handle duplicates gracefully
                    try:
                        new_source = ThryveDataSource(
                            id=data_source_id,
                            name=name,
                            data_source_type=data_source_type,
                            retrieval_method=retrieval_method,
                            historic_data=historic_data,
                            shared_oauth_client=shared_oauth_client,
                            is_active=True
                        )
                        db.add(new_source)
                        db.flush()  # Flush to check for duplicates before commit
                        created_count += 1
                        logger.debug(f"Created data source: {name} (ID: {data_source_id})")
                    except IntegrityError as e:
                        # Duplicate entry found (race condition), skip it
                        db.rollback()
                        logger.warning(f"⏭️  Skipped duplicate (IntegrityError): {name} (ID: {data_source_id})")
                        continue
        
        # Commit all changes at once
        try:
            db.commit()
            logger.info(f"✅ Successfully seeded Thryve data sources: {created_count} created, {updated_count} updated")
        except IntegrityError as e:
            db.rollback()
            logger.error(f"❌ Error committing changes: {e}")
            raise
        
        return (created_count, updated_count)
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error seeding Thryve data sources: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    db = SessionLocal()
    try:
        created, updated = seed_thryve_data_sources(db)
        print(f"Created: {created}, Updated: {updated}")
    finally:
        db.close()

