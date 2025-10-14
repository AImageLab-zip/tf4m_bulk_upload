#!/usr/bin/env python3
"""
Interactive file mapping tool for the Dental Data Management application.
"""

import sys
import os
import json
from typing import Dict, List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.file_analyzer import FileAnalyzer
from core.models import DataType, FileData, PatientData, MatchStatus

class InteractiveMapper:
    """Interactive tool for mapping dental files."""
    
    def __init__(self):
        self.file_analyzer = FileAnalyzer()
        
    def analyze_and_map(self, folder_path: str, patient_name: str = "Patient"):
        """Analyze folder and provide interactive mapping."""
        print(f"🔍 Analyzing folder: {folder_path}")
        print(f"👤 Patient: {patient_name}")
        print("=" * 60)
        
        if not os.path.exists(folder_path):
            print(f"❌ ERROR: Folder does not exist: {folder_path}")
            return
            
        # Analyze the patient folder
        patient_data = self.file_analyzer.analyze_patient_folder(folder_path)
        patient_data.patient_id = patient_name
        
        # Show current mapping
        self.show_current_mapping(patient_data)
        
        # Show unmatched files and allow manual mapping
        self.handle_unmatched_files(patient_data)
        
        # Show final summary
        self.show_final_summary(patient_data)
        
        return patient_data
        
    def show_current_mapping(self, patient_data: PatientData):
        """Show the current file mapping."""
        print("\n📂 CURRENT FILE MAPPING:")
        print("-" * 40)
        
        # CBCT Files
        if patient_data.cbct_files:
            print(f"🦷 CBCT DICOM Files: {len(patient_data.cbct_files)} files")
            if patient_data.cbct_folder:
                print(f"   📁 Folder: {patient_data.cbct_folder}")
            for i, file_data in enumerate(patient_data.cbct_files[:3]):  # Show first 3
                print(f"   📄 {file_data.filename}")
            if len(patient_data.cbct_files) > 3:
                print(f"   ... and {len(patient_data.cbct_files) - 3} more files")
        else:
            print("❌ CBCT DICOM Files: MISSING")
            
        # IOS Files
        if patient_data.ios_upper:
            print(f"🔝 IOS Upper Scan: ✅ {patient_data.ios_upper.filename}")
            print(f"   📄 {patient_data.ios_upper.path}")
            print(f"   🎯 Confidence: {patient_data.ios_upper.confidence:.1%}")
        else:
            print("❌ IOS Upper Scan: MISSING")
            
        if patient_data.ios_lower:
            print(f"🔽 IOS Lower Scan: ✅ {patient_data.ios_lower.filename}")
            print(f"   📄 {patient_data.ios_lower.path}")
            print(f"   🎯 Confidence: {patient_data.ios_lower.confidence:.1%}")
        else:
            print("❌ IOS Lower Scan: MISSING")
            
        # Radiographs
        if patient_data.teleradiography:
            print(f"📻 Teleradiography: ✅ {patient_data.teleradiography.filename}")
            print(f"   📄 {patient_data.teleradiography.path}")
            print(f"   🎯 Confidence: {patient_data.teleradiography.confidence:.1%}")
        else:
            print("❌ Teleradiography: MISSING")
            
        if patient_data.orthopantomography:
            print(f"🔬 Orthopantomography: ✅ {patient_data.orthopantomography.filename}")
            print(f"   📄 {patient_data.orthopantomography.path}")
            print(f"   🎯 Confidence: {patient_data.orthopantomography.confidence:.1%}")
        else:
            print("❌ Orthopantomography: MISSING")
            
        # Intraoral Photos
        if patient_data.intraoral_photos:
            print(f"📸 Intraoral Photos: {len(patient_data.intraoral_photos)} files")
            for photo in patient_data.intraoral_photos:
                print(f"   📷 {photo.filename}")
        else:
            print("⚠️  Intraoral Photos: None detected")
            
    def handle_unmatched_files(self, patient_data: PatientData):
        """Handle unmatched files interactively."""
        if not patient_data.unmatched_files:
            print("\n✅ All files have been successfully mapped!")
            return
            
        print(f"\n❓ UNMATCHED FILES ({len(patient_data.unmatched_files)}):")
        print("-" * 40)
        
        for i, file_data in enumerate(patient_data.unmatched_files):
            print(f"{i+1}. {file_data.filename}")
            print(f"   📄 Path: {file_data.path}")
            print(f"   📊 Status: {file_data.status.value}")
            
        print("\n🔧 MANUAL MAPPING OPTIONS:")
        print("1. Map unmatched files to data types")
        print("2. Search for missing files in unmatched list")
        print("3. Show all files in directory")
        print("4. Continue without changes")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-4): ").strip()
                
                if choice == "1":
                    self.map_unmatched_files(patient_data)
                    break
                elif choice == "2":
                    self.search_missing_files(patient_data)
                    break
                elif choice == "3":
                    self.show_all_files(patient_data)
                    continue
                elif choice == "4":
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-4.")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                return
                
    def map_unmatched_files(self, patient_data: PatientData):
        """Interactively map unmatched files."""
        if not patient_data.unmatched_files:
            print("No unmatched files to map.")
            return
            
        print("\n🎯 MANUAL FILE MAPPING:")
        print("-" * 30)
        
        data_types = {
            "1": (DataType.CBCT_DICOM, "CBCT DICOM Files"),
            "2": (DataType.IOS_UPPER, "IOS Upper Scan"),
            "3": (DataType.IOS_LOWER, "IOS Lower Scan"),
            "4": (DataType.TELERADIOGRAPHY, "Teleradiography"),
            "5": (DataType.ORTHOPANTOMOGRAPHY, "Orthopantomography"),
            "6": (DataType.INTRAORAL_PHOTO, "Intraoral Photo"),
            "7": (None, "Skip this file")
        }
        
        # Show available data types
        print("Available data types:")
        for key, (data_type, description) in data_types.items():
            print(f"  {key}. {description}")
            
        files_to_remove = []
        
        for file_data in patient_data.unmatched_files:
            print(f"\n📄 File: {file_data.filename}")
            print(f"📁 Path: {file_data.path}")
            
            while True:
                try:
                    choice = input("Map to data type (1-7, or 'q' to quit): ").strip().lower()
                    
                    if choice == 'q':
                        return
                    elif choice in data_types:
                        selected_type, description = data_types[choice]
                        
                        if selected_type is None:
                            print(f"⏭️  Skipping {file_data.filename}")
                            break
                            
                        # Update file data
                        file_data.data_type = selected_type
                        file_data.confidence = 1.0  # Manual assignment gets max confidence
                        file_data.status = MatchStatus.MATCHED
                        
                        # Move to appropriate location in patient data
                        self._assign_file_to_patient(patient_data, file_data)
                        files_to_remove.append(file_data)
                        
                        print(f"✅ Mapped {file_data.filename} to {description}")
                        break
                    else:
                        print("❌ Invalid choice. Please enter 1-7 or 'q' to quit.")
                        
                except KeyboardInterrupt:
                    print("\n👋 Stopping mapping...")
                    return
                    
        # Remove mapped files from unmatched list
        for file_data in files_to_remove:
            patient_data.unmatched_files.remove(file_data)
            
    def search_missing_files(self, patient_data: PatientData):
        """Search for missing files in the unmatched list."""
        missing_types = patient_data.get_missing_data_types()
        
        if not missing_types:
            print("✅ No missing data types!")
            return
            
        print(f"\n🔍 SEARCHING FOR MISSING FILES:")
        print("-" * 35)
        
        for data_type in missing_types:
            print(f"\n❓ Missing: {data_type.value}")
            print("Possible matches in unmatched files:")
            
            candidates = []
            for file_data in patient_data.unmatched_files:
                # Simple heuristic matching
                filename_lower = file_data.filename.lower()
                
                if data_type == DataType.TELERADIOGRAPHY:
                    if any(keyword in filename_lower for keyword in ['tele', 'lateral', 'cephalo']):
                        candidates.append(file_data)
                elif data_type == DataType.ORTHOPANTOMOGRAPHY:
                    if any(keyword in filename_lower for keyword in ['ortho', 'panoramic', 'opt']):
                        candidates.append(file_data)
                elif data_type == DataType.IOS_UPPER:
                    if any(keyword in filename_lower for keyword in ['upper', 'superiore', 'maxilla']):
                        candidates.append(file_data)
                elif data_type == DataType.IOS_LOWER:
                    if any(keyword in filename_lower for keyword in ['lower', 'inferiore', 'mandible']):
                        candidates.append(file_data)
                        
            if candidates:
                for i, candidate in enumerate(candidates):
                    print(f"  {i+1}. {candidate.filename}")
                    
                try:
                    choice = input(f"Select file for {data_type.value} (1-{len(candidates)}, or Enter to skip): ").strip()
                    
                    if choice and choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(candidates):
                            selected_file = candidates[idx]
                            
                            # Update file data
                            selected_file.data_type = data_type
                            selected_file.confidence = 0.8  # High confidence for manual selection
                            selected_file.status = MatchStatus.MATCHED
                            
                            # Move to appropriate location
                            self._assign_file_to_patient(patient_data, selected_file)
                            patient_data.unmatched_files.remove(selected_file)
                            
                            print(f"✅ Assigned {selected_file.filename} to {data_type.value}")
                            
                except (ValueError, KeyboardInterrupt):
                    print("⏭️  Skipped")
                    continue
            else:
                print("  No obvious candidates found.")
                
    def show_all_files(self, patient_data: PatientData):
        """Show all files found in the directory."""
        print(f"\n📋 ALL FILES IN DIRECTORY:")
        print("-" * 30)
        
        all_files = patient_data.get_all_files()
        
        for i, file_data in enumerate(all_files, 1):
            status_icon = "✅" if file_data.status == MatchStatus.MATCHED else "❓"
            data_type = file_data.data_type.value if file_data.data_type else "Unknown"
            
            print(f"{i:2d}. {status_icon} {file_data.filename}")
            print(f"    Type: {data_type}")
            print(f"    Path: {file_data.path}")
            if file_data.confidence > 0:
                print(f"    Confidence: {file_data.confidence:.1%}")
            print()
            
    def _assign_file_to_patient(self, patient_data: PatientData, file_data: FileData):
        """Assign a file to the appropriate location in patient data."""
        if file_data.data_type == DataType.CBCT_DICOM:
            patient_data.cbct_files.append(file_data)
        elif file_data.data_type == DataType.IOS_UPPER:
            patient_data.ios_upper = file_data
        elif file_data.data_type == DataType.IOS_LOWER:
            patient_data.ios_lower = file_data
        elif file_data.data_type == DataType.INTRAORAL_PHOTO:
            patient_data.intraoral_photos.append(file_data)
        elif file_data.data_type == DataType.TELERADIOGRAPHY:
            patient_data.teleradiography = file_data
        elif file_data.data_type == DataType.ORTHOPANTOMOGRAPHY:
            patient_data.orthopantomography = file_data
            
    def show_final_summary(self, patient_data: PatientData):
        """Show final summary after mapping."""
        print("\n" + "=" * 60)
        print("📊 FINAL MAPPING SUMMARY")
        print("=" * 60)
        
        missing_types = patient_data.get_missing_data_types()
        is_complete = patient_data.is_complete()
        
        status_icon = "✅" if is_complete else "⚠️"
        status_text = "COMPLETE" if is_complete else "INCOMPLETE"
        
        print(f"{status_icon} Patient Status: {status_text}")
        print(f"📁 Patient ID: {patient_data.patient_id}")
        print(f"📄 Total Files: {len(patient_data.get_all_files())}")
        print(f"❓ Unmatched Files: {len(patient_data.unmatched_files)}")
        
        if missing_types:
            print(f"❌ Missing: {', '.join([dt.value for dt in missing_types])}")
        else:
            print("✅ All required data types present")
            
        # Show counts
        print("\n📊 File Counts:")
        print(f"  🦷 CBCT DICOM: {len(patient_data.cbct_files)}")
        print(f"  🔝 IOS Upper: {'✅' if patient_data.ios_upper else '❌'}")
        print(f"  🔽 IOS Lower: {'✅' if patient_data.ios_lower else '❌'}")
        print(f"  📻 Teleradiography: {'✅' if patient_data.teleradiography else '❌'}")
        print(f"  🔬 Orthopantomography: {'✅' if patient_data.orthopantomography else '❌'}")
        print(f"  📸 Intraoral Photos: {len(patient_data.intraoral_photos)}")
        
        if patient_data.unmatched_files:
            print(f"\n❓ Remaining Unmatched Files:")
            for file_data in patient_data.unmatched_files:
                print(f"  📄 {file_data.filename}")


