"""
Upload dialog for TF4M integration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from core.models import PatientData

class UploadDialog:
    """Dialog for selecting upload options."""
    
    def __init__(self, parent, patients: List[PatientData]):
        self.parent = parent
        self.patients = patients
        self.result = None
        
        # Count complete and incomplete patients
        self.complete_patients = [p for p in patients if p.is_complete() or p.manually_complete]
        self.incomplete_patients = [p for p in patients if not (p.is_complete() or p.manually_complete)]
        
        self.setup_dialog()
    
    def setup_dialog(self):
        """Setup the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Upload to TF4M")
        self.dialog.geometry("500x600")  # Increased height from 400 to 600
        self.dialog.minsize(450, 550)    # Set minimum size
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self.create_widgets()
        
        # Set focus and make modal
        self.dialog.focus_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Upload Patients to TF4M", 
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Patient statistics
        stats_frame = ttk.LabelFrame(main_frame, text="Patient Summary")
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        stats_inner = ttk.Frame(stats_frame)
        stats_inner.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(stats_inner, text=f"Total patients: {len(self.patients)}").pack(anchor=tk.W)
        ttk.Label(stats_inner, text=f"Complete patients: {len(self.complete_patients)}").pack(anchor=tk.W)
        ttk.Label(stats_inner, text=f"Incomplete patients: {len(self.incomplete_patients)}").pack(anchor=tk.W)
        
        # Upload options
        options_frame = ttk.LabelFrame(main_frame, text="Upload Options")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        options_inner = ttk.Frame(options_frame)
        options_inner.pack(fill=tk.X, padx=10, pady=10)
        
        self.upload_choice = tk.StringVar(value="complete_only")
        
        # Option 1: Complete patients only
        ttk.Radiobutton(
            options_inner,
            text=f"Upload complete patients only ({len(self.complete_patients)} patients)",
            variable=self.upload_choice,
            value="complete_only"
        ).pack(anchor=tk.W, pady=2)
        
        # Option 2: All patients
        ttk.Radiobutton(
            options_inner,
            text=f"Upload all patients ({len(self.patients)} patients)",
            variable=self.upload_choice,
            value="all_patients"
        ).pack(anchor=tk.W, pady=2)
        
        # Warning for incomplete patients
        if self.incomplete_patients:
            warning_frame = ttk.Frame(main_frame)
            warning_frame.pack(fill=tk.X, pady=(0, 10))
            
            warning_label = ttk.Label(
                warning_frame,
                text="⚠️ Note: Incomplete patients may not upload successfully",
                foreground="orange"
            )
            warning_label.pack(anchor=tk.W)
        
        # Upload behavior explanation
        behavior_frame = ttk.LabelFrame(main_frame, text="Upload Behavior")
        behavior_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        behavior_text = tk.Text(behavior_frame, height=5, wrap=tk.WORD, state=tk.DISABLED)
        behavior_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        behavior_info = (
            "• Check if patients already exist on TF4M server\n"
            "• For existing patients: compare file hashes and upload only new/changed files\n" 
            "• For new patients: create patient and upload all files\n"
            "• Update local cache with upload status and remote patient IDs\n"
            "• Skip patients that are already up-to-date"
        )
        
        behavior_text.config(state=tk.NORMAL)
        behavior_text.insert(tk.END, behavior_info)
        behavior_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))  # Added top padding for spacing
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Start Upload",
            command=self.on_upload,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)
    
    def on_upload(self):
        """Handle upload button click."""
        choice = self.upload_choice.get()
        
        if choice == "complete_only":
            if not self.complete_patients:
                messagebox.showwarning(
                    "No Complete Patients", 
                    "There are no complete patients to upload."
                )
                return
            selected_patients = self.complete_patients
        else:  # all_patients
            if not self.patients:
                messagebox.showwarning(
                    "No Patients", 
                    "There are no patients to upload."
                )
                return
            selected_patients = self.patients
        
        # Confirm upload
        confirm_message = (
            f"Upload {len(selected_patients)} patient(s) to TF4M?\n\n"
            f"This will:\n"
            f"• Check for existing patients on the server\n"
            f"• Upload new or changed files\n"
            f"• Update local cache with upload status"
        )
        
        if messagebox.askyesno("Confirm Upload", confirm_message):
            self.result = {
                'action': 'upload',
                'patients': selected_patients,
                'choice': choice
            }
            self.dialog.destroy()
    
    def on_cancel(self):
        """Handle cancel button click."""
        self.result = {'action': 'cancel'}
        self.dialog.destroy()
    
    def show(self) -> Optional[dict]:
        """Show the dialog and return the result."""
        self.parent.wait_window(self.dialog)
        return self.result