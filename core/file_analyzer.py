"""
File analysis module for detecting and categorizing dental data files.
"""

import os
import re
from typing import Optional, Tuple, List
from PIL import Image
import pydicom
import logging

# Try to import magic for MIME type detection (optional)
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic-bin not available. MIME type detection will be disabled.")

from .models import DataType, FileData, PatientData, MatchStatus
from .cbct_converter import CBCTConverter
from .match_cache import MatchCache

class FileAnalyzer:
    """Analyzes files to determine their data type based on various criteria."""
    
    def _should_ignore_file(self, filename: str) -> bool:
        """Check if a file should be ignored during analysis."""
        filename_lower = filename.lower()
        
        # Ignore all files starting with "."
        if filename.startswith('.'):
            return True
            
        # Ignore specific system files
        system_files = {'thumbs.db', 'desktop.ini', 'icon\r'}
        if filename_lower in system_files:
            return True
            
        return False
    
    # Folder name patterns
    CBCT_FOLDER_PATTERNS = [
        r'cbct',
        r'cone.*beam',
        r'3d',
        r'dicom',
        r'ct'
    ]
    
    IOS_FOLDER_PATTERNS = [
        r'scansioni',
        r'scan',
        r'ios',
        r'intraoral.*scan',
        r'stl'
    ]
    
    # File name patterns
    UPPER_PATTERNS = [
        r'upper',
        r'superiore',
        r'sup',
        r'mascella',
        r'mascellare',  # Added Italian variant
        r'maxilla',
        r'maxillary',
        r'maxillari',   # Added Italian variant
        r'maxillar',    # Added variant
        r'upperjaw',
        r'upper.*jaw'
    ]
    
    LOWER_PATTERNS = [
        r'lower',
        r'inferiore', 
        r'inf',
        r'mandibola',
        r'mandibolar',  # Added variant
        r'mandible',
        r'mandibular',  # Added English variant
        r'lowerjaw',
        r'lower.*jaw'
    ]
    
    TELERADIO_PATTERNS = [
        r'tele',
        r'laterale',
        r'lateral',
        r'cefalometria',
        r'cephalometric'
    ]
    
    ORTHO_PATTERNS = [
        r'orto',
        r'ortho',
        r'panoramic',
        r'opt',
        r'ortopantomografia'
    ]
    
    def __init__(self):
        # Initialize MIME type detector if available
        if MAGIC_AVAILABLE:
            self.mime = magic.Magic(mime=True)
        else:
            self.mime = None
            
        self.cbct_converter = CBCTConverter()
        self.match_cache = MatchCache()
        self.logger = logging.getLogger(__name__)
        
        # Clean up expired cache entries on initialization (only for centralized cache)
        if self.match_cache.centralized_cache:
            self.match_cache.cleanup_expired_entries()
    
    def analyze_patient_folder(self, folder_path: str, use_cache: bool = True) -> PatientData:
        """Analyze a patient folder and categorize all files.
        
        Args:
            folder_path: Path to the patient folder
            use_cache: Whether to use cached results if available
            
        Returns:
            PatientData with categorized files
        """
        self.logger.info(f"Analyzing patient folder: {folder_path}")
        
        # Try to load from cache first
        if use_cache:
            cached_data = self.match_cache.get_cached_matches(folder_path)
            if cached_data is not None:
                self.logger.info(f"Using cached matches for {os.path.basename(folder_path)}")
                # Still need to run post-processing for CBCT conversion and zip creation
                self._run_post_processing(cached_data)
                return cached_data
        
        # Perform fresh analysis
        patient_id = os.path.basename(folder_path)
        patient_data = PatientData(patient_id=patient_id, folder_path=folder_path)
        
        if not os.path.exists(folder_path):
            patient_data.validation_errors.append(f"Folder does not exist: {folder_path}")
            return patient_data
        
        # First, find CBCT and IOS folders
        cbct_folder, ios_folder = self._find_special_folders(folder_path)
        patient_data.cbct_folder = cbct_folder
        patient_data.ios_folder = ios_folder
        
        # Analyze CBCT folder
        if cbct_folder:
            patient_data.cbct_files = self._analyze_cbct_folder(cbct_folder)
        
        # Analyze IOS folder
        if ios_folder:
            ios_upper, ios_lower = self._analyze_ios_folder(ios_folder)
            patient_data.ios_upper = ios_upper
            patient_data.ios_lower = ios_lower
        
        # Analyze main folder files
        main_files = self._get_files_in_folder(folder_path, exclude_folders=[cbct_folder, ios_folder])
        self._categorize_main_folder_files(main_files, patient_data)
        
        # Run post-processing
        self._run_post_processing(patient_data)
        
        # Cache the results for future use
        if use_cache:
            self.match_cache.cache_matches(patient_data)
        
        return patient_data
    
    def _run_post_processing(self, patient_data: PatientData):
        """Run post-processing steps like CBCT conversion and zip creation."""
        # Automatically convert CBCT to NIfTI if CBCT data is found
        if patient_data.cbct_files and patient_data.cbct_folder:
            project_root = os.path.dirname(patient_data.folder_path)
            self._convert_cbct_to_nifti(patient_data, project_root)
        
        # Create patient data zip package
        project_root = os.path.dirname(patient_data.folder_path)
        self._create_patient_zip(patient_data, project_root)
    
    def _find_special_folders(self, folder_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Find CBCT and IOS folders within the patient folder."""
        cbct_folder = None
        ios_folder = None
        
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    item_lower = item.lower()
                    
                    # Skip tmp folders - they should not be considered as special folders
                    if item_lower == 'tmp':
                        continue
                    
                    # Check for CBCT folder
                    if not cbct_folder and self._matches_patterns(item_lower, self.CBCT_FOLDER_PATTERNS):
                        cbct_folder = item_path
                    
                    # Check for IOS folder
                    if not ios_folder and self._matches_patterns(item_lower, self.IOS_FOLDER_PATTERNS):
                        ios_folder = item_path
        except PermissionError:
            pass
        
        return cbct_folder, ios_folder
    
    def _analyze_cbct_folder(self, cbct_folder: str) -> List[FileData]:
        """Analyze CBCT folder and return DICOM files."""
        cbct_files = []
        
        for root, dirs, files in os.walk(cbct_folder):
            for file in files:
                # Skip files that should be ignored
                if self._should_ignore_file(file):
                    continue
                    
                file_path = os.path.join(root, file)
                if self._is_dicom_file(file_path):
                    file_data = FileData(
                        path=file_path,
                        data_type=DataType.CBCT_DICOM,
                        confidence=0.9,
                        status=MatchStatus.MATCHED
                    )
                    cbct_files.append(file_data)
        
        return cbct_files
    
    def _analyze_ios_folder(self, ios_folder: str) -> Tuple[Optional[FileData], Optional[FileData]]:
        """Analyze IOS folder and return upper and lower STL files."""
        stl_files = []
        
        try:
            for file in os.listdir(ios_folder):
                # Skip files that should be ignored
                if self._should_ignore_file(file):
                    continue
                    
                file_path = os.path.join(ios_folder, file)
                if os.path.isfile(file_path) and file.lower().endswith('.stl'):
                    stl_files.append(file_path)
        except PermissionError:
            pass
        
        if len(stl_files) == 0:
            return None, None
        elif len(stl_files) == 1:
            # Only one STL file - try to determine if it's upper or lower based on filename
            filename = os.path.basename(stl_files[0]).lower()
            if self._matches_patterns(filename, self.UPPER_PATTERNS):
                file_data = FileData(
                    path=stl_files[0],
                    data_type=DataType.IOS_UPPER,
                    confidence=0.7,
                    status=MatchStatus.MATCHED
                )
                return file_data, None
            elif self._matches_patterns(filename, self.LOWER_PATTERNS):
                file_data = FileData(
                    path=stl_files[0],
                    data_type=DataType.IOS_LOWER,
                    confidence=0.7,
                    status=MatchStatus.MATCHED
                )
                return None, file_data
            else:
                # Ambiguous single file
                file_data = FileData(
                    path=stl_files[0],
                    data_type=None,
                    confidence=0.0,
                    status=MatchStatus.AMBIGUOUS
                )
                return file_data, None
        else:
            # Try to match upper and lower
            upper_file = None
            lower_file = None
            unmatched_files = []
            
            for file_path in stl_files:
                filename = os.path.basename(file_path).lower()
                
                if self._matches_patterns(filename, self.UPPER_PATTERNS):
                    if upper_file is None:
                        upper_file = FileData(
                            path=file_path,
                            data_type=DataType.IOS_UPPER,
                            confidence=0.8,
                            status=MatchStatus.MATCHED
                        )
                    else:
                        # Multiple upper files - keep the first, mark others as ambiguous
                        unmatched_files.append(file_path)
                elif self._matches_patterns(filename, self.LOWER_PATTERNS):
                    if lower_file is None:
                        lower_file = FileData(
                            path=file_path,
                            data_type=DataType.IOS_LOWER,
                            confidence=0.8,
                            status=MatchStatus.MATCHED
                        )
                    else:
                        # Multiple lower files - keep the first, mark others as ambiguous
                        unmatched_files.append(file_path)
                else:
                    unmatched_files.append(file_path)
            
            # If we have exactly 2 files and haven't matched them by name,
            # try to assign them based on alphabetical order as a fallback
            if len(stl_files) == 2 and upper_file is None and lower_file is None:
                sorted_files = sorted(stl_files)
                upper_file = FileData(
                    path=sorted_files[0],
                    data_type=DataType.IOS_UPPER,
                    confidence=0.3,  # Lower confidence since it's a guess
                    status=MatchStatus.MATCHED
                )
                lower_file = FileData(
                    path=sorted_files[1],
                    data_type=DataType.IOS_LOWER,
                    confidence=0.3,
                    status=MatchStatus.MATCHED
                )
            
            return upper_file, lower_file
    
    def _categorize_main_folder_files(self, files: List[str], patient_data: PatientData):
        """Categorize files in the main patient folder."""
        for file_path in files:
            file_data = self._analyze_single_file(file_path)
            
            if file_data.data_type == DataType.TELERADIOGRAPHY:
                if patient_data.teleradiography is None:
                    patient_data.teleradiography = file_data
                else:
                    # Multiple potential teleradiography files
                    file_data.status = MatchStatus.AMBIGUOUS
                    patient_data.unmatched_files.append(file_data)
            
            elif file_data.data_type == DataType.ORTHOPANTOMOGRAPHY:
                if patient_data.orthopantomography is None:
                    patient_data.orthopantomography = file_data
                else:
                    # Multiple potential orthopantomography files
                    file_data.status = MatchStatus.AMBIGUOUS
                    patient_data.unmatched_files.append(file_data)
            
            elif file_data.data_type == DataType.INTRAORAL_PHOTO:
                patient_data.intraoral_photos.append(file_data)
            
            else:
                patient_data.unmatched_files.append(file_data)
    
    def _analyze_single_file(self, file_path: str) -> FileData:
        """Analyze a single file to determine its type."""
        filename = os.path.basename(file_path).lower()
        extension = os.path.splitext(filename)[1].lower()
        
        # Check if it's an image file
        if extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
            # Try to determine the type based on filename
            if self._matches_patterns(filename, self.TELERADIO_PATTERNS):
                return FileData(
                    path=file_path,
                    data_type=DataType.TELERADIOGRAPHY,
                    confidence=0.7,
                    status=MatchStatus.MATCHED
                )
            elif self._matches_patterns(filename, self.ORTHO_PATTERNS):
                return FileData(
                    path=file_path,
                    data_type=DataType.ORTHOPANTOMOGRAPHY,
                    confidence=0.7,
                    status=MatchStatus.MATCHED
                )
            else:
                # Analyze image properties
                try:
                    image_type = self._analyze_image_properties(file_path)
                    if image_type:
                        confidence = 0.6 if image_type in [DataType.TELERADIOGRAPHY, DataType.ORTHOPANTOMOGRAPHY] else 0.8
                        return FileData(
                            path=file_path,
                            data_type=image_type,
                            confidence=confidence,
                            status=MatchStatus.MATCHED
                        )
                except:
                    pass
                
                # Default to intraoral photo for unidentified images
                return FileData(
                    path=file_path,
                    data_type=DataType.INTRAORAL_PHOTO,
                    confidence=0.5,
                    status=MatchStatus.MATCHED
                )
        
        # Unknown file type
        return FileData(
            path=file_path,
            data_type=None,
            confidence=0.0,
            status=MatchStatus.UNMATCHED
        )
    
    def _analyze_image_properties(self, file_path: str) -> Optional[DataType]:
        """Analyze image properties to determine type using advanced RGB analysis."""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                aspect_ratio = width / height
                
                # Perform detailed RGB analysis
                rgb_analysis = self._classify_image_by_content(img)
                
                # Check if it's grayscale
                is_grayscale = img.mode in ['L', '1'] or (img.mode == 'RGB' and self._is_grayscale_image(img))
                
                if is_grayscale:
                    # Square-ish aspect ratio -> likely teleradiography
                    if 0.8 <= aspect_ratio <= 1.2:
                        return DataType.TELERADIOGRAPHY
                    # Rectangular aspect ratio -> likely orthopantomography
                    elif aspect_ratio > 1.5 or aspect_ratio < 0.7:
                        return DataType.ORTHOPANTOMOGRAPHY
                else:
                    # Use RGB analysis for color images
                    if rgb_analysis:
                        return rgb_analysis
                    # Fallback to intraoral photo for color images
                    return DataType.INTRAORAL_PHOTO
        except Exception:
            pass
        
        return None
    
    def _classify_image_by_content(self, img: Image.Image) -> Optional[DataType]:
        """Classify image based on RGB color analysis and content characteristics."""
        try:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get image statistics
            width, height = img.size
            total_pixels = width * height
            
            # Sample pixels for analysis (use a grid for better coverage)
            sample_points = []
            step_x = max(1, width // 20)  # Sample every 20th pixel horizontally
            step_y = max(1, height // 20)  # Sample every 20th pixel vertically
            
            for x in range(0, width, step_x):
                for y in range(0, height, step_y):
                    sample_points.append((x, y))
            
            # Analyze color characteristics
            red_values = []
            green_values = []
            blue_values = []
            brightness_values = []
            saturation_values = []
            
            for x, y in sample_points:
                r, g, b = img.getpixel((x, y))
                red_values.append(r)
                green_values.append(g)
                blue_values.append(b)
                
                # Calculate brightness (luminance)
                brightness = 0.299 * r + 0.587 * g + 0.114 * b
                brightness_values.append(brightness)
                
                # Calculate saturation
                max_rgb = max(r, g, b)
                min_rgb = min(r, g, b)
                if max_rgb > 0:
                    saturation = (max_rgb - min_rgb) / max_rgb
                else:
                    saturation = 0
                saturation_values.append(saturation)
            
            if not sample_points:
                return None
            
            # Calculate statistics
            avg_red = sum(red_values) / len(red_values)
            avg_green = sum(green_values) / len(green_values)
            avg_blue = sum(blue_values) / len(blue_values)
            avg_brightness = sum(brightness_values) / len(brightness_values)
            avg_saturation = sum(saturation_values) / len(saturation_values)
            
            # Calculate color variance
            red_variance = sum((r - avg_red) ** 2 for r in red_values) / len(red_values)
            green_variance = sum((g - avg_green) ** 2 for g in green_values) / len(green_values)
            blue_variance = sum((b - avg_blue) ** 2 for b in blue_values) / len(blue_values)
            
            # Histogram-based grayscale detection
            # Check if RGB channels are highly correlated (screen photos of grayscale images)
            try:
                hist_r = img.split()[0].histogram()
                hist_g = img.split()[1].histogram()
                hist_b = img.split()[2].histogram()
                
                # Calculate histogram correlation
                total_diff_rg = sum(abs(hist_r[i] - hist_g[i]) for i in range(256))
                total_diff_gb = sum(abs(hist_g[i] - hist_b[i]) for i in range(256))
                total_diff_rb = sum(abs(hist_r[i] - hist_b[i]) for i in range(256))
                
                total_pixels = img.width * img.height
                normalized_diff_rg = total_diff_rg / total_pixels
                normalized_diff_gb = total_diff_gb / total_pixels
                normalized_diff_rb = total_diff_rb / total_pixels
                avg_hist_diff = (normalized_diff_rg + normalized_diff_gb + normalized_diff_rb) / 3
                
                # If histogram indicates near-grayscale, it's likely a screen photo
                # of teleradiography or panoramic image
                is_near_grayscale = avg_hist_diff < 0.3
            except:
                is_near_grayscale = False
            
            # Detect dominant colors
            red_dominant = avg_red > avg_green and avg_red > avg_blue
            pink_red_tones = avg_red > 150 and avg_green < 120 and avg_blue < 120
            
            # Classify based on characteristics
            
            # 1. Screen photos of X-rays/panoramic should be detected as grayscale
            #    Even if they have some color saturation from screen photography
            if is_near_grayscale and avg_hist_diff < 0.2:
                # Very likely a screen photo of a grayscale medical image
                # Don't classify as intraoral
                return None
            
            # 2. Intraoral photos typically have:
            #    - High color saturation (teeth, gums, oral tissues)
            #    - Pink/red tones from gums and oral tissues
            #    - Good color variance (different oral structures)
            #    - Moderate to high brightness
            #    - NOT near-grayscale on histogram analysis
            if (avg_saturation > 0.3 and 
                not is_near_grayscale and
                (pink_red_tones or red_dominant) and 
                avg_brightness > 80 and 
                max(red_variance, green_variance, blue_variance) > 1000):
                return DataType.INTRAORAL_PHOTO
            
            # 3. Facial photos typically have:
            #    - Moderate saturation
            #    - Skin tones (balanced RGB with slight red/yellow bias)
            #    - Good color variance (face, background, clothing)
            #    - NOT near-grayscale on histogram analysis
            skin_tone_detected = (
                120 < avg_red < 200 and 
                100 < avg_green < 180 and 
                80 < avg_blue < 160 and
                avg_red > avg_green > avg_blue
            )
            
            if (0.2 < avg_saturation < 0.6 and 
                not is_near_grayscale and
                skin_tone_detected and 
                avg_brightness > 60 and
                max(red_variance, green_variance, blue_variance) > 800):
                return DataType.FACIAL_PHOTO
            
            # 4. X-rays would be mostly grayscale (handled elsewhere)
            # 5. If high saturation but no specific characteristics, assume intraoral
            #    Only if NOT near-grayscale
            if avg_saturation > 0.4 and not is_near_grayscale:
                return DataType.INTRAORAL_PHOTO
                
        except Exception as e:
            # Log error for debugging
            print(f"Error in RGB analysis: {e}")
            pass
        
        return None

    def _is_grayscale_image(self, img: Image.Image) -> bool:
        """
        Check if an RGB image is actually grayscale.
        Uses histogram analysis to detect screen photos of grayscale images.
        """
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Use histogram analysis for better detection
        try:
            # Get histograms for each channel
            hist_r = img.split()[0].histogram()
            hist_g = img.split()[1].histogram()
            hist_b = img.split()[2].histogram()
            
            # Calculate correlation between channels
            # For truly grayscale or near-grayscale (screen photos), 
            # the RGB histograms should be very similar
            total_diff_rg = sum(abs(hist_r[i] - hist_g[i]) for i in range(256))
            total_diff_gb = sum(abs(hist_g[i] - hist_b[i]) for i in range(256))
            total_diff_rb = sum(abs(hist_r[i] - hist_b[i]) for i in range(256))
            
            # Calculate total pixels for normalization
            total_pixels = img.width * img.height
            
            # Normalize differences
            normalized_diff_rg = total_diff_rg / total_pixels
            normalized_diff_gb = total_diff_gb / total_pixels
            normalized_diff_rb = total_diff_rb / total_pixels
            
            # Average normalized difference
            avg_diff = (normalized_diff_rg + normalized_diff_gb + normalized_diff_rb) / 3
            
            # Threshold for grayscale detection
            # Lower threshold catches screen photos of grayscale images
            # Values below 0.3 indicate near-grayscale (including screen photos)
            # Values above 0.3 indicate truly colored images (intraoral photos)
            is_grayscale = avg_diff < 0.3
            
            return is_grayscale
            
        except Exception as e:
            # Fallback to pixel sampling if histogram fails
            print(f"Histogram analysis failed, using pixel sampling: {e}")
            sample_size = min(100, img.width * img.height)
            for i in range(0, sample_size, max(1, sample_size // 10)):
                x = i % img.width
                y = i // img.width
                r, g, b = img.getpixel((x, y))
                if abs(r - g) > 10 or abs(g - b) > 10 or abs(r - b) > 10:
                    return False
            return True
    
    def _is_dicom_file(self, file_path: str) -> bool:
        """Check if a file is a DICOM file."""
        # First check file extension
        extension = os.path.splitext(file_path)[1].lower()
        if extension in ['.dcm', '.dicom']:
            return True
            
        try:
            # Try to read as DICOM
            pydicom.dcmread(file_path, force=True)
            return True
        except:
            # Check MIME type if magic is available
            if self.mime:
                try:
                    mime_type = self.mime.from_file(file_path)
                    if 'dicom' in mime_type.lower():
                        return True
                except:
                    pass
        
        return False
    
    def _get_files_in_folder(self, folder_path: str, exclude_folders: List[Optional[str]] = None) -> List[str]:
        """Get all files in a folder, excluding specified subfolders."""
        files = []
        exclude_folders = [f for f in (exclude_folders or []) if f is not None]
        
        try:
            for item in os.listdir(folder_path):
                # Skip files that should be ignored
                if self._should_ignore_file(item):
                    continue
                    
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    files.append(item_path)
                elif os.path.isdir(item_path) and item_path not in exclude_folders:
                    # Skip tmp folders - they should not be scanned for patient files
                    if item.lower() == 'tmp':
                        continue
                    # Recursively get files from subdirectories (except excluded ones)
                    files.extend(self._get_files_in_folder(item_path))
        except PermissionError:
            pass
        
        return files
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given regex patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _convert_cbct_to_nifti(self, patient_data: PatientData, project_root: str) -> None:
        """
        Automatically convert CBCT DICOM files to NIfTI format.
        
        Args:
            patient_data: PatientData object with CBCT information
            project_root: Path to the project root folder
        """
        try:
            self.logger.info(f"Starting automatic CBCT to NIfTI conversion for patient {patient_data.patient_id}")
            
            # Set conversion status to converting
            patient_data.nifti_conversion_status = "converting"
            
            # Perform the conversion using new method signature
            nifti_path = self.cbct_converter.convert_cbct_to_nifti(
                patient_data.cbct_folder,
                patient_data.patient_id,
                project_root
            )
            
            if nifti_path and os.path.exists(nifti_path):
                # Success
                patient_data.nifti_conversion_path = nifti_path
                patient_data.nifti_conversion_status = "completed"
                patient_data.nifti_conversion_info = self.cbct_converter.get_conversion_info(nifti_path)
                
                self.logger.info(f"Successfully converted CBCT to NIfTI for patient {patient_data.patient_id}: {nifti_path}")
                
            else:
                # Failed
                patient_data.nifti_conversion_status = "failed"
                self.logger.error(f"CBCT to NIfTI conversion failed for patient {patient_data.patient_id}")
                
        except Exception as e:
            # Error
            patient_data.nifti_conversion_status = "failed"
            self.logger.error(f"Error during CBCT to NIfTI conversion for patient {patient_data.patient_id}: {e}")
            
            # Add error to patient validation errors
            patient_data.validation_errors.append(f"CBCT conversion failed: {str(e)}")
    
    def _create_patient_zip(self, patient_data: PatientData, project_root: str) -> None:
        """
        Create a zip package containing all patient data.
        
        Args:
            patient_data: PatientData object
            project_root: Path to the project root folder
        """
        try:
            self.logger.info(f"Creating patient data package for {patient_data.patient_id}")
            
            # Create the zip package
            zip_path = self.cbct_converter.create_patient_zip(
                patient_data.folder_path,
                patient_data.patient_id,
                project_root
            )
            
            if zip_path and os.path.exists(zip_path):
                # Success
                patient_data.zip_package_path = zip_path
                
                # Get zip file info
                files_info = self.cbct_converter.get_patient_files_info(project_root, patient_data.patient_id)
                if 'zip' in files_info:
                    patient_data.zip_package_info = files_info['zip']
                
                self.logger.info(f"Successfully created patient package for {patient_data.patient_id}: {zip_path}")
                
            else:
                self.logger.error(f"Failed to create patient package for {patient_data.patient_id}")
                
        except Exception as e:
            self.logger.error(f"Error creating patient package for {patient_data.patient_id}: {e}")
            
            # Add error to patient validation errors
            patient_data.validation_errors.append(f"Package creation failed: {str(e)}")
    
    # Cache management methods
    
    def invalidate_cache(self, folder_path: str):
        """Invalidate cache for a specific patient folder.
        
        This should be called when user makes manual changes to file assignments.
        
        Args:
            folder_path: Path to the patient folder whose cache should be invalidated
        """
        self.match_cache.invalidate_cache(folder_path)
        self.logger.info(f"Invalidated cache for {folder_path}")
    
    def update_cache(self, patient_data: PatientData):
        """Update cache with new patient data.
        
        This should be called after user makes manual changes to preserve them.
        
        Args:
            patient_data: Updated patient data to cache
        """
        self.match_cache.cache_matches(patient_data)
        self.logger.info(f"Updated cache for {patient_data.patient_id}")
    
    def clear_all_cache(self):
        """Clear all cached matching results."""
        self.match_cache.clear_cache()
        self.logger.info("Cleared all cache entries")
    
    def get_cache_stats(self):
        """Get cache statistics."""
        return self.match_cache.get_cache_stats()
    
    def has_cached_data(self, folder_path: str) -> bool:
        """Check if folder has valid cached data.
        
        Args:
            folder_path: Path to check
            
        Returns:
            True if valid cache exists, False otherwise
        """
        cached_data = self.match_cache.get_cached_matches(folder_path)
        return cached_data is not None
