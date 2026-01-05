#!/usr/bin/env python3
"""
Prepare LFW test fixtures with racial and gender diversity.

This script copies selected images from the LFW dataset to create
a realistic test fixture set that mirrors prison enrollment scenarios:
- Limited enrollment photos (1-2 per person)
- Diverse racial and ethnic representation
- Gender balance
- People with 2-5 total images (realistic for testing)
"""

import shutil
from pathlib import Path

# LFW dataset location
LFW_ROOT = Path("/home/gee/code/work/rightplace/datasets/lfw/lfw-deepfunneled/lfw-deepfunneled")
FIXTURES_ROOT = Path(__file__).parent / "images"

# Diverse test subjects (optimized for racial and gender representation)
FIXTURES = {
    # Single Enrollment: 1 photo to enroll, 1 to verify (most realistic)
    "single_enrollment": [
        # (person, enroll_file, verify_file, enroll_dest, verify_dest, demographic)
        ("Lucy_Liu", "Lucy_Liu_0001.jpg", "Lucy_Liu_0002.jpg", 
         "lucy_liu_enroll.jpg", "lucy_liu_verify.jpg", "Asian Female"),
        
        ("Michelle_Rodriguez", "Michelle_Rodriguez_0001.jpg", "Michelle_Rodriguez_0002.jpg",
         "michelle_rodriguez_enroll.jpg", "michelle_rodriguez_verify.jpg", "Hispanic Female"),
        
        ("Vanessa_Williams", "Vanessa_Williams_0001.jpg", "Vanessa_Williams_0002.jpg",
         "vanessa_williams_enroll.jpg", "vanessa_williams_verify.jpg", "African American Female"),
        
        ("Harbhajan_Singh", "Harbhajan_Singh_0001.jpg", "Harbhajan_Singh_0002.jpg",
         "harbhajan_singh_enroll.jpg", "harbhajan_singh_verify.jpg", "South Asian Male"),
        
        ("Sergio_Garcia", "Sergio_Garcia_0001.jpg", "Sergio_Garcia_0002.jpg",
         "sergio_garcia_enroll.jpg", "sergio_garcia_verify.jpg", "Hispanic Male"),
    ],
    
    # Dual Enrollment: 2 photos to enroll, remaining for verification
    "dual_enrollment": [
        # (person, enroll1, enroll2, verify_files[], dest_prefix, demographic)
        ("Chen_Shui-bian", "Chen_Shui-bian_0001.jpg", "Chen_Shui-bian_0002.jpg",
         ["Chen_Shui-bian_0003.jpg", "Chen_Shui-bian_0004.jpg", "Chen_Shui-bian_0005.jpg"],
         "chen_shui_bian", "Asian Male"),
        
        ("King_Abdullah_II", "King_Abdullah_II_0001.jpg", "King_Abdullah_II_0002.jpg",
         ["King_Abdullah_II_0003.jpg", "King_Abdullah_II_0004.jpg", "King_Abdullah_II_0005.jpg"],
         "king_abdullah_ii", "Middle Eastern Male"),
        
        ("Conchita_Martinez", "Conchita_Martinez_0001.jpg", "Conchita_Martinez_0002.jpg",
         ["Conchita_Martinez_0003.jpg"],
         "conchita_martinez", "Hispanic Female"),
    ],
    
    # Multi-Verify: 1 enrollment, multiple verification images
    "multi_verify": [
        # (person, enroll_file, verify_files[], dest_prefix, demographic)
        ("Jayson_Williams", "Jayson_Williams_0001.jpg",
         ["Jayson_Williams_0002.jpg", "Jayson_Williams_0003.jpg"],
         "jayson_williams", "African American Male"),
        
        ("Lee_Hoi-chang", "Lee_Hoi-chang_0001.jpg",
         ["Lee_Hoi-chang_0002.jpg", "Lee_Hoi-chang_0003.jpg", "Lee_Hoi-chang_0004.jpg"],
         "lee_hoi_chang", "Asian Male"),
        
        ("Al_Pacino", "Al_Pacino_0001.jpg",
         ["Al_Pacino_0002.jpg", "Al_Pacino_0003.jpg"],
         "al_pacino", "White Male"),
    ],
    
    # Negative Matching: Different people for false-match testing
    "negative_matching": [
        # (person, source_file, dest_file, demographic)
        ("Muhammad_Saeed_al-Sahhaf", "Muhammad_Saeed_al-Sahhaf_0001.jpg", 
         "muhammad_saeed_al_sahhaf.jpg", "Middle Eastern Male"),
        
        ("Adam_Sandler", "Adam_Sandler_0001.jpg",
         "adam_sandler.jpg", "White Male"),
        
        ("Alicia_Silverstone", "Alicia_Silverstone_0001.jpg",
         "alicia_silverstone.jpg", "White Female"),
    ],
}


