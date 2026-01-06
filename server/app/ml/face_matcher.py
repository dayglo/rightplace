"""
Face Matcher for 1:N matching using cosine similarity.

This module provides efficient face matching functionality using
pre-extracted embeddings and cosine similarity.
"""

import logging
from typing import Optional

import numpy as np

from app.models.face import MatchRecommendation, MatchResult

logger = logging.getLogger(__name__)


class FaceMatcher:
    """
    Face matcher using cosine similarity for 1:N matching.
    
    This class performs efficient matching of a query embedding against
    a database of enrolled embeddings using cosine similarity.
    """
    
    def __init__(
        self,
        threshold: float = 0.75,
        auto_accept_threshold: float = 0.92,
        review_threshold: float = 0.60
    ):
        """
        Initialize the face matcher.
        
        Args:
            threshold: Minimum similarity for a match (default: 0.75)
            auto_accept_threshold: Threshold for auto-accept recommendation (default: 0.92)
            review_threshold: Threshold for review recommendation (default: 0.60)
        """
        self.threshold = threshold
        self.auto_accept_threshold = auto_accept_threshold
        self.review_threshold = review_threshold
        
        logger.info(
            f"Initialized FaceMatcher with thresholds: "
            f"match={threshold}, auto_accept={auto_accept_threshold}, review={review_threshold}"
        )
    
    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Since our embeddings are L2-normalized, cosine similarity
        simplifies to the dot product.
        
        Args:
            embedding1: First embedding (512-dim normalized vector)
            embedding2: Second embedding (512-dim normalized vector)
            
        Returns:
            Cosine similarity in range [-1, 1], where:
            - 1.0 = identical
            - 0.0 = orthogonal (unrelated)
            - -1.0 = opposite
        """
        # Cosine similarity for normalized vectors is just the dot product
        similarity = float(np.dot(embedding1, embedding2))
        
        return similarity
    
    def get_recommendation(self, confidence: float) -> MatchRecommendation:
        """
        Get match recommendation based on confidence score.
        
        Thresholds (from FaceRecognitionPolicy):
        - ≥0.92: AUTO_ACCEPT (high confidence)
        - 0.75-0.91: CONFIRM (suggest match, officer confirms)
        - 0.60-0.74: REVIEW (low confidence, manual review)
        - <0.60: NO_MATCH (below verification threshold)
        
        Args:
            confidence: Similarity score between 0 and 1
            
        Returns:
            MatchRecommendation enum value
        """
        if confidence >= self.auto_accept_threshold:
            return MatchRecommendation.AUTO_ACCEPT
        elif confidence >= self.threshold:
            return MatchRecommendation.CONFIRM
        elif confidence >= self.review_threshold:
            return MatchRecommendation.REVIEW
        else:
            return MatchRecommendation.NO_MATCH
    
    def find_match(
        self,
        query_embedding: np.ndarray,
        enrolled_embeddings: dict[str, np.ndarray]
    ) -> MatchResult:
        """
        Find best match for query embedding in enrolled database.
        
        Performs 1:N matching by comparing the query embedding against
        all enrolled embeddings using cosine similarity.
        
        Args:
            query_embedding: Query face embedding (512-dim normalized vector)
            enrolled_embeddings: Dictionary mapping inmate_id to embedding
            
        Returns:
            MatchResult with best match, confidence, and recommendation
        """
        if not enrolled_embeddings:
            logger.warning("Empty enrollment database - no matches possible")
            return self._no_match_result()
        
        # Calculate similarities for all enrolled embeddings
        matches = []
        for inmate_id, enrolled_embedding in enrolled_embeddings.items():
            similarity = self.calculate_similarity(query_embedding, enrolled_embedding)
            matches.append({
                "inmate_id": inmate_id,
                "confidence": float(similarity)
            })
        
        # Sort by confidence (descending)
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Best match
        best_match = matches[0]
        best_inmate_id = best_match["inmate_id"]
        best_confidence = best_match["confidence"]
        
        # Determine if match is above threshold
        matched = best_confidence >= self.threshold
        recommendation = self.get_recommendation(best_confidence)
        
        logger.debug(
            f"Best match: {best_inmate_id if matched else 'none'} "
            f"(confidence: {best_confidence:.4f}, recommendation: {recommendation.value})"
        )
        
        # Build result (note: we're not populating all fields yet, just what's needed for matching)
        # The full MatchResult with inmate details and detection info will be added
        # when we integrate with the Face Recognition Service in Phase 2.5
        return MatchResult(
            matched=matched,
            inmate_id=best_inmate_id if matched else None,
            inmate=None,  # Will be populated by service layer
            confidence=best_confidence,
            threshold_used=self.threshold,
            recommendation=recommendation,
            at_expected_location=None,  # Will be checked by service layer
            all_matches=matches,
            detection=None,  # Will be populated by service layer
        )
    
    def _no_match_result(self) -> MatchResult:
        """
        Create a 'no match' result for empty database.
        
        Returns:
            MatchResult indicating no match found
        """
        return MatchResult(
            matched=False,
            inmate_id=None,
            inmate=None,
            confidence=0.0,
            threshold_used=self.threshold,
            recommendation=MatchRecommendation.NO_MATCH,
            at_expected_location=None,
            all_matches=[],
            detection=None,
        )
