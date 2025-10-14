"""
Data models for the dental data management application.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import os

class DataType(Enum):
    """Enumeration of different data types in a patient folder."""
    CBCT_DICOM = "cbct_dicom"
    IOS_UPPER = "ios_upper"
    IOS_LOWER = "ios_lower"
    INTRAORAL_PHOTO = "intraoral_photo"
    TELERADIOGRAPHY = "teleradiography"
    ORTHOPANTOMOGRAPHY = "orthopantomography"
    EXCLUDE = "exclude"  # Files to exclude from upload

class MatchStatus(Enum):
    """Status of file matching."""
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"
    MANUAL = "manual"

@dataclass
class FileData:
    """Represents a file in the patient data structure."""
    path: str
    data_type: Optional[DataType] = None
    confidence: float = 0.0
    status: MatchStatus = MatchStatus.UNMATCHED
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def filename(self) -> str:
        return os.path.basename(self.path)
    
    @property
    def extension(self) -> str:
        return os.path.splitext(self.path)[1].lower()

@dataclass
class PatientData:
    """Represents all data for a single patient."""
    patient_id: str
    folder_path: str
    cbct_folder: Optional[str] = None
    ios_folder: Optional[str] = None
    cbct_files: List[FileData] = field(default_factory=list)
    ios_upper: Optional[FileData] = None
    ios_lower: Optional[FileData] = None
    intraoral_photos: List[FileData] = field(default_factory=list)
    teleradiography: Optional[FileData] = None
    orthopantomography: Optional[FileData] = None
    unmatched_files: List[FileData] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    upload_status: str = "pending"
    manually_complete: bool = False
    manual_completion_note: str = ""
    nifti_conversion_path: Optional[str] = None
    nifti_conversion_status: str = "pending"  # pending, converting, completed, failed
    nifti_conversion_info: Dict[str, Any] = field(default_factory=dict)
    zip_package_path: Optional[str] = None
    zip_package_info: Dict[str, Any] = field(default_factory=dict)
    
    def get_all_files(self) -> List[FileData]:
        """Get all files associated with this patient."""
        files = []
        files.extend(self.cbct_files)
        if self.ios_upper:
            files.append(self.ios_upper)
        if self.ios_lower:
            files.append(self.ios_lower)
        files.extend(self.intraoral_photos)
        if self.teleradiography:
            files.append(self.teleradiography)
        if self.orthopantomography:
            files.append(self.orthopantomography)
        files.extend(self.unmatched_files)
        return files
    
    def get_missing_data_types(self) -> List[DataType]:
        """Get list of missing required data types."""
        missing = []
        if not self.cbct_files:
            missing.append(DataType.CBCT_DICOM)
        if not self.ios_upper:
            missing.append(DataType.IOS_UPPER)
        if not self.ios_lower:
            missing.append(DataType.IOS_LOWER)
        if not self.teleradiography:
            missing.append(DataType.TELERADIOGRAPHY)
        if not self.orthopantomography:
            missing.append(DataType.ORTHOPANTOMOGRAPHY)
        return missing
    
    def is_complete(self) -> bool:
        """Check if patient data is complete."""
        # If manually marked as complete, consider it complete
        if self.manually_complete:
            return True
            
        # Count unmatched files, but ignore system files
        system_files = {'.ds_store', 'thumbs.db', 'desktop.ini'}
        significant_unmatched = [
            f for f in self.unmatched_files 
            if f.filename.lower() not in system_files
        ]
        return len(self.get_missing_data_types()) == 0 and len(significant_unmatched) == 0

@dataclass
class ProjectData:
    """Represents the entire project with all patients."""
    root_path: str
    patients: List[PatientData] = field(default_factory=list)
    global_errors: List[str] = field(default_factory=list)
    
    def get_incomplete_patients(self) -> List[PatientData]:
        """Get list of patients with incomplete data."""
        return [p for p in self.patients if not p.is_complete()]
    
    def get_complete_patients(self) -> List[PatientData]:
        """Get list of patients with complete data."""
        return [p for p in self.patients if p.is_complete()]
