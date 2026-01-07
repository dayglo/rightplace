#!/usr/bin/env python3
"""
Progressive Enrollment Demo - Prison Roll Call

Demonstrates how accuracy improves as more enrollment photos are added.

This script:
- Enrolls Tony Blair with 1 photo → verifies
- Adds 2 more photos (total 3) → verifies
- Adds 7 more photos (total 10) → verifies
- Shows confidence improvement at each stage
- Generates an interactive HTML page

Usage:
    cd server
    source venv/bin/activate
    python scripts/demo_progressive_enrollment.py
"""

import argparse
import base64
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import FaceRecognitionPolicy, Settings
from app.db.database import get_connection
from app.db.repositories.embedding_repo import EmbeddingRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.ml.face_detector import FaceDetector
from app.ml.face_embedder import FaceEmbedder
from app.ml.face_matcher import FaceMatcher
from app.models.inmate import InmateCreate
from app.services.face_recognition import FaceRecognitionService, EnrollmentResult
from app.models.face import MatchResult


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ProgressiveEnrollmentHTML:
    """Generate HTML page for progressive enrollment demo."""
    
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.stages = []
        self.confidences = []
        
    def add_stage(self, stage_num: int, enrollment_count: int, confidence: float, 
                  enrollment_photos: list[Path], verify_photo: Path, matched: bool):
        """Add a stage to the HTML."""
        self.confidences.append(confidence)
        
        # Encode enrollment photos
        enroll_html = ""
        for i, photo in enumerate(enrollment_photos, 1):
            img = cv2.imread(str(photo))
            _, buffer = cv2.imencode('.jpg', img)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            enroll_html += f"""
            <div class="image-container">
                <img src="data:image/jpeg;base64,{img_base64}" alt="Enrollment #{i}">
                <div class="image-label">Enrollment #{i}</div>
            </div>
            """
        
        # Encode verification photo
        verify_img = cv2.imread(str(verify_photo))
        _, buffer = cv2.imencode('.jpg', verify_img)
        verify_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Calculate improvement
        improvement_html = ""
        if len(self.confidences) > 1:
            improvement = self.confidences[-1] - self.confidences[-2]
            total_improvement = self.confidences[-1] - self.confidences[0]
            improvement_html = f"""
            <div class="result-item {'success' if improvement >= 0 else 'warning'}">
                📈 <strong>Improvement from previous stage:</strong> {'+' if improvement >= 0 else ''}{improvement:.2%}
            </div>
            <div class="result-item {'success' if total_improvement >= 0 else 'warning'}">
                📊 <strong>Total improvement from Stage 1:</strong> {'+' if total_improvement >= 0 else ''}{total_improvement:.2%}
            </div>
            """
        
        stage_html = f"""
        <div class="stage-card">
            <h2>Stage {stage_num}: {enrollment_count} Enrollment Photo{'s' if enrollment_count > 1 else ''}</h2>
            <span class="status-badge {'success' if matched else 'error'}">{'MATCHED' if matched else 'NO MATCH'}</span>
            
            <div class="image-section">
                {enroll_html}
                <div class="image-container">
                    <img src="data:image/jpeg;base64,{verify_base64}" alt="Verification">
                    <div class="image-label">Verification Photo</div>
                </div>
            </div>
            
            <div class="results-section">
                <h3 style="color: #00d4ff; margin-bottom: 15px;">Results:</h3>
                <div class="confidence-meter">
                    <div class="confidence-fill {'excellent' if confidence >= 0.85 else 'good' if confidence >= 0.75 else 'poor'}" 
                         style="width: {confidence*100}%">
                        {confidence:.1%} Confidence
                    </div>
                </div>
                {improvement_html}
            </div>
        </div>
        """
        self.stages.append(stage_html)
    
    def render(self):
        """Render and save the HTML page."""
        # Create confidence progression graph
        graph_html = self._create_confidence_graph()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Progressive Enrollment Demo - Tony Blair</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e4;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        h1 {{
            font-size: 2.5em;
            color: #00d4ff;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0,212,255,0.3);
        }}
        .stage-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        h2 {{
            color: #00d4ff;
            font-size: 1.8em;
            margin-bottom: 15px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-badge.success {{ background: #00ff88; color: #000; }}
        .status-badge.error {{ background: #ff3366; color: #fff; }}
        .image-section {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .image-container {{
            flex: 1;
            min-width: 200px;
            max-width: 300px;
        }}
        .image-container img {{
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.5);
        }}
        .image-label {{
            text-align: center;
            margin-top: 10px;
            font-weight: bold;
            color: #00d4ff;
        }}
        .results-section {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .result-item {{
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
        }}
        .result-item.success {{ border-color: #00ff88; }}
        .result-item.warning {{ border-color: #ffaa00; }}
        .confidence-meter {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 30px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .confidence-fill {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            transition: width 0.5s ease;
        }}
        .confidence-fill.excellent {{ background: linear-gradient(90deg, #00ff88 0%, #00ff00 100%); color: #000; }}
        .confidence-fill.good {{ background: linear-gradient(90deg, #ffaa00 0%, #ffdd00 100%); color: #000; }}
        .confidence-fill.poor {{ background: linear-gradient(90deg, #ff3366 0%, #ff6666 100%); color: #fff; }}
        .graph-container {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 30px;
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📈 Progressive Enrollment Demo</h1>
            <p style="font-size: 1.2em; color: #888;">
                Demonstrating how accuracy improves with more enrollment photos
            </p>
            <p style="margin-top: 10px; color: #00d4ff;">
                <strong>Subject:</strong> Tony Blair | <strong>Dataset:</strong> LFW
            </p>
        </header>
        
        {graph_html}
        
        {''.join(self.stages)}
        
        <footer style="text-align: center; padding: 30px; color: #666; margin-top: 50px;">
            <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 10px;">Prison Roll Call System • Progressive Enrollment Demo</p>
        </footer>
    </div>
</body>
</html>"""
        
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w') as f:
            f.write(html)
    
    def _create_confidence_graph(self):
        """Create a visual confidence progression graph."""
        if not self.confidences:
            return ""
        
        stages_labels = ["Stage 1", "Stage 2", "Stage 3"]
        max_confidence = max(self.confidences) if self.confidences else 1.0
        
        bars_html = ""
        for i, conf in enumerate(self.confidences):
            height = (conf / max_confidence) * 200  # Max height 200px
            bars_html += f"""
            <div style="display: inline-block; margin: 0 20px; text-align: center;">
                <div style="background: linear-gradient(180deg, #00ff88 0%, #00d4ff 100%); 
                            width: 80px; height: {height}px; border-radius: 10px 10px 0 0;
                            display: flex; align-items: flex-end; justify-content: center;
                            padding-bottom: 10px; color: #000; font-weight: bold;">
                    {conf:.1%}
                </div>
                <div style="margin-top: 10px; color: #00d4ff; font-weight: bold;">
                    {stages_labels[i] if i < len(stages_labels) else f'Stage {i+1}'}
                </div>
            </div>
            """
        
        total_improvement = self.confidences[-1] - self.confidences[0] if len(self.confidences) > 1 else 0
        improvement_color = '#00ff88' if total_improvement >= 0 else '#ff3366'
        
        return f"""
        <div class="graph-container">
            <h2 style="color: #00d4ff; margin-bottom: 20px;">📊 Confidence Progression</h2>
            <div style="display: flex; justify-content: center; align-items: flex-end; height: 250px;">
                {bars_html}
            </div>
            <div style="text-align: center; margin-top: 30px; font-size: 1.2em;">
                <span style="color: {improvement_color}; font-weight: bold;">
                    Total Improvement: {'+' if total_improvement >= 0 else ''}{total_improvement:.2%}
                </span>
            </div>
        </div>
        """


def print_banner(text: str):
    """Print a banner message."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")


def wait_for_enter(interactive: bool = True):
    """Wait for user to press ENTER if in interactive mode."""
    if interactive:
        input(f"\n{Colors.CYAN}[Press ENTER to continue...]{Colors.END} ")


def main():
    parser = argparse.ArgumentParser(
        description="Progressive Enrollment Demo - Show accuracy improvement"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo_output/progressive_enrollment.html"),
        help="Output HTML file (default: demo_output/progressive_enrollment.html)"
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help="Run continuously without pausing (default: interactive with pauses)"
    )
    
    args = parser.parse_args()
    interactive = not args.no_pause
    
    # Initialize HTML generator
    html_gen = ProgressiveEnrollmentHTML(args.output)
    
    # Paths
    script_dir = Path(__file__).parent
    server_dir = script_dir.parent
    lfw_dir = server_dir.parent / "datasets" / "lfw" / "lfw-deepfunneled" / "lfw-deepfunneled" / "Tony_Blair"
    
    if not lfw_dir.exists():
        print(f"{Colors.RED}Error: Tony Blair directory not found: {lfw_dir}{Colors.END}")
        sys.exit(1)
    
    # Get Tony Blair photos
    tony_blair_photos = sorted(list(lfw_dir.glob("Tony_Blair_*.jpg")))
    
    if len(tony_blair_photos) < 10:
        print(f"{Colors.RED}Error: Need at least 10 Tony Blair photos, found {len(tony_blair_photos)}{Colors.END}")
        sys.exit(1)
    
    # Select photos for progressive enrollment (using single-face photos only)
    # Photos #2-#14 and #17-#18 have single faces (avoid #1, #15, #16 which have multiple faces)
    enroll_stage_1 = tony_blair_photos[1:2]      # Photo #2 (1 photo)
    enroll_stage_2 = tony_blair_photos[2:4]      # Photos #3-#4 (2 more photos, total 3)
    enroll_stage_3 = tony_blair_photos[4:11]     # Photos #5-#11 (7 more photos, total 10)
    verify_photo = tony_blair_photos[16]         # Photo #17 (single face, similar conditions)
    
    print_banner("PROGRESSIVE ENROLLMENT DEMO - TONY BLAIR")
    print(f"{Colors.BOLD}Output:{Colors.END} {args.output}")
    print(f"{Colors.BOLD}Dataset:{Colors.END} LFW Tony Blair photos")
    print(f"{Colors.BOLD}Total Photos Available:{Colors.END} {len(tony_blair_photos)}")
    print(f"{Colors.BOLD}Verification Photo:{Colors.END} {verify_photo.name}\n")
    print(f"{Colors.GREEN}✓ Open {args.output} in your browser to see results!{Colors.END}\n")
    
    # Initialize service
    print("Initializing Face Recognition Service...")
    settings = Settings()
    policy = FaceRecognitionPolicy()
    
    db = get_connection(settings.database_url)
    detector = FaceDetector(backend="retinaface")
    embedder = FaceEmbedder(model="Facenet512")
    matcher = FaceMatcher(
        threshold=policy.verification_threshold,
        auto_accept_threshold=policy.auto_accept_threshold,
        review_threshold=policy.manual_review_threshold,
    )
    inmate_repo = InmateRepository(db)
    embedding_repo = EmbeddingRepository(db, max_embeddings_per_inmate=10)  # Allow 10 embeddings for demo
    
    service = FaceRecognitionService(
        detector=detector,
        embedder=embedder,
        matcher=matcher,
        inmate_repo=inmate_repo,
        embedding_repo=embedding_repo,
        policy=policy,
    )
    
    print(f"{Colors.GREEN}✓ Service initialized{Colors.END}\n")
    
    # Create Tony Blair inmate record
    print_banner("STEP 1: CREATE INMATE RECORD")
    
    inmate_create = InmateCreate(
        inmate_number="A9999",
        first_name="Tony",
        last_name="Blair",
        date_of_birth="1953-05-06",
        cell_block="VIP",
        cell_number="001",
    )
    
    inmate = inmate_repo.create(inmate_create)
    print(f"{Colors.GREEN}✓ Created inmate: {inmate.first_name} {inmate.last_name} ({inmate.inmate_number}){Colors.END}")
    
    wait_for_enter(interactive)
    
    # STAGE 1: Enroll 1 photo
    print_banner("STAGE 1: ENROLL 1 PHOTO")
    
    for img_path in enroll_stage_1:
        print(f"Enrolling: {img_path.name}")
        result = service.enroll_face(inmate.id, img_path)
        print(f"  Quality: {result.quality:.2f} - {Colors.GREEN if result.success else Colors.RED}{result.message}{Colors.END}")
    
    embedding_count = embedding_repo.get_count(inmate.id)
    print(f"\n{Colors.CYAN}Total Embeddings Stored: {embedding_count}{Colors.END}")
    
    wait_for_enter(interactive)
    
    # VERIFY STAGE 1
    print_banner("VERIFICATION AFTER 1 ENROLLMENT")
    
    print(f"Verifying with: {verify_photo.name}")
    
    # Time the verification
    start_time = time.time()
    result = service.verify_face(verify_photo)
    verification_time = time.time() - start_time
    
    fps = 1.0 / verification_time if verification_time > 0 else 0
    print(f"\n{Colors.BLUE}⏱️  Verification Time: {verification_time:.3f}s ({fps:.1f} FPS){Colors.END}")
    
    # Show debug info about individual photo similarities
    if result.all_matches and len(result.all_matches) > 0:
        best_match_data = result.all_matches[0]
        print(f"\n{Colors.CYAN}📊 Ensemble Matching Debug:{Colors.END}")
        if "best_match" in best_match_data and "weighted_avg" in best_match_data:
            print(f"  Best Match (70%):       {best_match_data['best_match']:.2%}")
            print(f"  Weighted Average (30%): {best_match_data['weighted_avg']:.2%}")
            print(f"  Ensemble Confidence:    {best_match_data['confidence']:.2%}")
            print(f"  Number of Photos:       {best_match_data.get('num_photos', 'N/A')}")
    
    if result.matched and result.inmate_id == inmate.id:
        print(f"\n{Colors.GREEN}✓ MATCHED: {inmate.first_name} {inmate.last_name}{Colors.END}")
        print(f"  Final Confidence: {Colors.BOLD}{result.confidence:.2%}{Colors.END}")
        print(f"  Recommendation: {result.recommendation.value}")
        stage_1_confidence = result.confidence
        stage_1_matched = True
    else:
        print(f"\n{Colors.RED}✗ NO MATCH or WRONG MATCH{Colors.END}")
        print(f"  Final Confidence: {result.confidence:.2%}")
        stage_1_confidence = result.confidence
        stage_1_matched = False
    
    # Add Stage 1 to HTML
    html_gen.add_stage(1, 1, stage_1_confidence, enroll_stage_1, verify_photo, stage_1_matched)
    html_gen.render()
    
    wait_for_enter(interactive)
    
    # STAGE 2: Enroll 2 more photos (total 3)
    print_banner("STAGE 2: ENROLL 2 MORE PHOTOS (Total: 3)")
    
    for img_path in enroll_stage_2:
        print(f"Enrolling: {img_path.name}")
        result = service.enroll_face(inmate.id, img_path)
        print(f"  Quality: {result.quality:.2f} - {Colors.GREEN if result.success else Colors.RED}{result.message}{Colors.END}")
    
    embedding_count = embedding_repo.get_count(inmate.id)
    print(f"\n{Colors.CYAN}Total Embeddings Stored: {embedding_count}{Colors.END}")
    
    wait_for_enter(interactive)
    
    # VERIFY STAGE 2
    print_banner("VERIFICATION AFTER 3 ENROLLMENTS")
    
    print(f"Verifying with: {verify_photo.name}")
    
    # Time the verification
    start_time = time.time()
    result = service.verify_face(verify_photo)
    verification_time = time.time() - start_time
    
    fps = 1.0 / verification_time if verification_time > 0 else 0
    print(f"\n{Colors.BLUE}⏱️  Verification Time: {verification_time:.3f}s ({fps:.1f} FPS){Colors.END}")
    
    # Show debug info about individual photo similarities
    if result.all_matches and len(result.all_matches) > 0:
        best_match_data = result.all_matches[0]
        print(f"\n{Colors.CYAN}📊 Ensemble Matching Debug:{Colors.END}")
        if "best_match" in best_match_data and "weighted_avg" in best_match_data:
            print(f"  Best Match (70%):       {best_match_data['best_match']:.2%}")
            print(f"  Weighted Average (30%): {best_match_data['weighted_avg']:.2%}")
            print(f"  Ensemble Confidence:    {best_match_data['confidence']:.2%}")
            print(f"  Number of Photos:       {best_match_data.get('num_photos', 'N/A')}")
    
    if result.matched and result.inmate_id == inmate.id:
        print(f"\n{Colors.GREEN}✓ MATCHED: {inmate.first_name} {inmate.last_name}{Colors.END}")
        print(f"  Final Confidence: {Colors.BOLD}{result.confidence:.2%}{Colors.END}")
        print(f"  Recommendation: {result.recommendation.value}")
        stage_2_confidence = result.confidence
        stage_2_matched = True
        improvement = stage_2_confidence - stage_1_confidence
        print(f"  {Colors.YELLOW}Improvement: {'+' if improvement >= 0 else ''}{improvement:.2%}{Colors.END}")
    else:
        print(f"\n{Colors.RED}✗ NO MATCH or WRONG MATCH{Colors.END}")
        print(f"  Final Confidence: {result.confidence:.2%}")
        stage_2_confidence = result.confidence
        stage_2_matched = False
        improvement = stage_2_confidence - stage_1_confidence
        print(f"  Change: {'+' if improvement >= 0 else ''}{improvement:.2%}")
    
    # Add Stage 2 to HTML (all enrolled photos so far)
    all_enroll_stage_2 = enroll_stage_1 + enroll_stage_2
    html_gen.add_stage(2, 3, stage_2_confidence, all_enroll_stage_2, verify_photo, stage_2_matched)
    html_gen.render()
    
    wait_for_enter(interactive)
    
    # STAGE 3: Enroll 7 more photos (total 10)
    print_banner("STAGE 3: ENROLL 7 MORE PHOTOS (Total: 10)")
    
    for img_path in enroll_stage_3:
        print(f"Enrolling: {img_path.name}")
        result = service.enroll_face(inmate.id, img_path)
        print(f"  Quality: {result.quality:.2f} - {Colors.GREEN if result.success else Colors.RED}{result.message}{Colors.END}")
    
    embedding_count = embedding_repo.get_count(inmate.id)
    print(f"\n{Colors.CYAN}Total Embeddings Stored: {embedding_count}{Colors.END}")
    
    # Note: Our system limits to 5 embeddings by default
    if embedding_count < 10:
        print(f"{Colors.YELLOW}Note: System configured to keep max {embedding_count} embeddings (newest ones){Colors.END}")
    
    wait_for_enter(interactive)
    
    # VERIFY STAGE 3
    print_banner("VERIFICATION AFTER 10 ENROLLMENTS")
    
    print(f"Verifying with: {verify_photo.name}")
    
    # Time the verification
    start_time = time.time()
    result = service.verify_face(verify_photo)
    verification_time = time.time() - start_time
    
    fps = 1.0 / verification_time if verification_time > 0 else 0
    print(f"\n{Colors.BLUE}⏱️  Verification Time: {verification_time:.3f}s ({fps:.1f} FPS){Colors.END}")
    
    # Show debug info about individual photo similarities
    if result.all_matches and len(result.all_matches) > 0:
        best_match_data = result.all_matches[0]
        print(f"\n{Colors.CYAN}📊 Ensemble Matching Debug:{Colors.END}")
        if "best_match" in best_match_data and "weighted_avg" in best_match_data:
            print(f"  Best Match (70%):       {best_match_data['best_match']:.2%}")
            print(f"  Weighted Average (30%): {best_match_data['weighted_avg']:.2%}")
            print(f"  Ensemble Confidence:    {best_match_data['confidence']:.2%}")
            print(f"  Number of Photos:       {best_match_data.get('num_photos', 'N/A')}")
    
    if result.matched and result.inmate_id == inmate.id:
        print(f"\n{Colors.GREEN}✓ MATCHED: {inmate.first_name} {inmate.last_name}{Colors.END}")
        print(f"  Final Confidence: {Colors.BOLD}{result.confidence:.2%}{Colors.END}")
        print(f"  Recommendation: {result.recommendation.value}")
        stage_3_confidence = result.confidence
        stage_3_matched = True
        improvement_2_to_3 = stage_3_confidence - stage_2_confidence
        total_improvement = stage_3_confidence - stage_1_confidence
        print(f"  {Colors.YELLOW}Improvement (3→10): {'+' if improvement_2_to_3 >= 0 else ''}{improvement_2_to_3:.2%}{Colors.END}")
        print(f"  {Colors.YELLOW}Total Improvement (1→10): {'+' if total_improvement >= 0 else ''}{total_improvement:.2%}{Colors.END}")
    else:
        print(f"\n{Colors.RED}✗ NO MATCH or WRONG MATCH{Colors.END}")
        print(f"  Final Confidence: {result.confidence:.2%}")
        stage_3_confidence = result.confidence
        stage_3_matched = False
        improvement_2_to_3 = stage_3_confidence - stage_2_confidence
        total_improvement = stage_3_confidence - stage_1_confidence
        print(f"  Change (3→10): {'+' if improvement_2_to_3 >= 0 else ''}{improvement_2_to_3:.2%}")
        print(f"  Total Change (1→10): {'+' if total_improvement >= 0 else ''}{total_improvement:.2%}")
    
    # Add Stage 3 to HTML (all enrolled photos)
    all_enroll_stage_3 = enroll_stage_1 + enroll_stage_2 + enroll_stage_3
    html_gen.add_stage(3, 10, stage_3_confidence, all_enroll_stage_3, verify_photo, stage_3_matched)
    html_gen.render()
    
    wait_for_enter(interactive)
    
    # SUMMARY
    print_banner("SUMMARY: PROGRESSIVE ENROLLMENT RESULTS")
    
    print(f"📊 {Colors.BOLD}Confidence Progression:{Colors.END}\n")
    print(f"  Stage 1 (1 enrollment):   {stage_1_confidence:.2%}")
    print(f"  Stage 2 (3 enrollments):  {stage_2_confidence:.2%}")
    print(f"  Stage 3 (10 enrollments): {stage_3_confidence:.2%}\n")
    
    total_improvement = stage_3_confidence - stage_1_confidence
    improvement_color = Colors.GREEN if total_improvement > 0 else Colors.RED
    
    print(f"  {improvement_color}Total Improvement: {'+' if total_improvement >= 0 else ''}{total_improvement:.2%}{Colors.END}\n")
    
    print(f"{Colors.CYAN}Key Takeaway:{Colors.END}")
    print(f"  More enrollment photos = Better accuracy!")
    print(f"  The multi-embedding system averages {embedding_count} embeddings for robust matching.\n")
    
    print(f"{Colors.GREEN}✓ HTML report saved to: {args.output}{Colors.END}")
    print(f"{Colors.CYAN}Open it in your browser to see the full visualization!{Colors.END}\n")


if __name__ == "__main__":
    main()
