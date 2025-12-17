#!/usr/bin/env python3
"""
Script to compare section_metric_template.csv with database and update differences.
This script identifies differences in metric templates and updates them accordingly.
"""

import os
import sys
import csv
import logging
from typing import Dict, List, Optional, Tuple
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
from app.models.health_metrics import HealthRecordMetricTemplate, HealthRecordSectionTemplate
from app.models.health_record import HealthRecordMetric
from app.models.thryve_data_type import ThryveDataType
from app.crud.health_record import HealthRecordSectionTemplateCRUD, HealthRecordMetricTemplateCRUD

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReferenceRangeParser:
    """Parser for reference range strings"""
    
    @staticmethod
    def parse_reference_range(reference: str) -> Optional[Dict]:
        """Parse reference range string into structured data"""
        if not reference or not reference.strip():
            return None
        
        # Simple parsing - can be enhanced
        # For now, return as-is in a structured format
        return {"raw": reference.strip()}


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


def parse_csv_row(row: Dict[str, str]) -> Optional[Dict]:
    """Parse a CSV row into structured metric data"""
    metric_en = row.get("Metric (EN)", "").strip()
    section_en = row.get("Section (EN)", "").strip()
    thryve_data_type_id_str = row.get("Thryve dataTypeId", "").strip()
    thryve_type = row.get("Thryve type", "").strip()
    
    if not metric_en or not section_en:
        return None
    
    # Parse Thryve data type ID
    thryve_data_type_id = None
    if thryve_data_type_id_str and thryve_data_type_id_str.isdigit():
        thryve_data_type_id = int(thryve_data_type_id_str)
    
    # Validate thryve_type
    thryve_type_valid = thryve_type if thryve_type in ["Daily", "Epoch"] else None
    
    # Generate metric name (same logic as add_admin_templates.py)
    metric_name = metric_en.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
    
    return {
        "metric_name": metric_name,
        "display_name": metric_en,
        "section_en": section_en,
        "thryve_data_type_id": thryve_data_type_id,
        "thryve_type": thryve_type_valid
    }


def find_metric_template_by_thryve_type_id(
    db: Session, 
    thryve_data_type_id: int
) -> Optional[Tuple[HealthRecordMetricTemplate, Optional[ThryveDataType]]]:
    """
    Find metric template by Thryve data type ID.
    
    Returns:
        (metric_template, thryve_data_type) or None if not found
    """
    if not thryve_data_type_id:
        return None
    
    # Find ThryveDataType
    thryve_data_type = db.query(ThryveDataType).filter(
        ThryveDataType.data_type_id == thryve_data_type_id,
        ThryveDataType.is_active == True
    ).first()
    
    if not thryve_data_type:
        return None
    
    # Find metric template linked to this ThryveDataType
    metric_template = db.query(HealthRecordMetricTemplate).filter(
        HealthRecordMetricTemplate.thryve_data_type_id == thryve_data_type.id,
        HealthRecordMetricTemplate.is_active == True
    ).first()
    
    if metric_template:
        return (metric_template, thryve_data_type)
    return None


def find_metric_template_by_name_and_section(
    db: Session,
    metric_name: str,
    section_en: str
) -> Optional[HealthRecordMetricTemplate]:
    """
    Find metric template by name and section.
    This helps identify metrics that may have had their thryve_data_type_id changed.
    """
    # Normalize section name (same mapping as in add_admin_templates.py)
    section_mapping = {
        "Cardiovascular": "Cardiovascular",
        "Respiratory": "Respiratory", 
        "Temperature": "Temperature",
        "Sleep": "Sleep",
        "Activity": "Activity",
        "Anthropometric Measurements": "Anthropometric Measurements",
        "Body composition": "Body Composition",
        "Digital health": "Digital Health",
        "Hematology": "Hematology",
        "Biochemistry": "Biochemistry",
        "Endochronology": "Endocrinology",
        "Urine": "Urine Analysis"
    }
    
    section_name = section_mapping.get(section_en, section_en)
    section_name_normalized = section_name.lower().replace(" ", "_")
    
    # Find section template first
    section_template = db.query(HealthRecordSectionTemplate).filter(
        HealthRecordSectionTemplate.name == section_name_normalized,
        HealthRecordSectionTemplate.is_active == True
    ).first()
    
    if not section_template:
        return None
    
    # Find metric template by name within this section
    metric_template = db.query(HealthRecordMetricTemplate).filter(
        HealthRecordMetricTemplate.section_template_id == section_template.id,
        HealthRecordMetricTemplate.name == metric_name,
        HealthRecordMetricTemplate.is_active == True
    ).first()
    
    return metric_template


