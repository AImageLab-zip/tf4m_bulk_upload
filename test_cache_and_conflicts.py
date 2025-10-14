#!/usr/bin/env python3
"""
Test distributed cache and file conflict resolution.
"""

import sys
import os
import tempfile
import shutil

# Add the project root to the Python path
sys.path.append(r'C:\Users\Federico\Desktop\Desktop App TF4M')

from core.file_analyzer import FileAnalyzer
from core.project_manager import ProjectManager
from core.models import PatientData, FileData, DataType, MatchStatus

def test_distributed_cache():
    """Test distributed cache functionality."""
    print("Testing Distributed Cache")
    print("=" * 30)
    
    # Create a temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        patient_folder = os.path.join(temp_dir, "TestPatient")
        os.makedirs(patient_folder)
        
        # Create some test files
        test_files = [
            "image1.jpg",
            "image2.jpg", 
            "scan.dcm"
        ]
        
        for filename in test_files:
            file_path = os.path.join(patient_folder, filename)
            with open(file_path, 'w') as f:
                f.write(f"test content for {filename}")
        
        print(f"Created test patient folder: {patient_folder}")
        
        # Initialize analyzer with distributed cache (default)
        analyzer = FileAnalyzer()
        
        # Analyze patient folder
        patient_data = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
        
        print(f"Initial analysis:")
        print(f"  Patient ID: {patient_data.patient_id}")
        print(f"  Total files: {len(patient_data.get_all_files())}")
        
        # Update cache
        analyzer.update_cache(patient_data)
        
        # Check if cache file was created in patient folder
        cache_file = analyzer.cache.get_patient_cache_file(patient_folder)
        print(f"Cache file path: {cache_file}")
        
        if os.path.exists(cache_file):
            print("SUCCESS: Cache file created in patient folder!")
        else:
            print("FAILURE: Cache file not found in patient folder")
        
        # Test cache loading
        patient_data_2 = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
        
        if patient_data_2:
            print("SUCCESS: Cache loaded successfully!")
        else:
            print("FAILURE: Cache loading failed")

def test_file_conflict_resolution():
    """Test file conflict resolution for manual assignments."""
    print("\nTesting File Conflict Resolution")
    print("=" * 35)
    
    # Create test patient data
    patient_data = PatientData(
        patient_id="TestPatient",
        folder_path="/test/path"
    )
    
    # Create two image files
    auto_ortho = FileData(
        path="/test/path/auto_ortho.jpg",
        data_type=DataType.ORTHOPANTOMOGRAPHY,
        confidence=0.8,
        status=MatchStatus.MATCHED
    )
    
    manual_ortho = FileData(
        path="/test/path/manual_ortho.jpg",
        data_type=DataType.ORTHOPANTOMOGRAPHY,
        confidence=1.0,
        status=MatchStatus.MANUAL
    )
    
    # Initialize project manager
    project_manager = ProjectManager()
    
    # First, add the automatically assigned orthopantomography
    project_manager._add_file_to_patient(patient_data, auto_ortho)
    
    print(f"After adding automatic orthopantomography:")
    print(f"  Orthopantomography file: {patient_data.orthopantomography.filename if patient_data.orthopantomography else 'None'}")
    print(f"  Unmatched files: {len(patient_data.unmatched_files)}")
    
    # Now manually assign another file to orthopantomography
    project_manager._add_file_to_patient(patient_data, manual_ortho)
    
    print(f"\nAfter adding manual orthopantomography:")
    print(f"  Orthopantomography file: {patient_data.orthopantomography.filename if patient_data.orthopantomography else 'None'}")
    print(f"  Status: {patient_data.orthopantomography.status.value if patient_data.orthopantomography else 'None'}")
    print(f"  Unmatched files: {len(patient_data.unmatched_files)}")
    
    if len(patient_data.unmatched_files) > 0:
        print(f"  Unmatched file: {patient_data.unmatched_files[0].filename}")
        print("SUCCESS: Previous automatic assignment moved to unmatched!")
    else:
        print("FAILURE: Previous file disappeared instead of being moved to unmatched")

if __name__ == "__main__":
    test_distributed_cache()
    test_file_conflict_resolution()