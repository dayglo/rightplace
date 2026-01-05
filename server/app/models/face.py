"""
Face recognition data models.

Defines models for face detection, landmarks, quality assessment, and matching results.
"""
from enum import Enum

from pydantic import BaseModel

from app.models.inmate import Inmate


class BoundingBox(BaseModel):
    """Face detection bounding box coordinates."""

    x: int
    y: int
    width: int
    height: int


class FaceLandmarks(BaseModel):
    """5-point facial landmarks for alignment."""

    left_eye: tuple[int, int]
    right_eye: tuple[int, int]
    nose: tuple[int, int]
    left_mouth: tuple[int, int]
    right_mouth: tuple[int, int]


class QualityIssue(str, Enum):
    """Image quality issues affecting recognition."""

    NO_FACE = "no_face"
    MULTI_FACE = "multi_face"
    LOW_LIGHT = "low_light"
    BLUR = "blur"
    ANGLE = "angle"
    OCCLUSION = "occlusion"
    TOO_FAR = "too_far"
    TOO_CLOSE = "too_close"


class DetectionResult(BaseModel):
    """Face detection output with quality assessment."""

    detected: bool
    face_count: int
    bounding_box: BoundingBox | None
    landmarks: FaceLandmarks | None
    quality: float
    quality_issues: list[QualityIssue]


class MatchRecommendation(str, Enum):
    """Recommended action based on confidence score."""

    AUTO_ACCEPT = "auto_accept"
    CONFIRM = "confirm"
    REVIEW = "review"
    NO_MATCH = "no_match"


class MatchResult(BaseModel):
    """Face matching result with confidence and recommendation."""

    matched: bool
    inmate_id: str | None
    inmate: Inmate | None
    confidence: float
    threshold_used: float
    recommendation: MatchRecommendation
    at_expected_location: bool | None
    all_matches: list[dict]
    detection: DetectionResult
