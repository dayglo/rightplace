# Test Fixtures - LFW Dataset

## Overview

This directory contains carefully selected test images from the **Labeled Faces in the Wild (LFW)** dataset, organized to test realistic prison enrollment scenarios with diversity in race, ethnicity, and gender.

## Dataset Statistics

- **Total Images:** 36
- **Total People:** 15
- **Source:** LFW Deep-Funneled Dataset
- **Image Format:** JPEG, 250x250 pixels

## Diversity Profile

### Gender Distribution
- **Female:** 6 people (40%)
- **Male:** 9 people (60%)

### Ethnic/Racial Distribution
- **Asian:** 3 people (20%)
  - Lucy Liu, Chen Shui-bian, Lee Hoi-chang
- **Hispanic/Latino:** 3 people (20%)
  - Michelle Rodriguez, Sergio Garcia, Conchita Martinez
- **Middle Eastern:** 2 people (13%)
  - King Abdullah II, Muhammad Saeed al-Sahhaf
- **African American:** 2 people (13%)
  - Vanessa Williams, Jayson Williams
- **South Asian:** 1 person (7%)
  - Harbhajan Singh
- **White:** 4 people (27%)
  - Al Pacino, Adam Sandler, Alicia Silverstone, etc.

---

## Directory Structure

```
images/
├── single_enrollment/       # 1 enrollment photo, 1 verification (most realistic)
│   ├── lucy_liu_enroll.jpg
│   ├── lucy_liu_verify.jpg
│   ├── michelle_rodriguez_enroll.jpg
│   ├── michelle_rodriguez_verify.jpg
│   ├── vanessa_williams_enroll.jpg
│   ├── vanessa_williams_verify.jpg
│   ├── harbhajan_singh_enroll.jpg
│   ├── harbhajan_singh_verify.jpg
│   ├── sergio_garcia_enroll.jpg
│   └── sergio_garcia_verify.jpg
│
├── dual_enrollment/         # 2 enrollment photos, multiple verification
│   ├── chen_shui_bian_enroll_1.jpg
│   ├── chen_shui_bian_enroll_2.jpg
│   ├── chen_shui_bian_verify_1.jpg
│   ├── chen_shui_bian_verify_2.jpg
│   ├── chen_shui_bian_verify_3.jpg
│   ├── king_abdullah_ii_enroll_1.jpg
│   ├── king_abdullah_ii_enroll_2.jpg
│   ├── king_abdullah_ii_verify_1.jpg
│   ├── king_abdullah_ii_verify_2.jpg
│   ├── king_abdullah_ii_verify_3.jpg
│   ├── conchita_martinez_enroll_1.jpg
│   ├── conchita_martinez_enroll_2.jpg
│   └── conchita_martinez_verify_1.jpg
│
├── multi_verify/            # 1 enrollment, multiple verification images
│   ├── jayson_williams_enroll.jpg
│   ├── jayson_williams_verify_1.jpg
│   ├── jayson_williams_verify_2.jpg
│   ├── lee_hoi_chang_enroll.jpg
│   ├── lee_hoi_chang_verify_1.jpg
│   ├── lee_hoi_chang_verify_2.jpg
│   ├── lee_hoi_chang_verify_3.jpg
│   ├── al_pacino_enroll.jpg
│   ├── al_pacino_verify_1.jpg
│   └── al_pacino_verify_2.jpg
│
└── negative_matching/       # Different people for false-match testing
    ├── muhammad_saeed_al_sahhaf.jpg
    ├── adam_sandler.jpg
    └── alicia_silverstone.jpg
```

---

## Test Categories

### 1. Single Enrollment (5 people, 10 images)

**Purpose:** Test the most realistic prison scenario where each inmate has only 1 enrollment photo.

| Person | Demographic | Enrollment | Verification |
|--------|------------|------------|--------------|
| Lucy Liu | Asian Female | ✓ | ✓ |
| Michelle Rodriguez | Hispanic Female | ✓ | ✓ |
| Vanessa Williams | African American Female | ✓ | ✓ |
| Harbhajan Singh | South Asian Male | ✓ | ✓ |
| Sergio Garcia | Hispanic Male | ✓ | ✓ |

**Test Scenarios:**
- Minimum enrollment requirements
- Same person, different photo
- Cross-gender matching
- Cross-racial accuracy

---

### 2. Dual Enrollment (3 people, 13 images)

**Purpose:** Test recommended best practice where inmates are enrolled with 2 photos for improved accuracy.

| Person | Demographic | Enrollments | Verifications |
|--------|------------|-------------|---------------|
| Chen Shui-bian | Asian Male | 2 | 3 |
| King Abdullah II | Middle Eastern Male | 2 | 3 |
| Conchita Martinez | Hispanic Female | 2 | 1 |

