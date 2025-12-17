#!/usr/bin/env python3
"""
Script to update thryve_type column for existing metric templates from CSV.
This script only updates the thryve_type field without modifying or deleting existing templates.
"""

import os
import sys
import csv
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Add the parent directory to the path so we can import from app
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
    load_dotenv(override=True)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.health_metrics import HealthRecordMetricTemplate
from app.models.thryve_data_type import ThryveDataType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_csv_data(csv_path: Path) -> List[Dict[str, str]]:
    """Load data from CSV file"""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    raw_data = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig to handle BOM
        reader = csv.DictReader(f)
        for row in reader:
            # Clean row data (strip whitespace)
            cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items()}
            raw_data.append(cleaned_row)
    
    logger.info(f"Loaded {len(raw_data)} rows from CSV file")
    return raw_data


def update_thryve_types(db: Session, csv_data: List[Dict[str, str]]) -> tuple[int, int]:
    """
    Update thryve_type for existing metric templates based on CSV data.
    
    Returns:
        (updated_count, skipped_count)
    """
    updated_count = 0
    skipped_count = 0
    not_found_count = 0
    
    for row in csv_data:
        # Extract CSV data
        thryve_data_type_id_str = row.get("Thryve dataTypeId", "").strip()
        thryve_type = row.get("Thryve type", "").strip()
        
        # Skip if no thryve_type specified or invalid
        if not thryve_type or thryve_type not in ["Daily", "Epoch"]:
            skipped_count += 1
            continue
        
        # Skip if no dataTypeId
        if not thryve_data_type_id_str or not thryve_data_type_id_str.isdigit():
            skipped_count += 1
            continue
        
        thryve_data_type_id = int(thryve_data_type_id_str)
        
        # Find ThryveDataType by data_type_id
        thryve_data_type = db.query(ThryveDataType).filter(
            ThryveDataType.data_type_id == thryve_data_type_id,
            ThryveDataType.is_active == True
        ).first()
        
        if not thryve_data_type:
            logger.warning(f"Thryve data type not found for dataTypeId: {thryve_data_type_id}")
            not_found_count += 1
            continue
        
        # Find metric template(s) linked to this Thryve data type
        # Note: There could be multiple templates if duplicates exist, but typically one
        metric_templates = db.query(HealthRecordMetricTemplate).filter(
            HealthRecordMetricTemplate.thryve_data_type_id == thryve_data_type.id,
            HealthRecordMetricTemplate.is_active == True
        ).all()
        
        if not metric_templates:
            logger.warning(f"No metric template found for Thryve data type ID {thryve_data_type_id} ({thryve_data_type.name})")
            not_found_count += 1
            continue
        
        # Update all matching templates
        for metric_template in metric_templates:
            if metric_template.thryve_type == thryve_type:
                logger.debug(f"Metric template {metric_template.id} ({metric_template.name}) already has thryve_type='{thryve_type}', skipping")
                continue
            
            # Update thryve_type
            old_value = metric_template.thryve_type
            metric_template.thryve_type = thryve_type
            db.commit()
            db.refresh(metric_template)
            
            logger.info(
                f"Updated metric template {metric_template.id} ({metric_template.name}): "
                f"thryve_type '{old_value}' -> '{thryve_type}' (dataTypeId: {thryve_data_type_id})"
            )
            updated_count += 1
    
    logger.info(f"Update summary: {updated_count} updated, {skipped_count} skipped (no thryve_type), {not_found_count} not found")
    return updated_count, skipped_count


def main():
    """Main function to run the update"""
    
    # Load data from CSV file
    csv_path = Path(__file__).parent / "section_metric_template.csv"
    logger.info(f"Reading CSV file: {csv_path}")
    
    try:
        csv_data = load_csv_data(csv_path)
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return
    except Exception as e:
        logger.error(f"❌ Error reading CSV file: {e}")
        return
    
    if not csv_data:
        logger.warning("CSV file is empty, nothing to update")
        return
    
    try:
        # Get database session
        db = SessionLocal()
        
        try:
            logger.info("Starting thryve_type update...")
            updated_count, skipped_count = update_thryve_types(db, csv_data)
            
            logger.info(f"✅ Update completed successfully!")
            logger.info(f"   - Updated: {updated_count} metric templates")
            logger.info(f"   - Skipped: {skipped_count} rows (no thryve_type or invalid data)")
            
        except Exception as e:
            logger.error(f"❌ Error during update: {e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return


if __name__ == "__main__":
    main()

