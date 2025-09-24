from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime

from app.models.health_record import HealthRecordImage, ImageType, ImageFindings

class MedicalImageCRUD:
    def create(
        self,
        db: Session,
        user_id: int,
        image_type: str,
        body_part: str,
        image_date: str,
        findings: str,
        conclusions: str,
        original_filename: str,
        file_size_bytes: int,
        content_type: str,
        s3_key: str,
        doctor_name: str = "",
        doctor_number: str = "",
        interpretation: str = ""
    ) -> HealthRecordImage:
        """Create a new medical image record"""
        # Map exam_type to ImageType enum
        image_type_enum = ImageType.Others
        if image_type == "X-Ray":
            image_type_enum = ImageType.X_Ray
        elif image_type == "Ultrasound":
            image_type_enum = ImageType.Ultrasound
        elif image_type == "ECG":
            image_type_enum = ImageType.ECG
        
        # Map conclusions to ImageFindings enum
        findings_enum = ImageFindings.No_Findings
        if findings and "relevant" in findings.lower():
            findings_enum = ImageFindings.Relevant_Findings
        elif findings and ("low" in findings.lower() or "minor" in findings.lower()):
            findings_enum = ImageFindings.Low_Risk_Findings
        
        # Parse image date
        parsed_date = None
        if image_date:
            try:
                # Try different date formats
                for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]:
                    try:
                        parsed_date = datetime.strptime(image_date, fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                parsed_date = datetime.now()
        else:
            parsed_date = datetime.now()
        
        medical_image = HealthRecordImage(
            created_by=user_id,
            image_type=image_type_enum,
            body_part=body_part,
            image_date=parsed_date,
            findings=findings_enum,
            conclusions=conclusions,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
            s3_key=s3_key,
            doctor_name=doctor_name,
            doctor_number=doctor_number,
            interpretation=interpretation
        )
        
        db.add(medical_image)
        db.commit()
        db.refresh(medical_image)
        return medical_image
    
    def get_by_id(self, db: Session, image_id: int) -> Optional[HealthRecordImage]:
        """Get a medical image by ID"""
        return db.query(HealthRecordImage).filter(HealthRecordImage.id == image_id).first()
    
    def get_by_user(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[HealthRecordImage]:
        """Get medical images for a user with pagination"""
        return (
            db.query(HealthRecordImage)
            .filter(HealthRecordImage.created_by == user_id)
            .order_by(HealthRecordImage.image_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def count_by_user(self, db: Session, user_id: int) -> int:
        """Count medical images for a user"""
        return (
            db.query(func.count(HealthRecordImage.id))
            .filter(HealthRecordImage.created_by == user_id)
            .scalar()
        )
    
    def delete(self, db: Session, image_id: int) -> bool:
        """Delete a medical image"""
        medical_image = db.query(HealthRecordImage).filter(HealthRecordImage.id == image_id).first()
        if medical_image:
            db.delete(medical_image)
            db.commit()
            return True
        return False
    
    def update(
        self,
        db: Session,
        image_id: int,
        **kwargs
    ) -> Optional[HealthRecordImage]:
        """Update a medical image"""
        medical_image = db.query(HealthRecordImage).filter(HealthRecordImage.id == image_id).first()
        if medical_image:
            for key, value in kwargs.items():
                if hasattr(medical_image, key):
                    setattr(medical_image, key, value)
            db.commit()
            db.refresh(medical_image)
        return medical_image
