"""
Example of how to set TF4M credentials programmatically.
This shows the settings structure and values.
"""

# Example settings.json structure that gets created:
example_settings = {
    "tf4m_api": {
        "base_url": "https://toothfairy4m.ing.unimore.it",
        "username": "your_username",  # Replace with your actual username
        "password": "your_password"   # Replace with your actual password
    },
    "analysis": {
        "timeout_seconds": 300,
        "max_file_size_mb": 100,
        "enable_smart_matching": True
    }
}

print("TF4M Settings Configuration:")
print("=" * 40)
print("\n📍 Settings Location:")
print("   File → Settings... (Menu)")
print("   or ⚙️ Settings (Toolbar Button)")

print("\n🔧 Required Credentials:")
print("   Server URL: https://toothfairy4m.ing.unimore.it")
print("   Username:   [Your TF4M Username]")
print("   Password:   [Your TF4M Password]")

print("\n💾 Settings are saved to: settings.json")
print("\n🧪 Test Connection:")
print("   After entering credentials, click 'Test Connection'")
print("   This will verify your credentials work with the TF4M server")

print("\n📋 Settings File Example:")
import json
print(json.dumps(example_settings, indent=2))