def update_user_metrics_from_template(
    db: Session,
    metric_template: HealthRecordMetricTemplate,
    changes: List[str],
    template_changes: Dict[str, any]
) -> int:
    """
    Update user metrics that reference this template.
    Updates fields that should be synced from template to user metrics.
    
    Args:
        template_changes: Dict of field changes made to the template
        (e.g., {'thryve_type': 'Daily', 'display_name': 'New Name'})
    
    Returns:
        Number of user metrics updated
    """
    # Find all user metrics that reference this template
    user_metrics = db.query(HealthRecordMetric).filter(
        HealthRecordMetric.metric_tmp_id == metric_template.id
    ).all()
    
    if not user_metrics:
        return 0
    
    updated_count = 0
    for user_metric in user_metrics:
        user_metric_updated = False
        
        # Update fields that should be synced from template
        # Note: We update display_name, description, default_unit, reference_data, data_type
        # only if they match the template's current values (haven't been customized)
        # This is a conservative approach - we sync if values appear to be from template
        
        # Sync display_name if it matches the template's previous value or current value
        if 'display_name' in template_changes or user_metric.display_name == metric_template.display_name:
            if user_metric.display_name != metric_template.display_name:
                user_metric.display_name = metric_template.display_name
                user_metric_updated = True
        
        # Sync description if it matches or is None
        if user_metric.description is None or user_metric.description == metric_template.description:
            if user_metric.description != metric_template.description:
                user_metric.description = metric_template.description
                user_metric_updated = True
        
        # Sync default_unit if it matches or is None
        if user_metric.default_unit is None or user_metric.default_unit == metric_template.default_unit:
            if user_metric.default_unit != metric_template.default_unit:
                user_metric.default_unit = metric_template.default_unit
                user_metric_updated = True
        
        # Sync reference_data if it matches or is None
        if user_metric.reference_data is None or user_metric.reference_data == metric_template.reference_data:
            if user_metric.reference_data != metric_template.reference_data:
                user_metric.reference_data = metric_template.reference_data
                user_metric_updated = True
        
        # Sync data_type if it matches
        if user_metric.data_type == metric_template.data_type:
            # Already matches, no update needed
            pass
        else:
            # Only update if it's the default/common value
            user_metric.data_type = metric_template.data_type
            user_metric_updated = True
        
        if user_metric_updated:
            try:
                db.commit()
                db.refresh(user_metric)
                updated_count += 1
                logger.debug(
                    f"Updated user metric {user_metric.id} ({user_metric.display_name}) "
                    f"from template {metric_template.id} changes"
                )
            except Exception as e:
                logger.error(f"Error updating user metric {user_metric.id}: {e}")
                db.rollback()
                continue
        else:
            logger.debug(
                f"User metric {user_metric.id} ({user_metric.display_name}) "
                f"references template {metric_template.id} - no sync needed (may be customized)"
            )
    
    return updated_count


