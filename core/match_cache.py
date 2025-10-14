"""
Patient matching cache system for the dental data management application.

This module provides caching functionality to store and retrieve patient matching
results, allowing users to avoid recreating matches when reloading the same folders.
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import logging

from .models import PatientData, FileData, DataType, MatchStatus


@dataclass
class CacheEntry:
    """Represents a cache entry for patient matching data."""
    patient_id: str
    folder_path: str
    folder_hash: str
    timestamp: float
    file_count: int
    matched_files: Dict[str, Any] = field(default_factory=dict)
    unmatched_files: List[str] = field(default_factory=list)
    manual_assignments: Dict[str, str] = field(default_factory=dict)  # file_path -> data_type
    manually_complete: bool = False
    manual_completion_note: str = ""
    # Upload status fields
    upload_status: str = "not_uploaded"  # not_uploaded, uploading, uploaded, failed
    remote_patient_id: Optional[int] = None  # ID from TF4M system
    last_upload_attempt: Optional[float] = None
    upload_error_message: str = ""
    uploaded_file_hashes: Dict[str, str] = field(default_factory=dict)  # filename -> hash
    version: str = "1.1"  # Updated version for new fields
    
    def is_valid(self, current_hash: str, max_age_days: int = 30) -> bool:
        """Check if cache entry is valid."""
        # Check hash match
        if self.folder_hash != current_hash:
            return False
            
        # Check age
        age_seconds = time.time() - self.timestamp
        max_age_seconds = max_age_days * 24 * 60 * 60
        return age_seconds < max_age_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        # Handle backward compatibility for new fields
        if 'manually_complete' not in data:
            data['manually_complete'] = False
        if 'manual_completion_note' not in data:
            data['manual_completion_note'] = ""
        # Handle upload status fields (new in v1.1)
        if 'upload_status' not in data:
            data['upload_status'] = "not_uploaded"
        if 'remote_patient_id' not in data:
            data['remote_patient_id'] = None
        if 'last_upload_attempt' not in data:
            data['last_upload_attempt'] = None
        if 'upload_error_message' not in data:
            data['upload_error_message'] = ""
        if 'uploaded_file_hashes' not in data:
            data['uploaded_file_hashes'] = {}
        return cls(**data)


class MatchCache:
    """Cache system for patient matching results."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the match cache.
        
        Args:
            cache_dir: Directory to store cache files. If None, cache will be stored 
                      in each patient folder as needed.
        """
        self.logger = logging.getLogger(__name__)
        
        # If cache_dir is provided, use centralized cache (legacy mode)
        # If None, use distributed cache in patient folders (new default)
        self.cache_dir = cache_dir
        self.centralized_cache = cache_dir is not None
        
        if self.centralized_cache:
            self.ensure_cache_dir()
            self.cache_file = os.path.join(self.cache_dir, "patient_matches.json")
        else:
            self.cache_file = None  # Will be determined per patient folder
            
        self.cache_data: Dict[str, CacheEntry] = {}
        
        if self.centralized_cache:
            self.load_cache()
    
    def ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_key(self, folder_path: str) -> str:
        """Generate cache key for a folder path."""
        # Normalize path and use as key
        normalized_path = os.path.normpath(os.path.abspath(folder_path))
        return normalized_path
    
    def get_folder_hash(self, folder_path: str) -> str:
        """Generate hash for folder contents to detect changes."""
        hasher = hashlib.md5()
        
        try:
            # Include folder modification time and file count
            stat = os.stat(folder_path)
            hasher.update(f"{stat.st_mtime}_{stat.st_size}".encode())
            
            # Get cache file name to exclude it from hash calculation
            cache_filename = os.path.basename(self.get_patient_cache_file(folder_path))
            
            # Include file list and their modification times
            files = []
            for root, dirs, filenames in os.walk(folder_path):
                for filename in sorted(filenames):
                    # Skip cache file to avoid hash invalidation when cache is created
                    if filename == cache_filename:
                        continue
                        
                    file_path = os.path.join(root, filename)
                    try:
                        file_stat = os.stat(file_path)
                        rel_path = os.path.relpath(file_path, folder_path)
                        files.append(f"{rel_path}:{file_stat.st_mtime}:{file_stat.st_size}")
                    except (OSError, IOError):
                        continue
            
            hasher.update("|".join(files).encode())
            return hasher.hexdigest()
            
        except (OSError, IOError) as e:
            self.logger.warning(f"Error calculating folder hash for {folder_path}: {e}")
            # Fallback to timestamp
            return hashlib.md5(f"{time.time()}".encode()).hexdigest()
    
    def get_patient_cache_file(self, folder_path: str) -> str:
        """Get cache file path for a specific patient folder."""
        return os.path.join(folder_path, ".tf4m_cache.json")
    
    def load_patient_cache(self, folder_path: str) -> Dict[str, CacheEntry]:
        """Load cache data for a specific patient folder."""
        cache_file = self.get_patient_cache_file(folder_path)
        
        if not os.path.exists(cache_file):
            return {}
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Convert to CacheEntry objects
            cache_data = {}
            for key, entry_data in data.items():
                cache_data[key] = CacheEntry(**entry_data)
                
            return cache_data
            
        except (IOError, json.JSONDecodeError) as e:
            self.logger.warning(f"Error loading patient cache from {cache_file}: {e}")
            return {}
    
    def save_patient_cache(self, folder_path: str, cache_data: Dict[str, CacheEntry]):
        """Save cache data for a specific patient folder."""
        cache_file = self.get_patient_cache_file(folder_path)
        
        try:
            # Convert CacheEntry objects to dict
            data = {}
            for key, entry in cache_data.items():
                data[key] = {
                    'patient_id': entry.patient_id,
                    'folder_path': entry.folder_path,
                    'folder_hash': entry.folder_hash,
                    'timestamp': entry.timestamp,
                    'file_count': entry.file_count,
                    'matched_files': entry.matched_files,
                    'unmatched_files': entry.unmatched_files,
                    'manual_assignments': entry.manual_assignments,
                    'manually_complete': entry.manually_complete,
                    'manual_completion_note': entry.manual_completion_note,
                    'upload_status': entry.upload_status,
                    'remote_patient_id': entry.remote_patient_id,
                    'last_upload_attempt': entry.last_upload_attempt,
                    'upload_error_message': entry.upload_error_message,
                    'uploaded_file_hashes': entry.uploaded_file_hashes,
                    'version': entry.version
                }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except IOError as e:
            self.logger.error(f"Error saving patient cache to {cache_file}: {e}")
    
    def load_cache(self):
        """Load cache from disk."""
        if not self.centralized_cache:
            # For distributed cache, load per patient as needed
            self.cache_data = {}
            return
            
        if not os.path.exists(self.cache_file):
            self.cache_data = {}
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.cache_data = {}
            for key, entry_data in data.items():
                try:
                    self.cache_data[key] = CacheEntry.from_dict(entry_data)
                except Exception as e:
                    self.logger.warning(f"Error loading cache entry {key}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error loading cache file: {e}")
            self.cache_data = {}
    
    def save_cache(self):
        """Save cache to disk."""
        if not self.centralized_cache:
            self.logger.warning("save_cache() called for distributed cache mode")
            return
            
        try:
            # Convert to serializable format
            data = {}
            for key, entry in self.cache_data.items():
                data[key] = entry.to_dict()
            
            # Atomic write
            temp_file = self.cache_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Replace original file
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            os.rename(temp_file, self.cache_file)
            
            self.logger.info(f"Cache saved with {len(self.cache_data)} entries")
            
        except Exception as e:
            self.logger.error(f"Error saving cache file: {e}")
    
    def get_cached_matches(self, folder_path: str) -> Optional[PatientData]:
        """Retrieve cached matching results for a folder.
        
        Args:
            folder_path: Path to the patient folder
            
        Returns:
            PatientData if valid cache exists, None otherwise
        """
        cache_key = self.get_cache_key(folder_path)
        
        # Load cache data for this patient
        if self.centralized_cache:
            cache_data = self.cache_data
        else:
            cache_data = self.load_patient_cache(folder_path)
        
        if cache_key not in cache_data:
            self.logger.debug(f"No cache entry found for {folder_path}")
            return None
        
        entry = cache_data[cache_key]
        current_hash = self.get_folder_hash(folder_path)
        
        if not entry.is_valid(current_hash):
            self.logger.info(f"Cache entry for {folder_path} is invalid (hash mismatch or expired)")
            # Remove invalid entry
            del cache_data[cache_key]
            if self.centralized_cache:
                self.save_cache()
            else:
                self.save_patient_cache(folder_path, cache_data)
            return None
        
        self.logger.info(f"Loading cached matches for {folder_path}")
        return self._deserialize_patient_data(entry, folder_path)
    
    def cache_matches(self, patient_data: PatientData):
        """Cache matching results for a patient.
        
        Args:
            patient_data: Patient data with matching results to cache
        """
        cache_key = self.get_cache_key(patient_data.folder_path)
        folder_hash = self.get_folder_hash(patient_data.folder_path)
        
        # Serialize patient data
        matched_files = {}
        unmatched_files = []
        manual_assignments = {}
        
        # Process all matched files
        all_files = patient_data.get_all_files()
        for file_data in all_files:
            if file_data.status in [MatchStatus.MATCHED, MatchStatus.MANUAL] and file_data.data_type:
                file_info = {
                    'data_type': file_data.data_type.value,
                    'confidence': file_data.confidence,
                    'status': file_data.status.value,
                    'metadata': file_data.metadata
                }
                matched_files[file_data.path] = file_info
                
                # Track manual assignments by status
                if file_data.status == MatchStatus.MANUAL:
                    manual_assignments[file_data.path] = file_data.data_type.value
        
        # Process unmatched files
        for file_data in patient_data.unmatched_files:
            unmatched_files.append(file_data.path)
        
        # Create cache entry
        entry = CacheEntry(
            patient_id=patient_data.patient_id,
            folder_path=patient_data.folder_path,
            folder_hash=folder_hash,
            timestamp=time.time(),
            file_count=len(all_files),
            matched_files=matched_files,
            unmatched_files=unmatched_files,
            manual_assignments=manual_assignments,
            manually_complete=patient_data.manually_complete,
            manual_completion_note=patient_data.manual_completion_note
        )
        
        # Save cache entry
        if self.centralized_cache:
            self.cache_data[cache_key] = entry
            self.save_cache()
        else:
            # Load existing patient cache, update it, and save
            cache_data = self.load_patient_cache(patient_data.folder_path)
            cache_data[cache_key] = entry
            self.save_patient_cache(patient_data.folder_path, cache_data)
        
        self.logger.info(f"Cached matches for {patient_data.patient_id}: "
                        f"{len(matched_files)} matched, {len(unmatched_files)} unmatched")
    
    def _deserialize_patient_data(self, entry: CacheEntry, folder_path: str) -> PatientData:
        """Deserialize cache entry back to PatientData."""
        from .file_analyzer import FileAnalyzer
        
        # Create fresh PatientData by analyzing folder structure
        # but then apply cached matching results
        # IMPORTANT: use use_cache=False to avoid infinite recursion
        analyzer = FileAnalyzer()
        patient_data = analyzer.analyze_patient_folder(folder_path, use_cache=False)
        
        # Apply cached matches
        self._apply_cached_matches(patient_data, entry)
        
        return patient_data
    
    def _apply_cached_matches(self, patient_data: PatientData, entry: CacheEntry):
        """Apply cached matching results to patient data."""
        # Create file lookup
        all_files = patient_data.get_all_files()
        file_lookup = {f.path: f for f in all_files}
        
        # Reset patient data structure
        patient_data.cbct_files = []
        patient_data.ios_upper = None
        patient_data.ios_lower = None
        patient_data.intraoral_photos = []
        patient_data.teleradiography = None
        patient_data.orthopantomography = None
        patient_data.unmatched_files = []
        
        # Apply cached matches
        for file_path, file_info in entry.matched_files.items():
            if file_path in file_lookup:
                file_data = file_lookup[file_path]
                
                # Update file data
                try:
                    file_data.data_type = DataType(file_info['data_type'])
                    file_data.confidence = file_info.get('confidence', 0.8)
                    
                    # Restore status from cache, default to MATCHED for backward compatibility
                    status_value = file_info.get('status', 'matched')
                    file_data.status = MatchStatus(status_value)
                    
                    file_data.metadata.update(file_info.get('metadata', {}))
                    
                    # Assign to appropriate patient data field
                    self._assign_file_to_patient_structure(patient_data, file_data)
                    
                except ValueError as e:
                    self.logger.warning(f"Invalid data type in cache for {file_path}: {e}")
                    patient_data.unmatched_files.append(file_data)
        
        # Handle unmatched files
        for file_path in entry.unmatched_files:
            if file_path in file_lookup:
                file_data = file_lookup[file_path]
                file_data.status = MatchStatus.UNMATCHED
                file_data.data_type = None
                file_data.confidence = 0.0
                patient_data.unmatched_files.append(file_data)
        
        # Handle any files not in cache (new files)
        cached_files = set(entry.matched_files.keys()) | set(entry.unmatched_files)
        for file_path, file_data in file_lookup.items():
            if file_path not in cached_files:
                # New file not in cache - add to unmatched
                file_data.status = MatchStatus.UNMATCHED
                file_data.data_type = None
                file_data.confidence = 0.0
                patient_data.unmatched_files.append(file_data)
        
        # Restore manual completion status
        patient_data.manually_complete = getattr(entry, 'manually_complete', False)
        patient_data.manual_completion_note = getattr(entry, 'manual_completion_note', "")
    
    def _assign_file_to_patient_structure(self, patient_data: PatientData, file_data: FileData):
        """Assign file to appropriate patient data structure based on data type."""
        if file_data.data_type == DataType.CBCT_DICOM:
            patient_data.cbct_files.append(file_data)
        elif file_data.data_type == DataType.IOS_UPPER:
            patient_data.ios_upper = file_data
        elif file_data.data_type == DataType.IOS_LOWER:
            patient_data.ios_lower = file_data
        elif file_data.data_type == DataType.INTRAORAL_PHOTO:
            patient_data.intraoral_photos.append(file_data)
        elif file_data.data_type == DataType.TELERADIOGRAPHY:
            patient_data.teleradiography = file_data
        elif file_data.data_type == DataType.ORTHOPANTOMOGRAPHY:
            patient_data.orthopantomography = file_data
        else:
            # Unknown type, add to unmatched
            patient_data.unmatched_files.append(file_data)
    
    def invalidate_cache(self, folder_path: str):
        """Invalidate cache for a specific folder."""
        cache_key = self.get_cache_key(folder_path)
        
        if self.centralized_cache:
            if cache_key in self.cache_data:
                del self.cache_data[cache_key]
                self.save_cache()
                self.logger.info(f"Invalidated cache for {folder_path}")
        else:
            # For distributed cache, delete the cache file
            cache_file = self.get_patient_cache_file(folder_path)
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    self.logger.info(f"Invalidated cache for {folder_path}")
                except OSError as e:
                    self.logger.error(f"Error removing cache file {cache_file}: {e}")
    
    def clear_cache(self):
        """Clear all cache entries."""
        if self.centralized_cache:
            self.cache_data = {}
            self.save_cache()
            self.logger.info("Cleared all cache entries")
        else:
            self.logger.warning("clear_cache() not supported for distributed cache mode")
    
    def cleanup_expired_entries(self, max_age_days: int = 30):
        """Remove expired cache entries."""
        if not self.centralized_cache:
            self.logger.warning("cleanup_expired_entries() not supported for distributed cache mode")
            return
            
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        expired_keys = []
        for key, entry in self.cache_data.items():
            if current_time - entry.timestamp > max_age_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache_data[key]
        
        if expired_keys:
            self.save_cache()
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def update_upload_status(self, folder_path: str, status: str, 
                           remote_patient_id: Optional[int] = None, 
                           error_message: str = "", 
                           uploaded_file_hashes: Optional[Dict[str, str]] = None):
        """Update upload status for a patient."""
        cache_key = self.get_cache_key(folder_path)
        
        if self.centralized_cache:
            if cache_key in self.cache_data:
                entry = self.cache_data[cache_key]
                entry.upload_status = status
                entry.last_upload_attempt = time.time()
                if remote_patient_id is not None:
                    entry.remote_patient_id = remote_patient_id
                if error_message:
                    entry.upload_error_message = error_message
                if uploaded_file_hashes:
                    entry.uploaded_file_hashes.update(uploaded_file_hashes)
                self.save_cache()
        else:
            # Distributed cache
            cache_data = self.load_patient_cache(folder_path)
            if cache_key in cache_data:
                entry = cache_data[cache_key]
                entry.upload_status = status
                entry.last_upload_attempt = time.time()
                if remote_patient_id is not None:
                    entry.remote_patient_id = remote_patient_id
                if error_message:
                    entry.upload_error_message = error_message
                if uploaded_file_hashes:
                    entry.uploaded_file_hashes.update(uploaded_file_hashes)
                self.save_patient_cache(folder_path, cache_data)
    
    def get_upload_status(self, folder_path: str) -> Optional[Dict[str, Any]]:
        """Get upload status for a patient."""
        cache_key = self.get_cache_key(folder_path)
        
        if self.centralized_cache:
            entry = self.cache_data.get(cache_key)
        else:
            cache_data = self.load_patient_cache(folder_path)
            entry = cache_data.get(cache_key)
        
        if entry:
            return {
                'status': entry.upload_status,
                'remote_patient_id': entry.remote_patient_id,
                'last_upload_attempt': entry.last_upload_attempt,
                'error_message': entry.upload_error_message,
                'uploaded_file_hashes': entry.uploaded_file_hashes
            }
        return None
    
    def get_uploaded_patients(self) -> List[Dict[str, Any]]:
        """Get list of patients that have been uploaded."""
        uploaded_patients = []
        
        if self.centralized_cache:
            for entry in self.cache_data.values():
                if entry.upload_status == "uploaded" and entry.remote_patient_id:
                    uploaded_patients.append({
                        'patient_id': entry.patient_id,
                        'folder_path': entry.folder_path,
                        'remote_patient_id': entry.remote_patient_id,
                        'last_upload_attempt': entry.last_upload_attempt
                    })
        else:
            # For distributed cache, we'd need to scan all patient folders
            # This is more expensive, so we'll return empty list for now
            pass
        
        return uploaded_patients
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.centralized_cache:
            # For distributed cache, return basic stats
            return {
                'total_entries': 0,
                'total_matched_files': 0,
                'total_unmatched_files': 0,
                'cache_size_mb': 0.0,
                'mode': 'distributed'
            }
            
        total_entries = len(self.cache_data)
        total_matched_files = sum(len(entry.matched_files) for entry in self.cache_data.values())
        total_unmatched_files = sum(len(entry.unmatched_files) for entry in self.cache_data.values())
        
        # Calculate cache size
        cache_size = 0
        if os.path.exists(self.cache_file):
            cache_size = os.path.getsize(self.cache_file)
        
        oldest_entry = None
        newest_entry = None
        if self.cache_data:
            timestamps = [entry.timestamp for entry in self.cache_data.values()]
            oldest_entry = datetime.fromtimestamp(min(timestamps))
            newest_entry = datetime.fromtimestamp(max(timestamps))
        
        return {
            'total_entries': total_entries,
            'total_matched_files': total_matched_files,
            'total_unmatched_files': total_unmatched_files,
            'cache_size_bytes': cache_size,
            'cache_file': self.cache_file,
            'oldest_entry': oldest_entry.isoformat() if oldest_entry else None,
            'newest_entry': newest_entry.isoformat() if newest_entry else None
        }