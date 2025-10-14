#!/usr/bin/env python3
"""
Enhanced Interactive Bulk File Mapper for Dental Patient Data
Provides efficient bulk operations for mapping large numbers of files.
"""

import argparse
import os
import sys
from pathlib import Path

# Add the current directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.file_analyzer import FileAnalyzer
from core.models import DataType, MatchStatus

def main():
    parser = argparse.ArgumentParser(description="Enhanced bulk file mapper for dental patient data")
    parser.add_argument("folder_path", help="Path to the patient folder")
    parser.add_argument("--patient-name", help="Override patient name")
    args = parser.parse_args()
    
    folder_path = Path(args.folder_path)
    if not folder_path.exists():
        print(f"❌ Error: Path {folder_path} does not exist!")
        return
        
    print("🔍 ANALYZING PATIENT DATA...")
    print("=" * 60)
    
    # Initialize analyzer and analyze the folder
    analyzer = FileAnalyzer()
    patient_data = analyzer.analyze_patient_folder(folder_path)
    
    # Override patient name if provided
    if args.patient_name:
        patient_data.patient_id = args.patient_name
    
    print(f"📁 Patient: {patient_data.patient_id}")
    print(f"📊 Total Files: {len(patient_data.get_all_files())}")
    print(f"✅ Matched Files: {len(patient_data.get_all_files()) - len(patient_data.unmatched_files)}")
    print(f"❓ Unmatched Files: {len(patient_data.unmatched_files)}")
    
    # Show current status
    show_current_status(patient_data)
    
    if not patient_data.unmatched_files:
        print("\n✅ All files are already mapped! No action needed.")
        return
        
    # Enhanced bulk mapping interface
    bulk_mapper = BulkMapper()
    bulk_mapper.run(patient_data)
    
    # Show final summary
    print("\n" + "=" * 60)
    print("📊 FINAL MAPPING SUMMARY")
    print("=" * 60)
    
    missing_types = patient_data.get_missing_data_types()
    is_complete = patient_data.is_complete()
    status_emoji = "✅" if is_complete else "⚠️"
    print(f"{status_emoji} Patient Status: {'COMPLETE' if is_complete else 'INCOMPLETE'}")
    print(f"📁 Patient ID: {patient_data.patient_id}")
    print(f"📄 Total Files: {len(patient_data.get_all_files())}")
    print(f"❓ Unmatched Files: {len(patient_data.unmatched_files)}")
    
    if not is_complete:
        missing = [dt.value for dt in missing_types]
        print(f"❌ Missing: {', '.join(missing)}")
    
    # File type counts
    print(f"\n📊 File Counts:")
    counts = {
        "🦷 CBCT DICOM": len(patient_data.cbct_files),
        "🔝 IOS Upper": "✅" if patient_data.ios_upper else "❌",
        "🔽 IOS Lower": "✅" if patient_data.ios_lower else "❌",
        "📻 Teleradiography": "✅" if patient_data.teleradiography else "❌",
        "🔬 Orthopantomography": "✅" if patient_data.orthopantomography else "❌",
        "📸 Intraoral Photos": len(patient_data.intraoral_photos)
    }
    
    for label, count in counts.items():
        print(f"  {label}: {count}")
    
    if patient_data.unmatched_files:
        print(f"\n❓ Remaining Unmatched Files:")
        for file_data in patient_data.unmatched_files[:20]:  # Show first 20
            print(f"  📄 {file_data.filename}")
        if len(patient_data.unmatched_files) > 20:
            print(f"  ... and {len(patient_data.unmatched_files) - 20} more files")

def show_current_status(patient_data):
    """Show current mapping status."""
    print("\n📊 CURRENT STATUS:")
    print("-" * 30)
    
    # CBCT DICOM
    if patient_data.cbct_files:
        print(f"🦷 CBCT DICOM: {len(patient_data.cbct_files)} files")
    else:
        print("❌ CBCT DICOM: MISSING")
        
    # IOS Scans
    if patient_data.ios_upper:
        print(f"🔝 IOS Upper: ✅ {patient_data.ios_upper.filename}")
    else:
        print("❌ IOS Upper: MISSING")
        
    if patient_data.ios_lower:
        print(f"🔽 IOS Lower: ✅ {patient_data.ios_lower.filename}")
    else:
        print("❌ IOS Lower: MISSING")
        
    # X-rays
    if patient_data.teleradiography:
        print(f"📻 Teleradiography: ✅ {patient_data.teleradiography.filename}")
    else:
        print("❌ Teleradiography: MISSING")
        
    if patient_data.orthopantomography:
        print(f"🔬 Orthopantomography: ✅ {patient_data.orthopantomography.filename}")
    else:
        print("❌ Orthopantomography: MISSING")
        
    # Intraoral Photos
    if patient_data.intraoral_photos:
        print(f"📸 Intraoral Photos: {len(patient_data.intraoral_photos)} files")
    else:
        print("⚠️  Intraoral Photos: None detected")

