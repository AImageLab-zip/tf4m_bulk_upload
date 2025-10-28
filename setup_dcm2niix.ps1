# Download and Setup dcm2niix for TF4M Application
# This script downloads the dcm2niix executable and places it in the bin folder

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "    TF4M - dcm2niix Setup Script" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$binFolder = Join-Path $PSScriptRoot "bin"
$dcm2niixPath = Join-Path $binFolder "dcm2niix.exe"
$downloadUrl = "https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20230411/dcm2niix_win.zip"
$tempZip = Join-Path $env:TEMP "dcm2niix_win.zip"
$tempExtract = Join-Path $env:TEMP "dcm2niix_extract"

# Check if dcm2niix already exists
if (Test-Path $dcm2niixPath) {
    Write-Host "[INFO] dcm2niix.exe already exists in bin folder" -ForegroundColor Green
    Write-Host "       Location: $dcm2niixPath" -ForegroundColor Gray
    
    # Test if it works
    try {
        $version = & $dcm2niixPath --version 2>&1 | Select-Object -First 1
        Write-Host "[INFO] Version: $version" -ForegroundColor Green
        Write-Host ""
        $response = Read-Host "Do you want to re-download and replace it? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Host "[INFO] Keeping existing dcm2niix.exe" -ForegroundColor Yellow
            Write-Host "       Setup complete!" -ForegroundColor Green
            pause
            exit 0
        }
    } catch {
        Write-Host "[WARNING] Existing dcm2niix.exe appears to be corrupted" -ForegroundColor Yellow
        Write-Host "          Will download a fresh copy..." -ForegroundColor Yellow
    }
}

# Create bin folder if it doesn't exist
if (-not (Test-Path $binFolder)) {
    Write-Host "[INFO] Creating bin folder..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $binFolder | Out-Null
}

Write-Host ""
Write-Host "Downloading dcm2niix from GitHub..." -ForegroundColor Cyan
Write-Host "URL: $downloadUrl" -ForegroundColor Gray

try {
    # Download the zip file
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
    Write-Host "[OK] Download completed!" -ForegroundColor Green
    
    # Extract the zip file
    Write-Host ""
    Write-Host "Extracting archive..." -ForegroundColor Cyan
    
    # Clean up temp extract folder if it exists
    if (Test-Path $tempExtract) {
        Remove-Item $tempExtract -Recurse -Force
    }
    
    Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
    Write-Host "[OK] Extraction completed!" -ForegroundColor Green
    
    # Find dcm2niix.exe in the extracted files
    Write-Host ""
    Write-Host "Locating dcm2niix.exe..." -ForegroundColor Cyan
    
    $extractedExe = Get-ChildItem -Path $tempExtract -Filter "dcm2niix.exe" -Recurse | Select-Object -First 1
    
    if ($extractedExe) {
        # Copy to bin folder
        Copy-Item $extractedExe.FullName -Destination $dcm2niixPath -Force
        Write-Host "[OK] dcm2niix.exe copied to bin folder!" -ForegroundColor Green
        Write-Host "     Location: $dcm2niixPath" -ForegroundColor Gray
        
        # Test the executable
        Write-Host ""
        Write-Host "Testing dcm2niix..." -ForegroundColor Cyan
        
        try {
            $version = & $dcm2niixPath --version 2>&1 | Select-Object -First 1
            Write-Host "[OK] dcm2niix is working!" -ForegroundColor Green
            Write-Host "     Version: $version" -ForegroundColor Gray
        } catch {
            Write-Host "[ERROR] dcm2niix test failed: $_" -ForegroundColor Red
            Write-Host "        The file may be corrupted. Try downloading manually from:" -ForegroundColor Yellow
            Write-Host "        https://github.com/rordenlab/dcm2niix/releases" -ForegroundColor Yellow
            pause
            exit 1
        }
        
        # Clean up
        Write-Host ""
        Write-Host "Cleaning up temporary files..." -ForegroundColor Cyan
        Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
        Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Cleanup completed!" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "==================================================================" -ForegroundColor Green
        Write-Host "    Setup Completed Successfully!" -ForegroundColor Green
        Write-Host "==================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "dcm2niix is now bundled with your application." -ForegroundColor White
        Write-Host "The TF4M application will automatically use this version." -ForegroundColor White
        Write-Host "No additional user installation required!" -ForegroundColor White
        
    } else {
        Write-Host "[ERROR] Could not find dcm2niix.exe in the downloaded archive" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download manually from:" -ForegroundColor Yellow
        Write-Host "https://github.com/rordenlab/dcm2niix/releases" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Extract dcm2niix.exe and place it in:" -ForegroundColor Yellow
        Write-Host "$dcm2niixPath" -ForegroundColor Yellow
        pause
        exit 1
    }
    
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to download or extract dcm2niix: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually from:" -ForegroundColor Yellow
    Write-Host "https://github.com/rordenlab/dcm2niix/releases" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Download 'dcm2niix_win.zip', extract dcm2niix.exe, and place it in:" -ForegroundColor Yellow
    Write-Host "$dcm2niixPath" -ForegroundColor Yellow
    
    # Clean up on error
    if (Test-Path $tempZip) { Remove-Item $tempZip -Force -ErrorAction SilentlyContinue }
    if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue }
    
    pause
    exit 1
}

Write-Host ""
pause
