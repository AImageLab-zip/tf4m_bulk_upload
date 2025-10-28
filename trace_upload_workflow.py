"""
Upload workflow trace - shows the actual execution flow
"""

def trace_upload_workflow():
    """Trace the upload workflow step by step."""
    
    print("="*80)
    print("UPLOAD WORKFLOW EXECUTION TRACE")
    print("="*80)
    
    workflow_steps = [
        {
            "step": 1,
            "component": "MainWindow",
            "method": "upload_all_patients()",
            "action": "User clicks 'Upload All' button",
            "code": """
# gui/main_window.py - line ~220
def upload_all_patients(self):
    # Get all patients from project
    all_patients = self.project_manager.project_data.patients
    
    # Show upload dialog for user choice
    upload_dialog = UploadDialog(self.root, all_patients)
    result = upload_dialog.show()
    
    # Start upload with selected patients
    if result['action'] == 'upload':
        self.upload_manager.start_bulk_upload(result['patients'])
"""
        },
        {
            "step": 2, 
            "component": "UploadDialog",
            "method": "show()",
            "action": "Ask user: all patients or complete only?",
            "code": """
# gui/upload_dialog.py - line ~130
def on_upload(self):
    choice = self.upload_choice.get()  # 'complete_only' or 'all_patients'
    
    if choice == "complete_only":
        selected_patients = self.complete_patients
    else:
        selected_patients = self.patients
    
    self.result = {
        'action': 'upload',
        'patients': selected_patients,
        'choice': choice
    }
"""
        },
        {
            "step": 3,
            "component": "UploadManager", 
            "method": "start_bulk_upload()",
            "action": "Initialize upload queue and statistics",
            "code": """
# gui/upload_manager.py - line ~240
def start_bulk_upload(self, patients: List[PatientData]):
    self.upload_queue = patients.copy()
    self.upload_stats = {
        "total": len(patients),
        "completed": 0,
        "failed": 0, 
        "skipped": 0,
        "start_time": datetime.now()
    }
    self.populate_queue_tree()  # Show patients in UI
"""
        },
        {
            "step": 4,
            "component": "UploadManager",
            "method": "upload_worker()",
            "action": "Process each patient in background thread",
            "code": """
# gui/upload_manager.py - line ~310
def upload_worker(self):
    while self.upload_queue:
        patient = self.upload_queue.pop(0)
        
        # Check cache first - skip if already uploaded
        cache_status = self.cache.get_upload_status(patient.folder_path)
        if cache_status and cache_status.get('status') == 'uploaded':
            self.upload_stats["skipped"] += 1
            continue
            
        # Mark as uploading in cache
        self.cache.update_upload_status(patient.folder_path, "uploading")
        
        # Call API client
        success, message = self.api_client.upload_patient_data(patient, progress_callback)
"""
        },
        {
            "step": 5,
            "component": "TF4MAPIClient",
            "method": "upload_patient_data()",
            "action": "Check if patient exists on TF4M server",
            "code": """
# core/api_client.py - line ~150
def upload_patient_data(self, patient_data: PatientData, progress_callback):
    # Authenticate if needed
    if not self.is_authenticated:
        login_success, login_message = self.login()
    
    # Check if patient exists
    patient_exists, existing_patient, message = self.find_patient_by_name(patient_data.patient_id)
    
    if patient_exists:
        # Update existing patient
        return self._update_existing_patient(existing_patient, patient_data)
    else:
        # Create new patient
        return self._create_new_patient(patient_data)
"""
        },
        {
            "step": 6,
            "component": "TF4MAPIClient",
            "method": "_create_new_patient() OR _update_existing_patient()",
            "action": "Upload files based on patient status",
            "code": """
# For NEW patient:
def _create_new_patient(self, patient_data):
    # Prepare multipart form data
    files = {}
    if patient_data.ios_upper:
        files['upper_scan_raw'] = open(patient_data.ios_upper.path, 'rb')
    if patient_data.ios_lower:
        files['lower_scan_raw'] = open(patient_data.ios_lower.path, 'rb')
    if patient_data.cbct_files:
        files['cbct'] = open(patient_data.cbct_files[0].path, 'rb')
    
    # POST to /upload/ endpoint
    response = self.session.post(f"{self.base_url}/upload/", files=files, data=form_data)

# For EXISTING patient:
def _update_existing_patient(self, existing_patient, patient_data):
    # Get current files from server
    existing_files = self.get_patient_files(existing_patient['patient_id'])
    
    # Compare hashes and upload only new/changed files
    files_to_upload = self._compare_and_filter_files(patient_data, existing_files)
"""
        },
        {
            "step": 7,
            "component": "TF4MAPIClient",
            "method": "_compare_and_filter_files()",
            "action": "Compare local vs remote file hashes",
            "code": """
# core/api_client.py - line ~205
def _compare_and_filter_files(self, patient_data, existing_files):
    files_to_upload = []
    existing_hashes = {f['file_hash']: f for f in existing_files}
    
    local_files = self._get_all_patient_files(patient_data)
    for file_data, modality in local_files:
        local_hash = self.calculate_file_hash(file_data.path)
        if local_hash and local_hash not in existing_hashes:
            files_to_upload.append((file_data, modality))
    
    return files_to_upload
"""
        },
        {
            "step": 8,
            "component": "UploadManager",
            "method": "completion_callback()",
            "action": "Update cache and UI with results",
            "code": """
# gui/upload_manager.py - line ~340
def completion_callback(success, message):
    if success:
        self.upload_stats["completed"] += 1
        # Update cache with success
        self.cache.update_upload_status(patient.folder_path, "uploaded", remote_patient_id)
        self.log_message(f"✓ {patient.patient_id}: {message}")
    else:
        self.upload_stats["failed"] += 1  
        # Update cache with error
        self.cache.update_upload_status(patient.folder_path, "failed", error_message=message)
        self.log_message(f"✗ {patient.patient_id}: {message}")
"""
        }
    ]
    
    for step_info in workflow_steps:
        print(f"\nSTEP {step_info['step']}: {step_info['component']} - {step_info['method']}")
        print(f"Action: {step_info['action']}")
        print("Code:")
        print(step_info['code'])
        print("-" * 80)


