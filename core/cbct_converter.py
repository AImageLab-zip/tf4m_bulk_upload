"""
CBCT DICOM to NIfTI converter using dcm2niix.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import zipfile
from typing import Optional, List, Tuple
from pathlib import Path
import logging

class CBCTConverter:
    """Handles conversion of CBCT DICOM files to NIfTI format and patient data packaging."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def convert_cbct_to_nifti(self, dicom_folder: str, patient_id: str, project_root: str) -> Optional[str]:
        """
        Convert CBCT DICOM files to compressed NIfTI format.
        
        Args:
            dicom_folder: Path to folder containing DICOM files
            patient_id: Patient ID for naming the output file
            project_root: Path to project root folder
            
        Returns:
            Path to converted NIfTI file or None if conversion failed
        """
        self.logger.info(f"Starting CBCT to NIfTI conversion for patient {patient_id}")
        self.logger.info(f"DICOM folder: {dicom_folder}")
        self.logger.info(f"Project root: {project_root}")
        
        try:
            # Create tmp folder at project level
            tmp_folder = os.path.join(project_root, "tmp")
            os.makedirs(tmp_folder, exist_ok=True)
            self.logger.debug(f"Temp folder: {tmp_folder}")
            
            # Define NIfTI output path with patient ID
            nifti_filename = f"{patient_id}.nii.gz"
            final_nifti_path = os.path.join(tmp_folder, nifti_filename)
            
            # Check if NIfTI file already exists
            if os.path.exists(final_nifti_path):
                self.logger.info(f"NIfTI file already exists for patient {patient_id}: {final_nifti_path}")
                return final_nifti_path
            
            # Check if dcm2niix is available
            if not self._check_dcm2niix_available():
                self.logger.error("dcm2niix is not available or not installed")
                self.logger.error("SOLUTION: Install dcm2niix using one of these methods:")
                self.logger.error("  1. pip install dcm2niix")
                self.logger.error("  2. Download from https://github.com/rordenlab/dcm2niix/releases")
                self.logger.error("  3. Install via conda: conda install -c conda-forge dcm2niix")
                return None
            
            # Verify DICOM folder exists and has files
            if not os.path.exists(dicom_folder):
                self.logger.error(f"DICOM folder does not exist: {dicom_folder}")
                return None
            
            dicom_files = [f for f in os.listdir(dicom_folder) if os.path.isfile(os.path.join(dicom_folder, f))]
            self.logger.info(f"Found {len(dicom_files)} files in DICOM folder")
            
            if len(dicom_files) == 0:
                self.logger.error("No files found in DICOM folder")
                return None
            
            # Create temporary conversion folder
            with tempfile.TemporaryDirectory() as temp_conversion_dir:
                self.logger.debug(f"Temporary conversion directory: {temp_conversion_dir}")
                
                # Run dcm2niix conversion to temporary directory
                temp_nifti_path = self._run_dcm2niix(dicom_folder, temp_conversion_dir)
                
                if temp_nifti_path and os.path.exists(temp_nifti_path):
                    # Move and rename the NIfTI file to final location
                    shutil.move(temp_nifti_path, final_nifti_path)
                    
                    file_size = os.path.getsize(final_nifti_path)
                    self.logger.info(f"Successfully converted CBCT to NIfTI: {final_nifti_path} ({file_size:,} bytes)")
                    return final_nifti_path
                else:
                    self.logger.error("dcm2niix conversion failed or produced no output")
                    return None
                
        except Exception as e:
            self.logger.exception(f"Error converting CBCT to NIfTI for patient {patient_id}:")
            return None
    
    def create_patient_zip(self, patient_folder: str, patient_id: str, project_root: str) -> Optional[str]:
        """
        Create a zip file containing all patient data.
        
        Args:
            patient_folder: Path to patient's folder
            patient_id: Patient ID for naming the zip file
            project_root: Path to project root folder
            
        Returns:
            Path to created zip file or None if creation failed
        """
        try:
            # Create tmp folder at project level
            tmp_folder = os.path.join(project_root, "tmp")
            os.makedirs(tmp_folder, exist_ok=True)
            
            # Define zip output path with patient ID
            zip_filename = f"{patient_id}.zip"
            zip_path = os.path.join(tmp_folder, zip_filename)
            
            # Check if zip file already exists
            if os.path.exists(zip_path):
                self.logger.info(f"Zip file already exists for patient {patient_id}: {zip_path}")
                return zip_path
            
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through patient folder and add all files
                for root, dirs, files in os.walk(patient_folder):
                    # Skip the tmp folder if it exists within patient folder
                    if 'tmp' in dirs:
                        dirs.remove('tmp')
                    
                    for file in files:
                        # Skip system files
                        if self._should_skip_file(file):
                            continue
                        
                        file_path = os.path.join(root, file)
                        
                        # Calculate relative path from patient folder
                        rel_path = os.path.relpath(file_path, patient_folder)
                        
                        # Add file to zip with relative path
                        zipf.write(file_path, rel_path)
            
            self.logger.info(f"Successfully created patient zip: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"Error creating patient zip for {patient_id}: {e}")
            return None
    
    def _should_skip_file(self, filename: str) -> bool:
        """Check if a file should be skipped during zip creation."""
        skip_files = {
            '.ds_store', 'thumbs.db', 'desktop.ini', 
            '.tmp', '.temp', '.log'
        }
        
        filename_lower = filename.lower()
        
        # Skip hidden files and system files
        if filename.startswith('.') or filename_lower in skip_files:
            return True
        
        # Skip temporary files
        if filename_lower.endswith(('.tmp', '.temp', '.log', '.bak')):
            return True
        
        return False
    
    def _get_dcm2niix_executable(self) -> Optional[str]:
        """Find the dcm2niix executable path."""
        self.logger.info("Searching for dcm2niix executable...")
        
        # First priority: bundled executable in the 'bin' folder
        # This ensures the application works out-of-the-box without installation
        try:
            # Check if running as PyInstaller bundle
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                bundle_dir = sys._MEIPASS
                self.logger.debug(f"Running as PyInstaller bundle: {bundle_dir}")
            else:
                # Running as normal Python script
                current_dir = os.path.dirname(os.path.abspath(__file__))
                bundle_dir = os.path.dirname(current_dir)
            
            # Check in bin folder
            bundled_dcm2niix = os.path.join(bundle_dir, 'bin', 'dcm2niix.exe')
            self.logger.debug(f"Checking for bundled executable: {bundled_dcm2niix}")
            
            if os.path.isfile(bundled_dcm2niix):
                self.logger.info(f"Found bundled dcm2niix: {bundled_dcm2niix}")
                return bundled_dcm2niix
            else:
                self.logger.debug("Bundled dcm2niix not found in bin folder")
                
            # Also check root of bundle (legacy location)
            if getattr(sys, 'frozen', False):
                legacy_dcm2niix = os.path.join(bundle_dir, 'dcm2niix.exe')
                self.logger.debug(f"Checking legacy location: {legacy_dcm2niix}")
                if os.path.isfile(legacy_dcm2niix):
                    self.logger.info(f"Found dcm2niix in legacy location: {legacy_dcm2niix}")
                    return legacy_dcm2niix
                    
        except Exception as e:
            self.logger.warning(f"Error checking for bundled dcm2niix: {e}")
        
        # Second priority: virtual environment
        venv_path = os.environ.get('VIRTUAL_ENV')
        if venv_path:
            venv_dcm2niix = os.path.join(venv_path, 'Scripts', 'dcm2niix.exe')
            self.logger.debug(f"Checking virtual environment: {venv_dcm2niix}")
            if os.path.isfile(venv_dcm2niix):
                self.logger.info(f"Found dcm2niix in virtual environment: {venv_dcm2niix}")
                return venv_dcm2niix
            else:
                self.logger.debug("dcm2niix not found in virtual environment")
        else:
            self.logger.debug("No VIRTUAL_ENV environment variable set")
        
        # Third priority: project .venv directory (for development)
        if not getattr(sys, 'frozen', False):
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                venv_dcm2niix = os.path.join(project_root, '.venv', 'Scripts', 'dcm2niix.exe')
                self.logger.debug(f"Checking project .venv: {venv_dcm2niix}")
                if os.path.isfile(venv_dcm2niix):
                    self.logger.info(f"Found dcm2niix in project .venv: {venv_dcm2niix}")
                    return venv_dcm2niix
                else:
                    self.logger.debug("dcm2niix not found in project .venv")
            except Exception as e:
                self.logger.warning(f"Error checking project .venv: {e}")
        
        # Fourth priority: system PATH
        self.logger.debug("Checking system PATH for dcm2niix")
        try:
            result = subprocess.run(
                ["dcm2niix", "-h"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                self.logger.info("Found dcm2niix in system PATH")
                return "dcm2niix"
        except subprocess.TimeoutExpired:
            self.logger.warning("dcm2niix in PATH timed out")
        except FileNotFoundError:
            self.logger.debug("dcm2niix not found in system PATH")
        except subprocess.SubprocessError as e:
            self.logger.warning(f"Error checking dcm2niix in PATH: {e}")
        
        self.logger.error("dcm2niix executable not found in any location")
        self.logger.error("INSTALLATION OPTIONS:")
        self.logger.error("  1. Download dcm2niix.exe from https://github.com/rordenlab/dcm2niix/releases")
        
        # Provide appropriate path based on whether running as bundle or not
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
                self.logger.error(f"     and place it in: {os.path.join(app_dir, 'bin', 'dcm2niix.exe')}")
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                self.logger.error(f"     and place it in the 'bin' folder: {os.path.join(project_root, 'bin', 'dcm2niix.exe')}")
        except:
            pass
            
        self.logger.error("  2. Install via pip: pip install dcm2niix")
        self.logger.error("  3. Install via conda: conda install -c conda-forge dcm2niix")
        return None

    def _check_dcm2niix_available(self) -> bool:
        """Check if dcm2niix is available in the system."""
        return self._get_dcm2niix_executable() is not None
    
    def _run_dcm2niix(self, input_folder: str, output_folder: str) -> Optional[str]:
        """
        Run dcm2niix conversion with optimal settings for CBCT.
        
        Args:
            input_folder: Path to DICOM folder
            output_folder: Path to output folder
            
        Returns:
            Path to generated NIfTI file
        """
        try:
            # Get the dcm2niix executable
            dcm2niix_exe = self._get_dcm2niix_executable()
            if not dcm2niix_exe:
                self.logger.error("dcm2niix executable not found")
                return None
            
            # dcm2niix parameters:
            # -z y: compress output (gzip)
            # -b n: don't create BIDS sidecar JSON (we want to keep metadata in NIfTI header)
            # -ba n: don't anonymize (keep all metadata)
            # -f: output filename format (use default patient/study info)
            # -o: output directory
            # -v: verbose output for debugging
            
            cmd = [
                dcm2niix_exe,
                "-z", "y",      # Compress output
                "-b", "n",      # No BIDS JSON
                "-ba", "n",     # No anonymization (keep metadata)
                "-v", "1",      # Verbose output
                "-o", output_folder,
                input_folder
            ]
            
            self.logger.info(f"Running dcm2niix command: {' '.join(cmd)}")
            
            # Run the conversion, suppress terminal window on Windows
            creationflags = 0
            if sys.platform.startswith('win'):
                creationflags = subprocess.CREATE_NO_WINDOW
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                creationflags=creationflags
            )
            
            # Log the results regardless of return code
            self.logger.info(f"dcm2niix stdout: {result.stdout}")
            if result.stderr:
                self.logger.warning(f"dcm2niix stderr: {result.stderr}")
            
            # Check if NIfTI files were generated regardless of return code
            # dcm2niix can return non-zero exit codes for warnings but still produce valid files
            nifti_files = list(Path(output_folder).glob("*.nii.gz"))
            
            if nifti_files:
                # Return the first (and usually only) NIfTI file
                if result.returncode != 0:
                    self.logger.warning(f"dcm2niix returned code {result.returncode} but produced output file")
                return str(nifti_files[0])
            
            # Only try fallback if no files were produced
            if result.returncode != 0:
                self.logger.error(f"dcm2niix failed with return code {result.returncode}")
                self.logger.error(f"stderr: {result.stderr}")
                
                # Try with python -m dcm2niix as fallback
                return self._run_dcm2niix_python(input_folder, output_folder)
            
            self.logger.error("No NIfTI files were generated")
            return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("dcm2niix conversion timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error running dcm2niix: {e}")
            return None
    
    def _run_dcm2niix_python(self, input_folder: str, output_folder: str) -> Optional[str]:
        """
        Fallback: Run dcm2niix using python -m dcm2niix.
        """
        try:
            cmd = [
                "python", "-m", "dcm2niix",
                "-z", "y",      # Compress output
                "-b", "n",      # No BIDS JSON
                "-ba", "n",     # No anonymization
                "-v", "1",      # Verbose
                "-o", output_folder,
                input_folder
            ]
            
            self.logger.info(f"Running fallback command: {' '.join(cmd)}")
            
            # Run the conversion, suppress terminal window on Windows
            creationflags = 0
            if sys.platform.startswith('win'):
                creationflags = subprocess.CREATE_NO_WINDOW
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=creationflags
            )
            
            if result.returncode != 0:
                self.logger.error(f"Python dcm2niix failed: {result.stderr}")
                return None
            
            # Find generated NIfTI file
            nifti_files = list(Path(output_folder).glob("*.nii.gz"))
            return str(nifti_files[0]) if nifti_files else None
            
        except Exception as e:
            self.logger.error(f"Error running python dcm2niix: {e}")
            return None
    
    def get_conversion_info(self, nifti_path: str) -> dict:
        """
        Get information about the converted NIfTI file.
        
        Args:
            nifti_path: Path to NIfTI file
            
        Returns:
            Dictionary with file information
        """
        try:
            if not os.path.exists(nifti_path):
                return {}
            
            file_stats = os.stat(nifti_path)
            
            return {
                "file_path": nifti_path,
                "file_size": file_stats.st_size,
                "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "created": file_stats.st_ctime,
                "compressed": nifti_path.endswith('.gz'),
                "format": "NIfTI compressed" if nifti_path.endswith('.gz') else "NIfTI"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting NIfTI info: {e}")
            return {}
    
    def cleanup_tmp_folder(self, project_root: str, patient_id: str = None, keep_files: bool = True) -> bool:
        """
        Clean up temporary files in the project-level tmp folder.
        
        Args:
            project_root: Path to project root folder
            patient_id: Specific patient ID to clean up (if None, cleans all)
            keep_files: Whether to keep the final NIfTI and zip files
            
        Returns:
            True if cleanup was successful
        """
        try:
            tmp_folder = os.path.join(project_root, "tmp")
            
            if not os.path.exists(tmp_folder):
                return True
            
            if patient_id:
                # Clean up specific patient files
                patterns = [f"{patient_id}.nii.gz", f"{patient_id}.zip"]
                for pattern in patterns:
                    file_path = os.path.join(tmp_folder, pattern)
                    if os.path.exists(file_path) and not keep_files:
                        os.remove(file_path)
            else:
                # Clean up all temporary files if not keeping them
                if not keep_files:
                    shutil.rmtree(tmp_folder)
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up tmp folder: {e}")
            return False
    
    def get_patient_files_info(self, project_root: str, patient_id: str) -> dict:
        """
        Get information about patient files (NIfTI and zip).
        
        Args:
            project_root: Path to project root folder
            patient_id: Patient ID
            
        Returns:
            Dictionary with file information
        """
        try:
            tmp_folder = os.path.join(project_root, "tmp")
            info = {}
            
            # Check NIfTI file
            nifti_path = os.path.join(tmp_folder, f"{patient_id}.nii.gz")
            if os.path.exists(nifti_path):
                info['nifti'] = self.get_conversion_info(nifti_path)
            
            # Check zip file
            zip_path = os.path.join(tmp_folder, f"{patient_id}.zip")
            if os.path.exists(zip_path):
                file_stats = os.stat(zip_path)
                info['zip'] = {
                    "file_path": zip_path,
                    "file_size": file_stats.st_size,
                    "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                    "created": file_stats.st_ctime,
                    "format": "ZIP Archive"
                }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting patient files info: {e}")
            return {}