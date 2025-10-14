#!/usr/bin/env python3
"""
Test manual assignment status and cache persistence.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(r'C:\Users\Federico\Desktop\Desktop App TF4M')

from core.file_analyzer import FileAnalyzer
from core.project_manager import ProjectManager
from core.models import PatientData, FileData, DataType, MatchStatus

def test_manual_assignment_status():
    """Test manual assignment status and cache persistence."""
    print("Testing Manual Assignment Status and Cache Persistence")
    print("=" * 70)
    
    # Test with patient 5 folder that we know exists
    patient_folder = r"F:\Dati Ferrara - Test Bulk Upload\ESEMPI\5"
    
    if not os.path.exists(patient_folder):
        print(f"❌ Test folder not found: {patient_folder}")
        print("Please adjust the path to an existing patient folder")
        return
    
    print(f"Testing with folder: {patient_folder}")
    
    # Initialize components
    analyzer = FileAnalyzer()
    project_manager = ProjectManager()
    
    # Clear cache for clean test
    analyzer.invalidate_cache(patient_folder)
    print("🗑️  Cache cleared for clean test")
    
    # Step 1: Initial analysis
    print(f"\n📋 Step 1: Initial analysis...")
    patient_data = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
    
    print(f"  Patient ID: {patient_data.patient_id}")
    print(f"  Total files: {len(patient_data.get_all_files())}")
    print(f"  Unmatched files: {len(patient_data.unmatched_files)}")
    
    # Find the first unmatched file to test manual assignment
    if not patient_data.unmatched_files:
        print("⚠️  No unmatched files found. Trying to use a matched file for testing...")
        test_file = patient_data.get_all_files()[0] if patient_data.get_all_files() else None
    else:
        test_file = patient_data.unmatched_files[0]
    
    if not test_file:
        print("❌ No files found to test with")
        return
    
    original_filename = test_file.filename
    original_path = test_file.path
    print(f"🎯 Test file: {original_filename}")
    print(f"   Original status: {test_file.status.value}")
    print(f"   Original data type: {test_file.data_type.value if test_file.data_type else 'None'}")
    
    # Step 2: Simulate manual assignment using project manager
    print(f"\n🖱️  Step 2: Simulating manual assignment...")
    new_data_type = DataType.INTRAORAL_PHOTO
    success = project_manager.update_patient_file_assignment(
        patient_data.patient_id,
        original_path,
        new_data_type
    )
    
    if success:
        print(f"✅ Manual assignment successful")
        
        # Find the file again to check its status
        updated_file = None
        for file_data in patient_data.get_all_files():
            if file_data.path == original_path:
                updated_file = file_data
                break
        
        if updated_file:
            print(f"   New status: {updated_file.status.value}")
            print(f"   New data type: {updated_file.data_type.value}")
            print(f"   Confidence: {updated_file.confidence}")
            
            if updated_file.status == MatchStatus.MANUAL:
                print("✅ Status correctly set to MANUAL")
            else:
                print(f"❌ Status not set to MANUAL, got: {updated_file.status.value}")
        else:
            print("❌ Could not find updated file")
    else:
        print("❌ Manual assignment failed")
        return
    
    # Step 3: Update cache with manual assignment
    print(f"\n💾 Step 3: Updating cache...")
    analyzer.update_cache(patient_data)
    print("✅ Cache updated")
    
    # Step 4: Test cache persistence by reloading
    print(f"\n🔄 Step 4: Testing cache persistence...")
    patient_data_2 = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
    
    # Check if manual assignment was preserved
    manual_file = None
    for file_data in patient_data_2.get_all_files():
        if file_data.path == original_path:
            manual_file = file_data
            break
    
    if manual_file:
        print(f"🔍 Checking preserved file: {manual_file.filename}")
        print(f"   Status: {manual_file.status.value}")
        print(f"   Data type: {manual_file.data_type.value}")
        print(f"   Confidence: {manual_file.confidence}")
        
        if manual_file.status == MatchStatus.MANUAL:
            print("✅ SUCCESS: Manual status preserved in cache!")
        else:
            print(f"❌ FAILURE: Manual status NOT preserved, got: {manual_file.status.value}")
            
        if manual_file.data_type == new_data_type:
            print("✅ SUCCESS: Manual data type preserved in cache!")
        else:
            print(f"❌ FAILURE: Manual data type NOT preserved")
    else:
        print("❌ FAILURE: Could not find file after cache reload")
    
    # Step 5: Check cache statistics
    print(f"\n📊 Step 5: Cache statistics...")
    stats = analyzer.get_cache_stats()
    print(f"  Total cached entries: {stats['total_entries']}")
    print(f"  Total matched files: {stats['total_matched_files']}")
    print(f"  Cache size: {stats['cache_size_mb']:.1f} MB")
    
    print(f"\n🎉 Manual assignment test completed!")

if __name__ == "__main__":
    test_manual_assignment_status()