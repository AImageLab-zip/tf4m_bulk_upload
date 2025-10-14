import requests
import json
import os
from pathlib import Path

BASE_URL = "http://pdor.ing.unimore.it:8080"
PROJECT_SLUG = "maxillo"

USERNAME = "llumetti"
PASSWORD = "password"

FILES_CONFIG = {
    "upper_scan_raw": r"E:\ToothFairy4M\Dataset_Progetto_AI\IOS\Progetto AI\Bits2Bites\1\upper.stl",
    "lower_scan_raw": r"E:\ToothFairy4M\Dataset_Progetto_AI\IOS\Progetto AI\Bits2Bites\1\lower.stl",
    
    "cbct": r"E:\ToothFairy4M\Dataset_Progetto_AI\CBCT\niigz\1.nii.gz",
    
    "teleradiography": r"C:\Users\Luca\Pictures\licensed-image.jpg",
    "panoramic": r"C:\Users\Luca\Pictures\licensed-image.jpg",
    
    "intraoral_photos": [
        r"C:\Users\Luca\Pictures\licensed-image.jpg",
        r"C:\Users\Luca\Pictures\licensed-image.jpg", 
        r"C:\Users\Luca\Pictures\licensed-image.jpg",
        r"C:\Users\Luca\Pictures\licensed-image.jpg",
        r"C:\Users\Luca\Pictures\licensed-image.jpg"
    ],
    
    "rawzip": r"C:\Users\Luca\Downloads\download_2025-10-08_09-13-32.zip"
}


def login(username, password):
    """Login and get session cookies or token"""
    login_url = f"{BASE_URL}/login/"
    session = requests.Session()
    
    try:
        response = session.get(login_url)
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        else:
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
            else:
                print("Could not find CSRF token")
                return None
    except Exception as e:
        print(f"Error getting login page: {e}")
        return None
    
    login_data = {
        'username': username,
        'password': password,
        'csrfmiddlewaretoken': csrf_token
    }
    
    headers = {
        'Referer': login_url,
        'X-CSRFToken': csrf_token
    }
    
    try:
        response = session.post(login_url, data=login_data, headers=headers, allow_redirects=False)
        
        if response.status_code in [200, 302]:
            print("Login successful!")
            return session
        else:
            print(f"Login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None

def check_file_exists(file_path):
    """Check if file exists and print info"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"   {os.path.basename(file_path)} ({size:,} bytes)")
        return True
    else:
        print(f"   {file_path} - FILE NOT FOUND")
        return False

def upload_patient(session, folder_id="1"):
    """Upload patient with all modalities"""
    upload_url = f"{BASE_URL}/api/{PROJECT_SLUG}/upload/"
    
    files_to_open = []
    missing_files = []
    
    for field_name, file_path in FILES_CONFIG.items():
        if field_name == "intraoral_photos":
            continue
        if isinstance(file_path, str) and check_file_exists(file_path):
            files_to_open.append((field_name, file_path))
        elif isinstance(file_path, str):
            missing_files.append(file_path)

    # Intraoral photos è una lista di file, quindi va gestita a parte
    for i, file_path in enumerate(FILES_CONFIG['intraoral_photos']):
        if check_file_exists(f"{file_path}"):
            files_to_open.append(("intraoral_photos", file_path))  # Changed to rgb_images
        else:
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n{len(missing_files)} files are missing. Cannot proceed with upload.")
        return False

    print("Files to upload:")
    for field_name, file_path in files_to_open:
        print(f"   - {field_name}: {os.path.basename(file_path)}")
    
    data = {
        "name": "Test Upload Patient",
        "folder": folder_id,
        "visibility": "private",
        "cbct_upload_type": "file",
    }
    
    files = []
    try:
        for field_name, file_path in files_to_open:
            files.append((field_name, open(file_path, "rb")))
        response = session.post(upload_url, data=data, files=files)
        
        print(f"\nUpload completed!")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"Upload successful! Patient ID: {result.get('patient_id')}")
                print(f"\t- Details: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"Upload failed: {result}")
                return False
        else:
            print(f"Upload failed with status {response.status_code}")
            
    except Exception as e:
        print(f"Error during upload: {e}")
        return False
    finally:
        for _, file_handle in files:
            try:
                file_handle.close()
            except:
                pass

def main():
    session = login(USERNAME, PASSWORD)
    if not session:
        print("Login failed. Please check your credentials.")
        return
    success = upload_patient(session, folder_id="1")
    
    if success:
        print("\nUpload completed successfully!")
    else:
        print("\nUpload failed!")

if __name__ == "__main__":
    main()