# Exclude Files Feature - Implementation Summary

## Overview
Added the ability to mark files as "Exclude" in the reassign dialog, preventing them from being uploaded to TF4M.

## Changes Made

### 1. **core/models.py**
- Added `EXCLUDE = "exclude"` to the `DataType` enum
- Files marked with this type will be skipped during upload

### 2. **gui/patient_browser.py**

#### ReassignTypeDialog
- Added "Exclude from Upload" option to the type selection radio buttons
- Added informational label: "Note: Excluded files will not be uploaded to TF4M"

#### File Display (populate_files_tree)
- Excluded files are displayed with:
  - 🚫 icon prefix
  - "(EXCLUDED)" text suffix
  - Gray, italic text styling
- Tagged with "excluded" for consistent styling

### 3. **core/api_client.py**

#### _get_all_patient_files method
- Updated to filter out files where `data_type == DataType.EXCLUDE`
- Checks applied to:
  - CBCT files
  - IOS upper/lower scans
  - Intraoral photos
  - Teleradiography
  - Orthopantomography

## Usage

### How to Exclude a File:
1. Right-click on any file in the patient browser
2. Select "Reassign Type..."
3. Choose "Exclude from Upload" option
4. Click OK

### Visual Indicators:
- **File List**: `🚫 filename.ext (EXCLUDED)` in gray italic text
- **Preview Column**: 🚫 icon instead of file type icon

### Upload Behavior:
- Excluded files are automatically filtered out during upload
- They do not count towards completion requirements
- The system will only attempt to upload non-excluded files

## Testing

Run the test script to verify:
```bash
python test_exclude_functionality.py
```

Expected results:
- ✅ 4 files uploaded (non-excluded)
- ✅ 3 files correctly excluded
- ✅ All exclusion filters working properly

## Benefits

1. **Flexibility**: Users can exclude problematic or unnecessary files without deleting them
2. **Workflow Control**: Fine-tune which files get uploaded to TF4M
3. **Data Management**: Keep files in local project but skip them for remote upload
4. **Visual Feedback**: Clear indication of excluded status in the UI

## Examples

### Exclude duplicate files:
- If you have multiple similar photos, exclude the extras

### Exclude low-quality data:
- Mark poor quality scans as excluded rather than uploading them

### Exclude test files:
- Keep test data in the project but prevent it from being uploaded

### Exclude incomplete scans:
- Files that failed processing can be excluded from upload

## Notes

- Excluded files remain in the local project structure
- Exclusion status is saved in the project cache
- Files can be un-excluded by reassigning them to a proper type
- Exclusion is independent of file matching/validation status