def main():
    """Main entry point for interactive mapper."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive Dental File Mapper")
    parser.add_argument("folder", help="Path to the patient data folder")
    parser.add_argument("--patient-name", default="Patient", help="Name for the patient")
    parser.add_argument("--save", help="Save final mapping to JSON file")
    
    args = parser.parse_args()
    
    mapper = InteractiveMapper()
    patient_data = mapper.analyze_and_map(args.folder, args.patient_name)
    
    if args.save and patient_data:
        try:
            # Convert to dictionary for JSON serialization
            data = {
                "patient_id": patient_data.patient_id,
                "folder_path": patient_data.folder_path,
                "is_complete": patient_data.is_complete(),
                "missing_types": [dt.value for dt in patient_data.get_missing_data_types()],
                "files": {
                    "cbct_files": [f.path for f in patient_data.cbct_files],
                    "ios_upper": patient_data.ios_upper.path if patient_data.ios_upper else None,
                    "ios_lower": patient_data.ios_lower.path if patient_data.ios_lower else None,
                    "teleradiography": patient_data.teleradiography.path if patient_data.teleradiography else None,
                    "orthopantomography": patient_data.orthopantomography.path if patient_data.orthopantomography else None,
                    "intraoral_photos": [f.path for f in patient_data.intraoral_photos],
                    "unmatched_files": [f.path for f in patient_data.unmatched_files]
                }
            }
            
            with open(args.save, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Mapping saved to: {args.save}")
            
        except Exception as e:
            print(f"❌ Error saving mapping: {e}")

if __name__ == "__main__":
    main()
