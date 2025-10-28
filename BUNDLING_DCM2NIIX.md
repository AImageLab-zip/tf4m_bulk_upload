# Bundling dcm2niix with TF4M Application

## Overview

The TF4M Dental Manager application requires `dcm2niix` to convert DICOM files (CBCT scans) to NIfTI format. To provide a seamless user experience, dcm2niix is bundled with the application so end users don't need to install it separately.

## Quick Setup

### Automatic (Recommended)
```powershell
.\setup_dcm2niix.ps1
```

This PowerShell script will:
1. Download the latest dcm2niix from GitHub
2. Extract and place it in the `bin` folder
3. Verify it works correctly

### Manual Setup

1. Download dcm2niix from: https://github.com/rordenlab/dcm2niix/releases
2. For Windows: Download `dcm2niix_win.zip`
3. Extract `dcm2niix.exe` from the zip file
4. Place it in `bin/dcm2niix.exe` (create the `bin` folder if it doesn't exist)

## How It Works

### Development Mode (Running from Source)

When running from source (`python main.py`), the application searches for dcm2niix in this order:

1. **bin folder** (RECOMMENDED): `<project_root>/bin/dcm2niix.exe`
2. Virtual environment: `<venv>/Scripts/dcm2niix.exe`
3. Project .venv: `<project_root>/.venv/Scripts/dcm2niix.exe`
4. System PATH

### Production Mode (PyInstaller Bundle)

When running as a compiled executable, the application searches in this order:

1. **Bundled bin folder**: `<app_dir>/bin/dcm2niix.exe`
2. Legacy location: `<app_dir>/dcm2niix.exe`
3. System PATH

The PyInstaller spec file (`TF4M_Dental_Manager.spec`) is configured to automatically include the entire `bin` folder in the bundle.

## Building the Application

### Prerequisites
1. Ensure `bin/dcm2niix.exe` exists (run `setup_dcm2niix.ps1`)
2. Install PyInstaller: `pip install pyinstaller`

### Build Process

```powershell
# 1. Setup dcm2niix (if not already done)
.\setup_dcm2niix.ps1

# 2. Build the application
.\build_windows.ps1

# Or manually:
pyinstaller TF4M_Dental_Manager.spec --clean
```

The build process will:
- Include all files from the `bin` folder in the bundle
- Place them in `dist/TF4M_Dental_Manager/bin/`
- Make them accessible to the application at runtime

### Verification

After building, verify that dcm2niix is included:

```powershell
# Check if the file exists in the distribution
Test-Path "dist\TF4M_Dental_Manager\bin\dcm2niix.exe"

# Run the built application and check the logs
.\dist\TF4M_Dental_Manager\TF4M_Dental_Manager.exe

# Check the log file:
Get-Content "dist\TF4M_Dental_Manager\logs\tf4m_app.log"
# Look for lines like: "Found bundled dcm2niix: ..."
```

## Distribution

When distributing the application:

### Option 1: Folder Distribution
Simply zip the entire `dist/TF4M_Dental_Manager` folder. It contains:
```
TF4M_Dental_Manager/
├── TF4M_Dental_Manager.exe  (main application)
├── bin/
│   └── dcm2niix.exe          (bundled tool)
├── _internal/                (Python runtime and dependencies)
└── ...other files
```

### Option 2: Installer
If using NSIS or another installer, make sure to include the `bin` folder:
- Source: `dist/TF4M_Dental_Manager/bin/*`
- Destination: `$INSTDIR/bin/`

## Troubleshooting

### dcm2niix Not Found

If users report dcm2niix errors, check the logs:

1. Open the Console Log Viewer (Help → View Console Log)
2. Search for "dcm2niix"
3. Look for error messages

Common issues:

**Problem**: "dcm2niix executable not found"
- **Solution**: The `bin/dcm2niix.exe` was not included in the build
- **Fix**: Re-run `setup_dcm2niix.ps1` and rebuild

**Problem**: "dcm2niix.exe is not recognized as an internal or external command"
- **Solution**: File permissions issue or antivirus blocking
- **Fix**: Check file properties, unblock if needed

**Problem**: Application crashes when processing CBCT
- **Solution**: dcm2niix may be corrupted
- **Fix**: Download a fresh copy from GitHub releases

### Checking dcm2niix Version

To verify which dcm2niix is being used:

```powershell
# In development
.\bin\dcm2niix.exe --version

# In distribution
.\dist\TF4M_Dental_Manager\bin\dcm2niix.exe --version
```

## Licensing Note

**Important**: dcm2niix is licensed under the BSD 3-Clause License. When distributing your application:

1. Include the dcm2niix license file
2. Provide attribution to the dcm2niix project
3. See: https://github.com/rordenlab/dcm2niix

Example attribution text:
```
This application includes dcm2niix (https://github.com/rordenlab/dcm2niix)
dcm2niix is licensed under the BSD 3-Clause License
Copyright (c) 2014-2023 Chris Rorden, University of South Carolina
```

## Updates

To update dcm2niix to a newer version:

1. Delete the old `bin/dcm2niix.exe`
2. Run `setup_dcm2niix.ps1` again (it will download the latest version)
3. Or manually download and replace from GitHub releases

## Platform-Specific Notes

### Windows
- File name: `dcm2niix.exe`
- Download: `dcm2niix_win.zip` from releases

### macOS
- File name: `dcm2niix` (no .exe extension)
- Download: `dcm2niix_mac.zip` from releases
- May need to: `chmod +x bin/dcm2niix`
- May need to allow in Security settings

### Linux
- File name: `dcm2niix` (no .exe extension)
- Download: `dcm2niix_lnx.zip` from releases
- May need to: `chmod +x bin/dcm2niix`

## Development Tips

### Testing Different dcm2niix Versions

Place different versions in the bin folder with different names:
```
bin/
├── dcm2niix.exe          (current version - used by application)
├── dcm2niix_v1.0.20.exe  (backup/test version)
└── dcm2niix_latest.exe   (latest test version)
```

Swap by renaming files to test different versions.

### Debugging dcm2niix Issues

Enable verbose logging in the application and check:
1. Console Log Viewer (Help → View Console Log)
2. Filter by "dcm2niix" or "cbct_converter"
3. Look for command line arguments and output

The logs will show:
- Where dcm2niix was found
- The exact command being executed
- stdout and stderr from dcm2niix
- Any errors or warnings

## Summary

✅ **For Development**:
- Run `setup_dcm2niix.ps1` once
- dcm2niix will be used from `bin/` folder

✅ **For Building**:
- Ensure `bin/dcm2niix.exe` exists
- Run build script
- bin folder is automatically included

✅ **For Distribution**:
- Include entire `dist/TF4M_Dental_Manager` folder
- bin folder with dcm2niix will be bundled
- No user installation required!

✅ **For Users**:
- Just run the .exe
- Everything works out of the box
- No additional setup needed
