# Dental Data Management Application

This desktop application helps organize and upload dental patient data including CBCT scans, IOS files, intraoral photos, and radiographs to a Django backend system.

## Features

- **Automated File Analysis**: Intelligently categorizes dental data files based on folder structure, filename patterns, and image content
- **Patient Data Validation**: Ensures each patient has required data types (CBCT, IOS scans, radiographs, etc.)
- **Interactive File Management**: Drag-and-drop interface for resolving ambiguous file classifications
- **Bulk Upload**: Efficient batch uploading to Django API with progress tracking
- **Comprehensive Reporting**: Detailed validation reports and missing data summaries

## Required Data Structure

Each patient folder should contain:

1. **CBCT Folder**: Contains DICOM files from cone beam CT scans
   - Folder name patterns: "CBCT", "cone beam", "3d", "dicom", "ct"
   
2. **IOS Folder**: Contains STL files from intraoral scans
   - Folder name patterns: "scansioni", "scan", "ios", "intraoral scan", "stl"
   - Should contain two files: upper and lower jaw scans
   - Files should contain "upper"/"superiore" or "lower"/"inferiore" in their names

3. **Intraoral Photos**: RGB images of the mouth interior
   - Multiple JPG/PNG files
   - No specific naming convention

4. **Teleradiography**: Grayscale lateral cephalometric image
   - Square aspect ratio (approximately 1:1)
   - JPG/PNG format
   - May contain "tele", "lateral", "cefalometria" in filename

5. **Orthopantomography**: Grayscale panoramic dental X-ray
   - Rectangular aspect ratio
   - JPG/PNG format
   - May contain "ortho", "panoramic", "opt" in filename

## Installation

1. Clone or download this repository
2. Install Python 3.8 or higher
3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. **Open Project Folder**: Select the root folder containing patient subfolders

3. **Analyze**: Click "Analyze" to scan and categorize all patient data

4. **Review Results**: Use the Patient Browser to review detected files and resolve any ambiguities

5. **Configure API**: Go to Settings to configure your Django API endpoint and authentication

6. **Upload**: Use the Upload Manager to batch upload complete patient data

## Configuration

### API Settings
- **Base URL**: Your Django API endpoint (e.g., `http://localhost:8000`)
- **API Key**: Authentication token for API access
- **Timeout**: Request timeout in seconds

### Analysis Settings
- **Confidence Threshold**: Minimum confidence for automatic file classification
- **Folder Patterns**: Customize patterns for detecting CBCT and IOS folders
- **File Matching**: Configure case sensitivity and subfolder inclusion

## File Classification Logic

The application uses multiple methods to classify files:

1. **Folder Structure**: Analyzes folder names using regex patterns
2. **Filename Analysis**: Looks for keywords in filenames
3. **Image Content Analysis**: 
   - Detects grayscale vs color images
   - Analyzes aspect ratios
   - Distinguishes between different radiograph types

## API Integration

The application expects a Django REST API with the following endpoints:

- `GET /api/health/` - Health check
- `GET/POST /api/patients/` - Patient management
- `POST /api/uploads/` - File upload endpoint

### Upload Format

Files are uploaded with the following data:
- `patient_id`: Patient identifier
- `data_type`: Type of dental data (cbct_dicom, ios_upper, ios_lower, etc.)
- `file`: Binary file data
- `filename`: Original filename

## Error Handling

The application provides comprehensive error handling and reporting:

- **Validation Errors**: Missing or incomplete patient data
- **File Conflicts**: Ambiguous file classifications
- **Upload Failures**: Network or server errors during upload
- **Progress Tracking**: Real-time upload progress and ETA

## Troubleshooting

### Common Issues

1. **"No patients found"**: Ensure patient folders are direct subfolders of the selected root folder

2. **"Files not detected"**: Check folder naming conventions and file extensions

3. **"API connection failed"**: Verify Django server is running and API settings are correct

4. **"Upload timeout"**: Increase timeout setting for large files

### Log Files

Upload logs are available in the Upload Manager tab and can be saved for debugging.

## Development

### Project Structure
```
dental_data_manager/
├── main.py                 # Application entry point
├── core/                   # Core business logic
│   ├── models.py          # Data models
│   ├── file_analyzer.py   # File analysis logic
│   ├── project_manager.py # Project coordination
│   └── api_client.py      # API communication
├── gui/                    # User interface
│   ├── main_window.py     # Main application window
│   ├── patient_browser.py # Patient data browser
│   ├── upload_manager.py  # Upload management
│   └── settings_dialog.py # Configuration dialog
└── utils/                  # Utility functions
```

### Adding New File Types

To support additional dental data types:

1. Add new `DataType` enum value in `models.py`
2. Update file analysis patterns in `file_analyzer.py`
3. Add UI elements in `patient_browser.py`
4. Update API client upload logic

## License

This software is developed for TF4M dental data management purposes.
