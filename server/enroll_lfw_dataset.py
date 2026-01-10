#!/usr/bin/env python3
"""
Enroll LFW Dataset into Prison Roll Call System

This script processes the Labeled Faces in the Wild (LFW) dataset and enrolls
all celebrities into the system via the enrollment API.

Features:
- Database backup before starting
- Progress tracking with resume capability
- Max 20 photos per person
- Error handling and logging
- Summary statistics
"""
import os
import sys
import json
import time
import shutil
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
LFW_DATASET_PATH = Path("../datasets/lfw/lfw-deepfunneled/lfw-deepfunneled")
DATABASE_PATH = Path("data/prison_rollcall.db")
BACKUP_DIR = Path("data/backups")
PROGRESS_FILE = Path("data/enrollment_progress.json")
LOG_FILE = Path("data/enrollment_log.txt")
MAX_PHOTOS_PER_PERSON = 20

# Stats
stats = {
    "total_people": 0,
    "processed_people": 0,
    "successful_enrollments": 0,
    "failed_enrollments": 0,
    "skipped_people": 0,
    "total_photos_attempted": 0,
    "total_photos_enrolled": 0,
    "errors": []
}


def log(message: str, level: str = "INFO", end: str = "\n"):
    """Log message to console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line, end=end)
    
    # Always write full lines to file
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + "\n")


def backup_database():
    """Create a timestamped backup of the database."""
    if not DATABASE_PATH.exists():
        log("No database found to backup - will be created fresh", "WARNING")
        return None
    
    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"prison_rollcall_backup_{timestamp}.db"
    
    log(f"Backing up database to: {backup_path}")
    shutil.copy2(DATABASE_PATH, backup_path)
    log(f"✓ Database backed up successfully ({backup_path.stat().st_size} bytes)")
    
    return backup_path


def load_progress() -> Dict:
    """Load progress from previous run."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"processed_people": [], "inmate_mapping": {}}


def save_progress(progress: Dict):
    """Save current progress."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def check_server_ready() -> bool:
    """Check if the FastAPI server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def create_inmate(person_name: str, cell_number: int) -> Dict | None:
    """Create an inmate record for a person."""
    # Parse name from directory (e.g., "George_W_Bush" -> "George W Bush")
    name_parts = person_name.replace('_', ' ').split()
    
    # Assume last part is last name, rest is first name
    if len(name_parts) == 1:
        first_name = name_parts[0]
        last_name = ""
    else:
        first_name = " ".join(name_parts[:-1])
        last_name = name_parts[-1]
    
    # Create inmate data
    inmate_data = {
        "inmate_number": person_name,  # Use directory name as unique ID
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": "1970-01-01",  # Default date
        "cell_block": "LFW",
        "cell_number": str(cell_number).zfill(4)
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inmates", json=inmate_data)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            log(f"Failed to create inmate {person_name}: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"Error creating inmate {person_name}: {e}", "ERROR")
        return None


