"""
Test script to demonstrate the Excluded Files group in the file tree
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import PatientData, FileData, DataType

def test_excluded_files_grouping():
    """Test that excluded files are grouped separately"""
    
    print("=" * 70)
    print("Testing Excluded Files Grouping")
    print("=" * 70)
    print()
    
    # Create test patient data with mixed excluded/normal files
    patient = PatientData(
        patient_id="TEST_GROUPING",
        folder_path="C:/test"
    )
    
    # CBCT files - one normal, one excluded
    patient.cbct_files = [
        FileData(path="C:/test/cbct1.dcm", data_type=DataType.CBCT_DICOM),
        FileData(path="C:/test/cbct2.dcm", data_type=DataType.EXCLUDE),
        FileData(path="C:/test/cbct3.dcm", data_type=DataType.CBCT_DICOM),
    ]
    
    # IOS files
    patient.ios_upper = FileData(path="C:/test/upper.stl", data_type=DataType.IOS_UPPER)
    patient.ios_lower = FileData(path="C:/test/lower.stl", data_type=DataType.EXCLUDE)
    
    # Intraoral photos - mix of normal and excluded
    patient.intraoral_photos = [
        FileData(path="C:/test/photo1.jpg", data_type=DataType.INTRAORAL_PHOTO),
        FileData(path="C:/test/photo2.jpg", data_type=DataType.INTRAORAL_PHOTO),
        FileData(path="C:/test/photo3.jpg", data_type=DataType.EXCLUDE),
        FileData(path="C:/test/photo4.jpg", data_type=DataType.INTRAORAL_PHOTO),
        FileData(path="C:/test/photo5.jpg", data_type=DataType.EXCLUDE),
    ]
    
    # Teleradiography - excluded
    patient.teleradiography = FileData(path="C:/test/xray.jpg", data_type=DataType.EXCLUDE)
    
    # Orthopantomography - normal
    patient.orthopantomography = FileData(path="C:/test/panoramic.jpg", data_type=DataType.ORTHOPANTOMOGRAPHY)
    
    # Simulate the filtering logic from populate_files_tree
    print("📊 File Distribution Analysis:")
    print("-" * 70)
    
    # Count files by category
    regular_groups = {
        "🦷 CBCT DICOM": [],
        "🔝 IOS Upper": [],
        "🔽 IOS Lower": [],
        "📸 Intraoral Photos": [],
        "📻 Teleradiography": [],
        "🔬 Orthopantomography": []
    }
    
    excluded_files = []
    
    # Process CBCT
    for cbct in patient.cbct_files:
        if cbct.data_type == DataType.EXCLUDE:
            excluded_files.append(("CBCT", cbct.path))
        else:
            regular_groups["🦷 CBCT DICOM"].append(cbct.path)
    
    # Process IOS
    if patient.ios_upper:
        if patient.ios_upper.data_type == DataType.EXCLUDE:
            excluded_files.append(("IOS Upper", patient.ios_upper.path))
        else:
            regular_groups["🔝 IOS Upper"].append(patient.ios_upper.path)
    
    if patient.ios_lower:
        if patient.ios_lower.data_type == DataType.EXCLUDE:
            excluded_files.append(("IOS Lower", patient.ios_lower.path))
        else:
            regular_groups["🔽 IOS Lower"].append(patient.ios_lower.path)
    
    # Process intraoral photos
    for photo in patient.intraoral_photos:
        if photo.data_type == DataType.EXCLUDE:
            excluded_files.append(("Intraoral Photo", photo.path))
        else:
            regular_groups["📸 Intraoral Photos"].append(photo.path)
    
    # Process teleradiography
    if patient.teleradiography:
        if patient.teleradiography.data_type == DataType.EXCLUDE:
            excluded_files.append(("Teleradiography", patient.teleradiography.path))
        else:
            regular_groups["📻 Teleradiography"].append(patient.teleradiography.path)
    
    # Process orthopantomography
    if patient.orthopantomography:
        if patient.orthopantomography.data_type == DataType.EXCLUDE:
            excluded_files.append(("Orthopantomography", patient.orthopantomography.path))
        else:
            regular_groups["🔬 Orthopantomography"].append(patient.orthopantomography.path)
    
    # Display regular groups
    print("\n📁 REGULAR FILE GROUPS:")
    print("-" * 70)
    total_regular = 0
    for group_name, files in regular_groups.items():
        if files:
            print(f"\n{group_name} ({len(files)} files):")
            for file_path in files:
                print(f"  ✓ {os.path.basename(file_path)}")
            total_regular += len(files)
    
    # Display excluded group
    print("\n\n🚫 EXCLUDED FILES GROUP:")
    print("-" * 70)
    if excluded_files:
        print(f"\n🚫 Excluded Files ({len(excluded_files)} files):")
        for original_type, file_path in excluded_files:
            print(f"  🚫 {os.path.basename(file_path):20} (was: {original_type})")
    else:
        print("  (No excluded files)")
    
    print("\n" + "=" * 70)
    print("📈 SUMMARY:")
    print("-" * 70)
    print(f"  Regular Files:  {total_regular} files (will be uploaded)")
    print(f"  Excluded Files: {len(excluded_files)} files (will NOT be uploaded)")
    print(f"  Total Files:    {total_regular + len(excluded_files)} files")
    print("=" * 70)
    print()
    
    print("✨ Key Benefits of Separate Excluded Group:")
    print("-" * 70)
    print("  1. Clear visual separation of excluded vs. active files")
    print("  2. Easy to see how many files are excluded at a glance")
    print("  3. Grouped by exclusion status rather than original type")
    print("  4. Cleaner display - no 'EXCLUDED' labels in regular groups")
    print("  5. All excluded files in one place for review")
    print("-" * 70)

if __name__ == "__main__":
    test_excluded_files_grouping()
