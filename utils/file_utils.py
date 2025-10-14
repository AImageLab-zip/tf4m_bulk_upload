"""
Utility functions for the dental data management application.
"""

import os
import re
import hashlib
from typing import List, Optional, Tuple
from PIL import Image
import json


def normalize_path(path: str) -> str:
    """Normalize a file path for cross-platform compatibility."""
    return os.path.normpath(os.path.abspath(path))


def get_file_hash(file_path: str) -> Optional[str]:
    """Get MD5 hash of a file."""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None


def get_image_info(image_path: str) -> Optional[dict]:
    """Get basic information about an image file."""
    try:
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "aspect_ratio": img.width / img.height if img.height > 0 else 0
            }
    except Exception:
        return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def is_image_file(file_path: str) -> bool:
    """Check if a file is an image based on extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
    return os.path.splitext(file_path)[1].lower() in image_extensions


def is_dicom_file(file_path: str) -> bool:
    """Check if a file is a DICOM file based on extension."""
    dicom_extensions = {'.dcm', '.dicom', '.dic'}
    return os.path.splitext(file_path)[1].lower() in dicom_extensions


def is_stl_file(file_path: str) -> bool:
    """Check if a file is an STL file."""
    return os.path.splitext(file_path)[1].lower() == '.stl'


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def find_files_by_pattern(directory: str, pattern: str, recursive: bool = True) -> List[str]:
    """Find files matching a regex pattern."""
    matched_files = []
    pattern_regex = re.compile(pattern, re.IGNORECASE)
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if pattern_regex.search(file):
                    matched_files.append(os.path.join(root, file))
    else:
        try:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path) and pattern_regex.search(file):
                    matched_files.append(file_path)
        except PermissionError:
            pass
    
    return matched_files


def load_json_config(config_path: str, default_config: dict = None) -> dict:
    """Load configuration from JSON file."""
    if default_config is None:
        default_config = {}
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults
                merged_config = default_config.copy()
                merged_config.update(config)
                return merged_config
    except Exception:
        pass
    
    return default_config


def save_json_config(config_path: str, config: dict) -> bool:
    """Save configuration to JSON file."""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def validate_directory_structure(root_path: str) -> Tuple[bool, List[str]]:
    """Validate that the directory structure is suitable for analysis."""
    errors = []
    
    if not os.path.exists(root_path):
        errors.append(f"Directory does not exist: {root_path}")
        return False, errors
    
    if not os.path.isdir(root_path):
        errors.append(f"Path is not a directory: {root_path}")
        return False, errors
    
    try:
        # Check if we can read the directory
        os.listdir(root_path)
    except PermissionError:
        errors.append(f"Permission denied to read directory: {root_path}")
        return False, errors
    
    # Check for at least one subdirectory (potential patient folder)
    has_subdirs = False
    try:
        for item in os.listdir(root_path):
            item_path = os.path.join(root_path, item)
            if os.path.isdir(item_path):
                has_subdirs = True
                break
    except PermissionError:
        pass
    
    if not has_subdirs:
        errors.append("No subdirectories found (patient folders)")
    
    return len(errors) == 0, errors


def create_backup_filename(original_path: str) -> str:
    """Create a backup filename with timestamp."""
    directory = os.path.dirname(original_path)
    filename = os.path.basename(original_path)
    name, ext = os.path.splitext(filename)
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{name}_backup_{timestamp}{ext}"
    
    return os.path.join(directory, backup_name)


def is_grayscale_image(image_path: str) -> bool:
    """Check if an image is grayscale."""
    try:
        with Image.open(image_path) as img:
            if img.mode in ['L', '1']:
                return True
            elif img.mode == 'RGB':
                # Sample pixels to check if R=G=B
                img_small = img.resize((50, 50))  # Reduce size for faster processing
                pixels = list(img_small.getdata())
                
                grayscale_count = 0
                for r, g, b in pixels:
                    if abs(r - g) <= 5 and abs(g - b) <= 5 and abs(r - b) <= 5:
                        grayscale_count += 1
                
                # If more than 90% of pixels are grayscale, consider it grayscale
                return (grayscale_count / len(pixels)) > 0.9
    except Exception:
        pass
    
    return False


def extract_keywords_from_filename(filename: str) -> List[str]:
    """Extract potential keywords from a filename."""
    # Remove extension
    name = os.path.splitext(filename)[0]
    
    # Split by common separators
    separators = ['-', '_', ' ', '.', '(', ')', '[', ']']
    keywords = [name.lower()]
    
    for sep in separators:
        new_keywords = []
        for keyword in keywords:
            new_keywords.extend(keyword.split(sep))
        keywords = new_keywords
    
    # Filter out empty strings and very short words
    keywords = [k.strip() for k in keywords if len(k.strip()) > 2]
    
    return list(set(keywords))  # Remove duplicates


def calculate_confidence_score(matches: List[float]) -> float:
    """Calculate confidence score from multiple match scores."""
    if not matches:
        return 0.0
    
    # Use weighted average with diminishing returns
    total_weight = 0
    weighted_sum = 0
    
    for i, score in enumerate(sorted(matches, reverse=True)):
        weight = 1.0 / (i + 1)  # Diminishing weight for additional matches
        weighted_sum += score * weight
        total_weight += weight
    
    return min(1.0, weighted_sum / total_weight) if total_weight > 0 else 0.0
