#!/usr/bin/env python3
"""
Test tmp folder exclusion.
"""

import sys
import os
import tempfile
import shutil

# Add the project root to the Python path
sys.path.append(r'C:\Users\Federico\Desktop\Desktop App TF4M')

from core.project_manager import ProjectManager
from core.file_analyzer import FileAnalyzer

def test_tmp_folder_exclusion():
    """Test that tmp folders are properly excluded."""
    print("Testing tmp folder exclusion")
    print("=" * 50)
    
    # Create a temporary test directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Creating test structure in: {temp_dir}")
        
        # Create patient folders
        patient1_dir = os.path.join(temp_dir, "Patient1")
        patient2_dir = os.path.join(temp_dir, "Patient2")
        tmp_dir = os.path.join(temp_dir, "tmp")
        
        os.makedirs(patient1_dir)
        os.makedirs(patient2_dir)
        os.makedirs(tmp_dir)
        
        # Create some test files
        with open(os.path.join(patient1_dir, "test1.dcm"), 'w') as f:
            f.write("test dicom file")
        with open(os.path.join(patient2_dir, "test2.jpg"), 'w') as f:
            f.write("test image file")
        with open(os.path.join(tmp_dir, "temp_file.nii.gz"), 'w') as f:
            f.write("temp nifti file")
        
        # Create tmp folder inside a patient folder too
        patient1_tmp = os.path.join(patient1_dir, "tmp")
        os.makedirs(patient1_tmp)
        with open(os.path.join(patient1_tmp, "patient_temp.zip"), 'w') as f:
            f.write("patient temp file")
        
        print("Test directory structure created:")
        print(f"  {temp_dir}/")
        print(f"    Patient1/")
        print(f"      test1.dcm")
        print(f"      tmp/")
        print(f"        patient_temp.zip")
        print(f"    Patient2/")
        print(f"      test2.jpg")
        print(f"    tmp/")
        print(f"      temp_file.nii.gz")
        
        # Test ProjectManager patient folder detection
        project_manager = ProjectManager()
        
        # Use the internal method to find patient folders
        patient_folders = project_manager._find_patient_folders(temp_dir)
        
        print(f"\nFound patient folders: {len(patient_folders)}")
        for folder in patient_folders:
            folder_name = os.path.basename(folder)
            print(f"  - {folder_name}")
        
        # Verify tmp folder is not included
        tmp_included = any("tmp" in os.path.basename(folder).lower() for folder in patient_folders)
        
        if tmp_included:
            print("\n❌ FAILURE: tmp folder was included in patient folders!")
        else:
            print("\n✅ SUCCESS: tmp folder was properly excluded from patient folders!")
        
        # Test FileAnalyzer file scanning
        print(f"\nTesting file scanning within patient folders...")
        analyzer = FileAnalyzer()
        
        for patient_folder in patient_folders:
            patient_name = os.path.basename(patient_folder)
            print(f"\nScanning {patient_name}:")
            
            # Get files using the internal method
            files = analyzer._get_files_in_folder(patient_folder)
            
            print(f"  Found {len(files)} files:")
            for file_path in files:
                rel_path = os.path.relpath(file_path, patient_folder)
                print(f"    - {rel_path}")
            
            # Check if any tmp files were included
            tmp_files = [f for f in files if "tmp" in f.lower()]
            if tmp_files:
                print(f"  ❌ FAILURE: tmp files were included: {tmp_files}")
            else:
                print(f"  ✅ SUCCESS: no tmp files included")

if __name__ == "__main__":
    test_tmp_folder_exclusion()