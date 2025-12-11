#!/usr/bin/env python3
"""
Script to add admin-predefined section/metric templates to the database.
This script parses the CSV file and creates section and metric templates
with multi-language support (EN, PT, ES) and reference range parsing.
"""

import os
import sys
import json
import re
import csv
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
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
    # Try loading from project root if script is run from different directory
    load_dotenv(override=True)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.health_metrics import HealthRecordSectionTemplate, HealthRecordMetricTemplate
from app.models.health_record import HealthRecordType
from app.models.user import User, UserRole
from app.models.thryve_data_type import ThryveDataType
from app.crud.health_record import HealthRecordSectionTemplateCRUD, HealthRecordMetricTemplateCRUD
from app.crud.user import user_crud

# Verify DATABASE_URL is loaded
if "username" in settings.DATABASE_URL or "password" in settings.DATABASE_URL:
    logging.warning("⚠️  DATABASE_URL appears to have placeholder values. Please check your .env file.")
    logging.warning(f"   Current DATABASE_URL: {settings.DATABASE_URL.split('@')[0]}@...")
else:
    logging.info(f"✅ Database connection configured (host: {settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'unknown'})")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferenceRangeParser:
    """Parse reference ranges from various formats"""
    
    @staticmethod
    def parse_reference_range(reference_str: str) -> Dict[str, Any]:
        """
        Parse reference range string into structured data.
        Returns format: {"male": {"min": value, "max": value}, "female": {"min": value, "max": value}}
        
        Examples:
        - "7-9" -> {"male": {"min": 7, "max": 9}, "female": {"min": 7, "max": 9}}
        - ">8000" -> {"male": {"min": 8000.01, "max": null}, "female": {"min": 8000.01, "max": null}}
        - ">=2" -> {"male": {"min": 2, "max": null}, "female": {"min": 2, "max": null}}
        - "<8000" -> {"male": {"min": null, "max": 7999.99}, "female": {"min": null, "max": 7999.99}}
        - "<=2" -> {"male": {"min": null, "max": 2}, "female": {"min": null, "max": 2}}
        - "Men: <94, Female: <80" -> {"male": {"min": null, "max": 94}, "female": {"min": null, "max": 80}}
        """
        if not reference_str or not reference_str.strip():
            return {"male": {"min": None, "max": None}, "female": {"min": None, "max": None}}
        
        ref_clean = reference_str.strip().lower()
        
        # Handle gender-specific ranges
        if "men:" in ref_clean and "female:" in ref_clean:
            return ReferenceRangeParser._parse_gender_specific(ref_clean)
        
        # Parse simple range and apply to both genders
        parsed_range = ReferenceRangeParser._parse_simple_range(ref_clean)
        return {
            "male": parsed_range,
            "female": parsed_range
        }
    
    @staticmethod
    def _parse_gender_specific(ref_str: str) -> Dict[str, Any]:
        """Parse gender-specific reference ranges"""
        result = {"male": {"min": None, "max": None}, "female": {"min": None, "max": None}}
        
        # Extract male values
        male_match = re.search(r'men:\s*([^,]+)', ref_str)
        if male_match:
            male_ref = male_match.group(1).strip()
            result["male"] = ReferenceRangeParser._parse_simple_range(male_ref)
        
        # Extract female values
        female_match = re.search(r'female:\s*([^,]+)', ref_str)
        if female_match:
            female_ref = female_match.group(1).strip()
            result["female"] = ReferenceRangeParser._parse_simple_range(female_ref)
        
        return result
    
    @staticmethod
    def _parse_simple_range(ref_str: str) -> Dict[str, Any]:
        """Parse simple reference range without gender"""
        ref_clean = ref_str.strip()
        
        # Extract numeric value and operator, ignoring units
        numeric_value = ReferenceRangeParser._extract_numeric_value(ref_clean)
        if numeric_value is None:
            logger.warning(f"Could not extract numeric value from: '{ref_str}'")
            return {"min": None, "max": None}
        
        # Handle range format: "7-9" -> min: 7, max: 9
        if "-" in ref_clean and not ref_clean.startswith("<") and not ref_clean.startswith(">"):
            parts = ref_clean.split("-")
            if len(parts) == 2:
                try:
                    min_val = ReferenceRangeParser._extract_numeric_value(parts[0])
                    max_val = ReferenceRangeParser._extract_numeric_value(parts[1])
                    if min_val is not None and max_val is not None:
                        return {"min": min_val, "max": max_val}
                except ValueError:
                    pass
        
        # Handle >95% -> min: 95.01, max: null
        elif ref_clean.startswith(">"):
            return {"min": numeric_value + 0.01, "max": None}
        
        # Handle >=2 -> min: 2, max: null
        elif ref_clean.startswith(">="):
            return {"min": numeric_value, "max": None}
        
        # Handle <94 -> min: null, max: 93.99
        elif ref_clean.startswith("<") and not ref_clean.startswith("<="):
            return {"min": None, "max": numeric_value - 0.01}
        
        # Handle <=2 -> min: null, max: 2
        elif ref_clean.startswith("<="):
            return {"min": None, "max": numeric_value}
        
        # Try to parse as single number
        return {"min": numeric_value, "max": numeric_value}
    
    @staticmethod
    def _extract_numeric_value(text: str) -> float:
        """Extract numeric value from text, ignoring units like %, cm, etc."""
        import re
        # Find the first number in the text (including decimals)
        match = re.search(r'-?\d+\.?\d*', text)
        if match:
            return float(match.group())
        return None

