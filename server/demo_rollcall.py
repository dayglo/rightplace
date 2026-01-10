#!/usr/bin/env python3
"""
Prison Roll Call Demo Script

This script demonstrates a complete rollcall process with:
1. Lucy Liu (Cell 101) - Present and verified ✓
2. Sergio Garcia (Cell 102) - Not found ✗
3. Michelle Rodriguez (Cell 103) - First attempt fails, retry succeeds ✓

Press SPACE to advance through each step.
"""

import os
import sys
import time
import json
import requests
import subprocess
import argparse
from pathlib import Path
from typing import Optional
import signal

# Color codes for terminal output
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures" / "images"
LOG_FILE = "/tmp/rollcall_demo.log"
SERVER_PROCESS = None
DONT_WAIT = False  # Global flag for --dont-wait mode

def print_header(text: str):
    """Print a colorful header"""
    print(f"\n{Color.BOLD}{Color.CYAN}{'='*60}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{text.center(60)}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*60}{Color.END}\n")

def print_step(step_num: int, text: str):
    """Print a step header"""
    print(f"\n{Color.BOLD}{Color.BLUE}[Step {step_num}]{Color.END} {Color.BOLD}{text}{Color.END}")

def print_success(text: str):
    """Print success message"""
    print(f"{Color.GREEN}✓ {text}{Color.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Color.RED}✗ {text}{Color.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Color.YELLOW}ℹ {text}{Color.END}")

def print_json(data: dict):
    """Print formatted JSON"""
    print(f"{Color.CYAN}{json.dumps(data, indent=2)}{Color.END}")

def wait_for_space():
    """Wait for user to press spacebar (or skip if --dont-wait)"""
    if DONT_WAIT:
        print(f"\n{Color.YELLOW}[Auto-continuing in --dont-wait mode]{Color.END}\n")
        time.sleep(0.5)  # Brief pause for readability
        return
    
    print(f"\n{Color.YELLOW}[Press SPACE to continue...]{Color.END}")
    
    # Handle different operating systems
    if os.name == 'nt':  # Windows
        import msvcrt
        while True:
            if msvcrt.getch() == b' ':
                break
    else:  # Unix/Linux/Mac
        import termios
        import tty
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch == ' ':
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    print()  # New line after key press