def compare_and_update(
    db: Session, 
    csv_data: List[Dict[str, str]]
) -> Tuple[int, int, int, int, List[str]]:
    """
    Compare CSV data with database and update differences.
    Also updates user metrics that reference changed templates.
    
    Returns:
        (updated_count, not_found_count, skipped_count, user_metrics_affected_count, update_details)
    """
    updated_count = 0
    not_found_count = 0
    skipped_count = 0
    user_metrics_affected_count = 0
    update_details = []
    
    for row in csv_data:
        parsed_data = parse_csv_row(row)
        if not parsed_data:
            skipped_count += 1
            continue
        
        csv_thryve_data_type_id = parsed_data["thryve_data_type_id"]
        csv_thryve_type = parsed_data["thryve_type"]
        metric_name = parsed_data["metric_name"]
        section_en = parsed_data["section_en"]
        display_name = parsed_data["display_name"]
        
        if not csv_thryve_data_type_id:
            skipped_count += 1
            continue
        
        # Find ThryveDataType from CSV dataTypeId
        csv_thryve_data_type = db.query(ThryveDataType).filter(
            ThryveDataType.data_type_id == csv_thryve_data_type_id,
            ThryveDataType.is_active == True
        ).first()
        
        if not csv_thryve_data_type:
            logger.warning(
                f"ThryveDataType not found for dataTypeId: {csv_thryve_data_type_id} "
                f"({display_name})"
            )
            not_found_count += 1
            continue
        
        # Strategy 1: Try to find metric template by thryve_data_type_id (current link)
        # Note: This finds what metric is currently linked to this dataTypeId
        result = find_metric_template_by_thryve_type_id(db, csv_thryve_data_type_id)
        
        if result:
            metric_template, current_thryve_data_type = result
            # Metric found by current thryve_data_type_id - check if it matches by name
            if metric_template.name == metric_name:
                # Perfect match - metric is correctly linked, just check for field differences
                needs_update = False
                changes = []
                
                # Compare thryve_type
                if metric_template.thryve_type != csv_thryve_type:
                    changes.append(f"thryve_type: '{metric_template.thryve_type}' -> '{csv_thryve_type}'")
                    metric_template.thryve_type = csv_thryve_type
                    needs_update = True
                
                if needs_update:
                    try:
                        # Prepare template changes dict for user metric sync
                        template_changes = {}
                        if csv_thryve_type and metric_template.thryve_type != csv_thryve_type:
                            template_changes['thryve_type'] = csv_thryve_type
                        
                        db.commit()
                        db.refresh(metric_template)
                        updated_count += 1
                        change_str = ", ".join(changes)
                        update_details.append(
                            f"Updated template {metric_template.id} ({metric_template.display_name}): {change_str}"
                        )
                        logger.info(
                            f"✅ Updated metric template {metric_template.id} ({metric_template.display_name}): {change_str}"
                        )
                        
                        # Update user metrics that reference this template
                        affected_count = update_user_metrics_from_template(db, metric_template, changes, template_changes)
                        if affected_count > 0:
                            user_metrics_affected_count += affected_count
                            logger.info(
                                f"   📋 Synced {affected_count} user metric(s) from template changes"
                            )
                    except Exception as e:
                        logger.error(f"❌ Error updating metric template {metric_template.id}: {e}")
                        db.rollback()
                continue
            else:
                # Metric found but name doesn't match - indicates a swap/mismatch issue
                # The dataTypeId is linked to a different metric, we'll handle it in Strategy 2
                logger.warning(
                    f"⚠️  Metric template {metric_template.id} linked to dataTypeId {csv_thryve_data_type_id} "
                    f"but name mismatch: DB='{metric_template.name}' vs CSV='{metric_name}' "
                    f"(will try to find by name and update link)"
                )
        
        # Strategy 2: Try to find by name and section (in case thryve_data_type_id changed)
        # This handles cases where the metric name matches but the thryve_data_type_id link changed
        metric_template_by_name = find_metric_template_by_name_and_section(
            db, metric_name, section_en
        )
        
        if metric_template_by_name:
            # Found by name - check if thryve_data_type_id needs updating
            needs_update = False
            changes = []
            
            # Get current thryve_data_type_id (data_type_id) from database
            # metric_template.thryve_data_type_id links to thryve_data_types.id
            db_thryve_data_type_id = None
            db_thryve_data_type_name = None
            if metric_template_by_name.thryve_data_type_id:
                db_thryve_data_type = db.query(ThryveDataType).filter(
                    ThryveDataType.id == metric_template_by_name.thryve_data_type_id
                ).first()
                if db_thryve_data_type:
                    db_thryve_data_type_id = db_thryve_data_type.data_type_id
                    db_thryve_data_type_name = db_thryve_data_type.name
            
            # Compare thryve_data_type_id (comparing data_type_id values)
            # If different, we need to update metric_template.thryve_data_type_id to point to csv_thryve_data_type.id
            if db_thryve_data_type_id != csv_thryve_data_type_id:
                old_name = f"dataTypeId {db_thryve_data_type_id} ({db_thryve_data_type_name})" if db_thryve_data_type_id else "None"
                new_name = f"dataTypeId {csv_thryve_data_type_id} ({csv_thryve_data_type.name})"
                changes.append(
                    f"thryve_data_type_id: {old_name} -> {new_name}"
                )
                # Update to link to the new ThryveDataType (using its id, not data_type_id)
                metric_template_by_name.thryve_data_type_id = csv_thryve_data_type.id
                needs_update = True
            
            # Compare thryve_type
            if metric_template_by_name.thryve_type != csv_thryve_type:
                changes.append(f"thryve_type: '{metric_template_by_name.thryve_type}' -> '{csv_thryve_type}'")
                metric_template_by_name.thryve_type = csv_thryve_type
                needs_update = True
            
            if needs_update:
                try:
                    # Prepare template changes dict for user metric sync
                    template_changes = {}
                    if csv_thryve_type and metric_template_by_name.thryve_type != csv_thryve_type:
                        template_changes['thryve_type'] = csv_thryve_type
                    # Note: thryve_data_type_id change doesn't affect user metrics directly
                    # as they reference templates via metric_tmp_id
                    
                    db.commit()
                    db.refresh(metric_template_by_name)
                    updated_count += 1
                    change_str = ", ".join(changes)
                    update_details.append(
                        f"Updated template {metric_template_by_name.id} ({metric_template_by_name.display_name}): {change_str}"
                    )
                    logger.info(
                        f"✅ Updated metric template {metric_template_by_name.id} "
                        f"({metric_template_by_name.display_name}): {change_str}"
                    )
                    
                    # Update user metrics that reference this template
                    affected_count = update_user_metrics_from_template(db, metric_template_by_name, changes, template_changes)
                    if affected_count > 0:
                        user_metrics_affected_count += affected_count
                        logger.info(
                            f"   📋 Synced {affected_count} user metric(s) from template changes"
                        )
                except Exception as e:
                    logger.error(f"❌ Error updating metric template {metric_template_by_name.id}: {e}")
                    db.rollback()
            continue
        
        # Not found by either method
        logger.warning(
            f"Metric template not found for: {display_name} "
            f"(dataTypeId: {csv_thryve_data_type_id}, name: {metric_name}, section: {section_en})"
        )
        not_found_count += 1
    
    return updated_count, not_found_count, skipped_count, user_metrics_affected_count, update_details


