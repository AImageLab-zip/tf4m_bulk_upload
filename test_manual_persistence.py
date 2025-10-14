#!/usr/bin/env python3
"""
Test manual assignment persistence in cache file.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.append(r'C:\Users\Federico\Desktop\Desktop App TF4M')

from core.file_analyzer import FileAnalyzer
from core.project_manager import ProjectManager
from core.models import ProjectData, PatientData, FileData, DataType, MatchStatus

def test_manual_assignment_persistence():
    """Test that manual assignments are immediately saved to cache."""
    print("Testing Manual Assignment Cache Persistence")
    print("="*50)
    
    # Test with a real patient folder
    patient_folder = r"F:\Dati Ferrara - Test Bulk Upload\ESEMPI\1"
    
    if not os.path.exists(patient_folder):
        print(f"Test folder not found: {patient_folder}")
        return
    
    print(f"Testing with: {patient_folder}")
    
    # Initialize components
    analyzer = FileAnalyzer()
    project_manager = ProjectManager()
    
    # Get cache file path
    cache_file = analyzer.match_cache.get_patient_cache_file(patient_folder)
    print(f"Cache file: {cache_file}")
    
    # Clear cache and analyze
    analyzer.invalidate_cache(patient_folder)
    
    # Set up project data for project manager
    project_manager.project_data = ProjectData(root_path=os.path.dirname(patient_folder))
    
    # Analyze patient folder
    patient_data = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
    
    # Add patient to project manager
    project_manager.project_data.patients = [patient_data]
    
    print(f"\nInitial state:")
    print(f"  Patient: {patient_data.patient_id}")
    print(f"  Total files: {len(patient_data.get_all_files())}")
    print(f"  Unmatched files: {len(patient_data.unmatched_files)}")
    
    if not patient_data.unmatched_files:
        print("No unmatched files to test manual assignment")
        return
    
    # Pick first unmatched file for manual assignment
    test_file = patient_data.unmatched_files[0]
    original_path = test_file.path
    print(f"  Test file: {test_file.filename}")
    
    # Read cache before manual assignment
    cache_before = None
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_before = json.load(f)
    
    # Perform manual assignment
    print(f"\nPerforming manual assignment...")
    success = project_manager.update_patient_file_assignment(
        patient_data.patient_id,
        original_path,
        DataType.INTRAORAL_PHOTO
    )
    
    if success:
        print(f"Manual assignment successful")
        
        # Update cache (this should happen automatically in GUI)
        analyzer.update_cache(patient_data)
        print(f"Cache updated")
        
        # Read cache after manual assignment
        cache_after = None
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_after = json.load(f)
            
            print(f"\nCache file analysis:")
            print(f"  Cache file exists: True")
            print(f"  Cache file size: {os.path.getsize(cache_file):,} bytes")
            
            # Check for manual assignments in cache
            cache_key = list(cache_after.keys())[0]
            matched_files = cache_after[cache_key].get('matched_files', {})
            manual_assignments = cache_after[cache_key].get('manual_assignments', {})
            
            print(f"  Total matched files in cache: {len(matched_files)}")
            print(f"  Manual assignments in cache: {len(manual_assignments)}")
            
            # Check if our manual assignment is recorded
            manual_found = False
            for file_path, file_info in matched_files.items():
                if file_path == original_path:
                    status = file_info.get('status', 'unknown')
                    data_type = file_info.get('data_type', 'unknown')
                    print(f"  Found test file in cache:")
                    print(f"    Status: {status}")
                    print(f"    Type: {data_type}")
                    
                    if status == 'manual':
                        print(f"    SUCCESS: Manual status recorded in cache!")
                        manual_found = True
                    break
            
            if not manual_found:
                print(f"  ISSUE: Manual assignment not found in cache")
                
            # Check manual_assignments section
            if original_path in manual_assignments:
                assigned_type = manual_assignments[original_path]
                print(f"  Manual assignment recorded: {assigned_type}")
            else:
                print(f"  No entry in manual_assignments section")
        
        else:
            print(f"FAILURE: Cache file not found after update")
            
        # Test persistence by reloading
        print(f"\nTesting persistence by reloading...")
        patient_data_2 = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
        
        # Check if manual assignment persisted
        manual_persisted = False
        for file_data in patient_data_2.get_all_files():
            if file_data.path == original_path:
                print(f"  Reloaded file: {file_data.filename}")
                print(f"  Status: {file_data.status.value}")
                print(f"  Type: {file_data.data_type.value if file_data.data_type else 'None'}")
                
                if file_data.status == MatchStatus.MANUAL:
                    print(f"  SUCCESS: Manual assignment persisted!")
                    manual_persisted = True
                break
        
        if not manual_persisted:
            print(f"  FAILURE: Manual assignment not persisted")
            
    else:
        print(f"Manual assignment failed")

if __name__ == "__main__":
    test_manual_assignment_persistence()