def show_actual_http_examples():
    """Show actual HTTP requests that would be made."""
    
    print("\n" + "="*80)
    print("ACTUAL HTTP REQUESTS")
    print("="*80)
    
    examples = [
        {
            "name": "1. Login Request",
            "method": "POST",
            "url": "https://toothfairy4m.ing.unimore.it/login/",
            "headers": "Content-Type: application/x-www-form-urlencoded",
            "body": "username=your_username&password=your_password&csrfmiddlewaretoken=xyz789"
        },
        {
            "name": "2. Get Patients List",
            "method": "GET", 
            "url": "https://toothfairy4m.ing.unimore.it/api/maxillo/patients/",
            "headers": "Cookie: sessionid=abc123; csrftoken=xyz789",
            "body": "(empty)"
        },
        {
            "name": "3. Get Patient Files",
            "method": "GET",
            "url": "https://toothfairy4m.ing.unimore.it/api/maxillo/patients/25/files/",
            "headers": "Cookie: sessionid=abc123; csrftoken=xyz789", 
            "body": "(empty)"
        },
        {
            "name": "4. Upload New Patient",
            "method": "POST",
            "url": "https://toothfairy4m.ing.unimore.it/upload/",
            "headers": "Content-Type: multipart/form-data; Cookie: sessionid=abc123",
            "body": "multipart form with: name, upper_scan_raw, lower_scan_raw, cbct files"
        }
    ]
    
    for example in examples:
        print(f"\n{example['name']}:")
        print(f"  {example['method']} {example['url']}")
        print(f"  Headers: {example['headers']}")
        print(f"  Body: {example['body']}")


if __name__ == "__main__":
    trace_upload_workflow()
    show_actual_http_examples()
    
    print(f"\n" + "="*80)
    print("CACHE FILE EXAMPLE (.tf4m_cache.json):")
    print("="*80)
    
    cache_example = """{
  "C:\\\\path\\\\to\\\\patient_001": {
    "patient_id": "Patient_001",
    "folder_path": "C:\\\\path\\\\to\\\\patient_001",
    "folder_hash": "abc123def456...",
    "timestamp": 1697000000.0,
    "upload_status": "uploaded",
    "remote_patient_id": 25,
    "last_upload_attempt": 1697000000.0,
    "upload_error_message": "",
    "uploaded_file_hashes": {
      "upper_scan.stl": "5af3c8ff261a027aa90648ee812a493ec49015ae...",
      "lower_scan.stl": "a0f54699df85f4593638955d846759f31bde1fca..." 
    },
    "version": "1.1"
  }
}"""
    print(cache_example)