def main():
    """Main function to run the comparison and update"""
    
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
        logger.warning("CSV file is empty, nothing to compare")
        return
    
    try:
        # Get database session
        db = SessionLocal()
        
        try:
            logger.info("Starting comparison and update...")
            updated_count, not_found_count, skipped_count, user_metrics_affected_count, update_details = compare_and_update(db, csv_data)
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("COMPARISON SUMMARY")
            logger.info("=" * 80)
            logger.info(f"✅ Updated: {updated_count} metric templates")
            logger.info(f"📋 User metrics affected: {user_metrics_affected_count} metrics reference updated templates")
            logger.info(f"⚠️  Not found: {not_found_count} metrics (not in database)")
            logger.info(f"⏭️  Skipped: {skipped_count} rows (no dataTypeId or invalid data)")
            logger.info("")
            
            if update_details:
                logger.info("DETAILED CHANGES:")
                logger.info("-" * 80)
                for detail in update_details:
                    logger.info(f"  • {detail}")
                logger.info("")
            
            if updated_count > 0:
                logger.info(f"✅ Comparison and update completed successfully!")
            else:
                logger.info("✅ Comparison completed - no differences found (database is up to date)")
            
        except Exception as e:
            logger.error(f"❌ Error during comparison: {e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return


if __name__ == "__main__":
    main()

