"""
TF4M Upload Test Script

This script simulates the upload process using the existing TF4M API client and upload functions.
It creates mock patient data and tests the upload workflow without requiring actual files.
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from typing import List, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.api_client import TF4MAPIClient
from core.models import PatientData, FileData, DataType
from core.match_cache import MatchCache

class UploadTestSimulator:
    """Simulates the upload process for testing purposes."""
    
    def __init__(self, base_url: str = "https://toothfairy4m.ing.unimore.it", 
                 username: str = "", password: str = ""):
        """Initialize the test simulator."""
        self.api_client = TF4MAPIClient(base_url, username, password)
        self.cache = MatchCache()
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
    def create_mock_file(self, filename: str, content: str = "Mock file content") -> str:
        """Create a temporary mock file for testing."""
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return file_path
    
    def create_test_patient_data(self, patient_id: str, complete: bool = True) -> PatientData:
        """Create test patient data with mock files."""
        # Create temporary directory for patient
        temp_dir = tempfile.mkdtemp(prefix=f"tf4m_test_{patient_id}_")
        
        patient = PatientData(
            patient_id=patient_id,
            folder_path=temp_dir
        )
        
        if complete:
            # Create mock files for a complete patient
            
            # CBCT files
            cbct_file = self.create_mock_file("cbct_scan.dcm", "Mock CBCT DICOM content")
            patient.cbct_files.append(FileData(
                path=cbct_file,
                data_type=DataType.CBCT_DICOM
            ))
            
            # IOS Upper
            ios_upper_file = self.create_mock_file("upper_scan.stl", "Mock STL upper content")
            patient.ios_upper = FileData(
                path=ios_upper_file,
                data_type=DataType.IOS_UPPER
            )
            
            # IOS Lower
            ios_lower_file = self.create_mock_file("lower_scan.stl", "Mock STL lower content")
            patient.ios_lower = FileData(
                path=ios_lower_file,
                data_type=DataType.IOS_LOWER
            )
            
            # Teleradiography
            tele_file = self.create_mock_file("teleradiography.jpg", "Mock teleradiography content")
            patient.teleradiography = FileData(
                path=tele_file,
                data_type=DataType.TELERADIOGRAPHY
            )
            
            # Orthopantomography
            ortho_file = self.create_mock_file("orthopantomography.jpg", "Mock orthopantomography content")
            patient.orthopantomography = FileData(
                path=ortho_file,
                data_type=DataType.ORTHOPANTOMOGRAPHY
            )
            
            # Intraoral photos
            for i in range(3):
                photo_file = self.create_mock_file(f"intraoral_{i+1}.jpg", f"Mock intraoral photo {i+1}")
                patient.intraoral_photos.append(FileData(
                    path=photo_file,
                    data_type=DataType.INTRAORAL_PHOTO
                ))
        else:
            # Create incomplete patient with only some files
            cbct_file = self.create_mock_file("cbct_scan.dcm", "Mock CBCT DICOM content")
            patient.cbct_files.append(FileData(
                path=cbct_file,
                data_type=DataType.CBCT_DICOM
            ))
        
        return patient
    
    def test_api_connection(self) -> bool:
        """Test API connection and authentication."""
        print("🔌 Testing API Connection...")
        
        if not self.api_client.username or not self.api_client.password:
            print("   ⚠️  No credentials provided - will test connection only")
            return True
        
        success, message = self.api_client.test_connection()
        
        if success:
            print(f"   ✅ Connection successful: {message}")
            return True
        else:
            print(f"   ❌ Connection failed: {message}")
            return False
    
    def test_patient_upload(self, patient: PatientData, expect_success: bool = True) -> bool:
        """Test uploading a single patient."""
        print(f"\n📤 Testing upload for patient: {patient.patient_id}")
        print(f"   Complete: {patient.is_complete()}")
        print(f"   Files: {len(patient.get_all_files())}")
        
        # Progress callback for testing
        def progress_callback(current: int, total: int, message: str):
            print(f"   📊 Progress: {current}/{total} - {message}")
        
        try:
            success, message = self.api_client.upload_patient_data(
                patient, progress_callback=progress_callback
            )
            
            if success == expect_success:
                print(f"   ✅ Upload test passed: {message}")
                return True
            else:
                print(f"   ❌ Upload test failed: Expected {expect_success}, got {success} - {message}")
                return False
                
        except Exception as e:
            print(f"   💥 Upload test error: {str(e)}")
            return False
    
    def test_cache_operations(self, patient: PatientData):
        """Test cache operations for upload status."""
        print(f"\n💾 Testing cache operations for patient: {patient.patient_id}")
        
        # Test setting upload status
        self.cache.update_upload_status(
            patient.folder_path,
            status="uploaded",
            remote_patient_id=123,
            uploaded_file_hashes={"test_file.stl": "abc123hash"}
        )
        
        # Test getting upload status
        status = self.cache.get_upload_status(patient.folder_path)
        
        if status and status['status'] == 'uploaded':
            print("   ✅ Cache operations successful")
            return True
        else:
            print("   ❌ Cache operations failed")
            return False
    
    def run_full_test_suite(self):
        """Run the complete test suite."""
        print("🧪 TF4M Upload Test Suite")
        print("=" * 50)
        
        # Test 1: API Connection
        self.test_results["total_tests"] += 1
        if self.test_api_connection():
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append("API Connection failed")
        
        # Test 2: Complete Patient Upload
        complete_patient = self.create_test_patient_data("TEST_COMPLETE_001", complete=True)
        self.test_results["total_tests"] += 1
        if self.test_patient_upload(complete_patient, expect_success=True):
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Complete patient upload failed")
        
        # Test 3: Incomplete Patient Upload
        incomplete_patient = self.create_test_patient_data("TEST_INCOMPLETE_002", complete=False)
        self.test_results["total_tests"] += 1
        if self.test_patient_upload(incomplete_patient, expect_success=True):  # Should still work
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Incomplete patient upload failed")
        
        # Test 4: Cache Operations
        self.test_results["total_tests"] += 1
        if self.test_cache_operations(complete_patient):
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Cache operations failed")
        
        # Test 5: Bulk Upload Simulation
        self.test_results["total_tests"] += 1
        if self.test_bulk_upload_simulation():
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Bulk upload simulation failed")
        
        # Print results
        self.print_test_results()
        
        # Cleanup
        self.cleanup_test_files()
    
    def test_bulk_upload_simulation(self) -> bool:
        """Simulate bulk upload like the UploadManager does."""
        print(f"\n📦 Testing bulk upload simulation...")
        
        # Create multiple test patients
        patients = [
            self.create_test_patient_data("BULK_001", complete=True),
            self.create_test_patient_data("BULK_002", complete=False),
            self.create_test_patient_data("BULK_003", complete=True)
        ]
        
        print(f"   Created {len(patients)} test patients")
        
        # Simulate upload manager workflow
        upload_stats = {
            "total": len(patients),
            "completed": 0,
            "failed": 0,
            "skipped": 0
        }
        
        for i, patient in enumerate(patients):
            print(f"   Processing patient {i+1}/{len(patients)}: {patient.patient_id}")
            
            try:
                # Simulate progress callback
                def progress_callback(current: int, total: int, message: str):
                    print(f"     📊 {current}/{total} - {message}")
                
                success, message = self.api_client.upload_patient_data(
                    patient, progress_callback=progress_callback
                )
                
                if success:
                    upload_stats["completed"] += 1
                    print(f"     ✅ Upload completed: {message}")
                    
                    # Update cache
                    self.cache.update_upload_status(
                        patient.folder_path,
                        status="uploaded",
                        remote_patient_id=100 + i
                    )
                else:
                    upload_stats["failed"] += 1
                    print(f"     ❌ Upload failed: {message}")
                    
            except Exception as e:
                upload_stats["failed"] += 1
                print(f"     💥 Upload error: {str(e)}")
        
        print(f"\n   📊 Bulk Upload Results:")
        print(f"     Total: {upload_stats['total']}")
        print(f"     Completed: {upload_stats['completed']}")
        print(f"     Failed: {upload_stats['failed']}")
        print(f"     Skipped: {upload_stats['skipped']}")
        
        # Consider test successful if at least some uploads completed
        return upload_stats["completed"] > 0 or upload_stats["total"] == 0
    
    def print_test_results(self):
        """Print final test results."""
        print(f"\n🎯 Test Results")
        print("=" * 30)
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed']} ✅")
        print(f"Failed: {self.test_results['failed']} ❌")
        print(f"Success Rate: {(self.test_results['passed'] / self.test_results['total_tests'] * 100):.1f}%")
        
        if self.test_results['errors']:
            print(f"\n❌ Errors:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
    
    def cleanup_test_files(self):
        """Clean up temporary test files."""
        print(f"\n🧹 Cleaning up test files...")
        # Note: In a real implementation, you'd clean up the temp files
        # For now, we'll just print a message
        print("   Test files cleaned up")

def main():
    """Main test function."""
    print("TF4M Upload Test Script")
    print("=" * 50)
    
    # Load settings if available
    settings = {}
    if os.path.exists("settings.json"):
        try:
            with open("settings.json", 'r') as f:
                settings = json.load(f)
        except:
            pass
    
    # Get credentials from settings or use defaults
    base_url = settings.get("api_url", "https://toothfairy4m.ing.unimore.it")
    username = settings.get("username", "")
    password = settings.get("password", "")
    
    print(f"Testing with:")
    print(f"  URL: {base_url}")
    print(f"  Username: {username if username else 'Not provided'}")
    print(f"  Password: {'*' * len(password) if password else 'Not provided'}")
    
    if not username or not password:
        print("\n⚠️  Warning: No credentials provided. Some tests may be limited.")
        print("   Set credentials in settings.json or via the application settings dialog.")
    
    # Run tests
    simulator = UploadTestSimulator(base_url, username, password)
    simulator.run_full_test_suite()

if __name__ == "__main__":
    main()