#!/usr/bin/env python3
"""
Seed script for Thryve data types
Reads from Thryve_data_types.csv and populates the database
"""
import csv
import sys
import os
from pathlib import Path
from typing import Dict, List

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
from app.models.thryve_data_type import ThryveDataType, ThryveDailyEpoch
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verify DATABASE_URL is loaded
if "username" in settings.DATABASE_URL or "password" in settings.DATABASE_URL:
    logger.warning("⚠️  DATABASE_URL appears to have placeholder values. Please check your .env file.")
    logger.warning(f"   Current DATABASE_URL: {settings.DATABASE_URL.split('@')[0]}@...")
else:
    logger.info(f"✅ Database connection configured (host: {settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'unknown'})")

# Platform columns from CSV (excluding dataTypeId, name, category, type, description, unit, valueType)
PLATFORM_COLUMNS = [
    "Fitbit", "Garmin", "Polar", "AppleHealth", "SamsungHealth", "Withings",
    "Strava", "GoogleFitREST", "OmronConnect", "Suunto", "Oura", "iHealth",
    "Beurer", "HuaweiHealth", "GoogleFitNative", "Dexcom", "Whoop", "Decathlon",
    "HealthConnect", "Komoot"
]


def parse_platform_support(row: Dict[str, str]) -> Dict[str, bool]:
    """Parse platform support columns into JSON object"""
    platform_support = {}
    for platform in PLATFORM_COLUMNS:
        value = row.get(platform, "").strip().lower()
        platform_support[platform] = value == "checked"
    return platform_support


def seed_thryve_data_types(db: Session) -> tuple[int, int]:
    """
    Seed Thryve data types from CSV file
    Returns: (created_count, updated_count)
    """
    csv_path = Path(__file__).parent / "Thryve_data_types.csv"
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return (0, 0)
    
    created_count = 0
    updated_count = 0
    
    try:
        # Try with utf-8-sig to handle BOM if present
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Debug: Print available keys if first row fails
            first_row = True
            for row in reader:
                if first_row:
                    logger.debug(f"CSV columns found: {list(row.keys())}")
                    first_row = False
                
                # Handle potential BOM or whitespace in column names
                row_clean = {k.strip(): v for k, v in row.items()}
                
                # Try different possible column name variations
                data_type_id_key = None
                for key in ['dataTypeId', 'DataTypeId', 'datatypeid', 'data_type_id']:
                    if key in row_clean:
                        data_type_id_key = key
                        break
                
                if not data_type_id_key:
                    logger.error(f"Could not find dataTypeId column. Available keys: {list(row_clean.keys())}")
                    raise KeyError(f"dataTypeId column not found. Available columns: {list(row_clean.keys())}")
                
                data_type_id = int(row_clean[data_type_id_key])
                name = row_clean.get('name', '').strip()
                category = row_clean.get('category', '').strip()
                type_str = row_clean.get('type', '').strip()  # "Daily" or "Epoch"
                description = row_clean.get('description', '').strip()
                unit = row_clean.get('unit', '').strip() or None
                value_type = row_clean.get('valueType', '').strip()
                
                # Convert type string to enum
                data_type_enum = ThryveDailyEpoch.DAILY if type_str.lower() == "daily" else ThryveDailyEpoch.EPOCH
                
                # Parse platform support (use cleaned row)
                platform_support = parse_platform_support(row_clean)
                
                # Check if data_type_id already exists (skip if found, regardless of type)
                existing = db.query(ThryveDataType).filter(
                    ThryveDataType.data_type_id == data_type_id
                ).first()
                
                if existing:
                    # Data type ID already exists, skip this entry
                    logger.debug(f"⏭️  Skipped (data_type_id exists): {name} (ID: {data_type_id}, Type: {type_str})")
                    continue
                
                # Create new - handle duplicates gracefully
                try:
                    new_type = ThryveDataType(
                        data_type_id=data_type_id,
                        name=name,
                        category=category,
                        type=data_type_enum,
                        description=description,
                        unit=unit,
                        value_type=value_type,
                        platform_support=platform_support,
                        is_active=True
                    )
                    db.add(new_type)
                    db.flush()  # Flush to check for duplicates before commit
                    created_count += 1
                    logger.debug(f"Created data type: {name} (ID: {data_type_id}, Type: {type_str})")
                except IntegrityError as e:
                    # Duplicate entry found (race condition), skip it
                    db.rollback()
                    logger.warning(f"⏭️  Skipped duplicate (IntegrityError): {name} (ID: {data_type_id}, Type: {type_str})")
                    continue
        
        # Commit all changes at once
        try:
            db.commit()
            logger.info(f"✅ Successfully seeded Thryve data types: {created_count} created, {updated_count} updated")
        except IntegrityError as e:
            db.rollback()
            logger.error(f"❌ Error committing changes: {e}")
            raise
        
        return (created_count, updated_count)
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error seeding Thryve data types: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    db = SessionLocal()
    try:
        created, updated = seed_thryve_data_types(db)
        print(f"Created: {created}, Updated: {updated}")
    finally:
        db.close()

