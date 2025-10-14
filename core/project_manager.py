"""
Project manager for handling the overall analysis and management of dental data.
"""

import os
from typing import List, Callable, Optional
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .models import ProjectData, PatientData, DataType, MatchStatus
from .file_analyzer import FileAnalyzer
from .cbct_converter import CBCTConverter

class ProjectManager:
    """Manages the analysis and processing of dental data projects."""
    
    def __init__(self):
        self.file_analyzer = FileAnalyzer()
        self.cbct_converter = CBCTConverter()
        self.project_data: Optional[ProjectData] = None
        self._analysis_callbacks: List[Callable] = []
        self.logger = logging.getLogger(__name__)
    
    def add_analysis_callback(self, callback: Callable):
        """Add a callback to be called during analysis progress."""
        self._analysis_callbacks.append(callback)
    
    def analyze_project(self, root_path: str, progress_callback: Optional[Callable] = None) -> ProjectData:
        """Analyze the entire project structure."""
        self.project_data = ProjectData(root_path=root_path)
        
        if not os.path.exists(root_path):
            self.project_data.global_errors.append(f"Root path does not exist: {root_path}")
            return self.project_data
        
        # Find all patient folders
        patient_folders = self._find_patient_folders(root_path)
        
        if not patient_folders:
            self.project_data.global_errors.append("No patient folders found in the specified directory")
            return self.project_data
        
        # Analyze each patient folder
        total_patients = len(patient_folders)
        
        for i, folder_path in enumerate(patient_folders):
            try:
                patient_data = self.file_analyzer.analyze_patient_folder(folder_path)
                self.project_data.patients.append(patient_data)
                
                if progress_callback:
                    progress_callback(i + 1, total_patients, f"Analyzed patient: {patient_data.patient_id}")
                
            except Exception as e:
                error_msg = f"Error analyzing patient folder {folder_path}: {str(e)}"
                self.project_data.global_errors.append(error_msg)
                if progress_callback:
                    progress_callback(i + 1, total_patients, f"Error analyzing: {os.path.basename(folder_path)}")
        
        return self.project_data
    
    def analyze_project_async(self, root_path: str, progress_callback: Optional[Callable] = None, 
                            completion_callback: Optional[Callable] = None):
        """Analyze the project asynchronously."""
        def analyze_worker():
            try:
                result = self.analyze_project(root_path, progress_callback)
                if completion_callback:
                    completion_callback(result)
            except Exception as e:
                if completion_callback:
                    completion_callback(None, str(e))
        
        thread = threading.Thread(target=analyze_worker, daemon=True)
        thread.start()
    
    def _find_patient_folders(self, root_path: str) -> List[str]:
        """Find all patient folders in the root directory."""
        patient_folders = []
        
        try:
            for item in os.listdir(root_path):
                item_path = os.path.join(root_path, item)
                if os.path.isdir(item_path):
                    # Skip tmp folders - they should not be considered as patient folders
                    if item.lower() == 'tmp':
                        continue
                    # Consider any other subfolder as a potential patient folder
                    patient_folders.append(item_path)
        except PermissionError:
            pass
        
        return sorted(patient_folders)
    
    def get_validation_report(self) -> dict:
        """Generate a comprehensive validation report."""
        if not self.project_data:
            return {"error": "No project data available"}
        
        report = {
            "total_patients": len(self.project_data.patients),
            "complete_patients": len(self.project_data.get_complete_patients()),
            "incomplete_patients": len(self.project_data.get_incomplete_patients()),
            "global_errors": self.project_data.global_errors,
            "patient_details": []
        }
        
        for patient in self.project_data.patients:
            patient_report = {
                "patient_id": patient.patient_id,
                "is_complete": patient.is_complete(),
                "missing_data_types": [dt.value for dt in patient.get_missing_data_types()],
                "unmatched_files": len(patient.unmatched_files),
                "validation_errors": patient.validation_errors,
                "file_counts": {
                    "cbct_files": len(patient.cbct_files),
                    "intraoral_photos": len(patient.intraoral_photos),
                    "has_ios_upper": patient.ios_upper is not None,
                    "has_ios_lower": patient.ios_lower is not None,
                    "has_teleradiography": patient.teleradiography is not None,
                    "has_orthopantomography": patient.orthopantomography is not None
                }
            }
            report["patient_details"].append(patient_report)
        
        return report
    
    def update_patient_file_assignment(self, patient_id: str, file_path: str, data_type: DataType):
        """Update the assignment of a file to a specific data type."""
        if not self.project_data:
            return False
        
        # Check if the file actually exists
        if not os.path.exists(file_path):
            print(f"Warning: File no longer exists: {file_path}")
            # File doesn't exist anymore - we should still try to update the cache
            # but return False to inform the user
            return False
        
        # Find the patient
        patient = None
        for p in self.project_data.patients:
            if p.patient_id == patient_id:
                patient = p
                break
        
        if not patient:
            print(f"Error: Patient not found: {patient_id}")
            return False
        
        # Find the file in unmatched files
        file_data = None
        for f in patient.unmatched_files:
            if f.path == file_path:
                file_data = f
                break
        
        # Also check in other lists
        if not file_data:
            for f in patient.get_all_files():
                if f.path == file_path:
                    file_data = f
                    break
        
        if not file_data:
            print(f"Error: File data not found in patient: {file_path}")
            return False
        
        # Remove from current location
        self._remove_file_from_patient(patient, file_data)
        
        # Update file data
        file_data.data_type = data_type
        file_data.confidence = 1.0  # Manual assignment gets highest confidence
        file_data.status = MatchStatus.MANUAL  # Mark as manually assigned
        
        # Add to appropriate location
        self._add_file_to_patient(patient, file_data)
        
        return True
    
    def _remove_file_from_patient(self, patient: PatientData, file_data):
        """Remove a file from all patient lists."""
        if file_data in patient.unmatched_files:
            patient.unmatched_files.remove(file_data)
        if file_data in patient.cbct_files:
            patient.cbct_files.remove(file_data)
        if file_data in patient.intraoral_photos:
            patient.intraoral_photos.remove(file_data)
        if patient.ios_upper == file_data:
            patient.ios_upper = None
        if patient.ios_lower == file_data:
            patient.ios_lower = None
        if patient.teleradiography == file_data:
            patient.teleradiography = None
        if patient.orthopantomography == file_data:
            patient.orthopantomography = None
    
    def _add_file_to_patient(self, patient: PatientData, file_data):
        """Add a file to the appropriate patient list based on its data type."""
        if file_data.data_type == DataType.EXCLUDE:
            # Excluded files are kept in their original location but marked as excluded
            # They stay where they were (cbct, ios, intraoral, etc.) but won't be uploaded
            # Determine where to add based on file extension/characteristics
            if file_data.path.lower().endswith(('.dcm', '.dicom')):
                patient.cbct_files.append(file_data)
            elif file_data.path.lower().endswith('.stl'):
                # STL files could be IOS - add to unmatched for now
                patient.unmatched_files.append(file_data)
            elif file_data.path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                patient.intraoral_photos.append(file_data)
            else:
                patient.unmatched_files.append(file_data)
        elif file_data.data_type == DataType.CBCT_DICOM:
            patient.cbct_files.append(file_data)
        elif file_data.data_type == DataType.IOS_UPPER:
            # For manual assignments, check if there's already a file
            if patient.ios_upper is not None:
                # Move existing file to unmatched regardless of its status
                # This ensures files never disappear when being replaced
                patient.unmatched_files.append(patient.ios_upper)
            patient.ios_upper = file_data
        elif file_data.data_type == DataType.IOS_LOWER:
            # For manual assignments, check if there's already a file
            if patient.ios_lower is not None:
                # Move existing file to unmatched regardless of its status
                # This ensures files never disappear when being replaced
                patient.unmatched_files.append(patient.ios_lower)
            patient.ios_lower = file_data
        elif file_data.data_type == DataType.INTRAORAL_PHOTO:
            patient.intraoral_photos.append(file_data)
        elif file_data.data_type == DataType.TELERADIOGRAPHY:
            # For manual assignments, check if there's already a file
            if patient.teleradiography is not None:
                # Move existing file to unmatched regardless of its status
                # This ensures files never disappear when being replaced
                patient.unmatched_files.append(patient.teleradiography)
            patient.teleradiography = file_data
        elif file_data.data_type == DataType.ORTHOPANTOMOGRAPHY:
            # For manual assignments, check if there's already a file
            if patient.orthopantomography is not None:
                # Move existing file to unmatched regardless of its status
                # This ensures files never disappear when being replaced
                patient.unmatched_files.append(patient.orthopantomography)
            patient.orthopantomography = file_data
        else:
            patient.unmatched_files.append(file_data)
    
    def get_patient_by_id(self, patient_id: str) -> Optional[PatientData]:
        """Get patient data by ID."""
        if not self.project_data:
            return None
        
        for patient in self.project_data.patients:
            if patient.patient_id == patient_id:
                return patient
        return None
    
    def convert_cbct_to_nifti(self, patient_id: str, progress_callback: Optional[Callable] = None) -> bool:
        """
        Convert CBCT DICOM files to NIfTI format for a specific patient.
        
        Args:
            patient_id: ID of the patient
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if conversion was successful, False otherwise
        """
        patient = self.get_patient_by_id(patient_id)
        if not patient:
            self.logger.error(f"Patient {patient_id} not found")
            return False
        
        if not patient.cbct_files:
            self.logger.warning(f"No CBCT files found for patient {patient_id}")
            return False
        
        if not patient.cbct_folder:
            self.logger.error(f"No CBCT folder identified for patient {patient_id}")
            return False
        
        try:
            # Update status
            patient.nifti_conversion_status = "converting"
            if progress_callback:
                progress_callback(f"Converting CBCT for patient {patient_id}...")
            
            # Perform conversion
            nifti_path = self.cbct_converter.convert_cbct_to_nifti(
                patient.cbct_folder, 
                patient.folder_path
            )
            
            if nifti_path:
                patient.nifti_conversion_path = nifti_path
                patient.nifti_conversion_status = "completed"
                patient.nifti_conversion_info = self.cbct_converter.get_conversion_info(nifti_path)
                
                if progress_callback:
                    progress_callback(f"CBCT conversion completed for patient {patient_id}")
                
                self.logger.info(f"Successfully converted CBCT for patient {patient_id}")
                return True
            else:
                patient.nifti_conversion_status = "failed"
                if progress_callback:
                    progress_callback(f"CBCT conversion failed for patient {patient_id}")
                
                self.logger.error(f"CBCT conversion failed for patient {patient_id}")
                return False
                
        except Exception as e:
            patient.nifti_conversion_status = "failed"
            self.logger.error(f"Error converting CBCT for patient {patient_id}: {e}")
            if progress_callback:
                progress_callback(f"Error converting CBCT for patient {patient_id}: {e}")
            return False
    
    def convert_all_cbct_to_nifti(self, progress_callback: Optional[Callable] = None) -> dict:
        """
        Convert CBCT DICOM files to NIfTI for all patients with CBCT data.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with conversion results
        """
        if not self.project_data:
            return {"error": "No project data available"}
        
        results = {
            "total_patients": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "skipped": 0,
            "details": []
        }
        
        # Find patients with CBCT data
        patients_with_cbct = [p for p in self.project_data.patients if p.cbct_files and p.cbct_folder]
        results["total_patients"] = len(patients_with_cbct)
        
        if not patients_with_cbct:
            if progress_callback:
                progress_callback("No patients with CBCT data found")
            return results
        
        for i, patient in enumerate(patients_with_cbct):
            try:
                if progress_callback:
                    progress_callback(f"Converting CBCT {i+1}/{len(patients_with_cbct)}: {patient.patient_id}")
                
                # Skip if already converted
                if patient.nifti_conversion_status == "completed" and patient.nifti_conversion_path:
                    if os.path.exists(patient.nifti_conversion_path):
                        results["skipped"] += 1
                        results["details"].append({
                            "patient_id": patient.patient_id,
                            "status": "skipped",
                            "reason": "Already converted"
                        })
                        continue
                
                # Perform conversion
                success = self.convert_cbct_to_nifti(patient.patient_id, progress_callback)
                
                if success:
                    results["successful_conversions"] += 1
                    results["details"].append({
                        "patient_id": patient.patient_id,
                        "status": "success",
                        "nifti_path": patient.nifti_conversion_path
                    })
                else:
                    results["failed_conversions"] += 1
                    results["details"].append({
                        "patient_id": patient.patient_id,
                        "status": "failed",
                        "reason": "Conversion failed"
                    })
                    
            except Exception as e:
                results["failed_conversions"] += 1
                results["details"].append({
                    "patient_id": patient.patient_id,
                    "status": "error",
                    "reason": str(e)
                })
                self.logger.error(f"Error processing patient {patient.patient_id}: {e}")
        
        if progress_callback:
            progress_callback(f"CBCT conversion completed: {results['successful_conversions']} successful, {results['failed_conversions']} failed")
        
        return results
    
    def get_nifti_conversion_status(self) -> dict:
        """Get overview of NIfTI conversion status for all patients."""
        if not self.project_data:
            return {}
        
        status = {
            "total_patients": len(self.project_data.patients),
            "patients_with_cbct": 0,
            "pending": 0,
            "converting": 0,
            "completed": 0,
            "failed": 0
        }
        
        for patient in self.project_data.patients:
            if patient.cbct_files:
                status["patients_with_cbct"] += 1
                
                if patient.nifti_conversion_status == "pending":
                    status["pending"] += 1
                elif patient.nifti_conversion_status == "converting":
                    status["converting"] += 1
                elif patient.nifti_conversion_status == "completed":
                    status["completed"] += 1
                elif patient.nifti_conversion_status == "failed":
                    status["failed"] += 1
        
        return status