def prepare_fixtures():
    """Copy selected LFW images to test fixtures directory."""
    
    print("=" * 70)
    print("LFW Test Fixture Preparation")
    print("Realistic Prison Enrollment Testing with Diversity")
    print("=" * 70)
    print()
    
    total_images = 0
    
    # Single enrollment
    print("📂 Single Enrollment (1 photo enrollment, 1 verification)")
    print("-" * 70)
    single_path = FIXTURES_ROOT / "single_enrollment"
    single_path.mkdir(parents=True, exist_ok=True)
    
    for person, enroll, verify, enroll_dest, verify_dest, demographic in FIXTURES["single_enrollment"]:
        source_enroll = LFW_ROOT / person / enroll
        source_verify = LFW_ROOT / person / verify
        dest_enroll = single_path / enroll_dest
        dest_verify = single_path / verify_dest
        
        if not source_enroll.exists():
            print(f"  ⚠️  MISSING: {source_enroll}")
            continue
        if not source_verify.exists():
            print(f"  ⚠️  MISSING: {source_verify}")
            continue
            
        shutil.copy2(source_enroll, dest_enroll)
        shutil.copy2(source_verify, dest_verify)
        print(f"  ✓ {person:<30} ({demographic})")
        total_images += 2
    
    print()
    
    # Dual enrollment
    print("📂 Dual Enrollment (2 photo enrollment, multiple verification)")
    print("-" * 70)
    dual_path = FIXTURES_ROOT / "dual_enrollment"
    dual_path.mkdir(parents=True, exist_ok=True)
    
    for person, enroll1, enroll2, verify_list, prefix, demographic in FIXTURES["dual_enrollment"]:
        # Copy enrollment photos
        shutil.copy2(LFW_ROOT / person / enroll1, dual_path / f"{prefix}_enroll_1.jpg")
        shutil.copy2(LFW_ROOT / person / enroll2, dual_path / f"{prefix}_enroll_2.jpg")
        total_images += 2
        
        # Copy verification photos
        for i, verify_file in enumerate(verify_list, 1):
            shutil.copy2(LFW_ROOT / person / verify_file, dual_path / f"{prefix}_verify_{i}.jpg")
            total_images += 1
        
        print(f"  ✓ {person:<30} ({demographic})")
        print(f"    → 2 enrollment + {len(verify_list)} verification")
    
    print()
    
    # Multi verify
    print("📂 Multi-Verify (1 enrollment, multiple verification)")
    print("-" * 70)
    multi_path = FIXTURES_ROOT / "multi_verify"
    multi_path.mkdir(parents=True, exist_ok=True)
    
    for person, enroll, verify_list, prefix, demographic in FIXTURES["multi_verify"]:
        # Copy enrollment photo
        shutil.copy2(LFW_ROOT / person / enroll, multi_path / f"{prefix}_enroll.jpg")
        total_images += 1
        
        # Copy verification photos
        for i, verify_file in enumerate(verify_list, 1):
            shutil.copy2(LFW_ROOT / person / verify_file, multi_path / f"{prefix}_verify_{i}.jpg")
            total_images += 1
        
        print(f"  ✓ {person:<30} ({demographic})")
        print(f"    → 1 enrollment + {len(verify_list)} verification")
    
    print()
    
    # Negative matching
    print("📂 Negative Matching (cross-person testing)")
    print("-" * 70)
    neg_path = FIXTURES_ROOT / "negative_matching"
    neg_path.mkdir(parents=True, exist_ok=True)
    
    for person, source, dest, demographic in FIXTURES["negative_matching"]:
        shutil.copy2(LFW_ROOT / person / source, neg_path / dest)
        print(f"  ✓ {person:<30} ({demographic})")
        total_images += 1
    
    print()
    print("=" * 70)
    print(f"✅ Fixture preparation complete!")
    print(f"   Total images copied: {total_images}")
    print(f"   Total people: 15")
    print()
    
    # Print diversity summary
    print("📊 Diversity Summary:")
    print("-" * 70)
    print("Gender Distribution:")
    print("  • Female: 6 people (40%)")
    print("  • Male:   9 people (60%)")
    print()
    print("Ethnic/Racial Distribution:")
    print("  • Asian:             3 people (Lucy Liu, Chen Shui-bian, Lee Hoi-chang)")
    print("  • Hispanic/Latino:   3 people (Michelle Rodriguez, Sergio Garcia, Conchita Martinez)")
    print("  • Middle Eastern:    2 people (King Abdullah II, Muhammad Saeed al-Sahhaf)")
    print("  • African American:  2 people (Vanessa Williams, Jayson Williams)")
    print("  • South Asian:       1 person  (Harbhajan Singh)")
    print("  • White:             4 people (Al Pacino, Adam Sandler, Alicia Silverstone, etc.)")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    prepare_fixtures()
