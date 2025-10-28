"""
Test script to verify that TF4M credentials are properly loaded from settings.
"""

import json
import os
import sys
sys.path.append('.')

from core.api_client import TF4MAPIClient

def test_credential_loading():
    """Test that credentials are properly loaded from settings."""
    
    # Create a test settings file
    test_settings = {
        "api_url": "https://toothfairy4m.ing.unimore.it",
        "username": "test_user",
        "password": "test_password"
    }
    
    settings_file = "test_settings.json"
    with open(settings_file, 'w') as f:
        json.dump(test_settings, f, indent=2)
    
    print("✅ Created test settings file:")
    print(json.dumps(test_settings, indent=2))
    
    # Test loading settings (similar to main window)
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                loaded_settings = json.load(f)
                
        # Create API client and apply settings
        api_client = TF4MAPIClient(loaded_settings["api_url"])
        api_client.set_credentials(loaded_settings["username"], loaded_settings["password"])
        
        print(f"\n✅ API Client initialized:")
        print(f"   Base URL: {api_client.base_url}")
        print(f"   Username: {api_client.username}")
        print(f"   Password: {'*' * len(api_client.password) if api_client.password else 'None'}")
        print(f"   Authenticated: {api_client.is_authenticated}")
        
        # Test that credentials are available for login
        if api_client.username and api_client.password:
            print(f"\n✅ Credentials are properly set and ready for authentication")
        else:
            print(f"\n❌ Credentials are missing!")
            
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
    finally:
        # Clean up test file
        if os.path.exists(settings_file):
            os.remove(settings_file)
            print(f"\n🧹 Cleaned up test settings file")

if __name__ == "__main__":
    print("🧪 Testing TF4M Credential Loading")
    print("=" * 40)
    test_credential_loading()