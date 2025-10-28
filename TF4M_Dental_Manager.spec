# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TF4M Dental Data Management Application
Supports both Windows and macOS builds
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the project root directory
project_root = os.path.abspath(SPECPATH)

# Determine platform
is_windows = sys.platform.startswith('win')
is_mac = sys.platform == 'darwin'

# Application name
app_name = 'TF4M_Dental_Manager'

# Collect data files
datas = []

# Include the entire bin folder with dcm2niix and any other utilities
bin_folder = os.path.join(project_root, 'bin')
if os.path.exists(bin_folder):
    # Include all files from bin folder
    for item in os.listdir(bin_folder):
        item_path = os.path.join(bin_folder, item)
        if os.path.isfile(item_path):
            # Add each file to the bin folder in the distribution
            datas.append((item_path, 'bin'))
            print(f"Including in bundle: {item} -> bin/")

# Legacy: Also check for dcm2niix.exe in project root (for backwards compatibility)
if is_windows:
    root_dcm2niix = os.path.join(project_root, 'dcm2niix.exe')
    if os.path.isfile(root_dcm2niix):
        datas.append((root_dcm2niix, '.'))
        print(f"Including legacy dcm2niix.exe from project root")

# Collect hidden imports
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'PIL',
    'PIL._imagingtk',
    'PIL._tkinter_finder',
    'pydicom',
    'numpy',
    'requests',
    'magic',
    'ttkthemes',
]

# Add all submodules from core, gui, and utils
hiddenimports.extend(collect_submodules('core'))
hiddenimports.extend(collect_submodules('gui'))
hiddenimports.extend(collect_submodules('utils'))

# Collect ttkthemes data files
try:
    datas.extend(collect_data_files('ttkthemes'))
except:
    pass

# Analysis
a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE configuration
# Check if icon file exists
icon_path = None
if is_windows and os.path.exists('icon.ico'):
    icon_path = 'icon.ico'
elif is_mac and os.path.exists('icon.icns'):
    icon_path = 'icon.icns'

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Optional: Add icon files
)

# COLLECT - gather all files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# macOS .app bundle
if is_mac:
    # Check if icon file exists for macOS
    mac_icon = 'icon.icns' if os.path.exists('icon.icns') else None
    
    app = BUNDLE(
        coll,
        name=f'{app_name}.app',
        icon=mac_icon,  # Optional: Add macOS icon
        bundle_identifier='com.tf4m.dentalmanager',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleName': 'TF4M Dental Manager',
            'CFBundleDisplayName': 'TF4M Dental Manager',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2025',
        },
    )