**Test Scenarios:**
- Dual photo enrollment improves confidence
- Multiple verification images
- Angle variation in enrollment

---

### 3. Multi-Verify (3 people, 10 images)

**Purpose:** Test system consistency across multiple verification attempts for the same person.

| Person | Demographic | Enrollments | Verifications |
|--------|------------|-------------|---------------|
| Jayson Williams | African American Male | 1 | 2 |
| Lee Hoi-chang | Asian Male | 1 | 3 |
| Al Pacino | White Male | 1 | 2 |

**Test Scenarios:**
- Consistent matching across attempts
- Confidence score stability
- Verification repeatability

---

### 4. Negative Matching (3 people, 3 images)

**Purpose:** Test that different people do NOT match (false positive prevention).

| Person | Demographic | Use Case |
|--------|------------|----------|
| Muhammad Saeed al-Sahhaf | Middle Eastern Male | Cross-person testing |
| Adam Sandler | White Male | False match prevention |
| Alicia Silverstone | White Female | Gender/cross-person testing |

**Test Scenarios:**
- No false positives
- Confidence scores below threshold
- 1:N matching accuracy

---

## Regenerating Fixtures

If you need to regenerate the fixtures (e.g., after dataset updates):

```bash
cd server
source .venv/bin/activate  # Activate virtual environment
python3 tests/fixtures/prepare_lfw_fixtures.py
```

This will:
1. Create the `images/` directory structure
2. Copy all 36 images from LFW dataset
3. Print diversity summary
4. Validate all source images exist

---

## Usage in Tests

### Example: Single Enrollment Test

```python
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "images"

def test_single_photo_enrollment():
    """Test realistic single-photo enrollment scenario."""
    enroll_img = FIXTURES / "single_enrollment" / "lucy_liu_enroll.jpg"
    verify_img = FIXTURES / "single_enrollment" / "lucy_liu_verify.jpg"
    
    # Enroll with single photo
    service.enroll("inmate_001", enroll_img)
    
    # Verify with different photo of same person
    result = service.verify(verify_img, ["inmate_001"])
    
    assert result.matched is True
    assert result.confidence >= 0.75
```

### Example: Cross-Racial Matching Test

```python
def test_cross_racial_matching():
    """Ensure system works equally well across races."""
    # Enroll diverse subjects
    service.enroll("asian_001", FIXTURES / "single_enrollment" / "lucy_liu_enroll.jpg")
    service.enroll("hispanic_001", FIXTURES / "single_enrollment" / "michelle_rodriguez_enroll.jpg")
    service.enroll("african_american_001", FIXTURES / "single_enrollment" / "vanessa_williams_enroll.jpg")
    
    # Verify each
    results = [
        service.verify(FIXTURES / "single_enrollment" / "lucy_liu_verify.jpg", enrolled_ids),
        service.verify(FIXTURES / "single_enrollment" / "michelle_rodriguez_verify.jpg", enrolled_ids),
        service.verify(FIXTURES / "single_enrollment" / "vanessa_williams_verify.jpg", enrolled_ids),
    ]
    
    # All should match with similar confidence
    assert all(r.matched for r in results)
    assert all(r.confidence >= 0.75 for r in results)
```

---

## Design Rationale

### Why LFW Dataset?

1. **Realistic Constraints:** People with 2-5 images mirror prison enrollment reality
2. **Diversity:** Includes people of various races, ethnicities, and genders
3. **Quality:** Deep-funneled preprocessing ensures consistent face detection
4. **Standard Benchmark:** Widely used in face recognition research
5. **Size:** 13,233 images of 5,749 people - sufficient variety for testing

### Why NOT High-Image-Count People?

We intentionally avoided using people with 100+ images (e.g., George W. Bush with 530) because:
- **Unrealistic:** Prisons won't take hundreds of photos per inmate
- **Overfitting Risk:** Tests might pass only because of excessive training data
- **Operational Reality:** System must work with 1-2 enrollment photos

### Diversity Considerations

- **40% female representation** reflects diverse facility populations
- **5 distinct ethnic/racial groups** ensure cross-racial accuracy
- **Mix of public figures** from politics, sports, entertainment reduces bias toward any single domain
- **Balanced 2-5 image counts** test both minimal and recommended enrollment practices

---

## License

The LFW dataset is publicly available for research purposes. Original dataset:
- **Source:** University of Massachusetts, Amherst
- **Citation:** Huang et al., "Labeled Faces in the Wild"
- **License:** Research and non-commercial use

---

## Maintenance

**Last Updated:** January 5, 2026  
**LFW Version:** Deep-Funneled  
**Total Fixtures:** 36 images, 15 people  
**Prepared By:** `prepare_lfw_fixtures.py`
