#!/usr/bin/env python3
"""
Diagnostic test for cache functionality.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(r'C:\Users\Federico\Desktop\Desktop App TF4M')

from core.file_analyzer import FileAnalyzer
from core.project_manager import ProjectManager
from core.models import DataType, MatchStatus

def test_cache_diagnostic():
    """Comprehensive cache diagnostic."""
    print("Cache Diagnostic Test")
    print("=" * 40)
    
    # Test with a real patient folder
    patient_folder = r"F:\Dati Ferrara - Test Bulk Upload\ESEMPI\1"
    
    if not os.path.exists(patient_folder):
        print(f"❌ Test folder not found: {patient_folder}")
        print("Available folders:")
        base_folder = r"F:\Dati Ferrara - Test Bulk Upload\ESEMPI"
        if os.path.exists(base_folder):
            for item in os.listdir(base_folder):
                item_path = os.path.join(base_folder, item)
                if os.path.isdir(item_path):
                    print(f"  - {item}")
        return
    
    print(f"Testing with folder: {patient_folder}")
    
    # Initialize components
    analyzer = FileAnalyzer()
    project_manager = ProjectManager()
    
    # Step 1: Check cache mode
    print(f"\n1. Cache Configuration:")
    print(f"   Mode: {'centralized' if analyzer.match_cache.centralized_cache else 'distributed'}")
    
    # Step 2: Clear existing cache
    print(f"\n2. Clearing existing cache...")
    analyzer.invalidate_cache(patient_folder)
    
    cache_file = analyzer.match_cache.get_patient_cache_file(patient_folder)
    print(f"   Expected cache file: {cache_file}")
    print(f"   Cache file exists: {os.path.exists(cache_file)}")
    
    # Step 3: Initial analysis
    print(f"\n3. Initial analysis...")
    patient_data = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
    
    print(f"   Patient ID: {patient_data.patient_id}")
    print(f"   Total files: {len(patient_data.get_all_files())}")
    print(f"   Unmatched files: {len(patient_data.unmatched_files)}")
    
    # Step 4: Check if cache was created
    print(f"\n4. Cache creation check...")
    print(f"   Cache file exists: {os.path.exists(cache_file)}")
    if os.path.exists(cache_file):
        file_size = os.path.getsize(cache_file)
        print(f"   Cache file size: {file_size} bytes")
        
        if file_size > 0:
            print("   ✅ Cache file has content")
        else:
            print("   ❌ Cache file is empty")
    
    # Step 5: Test manual assignment
    if patient_data.unmatched_files:
        print(f"\n5. Testing manual assignment...")
        test_file = patient_data.unmatched_files[0]
        original_path = test_file.path
        print(f"   Original file: {test_file.filename}")
        print(f"   Original status: {test_file.status.value}")
        
        # Manually assign file
        success = project_manager.update_patient_file_assignment(
            patient_data.patient_id,
            original_path,
            DataType.INTRAORAL_PHOTO
        )
        
        if success:
            print("   ✅ Manual assignment successful")
            
            # Update cache
            analyzer.update_cache(patient_data)
            print("   ✅ Cache update called")
            
            # Check cache file again
            if os.path.exists(cache_file):
                file_size = os.path.getsize(cache_file)
                print(f"   Cache file size after update: {file_size} bytes")
            
            # Test if manual assignment is preserved by reloading
            print(f"\n6. Testing cache persistence...")
            patient_data_2 = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
            
            # Look for the manually assigned file
            manual_found = False
            for file_data in patient_data_2.get_all_files():
                if file_data.path == original_path:
                    print(f"   Found file: {file_data.filename}")
                    print(f"   Status: {file_data.status.value}")
                    print(f"   Data type: {file_data.data_type.value if file_data.data_type else 'None'}")
                    
                    if file_data.status == MatchStatus.MANUAL:
                        print("   ✅ Manual status preserved!")
                        manual_found = True
                    else:
                        print("   ❌ Manual status NOT preserved")
                    break
            
            if not manual_found:
                print("   ❌ Manually assigned file not found")
        else:
            print("   ❌ Manual assignment failed")
    else:
        print(f"\n5. No unmatched files to test manual assignment")
    
    print(f"\nDiagnostic test completed!")

if __name__ == "__main__":
    test_cache_diagnostic()