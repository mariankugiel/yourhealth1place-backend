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
from app.models.user import User
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
            "Analysis": 1,  # Analysis tab
            "Vitals": 2,     # Vitals tab
            "Body": 3,       # Body Composition tab
            "Lifestyle": 4, # Lifestyle tab
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
            User.is_superuser == True
        ).first()
        
        if admin_user:
            logger.info(f"Found existing admin user: {admin_user.id}")
            return admin_user.id
        
        # Create admin user if not found
        admin_data = {
            "supabase_user_id": "admin-system",
            "email": "admin@saluso.com",
            "is_active": True,
            "is_superuser": True
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
        
        # Create new section template
        section_template_data = {
            "name": section_data["name"],
            "display_name": section_data["display_name"],
            "display_name_pt": section_data.get("display_name_pt"),
            "display_name_es": section_data.get("display_name_es"),
            "description": f"Admin-defined {section_data['display_name']} section",
            "health_record_type_id": health_record_type_id,
            "is_active": True,
            "is_default": True,
            "created_by": self.admin_user_id
        }
        
        section_template = self.section_crud.create(self.db, section_template_data)
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
        
        # Create new metric template
        metric_template_data = {
            "section_template_id": section_template.id,
            "name": metric_data["name"],
            "display_name": metric_data["display_name"],
            "display_name_pt": metric_data.get("display_name_pt"),
            "display_name_es": metric_data.get("display_name_es"),
            "description": f"Admin-defined {metric_data['display_name']} metric",
            "default_unit": metric_data.get("unit"),
            "default_unit_pt": metric_data.get("unit_pt"),
            "default_unit_es": metric_data.get("unit_es"),
            "original_reference": metric_data.get("reference"),
            "reference_data": metric_data.get("reference_data"),
            "data_type": metric_data.get("data_type", "number"),
            "is_active": True,
            "is_default": True,
            "created_by": self.admin_user_id
        }
        
        metric_template = self.metric_crud.create(self.db, metric_template_data)
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
