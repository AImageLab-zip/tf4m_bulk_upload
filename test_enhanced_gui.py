#!/usr/bin/env python3
"""
Quick test to demonstrate the enhanced GUI with sample data.
"""

import os
import sys
from pathlib import Path

# Add the current directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk

from core.file_analyzer import FileAnalyzer
from core.project_manager import ProjectManager
from gui.patient_browser import PatientBrowser

def test_gui_with_sample():
    """Test the GUI with sample data."""
    
    # Create main window
    root = tk.Tk()
    root.title("Dental Data Manager - Test")
    root.geometry("1200x800")
    
    # Create project manager
    project_manager = ProjectManager()
    
    # Initialize project data if needed
    if not project_manager.project_data:
        from core.models import ProjectData
        project_manager.project_data = ProjectData(root_path="D:/Download/Esempio")
    
    # Load sample data
    sample_path = Path("D:/Download/Esempio/Esempio")
    if sample_path.exists():
        print("Loading sample data...")
        
        # Analyze the sample folder
        analyzer = FileAnalyzer()
        patient_data = analyzer.analyze_patient_folder(sample_path)
        patient_data.patient_id = "Sample_Patient"
        
        # Add to project
        project_manager.project_data.patients.append(patient_data)
        
        print(f"✅ Loaded patient: {patient_data.patient_id}")
        print(f"📊 Total files: {len(patient_data.get_all_files())}")
        print(f"❓ Unmatched files: {len(patient_data.unmatched_files)}")
        print(f"❌ Missing types: {len(patient_data.get_missing_data_types())}")
    else:
        print("❌ Sample folder not found. Creating dummy data...")
        
        # Create a dummy patient for demonstration
        from core.models import PatientData, FileData, DataType, MatchStatus
        
        dummy_patient = PatientData(
            patient_id="Demo_Patient",
            folder_path="C:/Demo"
        )
        
        # Add some dummy files
        dummy_patient.teleradiography = FileData(
            path="C:/Demo/teleradiography.jpg",
            data_type=DataType.TELERADIOGRAPHY,
            status=MatchStatus.MATCHED,
            confidence=0.9
        )
        
        # Add some unmatched files
        for i in range(5):
            dummy_patient.unmatched_files.append(FileData(
                path=f"C:/Demo/unmatched_file_{i}.dcm",
                status=MatchStatus.UNMATCHED
            ))
        
        project_manager.project_data.patients.append(dummy_patient)
        print("✅ Created demo patient with dummy data")
    
    # Create patient browser
    patient_browser = PatientBrowser(root, project_manager)
    patient_browser.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Load the project data
    patient_browser.load_project_data(project_manager.project_data)
    
    print("\n🚀 GUI launched! The enhanced interface shows:")
    print("  📊 Detailed completeness overview for each data type")
    print("  ✅/❌ Clear status indicators for required vs optional data")
    print("  🎯 Bulk mapping tools for efficient file assignment")
    print("  📄 Unmatched file counts and details")
    print("\nSelect a patient to see the enhanced completeness display!")
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    test_gui_with_sample()
