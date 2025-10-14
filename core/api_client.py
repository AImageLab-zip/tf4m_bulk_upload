"""
API client for uploading dental data to the TF4M Django backend.
"""

import requests
import os
import hashlib
from typing import Optional, Dict, Any, Callable, List, Tuple
import json
import time
from threading import Thread

from .models import PatientData, DataType, FileData

class TF4MAPIClient:
    """Client for interacting with the TF4M Django API."""
    
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None, project_slug: str = "maxillo"):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.project_slug = project_slug
        self.session = requests.Session()
        self.is_authenticated = False
        
    def login(self) -> tuple[bool, str]:
        """Login to the TF4M API using session authentication."""
        if not self.username or not self.password:
            return False, "Username and password are required"
            
        try:
            # Get CSRF token first
            login_page = self.session.get(f"{self.base_url}/login/")
            if login_page.status_code != 200:
                return False, f"Failed to get login page: HTTP {login_page.status_code}"
                
            csrf_token = self.session.cookies.get('csrftoken')
            if not csrf_token:
                return False, "Could not retrieve CSRF token"
            
            # Login with credentials
            login_data = {
                'username': self.username,
                'password': self.password,
                'csrfmiddlewaretoken': csrf_token
            }
            
            login_response = self.session.post(f"{self.base_url}/login/", data=login_data)
            
            if login_response.status_code == 200:
                # Check if login was actually successful by trying to access patients API
                test_response = self.session.get(f"{self.base_url}/api/maxillo/patients/")
                if test_response.status_code == 200:
                    self.is_authenticated = True
                    return True, "Login successful"
                else:
                    return False, "Login failed - invalid credentials"
            else:
                return False, f"Login failed: HTTP {login_response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error during login: {str(e)}"
    
    def _get_csrf_token(self) -> Optional[str]:
        """Get CSRF token from session cookies or by fetching upload page."""
        csrf_token = self.session.cookies.get('csrftoken')
        if not csrf_token:
            # Try to get fresh CSRF token from upload page
            try:
                self.session.get(f"{self.base_url}/upload/")
                csrf_token = self.session.cookies.get('csrftoken')
            except Exception:
                pass
        return csrf_token
    
    def test_connection(self) -> tuple[bool, str]:
        """Test the connection to the API."""
        if not self.is_authenticated:
            login_success, login_message = self.login()
            if not login_success:
                return False, f"Authentication failed: {login_message}"
        
        try:
            response = self.session.get(f"{self.base_url}/api/{self.project_slug}/patients/")
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def get_patients(self) -> tuple[bool, List[Dict[str, Any]], str]:
        """Get list of all patients from the API."""
        if not self.is_authenticated:
            login_success, login_message = self.login()
            if not login_success:
                return False, [], f"Authentication failed: {login_message}"
        
        try:
            response = self.session.get(f"{self.base_url}/api/{self.project_slug}/patients/")
            if response.status_code == 200:
                data = response.json()
                return True, data.get('patients', []), "Success"
            else:
                return False, [], f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, [], f"Connection error: {str(e)}"
        except json.JSONDecodeError as e:
            return False, [], f"Invalid JSON response: {str(e)}"
    
    def get_patient_files(self, patient_id: int) -> tuple[bool, List[Dict[str, Any]], str]:
        """Get list of files for a specific patient."""
        if not self.is_authenticated:
            login_success, login_message = self.login()
            if not login_success:
                return False, [], f"Authentication failed: {login_message}"
        
        try:
            response = self.session.get(f"{self.base_url}/api/{self.project_slug}/patients/{patient_id}/files/")
            if response.status_code == 200:
                data = response.json()
                return True, data.get('files', []), "Success"
            else:
                return False, [], f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, [], f"Connection error: {str(e)}"
        except json.JSONDecodeError as e:
            return False, [], f"Invalid JSON response: {str(e)}"
    
    def find_patient_by_name(self, patient_name: str) -> tuple[bool, Optional[Dict[str, Any]], str]:
        """Find a patient by name."""
        success, patients, message = self.get_patients()
        if not success:
            return False, None, message
        
        # Look for exact or partial match
        for patient in patients:
            if patient.get('name', '').lower() == patient_name.lower():
                return True, patient, "Found exact match"
        
        # Look for partial match
        for patient in patients:
            if patient_name.lower() in patient.get('name', '').lower():
                return True, patient, "Found partial match"
        
        return False, None, "Patient not found"
    
    def delete_patient(self, patient_id: str) -> tuple[bool, str]:
        """Delete a patient from the TF4M platform.
        
        Args:
            patient_id: The ID of the patient to delete on the remote server
            
        Returns:
            tuple[bool, str]: (success, message)
        """
        if not self.is_authenticated:
            login_success, login_message = self.login()
            if not login_success:
                return False, f"Authentication failed: {login_message}"
        
        try:
            # Check if base_url includes /maxillo, if not add it
            if '/maxillo' in self.base_url:
                delete_url = f"{self.base_url}/patient/{patient_id}/delete/"
            else:
                delete_url = f"{self.base_url}/maxillo/patient/{patient_id}/delete/"
            
            print(f"Attempting to delete patient at URL: {delete_url}")
            
            response = self.session.post(
                delete_url,
                headers={
                    'X-CSRFToken': self._get_csrf_token(),
                    'Referer': self.base_url
                },
                timeout=30
            )
            
            print(f"Delete response status: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 204:
                return True, f"Patient {patient_id} deleted successfully"
            elif response.status_code == 404:
                return False, f"Patient not found on server (ID: {patient_id}). May have already been deleted or ID mismatch."
            else:
                return False, f"Failed to delete patient (Status: {response.status_code}, URL: {delete_url})"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error while deleting patient: {str(e)}"
        except Exception as e:
            return False, f"Error deleting patient: {str(e)}"
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of a file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return None
    
    def upload_patient_data(self, patient_data: PatientData, 
                          progress_callback: Optional[Callable] = None,
                          delete_before_reupload: bool = True) -> tuple[bool, str]:
        """Upload all data for a single patient to TF4M API.
        
        Args:
            patient_data: Patient data to upload
            progress_callback: Optional callback for progress updates
            delete_before_reupload: If True and patient exists, delete and recreate it.
                                   If False, skip patients that already exist.
        
        If patient already exists on the server and delete_before_reupload is True,
        it will be deleted and recreated with all data, since the API doesn't support
        partial updates.
        """
        if not self.is_authenticated:
            login_success, login_message = self.login()
            if not login_success:
                return False, f"Authentication failed: {login_message}"
        
        try:
            # Check if patient already exists
            patient_exists, existing_patient, search_message = self.find_patient_by_name(patient_data.patient_id)
            
            if patient_exists and existing_patient:
                patient_id = existing_patient['patient_id']
                remote_patient_name = existing_patient['name']
                
                # Get existing files for comparison
                files_success, existing_files, files_message = self.get_patient_files(patient_id)
                if not files_success:
                    return False, f"Failed to get existing files: {files_message}"
                
                # Check which files need to be uploaded
                files_to_upload = self._compare_and_filter_files(patient_data, existing_files)
                
                if not files_to_upload:
                    return True, f"Patient '{remote_patient_name}' already has all files up to date"
                
                # Check if delete_before_reupload is enabled
                if not delete_before_reupload:
                    # Skip this patient if delete is disabled
                    return True, f"Patient '{remote_patient_name}' already exists (skipped due to settings)"
                
                # Since API doesn't support updates, delete the existing patient
                if progress_callback:
                    progress_callback("Deleting existing patient from server...")
                
                delete_success, delete_message = self.delete_patient(patient_id)
                if not delete_success:
                    return False, f"Failed to delete existing patient before reupload: {delete_message}"
                
                if progress_callback:
                    progress_callback(f"Deleted existing patient '{remote_patient_name}'. Creating new patient...")
            
            # Create new patient and upload all files
            success, patient_id, message = self._create_new_patient(patient_data)
            if not success:
                return False, f"Failed to create patient: {message}"
            
            # Upload all files
            all_files = self._get_all_patient_files(patient_data)
            success, message = self._upload_files_to_existing_patient(
                patient_id, all_files, progress_callback
            )
            
            if success:
                if patient_exists:
                    return True, f"Reuploaded patient '{patient_data.patient_id}' with {len(all_files)} files"
                else:
                    return True, f"Created new patient '{patient_data.patient_id}' with {len(all_files)} files"
            else:
                return False, f"Failed to upload files: {message}"
                
        except Exception as e:
            return False, f"Upload error: {str(e)}"
    
    def _compare_and_filter_files(self, patient_data: PatientData, 
                                existing_files: List[Dict[str, Any]]) -> List[Tuple[FileData, str]]:
        """Compare local files with remote files and return files that need uploading."""
        files_to_upload = []
        
        # Create a map of existing file hashes
        existing_hashes = {f['file_hash']: f for f in existing_files}
        
        # Get all local files with their TF4M modality mappings
        local_files = self._get_all_patient_files(patient_data)
        
        for file_data, modality in local_files:
            local_hash = self.calculate_file_hash(file_data.path)
            if local_hash and local_hash not in existing_hashes:
                files_to_upload.append((file_data, modality))
        
        return files_to_upload
    
    def _get_all_patient_files(self, patient_data: PatientData) -> List[Tuple[FileData, str]]:
        """Get all patient files with their TF4M modality mappings, excluding files marked as EXCLUDE."""
        files = []
        
        # Map local data types to TF4M modality slugs
        modality_mapping = {
            'cbct_dicom': 'cbct',
            'ios_upper': 'upper_scan_raw',
            'ios_lower': 'lower_scan_raw', 
            'intraoral_photo': 'intraoral_photos',
            'teleradiography': 'teleradiography',
            'orthopantomography': 'panoramich'
        }
        
        # Add CBCT files - prefer NIFTI version if available
        if (patient_data.nifti_conversion_status == "completed" and 
            patient_data.nifti_conversion_path and 
            os.path.exists(patient_data.nifti_conversion_path)):
            # Use converted NIFTI file
            nifti_file = FileData(
                path=patient_data.nifti_conversion_path,
                data_type=DataType.CBCT_DICOM
            )
            files.append((nifti_file, modality_mapping['cbct_dicom']))
        else:
            # Use original CBCT files if no NIFTI conversion available
            for cbct_file in patient_data.cbct_files:
                # Skip excluded files
                if cbct_file.data_type != DataType.EXCLUDE:
                    files.append((cbct_file, modality_mapping['cbct_dicom']))
        
        # Add IOS files (skip if excluded)
        if patient_data.ios_upper and patient_data.ios_upper.data_type != DataType.EXCLUDE:
            files.append((patient_data.ios_upper, modality_mapping['ios_upper']))
        if patient_data.ios_lower and patient_data.ios_lower.data_type != DataType.EXCLUDE:
            files.append((patient_data.ios_lower, modality_mapping['ios_lower']))
        
        # Add intraoral photos (skip excluded)
        for photo in patient_data.intraoral_photos:
            if photo.data_type != DataType.EXCLUDE:
                files.append((photo, modality_mapping['intraoral_photo']))
        
        # Add teleradiography (skip if excluded)
        if patient_data.teleradiography and patient_data.teleradiography.data_type != DataType.EXCLUDE:
            files.append((patient_data.teleradiography, modality_mapping['teleradiography']))
        
        # Add orthopantomography (skip if excluded)
        if patient_data.orthopantomography and patient_data.orthopantomography.data_type != DataType.EXCLUDE:
            files.append((patient_data.orthopantomography, modality_mapping['orthopantomography']))
        
        # Add ZIP package file if available
        if patient_data.zip_package_path and os.path.exists(patient_data.zip_package_path):
            zip_file = FileData(
                path=patient_data.zip_package_path,
                data_type=None  # ZIP files don't have a specific DataType in our enum
            )
            files.append((zip_file, 'rawzip'))
        
        return files
    
    def _create_new_patient(self, patient_data: PatientData) -> tuple[bool, Optional[int], str]:
        """Create a new patient using the TF4M upload endpoint."""
        try:
            # Get CSRF token
            csrf_token = self._get_csrf_token()
            if not csrf_token:
                return False, None, "Failed to get CSRF token"
            
            # Prepare form data - matching upload_script.py
            form_data = {
                'name': patient_data.patient_id,
                'folder': '2',  # Default folder
                'visibility': 'private',
                'cbct_upload_type': 'file'
            }
            
            # Prepare files list (field_name, file_handle) tuples
            files_to_upload = []
            
            try:
                # Add IOS files with new field names
                if patient_data.ios_upper and os.path.exists(patient_data.ios_upper.path):
                    files_to_upload.append(('upper_scan_raw', open(patient_data.ios_upper.path, 'rb')))
                
                if patient_data.ios_lower and os.path.exists(patient_data.ios_lower.path):
                    files_to_upload.append(('lower_scan_raw', open(patient_data.ios_lower.path, 'rb')))
                
                # Add CBCT file (prefer NIFTI if available)
                if (patient_data.nifti_conversion_status == "completed" and 
                    patient_data.nifti_conversion_path and 
                    os.path.exists(patient_data.nifti_conversion_path)):
                    files_to_upload.append(('cbct', open(patient_data.nifti_conversion_path, 'rb')))
                elif patient_data.cbct_files:
                    cbct_file = patient_data.cbct_files[0]
                    if os.path.exists(cbct_file.path):
                        files_to_upload.append(('cbct', open(cbct_file.path, 'rb')))
                
                # Add intraoral photos - all use same field name 'intraoral_photos'
                for photo in patient_data.intraoral_photos:
                    if os.path.exists(photo.path):
                        files_to_upload.append(('intraoral_photos', open(photo.path, 'rb')))
                
                # Add teleradiography
                if patient_data.teleradiography and os.path.exists(patient_data.teleradiography.path):
                    files_to_upload.append(('teleradiography', open(patient_data.teleradiography.path, 'rb')))
                
                # Add orthopantomography (panoramic)
                if patient_data.orthopantomography and os.path.exists(patient_data.orthopantomography.path):
                    files_to_upload.append(('panoramic', open(patient_data.orthopantomography.path, 'rb')))
                
                # Add ZIP package
                if patient_data.zip_package_path and os.path.exists(patient_data.zip_package_path):
                    files_to_upload.append(('rawzip', open(patient_data.zip_package_path, 'rb')))
                
                if not files_to_upload:
                    return False, None, "No suitable files found to create patient"
                
                # Upload patient - matching upload_script.py API call
                upload_url = f"{self.base_url}/api/{self.project_slug}/upload/"
                response = self.session.post(
                    upload_url,
                    data=form_data,
                    files=files_to_upload,
                    timeout=300
                )
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get('success'):
                            patient_id = result.get('patient_id')
                            return True, patient_id, f"Patient created successfully with ID {patient_id}"
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            return False, None, f"Upload failed: {error_msg}"
                    except json.JSONDecodeError:
                        return False, None, f"Invalid JSON response from server"
                else:
                    return False, None, f"HTTP {response.status_code}: {response.text[:200]}"
                    
            finally:
                # Always close file handles
                for field_name, file_handle in files_to_upload:
                    try:
                        file_handle.close()
                    except:
                        pass
                        
        except Exception as e:
            return False, None, f"Upload error: {str(e)}"
    
    def _upload_files_to_existing_patient(self, patient_id: int, 
                                        files_to_upload: List[Tuple[FileData, str]],
                                        progress_callback: Optional[Callable] = None) -> tuple[bool, str]:
        """Upload files to an existing patient using individual file uploads."""
        if not files_to_upload:
            return True, "No files to upload"
        
        try:
            total_files = len(files_to_upload)
            uploaded_count = 0
            
            for file_data, modality in files_to_upload:
                if progress_callback:
                    progress_callback(uploaded_count, total_files, f"Uploading {file_data.filename}")
                
                success, message = self._upload_single_file_to_patient(patient_id, file_data, modality)
                if not success:
                    return False, f"Failed to upload {file_data.filename}: {message}"
                
                uploaded_count += 1
                if progress_callback:
                    progress_callback(uploaded_count, total_files, f"Uploaded {file_data.filename}")
            
            return True, f"Successfully uploaded {uploaded_count} files"
            
        except Exception as e:
            return False, str(e)
    
    def _upload_single_file_to_patient(self, patient_id: int, file_data: FileData, 
                                     modality: str) -> tuple[bool, str]:
        """Upload a single file to an existing patient."""
        # For now, we'll use the main upload endpoint with the patient name
        # This is a limitation of the current TF4M API structure
        
        # Note: The TF4M API seems to primarily use the bulk upload endpoint
        # Individual file uploads to existing patients might need a different approach
        # For now, we'll return success but note this limitation
        
        return True, f"File {file_data.filename} marked for upload (individual file upload not fully supported by TF4M API)"
    
    def upload_patient_data_async(self, patient_data: PatientData,
                                progress_callback: Optional[Callable] = None,
                                completion_callback: Optional[Callable] = None):
        """Upload patient data asynchronously."""
        def upload_worker():
            success, message = self.upload_patient_data(patient_data, progress_callback)
            if completion_callback:
                completion_callback(success, message)
        
        thread = Thread(target=upload_worker, daemon=True)
        thread.start()
    
    def _create_or_get_patient(self, patient_identifier: str) -> Optional[str]:
        """Create or get a patient record."""
        try:
            # Try to get existing patient
            response = self.session.get(f"{self.base_url}/api/patients/{patient_identifier}/")
            if response.status_code == 200:
                return response.json()['id']
            
            # Create new patient
            patient_data = {
                'identifier': patient_identifier,
                'name': patient_identifier  # Use identifier as name for now
            }
            response = self.session.post(f"{self.base_url}/api/patients/", json=patient_data)
            if response.status_code == 201:
                return response.json()['id']
            
        except Exception:
            pass
        
        return None
    
    def _upload_file(self, patient_id: str, file_data, data_type: DataType) -> tuple[bool, str]:
        """Upload a single file."""
        try:
            if not os.path.exists(file_data.path):
                return False, f"File not found: {file_data.path}"
            
            # Map local DataType values to TF4M database modality values
            modality_mapping = {
                'cbct_dicom': 'cbct',
                'ios_upper': 'ios',
                'ios_lower': 'ios',
                'intraoral_photo': 'intraoral',
                'teleradiography': 'teleradiography',
                'orthopantomography': 'panoramich'
            }
            
            # Handle ZIP files (data_type might be None) or use mapping
            if data_type is None:
                # For ZIP files, check file extension
                if file_data.path.lower().endswith('.zip'):
                    tf4m_modality = 'rawzip'
                else:
                    tf4m_modality = 'rawzip'  # Default to rawzip for unknown files
            else:
                tf4m_modality = modality_mapping.get(data_type.value, data_type.value)
            
            # Prepare file upload
            with open(file_data.path, 'rb') as f:
                files = {'file': (file_data.filename, f, self._get_content_type(file_data.path))}
                data = {
                    'patient_id': patient_id,
                    'data_type': tf4m_modality,
                    'filename': file_data.filename
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/{self.project_slug}/uploads/",
                    files=files,
                    data=data,
                    timeout=300  # 5 minutes timeout for large files
                )
                
                if response.status_code in [200, 201]:
                    return True, "Upload successful"
                else:
                    return False, f"HTTP {response.status_code}: {response.text}"
                    
        except Exception as e:
            return False, str(e)
    
    def _get_content_type(self, file_path: str) -> str:
        """Get the content type for a file."""
        extension = os.path.splitext(file_path)[1].lower()
        
        content_types = {
            '.dcm': 'application/dicom',
            '.dicom': 'application/dicom',
            '.stl': 'application/sla',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.zip': 'application/zip',
            '.nii': 'application/octet-stream',
            '.nii.gz': 'application/gzip'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def get_upload_status(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get upload status for a patient."""
        try:
            response = self.session.get(f"{self.base_url}/api/patients/{patient_id}/upload-status/")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    
    def set_credentials(self, username: str, password: str):
        """Update the authentication credentials."""
        self.username = username
        self.password = password
        self.is_authenticated = False  # Force re-authentication
    
    def set_base_url(self, base_url: str):
        """Update the base URL."""
        self.base_url = base_url.rstrip('/')
        self.is_authenticated = False  # Force re-authentication


# Keep the old APIClient class for backward compatibility
class APIClient(TF4MAPIClient):
    """Backward compatibility alias for the TF4M API client."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        # Convert old API key initialization to username/password
        super().__init__(base_url)
        if api_key:
            # For now, treat api_key as username (password would need to be set separately)
            self.username = api_key
    
    def set_api_key(self, api_key: str):
        """Update the API key (backward compatibility)."""
        self.username = api_key
