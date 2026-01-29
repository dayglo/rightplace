#!/usr/bin/env python3
"""
Face Detection Demo - Prison Roll Call

Demonstrates DeepFace face detection working with diverse LFW test fixtures.

This script:
- Processes all 36 LFW test images through FaceDetector
- Draws bounding boxes and landmarks on detected faces
- Saves annotated images to output directory
- Prints structured detection results
- Generates summary statistics

Usage:
    cd server
    source .venv/bin/activate
    python scripts/demo_face_detection.py [--backend retinaface|mtcnn|opencv]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.face_detector import FaceDetector
from app.models.face import DetectionResult, QualityIssue


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def draw_detection(img: np.ndarray, result: DetectionResult) -> np.ndarray:
    """
    Draw bounding box and landmarks on image.
    
    Args:
        img: Image array (BGR format)
        result: Detection result with bounding box and landmarks
        
    Returns:
        Annotated image
    """
    annotated = img.copy()
    
    if not result.detected or result.bounding_box is None:
        # Draw red X if no face detected
        h, w = img.shape[:2]
        cv2.line(annotated, (0, 0), (w, h), (0, 0, 255), 3)
        cv2.line(annotated, (w, 0), (0, h), (0, 0, 255), 3)
        cv2.putText(annotated, "NO FACE", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        return annotated
    
    bbox = result.bounding_box
    
    # Color based on quality
    if result.quality >= 0.75:
        color = (0, 255, 0)  # Green - good quality
    elif result.quality >= 0.50:
        color = (0, 255, 255)  # Yellow - acceptable
    else:
        color = (0, 0, 255)  # Red - poor quality
    
    # Draw bounding box
    cv2.rectangle(
        annotated,
        (bbox.x, bbox.y),
        (bbox.x + bbox.width, bbox.y + bbox.height),
        color,
        3
    )
    
    # Draw landmarks if available
    if result.landmarks:
        landmark_color = (255, 0, 255)  # Magenta
        landmarks_dict = {
            'L_eye': result.landmarks.left_eye,
            'R_eye': result.landmarks.right_eye,
            'Nose': result.landmarks.nose,
            'L_mouth': result.landmarks.left_mouth,
            'R_mouth': result.landmarks.right_mouth,
        }
        
        for name, (x, y) in landmarks_dict.items():
            cv2.circle(annotated, (x, y), 4, landmark_color, -1)
            cv2.putText(annotated, name, (x + 5, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, landmark_color, 1)
    
    # Draw quality score
    quality_text = f"Q: {result.quality:.2f}"
    cv2.putText(annotated, quality_text, (bbox.x, bbox.y - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    # Draw quality issues
    if result.quality_issues:
        issues_text = ", ".join([issue.value for issue in result.quality_issues])
        cv2.putText(annotated, issues_text, (bbox.x, bbox.y + bbox.height + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    # Draw face count warning if multiple faces
    if result.face_count > 1:
        warning = f"WARNING: {result.face_count} faces detected!"
        cv2.putText(annotated, warning, (20, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    return annotated


def format_result(image_name: str, result: DetectionResult) -> str:
    """
    Format detection result as colored terminal output.
    
    Args:
        image_name: Name of the image file
        result: Detection result
        
    Returns:
        Formatted string with ANSI colors
    """
    lines = []
    lines.append(f"\n{Colors.BOLD}{Colors.CYAN}Processing: {image_name}{Colors.END}")
    
    if result.detected:
        lines.append(f"  {Colors.GREEN}✓ Face detected{Colors.END}")
        
        if result.bounding_box:
            bbox = result.bounding_box
            lines.append(f"    Box: x={bbox.x}, y={bbox.y}, w={bbox.width}, h={bbox.height}")
        
        # Quality with color coding
        if result.quality >= 0.75:
            quality_color = Colors.GREEN
            quality_label = "Excellent"
        elif result.quality >= 0.50:
            quality_color = Colors.YELLOW
            quality_label = "Acceptable"
        else:
            quality_color = Colors.RED
            quality_label = "Poor"
        
        lines.append(f"    Quality: {quality_color}{result.quality:.2f} ({quality_label}){Colors.END}")
        
        # Landmarks
        if result.landmarks:
            lines.append(f"    Landmarks: left_eye={result.landmarks.left_eye}, "
                        f"right_eye={result.landmarks.right_eye}, "
                        f"nose={result.landmarks.nose}")
        
        # Issues
        if result.quality_issues:
            issues_str = ", ".join([issue.value.upper() for issue in result.quality_issues])
            lines.append(f"    {Colors.RED}Issues: {issues_str}{Colors.END}")
        else:
            lines.append(f"    {Colors.GREEN}Issues: None{Colors.END}")
        
        # Face count warning
        if result.face_count > 1:
            lines.append(f"    {Colors.YELLOW}⚠ Warning: {result.face_count} faces detected{Colors.END}")
    else:
        lines.append(f"  {Colors.RED}✗ No face detected{Colors.END}")
        if result.quality_issues:
            issues_str = ", ".join([issue.value.upper() for issue in result.quality_issues])
            lines.append(f"    Reason: {issues_str}")
    
    return "\n".join(lines)


def process_all_images(
    fixtures_dir: Path,
    output_dir: Path,
    backend: str = "retinaface"
) -> Dict:
    """
    Process all test fixture images.
    
    Args:
        fixtures_dir: Path to fixtures/images directory
        output_dir: Path to save annotated images
        backend: Detection backend to use
        
    Returns:
        Summary statistics
    """
    detector = FaceDetector(backend=backend)
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "annotated").mkdir(exist_ok=True)
    
    # Statistics
    stats = {
        "total_images": 0,
        "detected": 0,
        "not_detected": 0,
        "multi_face": 0,
        "quality_excellent": 0,  # >= 0.75
        "quality_acceptable": 0,  # 0.50 - 0.74
        "quality_poor": 0,  # < 0.50
        "quality_scores": [],
        "issues": {},
        "results": [],
    }
    
    # Process all images
    categories = ["single_enrollment", "dual_enrollment", "multi_verify", "negative_matching"]
    
    for category in categories:
        category_dir = fixtures_dir / category
        if not category_dir.exists():
            continue
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}Category: {category.upper().replace('_', ' ')}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        
        for img_path in sorted(category_dir.glob("*.jpg")):
            stats["total_images"] += 1
            
            # Detect face
            result = detector.detect(img_path)
            
            # Print result
            print(format_result(img_path.name, result))
            
            # Update statistics
            if result.detected:
                stats["detected"] += 1
                stats["quality_scores"].append(result.quality)
                
                if result.quality >= 0.75:
                    stats["quality_excellent"] += 1
                elif result.quality >= 0.50:
                    stats["quality_acceptable"] += 1
                else:
                    stats["quality_poor"] += 1
                
                if result.face_count > 1:
                    stats["multi_face"] += 1
            else:
                stats["not_detected"] += 1
            
            # Track issues
            for issue in result.quality_issues:
                issue_name = issue.value
                stats["issues"][issue_name] = stats["issues"].get(issue_name, 0) + 1
            
            # Save result
            stats["results"].append({
                "image": str(img_path.relative_to(fixtures_dir)),
                "category": category,
                "detected": result.detected,
                "quality": result.quality,
                "face_count": result.face_count,
                "issues": [issue.value for issue in result.quality_issues],
            })
            
            # Draw and save annotated image
            img = cv2.imread(str(img_path))
            annotated = draw_detection(img, result)
            output_path = output_dir / "annotated" / f"{category}_{img_path.name}"
            cv2.imwrite(str(output_path), annotated)
    
    return stats


def print_summary(stats: Dict, backend: str):
    """Print summary statistics."""
    print(f"\n\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}DETECTION SUMMARY - Backend: {backend.upper()}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    total = stats["total_images"]
    detected = stats["detected"]
    detection_rate = (detected / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}Total Images:{Colors.END} {total}")
    print(f"{Colors.GREEN}Detected:{Colors.END} {detected} ({detection_rate:.1f}%)")
    print(f"{Colors.RED}Not Detected:{Colors.END} {stats['not_detected']}")
    print(f"{Colors.YELLOW}Multi-Face:{Colors.END} {stats['multi_face']}")
    
    print(f"\n{Colors.BOLD}Quality Distribution:{Colors.END}")
    print(f"  {Colors.GREEN}Excellent (≥0.75):{Colors.END} {stats['quality_excellent']}")
    print(f"  {Colors.YELLOW}Acceptable (0.50-0.74):{Colors.END} {stats['quality_acceptable']}")
    print(f"  {Colors.RED}Poor (<0.50):{Colors.END} {stats['quality_poor']}")
    
    if stats["quality_scores"]:
        avg_quality = sum(stats["quality_scores"]) / len(stats["quality_scores"])
        print(f"\n{Colors.BOLD}Average Quality:{Colors.END} {avg_quality:.3f}")
        print(f"{Colors.BOLD}Min Quality:{Colors.END} {min(stats['quality_scores']):.3f}")
        print(f"{Colors.BOLD}Max Quality:{Colors.END} {max(stats['quality_scores']):.3f}")
    
    if stats["issues"]:
        print(f"\n{Colors.BOLD}Quality Issues Breakdown:{Colors.END}")
        for issue, count in sorted(stats["issues"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {issue}: {count}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✓ Annotated images saved to: demo_output/annotated/{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}✓ Results saved to: demo_output/detection_results.json{Colors.END}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Face Detection Demo - DeepFace on LFW Fixtures"
    )
    parser.add_argument(
        "--backend",
        choices=["retinaface", "mtcnn", "opencv", "ssd"],
        default="retinaface",
        help="Detection backend (default: retinaface)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo_output"),
        help="Output directory for annotated images (default: demo_output)"
    )
    
    args = parser.parse_args()
    
    # Paths
    script_dir = Path(__file__).parent
    server_dir = script_dir.parent
    fixtures_dir = server_dir / "tests" / "fixtures" / "images"
    output_dir = args.output
    
    if not fixtures_dir.exists():
        print(f"{Colors.RED}Error: Fixtures directory not found: {fixtures_dir}{Colors.END}")
        print(f"{Colors.YELLOW}Run prepare_lfw_fixtures.py first to download test images.{Colors.END}")
        sys.exit(1)
    
    # Header
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}PRISON ROLL CALL - FACE DETECTION DEMO{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"\n{Colors.BOLD}Backend:{Colors.END} {args.backend}")
    print(f"{Colors.BOLD}Fixtures:{Colors.END} {fixtures_dir}")
    print(f"{Colors.BOLD}Output:{Colors.END} {output_dir}")
    print(f"{Colors.BOLD}Started:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Process images
    stats = process_all_images(fixtures_dir, output_dir, args.backend)
    
    # Print summary
    print_summary(stats, args.backend)
    
    # Save JSON results
    results_file = output_dir / "detection_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "backend": args.backend,
            "statistics": {
                "total_images": stats["total_images"],
                "detected": stats["detected"],
                "not_detected": stats["not_detected"],
                "multi_face": stats["multi_face"],
                "quality_excellent": stats["quality_excellent"],
                "quality_acceptable": stats["quality_acceptable"],
                "quality_poor": stats["quality_poor"],
                "average_quality": sum(stats["quality_scores"]) / len(stats["quality_scores"]) if stats["quality_scores"] else 0,
                "issues": stats["issues"],
            },
            "results": stats["results"],
        }, f, indent=2)
    
    print(f"{Colors.BOLD}{Colors.GREEN}Demo completed successfully!{Colors.END}\n")


if __name__ == "__main__":
    main()
