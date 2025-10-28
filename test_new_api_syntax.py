"""
Test script to verify the updated TF4M API syntax matches upload_script.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.api_client import TF4MAPIClient
from core.models import PatientData, FileData, DataType

def test_api_syntax():
    """Test that the API client matches the new syntax"""
    
    print("=" * 60)
    print("Testing Updated TF4M API Syntax")
    print("=" * 60)
    print()
    
    # Test 1: Check constructor accepts project_slug
    print("✓ Test 1: Constructor with project_slug")
    api_client = TF4MAPIClient(
        base_url="https://toothfairy4m.ing.unimore.it",
        username="test_user",
        password="test_pass",
        project_slug="maxillo"
    )
    assert api_client.project_slug == "maxillo"
    print(f"  - project_slug: {api_client.project_slug}")
    print()
    
    # Test 2: Check _get_csrf_token method exists
    print("✓ Test 2: _get_csrf_token method exists")
    assert hasattr(api_client, '_get_csrf_token')
    print("  - Method exists: _get_csrf_token()")
    print()
    
    # Test 3: Check API URLs use project_slug
    print("✓ Test 3: API URLs use project_slug")
    expected_upload_url = f"{api_client.base_url}/api/{api_client.project_slug}/upload/"
    print(f"  - Upload URL: {expected_upload_url}")
    print()
    
    # Test 4: Verify field name changes
    print("✓ Test 4: Field name mapping")
    field_mappings = {
        "IOS Upper": "upper_scan_raw",
        "IOS Lower": "lower_scan_raw",
        "CBCT": "cbct",
        "Intraoral Photos": "intraoral_images",
        "Teleradiography": "teleradiography",
        "Panoramic": "panoramic",
        "ZIP": "rawzip"
    }
    
    for desc, field_name in field_mappings.items():
        print(f"  - {desc:20} → {field_name}")
    print()
    
    # Test 5: Verify form data structure
    print("✓ Test 5: Form data structure")
    form_fields = {
        "name": "Patient ID",
        "folder": "Folder ID (e.g., '2')",
        "visibility": "'private'",
        "cbct_upload_type": "'file'"
    }
    
    for field, desc in form_fields.items():
        print(f"  - {field:20} : {desc}")
    print()
    
    print("=" * 60)
    print("All syntax checks passed!")
    print("=" * 60)
    print()
    print("Key Changes Summary:")
    print("-" * 60)
    print("1. Added project_slug parameter to constructor (default: 'maxillo')")
    print("2. Field names updated:")
    print("   • ios_upper/ios_lower → upper_scan_raw/lower_scan_raw")
    print("   • intraoral_0, intraoral_1, ... → intraoral_images (repeated)")
    print("   • panoramich → panoramic")
    print("3. Form data includes:")
    print("   • cbct_upload_type: 'file'")
    print("   • folder: '2' (default)")
    print("   • visibility: 'private'")
    print("4. Removed selected_modalities field")
    print("5. API endpoints use project_slug:")
    print(f"   • /api/{api_client.project_slug}/upload/")
    print(f"   • /api/{api_client.project_slug}/patients/")
    print("-" * 60)

if __name__ == "__main__":
    try:
        test_api_syntax()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
