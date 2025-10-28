# Building TF4M Dental Manager Installers

This document provides instructions for creating installers for the TF4M Dental Manager application on Windows and macOS.

## Prerequisites

### All Platforms
- Python 3.8 or higher
- Virtual environment with all dependencies installed (see `requirements.txt`)
- PyInstaller (will be installed automatically by build scripts)
- **dcm2niix executable** (required for DICOM to NIfTI conversion)

### Windows Additional Requirements
- Windows 10 or higher
- PowerShell 5.1 or higher
- Optional: [NSIS](https://nsis.sourceforge.io/) for creating a professional installer

### macOS Additional Requirements
- macOS 10.13 or higher
- Xcode Command Line Tools: `xcode-select --install`
- Optional: Homebrew for creating DMG files: `brew install create-dmg`
- Optional: Apple Developer ID for code signing and notarization

## Setup dcm2niix (IMPORTANT!)

Before building, you MUST include dcm2niix in the application bundle:

### Automatic Setup (Recommended)
```powershell
.\setup_dcm2niix.ps1
```

This script will:
1. Download the latest dcm2niix from GitHub
2. Extract and place it in the `bin` folder
3. Verify it works correctly

### Manual Setup
1. Download dcm2niix from https://github.com/rordenlab/dcm2niix/releases
2. Extract `dcm2niix.exe` (Windows) or `dcm2niix` (macOS/Linux)
3. Place it in the `bin` folder at the project root
4. The application will automatically use this bundled version

**Note:** Without dcm2niix, the application cannot convert DICOM files to NIfTI format!

## Building on Windows

### Quick Build

1. **FIRST: Setup dcm2niix** (see above)
2. Open PowerShell in the project directory
3. Run the build script:
   ```powershell
   .\build_windows.ps1
   ```
4. Follow the prompts to optionally create a ZIP file

The built application will be in `dist\TF4M_Dental_Manager\TF4M_Dental_Manager.exe`

### Manual Build

If you prefer to build manually:

```powershell
# FIRST: Ensure dcm2niix.exe is in the bin folder!

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install PyInstaller
python -m pip install pyinstaller

# Build the application
pyinstaller TF4M_Dental_Manager.spec --clean
```

### Creating a Professional Windows Installer (Optional)

For a more professional installer with Start Menu shortcuts and uninstaller:

1. Install [NSIS](https://nsis.sourceforge.io/)
2. Create an NSIS script (example provided below)
3. Compile the script with NSIS

**Example NSIS Script (`installer.nsi`):**

```nsis
!define APPNAME "TF4M Dental Manager"
!define COMPANYNAME "TF4M"
!define DESCRIPTION "Dental Data Management Application"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\${COMPANYNAME}\${APPNAME}"

Name "${APPNAME}"
OutFile "TF4M_Dental_Manager_Setup.exe"

Page directory
Page instfiles

Section "Install"
    SetOutPath $INSTDIR
    File /r "dist\TF4M_Dental_Manager\*.*"
    
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\TF4M_Dental_Manager.exe"
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\TF4M_Dental_Manager.exe"
    
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
    Delete "$DESKTOP\${APPNAME}.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"
    
    RMDir /r "$INSTDIR"
SectionEnd
```

Compile with: `makensis installer.nsi`

## Building on macOS

### Quick Build

1. Open Terminal in the project directory
2. Make the script executable:
   ```bash
   chmod +x build_macos.sh
   ```
3. Run the build script:
   ```bash
   ./build_macos.sh
   ```
4. Follow the prompts to optionally create a DMG file

The built application will be in `dist/TF4M_Dental_Manager.app`

### Manual Build

If you prefer to build manually:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install PyInstaller
python -m pip install pyinstaller

# Build the application
pyinstaller TF4M_Dental_Manager.spec --clean
```

### Creating a DMG Installer (Optional)

To create a professional DMG installer:

```bash
# Install create-dmg (if not already installed)
brew install create-dmg

# Create DMG
create-dmg \
    --volname "TF4M Dental Manager" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "TF4M_Dental_Manager.app" 200 190 \
    --hide-extension "TF4M_Dental_Manager.app" \
    --app-drop-link 600 185 \
    "TF4M_Dental_Manager_Installer.dmg" \
    "dist/TF4M_Dental_Manager.app"
```

### Code Signing and Notarization (For Distribution)

If you plan to distribute the application outside your organization:

1. **Sign the application:**
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" \
       dist/TF4M_Dental_Manager.app
   ```

2. **Create a signed DMG:**
   ```bash
   codesign --sign "Developer ID Application: Your Name" TF4M_Dental_Manager_Installer.dmg
   ```

3. **Notarize with Apple:**
   ```bash
   # Submit for notarization
   xcrun altool --notarize-app \
       --primary-bundle-id "com.tf4m.dentalmanager" \
       --username "your-apple-id@email.com" \
       --password "@keychain:AC_PASSWORD" \
       --file TF4M_Dental_Manager_Installer.dmg
   
   # Check status (after receiving RequestUUID)
   xcrun altool --notarization-info <RequestUUID> \
       --username "your-apple-id@email.com" \
       --password "@keychain:AC_PASSWORD"
   
   # Staple the notarization ticket
   xcrun stapler staple TF4M_Dental_Manager_Installer.dmg
   ```

For more information, see [Apple's notarization documentation](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution).

## Adding Application Icons (Optional)

To add custom icons to your application:

### Windows Icon (.ico)
1. Create a 256x256 PNG icon
2. Convert to .ico format (use online tools or ImageMagick)
3. Save as `icon.ico` in the project root
4. The build script will automatically include it

### macOS Icon (.icns)
1. Create a 1024x1024 PNG icon
2. Convert to .icns format:
   ```bash
   # Create iconset directory
   mkdir MyIcon.iconset
   
   # Create different sizes
   sips -z 16 16     icon.png --out MyIcon.iconset/icon_16x16.png
   sips -z 32 32     icon.png --out MyIcon.iconset/icon_16x16@2x.png
   sips -z 32 32     icon.png --out MyIcon.iconset/icon_32x32.png
   sips -z 64 64     icon.png --out MyIcon.iconset/icon_32x32@2x.png
   sips -z 128 128   icon.png --out MyIcon.iconset/icon_128x128.png
   sips -z 256 256   icon.png --out MyIcon.iconset/icon_128x128@2x.png
   sips -z 256 256   icon.png --out MyIcon.iconset/icon_256x256.png
   sips -z 512 512   icon.png --out MyIcon.iconset/icon_256x256@2x.png
   sips -z 512 512   icon.png --out MyIcon.iconset/icon_512x512.png
   sips -z 1024 1024 icon.png --out MyIcon.iconset/icon_512x512@2x.png
   
   # Convert to icns
   iconutil -c icns MyIcon.iconset
   mv MyIcon.icns icon.icns
   ```
3. Save as `icon.icns` in the project root

## Distribution

### Windows
- **ZIP Distribution**: Zip the entire `dist\TF4M_Dental_Manager` folder
- **NSIS Installer**: Distribute the `.exe` created by NSIS
- Users may need to allow the application through Windows Defender SmartScreen

### macOS
- **ZIP Distribution**: 
  ```bash
  zip -r TF4M_Dental_Manager.zip dist/TF4M_Dental_Manager.app
  ```
- **DMG Distribution**: Distribute the `.dmg` file
- Users may need to allow the application in System Preferences > Security & Privacy
- For code-signed and notarized apps, this warning is minimized

## Troubleshooting

### Windows

**Issue**: "pyinstaller: command not found"
- **Solution**: Make sure you've activated the virtual environment

**Issue**: Application fails to start
- **Solution**: Check that all dependencies are listed in `requirements.txt` and the `.spec` file

**Issue**: Missing DLL errors
- **Solution**: PyInstaller should automatically include all DLLs. If not, add them manually to the `.spec` file

### macOS

**Issue**: "permission denied" when running build script
- **Solution**: Run `chmod +x build_macos.sh`

**Issue**: Application won't open (damaged/unidentified developer)
- **Solution**: Right-click the app and select "Open", or sign the application

**Issue**: Missing modules at runtime
- **Solution**: Add missing modules to `hiddenimports` in the `.spec` file

## File Size Optimization

If the installer is too large:

1. Use UPX compression (already enabled in `.spec` file)
2. Exclude unnecessary packages in the `.spec` file
3. Consider using `--onefile` mode (slower startup but single executable)

## Testing

Before distributing:

1. **Test on a clean machine** without Python installed
2. **Test all features** of the application
3. **Check file associations** and permissions
4. **Verify uninstallation** (for NSIS/DMG installers)

## Version Updates

When releasing a new version:

1. Update version number in `TF4M_Dental_Manager.spec`
2. Update version in NSIS script (if using)
3. Update version in macOS Info.plist
4. Tag the release in version control
5. Create release notes

## Support

For issues with the build process, check:
- PyInstaller documentation: https://pyinstaller.org/
- NSIS documentation: https://nsis.sourceforge.io/
- Apple Developer documentation: https://developer.apple.com/

## License

Include appropriate license information with your distribution.
