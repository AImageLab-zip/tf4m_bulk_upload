#!/bin/bash
# Build script for macOS installer
# Run this script to create a macOS .app bundle and optionally a .dmg installer

echo "========================================"
echo "TF4M Dental Manager - macOS Build Script"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if PyInstaller is installed
echo "Checking for PyInstaller..."
if ! python -m pip list | grep -q pyinstaller; then
    echo "PyInstaller not found. Installing..."
    python -m pip install pyinstaller
else
    echo "PyInstaller is already installed."
fi

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf build dist

# Build the application
echo ""
echo "Building application with PyInstaller..."
echo "This may take several minutes..."
pyinstaller TF4M_Dental_Manager.spec --clean

# Check if build was successful
if [ -d "dist/TF4M_Dental_Manager.app" ]; then
    echo ""
    echo "========================================"
    echo "Build completed successfully!"
    echo "========================================"
    echo ""
    echo "Application location:"
    echo "  dist/TF4M_Dental_Manager.app"
    echo ""
    
    # Optional: Create a DMG file
    echo "Would you like to create a DMG file for distribution? (y/n)"
    read -r create_dmg
    
    if [ "$create_dmg" = "y" ] || [ "$create_dmg" = "Y" ]; then
        echo ""
        echo "Creating DMG file..."
        
        # Install create-dmg if not already installed
        if ! command -v create-dmg &> /dev/null; then
            echo "Installing create-dmg..."
            brew install create-dmg
        fi
        
        timestamp=$(date +"%Y%m%d_%H%M%S")
        dmg_name="TF4M_Dental_Manager_macOS_$timestamp.dmg"
        
        # Create DMG
        create-dmg \
            --volname "TF4M Dental Manager" \
            --window-pos 200 120 \
            --window-size 800 400 \
            --icon-size 100 \
            --icon "TF4M_Dental_Manager.app" 200 190 \
            --hide-extension "TF4M_Dental_Manager.app" \
            --app-drop-link 600 185 \
            "$dmg_name" \
            "dist/TF4M_Dental_Manager.app"
        
        if [ -f "$dmg_name" ]; then
            echo "DMG file created: $dmg_name"
        else
            echo "Warning: DMG creation failed. You can still distribute the .app bundle."
        fi
    fi
    
    echo ""
    echo "To distribute:"
    echo "  1. Zip the .app bundle: zip -r TF4M_Dental_Manager.zip dist/TF4M_Dental_Manager.app"
    echo "  2. Or distribute the DMG file created above"
    echo ""
    echo "Note: For distribution outside the App Store, you may need to:"
    echo "  - Sign the application with a Developer ID certificate"
    echo "  - Notarize the application with Apple"
    echo ""
else
    echo ""
    echo "========================================"
    echo "Build failed!"
    echo "========================================"
    echo "Please check the error messages above."
    exit 1
fi

echo ""
echo "Build process completed!"
