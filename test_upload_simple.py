"""
Simple TF4M Upload Test

A focused test script that demonstrates the upload workflow step by step.
"""

import os
import sys
import json
import tempfile
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.api_client import TF4MAPIClient
from core.models import PatientData, FileData, DataType

def create_test_patient() -> PatientData:
    """Create a test patient with mock files."""
    print("📋 Creating test patient data...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="tf4m_test_")
    
    # Create mock files
    def create_mock_file(filename: str, content: str = "Mock content") -> str:
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content + f" - Created at {datetime.now()}")
        return file_path
    
    # Create patient
    patient = PatientData(
        patient_id="TEST_PATIENT_001",
        folder_path=temp_dir
    )
    
    # Add files
    patient.ios_upper = FileData(
        path=create_mock_file("upper.stl"),
        data_type=DataType.IOS_UPPER
    )
    
    patient.ios_lower = FileData(
        path=create_mock_file("lower.stl"),
        data_type=DataType.IOS_LOWER
    )
    
    patient.teleradiography = FileData(
        path=create_mock_file("teleradiography.jpg"),
        data_type=DataType.TELERADIOGRAPHY
    )
    
    print(f"   ✅ Created patient '{patient.patient_id}' with {len(patient.get_all_files())} files")
    print(f"   📁 Files: {[f.filename for f in patient.get_all_files()]}")
    
    return patient

def test_upload_workflow():
    """Test the complete upload workflow."""
    print("🧪 TF4M Upload Workflow Test")
    print("=" * 40)
    
    # Load settings
    print("\n1️⃣ Loading settings...")
    settings = {}
    if os.path.exists("settings.json"):
        try:
            with open("settings.json", 'r') as f:
                settings = json.load(f)
            print("   ✅ Settings loaded from settings.json")
        except Exception as e:
            print(f"   ⚠️  Failed to load settings: {e}")
    else:
        print("   ⚠️  No settings.json found, using defaults")
    
    # Initialize API client
    print("\n2️⃣ Initializing API client...")
    base_url = settings.get("api_url", "http://pdor.ing.unimore.it:8080")
    username = settings.get("username", "")
    password = settings.get("password", "")
    
    api_client = TF4MAPIClient(base_url, username, password)
    
    print(f"   🌐 Base URL: {base_url}")
    print(f"   👤 Username: {username if username else 'Not set'}")
    print(f"   🔒 Password: {'Set' if password else 'Not set'}")
    
    # Test connection
    print("\n3️⃣ Testing connection...")
    if username and password:
        success, message = api_client.test_connection()
        if success:
            print(f"   ✅ Connection successful: {message}")
        else:
            print(f"   ❌ Connection failed: {message}")
            print("   ⚠️  Upload test will continue but may fail")
    else:
        print("   ⚠️  No credentials provided, skipping connection test")
    
    # Create test patient
    print("\n4️⃣ Creating test patient...")
    patient = create_test_patient()
    
    # Test upload
    print("\n5️⃣ Testing upload...")
    
    def progress_callback(current: int, total: int, message: str):
        percentage = (current / total * 100) if total > 0 else 0
        print(f"   📊 Progress: {current}/{total} ({percentage:.1f}%) - {message}")
    
    try:
        print("   🚀 Starting upload...")
        success, message = api_client.upload_patient_data(
            patient, 
            progress_callback=progress_callback
        )
        
        if success:
            print(f"   ✅ Upload successful: {message}")
        else:
            print(f"   ❌ Upload failed: {message}")
            
    except Exception as e:
        print(f"   💥 Upload error: {str(e)}")
        import traceback
        print(f"   📄 Traceback:")
        traceback.print_exc()
    
    # Test patient lookup
    print("\n6️⃣ Testing patient lookup...")
    try:
        found, patient_info, lookup_message = api_client.find_patient_by_name(patient.patient_id)
        if found:
            print(f"   ✅ Patient found: {patient_info}")
        else:
            print(f"   ❌ Patient not found: {lookup_message}")
    except Exception as e:
        print(f"   💥 Lookup error: {str(e)}")
    
    # Test getting all patients
    print("\n7️⃣ Testing patient list...")
    try:
        success, patients, list_message = api_client.get_patients()
        if success:
            print(f"   ✅ Retrieved {len(patients)} patients from server")
            for patient_info in patients[:3]:  # Show first 3
                print(f"     • {patient_info.get('name', 'Unknown')} (ID: {patient_info.get('patient_id', 'Unknown')})")
            if len(patients) > 3:
                print(f"     ... and {len(patients) - 3} more")
        else:
            print(f"   ❌ Failed to get patient list: {list_message}")
    except Exception as e:
        print(f"   💥 Patient list error: {str(e)}")
    
    print("\n🎯 Upload workflow test completed!")
    print("\n📝 Next steps:")
    print("   1. Check the TF4M server to verify the patient was created")
    print("   2. Verify that files were uploaded correctly")
    print("   3. Test with different patient configurations")

def show_upload_request_example():
    """Show what an actual upload request looks like."""
    print("\n📡 Example Upload Request Structure")
    print("=" * 40)
    
    example_request = {
        "method": "POST",
        "url": "http://pdor.ing.unimore.it:8080/upload/",
        "headers": {
            "Content-Type": "multipart/form-data",
            "Cookie": "csrftoken=...; sessionid=..."
        },
        "form_data": {
            "name": "TEST_PATIENT_001",
            "visibility": "private",
            "csrfmiddlewaretoken": "csrf_token_value"
        },
        "files": {
            "upper_scan_raw": "upper.stl (binary data)",
            "lower_scan_raw": "lower.stl (binary data)",
            "cbct": "cbct_scan.dcm (binary data)",
            "cbct_upload_type": "file"
        }
    }
    
    print("Request structure:")
    import json
    print(json.dumps(example_request, indent=2))
    
    print("\n🔄 Upload Process Flow:")
    print("1. Login to TF4M with credentials")
    print("2. Get CSRF token from login page")
    print("3. Check if patient exists on server")
    print("4. If patient exists:")
    print("   - Get existing files and compare hashes")
    print("   - Upload only new/changed files")
    print("5. If patient doesn't exist:")
    print("   - Create new patient with initial files")
    print("   - Upload remaining files")
    print("6. Update local cache with upload status")

if __name__ == "__main__":
    test_upload_workflow()
    show_upload_request_example()