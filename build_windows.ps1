# Build script for Windows installer
# Run this script in PowerShell to create a Windows executable

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TF4M Dental Manager - Windows Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path ".venv")) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".venv\Scripts\Activate.ps1"

# Check if PyInstaller is installed
Write-Host "Checking for PyInstaller..." -ForegroundColor Green
$pyinstaller = & python -m pip list | Select-String -Pattern "pyinstaller"
if (-Not $pyinstaller) {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    & python -m pip install pyinstaller
} else {
    Write-Host "PyInstaller is already installed." -ForegroundColor Green
}

# Clean previous builds
Write-Host ""
Write-Host "Cleaning previous builds..." -ForegroundColor Green
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}

# Build the application
Write-Host ""
Write-Host "Building application with PyInstaller..." -ForegroundColor Green
Write-Host "This may take several minutes..." -ForegroundColor Yellow
& pyinstaller TF4M_Dental_Manager.spec --clean

# Check if build was successful
if (Test-Path "dist\TF4M_Dental_Manager") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Application location:" -ForegroundColor Cyan
    Write-Host "  dist\TF4M_Dental_Manager\TF4M_Dental_Manager.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "To distribute:" -ForegroundColor Cyan
    Write-Host "  1. Zip the entire 'dist\TF4M_Dental_Manager' folder" -ForegroundColor White
    Write-Host "  2. Or create an installer using NSIS (see BUILD_INSTRUCTIONS.md)" -ForegroundColor White
    Write-Host ""
    
    # Optional: Create a zip file
    $createZip = Read-Host "Would you like to create a ZIP file for distribution? (y/n)"
    if ($createZip -eq "y" -or $createZip -eq "Y") {
        Write-Host ""
        Write-Host "Creating ZIP file..." -ForegroundColor Green
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $zipName = "TF4M_Dental_Manager_Windows_$timestamp.zip"
        Compress-Archive -Path "dist\TF4M_Dental_Manager\*" -DestinationPath $zipName -Force
        Write-Host "ZIP file created: $zipName" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Build failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
