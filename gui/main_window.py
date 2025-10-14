"""
Main window for the Dental Data Management application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Optional

from core.project_manager import ProjectManager
from core.api_client import TF4MAPIClient, APIClient
from gui.patient_browser import PatientBrowser
from gui.settings_dialog import SettingsDialog
from gui.upload_manager import UploadManager
from gui.upload_dialog import UploadDialog

class MainWindow:
    """Main application window."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.project_manager = ProjectManager()
        self.api_client = TF4MAPIClient("http://pdor.ing.unimore.it:8080", project_slug="maxillo")  # Default TF4M URL
        
        # Load saved settings and apply to API client
        self.load_and_apply_settings()
        
        self.setup_window()
        self.create_widgets()
        self.current_project_path: Optional[str] = None
        
    def setup_window(self):
        """Setup the main window properties."""
        self.root.title("Dental Data Management - TF4M")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def create_widgets(self):
        """Create and layout all widgets."""
        self.create_menu()
        self.create_toolbar()
        self.create_main_content()
        self.create_status_bar()
        
    def create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Project Folder...", command=self.open_project_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Settings...", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Generate Report", command=self.generate_report)
        tools_menu.add_command(label="Test API Connection", command=self.test_api_connection)
        tools_menu.add_separator()
        
        # Cache submenu
        cache_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Cache Management", menu=cache_menu)
        cache_menu.add_command(label="View Cache Statistics", command=self.view_cache_stats)
        cache_menu.add_command(label="Clear Current Patient Cache", command=self.clear_current_patient_cache)
        cache_menu.add_separator()
        cache_menu.add_command(label="Clear All Cache", command=self.clear_all_cache)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Open folder button
        self.open_btn = ttk.Button(
            toolbar_frame, 
            text="Open Project Folder", 
            command=self.open_project_folder
        )
        self.open_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Analyze button
        self.analyze_btn = ttk.Button(
            toolbar_frame, 
            text="Analyze", 
            command=self.analyze_project,
            state="disabled"
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Upload button
        self.upload_btn = ttk.Button(
            toolbar_frame, 
            text="Upload All", 
            command=self.upload_all_patients,
            state="disabled"
        )
        self.upload_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Settings button
        self.settings_btn = ttk.Button(
            toolbar_frame, 
            text="⚙️ Settings", 
            command=self.open_settings
        )
        self.settings_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(toolbar_frame, textvariable=self.progress_var)
        self.progress_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.progress_bar = ttk.Progressbar(toolbar_frame, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 5))
        
    def create_main_content(self):
        """Create the main content area."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Patient browser tab
        self.patient_browser = PatientBrowser(self.notebook, self.project_manager)
        self.notebook.add(self.patient_browser.frame, text="Patient Browser")
        
        # Upload manager tab
        self.upload_manager = UploadManager(self.notebook, self.api_client)
        self.notebook.add(self.upload_manager.frame, text="Upload Manager")
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="Ready - Select a project folder to begin")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)
        
        # Project path label
        self.project_path_var = tk.StringVar(value="")
        self.project_path_label = ttk.Label(self.status_frame, textvariable=self.project_path_var, foreground="gray")
        self.project_path_label.pack(side=tk.RIGHT)
    
    def load_and_apply_settings(self):
        """Load settings from file and apply them to the API client."""
        import json
        settings_file = "settings.json"
        
        # Default settings
        default_settings = {
            "api_url": "http://pdor.ing.unimore.it:8080",
            "username": "",
            "password": ""
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
        except Exception:
            pass  # Use default settings if loading fails
        
        # Apply settings to API client
        if default_settings["api_url"]:
            self.api_client.set_base_url(default_settings["api_url"])
        
        if default_settings["username"] and default_settings["password"]:
            self.api_client.set_credentials(default_settings["username"], default_settings["password"])
        
    def open_project_folder(self):
        """Open a project folder dialog."""
        folder_path = filedialog.askdirectory(
            title="Select Project Folder",
            initialdir=os.path.expanduser("~")
        )
        
        if folder_path:
            self.current_project_path = folder_path
            self.project_path_var.set(f"Project: {folder_path}")
            self.status_var.set(f"Project folder selected: {os.path.basename(folder_path)}")
            self.analyze_btn.config(state="normal")
            
    def analyze_project(self):
        """Analyze the current project."""
        if not self.current_project_path:
            messagebox.showerror("Error", "No project folder selected")
            return
            
        self.analyze_btn.config(state="disabled")
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
        self.status_var.set("Analyzing project...")
        
        def progress_callback(current, total, message):
            """Update progress during analysis."""
            self.progress_var.set(f"{current}/{total}: {message}")
            self.progress_bar.config(mode='determinate', maximum=total, value=current)
            self.root.update_idletasks()
            
        def completion_callback(result, error=None):
            """Handle analysis completion."""
            self.progress_bar.stop()
            self.progress_bar.config(value=0)
            
            if error:
                self.status_var.set("Analysis failed")
                self.progress_var.set("Ready")
                messagebox.showerror("Analysis Error", f"Failed to analyze project: {error}")
            else:
                total_patients = len(result.patients)
                complete_patients = len(result.get_complete_patients())
                self.status_var.set(f"Analysis complete: {total_patients} patients found, {complete_patients} complete")
                self.progress_var.set("Analysis complete")
                
                # Update patient browser
                self.patient_browser.load_project_data(result)
                
                # Enable upload button if there are complete patients
                if complete_patients > 0:
                    self.upload_btn.config(state="normal")
                    
            self.analyze_btn.config(state="normal")
            
        # Start analysis in background
        self.project_manager.analyze_project_async(
            self.current_project_path,
            progress_callback,
            completion_callback
        )
        
    def upload_all_patients(self):
        """Upload patients with TF4M integration."""
        if not self.project_manager.project_data:
            messagebox.showerror("Error", "No project data available")
            return
        
        all_patients = self.project_manager.project_data.patients
        if not all_patients:
            messagebox.showinfo("Info", "No patients available for upload")
            return
        
        # Show upload dialog to get user preferences
        upload_dialog = UploadDialog(self.root, all_patients)
        result = upload_dialog.show()
        
        if not result or result['action'] == 'cancel':
            return
        
        selected_patients = result['patients']
        
        # Switch to upload manager tab
        self.notebook.select(self.upload_manager.frame)
        
        # Start upload process with selected patients
        self.upload_manager.start_bulk_upload(selected_patients)
        
    def test_api_connection(self):
        """Test the API connection."""
        success, message = self.api_client.test_connection()
        if success:
            messagebox.showinfo("Connection Test", "API connection successful!")
        else:
            messagebox.showerror("Connection Test", f"API connection failed: {message}")
            
    def open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self.root, self.api_client)
        # Reload settings after dialog closes to ensure API client has latest credentials
        self.load_and_apply_settings()
        
    def generate_report(self):
        """Generate and display a validation report."""
        if not self.project_manager.project_data:
            messagebox.showerror("Error", "No project data available")
            return
            
        report = self.project_manager.get_validation_report()
        
        # Create a new window to display the report
        report_window = tk.Toplevel(self.root)
        report_window.title("Validation Report")
        report_window.geometry("800x600")
        
        # Create text widget with scrollbar
        frame = ttk.Frame(report_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Format and insert report
        self._format_report(text_widget, report)
        text_widget.config(state=tk.DISABLED)
        
    def _format_report(self, text_widget, report):
        """Format the validation report for display."""
        text_widget.insert(tk.END, "DENTAL DATA VALIDATION REPORT\n")
        text_widget.insert(tk.END, "=" * 50 + "\n\n")
        
        # Summary
        text_widget.insert(tk.END, f"Total Patients: {report['total_patients']}\n")
        text_widget.insert(tk.END, f"Complete Patients: {report['complete_patients']}\n")
        text_widget.insert(tk.END, f"Incomplete Patients: {report['incomplete_patients']}\n\n")
        
        # Global errors
        if report['global_errors']:
            text_widget.insert(tk.END, "GLOBAL ERRORS:\n")
            for error in report['global_errors']:
                text_widget.insert(tk.END, f"  - {error}\n")
            text_widget.insert(tk.END, "\n")
        
        # Patient details
        text_widget.insert(tk.END, "PATIENT DETAILS:\n")
        text_widget.insert(tk.END, "-" * 30 + "\n")
        
        for patient in report['patient_details']:
            text_widget.insert(tk.END, f"\nPatient: {patient['patient_id']}\n")
            text_widget.insert(tk.END, f"  Status: {'COMPLETE' if patient['is_complete'] else 'INCOMPLETE'}\n")
            
            if patient['missing_data_types']:
                text_widget.insert(tk.END, f"  Missing: {', '.join(patient['missing_data_types'])}\n")
                
            if patient['unmatched_files'] > 0:
                text_widget.insert(tk.END, f"  Unmatched files: {patient['unmatched_files']}\n")
                
            # File counts
            counts = patient['file_counts']
            text_widget.insert(tk.END, f"  Files: CBCT({counts['cbct_files']}), ")
            text_widget.insert(tk.END, f"Photos({counts['intraoral_photos']}), ")
            text_widget.insert(tk.END, f"IOS Upper({'✓' if counts['has_ios_upper'] else '✗'}), ")
            text_widget.insert(tk.END, f"IOS Lower({'✓' if counts['has_ios_lower'] else '✗'}), ")
            text_widget.insert(tk.END, f"Tele({'✓' if counts['has_teleradiography'] else '✗'}), ")
            text_widget.insert(tk.END, f"Ortho({'✓' if counts['has_orthopantomography'] else '✗'})\n")
            
            if patient['validation_errors']:
                text_widget.insert(tk.END, "  Errors:\n")
                for error in patient['validation_errors']:
                    text_widget.insert(tk.END, f"    - {error}\n")
                    
    def show_about(self):
        """Show about dialog."""
        about_text = """Dental Data Management Application
        
Version 1.0
        
This application helps organize and upload dental patient data
including CBCT scans, IOS files, intraoral photos, and radiographs
to a Django backend system.

Developed for TF4M"""
        
        messagebox.showinfo("About", about_text)
    
    # Cache management methods
    
    def view_cache_stats(self):
        """Show cache statistics."""
        self.patient_browser.view_cache_stats()
    
    def clear_current_patient_cache(self):
        """Clear cache for currently selected patient."""
        self.patient_browser.clear_patient_cache()
    
    def clear_all_cache(self):
        """Clear all cache entries."""
        self.patient_browser.clear_all_cache()
