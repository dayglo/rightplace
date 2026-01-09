"""
Enrollment endpoints for Prison Roll Call API.

Provides endpoints for enrolling inmate faces.
"""
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_face_recognition_service
from app.models.face import (
    EnrollmentSuccessResponse,
    EnrollmentErrorResponse,
    InmateNotFoundResponse,
)
from app.services.face_recognition import FaceRecognitionService

logger = logging.getLogger(__name__)

router = APIRouter()

# File size limit: 2MB as per design spec
MAX_FILE_SIZE = 2 * 1024 * 1024


@router.post("/enrollment/{inmate_id}")
async def enroll_inmate(
    inmate_id: str,
    image: UploadFile = File(...),
    service: FaceRecognitionService = Depends(get_face_recognition_service),
):
    """
    Enroll an inmate's face for recognition.
    
    This endpoint accepts an image file and enrolls the inmate's face
    by extracting and storing their face embedding. The image must meet
    quality requirements to be accepted.
    
    Args:
        inmate_id: Inmate ID to enroll
        image: Uploaded image file (JPEG, PNG)
        service: Face recognition service instance
        
    Returns:
        EnrollmentSuccessResponse: Enrollment succeeded (200)
        EnrollmentErrorResponse: Quality/detection issues (400)
        InmateNotFoundResponse: Inmate not found (404)
        
    Raises:
        HTTPException: 400 if file is not an image or too large
    """
    # Validate file is an image
    if not image.content_type or not image.content_type.startswith("image/"):
        logger.warning(f"Invalid file type: {image.content_type}")
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG, PNG, etc.)"
        )
    
    # Read file content to check size
    file_content = await image.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE})")
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size} bytes) exceeds maximum ({MAX_FILE_SIZE} bytes)"
        )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(file_content)
        tmp_path = Path(tmp.name)
    
    try:
        # Perform enrollment
        logger.info(f"Enrolling inmate {inmate_id} ({file_size} bytes)")
        result = service.enroll_face(inmate_id, tmp_path)
        
        # Check if inmate was found
        if "not found" in result.message.lower():
            logger.error(f"Inmate {inmate_id} not found")
            raise HTTPException(
                status_code=404,
                detail=InmateNotFoundResponse(
                    error="inmate_not_found",
                    message=result.message
                ).dict()
            )
        
        # If enrollment succeeded
        if result.success:
            logger.info(
                f"Successfully enrolled inmate {inmate_id} with quality {result.quality:.2f}"
            )
            
            # Get embedder model version
            model_version = service.embedder.model
            
            return EnrollmentSuccessResponse(
                success=True,
                inmate_id=inmate_id,
                quality=result.quality,
                enrolled_at=result.enrolled_at.isoformat() if result.enrolled_at else "",
                embedding_version=model_version
            )
        
        # Enrollment failed due to quality/detection issues
        logger.warning(
            f"Enrollment failed for inmate {inmate_id}: {result.message}"
        )
        
        # Convert QualityIssue enums to strings
        quality_issues_str = [issue.value for issue in result.quality_issues]
        
        # Determine error code based on message
        error_code = "enrollment_failed"
        if "no face" in result.message.lower():
            error_code = "no_face_detected"
        elif "multiple" in result.message.lower():
            error_code = "multiple_faces"
        elif "quality" in result.message.lower():
            error_code = "quality_too_low"
        
        raise HTTPException(
            status_code=400,
            detail=EnrollmentErrorResponse(
                success=False,
                error=error_code,
                quality=result.quality,
                quality_issues=quality_issues_str,
                message=result.message
            ).dict()
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error during enrollment: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
    
    finally:
        # Cleanup temporary file
        try:
            tmp_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {tmp_path}: {e}")