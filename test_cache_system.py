#!/usr/bin/env python3
"""
Test the patient matching cache system.
"""

import sys
import os
import tempfile
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.file_analyzer import FileAnalyzer
from core.models import PatientData, FileData, DataType, MatchStatus

def test_cache_system():
    """Test the cache system with sample data."""
    print("🧪 TESTING PATIENT MATCHING CACHE SYSTEM")
    print("=" * 60)
    
    # Test with patient 5 folder that we know exists
    patient_folder = r"F:\Dati Ferrara - Test Bulk Upload\ESEMPI\5"
    
    if not os.path.exists(patient_folder):
        print(f"❌ Test folder not found: {patient_folder}")
        print("Please adjust the path to an existing patient folder")
        return
    
    # Initialize analyzer
    analyzer = FileAnalyzer()
    
    print("📊 Cache statistics before analysis:")
    stats = analyzer.get_cache_stats()
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Total matched files: {stats['total_matched_files']}")
    print(f"  Cache size: {stats['cache_size_bytes'] / 1024:.1f} KB")
    
    print(f"\n🔍 First analysis (should create cache)...")
    start_time = time.time()
    patient_data_1 = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
    first_analysis_time = time.time() - start_time
    print(f"  ⏱️  Analysis time: {first_analysis_time:.2f} seconds")
    print(f"  📄 Total files: {len(patient_data_1.get_all_files())}")
    print(f"  ✅ Matched files: {len(patient_data_1.get_all_files()) - len(patient_data_1.unmatched_files)}")
    print(f"  ❓ Unmatched files: {len(patient_data_1.unmatched_files)}")
    
    print(f"\n🔍 Second analysis (should use cache)...")
    start_time = time.time()
    patient_data_2 = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
    second_analysis_time = time.time() - start_time
    print(f"  ⏱️  Analysis time: {second_analysis_time:.2f} seconds")
    print(f"  📄 Total files: {len(patient_data_2.get_all_files())}")
    print(f"  ✅ Matched files: {len(patient_data_2.get_all_files()) - len(patient_data_2.unmatched_files)}")
    print(f"  ❓ Unmatched files: {len(patient_data_2.unmatched_files)}")
    
    # Check if cache made it faster
    if second_analysis_time < first_analysis_time:
        speedup = first_analysis_time / second_analysis_time
        print(f"  🚀 Cache speedup: {speedup:.1f}x faster")
    else:
        print(f"  ⚠️  No speedup detected (cache might not be working)")
    
    print(f"\n🔄 Testing manual assignment simulation...")
    # Simulate manual assignment
    if patient_data_2.unmatched_files:
        test_file = patient_data_2.unmatched_files[0]
        original_status = test_file.status
        original_type = test_file.data_type
        
        # Manually assign file
        test_file.data_type = DataType.INTRAORAL_PHOTO
        test_file.status = MatchStatus.MATCHED
        test_file.confidence = 0.95  # High confidence for manual assignment
        
        # Move from unmatched to matched
        patient_data_2.unmatched_files.remove(test_file)
        patient_data_2.intraoral_photos.append(test_file)
        
        print(f"  📝 Assigned '{test_file.filename}' to Intraoral Photo")
        
        # Update cache
        analyzer.update_cache(patient_data_2)
        print(f"  💾 Updated cache with manual assignment")
        
        # Test cache with manual assignment
        print(f"\n🔍 Third analysis (should preserve manual assignment)...")
        patient_data_3 = analyzer.analyze_patient_folder(patient_folder, use_cache=True)
        
        # Check if manual assignment was preserved
        found_assignment = False
        for photo in patient_data_3.intraoral_photos:
            if photo.path == test_file.path:
                found_assignment = True
                print(f"  ✅ Manual assignment preserved: {photo.filename}")
                break
        
        if not found_assignment:
            print(f"  ❌ Manual assignment NOT preserved")
        
    print(f"\n📊 Final cache statistics:")
    stats = analyzer.get_cache_stats()
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Total matched files: {stats['total_matched_files']}")
    print(f"  Total unmatched files: {stats['total_unmatched_files']}")
    print(f"  Cache size: {stats['cache_size_bytes'] / 1024:.1f} KB")
    print(f"  Cache file: {stats['cache_file']}")
    
    print(f"\n🔍 Testing cache invalidation...")
    analyzer.invalidate_cache(patient_folder)
    print(f"  💨 Cache invalidated for patient folder")
    
    # Verify cache was invalidated
    has_cache = analyzer.has_cached_data(patient_folder)
    print(f"  📋 Has cached data: {has_cache}")
    
    print(f"\n✅ Cache system test completed!")

if __name__ == "__main__":
    import time
    test_cache_system()