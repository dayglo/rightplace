"""
Face Embedding wrapper using DeepFace.

This module provides a clean interface for face embedding extraction using DeepFace
with Facenet512 (default) or ArcFace models.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
from deepface import DeepFace

logger = logging.getLogger(__name__)


class FaceEmbedder:
    """
    Face embedder using DeepFace with Facenet512 or ArcFace models.
    
    This class wraps DeepFace's embedding extraction capabilities and provides
    a clean interface that returns 512-dimensional face embeddings.
    """
    
    def __init__(self, model: str = "Facenet512"):
        """
        Initialize the face embedder.
        
        Args:
            model: Recognition model to use. Options:
                - "Facenet512" (default, 98.4% accuracy)
                - "ArcFace" (96.7% accuracy, faster)
        """
        self.model = model
        logger.info(f"Initialized FaceEmbedder with model: {model}")
    
    def extract(self, image_path: str | Path) -> np.ndarray:
        """
        Extract face embedding from an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            512-dimensional face embedding as numpy array (float32)
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If no face detected or embedding extraction fails
            
        Example:
            >>> embedder = FaceEmbedder()
            >>> embedding = embedder.extract("image.jpg")
            >>> print(embedding.shape)
            (512,)
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            # Extract embedding using DeepFace
            embedding_objs = DeepFace.represent(
                img_path=str(image_path),
                model_name=self.model,
                enforce_detection=True,
                detector_backend="retinaface",
                align=True,
            )
            
            if not embedding_objs or len(embedding_objs) == 0:
                logger.error(f"No face detected in {image_path}")
                raise ValueError(f"No face detected in {image_path}")
            
            # Get the first face's embedding
            # DeepFace.represent returns a list of dicts, one per detected face
            embedding = np.array(embedding_objs[0]["embedding"], dtype=np.float32)
            
            # Normalize the embedding (L2 normalization)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            logger.debug(f"Extracted embedding from {image_path}, shape: {embedding.shape}, norm: {np.linalg.norm(embedding):.4f}")
            
            return embedding
            
        except ValueError as e:
            # Re-raise ValueError (no face detected)
            raise
        except Exception as e:
            logger.error(f"Error extracting embedding from {image_path}: {e}", exc_info=True)
            raise ValueError(f"Failed to extract embedding: {e}")
    
    def extract_from_array(self, img: np.ndarray) -> np.ndarray:
        """
        Extract face embedding from numpy array (useful for camera frames).
        
        Args:
            img: Image as numpy array (BGR format)
            
        Returns:
            512-dimensional face embedding as numpy array (float32)
            
        Raises:
            ValueError: If no face detected or embedding extraction fails
        """
        try:
            # Extract embedding using DeepFace
            embedding_objs = DeepFace.represent(
                img_path=img,
                model_name=self.model,
                enforce_detection=True,
                detector_backend="retinaface",
                align=True,
            )
            
            if not embedding_objs or len(embedding_objs) == 0:
                logger.error("No face detected in image array")
                raise ValueError("No face detected in image array")
            
            # Get the first face's embedding
            embedding = np.array(embedding_objs[0]["embedding"], dtype=np.float32)
            
            # Normalize the embedding (L2 normalization)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            logger.debug(f"Extracted embedding from array, shape: {embedding.shape}, norm: {np.linalg.norm(embedding):.4f}")
            
            return embedding
            
        except ValueError as e:
            # Re-raise ValueError (no face detected)
            raise
        except Exception as e:
            logger.error(f"Error extracting embedding from array: {e}", exc_info=True)
            raise ValueError(f"Failed to extract embedding: {e}")
