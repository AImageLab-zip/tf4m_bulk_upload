"""
Example upload request demonstration for TF4M integration.
This script shows how the upload process works without actually uploading files.
"""

import os
import sys
import hashlib
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from core.api_client import TF4MAPIClient
from core.models import PatientData, FileData


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file for demonstration."""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"Error calculating hash: {str(e)}"


def print_upload_example():
    """Print example of how upload requests are structured."""
    
    print("="*80)
    print("TF4M UPLOAD REQUEST EXAMPLE")
    print("="*80)
    
    # Example patient data
    print("\n1. PATIENT DATA STRUCTURE:")
    print("-" * 40)
    
    patient_example = {
        "patient_id": "Patient_001",
        "folder_path": "/path/to/patient_001",
        "files": {
            "cbct_files": ["patient_001_cbct.dcm", "patient_001_cbct_2.dcm"],
            "ios_upper": "upper_scan.stl",
            "ios_lower": "lower_scan.stl", 
            "intraoral_photos": ["photo_1.jpg", "photo_2.jpg", "photo_3.jpg"],
            "teleradiography": "tele_xray.jpg",
            "orthopantomography": "panoramic.jpg"
        }
    }
    
    for key, value in patient_example.items():
        print(f"  {key}: {value}")
    
    print("\n2. TF4M API ENDPOINTS:")
    print("-" * 40)
    print("  Base URL: https://toothfairy4m.ing.unimore.it")
    print("  Login: POST /login/")
    print("  Patients List: GET /api/maxillo/patients/")
    print("  Patient Files: GET /api/maxillo/patients/{id}/files/")
    print("  Upload: POST /upload/")
    
    print("\n3. AUTHENTICATION FLOW:")
    print("-" * 40)
    print("  Step 1: GET /login/ (get CSRF token)")
    print("  Step 2: POST /login/ with credentials + CSRF token")
    print("  Step 3: Use session cookies for subsequent requests")
    
    print("\n4. UPLOAD PROCESS FLOW:")
    print("-" * 40)
    print("  Step 1: Check if patient exists via GET /api/maxillo/patients/")
    print("  Step 2: If exists, get current files via GET /api/maxillo/patients/{id}/files/")
    print("  Step 3: Compare local file hashes with remote file hashes")
    print("  Step 4: Upload only new/changed files")
    print("  Step 5: If patient doesn't exist, create new patient with POST /upload/")
    
    print("\n5. EXAMPLE HTTP REQUEST FOR NEW PATIENT:")
    print("-" * 40)
    
    example_request = """
POST /upload/ HTTP/1.1
Host: pdor.ing.unimore.it:8080
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
Cookie: sessionid=abc123...; csrftoken=xyz789...

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="csrfmiddlewaretoken"

xyz789...
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="name"

Patient_001
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="upper_scan_raw"; filename="upper_scan.stl"
Content-Type: model/stl

[STL file binary data...]
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="lower_scan_raw"; filename="lower_scan.stl"
Content-Type: model/stl

[STL file binary data...]
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="cbct"; filename="cbct_scan.nii"
Content-Type: application/octet-stream

[CBCT file binary data...]
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="cbct_upload_type"

file
------WebKitFormBoundary7MA4YWxkTrZu0gW--
"""
    
    print(example_request.strip())
    
    print("\n6. EXPECTED RESPONSE:")
    print("-" * 40)
    print("  Success: HTTP 200/201/302 (redirect)")
    print("  Error: HTTP 4xx/5xx with error message")
    
    print("\n7. FILE HASH COMPARISON EXAMPLE:")
    print("-" * 40)
    
    # Example of file comparison logic
    remote_files_example = [
        {
            "id": 43,
            "filename": "ios_upper_patient_25.stl",
            "file_hash": "5af3c8ff261a027aa90648ee812a493ec49015ae07df5823541f6c17b4b9f6cb",
            "file_type": "cbct_raw",
            "file_size": 8520634
        },
        {
            "id": 44, 
            "filename": "ios_lower_patient_25.stl",
            "file_hash": "a0f54699df85f4593638955d846759f31bde1fca5d9aadbf1b96334300891895",
            "file_type": "cbct_raw",
            "file_size": 8539984
        }
    ]
    
    print("  Remote files from TF4M:")
    for file_info in remote_files_example:
        print(f"    {file_info['filename']}: {file_info['file_hash'][:16]}...")
    
    print("\n  Local file comparison logic:")
    print("    - Calculate SHA256 hash of local file")
    print("    - Compare with remote file hashes")
    print("    - Upload only if hash differs or file is new")
    
    print("\n8. CACHE INTEGRATION:")
    print("-" * 40)
    print("  Cache file: .tf4m_cache.json in each patient folder")
    print("  Stores:")
    print("    - upload_status: 'not_uploaded', 'uploading', 'uploaded', 'failed'")
    print("    - remote_patient_id: TF4M patient ID")
    print("    - last_upload_attempt: timestamp")
    print("    - uploaded_file_hashes: hash map")
    print("    - upload_error_message: error details")


def demonstrate_api_client():
    """Demonstrate API client usage (without actual upload)."""
    
    print("\n" + "="*80)
    print("API CLIENT DEMONSTRATION")
    print("="*80)
    
    # Create API client instance
    api_client = TF4MAPIClient("https://toothfairy4m.ing.unimore.it")
    
    print(f"\n1. API Client initialized:")
    print(f"   Base URL: {api_client.base_url}")
    print(f"   Authenticated: {api_client.is_authenticated}")
    
    print(f"\n2. Authentication would work like this:")
    print(f"   api_client.username = 'your_username'")
    print(f"   api_client.password = 'your_password'")
    print(f"   success, message = api_client.login()")
    
    print(f"\n3. Upload process would be:")
    print(f"   success, message = api_client.upload_patient_data(patient_data, progress_callback)")
    
    print(f"\n4. Progress callback receives:")
    print(f"   current: int (files uploaded so far)")
    print(f"   total: int (total files to upload)")
    print(f"   message: str (current operation description)")


if __name__ == "__main__":
    print_upload_example()
    demonstrate_api_client()
    
    print("\n" + "="*80)
    print("To test actual upload:")
    print("1. Set credentials in Settings dialog")
    print("2. Load a project with patient data")
    print("3. Click 'Upload All' button")
    print("4. Select upload options in dialog")
    print("5. Monitor progress in Upload Manager tab")
    print("="*80)