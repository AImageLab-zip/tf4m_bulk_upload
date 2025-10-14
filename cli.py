#!/usr/bin/env python3
"""
Command-line interface for the Dental Data Management application.
This version can be used when GUI is not available.
"""

import sys
import os
import argparse
import json
from typing import Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.project_manager import ProjectManager
from core.api_client import APIClient

class DentalDataCLI:
    """Command-line interface for dental data management."""
    
    def __init__(self):
        self.project_manager = ProjectManager()
        self.api_client = APIClient("http://localhost:8000")
        
    def analyze_folder(self, folder_path: str, output_file: Optional[str] = None):
        """Analyze a folder and generate a report."""
        print(f"Analyzing folder: {folder_path}")
        print("-" * 50)
        
        if not os.path.exists(folder_path):
            print(f"ERROR: Folder does not exist: {folder_path}")
            return False
            
        # Progress callback
        def progress_callback(current, total, message):
            print(f"[{current}/{total}] {message}")
            
        # Analyze the project
        try:
            project_data = self.project_manager.analyze_project(folder_path, progress_callback)
        except Exception as e:
            print(f"ERROR: Failed to analyze project: {e}")
            return False
            
        # Generate report
        self.print_analysis_report(project_data)
        
        # Save to file if requested
        if output_file:
            self.save_report_to_file(project_data, output_file)
            print(f"\nReport saved to: {output_file}")
            
        return True
        
    def analyze_single_patient(self, folder_path: str, patient_name: str, output_file: Optional[str] = None):
        """Analyze a folder as a single patient instead of looking for subfolders."""
        print(f"Analyzing folder as single patient: {folder_path}")
        print(f"Patient name: {patient_name}")
        print("-" * 50)
        
        if not os.path.exists(folder_path):
            print(f"ERROR: Folder does not exist: {folder_path}")
            return False
            
        # Analyze as single patient
        try:
            patient_data = self.project_manager.file_analyzer.analyze_patient_folder(folder_path)
            patient_data.patient_id = patient_name
        except Exception as e:
            print(f"ERROR: Failed to analyze patient folder: {e}")
            return False
            
        # Create a project with just this patient
        from core.models import ProjectData
        project_data = ProjectData(root_path=folder_path)
        project_data.patients = [patient_data]
        
        # Set the project data in the manager
        self.project_manager.project_data = project_data
        
        # Generate report
        self.print_analysis_report(project_data)
        
        # Save to file if requested
        if output_file:
            self.save_report_to_file(project_data, output_file)
            print(f"\nReport saved to: {output_file}")
            
        return True
        
    def print_analysis_report(self, project_data):
        """Print the analysis report to console."""
        print("\n" + "=" * 60)
        print("DENTAL DATA ANALYSIS REPORT")
        print("=" * 60)
        
        # Summary
        total_patients = len(project_data.patients)
        complete_patients = len(project_data.get_complete_patients())
        incomplete_patients = len(project_data.get_incomplete_patients())
        
        print(f"\nSUMMARY:")
        print(f"  Total Patients: {total_patients}")
        print(f"  Complete Patients: {complete_patients}")
        print(f"  Incomplete Patients: {incomplete_patients}")
        print(f"  Success Rate: {(complete_patients/total_patients*100):.1f}%" if total_patients > 0 else "  Success Rate: N/A")
        
        # Global errors
        if project_data.global_errors:
            print(f"\nGLOBAL ERRORS:")
            for error in project_data.global_errors:
                print(f"  ❌ {error}")
                
        # Patient details
        print(f"\nPATIENT DETAILS:")
        print("-" * 40)
        
        for patient in project_data.patients:
            status_icon = "✅" if patient.is_complete() else "⚠️"
            print(f"\n{status_icon} Patient: {patient.patient_id}")
            
            # File counts
            files = patient.get_all_files()
            print(f"   Total files: {len(files)}")
            print(f"   CBCT files: {len(patient.cbct_files)}")
            print(f"   Intraoral photos: {len(patient.intraoral_photos)}")
            print(f"   IOS Upper: {'✓' if patient.ios_upper else '✗'}")
            print(f"   IOS Lower: {'✓' if patient.ios_lower else '✗'}")
            print(f"   Teleradiography: {'✓' if patient.teleradiography else '✗'}")
            print(f"   Orthopantomography: {'✓' if patient.orthopantomography else '✗'}")
            
            # Missing data
            missing = patient.get_missing_data_types()
            if missing:
                print(f"   Missing: {', '.join([dt.value for dt in missing])}")
                
            # Unmatched files
            if patient.unmatched_files:
                print(f"   Unmatched files: {len(patient.unmatched_files)}")
                for file_data in patient.unmatched_files:
                    print(f"     - {file_data.filename}")
                    
            # Validation errors
            if patient.validation_errors:
                print(f"   Errors:")
                for error in patient.validation_errors:
                    print(f"     ❌ {error}")
                    
    def save_report_to_file(self, project_data, output_file: str):
        """Save the analysis report to a JSON file."""
        report = self.project_manager.get_validation_report()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ERROR: Failed to save report: {e}")
            
    def test_api_connection(self, base_url: str, api_key: Optional[str] = None):
        """Test API connection."""
        print(f"Testing API connection to: {base_url}")
        
        self.api_client.set_base_url(base_url)
        if api_key:
            self.api_client.set_api_key(api_key)
            
        success, message = self.api_client.test_connection()
        
        if success:
            print("✅ API connection successful!")
        else:
            print(f"❌ API connection failed: {message}")
            
        return success
        
    def list_file_details(self, folder_path: str):
        """List detailed file information for debugging."""
        print(f"Detailed file analysis for: {folder_path}")
        print("-" * 50)
        
        project_data = self.project_manager.analyze_project(folder_path)
        
        for patient in project_data.patients:
            print(f"\nPatient: {patient.patient_id}")
            print(f"Folder: {patient.folder_path}")
            
            if patient.cbct_folder:
                print(f"CBCT Folder: {patient.cbct_folder}")
            if patient.ios_folder:
                print(f"IOS Folder: {patient.ios_folder}")
                
            print("\nAll Files:")
            for file_data in patient.get_all_files():
                confidence = f"{file_data.confidence:.1%}" if file_data.confidence > 0 else "N/A"
                data_type = file_data.data_type.value if file_data.data_type else "Unknown"
                print(f"  {file_data.filename}")
                print(f"    Path: {file_data.path}")
                print(f"    Type: {data_type}")
                print(f"    Status: {file_data.status.value}")
                print(f"    Confidence: {confidence}")
                print()

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Dental Data Management CLI")
    parser.add_argument("command", choices=["analyze", "test-api", "list-files", "analyze-single"], 
                       help="Command to execute")
    parser.add_argument("--folder", "-f", help="Path to the patient data folder")
    parser.add_argument("--output", "-o", help="Output file for analysis report")
    parser.add_argument("--api-url", default="http://localhost:8000", 
                       help="API base URL")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--patient-name", help="Name for single patient analysis")
    
    args = parser.parse_args()
    
    cli = DentalDataCLI()
    
    if args.command == "analyze":
        if not args.folder:
            print("ERROR: --folder is required for analyze command")
            return 1
        success = cli.analyze_folder(args.folder, args.output)
        return 0 if success else 1
        
    elif args.command == "analyze-single":
        if not args.folder:
            print("ERROR: --folder is required for analyze-single command")
            return 1
        success = cli.analyze_single_patient(args.folder, args.patient_name or "Patient", args.output)
        return 0 if success else 1
        
    elif args.command == "test-api":
        success = cli.test_api_connection(args.api_url, args.api_key)
        return 0 if success else 1
        
    elif args.command == "list-files":
        if not args.folder:
            print("ERROR: --folder is required for list-files command")
            return 1
        cli.list_file_details(args.folder)
        return 0
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
