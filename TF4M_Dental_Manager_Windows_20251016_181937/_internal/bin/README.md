# Bundled Executables

This folder contains standalone executables that are bundled with the TF4M application.

## dcm2niix.exe

**Purpose:** Converts DICOM files (CBCT scans) to NIfTI format (.nii.gz)

**Download:** https://github.com/rordenlab/dcm2niix/releases

### Installation Instructions:

1. Go to https://github.com/rordenlab/dcm2niix/releases
2. Download the latest Windows release (e.g., `dcm2niix_win.zip`)
3. Extract `dcm2niix.exe` from the zip file
4. Place `dcm2niix.exe` in this `bin` folder

### Current Status:
- [ ] dcm2niix.exe is NOT present (needs to be added)
- Once added, the application will automatically use this bundled version
- No user installation required!

### Version Information:
It's recommended to use dcm2niix version v1.0.20211006 or later.

### Alternative:
If dcm2niix.exe is not present in this folder, the application will try to find it in:
1. The bundled `bin` folder (this folder) - **RECOMMENDED**
2. Python virtual environment
3. System PATH

For distribution, make sure to include dcm2niix.exe in this folder!
