"""
Face Detection wrapper using DeepFace.

This module provides a clean interface for face detection using DeepFace
with RetinaFace backend (fallback to MTCNN or OpenCV if needed).
"""

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from deepface import DeepFace

from app.models.face import (
    BoundingBox,
    DetectionResult,
    FaceLandmarks,
    QualityIssue,
)

logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Face detector using DeepFace with RetinaFace backend.
    
    This class wraps DeepFace's face detection capabilities and provides
    a clean interface that returns structured detection results.
    """
    
    def __init__(self, backend: str = "retinaface"):
        """
        Initialize the face detector.
        
        Args:
            backend: Detection backend to use. Options:
                - "retinaface" (default, most accurate)
                - "mtcnn" (fallback)
                - "opencv" (fastest, least accurate)
                - "ssd"
        """
        self.backend = backend
        logger.info(f"Initialized FaceDetector with backend: {backend}")
    
    def detect(self, image_path: str | Path) -> DetectionResult:
        """
        Detect face in an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            DetectionResult with detection info, bounding box, landmarks, quality
            
        Example:
            >>> detector = FaceDetector()
            >>> result = detector.detect("image.jpg")
            >>> if result.detected:
            ...     print(f"Face found at {result.bounding_box}")
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return self._no_face_result([QualityIssue.NO_FACE])
        
        try:
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Failed to read image: {image_path}")
                return self._no_face_result([QualityIssue.NO_FACE])
            
            # Detect faces using DeepFace
            faces = DeepFace.extract_faces(
                img_path=str(image_path),
                detector_backend=self.backend,
                enforce_detection=False,
                align=True,
            )
            
            if not faces or len(faces) == 0:
                logger.warning(f"No faces detected in {image_path}")
                return self._no_face_result([QualityIssue.NO_FACE])
            
            if len(faces) > 1:
                logger.warning(f"Multiple faces detected ({len(faces)}) in {image_path}")
                # Return the largest face but flag multi-face issue
                face = max(faces, key=lambda f: f.get('facial_area', {}).get('w', 0) * f.get('facial_area', {}).get('h', 0))
                quality_issues = [QualityIssue.MULTI_FACE]
            else:
                face = faces[0]
                quality_issues = []
            
            # Extract bounding box
            facial_area = face.get('facial_area', {})
            bounding_box = BoundingBox(
                x=facial_area.get('x', 0),
                y=facial_area.get('y', 0),
                width=facial_area.get('w', 0),
                height=facial_area.get('h', 0),
            )
            
            # Extract landmarks (if available)
            landmarks = None
            if 'left_eye' in face:
                landmarks = FaceLandmarks(
                    left_eye=(int(face['left_eye'][0]), int(face['left_eye'][1])),
                    right_eye=(int(face['right_eye'][0]), int(face['right_eye'][1])),
                    nose=(int(face['nose'][0]), int(face['nose'][1])),
                    left_mouth=(int(face['mouth_left'][0]), int(face['mouth_left'][1])),
                    right_mouth=(int(face['mouth_right'][0]), int(face['mouth_right'][1])),
                )
            
            # Calculate quality score
            confidence = face.get('confidence', 0.0)
            quality, additional_issues = self._assess_quality(img, bounding_box, confidence)
            quality_issues.extend(additional_issues)
            
            return DetectionResult(
                detected=True,
                face_count=len(faces),
                bounding_box=bounding_box,
                landmarks=landmarks,
                quality=quality,
                quality_issues=quality_issues,
            )
            
        except Exception as e:
            logger.error(f"Error detecting face in {image_path}: {e}", exc_info=True)
            return self._no_face_result([QualityIssue.NO_FACE])
    
    def detect_from_array(self, img: np.ndarray) -> DetectionResult:
        """
        Detect face from numpy array (useful for camera frames).
        
        Args:
            img: Image as numpy array (BGR format)
            
        Returns:
            DetectionResult
        """
        try:
            # Detect faces using DeepFace
            faces = DeepFace.extract_faces(
                img_path=img,
                detector_backend=self.backend,
                enforce_detection=False,
                align=True,
            )
            
            if not faces or len(faces) == 0:
                return self._no_face_result([QualityIssue.NO_FACE])
            
            if len(faces) > 1:
                logger.warning(f"Multiple faces detected ({len(faces)})")
                face = max(faces, key=lambda f: f.get('facial_area', {}).get('w', 0) * f.get('facial_area', {}).get('h', 0))
                quality_issues = [QualityIssue.MULTI_FACE]
            else:
                face = faces[0]
                quality_issues = []
            
            # Extract bounding box
            facial_area = face.get('facial_area', {})
            bounding_box = BoundingBox(
                x=facial_area.get('x', 0),
                y=facial_area.get('y', 0),
                width=facial_area.get('w', 0),
                height=facial_area.get('h', 0),
            )
            
            # Extract landmarks
            landmarks = None
            if 'left_eye' in face:
                landmarks = FaceLandmarks(
                    left_eye=(int(face['left_eye'][0]), int(face['left_eye'][1])),
                    right_eye=(int(face['right_eye'][0]), int(face['right_eye'][1])),
                    nose=(int(face['nose'][0]), int(face['nose'][1])),
                    left_mouth=(int(face['mouth_left'][0]), int(face['mouth_left'][1])),
                    right_mouth=(int(face['mouth_right'][0]), int(face['mouth_right'][1])),
                )
            
            # Calculate quality
            confidence = face.get('confidence', 0.0)
            quality, additional_issues = self._assess_quality(img, bounding_box, confidence)
            quality_issues.extend(additional_issues)
            
            return DetectionResult(
                detected=True,
                face_count=len(faces),
                bounding_box=bounding_box,
                landmarks=landmarks,
                quality=quality,
                quality_issues=quality_issues,
            )
            
        except Exception as e:
            logger.error(f"Error detecting face from array: {e}", exc_info=True)
            return self._no_face_result([QualityIssue.NO_FACE])
    
    def _assess_quality(
        self, 
        img: np.ndarray, 
        bbox: BoundingBox,
        confidence: float
    ) -> tuple[float, list[QualityIssue]]:
        """
        Assess image quality for face recognition.
        
        Args:
            img: Image array
            bbox: Bounding box of detected face
            confidence: Detection confidence from detector
            
        Returns:
            Tuple of (quality_score, list of quality issues)
        """
        issues = []
        quality_score = confidence  # Start with detector confidence
        
        # Extract face region
        y1 = max(0, bbox.y)
        y2 = min(img.shape[0], bbox.y + bbox.height)
        x1 = max(0, bbox.x)
        x2 = min(img.shape[1], bbox.x + bbox.width)
        face_img = img[y1:y2, x1:x2]
        
        if face_img.size == 0:
            return 0.0, [QualityIssue.TOO_FAR]
        
        # Check face size
        face_area = bbox.width * bbox.height
        image_area = img.shape[0] * img.shape[1]
        face_ratio = face_area / image_area
        
        if face_ratio < 0.02:  # Too small (< 2% of image)
            issues.append(QualityIssue.TOO_FAR)
            quality_score *= 0.7
        elif face_ratio > 0.8:  # Too large (> 80% of image)
            issues.append(QualityIssue.TOO_CLOSE)
            quality_score *= 0.9
        
        # Check brightness
        gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray_face)
        
        if mean_brightness < 50:  # Too dark
            issues.append(QualityIssue.LOW_LIGHT)
            quality_score *= 0.6
        elif mean_brightness > 220:  # Too bright
            issues.append(QualityIssue.LOW_LIGHT)
            quality_score *= 0.8
        
        # Check blur using Laplacian variance
        laplacian = cv2.Laplacian(gray_face, cv2.CV_64F)
        blur_score = laplacian.var()
        
        if blur_score < 100:  # Blurry image
            issues.append(QualityIssue.BLUR)
            quality_score *= 0.6
        
        # Ensure quality is between 0 and 1
        quality_score = max(0.0, min(1.0, quality_score))
        
        return quality_score, issues
    
    def _no_face_result(self, issues: list[QualityIssue]) -> DetectionResult:
        """Create a 'no face detected' result."""
        return DetectionResult(
            detected=False,
            face_count=0,
            bounding_box=None,
            landmarks=None,
            quality=0.0,
            quality_issues=issues,
        )
