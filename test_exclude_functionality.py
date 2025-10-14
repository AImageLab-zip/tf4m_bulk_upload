"""
Test script to verify the exclude functionality for file uploads
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import PatientData, FileData, DataType
from core.api_client import TF4MAPIClient

def test_exclude_functionality():
    """Test that excluded files are not included in upload"""
    
    print("=" * 60)
    print("Testing Exclude Functionality")
    print("=" * 60)
    print()
    
    # Create test patient data
    patient = PatientData(
        patient_id="TEST_EXCLUDE",
        folder_path="C:/test"
    )
    
    # Add some test files with different types
    patient.ios_upper = FileData(
        path="C:/test/upper.stl",
        data_type=DataType.IOS_UPPER
    )
    
    patient.ios_lower = FileData(
        path="C:/test/lower.stl",
        data_type=DataType.EXCLUDE  # This should be excluded
    )
    
    patient.intraoral_photos = [
        FileData(path="C:/test/photo1.jpg", data_type=DataType.INTRAORAL_PHOTO),
        FileData(path="C:/test/photo2.jpg", data_type=DataType.EXCLUDE),  # Excluded
        FileData(path="C:/test/photo3.jpg", data_type=DataType.INTRAORAL_PHOTO),
    ]
    
    patient.teleradiography = FileData(
        path="C:/test/xray.jpg",
        data_type=DataType.TELERADIOGRAPHY
    )
    
    patient.orthopantomography = FileData(
        path="C:/test/panoramic.jpg",
        data_type=DataType.EXCLUDE  # This should be excluded
    )
    
    # Test the API client's file gathering
    api_client = TF4MAPIClient("http://test.com", project_slug="maxillo")
    files_to_upload = api_client._get_all_patient_files(patient)
    
    print("Files to upload (after exclusion filtering):")
    print("-" * 60)
    
    expected_files = [
        ("upper.stl", "upper_scan_raw"),
        ("photo1.jpg", "intraoral_photos"),
        ("photo3.jpg", "intraoral_photos"),
        ("xray.jpg", "teleradiography"),
    ]
    
    excluded_files = [
        "lower.stl",
        "photo2.jpg",
        "panoramic.jpg"
    ]
    
    # Check results
    uploaded_count = 0
    for file_data, field_name in files_to_upload:
        print(f"  ✓ {os.path.basename(file_data.path):20} → {field_name}")
        uploaded_count += 1
    
    print()
    print(f"Total files to upload: {uploaded_count}")
    print()
    
    # Verify excluded files are not in the list
    print("Verifying exclusions:")
    print("-" * 60)
    
    upload_paths = [os.path.basename(f[0].path) for f in files_to_upload]
    
    all_correct = True
    for excluded_file in excluded_files:
        if excluded_file in upload_paths:
            print(f"  ❌ ERROR: {excluded_file} should be excluded but was found!")
            all_correct = False
        else:
            print(f"  ✓ {excluded_file:20} correctly excluded")
    
    print()
    
    # Summary
    print("=" * 60)
    if all_correct and uploaded_count == len(expected_files):
        print("✅ All tests passed!")
        print(f"  - {uploaded_count} files will be uploaded")
        print(f"  - {len(excluded_files)} files correctly excluded")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    print()
    
    # Display feature summary
    print("Exclude Feature Summary:")
    print("-" * 60)
    print("1. Added DataType.EXCLUDE to models.py")
    print("2. Updated ReassignTypeDialog with 'Exclude from Upload' option")
    print("3. API client filters out excluded files during upload")
    print("4. Excluded files shown with 🚫 icon and gray text")
    print("5. Files can be reassigned from any type to EXCLUDE")
    print("-" * 60)

if __name__ == "__main__":
    test_exclude_functionality()
