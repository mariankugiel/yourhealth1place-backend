#!/usr/bin/env python3
"""
Script to add admin-predefined section/metric templates to the database.
This script parses the provided raw data and creates section and metric templates
with multi-language support (EN, PT, ES) and reference range parsing.
"""

import os
import sys
import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.health_metrics import HealthRecordSectionTemplate, HealthRecordMetricTemplate
from app.models.health_record import HealthRecordType
from app.models.user import User, UserRole
from app.crud.health_record import HealthRecordSectionTemplateCRUD, HealthRecordMetricTemplateCRUD
from app.crud.user import user_crud

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
        self.tab_to_health_record_type = {
            "Analysis": 1,   # Analysis tab
            "Vitals": 2,     # Vitals tab
            "Body": 3,       # Body Composition tab
            "Lifestyle": 4,  # Lifestyle tab
            "Exams": 5       # Exams tab
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
            # Extract data
            metric_en = row.get("Metric (EN)", "").strip()
            section_en = row.get("Section (EN)", "").strip()
            tab = row.get("Tab", "").strip()
            unit_en = row.get("Unit (metric system EN)", "").strip()
            reference = row.get("Reference (metric system)", "").strip()
            
            # Multi-language data
            metric_pt = row.get("Metric (PT)", "").strip()
            section_pt = row.get("Section (PT)", "").strip()
            unit_pt = row.get("Unit (metric system PT)", "").strip()
            
            metric_es = row.get("Metric (ES)", "").strip()
            section_es = row.get("Section (ES)", "").strip()
            unit_es = row.get("Unit (metric system ES)", "").strip()
            
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
            
            # Create metric data
            metric_data = {
                "name": metric_en.lower().replace(" ", "_").replace("(", "").replace(")", ""),
                "display_name": metric_en,
                "display_name_pt": metric_pt if metric_pt else metric_en,
                "display_name_es": metric_es if metric_es else metric_en,
                "unit": unit_en,
                "unit_pt": unit_pt if unit_pt else unit_en,
                "unit_es": unit_es if unit_es else unit_en,
                "reference": reference,
                "reference_data": reference_data,
                "data_type": "number"
            }
            
            sections[section_name]["metrics"].append(metric_data)
        
        return sections
    
    def create_section_template(self, section_data: Dict[str, Any]) -> HealthRecordSectionTemplate:
        """Create section template"""
        # Get health record type ID based on tab
        tab = section_data.get("tab", "Vitals")
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
        
        # Create new section template (source language is 'en' for admin templates)
        section_template_data = {
            "name": section_data["name"],
            "display_name": section_data["display_name"],
            "description": f"Admin-defined {section_data['display_name']} section",
            "source_language": "en",  # Admin templates are in English
            "health_record_type_id": health_record_type_id,
            "is_active": True,
            "is_default": True,
            "created_by": self.admin_user_id
        }
        
        section_template = self.section_crud.create(self.db, section_template_data)
        
        # Create translations if provided
        from app.services.translation_service import translation_service
        if section_data.get("display_name_pt"):
            translation_service.get_translated_content(
                db=self.db,
                entity_type='health_record_section_template',
                entity_id=section_template.id,
                field_name='display_name',
                original_text=section_data["display_name"],
                target_language='pt',
                source_language='en'
            )
            # Manually create translation record with provided value
            from app.crud.translation import translation_crud
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
            return existing
        
        # Create new metric template (source language is 'en' for admin templates)
        metric_template_data = {
            "section_template_id": section_template.id,
            "name": metric_data["name"],
            "display_name": metric_data["display_name"],
            "description": f"Admin-defined {metric_data['display_name']} metric",
            "default_unit": metric_data.get("unit"),
            "source_language": "en",  # Admin templates are in English
            "original_reference": metric_data.get("reference"),
            "reference_data": metric_data.get("reference_data"),
            "data_type": metric_data.get("data_type", "number"),
            "is_active": True,
            "is_default": True,
            "created_by": self.admin_user_id
        }
        
        metric_template = self.metric_crud.create(self.db, metric_template_data)
        
        # Create translations if provided
        from app.crud.translation import translation_crud
        
        # Translate display_name
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
        
        # Translate default_unit
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
        logger.info(f"Created metric template: {metric_template.display_name}")
        return metric_template
    
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
                self.create_metric_template(section_template, metric_data)
        
        logger.info("Template import completed successfully!")

def main():
    """Main function to run the import"""
    
    # Raw data from the user
    raw_data = [
         # Analysis - Hematology
        {
            "Metric (EN)": "Erythrocytes",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "x10¹²/L",
            "Reference (metric system)": "3.90-5.10",
            "Metric (PT)": "Eritrócitos",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "x10¹²/L",
            "Metric (ES)": "Glóbulos rojos",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "x10¹²/L"
        },
        {
            "Metric (EN)": "Haemoglobin",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "g/dL",
            "Reference (metric system)": "12.0-15.2",
            "Metric (PT)": "Hemoglobina",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "g/dL",
            "Metric (ES)": "Hemoglobina",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "g/dL"
        },
        {
            "Metric (EN)": "HbA1c (IFCC/NGSP aligned)",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "%",
            "Reference (metric system)": "<5.7%",
            "Metric (PT)": "Hemoglobina glicada (HbA1c)",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "%",
            "Metric (ES)": "Hemoglobina glucosilada (HbA1c)",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "%"
        },
        {
            "Metric (EN)": "Hematocrit Cells",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "%",
            "Reference (metric system)": "37.0-46.0",
            "Metric (PT)": "Hematocrócitos",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "%",
            "Metric (ES)": "Hematocrito",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "%"
        },
        {
            "Metric (EN)": "Mean Glob. Vol. (MGV)",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "fL",
            "Reference (metric system)": "85-98",
            "Metric (PT)": "Vol. Glob. Médio (VGM)",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "fL",
            "Metric (ES)": "Volumen globular medio (VGM)",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "fL"
        },
        {
            "Metric (EN)": "Mean Glob. Hgb. (MgH)",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "pg",
            "Reference (metric system)": "28-32",
            "Metric (PT)": "Hgb. Glob. Média (HGM)",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "pg",
            "Metric (ES)": "Hb globular media (HGM)",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "pg"
        },
        {
            "Metric (EN)": "Glob. Hgb. Conc. Mean (CHGM)",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "g/dL",
            "Reference (metric system)": "32-36",
            "Metric (PT)": "Conc. Hgb. Glob. Média (CHGM)",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "g/dL",
            "Metric (ES)": "Concentración de hemoglobina globular Media (CHGM)",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "g/dL"
        },
        {
            "Metric (EN)": "RDW (red blood cell distribution index)",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "%",
            "Reference (metric system)": "12.0-14.7",
            "Metric (PT)": "RDW (índice distrib. eritrocit.)",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "%",
            "Metric (ES)": "RDW (índice de distribución de glóbulos rojos)",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "%"
        },
        {
            "Metric (EN)": "Leukocytes",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "x109 / L",
            "Reference (metric system)": "3.90-11.0",
            "Metric (PT)": "Leucócitos",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "x109 / L",
            "Metric (ES)": "Leucocitos",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "x109 / L"
        },
        {
            "Metric (EN)": "Neutrophils",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "x109 / L",
            "Reference (metric system)": "1.80-7.40",
            "Metric (PT)": "Neutrófilos",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "x109 / L",
            "Metric (ES)": "Neutrófilos",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "x109 / L"
        },
        {
            "Metric (EN)": "Eosinophils",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "x109 / L",
            "Reference (metric system)": "0.02-0.67",
            "Metric (PT)": "Eosinófilos",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "x109 / L",
            "Metric (ES)": "Eosinófilos",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "x109 / L"
        },
        {
            "Metric (EN)": "Basophils",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "x109 / L",
            "Reference (metric system)": "<0.13",
            "Metric (PT)": "Basófilos",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "x109 / L",
            "Metric (ES)": "Basófilos",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "x109 / L"
        },
        {
            "Metric (EN)": "Lymphocytes",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "x109 / L",
            "Reference (metric system)": "1.10-3.50",
            "Metric (PT)": "Linfócitos",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "x109 / L",
            "Metric (ES)": "Linfocitos",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "x109 / L"
        },
        {
            "Metric (EN)": "Monocytes",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "x109 / L",
            "Reference (metric system)": "0.21-0.92",
            "Metric (PT)": "Monócitos",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "x109 / L",
            "Metric (ES)": "Monocitos",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "x109 / L"
        },
        {
            "Metric (EN)": "Platelets",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "x109 / L",
            "Reference (metric system)": "170-430",
            "Metric (PT)": "Plaquetas",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "x109 / L",
            "Metric (ES)": "Plaquetas",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "x109 / L"
        },
        {
            "Metric (EN)": "MPV (mean plaq. vol.)",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "fL",
            "Reference (metric system)": "8.5-12.0",
            "Metric (PT)": "VPM (vol. plaq. médio)",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "fL",
            "Metric (ES)": "MPV (vol. plaquetario medio)",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "fL"
        },
        {
            "Metric (EN)": "Platelet tocrit",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "%",
            "Reference (metric system)": "0.20-0.36",
            "Metric (PT)": "Plaquetócrito",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "%",
            "Metric (ES)": "Tocrito plaquetario",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "%"
        },
        {
            "Metric (EN)": "PDW (plaq. distribution index)",
            "Section (EN)": "Hematology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "%",
            "Reference (metric system)": "9.0-17.0",
            "Metric (PT)": "PDW (índice distrib. plaq.)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "%",
            "Metric (ES)": "PDW (índice de distribución plaquetaria)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "%"
        },
        # Lab Analysis - Biochemistry
        {
            "Metric (EN)": "Fasting plasma glucose (FPG)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/dL",
            "Reference (metric system)": "74-106",
            "Metric (PT)": "Glucose",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mg/dL",
            "Metric (ES)": "Glucosa",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mg/dL"
        },
        {
            "Metric (EN)": "Bureau (Bile urea)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/dL",
            "Reference (metric system)": "19-49",
            "Metric (PT)": "Ureia",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mg/dL",
            "Metric (ES)": "Bureau (Urea biliar)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mg/dL"
        },
        {
            "Metric (EN)": "Creatinine",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/dL",
            "Reference (metric system)": "0.55-1.02",
            "Metric (PT)": "Creatinina",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mg/dL",
            "Metric (ES)": "Creatinina",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mg/dL"
        },
        {
            "Metric (EN)": "Triglycerides",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/dL",
            "Reference (metric system)": "<150",
            "Metric (PT)": "Triglicéridos",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mg/dL",
            "Metric (ES)": "Triglicéridos",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mg/dL"
        },
        {
            "Metric (EN)": "Total cholesterol",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/dL",
            "Reference (metric system)": "<190",
            "Metric (PT)": "Colesterol total",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mg/dL",
            "Metric (ES)": "Colesterol total",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mg/dL"
        },
        {
            "Metric (EN)": "HDL cholesterol",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/dL",
            "Reference (metric system)": ">45",
            "Metric (PT)": "Colesterol da fracção HDL",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mg/dL",
            "Metric (ES)": "Colesterol HDL",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mg/dL"
        },
        {
            "Metric (EN)": "LDL cholesterol",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/dL",
            "Reference (metric system)": "<116",
            "Metric (PT)": "Colesterol da fracção LDL",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mg/dL",
            "Metric (ES)": "Colesterol LDL",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mg/dL"
        },
        {
            "Metric (EN)": "Aspartate aminotransferase (AST/GOT)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "UI/L",
            "Reference (metric system)": "<34",
            "Metric (PT)": "Aspartato-aminotransferase (AST/GOT)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "UI/L",
            "Metric (ES)": "Aspartato aminotransferasa (AST/GOT)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "UI/L"
        },
        {
            "Metric (EN)": "Alanine aminotransferase (ALT/GPT)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "UI/L",
            "Reference (metric system)": "<49",
            "Metric (PT)": "Alanina-aminotransferase (ALT/GPT)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "UI/L",
            "Metric (ES)": "Alanina aminotransferasa (ALT/GPT)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "UI/L"
        },
        {
            "Metric (EN)": "Creatine kinase (CK/CPK)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "UI/L",
            "Reference (metric system)": "26-192",
            "Metric (PT)": "Creatina Quinase (CK/CPK)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "UI/L",
            "Metric (ES)": "Creatina quinasa (CK/CPK)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "UI/L"
        },
        {
            "Metric (EN)": "Sodium (Na)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mmol/L",
            "Reference (metric system)": "136-145",
            "Metric (PT)": "Sódio (Na)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mmol/L",
            "Metric (ES)": "Sodio (Na)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mmol/L"
        },
        {
            "Metric (EN)": "Potassium (K)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mmol/L",
            "Reference (metric system)": "3.5-5.1",
            "Metric (PT)": "Potássio (K)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mmol/L",
            "Metric (ES)": "Potasio (K)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mmol/L"
        },
        {
            "Metric (EN)": "Chlorine (Cl)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mmol/L",
            "Reference (metric system)": "98-107",
            "Metric (PT)": "Cloro (Cl)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mmol/L",
            "Metric (ES)": "Cloro (Cl)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mmol/L"
        },
        {
            "Metric (EN)": "Vitamin D (25-hydroxycalciferol)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "ng/mL",
            "Reference (metric system)": "30-100",
            "Metric (PT)": "Vitamina D (25-Hidroxicalciferol)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "ng/mL",
            "Metric (ES)": "Vitamina D (25-hidroxicalciferol)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "ng/mL"
        },
        {
            "Metric (EN)": "C-reactive protein (CRP)",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/dL",
            "Reference (metric system)": "<0.50",
            "Metric (PT)": "Proteína C reactiva (PCR)",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "mg/dL",
            "Metric (ES)": "Proteína C reactiva (PCR)",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "mg/dL"
        },
        {
            "Metric (EN)": "PSA",
            "Section (EN)": "Biochemistry",
            "Tab": "Analysis",
            "Unit (metric system EN)": "ng/mL",
            "Reference (metric system)": "<4.00",
            "Metric (PT)": "PSA, Antigénio Específico da Próstata",
            "Section (PT)": "Bioquímica",
            "Unit (metric system PT)": "ng/mL",
            "Metric (ES)": "PSA",
            "Section (ES)": "Bioquímica",
            "Unit (metric system ES)": "ng/mL"
        },
        # Lab Analysis - Endocrinology
        {
            "Metric (EN)": "Hormone Thyrostimulant (TSH)",
            "Section (EN)": "Endochronology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mUI/L",
            "Reference (metric system)": "0.55-4.78",
            "Metric (PT)": "Hormona tirostimulante (TSH)",
            "Section (PT)": "Endocronologia",
            "Unit (metric system PT)": "mUI/L",
            "Metric (ES)": "Hormona tiroestimulante (TSH)",
            "Section (ES)": "Endocronología",
            "Unit (metric system ES)": "mUI/L"
        },
        {
            "Metric (EN)": "Free thyroxine (FT4)",
            "Section (EN)": "Endochronology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "pmol/L",
            "Reference (metric system)": "10.3-34.7",
            "Metric (PT)": "Tiroxina livre (FT4)",
            "Section (PT)": "Endocronologia",
            "Unit (metric system PT)": "pmol/L",
            "Metric (ES)": "Tiroxina libre (FT4)",
            "Section (ES)": "Endocronología",
            "Unit (metric system ES)": "pmol/L"
        },
        {
            "Metric (EN)": "Free triiodothyronine (FT3)",
            "Section (EN)": "Endochronology",
            "Tab": "Analysis",
            "Unit (metric system EN)": "pmol/L",
            "Reference (metric system)": "3.5-6.5",
            "Metric (PT)": "Triiodotironina livre (FT3)",
            "Section (PT)": "Endocronologia",
            "Unit (metric system PT)": "pmol/L",
            "Metric (ES)": "Libre Triyodotironina (FT3)",
            "Section (ES)": "Endocronología",
            "Unit (metric system ES)": "pmol/L"
        },
        # Lab Analysis - Urine
        {
            "Metric (EN)": "Urine - color",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - cor",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Color de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - appearance",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - aspecto",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Aspecto de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - density",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - densidade",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Densidad de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - pH",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - pH",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Ph de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - protein",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - Proteínas",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Proteínas de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - glucose",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - Glucose",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Glucosa de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - ketone bodies",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - Corpos Cetónicos",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Cuerpos cetónicos de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - urobilinogen",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - Urobilinogénio",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Urobilinógeno de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - bilirubin",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - Bilirrubina",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Bilirrubina de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - nitrites",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - Nitritos",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Nitritos de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - leukocyte esterase (leukocytes)",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - Esterase leucocitária (Leucócitos)",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Esterasa leucocitaria (leucocitos)",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine - hemoglobin",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "",
            "Reference (metric system)": "",
            "Metric (PT)": "Urina - Hemoglobina",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "",
            "Metric (ES)": "Hemoglobina de la orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": ""
        },
        {
            "Metric (EN)": "Urine albumin-creatinine ratio (ACR)",
            "Section (EN)": "Urine",
            "Tab": "Analysis",
            "Unit (metric system EN)": "mg/g",
            "Reference (metric system)": "<30",
            "Metric (PT)": "Relação albumina-creatinina na urina (RAC)",
            "Section (PT)": "Urina",
            "Unit (metric system PT)": "mg/g",
            "Metric (ES)": "Relación albúmina-creatinina (RCA) en orina",
            "Section (ES)": "Orina",
            "Unit (metric system ES)": "mg/g"
        },
        {
            "Metric (EN)": "Blood pressure systolic",
            "Section (EN)": "Cardiovascular",
            "Tab": "Vitals",
            "Unit (metric system EN)": "mmHg",
            "Reference (metric system)": "90-120",
            "Metric (PT)": "Pressão arterial sistólica",
            "Section (PT)": "Cardiovascular",
            "Unit (metric system PT)": "mmHg",
            "Metric (ES)": "Presión arterial sistólica",
            "Section (ES)": "Cardiovascular",
            "Unit (metric system ES)": "mmHg"
        },
        {
            "Metric (EN)": "Blood pressure diastolic",
            "Section (EN)": "Cardiovascular",
            "Tab": "Vitals",
            "Unit (metric system EN)": "mmHg",
            "Reference (metric system)": "60-80",
            "Metric (PT)": "Pressão arterial diastólica",
            "Section (PT)": "Cardiovascular",
            "Unit (metric system PT)": "mmHg",
            "Metric (ES)": "Presión arterial diastólica",
            "Section (ES)": "Cardiovascular",
            "Unit (metric system ES)": "mmHg"
        },
        {
            "Metric (EN)": "Heart rate (resting)",
            "Section (EN)": "Cardiovascular",
            "Tab": "Vitals",
            "Unit (metric system EN)": "beats/min",
            "Reference (metric system)": "60-100",
            "Metric (PT)": "Frequência cardíaca (repouso)",
            "Section (PT)": "Cardiovascular",
            "Unit (metric system PT)": "pulsações/min",
            "Metric (ES)": "Frecuencia cardíaca (en reposo)",
            "Section (ES)": "Cardiovascular",
            "Unit (metric system ES)": "pulso/min"
        },
        {
            "Metric (EN)": "Heart rate (sleeping)",
            "Section (EN)": "Cardiovascular",
            "Tab": "Vitals",
            "Unit (metric system EN)": "beats/min",
            "Reference (metric system)": "40-60",
            "Metric (PT)": "Frequência cardíaca (a dormir)",
            "Section (PT)": "Cardiovascular",
            "Unit (metric system PT)": "pulsações/min",
            "Metric (ES)": "Frecuencia cardíaca (durante el sueño)",
            "Section (ES)": "Cardiovascular",
            "Unit (metric system ES)": "pulso/min"
        },
        {
            "Metric (EN)": "Respiratory rate (resting)",
            "Section (EN)": "Respiratory",
            "Tab": "Vitals",
            "Unit (metric system EN)": "breaths/min",
            "Reference (metric system)": "12-20",
            "Metric (PT)": "Frequência respiratória (repouso)",
            "Section (PT)": "Respiratório",
            "Unit (metric system PT)": "resp/min",
            "Metric (ES)": "Frecuencia respiratoria (en reposo)",
            "Section (ES)": "Respiratorio",
            "Unit (metric system ES)": "resp/min"
        },
        {
            "Metric (EN)": "Oxygen saturation",
            "Section (EN)": "Respiratory",
            "Tab": "Vitals",
            "Unit (metric system EN)": "%",
            "Reference (metric system)": ">95%",
            "Metric (PT)": "Saturação de oxigénio",
            "Section (PT)": "Respiratório",
            "Unit (metric system PT)": "%",
            "Metric (ES)": "Saturación de oxígeno",
            "Section (ES)": "Respiratorio",
            "Unit (metric system ES)": "%"
        },
        {
            "Metric (EN)": "Temperature",
            "Section (EN)": "Temperature",
            "Tab": "Vitals",
            "Unit (metric system EN)": "ºC",
            "Reference (metric system)": "36.1 - 37.2",
            "Metric (PT)": "Temperatura",
            "Section (PT)": "Temperatura",
            "Unit (metric system PT)": "ºC",
            "Metric (ES)": "Temperatura",
            "Section (ES)": "Temperatura",
            "Unit (metric system ES)": "ºC"
        },
        {
            "Metric (EN)": "Sleep time",
            "Section (EN)": "Sleep",
            "Tab": "Lifestyle",
            "Unit (metric system EN)": "Hours",
            "Reference (metric system)": "7-9",
            "Metric (PT)": "Tempo de sono",
            "Section (PT)": "Sono",
            "Unit (metric system PT)": "horas",
            "Metric (ES)": "Tiempo de sueño",
            "Section (ES)": "Sueño",
            "Unit (metric system ES)": "horas"
        },
        {
            "Metric (EN)": "Steps",
            "Section (EN)": "Activity",
            "Tab": "Lifestyle",
            "Unit (metric system EN)": "Number",
            "Reference (metric system)": ">8000",
            "Metric (PT)": "Passos",
            "Section (PT)": "Atividade",
            "Unit (metric system PT)": "número",
            "Metric (ES)": "Pasos",
            "Section (ES)": "Actividad",
            "Unit (metric system ES)": "número"
        },
        {
            "Metric (EN)": "Body Mass Index (BMI)",
            "Section (EN)": "Anthropometric Measurements",
            "Tab": "Body",
            "Unit (metric system EN)": "ratio",
            "Reference (metric system)": "18.5-24.5",
            "Metric (PT)": "Índice de Massa Corporal (IMC)",
            "Section (PT)": "Medidas Antropométricas",
            "Unit (metric system PT)": "ratio",
            "Metric (ES)": "Índice de masa corporal (IMC)",
            "Section (ES)": "Medidas antropométricas",
            "Unit (metric system ES)": "ratio"
        },
        {
            "Metric (EN)": "Waist circumference",
            "Section (EN)": "Anthropometric Measurements",
            "Tab": "Body",
            "Unit (metric system EN)": "cm",
            "Reference (metric system)": "Men: <94, Female: <80",
            "Metric (PT)": "Circunferência da cintura",
            "Section (PT)": "Medidas Antropométricas",
            "Unit (metric system PT)": "cm",
            "Metric (ES)": "Circunferencia de la cintura",
            "Section (ES)": "Medidas antropométricas",
            "Unit (metric system ES)": "cm"
        },
        {
            "Metric (EN)": "Waist-to-hip ratio (WHR)",
            "Section (EN)": "Anthropometric Measurements",
            "Tab": "Body",
            "Unit (metric system EN)": "ratio",
            "Reference (metric system)": "Men: >0.90, Female: >0.85",
            "Metric (PT)": "Relação cintura-anca (RCQ)",
            "Section (PT)": "Medidas Antropométricas",
            "Unit (metric system PT)": "ratio",
            "Metric (ES)": "Relación cintura-cadera (RCC)",
            "Section (ES)": "Medidas antropométricas",
            "Unit (metric system ES)": "ratio"
        },
        {
            "Metric (EN)": "Waist-to-height ratio (WHtR)",
            "Section (EN)": "Anthropometric Measurements",
            "Tab": "Body",
            "Unit (metric system EN)": "ratio",
            "Reference (metric system)": "<0.5",
            "Metric (PT)": "Relação cintura-altura (RCE)",
            "Section (PT)": "Atividade",
            "Unit (metric system PT)": "ratio",
            "Metric (ES)": "Relación cintura-estatura (RCT)",
            "Section (ES)": "Actividad",
            "Unit (metric system ES)": "ratio"
        },
        {
            "Metric (EN)": "Muscle-strengthening days",
            "Section (EN)": "Activity",
            "Tab": "Lifestyle",
            "Unit (metric system EN)": "days/week",
            "Reference (metric system)": "≥2",
            "Metric (PT)": "Dias de fortalecimento muscular",
            "Section (PT)": "Atividade",
            "Unit (metric system PT)": "dias/semana",
            "Metric (ES)": "Días de fortalecimiento muscular",
            "Section (ES)": "Actividad",
            "Unit (metric system ES)": "días/semana"
        },
        {
            "Metric (EN)": "Moderate aerobic activity (weekly)",
            "Section (EN)": "Activity",
            "Tab": "Lifestyle",
            "Unit (metric system EN)": "minutes/week",
            "Reference (metric system)": "150-300",
            "Metric (PT)": "Atividade aeróbica moderada (semanal)",
            "Section (PT)": "Cardiovascular",
            "Unit (metric system PT)": "minutos/semana",
            "Metric (ES)": "Actividad aeróbica moderada (semanal)",
            "Section (ES)": "Cardiovascular",
            "Unit (metric system ES)": "minutos/semana"
        },
        {
            "Metric (EN)": "Vigorous aerobic activity (weekly)",
            "Section (EN)": "Cardiovascular",
            "Tab": "Lifestyle",
            "Unit (metric system EN)": "minutes/week",
            "Reference (metric system)": "75-150",
            "Metric (PT)": "Atividade aeróbica vigorosa (semanal)",
            "Section (PT)": "Composição Corporal",
            "Unit (metric system PT)": "minutos/semana",
            "Metric (ES)": "Actividad aeróbica vigorosa (semanal)",
            "Section (ES)": "Composición corporal",
            "Unit (metric system ES)": "minutos/semana"
        },
        {
            "Metric (EN)": "Height",
            "Section (EN)": "Body composition",
            "Tab": "Body",
            "Unit (metric system EN)": "cm",
            "Reference (metric system)": "",
            "Metric (PT)": "Altura",
            "Section (PT)": "Composição Corporal",
            "Unit (metric system PT)": "cm",
            "Metric (ES)": "Estatura",
            "Section (ES)": "Composición corporal",
            "Unit (metric system ES)": "cm"
        },
        {
            "Metric (EN)": "Weight",
            "Section (EN)": "Body composition",
            "Tab": "Body",
            "Unit (metric system EN)": "kg",
            "Reference (metric system)": "",
            "Metric (PT)": "Peso",
            "Section (PT)": "Saúde Digital",
            "Unit (metric system PT)": "kg",
            "Metric (ES)": "Peso",
            "Section (ES)": "Salud digital",
            "Unit (metric system ES)": "kg"
        },
        {
            "Metric (EN)": "Screen time",
            "Section (EN)": "Digital health",
            "Tab": "Lifestyle",
            "Unit (metric system EN)": "hours",
            "Reference (metric system)": "<4",
            "Metric (PT)": "Tempo de ecrã",
            "Section (PT)": "Composição Corporal",
            "Unit (metric system PT)": "horas",
            "Metric (ES)": "Tiempo frente a la pantalla",
            "Section (ES)": "Composición corporal",
            "Unit (metric system ES)": "horas"
        },
        {
            "Metric (EN)": "Body fat %",
            "Section (EN)": "Body composition",
            "Tab": "Body",
            "Unit (metric system EN)": "%",
            "Reference (metric system)": "men: <25%, female: <35%",
            "Metric (PT)": "% de gordura corporal",
            "Section (PT)": "Composição Corporal",
            "Unit (metric system PT)": "%",
            "Metric (ES)": "% de grasa corporal",
            "Section (ES)": "Composición corporal",
            "Unit (metric system ES)": "%"
        },
        {
            "Metric (EN)": "Muscle mass %",
            "Section (EN)": "Body composition",
            "Tab": "Body",
            "Unit (metric system EN)": "%",
            "Reference (metric system)": "",
            "Metric (PT)": "% de massa muscular",
            "Section (PT)": "Corpo Composição",
            "Unit (metric system PT)": "%",
            "Metric (ES)": "% de masa muscular",
            "Section (ES)": "Cuerpo Composición",
            "Unit (metric system ES)": "%"
        },
        {
            "Metric (EN)": "Visceral fat",
            "Section (EN)": "Body composition",
            "Tab": "Body",
            "Unit (metric system EN)": "rating",
            "Reference (metric system)": "<12",
            "Metric (PT)": "Gordura visceral",
            "Section (PT)": "Hematologia",
            "Unit (metric system PT)": "rating",
            "Metric (ES)": "Grasa visceral",
            "Section (ES)": "Hematología",
            "Unit (metric system ES)": "rating"
        }
    ]
    
    try:
        # Get database session
        db = next(get_db())
        
        # Create importer
        importer = AdminTemplateImporter(db, 0)  # Will be set after getting admin user
        
        # Get or create admin user
        admin_user_id = importer.get_or_create_admin_user()
        importer.admin_user_id = admin_user_id
        
        # Import templates
        importer.import_templates(raw_data)
        
        logger.info("Admin template import completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during import: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()