def start_server():
    """Start the FastAPI server in background"""
    global SERVER_PROCESS
    
    print_info("Starting FastAPI server...")
    
    # Activate venv and start server
    venv_python = Path(__file__).parent / "venv" / "bin" / "python"
    
    # Create log file
    log_file = open(LOG_FILE, 'w')
    
    SERVER_PROCESS = subprocess.Popen(
        [str(venv_python), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=Path(__file__).parent,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid if os.name != 'nt' else None
    )
    
    print_info(f"Server output being logged to: {LOG_FILE}")
    print_info(f"Tail logs with: tail -f {LOG_FILE}")
    
    # Wait for server to be ready
    print_info("Waiting for server to be ready (loading models, may take 60s)...")
    max_attempts = 60
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                print_success("Server is ready!")
                print_info("Waiting for database and DeepFace models to fully initialize...")
                time.sleep(10)  # Give database and DeepFace models time to fully load
                return
        except requests.exceptions.RequestException:
            time.sleep(1)
            print(f".", end="", flush=True)
    
    print_error("Server failed to start within 60 seconds")
    sys.exit(1)

def stop_server():
    """Stop the FastAPI server"""
    global SERVER_PROCESS
    if SERVER_PROCESS:
        print_info("Stopping server...")
        if os.name != 'nt':
            os.killpg(os.getpgid(SERVER_PROCESS.pid), signal.SIGTERM)
        else:
            SERVER_PROCESS.terminate()
        SERVER_PROCESS.wait()
        print_success("Server stopped")

def cleanup_database():
    """Clean up and initialize the database using the setup script"""
    print_info("Initializing fresh database using setup_db.py...")
    
    # Run the setup_db.py script to properly initialize the database
    venv_python = Path(__file__).parent / "venv" / "bin" / "python"
    setup_script = Path(__file__).parent / "scripts" / "setup_db.py"
    
    result = subprocess.run(
        [str(venv_python), str(setup_script)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("Database initialized successfully!")
        # Show the output from setup_db.py
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                print(f"  {line}")
    else:
        print_error("Failed to initialize database!")
        print_error(f"Error: {result.stderr}")
        raise Exception("Database initialization failed")

def setup_test_data():
    """Create locations, inmates, and enroll faces"""
    print_header("SETUP: Creating Test Data")
    
    # Create Block A
    print_step(1, "Creating Cell Block A")
    response = requests.post(f"{BASE_URL}/locations", json={
        "name": "Block A",
        "type": "block",
        "building": "Main",
        "capacity": 100
    })
    
    if response.status_code not in [200, 201]:
        print_error(f"Failed to create location: HTTP {response.status_code}")
        print_error(f"Response: {response.text}")
        raise Exception(f"Location creation failed: {response.text}")
        
    block_a_id = response.json()["id"]
    print_success(f"Block A created (ID: {block_a_id})")
    
    # Create cells
    cells = {}
    for cell_num in [101, 102, 103]:
        print_step(2, f"Creating Cell {cell_num}")
        response = requests.post(f"{BASE_URL}/locations", json={
            "name": f"Cell {cell_num}",
            "type": "cell",
            "parent_id": block_a_id,
            "building": "Main",
            "capacity": 1
        })
        cells[cell_num] = response.json()["id"]
        print_success(f"Cell {cell_num} created (ID: {cells[cell_num]})")
    
    # Create inmates
    inmates_data = [
        {
            "inmate_number": "A-001",
            "first_name": "Lucy",
            "last_name": "Liu",
            "date_of_birth": "1968-12-02",
            "cell_block": "A",
            "cell_number": "101"
        },
        {
            "inmate_number": "A-002",
            "first_name": "Sergio",
            "last_name": "Garcia",
            "date_of_birth": "1980-01-09",
            "cell_block": "A",
            "cell_number": "102"
        },
        {
            "inmate_number": "A-003",
            "first_name": "Michelle",
            "last_name": "Rodriguez",
            "date_of_birth": "1978-07-12",
            "cell_block": "A",
            "cell_number": "103"
        }
    ]
    
    inmates = {}
    for data in inmates_data:
        print_step(3, f"Creating inmate {data['first_name']} {data['last_name']}")
        response = requests.post(f"{BASE_URL}/inmates", json=data)
        
        if response.status_code not in [200, 201]:
            print_error(f"Failed to create inmate: HTTP {response.status_code}")
            print_error(f"Response: {response.text}")
            raise Exception(f"Inmate creation failed: {response.text}")
        
        try:
            inmate = response.json()
        except Exception as e:
            print_error(f"Failed to parse JSON response: {e}")
            print_error(f"Raw response: {response.text}")
            print_error(f"Response headers: {response.headers}")
            raise
            
        inmates[data['inmate_number']] = inmate
        print_success(f"{data['first_name']} {data['last_name']} created (ID: {inmate['id']})")
    
    # Enroll faces
    enrollment_files = {
        "A-001": "single_enrollment/lucy_liu_enroll.jpg",
        "A-002": "single_enrollment/sergio_garcia_enroll.jpg",
        "A-003": "single_enrollment/michelle_rodriguez_enroll.jpg"
    }
    
    for inmate_num, file_path in enrollment_files.items():
        inmate = inmates[inmate_num]
        print_step(4, f"Enrolling {inmate['first_name']} {inmate['last_name']}")
        
        image_path = FIXTURES_DIR / file_path
        with open(image_path, 'rb') as f:
            # Properly set the file content type as image/jpeg
            files = {'image': (image_path.name, f, 'image/jpeg')}
            response = requests.post(
                f"{BASE_URL}/enrollment/{inmate['id']}",
                files=files
            )
        
        if response.status_code != 200:
            print_error(f"Failed to enroll {inmate['first_name']}: HTTP {response.status_code}")
            print_error(f"Response: {response.text}")
            continue
            
        result = response.json()
        if result.get('success'):
            print_success(f"{inmate['first_name']} enrolled (quality: {result['quality']:.2f})")
        else:
            print_error(f"Failed to enroll {inmate['first_name']}: {result.get('error', 'Unknown error')}")
            print_error(f"Response: {json.dumps(result, indent=2)}")
    
    print_success("\nSetup complete! All inmates enrolled.")
    return cells, inmates

def run_rollcall_demo(cells: dict, inmates: dict):
    """Run the interactive rollcall demonstration"""
    print_header("ROLLCALL DEMONSTRATION")
    
    # Step 1: Create roll call
    print_step(1, "Creating Roll Call")
    
    # Schedule for 10 seconds in the future to avoid "time in the past" error
    from datetime import datetime, timedelta
    scheduled_time = datetime.now() + timedelta(seconds=10)
    
    rollcall_data = {
        "name": "Block A Morning Roll Call",
        "scheduled_at": scheduled_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "officer_id": "officer_demo",
        "route": [
            {
                "id": f"stop-{cells[101]}",
                "location_id": cells[101],
                "order": 0,
                "expected_inmates": [inmates["A-001"]["id"]]
            },
            {
                "id": f"stop-{cells[102]}",
                "location_id": cells[102],
                "order": 1,
                "expected_inmates": [inmates["A-002"]["id"]]
            },
            {
                "id": f"stop-{cells[103]}",
                "location_id": cells[103],
                "order": 2,
                "expected_inmates": [inmates["A-003"]["id"]]
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/rollcalls", json=rollcall_data)
    if response.status_code not in [200, 201]:
        print_error(f"Failed to create roll call: HTTP {response.status_code}")
        print_error(f"Response: {response.text}")
        raise Exception(f"Roll call creation failed: {response.text}")
    
    rollcall = response.json()
    print_success(f"Roll call created: {rollcall['name']}")
    print_info(f"Roll Call ID: {rollcall['id']}")
    wait_for_space()
    
    # Step 2: Start roll call
    print_step(2, "Starting Roll Call")
    response = requests.post(f"{BASE_URL}/rollcalls/{rollcall['id']}/start")
    print_success("Roll call started!")
    print_info(f"Route: Cell 101 → Cell 102 → Cell 103")
    wait_for_space()
    
    # Step 3: Verify Lucy Liu (Cell 101) - SUCCESS
    print_step(3, "Arriving at Cell 101 - Expecting Lucy Liu (A-001)")
    wait_for_space()
    
    print_info("Capturing photo...")
    image_path = FIXTURES_DIR / "single_enrollment/lucy_liu_verify.jpg"
    with open(image_path, 'rb') as f:
        files = {'image': (image_path.name, f, 'image/jpeg')}
        response = requests.post(
            f"{BASE_URL}/verify/quick",
            files=files,
            data={
                'location_id': cells[101],
                'roll_call_id': rollcall['id']
            }
        )
    
    verify_result = response.json()
    print_json(verify_result)
    
    if verify_result.get('matched'):
        print_success(f"✓ {verify_result['inmate']['first_name']} {verify_result['inmate']['last_name']} verified!")
        print_info(f"Confidence: {verify_result['confidence']:.1%}")
        print_info(f"Recommendation: {verify_result['recommendation']}")
        
        # Record verification
        requests.post(f"{BASE_URL}/rollcalls/{rollcall['id']}/verification", json={
            "inmate_id": inmates["A-001"]["id"],
            "location_id": cells[101],
            "status": "verified",
            "confidence": verify_result['confidence'],
            "is_manual_override": False,
            "notes": ""
        })
    else:
        print_error("Verification failed!")
    
    wait_for_space()
    
    # Step 4: Verify Sergio Garcia (Cell 102) - NOT FOUND
    print_step(4, "Arriving at Cell 102 - Expecting Sergio Garcia (A-002)")
    wait_for_space()
    
    print_info("Capturing photo...")
    print_error("No inmate present in cell!")
    print_info("Using photo of wrong person to demonstrate no-match scenario...")
    
    image_path = FIXTURES_DIR / "single_enrollment/vanessa_williams_verify.jpg"
    with open(image_path, 'rb') as f:
        files = {'image': (image_path.name, f, 'image/jpeg')}
        response = requests.post(
            f"{BASE_URL}/verify/quick",
            files=files,
            data={
                'location_id': cells[102],
                'roll_call_id': rollcall['id']
            }
        )
    
    verify_result = response.json()
    print_json(verify_result)
    
    if not verify_result.get('matched'):
        print_error("✗ Sergio Garcia NOT FOUND at Cell 102")
        if 'confidence' in verify_result:
            print_info(f"Highest match confidence: {verify_result['confidence']:.1%} (below threshold)")
        
        # Record as not found
        requests.post(f"{BASE_URL}/rollcalls/{rollcall['id']}/verification", json={
            "inmate_id": inmates["A-002"]["id"],
            "location_id": cells[102],
            "status": "not_found",
            "confidence": 0.0,
            "is_manual_override": False,
            "notes": "Inmate not present at expected location"
        })
    
    wait_for_space()
    
    # Step 5: Verify Michelle Rodriguez (Cell 103) - FAIL THEN SUCCEED
    print_step(5, "Arriving at Cell 103 - Expecting Michelle Rodriguez (A-003)")
    wait_for_space()
    
    print_info("First attempt: Capturing photo (poor angle/lighting)...")
    image_path = FIXTURES_DIR / "single_enrollment/harbhajan_singh_verify.jpg"
    with open(image_path, 'rb') as f:
        files = {'image': (image_path.name, f, 'image/jpeg')}
        response = requests.post(
            f"{BASE_URL}/verify/quick",
            files=files,
            data={
                'location_id': cells[103],
                'roll_call_id': rollcall['id']
            }
        )
    
    verify_result = response.json()
    print_json(verify_result)
    
    if not verify_result.get('matched'):
        print_error("✗ First attempt failed - no match found")
        print_info(f"Confidence: {verify_result['confidence']:.1%}")
        print_info("Officer repositions camera for better angle...")
    
    wait_for_space()
    
    print_info("Second attempt: Recapturing photo...")
    image_path = FIXTURES_DIR / "single_enrollment/michelle_rodriguez_verify.jpg"
    with open(image_path, 'rb') as f:
        files = {'image': (image_path.name, f, 'image/jpeg')}
        response = requests.post(
            f"{BASE_URL}/verify/quick",
            files=files,
            data={
                'location_id': cells[103],
                'roll_call_id': rollcall['id']
            }
        )
    
    verify_result = response.json()
    print_json(verify_result)
    
    if verify_result.get('matched'):
        print_success(f"✓ {verify_result['inmate']['first_name']} {verify_result['inmate']['last_name']} verified!")
        print_info(f"Confidence: {verify_result['confidence']:.1%}")
        print_info(f"Recommendation: {verify_result['recommendation']}")
        
        # Record verification
        requests.post(f"{BASE_URL}/rollcalls/{rollcall['id']}/verification", json={
            "inmate_id": inmates["A-003"]["id"],
            "location_id": cells[103],
            "status": "verified",
            "confidence": verify_result['confidence'],
            "is_manual_override": False,
            "notes": "Second attempt after repositioning"
        })
    
    wait_for_space()
    
    # Step 6: Complete roll call
    print_step(6, "Completing Roll Call")
    response = requests.post(f"{BASE_URL}/rollcalls/{rollcall['id']}/complete")
    final_rollcall = response.json()
    
    print_header("ROLL CALL COMPLETE")
    print_success(f"Roll Call: {final_rollcall['name']}")
    print_info(f"Status: {final_rollcall['status']}")
    print_info(f"Started: {final_rollcall['started_at']}")
    print_info(f"Completed: {final_rollcall['completed_at']}")
    
    print(f"\n{Color.BOLD}Summary:{Color.END}")
    print_success("Verified: 2/3 (Lucy Liu, Michelle Rodriguez)")
    print_error("Not Found: 1/3 (Sergio Garcia)")
    print_info("Retries: 1 (Michelle Rodriguez)")

def main():
    """Main demo execution"""
    global DONT_WAIT
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Prison Roll Call Interactive Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./demo_rollcall.py              # Interactive mode (press SPACE to advance)
  ./demo_rollcall.py --dont-wait  # Auto-run mode (no pauses)
        """
    )
    parser.add_argument(
        '--dont-wait',
        action='store_true',
        help='Run demo automatically without waiting for spacebar'
    )
    
    args = parser.parse_args()
    DONT_WAIT = args.dont_wait
    
    if DONT_WAIT:
        print_header("AUTOMATED DEMO MODE")
        print_info("Running in --dont-wait mode (no spacebar required)")
    else:
        print_header("INTERACTIVE DEMO MODE")
        print_info("Press SPACE at each step to advance")
    
    try:
        # Initialize fresh database with proper schema
        cleanup_database()
        
        # Start server
        start_server()
        
        # Run setup
        cells, inmates = setup_test_data()
        
        print_info("\nTest data setup complete. Starting interactive demo...")
        wait_for_space()
        
        # Run demo
        run_rollcall_demo(cells, inmates)
        
        print_header("DEMO COMPLETE")
        print_success("Thank you for watching the Prison Roll Call demonstration!")
        print_info(f"\nServer logs available at: {LOG_FILE}")
        print_info("Press Ctrl+C to stop the server and exit")
        
        # Keep server running
        input("\nPress Enter to stop server and exit...")
        
    except KeyboardInterrupt:
        print_info("\n\nDemo interrupted by user")
    except Exception as e:
        print_error(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_server()

if __name__ == "__main__":
    main()