class AdminTemplateImporter:
    """Import admin templates from raw data"""
    
    def __init__(self, db: Session, admin_user_id: int):
        self.db = db
        self.admin_user_id = admin_user_id
        self.section_crud = HealthRecordSectionTemplateCRUD()
        self.metric_crud = HealthRecordMetricTemplateCRUD()
        self.parser = ReferenceRangeParser()
        
        # Tab to health record type ID mapping
        # Note: CSV uses "Lab analysis" (lowercase) for Analysis tab
        self.tab_to_health_record_type = {
            "Analysis": 1,      # Analysis tab (legacy)
            "Lab analysis": 1,  # Analysis tab (from CSV)
            "Vitals": 2,        # Vitals tab
            "Body": 3,          # Body Composition tab
            "Lifestyle": 4,     # Lifestyle tab
            "Exams": 5          # Exams tab
        }
        
        # Section mapping from raw data to standardized names
        self.section_mapping = {
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
    
    def get_or_create_admin_user(self) -> int:
        """Get or create admin user for template creation"""
        # Try to find existing admin user
        admin_user = self.db.query(User).filter(
            User.email == "admin@saluso.com",
            User.role == UserRole.ADMIN
        ).first()
        
        if admin_user:
            logger.info(f"Found existing admin user: {admin_user.id}")
            return admin_user.id
        
        # Create admin user if not found
        admin_data = {
            "supabase_user_id": "admin-system",
            "email": "admin@saluso.com",
            "is_active": True,
            "role": UserRole.ADMIN
        }
        
        admin_user = user_crud.create(self.db, admin_data)
        logger.info(f"Created admin user: {admin_user.id}")
        return admin_user.id
    
    def parse_raw_data(self, raw_data: List[Dict[str, str]]) -> Dict[str, Any]:
        """Parse raw data into structured format"""
        sections = {}
        
        for row in raw_data:
            # Extract data - handle potential BOM or whitespace in column names
            row_clean = {k.strip(): v.strip() if v else "" for k, v in row.items()}
            
            # Extract data
            metric_en = row_clean.get("Metric (EN)", "").strip()
            section_en = row_clean.get("Section (EN)", "").strip()
            tab = row_clean.get("Tab", "").strip()
            unit_en = row_clean.get("Unit (metric system EN)", "").strip()
            reference = row_clean.get("Reference (metric system)", "").strip()
            
            # Multi-language data
            metric_pt = row_clean.get("Metric (PT)", "").strip()
            section_pt = row_clean.get("Section (PT)", "").strip()
            unit_pt = row_clean.get("Unit (metric system PT)", "").strip()
            
            metric_es = row_clean.get("Metric (ES)", "").strip()
            section_es = row_clean.get("Section (ES)", "").strip()
            unit_es = row_clean.get("Unit (metric system ES)", "").strip()
            
            # Thryve data
            thryve_name = row_clean.get("Thryve name", "").strip()
            thryve_data_type_id_str = row_clean.get("Thryve dataTypeId", "").strip()
            
            if not metric_en or not section_en:
                continue
            
            # Normalize section name
            section_name = self.section_mapping.get(section_en, section_en)
            
            if section_name not in sections:
                sections[section_name] = {
                    "name": section_name.lower().replace(" ", "_"),
                    "display_name": section_name,
                    "display_name_pt": section_pt if section_pt else section_name,
                    "display_name_es": section_es if section_es else section_name,
                    "tab": tab,
                    "metrics": []
                }
            
            # Parse reference range
            reference_data = self.parser.parse_reference_range(reference)
            
            # Get Thryve data type info if available
            thryve_data_type_id = None
            if thryve_data_type_id_str and thryve_data_type_id_str.isdigit():
                thryve_data_type_id = int(thryve_data_type_id_str)
            
            # Determine data type from unit or Thryve info
            data_type = "number"
            if unit_en.lower() in ["boolean", "boolean"] or "Boolean" in unit_en:
                data_type = "boolean"
            elif not unit_en or unit_en.strip() == "":
                data_type = "text"
            
            # Create metric data
            metric_data = {
                "name": metric_en.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",", ""),
                "display_name": metric_en,
                "display_name_pt": metric_pt if metric_pt else metric_en,
                "display_name_es": metric_es if metric_es else metric_en,
                "unit": unit_en,
                "unit_pt": unit_pt if unit_pt else unit_en,
                "unit_es": unit_es if unit_es else unit_en,
                "reference": reference,
                "reference_data": reference_data,
                "data_type": data_type,
                "thryve_name": thryve_name,
                "thryve_data_type_id": thryve_data_type_id
            }
            
            sections[section_name]["metrics"].append(metric_data)
        
        return sections
    
    def create_section_template(self, section_data: Dict[str, Any]) -> HealthRecordSectionTemplate:
        """Create section template"""
        # Get health record type ID based on tab
        # CSV uses "Lab analysis" for Analysis tab
        tab = section_data.get("tab", "Vitals").strip()
        health_record_type_id = self.tab_to_health_record_type.get(tab, 2)  # Default to Vitals
        
        # Check if section already exists
        existing = self.section_crud.get_by_name_and_type(
            self.db, 
            section_data["name"], 
            health_record_type_id
        )
        
        if existing:
            logger.info(f"Section template already exists: {section_data['name']} (Tab: {tab})")
            return existing
        
        # Create new section template - store ONLY English (source language) in template table
        # All translations (ES, PT) will be stored in the translations table
        section_template_data = {
            "name": section_data["name"],
            "display_name": section_data["display_name"],  # English only
            "description": f"Admin-defined {section_data['display_name']} section",  # English only
            "source_language": "en",  # Always 'en' for admin templates
            "health_record_type_id": health_record_type_id,
            "is_active": True,
            "is_default": True,
            "created_by": self.admin_user_id
        }
        
        section_template = self.section_crud.create(self.db, section_template_data)
        
        # Store translations (ES, PT) in the translations table, NOT in the template table
        from app.crud.translation import translation_crud
        
        if section_data.get("display_name_pt"):
            translation_crud.create_translation(
                db=self.db,
                entity_type='health_record_section_template',
                entity_id=section_template.id,
                field_name='display_name',
                language='pt',
                translated_text=section_data["display_name_pt"],
                source_language='en'
            )
        
        if section_data.get("display_name_es"):
            translation_crud.create_translation(
                db=self.db,
                entity_type='health_record_section_template',
                entity_id=section_template.id,
                field_name='display_name',
                language='es',
                translated_text=section_data["display_name_es"],
                source_language='en'
            )
        logger.info(f"Created section template: {section_template.display_name} (Tab: {tab}, Health Record Type ID: {health_record_type_id})")
        return section_template
    
    def create_metric_template(self, section_template: HealthRecordSectionTemplate, metric_data: Dict[str, Any]) -> HealthRecordMetricTemplate:
        """Create metric template"""
        # Check if metric already exists
        existing = self.metric_crud.get_by_section_and_name(
            self.db,
            section_template.id,
            metric_data["name"]
        )
        
        if existing:
            logger.info(f"Metric template already exists: {metric_data['name']}")
            # Update Thryve link if provided
            if metric_data.get("thryve_data_type_id"):
                self._link_thryve_data_type(existing, metric_data["thryve_data_type_id"])
            return existing
        
        # Find Thryve data type if dataTypeId is provided
        thryve_data_type_id = None
        if metric_data.get("thryve_data_type_id"):
            # Try to find Thryve data type by data_type_id (check both Daily and Epoch)
            thryve_data_type = self.db.query(ThryveDataType).filter(
                ThryveDataType.data_type_id == metric_data["thryve_data_type_id"]
            ).first()
            if thryve_data_type:
                thryve_data_type_id = thryve_data_type.id
                logger.debug(f"Found Thryve data type: {thryve_data_type.name} (ID: {thryve_data_type.id}) for metric {metric_data['name']}")
            else:
                logger.warning(f"Thryve data type not found for dataTypeId: {metric_data['thryve_data_type_id']} (metric: {metric_data['name']})")
        
        # Create new metric template - store ONLY English (source language) in template table
        # All translations (ES, PT) for display_name and default_unit will be stored in the translations table
        metric_template_data = {
            "section_template_id": section_template.id,
            "name": metric_data["name"],
            "display_name": metric_data["display_name"],  # English only
            "description": f"Admin-defined {metric_data['display_name']} metric",  # English only
            "default_unit": metric_data.get("unit"),  # English only
            "source_language": "en",  # Always 'en' for admin templates
            "original_reference": metric_data.get("reference"),
            "reference_data": metric_data.get("reference_data"),
            "data_type": metric_data.get("data_type", "number"),
            "thryve_data_type_id": thryve_data_type_id,
            "is_active": True,
            "is_default": True,
            "created_by": self.admin_user_id
        }
        
        metric_template = self.metric_crud.create(self.db, metric_template_data)
        
        # Store translations (ES, PT) in the translations table, NOT in the template table
        from app.crud.translation import translation_crud
        
        # Translate display_name - store in translations table
        if metric_data.get("display_name_pt"):
            translation_crud.create_translation(
                db=self.db,
                entity_type='health_record_metric_template',
                entity_id=metric_template.id,
                field_name='display_name',
                language='pt',
                translated_text=metric_data["display_name_pt"],
                source_language='en'
            )
        if metric_data.get("display_name_es"):
            translation_crud.create_translation(
                db=self.db,
                entity_type='health_record_metric_template',
                entity_id=metric_template.id,
                field_name='display_name',
                language='es',
                translated_text=metric_data["display_name_es"],
                source_language='en'
            )
        
        # Translate default_unit - store in translations table
        if metric_data.get("unit_pt"):
            translation_crud.create_translation(
                db=self.db,
                entity_type='health_record_metric_template',
                entity_id=metric_template.id,
                field_name='default_unit',
                language='pt',
                translated_text=metric_data["unit_pt"],
                source_language='en'
            )
        if metric_data.get("unit_es"):
            translation_crud.create_translation(
                db=self.db,
                entity_type='health_record_metric_template',
                entity_id=metric_template.id,
                field_name='default_unit',
                language='es',
                translated_text=metric_data["unit_es"],
                source_language='en'
            )
        logger.info(f"Created metric template: {metric_template.display_name}" + (f" (linked to Thryve data type ID: {thryve_data_type_id})" if thryve_data_type_id else ""))
        return metric_template
    
    def _link_thryve_data_type(self, metric_template: HealthRecordMetricTemplate, thryve_data_type_id: int):
        """Link metric template to Thryve data type"""
        thryve_data_type = self.db.query(ThryveDataType).filter(
            ThryveDataType.data_type_id == thryve_data_type_id
        ).first()
        if thryve_data_type:
            metric_template.thryve_data_type_id = thryve_data_type.id
            logger.debug(f"Linked metric {metric_template.name} to Thryve data type: {thryve_data_type.name}")
    
    def import_templates(self, raw_data: List[Dict[str, str]]):
        """Import all templates from raw data"""
        logger.info("Starting template import...")
        
        # Parse raw data
        sections_data = self.parse_raw_data(raw_data)
        
        # Create sections and metrics
        for section_name, section_data in sections_data.items():
            logger.info(f"Processing section: {section_name}")
            
            # Create section template
            section_template = self.create_section_template(section_data)
            
            # Create metric templates
            for metric_data in section_data["metrics"]:
                try:
                   self.create_metric_template(section_template, metric_data)
                except IntegrityError as e:
                    logger.warning(f"⚠️  Skipped duplicate metric: {metric_data['name']} - {str(e)[:100]}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error creating metric {metric_data['name']}: {e}")
                    continue
        
        logger.info("Template import completed successfully!")

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

def main():
    """Main function to run the import"""
    
    # Load data from CSV file
    csv_path = Path(__file__).parent / "section_metric_template.csv"
    logger.info(f"Reading CSV file: {csv_path}")
    
    try:
        raw_data = load_csv_data(csv_path)
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return
    except Exception as e:
        logger.error(f"❌ Error reading CSV file: {e}")
        return
    
    # Fallback to hardcoded data if CSV is empty (for backward compatibility)
    if not raw_data:
        logger.warning("CSV file is empty, using fallback hardcoded data")
    
    try:
        # Get database session
        db = SessionLocal()
        
        # Create importer
        importer = AdminTemplateImporter(db, 0)  # Will be set after getting admin user
        
        # Get or create admin user
        admin_user_id = importer.get_or_create_admin_user()
        importer.admin_user_id = admin_user_id
        
        # Import templates
        importer.import_templates(raw_data)
        
        # Commit all changes
        try:
            db.commit()
            logger.info("Admin template import completed successfully!")
        except IntegrityError as e:
            db.rollback()
            logger.error(f"❌ Error committing changes: {e}")
            raise
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during import: {e}", exc_info=True)
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()
