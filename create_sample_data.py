#!/usr/bin/env python3
"""
Create sample test data for the dental application.
"""

import os
import json
from datetime import datetime

def create_sample_data():
    """Create sample patient data structure."""
    
    # Create test data directory
    test_data_dir = "sample_test_data"
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)
    
    # Sample patients
    patients = [
        "Patient_001_John_Doe",
        "Patient_002_Jane_Smith", 
        "Patient_003_Mike_Johnson"
    ]
    
    for patient in patients:
        patient_dir = os.path.join(test_data_dir, patient)
        os.makedirs(patient_dir, exist_ok=True)
        
        # Create CBCT folder with mock DICOM files
        cbct_dir = os.path.join(patient_dir, "CBCT")
        os.makedirs(cbct_dir, exist_ok=True)
        
        for i in range(3):
            dicom_file = os.path.join(cbct_dir, f"CT_{i+1:03d}.dcm")
            with open(dicom_file, 'w') as f:
                f.write(f"Mock DICOM file for {patient} - slice {i+1}")
        
        # Create IOS folder with STL files
        ios_dir = os.path.join(patient_dir, "scansioni")
        os.makedirs(ios_dir, exist_ok=True)
        
        upper_file = os.path.join(ios_dir, f"{patient}_upper_scan.stl")
        lower_file = os.path.join(ios_dir, f"{patient}_lower_scan.stl")
        
        with open(upper_file, 'w') as f:
            f.write(f"Mock STL file - upper jaw for {patient}")
            
        with open(lower_file, 'w') as f:
            f.write(f"Mock STL file - lower jaw for {patient}")
        
        # Create sample photos
        for i in range(5):
            photo_file = os.path.join(patient_dir, f"intraoral_photo_{i+1}.jpg")
            with open(photo_file, 'w') as f:
                f.write(f"Mock intraoral photo {i+1} for {patient}")
        
        # Create teleradiography
        tele_file = os.path.join(patient_dir, "teleradiography_lateral.jpg")
        with open(tele_file, 'w') as f:
            f.write(f"Mock teleradiography for {patient}")
        
        # Create orthopantomography
        ortho_file = os.path.join(patient_dir, "orthopantomography.jpg")
        with open(ortho_file, 'w') as f:
            f.write(f"Mock orthopantomography for {patient}")
        
        print(f"Created sample data for {patient}")
    
    # Create a summary file
    summary = {
        "created": datetime.now().isoformat(),
        "patients": patients,
        "description": "Sample test data for dental application",
        "structure": {
            "patient_folder": {
                "CBCT/": "Contains DICOM files",
                "scansioni/": "Contains STL files (upper and lower)",
                "*.jpg": "Intraoral photos and radiographs"
            }
        }
    }
    
    with open(os.path.join(test_data_dir, "README.json"), 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSample data created in '{test_data_dir}' directory")
    print("You can use this directory to test the application")

if __name__ == "__main__":
    create_sample_data()