class BulkMapper:
    """Enhanced bulk file mapper with pattern matching and smart suggestions."""
    
    def run(self, patient_data):
        """Run the bulk mapping interface."""
        while patient_data.unmatched_files:
            print("\n🔧 BULK MAPPING OPTIONS:")
            print("1. 🎯 Smart auto-mapping (recommended)")
            print("2. 🔍 Map by file pattern")
            print("3. 📋 Map all files to one type")
            print("4. 🎮 Interactive file-by-file mapping")
            print("5. 📊 Show unmatched files")
            print("6. ✅ Continue with current mapping")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                self.smart_auto_mapping(patient_data)
            elif choice == "2":
                self.map_by_pattern(patient_data)
            elif choice == "3":
                self.map_all_to_type(patient_data)
            elif choice == "4":
                self.interactive_mapping(patient_data)
            elif choice == "5":
                self.show_unmatched_files(patient_data)
            elif choice == "6":
                break
            else:
                print("❌ Invalid choice!")
    
    def smart_auto_mapping(self, patient_data):
        """Intelligent auto-mapping based on common patterns."""
        print("\n🎯 SMART AUTO-MAPPING")
        print("-" * 25)
        
        mappings_made = 0
        files_to_remove = []
        
        for file_data in patient_data.unmatched_files:
            filename_lower = file_data.filename.lower()
            suggested_type = None
            
            # CBCT DICOM detection patterns
            if (filename_lower.endswith('.dcm') or 
                'slice' in filename_lower or 
                '3d' in filename_lower or
                'cbct' in filename_lower):
                suggested_type = DataType.CBCT_DICOM
                
            # STL file patterns
            elif filename_lower.endswith('.stl'):
                if any(keyword in filename_lower for keyword in ['upper', 'max', 'superiore', 'mascella', 'mascellare', 'maxilla', 'maxillari', 'maxillar']):
                    suggested_type = DataType.IOS_UPPER
                elif any(keyword in filename_lower for keyword in ['lower', 'man', 'inferiore', 'mandibola', 'mandibolar', 'mandible', 'mandibular']):
                    suggested_type = DataType.IOS_LOWER
                    
            if suggested_type:
                print(f"📄 {file_data.filename} → {suggested_type.value}")
                file_data.data_type = suggested_type
                file_data.confidence = 0.8  # Auto-mapping confidence
                file_data.status = MatchStatus.MATCHED
                
                self._assign_file_to_patient(patient_data, file_data)
                files_to_remove.append(file_data)
                mappings_made += 1
        
        # Remove mapped files
        for file_data in files_to_remove:
            patient_data.unmatched_files.remove(file_data)
            
        print(f"\n✅ Auto-mapped {mappings_made} files")
        if mappings_made == 0:
            print("ℹ️  No files could be auto-mapped. Try manual mapping options.")
    
    def map_by_pattern(self, patient_data):
        """Map files by filename pattern."""
        print("\n🔍 MAP BY PATTERN")
        print("-" * 20)
        
        # Show some example patterns
        print("Example patterns:")
        print("  dcm - all .dcm files")
        print("  slice - files containing 'slice'")
        print("  upper - files containing 'upper'")
        print("  stl - all .stl files")
        
        pattern = input("\nEnter pattern to match: ").strip().lower()
        if not pattern:
            return
            
        # Find matching files
        matching_files = []
        for file_data in patient_data.unmatched_files:
            if pattern in file_data.filename.lower():
                matching_files.append(file_data)
                
        if not matching_files:
            print(f"❌ No files found matching pattern '{pattern}'")
            return
            
        print(f"\n📋 Found {len(matching_files)} files matching '{pattern}':")
        for i, file_data in enumerate(matching_files[:10], 1):
            print(f"  {i}. {file_data.filename}")
        if len(matching_files) > 10:
            print(f"  ... and {len(matching_files) - 10} more files")
            
        # Select data type
        data_type = self._select_data_type()
        if not data_type:
            return
            
        confirm = input(f"\nMap {len(matching_files)} files to {data_type.value}? (y/n): ").strip().lower()
        if confirm != 'y':
            return
            
        # Map the files
        for file_data in matching_files:
            file_data.data_type = data_type
            file_data.confidence = 0.9  # Pattern mapping confidence
            file_data.status = MatchStatus.MATCHED
            
            self._assign_file_to_patient(patient_data, file_data)
            patient_data.unmatched_files.remove(file_data)
            
        print(f"✅ Mapped {len(matching_files)} files to {data_type.value}")
    
    def map_all_to_type(self, patient_data):
        """Map all unmatched files to a single data type."""
        print("\n📋 MAP ALL TO ONE TYPE")
        print("-" * 25)
        
        if not patient_data.unmatched_files:
            print("No unmatched files to map.")
            return
            
        print(f"This will map ALL {len(patient_data.unmatched_files)} unmatched files to one data type.")
        
        # Select data type
        data_type = self._select_data_type()
        if not data_type:
            return
            
        confirm = input(f"\nMap ALL {len(patient_data.unmatched_files)} files to {data_type.value}? (y/n): ").strip().lower()
        if confirm != 'y':
            return
            
        # Map all files
        files_to_map = patient_data.unmatched_files[:]
        for file_data in files_to_map:
            file_data.data_type = data_type
            file_data.confidence = 0.7  # Bulk mapping confidence
            file_data.status = MatchStatus.MATCHED
            
            self._assign_file_to_patient(patient_data, file_data)
            patient_data.unmatched_files.remove(file_data)
            
        print(f"✅ Mapped all {len(files_to_map)} files to {data_type.value}")
    
    def interactive_mapping(self, patient_data):
        """Interactive file-by-file mapping."""
        print("\n🎮 INTERACTIVE MAPPING")
        print("-" * 25)
        
        if not patient_data.unmatched_files:
            print("No unmatched files to map.")
            return
            
        files_to_remove = []
        
        for i, file_data in enumerate(patient_data.unmatched_files, 1):
            print(f"\n📄 File {i}/{len(patient_data.unmatched_files)}: {file_data.filename}")
            print(f"📁 Path: {file_data.path}")
            
            # Show data type options
            data_types = {
                "1": DataType.CBCT_DICOM,
                "2": DataType.IOS_UPPER,
                "3": DataType.IOS_LOWER,
                "4": DataType.TELERADIOGRAPHY,
                "5": DataType.ORTHOPANTOMOGRAPHY,
                "6": DataType.INTRAORAL_PHOTO,
                "s": "skip",
                "q": "quit"
            }
            
            print("Map to:")
            print("  1. CBCT DICOM")
            print("  2. IOS Upper")
            print("  3. IOS Lower")
            print("  4. Teleradiography")
            print("  5. Orthopantomography")
            print("  6. Intraoral Photo")
            print("  s. Skip this file")
            print("  q. Quit mapping")
            
            choice = input("Your choice: ").strip().lower()
            
            if choice == "q":
                break
            elif choice == "s":
                continue
            elif choice in data_types and choice not in ["s", "q"]:
                data_type = data_types[choice]
                
                file_data.data_type = data_type
                file_data.confidence = 1.0  # Manual mapping gets max confidence
                file_data.status = MatchStatus.MATCHED
                
                self._assign_file_to_patient(patient_data, file_data)
                files_to_remove.append(file_data)
                
                print(f"✅ Mapped to {data_type.value}")
            else:
                print("❌ Invalid choice, skipping...")
                
        # Remove mapped files
        for file_data in files_to_remove:
            patient_data.unmatched_files.remove(file_data)
            
        print(f"\n✅ Completed interactive mapping")
    
    def show_unmatched_files(self, patient_data):
        """Show all unmatched files."""
        print(f"\n📄 UNMATCHED FILES ({len(patient_data.unmatched_files)}):")
        print("-" * 40)
        
        for i, file_data in enumerate(patient_data.unmatched_files, 1):
            print(f"{i}. {file_data.filename}")
            if i >= 50:  # Limit display
                print(f"... and {len(patient_data.unmatched_files) - 50} more files")
                break
    
    def _select_data_type(self):
        """Helper to select a data type."""
        data_types = {
            "1": DataType.CBCT_DICOM,
            "2": DataType.IOS_UPPER,
            "3": DataType.IOS_LOWER,
            "4": DataType.TELERADIOGRAPHY,
            "5": DataType.ORTHOPANTOMOGRAPHY,
            "6": DataType.INTRAORAL_PHOTO
        }
        
        print("\nSelect data type:")
        print("  1. CBCT DICOM")
        print("  2. IOS Upper")
        print("  3. IOS Lower")
        print("  4. Teleradiography")
        print("  5. Orthopantomography")
        print("  6. Intraoral Photo")
        
        choice = input("Your choice (1-6): ").strip()
        return data_types.get(choice)
    
    def _assign_file_to_patient(self, patient_data, file_data):
        """Assign a file to the appropriate patient data attribute."""
        if file_data.data_type == DataType.CBCT_DICOM:
            patient_data.cbct_files.append(file_data)
        elif file_data.data_type == DataType.IOS_UPPER:
            patient_data.ios_upper = file_data
        elif file_data.data_type == DataType.IOS_LOWER:
            patient_data.ios_lower = file_data
        elif file_data.data_type == DataType.TELERADIOGRAPHY:
            patient_data.teleradiography = file_data
        elif file_data.data_type == DataType.ORTHOPANTOMOGRAPHY:
            patient_data.orthopantomography = file_data
        elif file_data.data_type == DataType.INTRAORAL_PHOTO:
            patient_data.intraoral_photos.append(file_data)

if __name__ == "__main__":
    main()
