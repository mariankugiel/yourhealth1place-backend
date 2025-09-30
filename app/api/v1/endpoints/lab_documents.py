from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.core.database import get_db
from app.services.lab_document_analysis_service import LabDocumentAnalysisService
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the lab document analysis service
lab_service = LabDocumentAnalysisService()

# Pydantic models for bulk processing
class LabRecordData(BaseModel):
    lab_name: str
    type_of_analysis: str
    metric_name: str
    date_of_value: str
    value: str
    unit: str
    reference: str

class BulkLabRecordsRequest(BaseModel):
    records: List[LabRecordData]
    file_name: str
    description: Optional[str] = None
    s3_url: Optional[str] = None
    lab_test_date: Optional[str] = None
    lab_test_name: Optional[str] = None
    provider: Optional[str] = None

@router.post("/upload", response_model=dict)
async def upload_and_analyze_lab_document(
    file: UploadFile = File(..., description="Lab report PDF file"),
    description: Optional[str] = Form(None, description="Optional description for the document"),
    doc_date: Optional[str] = Form(None, description="Document date"),
    doc_type: Optional[str] = Form(None, description="Document type"),
    provider: Optional[str] = Form(None, description="Healthcare provider"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze a lab report PDF document (extraction only)
    
    This endpoint will:
    1. Store the PDF in AWS S3
    2. Extract text using pdfplumber
    3. Parse lab metrics using the multilingual extraction logic
    4. Return extracted data for user review (no health records created)
    
    Use /bulk endpoint to create health records after user confirmation.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for lab document analysis"
            )
        
        # Validate file size (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Extract lab data only (no health records created)
        lab_data = lab_service._extract_lab_data_advanced(
            lab_service._extract_text_from_pdf(file_content)
        )
        
        # Upload to S3
        s3_url = None
        try:
            s3_url = await lab_service._upload_to_s3(file_content, file.filename, str(current_user.id))
        except Exception as s3_error:
            logger.error(f"Failed to upload file to S3: {s3_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {str(s3_error)}"
            )
        
        logger.info(f"Successfully extracted {len(lab_data)} lab records for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Lab document analyzed successfully",
            "s3_url": s3_url,
            "lab_data": lab_data,
            "extracted_records_count": len(lab_data),
            "form_data": {
                "doc_date": doc_date,
                "doc_type": doc_type,
                "provider": provider,
                "description": description
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze lab document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze lab document: {str(e)}"
        )

@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get information about supported lab document formats
    """
    return {
        "supported_formats": ["PDF"],
        "max_file_size": "10MB",
        "supported_languages": [
            "Portuguese (PT)", "Spanish (ES)", "English (EN)", "French (FR)",
            "German (DE)", "Italian (IT)", "Polish (PL)", "Dutch (NL)",
            "Danish (DA)", "Swedish (SV)", "Norwegian (NO)", "Greek (EL)",
            "Croatian (HR)", "Serbian (SR)", "Romanian (RO)", "Bulgarian (BG)",
            "Turkish (TR)"
        ],
        "extraction_capabilities": [
            "Lab metrics and values",
            "Reference ranges",
            "Units and measurements",
            "Date extraction",
            "Lab name detection",
            "Section classification (Hematology, Biochemistry, Urine)",
            "Multi-language support"
        ],
        "output_format": {
            "health_records": "Stored in database with structured data",
            "document_storage": "PDF stored in AWS S3",
            "metadata": "Document information and analysis summary"
        }
    }

@router.get("/extraction-example")
async def get_extraction_example():
    """
    Get an example of what data is extracted from lab documents
    """
    return {
        "example_input": "Lab report PDF with metrics like:",
        "example_metrics": [
            {
                "metric_name": "Hemoglobin",
                "value": "14.2",
                "unit": "g/dL",
                "reference": "12.0-16.0",
                "status": "normal",
                "type_of_analysis": "HEMATOLOGIA"
            },
            {
                "metric_name": "Glucose",
                "value": "95",
                "unit": "mg/dL",
                "reference": "70-100",
                "status": "normal",
                "type_of_analysis": "BIOQUIMICA"
            },
            {
                "metric_name": "Urine Color",
                "value": "Amarela",
                "unit": "",
                "reference": "",
                "status": "text_value",
                "type_of_analysis": "URINA E DOSEAMENTOS URINÁRIOS"
            }
        ],
        "extraction_features": [
            "Automatic section detection",
            "Reference range parsing",
            "Unit normalization",
            "Status determination (normal/low/high)",
            "Date extraction and canonicalization",
            "Lab name identification",
            "Multi-language metric recognition"
        ]
    }

@router.post("/bulk", response_model=dict)
async def bulk_create_lab_records(
    request: BulkLabRecordsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk create health records from lab document analysis results
    
    This endpoint will:
    1. Create sections and metrics if they don't exist
    2. Create health records for all provided lab data
    3. Return summary of created records
    """
    try:
        logger.info(f"Starting bulk creation of {len(request.records)} lab records for user {current_user.id}")
        
        # Create medical document record first
        medical_doc = await lab_service._create_medical_document(
            db=db,
            user_id=current_user.id,
            file_name=request.file_name,
            s3_url=request.s3_url or "",  # Use S3 URL from request
            description=request.description,
            lab_test_date=request.lab_test_date,
            lab_test_name=request.lab_test_name,
            provider=request.provider
        )
        
        created_records = []
        created_sections = []
        created_metrics = []
        
        # Process each record
        for record_data in request.records:
            try:
                # Get or create section
                section = await lab_service._get_or_create_section(
                    db=db,
                    user_id=current_user.id,
                    section_type=record_data.type_of_analysis
                )
                
                if section.id not in [s.id for s in created_sections]:
                    created_sections.append(section)
                
                # Get or create metric
                metric = await lab_service._get_or_create_metric(
                    db=db,
                    user_id=current_user.id,
                    section_id=section.id,
                    record_data=record_data.dict()
                )
                
                if metric.id not in [m.id for m in created_metrics]:
                    created_metrics.append(metric)
                
                # Create health record
                health_record = await lab_service._create_health_record_from_lab_data(
                    db=db,
                    user_id=current_user.id,
                    record_data=record_data.dict()
                )
                
                if health_record:
                    created_records.append(health_record)
                    
            except Exception as e:
                logger.error(f"Failed to create health record for {record_data.metric_name}: {e}")
                continue
        
        logger.info(f"Successfully created {len(created_records)} health records, {len(created_sections)} sections, {len(created_metrics)} metrics")
        
        # Check if any records were created successfully
        if len(created_records) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create any health records. Please check the logs for details."
            )
        
        return {
            "success": True,
            "message": f"Successfully created {len(created_records)} health records",
            "created_records_count": len(created_records),
            "created_sections_count": len(created_sections),
            "created_metrics_count": len(created_metrics),
            "medical_document_id": medical_doc.id
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk create lab records: {e}")
        
        # Clean up S3 file if it was uploaded but processing failed
        if request.s3_url:
            try:
                from app.core.aws_service import aws_service
                cleanup_success = aws_service.delete_document(request.s3_url)
                if cleanup_success:
                    logger.info(f"Cleaned up S3 file after processing failure: {request.s3_url}")
                else:
                    logger.warning(f"Failed to clean up S3 file after processing failure: {request.s3_url}")
            except Exception as cleanup_error:
                logger.error(f"Error during S3 cleanup: {cleanup_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lab records: {str(e)}"
        )