def enroll_photo(inmate_id: str, photo_path: Path) -> Tuple[bool, str]:
    """Enroll a single photo for an inmate."""
    try:
        with open(photo_path, 'rb') as f:
            files = {'image': (photo_path.name, f, 'image/jpeg')}
            response = requests.post(
                f"{BASE_URL}/enrollment/{inmate_id}",
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            quality = result.get('quality', 0.0)
            return True, f"quality={quality:.2f}"
        else:
            error_detail = response.text
            return False, f"HTTP {response.status_code}: {error_detail[:100]}"
    
    except Exception as e:
        return False, str(e)


def process_person(person_name: str, person_dir: Path, cell_number: int, progress: Dict) -> Tuple[bool, int]:
    """
    Process one person from the dataset.
    
    Returns:
        (success, num_photos_enrolled)
    """
    # Skip if already processed
    if person_name in progress["processed_people"]:
        log(f"Skipping {person_name} (already processed)")
        stats["skipped_people"] += 1
        return True, 0
    
    log(f"\n{'='*60}")
    log(f"Processing: {person_name}")
    
    # Get all photos for this person
    photo_files = sorted(person_dir.glob("*.jpg"))
    
    # Limit to first MAX_PHOTOS_PER_PERSON
    if len(photo_files) > MAX_PHOTOS_PER_PERSON:
        log(f"Limiting from {len(photo_files)} to {MAX_PHOTOS_PER_PERSON} photos")
        photo_files = photo_files[:MAX_PHOTOS_PER_PERSON]
    
    log(f"Found {len(photo_files)} photos")
    
    # Create inmate record
    inmate = create_inmate(person_name, cell_number)
    if not inmate:
        log(f"Failed to create inmate for {person_name}", "ERROR")
        stats["errors"].append(f"{person_name}: Failed to create inmate")
        return False, 0
    
    inmate_id = inmate['id']
    log(f"✓ Created inmate (ID: {inmate_id})")
    
    # Enroll all photos
    enrolled_count = 0
    for i, photo_path in enumerate(photo_files, 1):
        stats["total_photos_attempted"] += 1
        log(f"  [{i}/{len(photo_files)}] Enrolling {photo_path.name}...", end=" ")
        
        success, message = enroll_photo(inmate_id, photo_path)
        
        if success:
            enrolled_count += 1
            stats["total_photos_enrolled"] += 1
            log(f"✓ {message}")
        else:
            log(f"✗ {message}", "ERROR")
            stats["errors"].append(f"{person_name}/{photo_path.name}: {message}")
    
    # Mark as processed
    progress["processed_people"].append(person_name)
    progress["inmate_mapping"][person_name] = inmate_id
    save_progress(progress)
    
    if enrolled_count > 0:
        stats["successful_enrollments"] += 1
        log(f"✓ Successfully enrolled {enrolled_count}/{len(photo_files)} photos for {person_name}")
        return True, enrolled_count
    else:
        stats["failed_enrollments"] += 1
        log(f"✗ Failed to enroll any photos for {person_name}", "ERROR")
        return False, 0


def main():
    """Main enrollment process."""
    log("="*60)
    log("LFW Dataset Enrollment Script")
    log("="*60)
    
    # Check if server is running
    if not check_server_ready():
        log("ERROR: FastAPI server is not running!", "ERROR")
        log("Please start the server first:")
        log("  cd server")
        log("  source venv/bin/activate")
        log("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    log("✓ Server is ready")
    
    # Backup database
    backup_path = backup_database()
    if backup_path:
        log(f"✓ Database backed up to: {backup_path}")
    
    # Load progress
    progress = load_progress()
    log(f"Previously processed: {len(progress['processed_people'])} people")
    
    # Get all person directories
    if not LFW_DATASET_PATH.exists():
        log(f"ERROR: LFW dataset not found at {LFW_DATASET_PATH}", "ERROR")
        sys.exit(1)
    
    person_dirs = sorted([d for d in LFW_DATASET_PATH.iterdir() if d.is_dir()])
    stats["total_people"] = len(person_dirs)
    
    log(f"Found {len(person_dirs)} people in LFW dataset")
    log(f"Max photos per person: {MAX_PHOTOS_PER_PERSON}")
    log(f"\nStarting enrollment...\n")
    
    # Process each person
    start_time = time.time()
    
    for i, person_dir in enumerate(person_dirs, 1):
        person_name = person_dir.name
        cell_number = i
        
        try:
            success, num_enrolled = process_person(person_name, person_dir, cell_number, progress)
            stats["processed_people"] += 1
            
            # Show progress
            percent = (i / len(person_dirs)) * 100
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(person_dirs) - i) / rate if rate > 0 else 0
            
            log(f"\nProgress: {i}/{len(person_dirs)} ({percent:.1f}%) | "
                f"Rate: {rate:.2f} people/sec | "
                f"ETA: {remaining/60:.1f} min")
            
        except KeyboardInterrupt:
            log("\n\nInterrupted by user! Progress has been saved.", "WARNING")
            log("Run the script again to resume.")
            break
        
        except Exception as e:
            log(f"Unexpected error processing {person_name}: {e}", "ERROR")
            stats["errors"].append(f"{person_name}: Unexpected error: {str(e)}")
            stats["failed_enrollments"] += 1
            continue
    
    # Print summary
    elapsed_time = time.time() - start_time
    
    log("\n" + "="*60)
    log("ENROLLMENT COMPLETE")
    log("="*60)
    log(f"Total time: {elapsed_time/60:.1f} minutes")
    log(f"Total people in dataset: {stats['total_people']}")
    log(f"Processed: {stats['processed_people']}")
    log(f"Skipped (already done): {stats['skipped_people']}")
    log(f"Successful enrollments: {stats['successful_enrollments']}")
    log(f"Failed enrollments: {stats['failed_enrollments']}")
    log(f"Total photos attempted: {stats['total_photos_attempted']}")
    log(f"Total photos enrolled: {stats['total_photos_enrolled']}")
    log(f"Errors: {len(stats['errors'])}")
    
    if stats['errors']:
        log(f"\nFirst 10 errors:")
        for error in stats['errors'][:10]:
            log(f"  - {error}")
    
    log(f"\nDatabase location: {DATABASE_PATH}")
    if backup_path:
        log(f"Backup location: {backup_path}")
    log(f"Progress file: {PROGRESS_FILE}")
    log(f"Log file: {LOG_FILE}")


if __name__ == "__main__":
    main()