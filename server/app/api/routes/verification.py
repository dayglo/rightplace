"""
Face detection and verification endpoints for Prison Roll Call API.

Provides endpoints for face detection, enrollment, and verification.
"""
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.dependencies import get_face_recognition_service
from app.models.face import DetectionResult, MatchResult
from app.services.face_recognition import FaceRecognitionService

logger = logging.getLogger(__name__)

router = APIRouter()

# File size limit: 2MB as per design spec
MAX_FILE_SIZE = 2 * 1024 * 1024


@router.post("/detect", response_model=DetectionResult)
async def detect_face(
    image: UploadFile = File(...),
    service: FaceRecognitionService = Depends(get_face_recognition_service),
):
    """
    Detect face in uploaded image.
    
    This endpoint accepts an image file and performs face detection,
    returning detection results including bounding box, landmarks,
    and quality assessment.
    
    Args:
        image: Uploaded image file (JPEG, PNG)
        service: Face recognition service instance
        
    Returns:
        DetectionResult: Detection results with face info and quality
        
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
        # Perform detection
        logger.info(f"Detecting face in uploaded image ({file_size} bytes)")
        result = service.detect_face(tmp_path)
        
        logger.info(
            f"Detection complete: detected={result.detected}, "
            f"face_count={result.face_count}, quality={result.quality:.2f}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error during face detection: {e}", exc_info=True)
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


@router.post("/verify/quick", response_model=MatchResult)
async def verify_quick(
    image: UploadFile = File(...),
    location_id: str = Form(...),
    roll_call_id: str = Form(...),
    service: FaceRecognitionService = Depends(get_face_recognition_service),
):
    """
    Quick verify face at a location during roll call.
    
    This endpoint accepts an image and performs face verification
    against enrolled inmates, optionally checking if the matched
    inmate is expected at the given location.
    
    Args:
        image: Uploaded image file (JPEG, PNG)
        location_id: Location ID where verification is happening
        roll_call_id: Roll call ID for this verification
        service: Face recognition service instance
        
    Returns:
        MatchResult: Verification result with match details
        
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
        # Perform verification
        logger.info(
            f"Verifying face at location {location_id} "
            f"for roll call {roll_call_id} ({file_size} bytes)"
        )
        result = service.verify_face(tmp_path, location_id=location_id)
        
        logger.info(
            f"Verification complete: matched={result.matched}, "
            f"confidence={result.confidence:.2f}, "
            f"recommendation={result.recommendation.value}"
        )
        
        return result
    
    except ValueError as e:
        # Handle face detection/extraction failures gracefully
        # This can happen when no face is detected or image quality is too poor
        logger.warning(f"Face detection/extraction failed: {e}")
        
        # Return a no-match result with empty detection
        from app.models.face import MatchResult, DetectionResult, MatchRecommendation, QualityIssue
        return MatchResult(
            matched=False,
            inmate_id=None,
            inmate=None,
            confidence=0.0,
            threshold_used=service.policy.verification_threshold,
            recommendation=MatchRecommendation.NO_MATCH,
            at_expected_location=None,
            all_matches=[],
            detection=DetectionResult(
                detected=False,
                face_count=0,
                bounding_box=None,
                landmarks=None,
                quality=0.0,
                quality_issues=[QualityIssue.NO_FACE],
            ),
        )
    
    except Exception as e:
        logger.error(f"Error during verification: {e}", exc_info=True)
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


@router.post("/verify", response_model=MatchResult)
async def verify(
    image: UploadFile = File(...),
    service: FaceRecognitionService = Depends(get_face_recognition_service),
):
    """
    Verify face against all enrolled inmates.
    
    This endpoint accepts an image and performs face verification
    against all enrolled inmates in the system.
    
    Args:
        image: Uploaded image file (JPEG, PNG)
        service: Face recognition service instance
        
    Returns:
        MatchResult: Verification result with match details
        
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
        # Perform verification
        logger.info(f"Verifying face ({file_size} bytes)")
        result = service.verify_face(tmp_path)
        
        logger.info(
            f"Verification complete: matched={result.matched}, "
            f"confidence={result.confidence:.2f}"
        )
        
        return result
    
    except ValueError as e:
        # Handle face detection/extraction failures gracefully
        logger.warning(f"Face detection/extraction failed: {e}")
        
        # Return a no-match result with empty detection
        from app.models.face import MatchResult, DetectionResult, MatchRecommendation, QualityIssue
        return MatchResult(
            matched=False,
            inmate_id=None,
            inmate=None,
            confidence=0.0,
            threshold_used=service.policy.verification_threshold,
            recommendation=MatchRecommendation.NO_MATCH,
            at_expected_location=None,
            all_matches=[],
            detection=DetectionResult(
                detected=False,
                face_count=0,
                bounding_box=None,
                landmarks=None,
                quality=0.0,
                quality_issues=[QualityIssue.NO_FACE],
            ),
        )
    
    except Exception as e:
        logger.error(f"Error during verification: {e}", exc_info=True)
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
