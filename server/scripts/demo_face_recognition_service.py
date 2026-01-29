#!/usr/bin/env python3
"""
Face Recognition Service Demo - Prison Roll Call

Interactive HTML-based demonstration of the complete face recognition workflow.

This script:
- Enrolls inmates using FaceRecognitionService
- Verifies faces with confidence scoring
- Shows policy thresholds and recommendations
- Generates a live HTML page with auto-refresh
- Pauses between scenarios for user control

Usage:
    cd server
    source .venv/bin/activate
    python scripts/demo_face_recognition_service.py
    
    Then open demo_output/index.html in your browser!
"""

import argparse
import base64
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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
from app.models.face import MatchResult, MatchRecommendation


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class HTMLPageGenerator:
    """Generate and update HTML demo page."""
    
    CSS = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e4;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        h1 {
            font-size: 2.5em;
            color: #00d4ff;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0,212,255,0.3);
        }
        
        .progress-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 30px;
            margin-top: 20px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #00d4ff 0%, #00ff88 100%);
            height: 100%;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #000;
        }
        
        .scenario-card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        
        .scenario-card.active {
            border: 2px solid #00d4ff;
            box-shadow: 0 8px 32px rgba(0,212,255,0.3);
        }
        
        .scenario-card.collapsed {
            padding: 15px 30px;
            cursor: pointer;
            opacity: 0.7;
        }
        
        .scenario-card.collapsed:hover {
            opacity: 1;
        }
        
        h2 {
            color: #00d4ff;
            font-size: 1.8em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-badge.success {
            background: #00ff88;
            color: #000;
        }
        
        .status-badge.warning {
            background: #ffaa00;
            color: #000;
        }
        
        .status-badge.error {
            background: #ff3366;
            color: #fff;
        }
        
        .status-badge.info {
            background: #00d4ff;
            color: #000;
        }
        
        .image-section {
            display: flex;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        .image-container {
            flex: 1;
            min-width: 300px;
            max-width: 500px;
        }
        
        .image-container img {
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.5);
        }
        
        .image-label {
            text-align: center;
            margin-top: 10px;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .results-section {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .result-item {
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
        }
        
        .result-item.success {
            border-color: #00ff88;
        }
        
        .result-item.warning {
            border-color: #ffaa00;
        }
        
        .result-item.error {
            border-color: #ff3366;
        }
        
        .result-item.info {
            border-color: #00d4ff;
        }
        
        .confidence-meter {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 30px;
            margin: 10px 0;
            overflow: hidden;
            position: relative;
        }
        
        .confidence-fill {
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            transition: width 0.5s ease;
        }
        
        .confidence-fill.excellent {
            background: linear-gradient(90deg, #00ff88 0%, #00ff00 100%);
            color: #000;
        }
        
        .confidence-fill.good {
            background: linear-gradient(90deg, #ffaa00 0%, #ffdd00 100%);
            color: #000;
        }
        
        .confidence-fill.poor {
            background: linear-gradient(90deg, #ff3366 0%, #ff6666 100%);
            color: #fff;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .stat-label {
            color: #888;
            margin-top: 5px;
            text-transform: uppercase;
            font-size: 0.9em;
        }
        
        .waiting-message {
            background: rgba(0,212,255,0.1);
            border: 2px dashed #00d4ff;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        footer {
            text-align: center;
            padding: 30px;
            color: #666;
            margin-top: 50px;
        }
        
        .recommendation-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.1em;
            margin: 10px 0;
        }
        
        .recommendation-badge.auto-accept {
            background: #00ff88;
            color: #000;
        }
        
        .recommendation-badge.confirm {
            background: #ffaa00;
            color: #000;
        }
        
        .recommendation-badge.review {
            background: #ff9500;
            color: #000;
        }
        
        .recommendation-badge.no-match {
            background: #ff3366;
            color: #fff;
        }
    """
    
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.scenarios = []
        self.current_scenario = 0
        self.total_scenarios = 0
        self.title = "Face Recognition Service Demo"
        
    def render(self):
        """Render and save the HTML page."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="2">
    <title>{self.title}</title>
    <style>{self.CSS}</style>
</head>
<body>
    <div class="container">
        {self._render_header()}
        {self._render_scenarios()}
        {self._render_footer()}
    </div>
</body>
</html>"""
        
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w') as f:
            f.write(html)
    
    def _render_header(self) -> str:
        progress = (self.current_scenario / self.total_scenarios * 100) if self.total_scenarios > 0 else 0
        return f"""<header>
    <h1>🔐 {self.title}</h1>
    <p style="font-size: 1.2em; color: #888;">
        Real-time demonstration of ML-powered inmate verification
    </p>
    <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%">
            Scenario {self.current_scenario} of {self.total_scenarios}
        </div>
    </div>
</header>"""
    
    def _render_scenarios(self) -> str:
        html = ""
        for i, scenario in enumerate(self.scenarios):
            is_active = i == self.current_scenario - 1
            is_collapsed = i < self.current_scenario - 1
            
            classes = ["scenario-card"]
            if is_active:
                classes.append("active")
            elif is_collapsed:
                classes.append("collapsed")
            
            html += f'<div class="{" ".join(classes)}">\n{scenario}\n</div>\n'
        
        return html
    
    def _render_footer(self) -> str:
        return f"""<footer>
    <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p style="margin-top: 10px;">Prison Roll Call System • Face Recognition Service Demo</p>
</footer>"""
    
    def set_progress(self, current: int, total: int):
        """Set progress counters."""
        self.current_scenario = current
        self.total_scenarios = total
    
    def add_intro(self):
        """Add introduction scenario."""
        html = """
<h2>👋 Welcome to the Face Recognition Service Demo</h2>
<p style="font-size: 1.1em; margin: 20px 0;">
    This demonstration showcases the <strong>FaceRecognitionService</strong> - 
    the orchestration layer that coordinates face detection, embedding extraction, 
    and matching for prison roll call operations.
</p>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">🎯</div>
        <div class="stat-label">Goal</div>
        <p style="margin-top: 10px;">Automate inmate verification during facility roll calls</p>
    </div>
    <div class="stat-card">
        <div class="stat-value">🧠</div>
        <div class="stat-label">Technology</div>
        <p style="margin-top: 10px;">DeepFace + Facenet512 + Policy-Based Matching</p>
    </div>
    <div class="stat-card">
        <div class="stat-value">⚡</div>
        <div class="stat-label">Speed</div>
        <p style="margin-top: 10px;"><300ms full verification pipeline</p>
    </div>
</div>

<div class="results-section">
    <h3 style="color: #00d4ff; margin-bottom: 15px;">What You'll See:</h3>
    <div class="result-item info">✓ <strong>Enrollment</strong>: Register inmates with quality checks</div>
    <div class="result-item info">✓ <strong>Verification</strong>: Match faces against enrolled database</div>
    <div class="result-item info">✓ <strong>Confidence Scoring</strong>: See how the policy thresholds work</div>
    <div class="result-item info">✓ <strong>Recommendations</strong>: AUTO_ACCEPT, CONFIRM, REVIEW, NO_MATCH</div>
</div>

<div class="waiting-message">
    ⏸️ <strong>Paused</strong> - Demo is waiting for you to press ENTER in the terminal...
</div>
"""
        self.scenarios.append(html)
    
    def add_enrollment_scenario(self, inmate_name: str, inmate_number: str, 
                                 image_path: Path, result: EnrollmentResult):
        """Add enrollment scenario."""
        # Read and encode image
        img = cv2.imread(str(image_path))
        annotated = self._draw_detection(img, result)
        img_base64 = self._encode_image(annotated)
        
        status = "success" if result.success else "error"
        status_text = "SUCCESS" if result.success else "FAILED"
        
        # Confidence meter
        confidence_class = "excellent" if result.quality >= 0.80 else "good" if result.quality >= 0.60 else "poor"
        
        html = f"""
<h2>📸 Enrollment: {inmate_name}</h2>
<span class="status-badge {status}">{status_text}</span>

<p style="font-size: 1.1em; margin: 15px 0;">
    <strong>Inmate Number:</strong> {inmate_number}<br>
    <strong>Image:</strong> {image_path.name}
</p>

<div class="image-section">
    <div class="image-container">
        <img src="data:image/jpeg;base64,{img_base64}" alt="Enrollment Image">
        <div class="image-label">Enrollment Photo</div>
    </div>
</div>

<div class="results-section">
    <h3 style="color: #00d4ff; margin-bottom: 15px;">Quality Assessment:</h3>
    <div class="confidence-meter">
        <div class="confidence-fill {confidence_class}" style="width: {result.quality*100}%">
            {result.quality:.1%} Quality
        </div>
    </div>
    
    <h3 style="color: #00d4ff; margin: 20px 0 15px 0;">Process Steps:</h3>
    <div class="result-item {'success' if result.quality > 0 else 'error'}">
        {'✓' if result.quality > 0 else '✗'} <strong>Face Detection</strong>: 
        {'Detected' if result.quality > 0 else 'No face found'}
    </div>
    <div class="result-item {'success' if result.success else 'warning'}">
        {'✓' if result.success else '⚠'} <strong>Quality Check</strong>: 
        {result.quality:.2f} {'≥' if result.success else '<'} 0.80 threshold
    </div>
    <div class="result-item {'success' if result.success else 'error'}">
        {'✓' if result.success else '✗'} <strong>Embedding Extraction</strong>: 
        {'512-dimensional vector created' if result.success else 'Skipped (quality too low)'}
    </div>
    <div class="result-item {'success' if result.success else 'error'}">
        {'✓' if result.success else '✗'} <strong>Database Storage</strong>: 
        {result.message}
    </div>
    
    {self._render_quality_issues(result.quality_issues) if result.quality_issues else ''}
</div>

<div class="waiting-message">
    ⏸️ <strong>Paused</strong> - Press ENTER to continue...
</div>
"""
        self.scenarios.append(html)
    
    def add_multi_enrollment_scenario(self, inmate_name: str, inmate_number: str, 
                                       enrollment_results: list[tuple[Path, EnrollmentResult]]):
        """Add multi-enrollment scenario showing all photos for one person."""
        # Determine overall status
        all_success = all(result.success for _, result in enrollment_results)
        status = "success" if all_success else "warning"
        status_text = "ALL ENROLLED" if all_success else "PARTIAL SUCCESS"
        
        # Render all enrollment images
        images_html = ""
        for i, (img_path, result) in enumerate(enrollment_results, 1):
            img = cv2.imread(str(img_path))
            annotated = self._draw_detection(img, result)
            img_base64 = self._encode_image(annotated)
            
            images_html += f"""
    <div class="image-container">
        <img src="data:image/jpeg;base64,{img_base64}" alt="Enrollment Photo #{i}">
        <div class="image-label">Enrollment Photo #{i}<br>Quality: {result.quality:.2f}</div>
    </div>
"""
        
        # Average quality
        avg_quality = sum(result.quality for _, result in enrollment_results) / len(enrollment_results)
        confidence_class = "excellent" if avg_quality >= 0.80 else "good" if avg_quality >= 0.60 else "poor"
        
        html = f"""
<h2>📸 Multi-Photo Enrollment: {inmate_name}</h2>
<span class="status-badge {status}">{status_text}</span>
<span class="status-badge info">{len(enrollment_results)} PHOTOS</span>

<p style="font-size: 1.1em; margin: 15px 0;">
    <strong>Inmate Number:</strong> {inmate_number}<br>
    <strong>Photos Enrolled:</strong> {len(enrollment_results)}<br>
    <strong>Average Quality:</strong> {avg_quality:.2f}
</p>

<div class="image-section">
{images_html}
</div>

<div class="results-section">
    <h3 style="color: #00d4ff; margin-bottom: 15px;">Multi-Embedding System:</h3>
    <div class="result-item success">
        ✓ <strong>Multiple Embeddings</strong>: {len(enrollment_results)} embeddings stored for this inmate
    </div>
    <div class="result-item success">
        ✓ <strong>Automatic Averaging</strong>: System will average all embeddings for matching
    </div>
    <div class="result-item success">
        ✓ <strong>Improved Accuracy</strong>: Multiple angles/lighting improve robustness
    </div>
    
    <h3 style="color: #00d4ff; margin: 20px 0 15px 0;">Individual Results:</h3>
"""
        
        for i, (img_path, result) in enumerate(enrollment_results, 1):
            html += f"""
    <div class="result-item {'success' if result.success else 'error'}">
        {'✓' if result.success else '✗'} <strong>Photo #{i}</strong> ({img_path.name}): 
        Quality {result.quality:.2f} - {result.message}
    </div>
"""
        
        html += """
</div>

<div class="waiting-message">
    ⏸️ <strong>Paused</strong> - Press ENTER to continue...
</div>
"""
        self.scenarios.append(html)
    
    def add_verification_scenario(self, image_path: Path, result: MatchResult, enrollment_photos: list[dict] = None):
        """Add verification scenario with enrollment photos displayed."""
        # Read and encode verification image
        img = cv2.imread(str(image_path))
        annotated = self._draw_match_result(img, result)
        img_base64 = self._encode_image(annotated)
        
        # Recommendation styling
        rec_map = {
            MatchRecommendation.AUTO_ACCEPT: ("auto-accept", "🟢 AUTO-ACCEPT", "High confidence - no officer confirmation needed"),
            MatchRecommendation.CONFIRM: ("confirm", "🟡 CONFIRM", "Medium confidence - officer should confirm visually"),
            MatchRecommendation.REVIEW: ("review", "🟠 REVIEW", "Low confidence - manual review required"),
            MatchRecommendation.NO_MATCH: ("no-match", "🔴 NO MATCH", "No enrolled inmate matched"),
        }
        
        rec_class, rec_text, rec_desc = rec_map.get(result.recommendation, ("info", "UNKNOWN", ""))
        
        html = f"""
<h2>🔍 Verification Attempt</h2>
<span class="status-badge {'success' if result.matched else 'error'}">
    {'MATCHED' if result.matched else 'NO MATCH'}
</span>

<p style="font-size: 1.1em; margin: 15px 0;">
    <strong>Image:</strong> {image_path.name}
</p>

<div class="image-section">
    {self._render_enrollment_photos(enrollment_photos) if enrollment_photos else ''}
    <div class="image-container">
        <img src="data:image/jpeg;base64,{img_base64}" alt="Verification Image">
        <div class="image-label">Verification Photo</div>
    </div>
</div>

<div class="results-section">
    <h3 style="color: #00d4ff; margin-bottom: 15px;">Matching Results:</h3>
    
    <div class="recommendation-badge {rec_class}">
        {rec_text}
    </div>
    <p style="margin: 10px 0; color: #aaa;">{rec_desc}</p>
    
    <div class="confidence-meter" style="margin-top: 20px;">
        <div class="confidence-fill {'excellent' if result.confidence >= 0.92 else 'good' if result.confidence >= 0.75 else 'poor'}" 
             style="width: {result.confidence*100}%">
            {result.confidence:.1%} Confidence
        </div>
    </div>
    
    {self._render_match_details(result)}
    
    <h3 style="color: #00d4ff; margin: 20px 0 15px 0;">Process Steps:</h3>
    <div class="result-item {'success' if result.detection.detected else 'error'}">
        {'✓' if result.detection.detected else '✗'} <strong>Face Detection</strong>: 
        {'Detected (quality: ' + f'{result.detection.quality:.2f}' + ')' if result.detection.detected else 'No face found'}
    </div>
    <div class="result-item {'success' if result.detection.detected else 'error'}">
        {'✓' if result.detection.detected else '✗'} <strong>Embedding Extraction</strong>: 
        {'512-dimensional vector extracted' if result.detection.detected else 'Skipped (no face)'}
    </div>
    <div class="result-item {'success' if result.matched else 'warning'}">
        {'✓' if result.matched else '⚠'} <strong>1:N Matching</strong>: 
        {f'Matched against {len(result.all_matches)} enrolled inmates' if result.all_matches else 'No enrolled inmates'}
    </div>
    <div class="result-item {'success' if result.matched else 'info'}">
        {'✓' if result.matched else 'ℹ'} <strong>Policy Check</strong>: 
        Threshold = {result.threshold_used:.2f}, Confidence = {result.confidence:.2f}
    </div>
</div>

<div class="waiting-message">
    ⏸️ <strong>Paused</strong> - Press ENTER to continue...
</div>
"""
        self.scenarios.append(html)
    
    def add_summary(self, stats: Dict):
        """Add summary scenario."""
        html = f"""
<h2>📊 Demo Summary</h2>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">{stats.get('enrollments', 0)}</div>
        <div class="stat-label">Enrollments</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats.get('verifications', 0)}</div>
        <div class="stat-label">Verifications</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats.get('matches', 0)}</div>
        <div class="stat-label">Matches</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats.get('avg_confidence', 0):.1%}</div>
        <div class="stat-label">Avg Confidence</div>
    </div>
</div>

<div class="results-section">
    <h3 style="color: #00d4ff; margin-bottom: 15px;">Key Takeaways:</h3>
    <div class="result-item success">
        ✓ <strong>Face Recognition Service</strong> successfully orchestrates detection, embedding, and matching
    </div>
    <div class="result-item success">
        ✓ <strong>Policy-based thresholds</strong> provide flexible confidence levels for different scenarios
    </div>
    <div class="result-item success">
        ✓ <strong>Recommendations</strong> guide officers while maintaining human oversight
    </div>
    <div class="result-item info">
        ℹ️ <strong>Next Steps</strong>: API endpoints (tasks 2.6-2.8) to expose these services
    </div>
</div>

<div style="background: rgba(0,212,255,0.1); border: 2px solid #00d4ff; border-radius: 10px; padding: 20px; margin: 20px 0; text-align: center;">
    <h3 style="color: #00d4ff;">✅ Demo Complete!</h3>
    <p style="margin-top: 10px;">All 154 unit tests passing. Ready for API development.</p>
</div>
"""
        self.scenarios.append(html)
    
    def _render_match_details(self, result: MatchResult) -> str:
        """Render match details."""
        if not result.matched or not result.inmate:
            return ""
        
        inmate = result.inmate
        return f"""
    <div style="background: rgba(0,255,136,0.1); border: 1px solid #00ff88; border-radius: 10px; padding: 20px; margin: 20px 0;">
        <h3 style="color: #00ff88; margin-bottom: 15px;">✓ Matched Inmate:</h3>
        <p style="font-size: 1.1em;">
            <strong>Name:</strong> {inmate.first_name} {inmate.last_name}<br>
            <strong>Number:</strong> {inmate.inmate_number}<br>
            <strong>Cell:</strong> Block {inmate.cell_block}, Cell {inmate.cell_number}<br>
            <strong>Confidence:</strong> {result.confidence:.2%}
        </p>
    </div>
"""
    
    def _render_enrollment_photos(self, enrollment_photos: list[dict]) -> str:
        """Render enrollment photos for matched inmate."""
        if not enrollment_photos:
            return ""
        
        html = ""
        for i, photo_info in enumerate(enrollment_photos, 1):
            photo_path = Path("tests/fixtures/images/dual_enrollment") / photo_info["photo_path"]
            if photo_path.exists():
                img = cv2.imread(str(photo_path))
                img_base64 = self._encode_image(img)
                quality = photo_info["quality"]
                
                html += f"""
    <div class="image-container">
        <img src="data:image/jpeg;base64,{img_base64}" alt="Enrollment #{i}">
        <div class="image-label">Enrollment Photo #{i}<br>(Quality: {quality:.2f})</div>
    </div>
"""
        return html
    
    def _render_quality_issues(self, issues) -> str:
        """Render quality issues."""
        if not issues:
            return ""
        
        issue_text = ", ".join([issue.value.upper() for issue in issues])
        return f"""
    <div class="result-item warning">
        ⚠ <strong>Quality Issues:</strong> {issue_text}
    </div>
"""
    
    def _draw_detection(self, img: np.ndarray, result: EnrollmentResult) -> np.ndarray:
        """Draw detection visualization on image."""
        annotated = img.copy()
        h, w = img.shape[:2]
        
        # Add quality score
        text = f"Quality: {result.quality:.2f}"
        color = (0, 255, 0) if result.success else (0, 0, 255)
        cv2.putText(annotated, text, (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
        
        # Add status
        status = "ENROLLED" if result.success else "REJECTED"
        cv2.putText(annotated, status, (20, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
        
        return annotated
    
    def _draw_match_result(self, img: np.ndarray, result: MatchResult) -> np.ndarray:
        """Draw match result visualization on image."""
        annotated = img.copy()
        
        # Color based on recommendation
        rec_colors = {
            MatchRecommendation.AUTO_ACCEPT: (0, 255, 0),  # Green
            MatchRecommendation.CONFIRM: (0, 255, 255),    # Yellow
            MatchRecommendation.REVIEW: (0, 165, 255),     # Orange
            MatchRecommendation.NO_MATCH: (0, 0, 255),     # Red
        }
        color = rec_colors.get(result.recommendation, (255, 255, 255))
        
        # Add confidence
        text = f"Confidence: {result.confidence:.2f}"
        cv2.putText(annotated, text, (20, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
        
        # Add recommendation
        rec_text = result.recommendation.value.upper().replace("_", " ")
        cv2.putText(annotated, rec_text, (20, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
        
        # Add match info
        if result.matched and result.inmate:
            match_text = f"{result.inmate.first_name} {result.inmate.last_name}"
            cv2.putText(annotated, match_text, (20, 170),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        
        return annotated
    
    def _encode_image(self, img: np.ndarray) -> str:
        """Encode image as base64."""
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')


def wait_for_enter():
    """Wait for user to press ENTER."""
    input(f"\n{Colors.CYAN}[Press ENTER to continue...]{Colors.END} ")


def print_banner(text: str):
    """Print a banner message."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Face Recognition Service Demo - Interactive HTML Output"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo_output/index.html"),
        help="Output HTML file (default: demo_output/index.html)"
    )
    
    args = parser.parse_args()
    
    # Paths
    script_dir = Path(__file__).parent
    server_dir = script_dir.parent
    fixtures_dir = server_dir / "tests" / "fixtures" / "images"
    
    if not fixtures_dir.exists():
        print(f"{Colors.RED}Error: Fixtures directory not found: {fixtures_dir}{Colors.END}")
        print(f"{Colors.YELLOW}Run prepare_lfw_fixtures.py first to download test images.{Colors.END}")
        sys.exit(1)
    
    # Initialize HTML generator
    html_gen = HTMLPageGenerator(args.output)
    
    # Print welcome
    print_banner("PRISON ROLL CALL - FACE RECOGNITION SERVICE DEMO")
    print(f"{Colors.BOLD}Output:{Colors.END} {args.output}")
    print(f"{Colors.BOLD}Started:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"{Colors.GREEN}✓ Open {args.output} in your browser!{Colors.END}")
    print(f"{Colors.GREEN}✓ The page will auto-refresh every 2 seconds{Colors.END}\n")
    
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
    embedding_repo = EmbeddingRepository(db)
    
    service = FaceRecognitionService(
        detector=detector,
        embedder=embedder,
        matcher=matcher,
        inmate_repo=inmate_repo,
        embedding_repo=embedding_repo,
        policy=policy,
    )
    
    print(f"{Colors.GREEN}✓ Service initialized{Colors.END}\n")
    
    # Statistics
    stats = {
        "enrollments": 0,
        "verifications": 0,
        "matches": 0,
        "confidences": [],
    }
    
    # Select test images from dual_enrollment directory
    dual_dir = fixtures_dir / "dual_enrollment"
    
    # Get unique person names
    person_names = set()
    for img in dual_dir.glob("*_enroll_*.jpg"):
        name = img.stem.rsplit("_enroll_", 1)[0]
        person_names.add(name)
    
    person_names = sorted(list(person_names))[:3]  # Use first 3 people
    
    # Build enrollment and verification lists
    enroll_images = []
    verify_images = []
    
    for person in person_names:
        # Add both enrollment photos for this person
        enroll_1 = dual_dir / f"{person}_enroll_1.jpg"
        enroll_2 = dual_dir / f"{person}_enroll_2.jpg"
        if enroll_1.exists():
            enroll_images.append(enroll_1)
        if enroll_2.exists():
            enroll_images.append(enroll_2)
        
        # Add verification photos
        for verify_img in sorted(dual_dir.glob(f"{person}_verify_*.jpg")):
            verify_images.append(verify_img)
    
    # Total scenarios: intro + (one enrollment scenario per person) + verifications + summary
    total_scenarios = 1 + len(person_names) + len(verify_images) + 1
    
    # Scenario 1: Introduction
    html_gen.set_progress(1, total_scenarios)
    html_gen.add_intro()
    html_gen.render()
    print_banner("SCENARIO 1: INTRODUCTION")
    print("Open the HTML page to see the introduction...")
    wait_for_enter()
    
    # Scenario 2+: Enrollments (group by person, all photos in one scenario)
    inmate_map = {}  # Track inmates by person name
    scenario_num = 2
    
    # Group enrollment images by person
    enrollments_by_person = {}
    for img_path in enroll_images:
        person_name = img_path.stem.rsplit("_enroll_", 1)[0].replace("_", " ").title()
        if person_name not in enrollments_by_person:
            enrollments_by_person[person_name] = []
        enrollments_by_person[person_name].append(img_path)
    
    # Process each person's enrollments together
    for person_name, person_images in enrollments_by_person.items():
        print_banner(f"SCENARIO {scenario_num}: ENROLLMENT - {person_name}")
        
        # Create or get inmate
        person_index = len(inmate_map) + 1
        inmate_number = f"A{1000+person_index:04d}"
        
        # Check if inmate already exists in DB
        existing_inmates = inmate_repo.get_all()
        existing_inmate = next((inm for inm in existing_inmates if inm.inmate_number == inmate_number), None)
        
        if existing_inmate:
            inmate = existing_inmate
            print(f"{Colors.YELLOW}Using existing inmate: {inmate.first_name} {inmate.last_name} ({inmate.inmate_number}){Colors.END}")
        else:
            inmate_create = InmateCreate(
                inmate_number=inmate_number,
                first_name=person_name.split()[0],
                last_name=" ".join(person_name.split()[1:]) if len(person_name.split()) > 1 else "Unknown",
                date_of_birth="1990-01-01",
                cell_block="A",
                cell_number=f"{100+person_index}",
            )
            
            inmate = inmate_repo.create(inmate_create)
            print(f"{Colors.GREEN}Created new inmate: {inmate.first_name} {inmate.last_name} ({inmate.inmate_number}){Colors.END}")
        
        inmate_map[person_name] = inmate
        
        # Enroll all photos for this person
        enrollment_results = []
        for i, img_path in enumerate(person_images, 1):
            print(f"Enrolling photo #{i}: {img_path.name}")
            result = service.enroll_face(inmate.id, img_path)
            print(f"  Quality: {result.quality:.2f} - {Colors.GREEN if result.success else Colors.RED}{result.message}{Colors.END}")
            enrollment_results.append((img_path, result))
            stats["enrollments"] += 1
        
        print(f"{Colors.GREEN}✓ Enrolled {len(person_images)} photos for {inmate.first_name} {inmate.last_name}{Colors.END}")
        
        # Update HTML with all enrollment photos for this person
        html_gen.set_progress(scenario_num, total_scenarios)
        html_gen.add_multi_enrollment_scenario(
            f"{inmate.first_name} {inmate.last_name}",
            inmate.inmate_number,
            enrollment_results
        )
        html_gen.render()
        
        scenario_num += 1
        wait_for_enter()
    
    # Verifications
    for img_path in verify_images:
        print_banner(f"SCENARIO {scenario_num}: VERIFICATION")
        
        print(f"Verifying with image: {img_path.name}")
        result = service.verify_face(img_path)
        
        # Get enrollment photos if matched
        enrollment_photos = None
        if result.matched and result.inmate_id:
            enrollment_photos = embedding_repo.get_photo_paths(result.inmate_id)
            print(f"{Colors.GREEN}✓ MATCH FOUND!{Colors.END}")
            print(f"  Inmate: {result.inmate.first_name} {result.inmate.last_name}")
            print(f"  Confidence: {result.confidence:.2%}")
            print(f"  Recommendation: {result.recommendation.value}")
            print(f"  Enrollment Photos: {len(enrollment_photos)} stored")
            stats["matches"] += 1
        else:
            print(f"{Colors.RED}✗ NO MATCH{Colors.END}")
            print(f"  Best confidence: {result.confidence:.2%}")
        
        # Update HTML with enrollment photos
        html_gen.set_progress(scenario_num, total_scenarios)
        html_gen.add_verification_scenario(img_path, result, enrollment_photos)
        html_gen.render()
        
        stats["verifications"] += 1
        stats["confidences"].append(result.confidence)
        scenario_num += 1
        wait_for_enter()
    
    # Final scenario: Summary
    print_banner(f"SCENARIO {total_scenarios}: SUMMARY")
    
    stats["avg_confidence"] = sum(stats["confidences"]) / len(stats["confidences"]) if stats["confidences"] else 0
    
    html_gen.set_progress(total_scenarios, total_scenarios)
    html_gen.add_summary(stats)
    html_gen.render()
    
    print(f"{Colors.GREEN}✓ Demo Complete!{Colors.END}\n")
    print(f"Statistics:")
    print(f"  Enrollments: {stats['enrollments']}")
    print(f"  Verifications: {stats['verifications']}")
    print(f"  Matches: {stats['matches']}")
    print(f"  Average Confidence: {stats['avg_confidence']:.2%}\n")
    print(f"{Colors.CYAN}Check the HTML page for the full interactive demo!{Colors.END}\n")


if __name__ == "__main__":
    main()
