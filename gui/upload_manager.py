"""
Upload manager widget for handling patient data uploads to TF4M.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Dict, Any
import time
import os
import json
from datetime import datetime, timedelta
import threading

from core.models import PatientData
from core.api_client import TF4MAPIClient, APIClient
from core.match_cache import MatchCache

class UploadManager:
    """Widget for managing patient data uploads to TF4M."""
    
    def __init__(self, parent, api_client):
        self.parent = parent
        self.api_client = api_client
        self.cache = MatchCache()  # For upload status tracking
        self.upload_queue: List[PatientData] = []
        self.current_upload: Optional[PatientData] = None
        self.upload_stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "estimated_finish": None
        }
        self.settings = self._load_settings()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.frame = ttk.Frame(self.parent)
        
        # Main container
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Upload controls
        self.create_upload_controls(main_frame)
        
        # Progress section
        self.create_progress_section(main_frame)
        
        # Upload queue
        self.create_queue_section(main_frame)
        
        # Log section
        self.create_log_section(main_frame)
        
    def create_upload_controls(self, parent):
        """Create upload control widgets."""
        controls_frame = ttk.LabelFrame(parent, text="Upload Controls")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = ttk.Button(
            button_frame,
            text="Start Upload",
            command=self.start_upload,
            state="disabled"
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.pause_btn = ttk.Button(
            button_frame,
            text="Pause",
            command=self.pause_upload,
            state="disabled"
        )
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_upload,
            state="disabled"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(
            button_frame,
            text="Clear Queue",
            command=self.clear_queue
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Upload settings
        settings_frame = ttk.Frame(controls_frame)
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(settings_frame, text="Concurrent uploads:").pack(side=tk.LEFT)
        self.concurrent_var = tk.IntVar(value=1)
        concurrent_spin = ttk.Spinbox(
            settings_frame,
            from_=1,
            to=5,
            width=5,
            textvariable=self.concurrent_var
        )
        concurrent_spin.pack(side=tk.LEFT, padx=(5, 20))
        
        self.retry_failed_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings_frame,
            text="Retry failed uploads",
            variable=self.retry_failed_var
        ).pack(side=tk.LEFT)
        
    def create_progress_section(self, parent):
        """Create progress display section."""
        progress_frame = ttk.LabelFrame(parent, text="Upload Progress")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Overall progress
        overall_frame = ttk.Frame(progress_frame)
        overall_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(overall_frame, text="Overall Progress:").pack(side=tk.LEFT)
        
        self.overall_progress = ttk.Progressbar(
            overall_frame,
            length=300,
            mode='determinate'
        )
        self.overall_progress.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        self.overall_label_var = tk.StringVar(value="0/0 (0%)")
        ttk.Label(overall_frame, textvariable=self.overall_label_var).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Current patient progress
        current_frame = ttk.Frame(progress_frame)
        current_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.current_patient_var = tk.StringVar(value="No upload in progress")
        ttk.Label(current_frame, textvariable=self.current_patient_var, font=("Arial", 9)).pack(side=tk.LEFT)
        
        self.current_progress = ttk.Progressbar(
            current_frame,
            length=300,
            mode='determinate'
        )
        self.current_progress.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        self.current_label_var = tk.StringVar(value="")
        ttk.Label(current_frame, textvariable=self.current_label_var).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Statistics
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.stats_var = tk.StringVar(value="Ready")
        ttk.Label(stats_frame, textvariable=self.stats_var, font=("Arial", 8)).pack(side=tk.LEFT)
        
        self.eta_var = tk.StringVar(value="")
        ttk.Label(stats_frame, textvariable=self.eta_var, font=("Arial", 8)).pack(side=tk.RIGHT)
        
    def create_queue_section(self, parent):
        """Create upload queue section."""
        queue_frame = ttk.LabelFrame(parent, text="Upload Queue")
        queue_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Queue treeview
        columns = ("status", "files", "size")
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show="tree headings", height=8)
        
        # Configure columns
        self.queue_tree.heading("#0", text="Patient ID")
        self.queue_tree.heading("status", text="Status")
        self.queue_tree.heading("files", text="Files")
        self.queue_tree.heading("size", text="Size")
        
        self.queue_tree.column("#0", width=150)
        self.queue_tree.column("status", width=100)
        self.queue_tree.column("files", width=80)
        self.queue_tree.column("size", width=100)
        
        # Scrollbars
        queue_v_scroll = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_tree.yview)
        queue_h_scroll = ttk.Scrollbar(queue_frame, orient=tk.HORIZONTAL, command=self.queue_tree.xview)
        self.queue_tree.configure(yscrollcommand=queue_v_scroll.set, xscrollcommand=queue_h_scroll.set)
        
        # Pack widgets
        self.queue_tree.grid(row=0, column=0, sticky="nsew")
        queue_v_scroll.grid(row=0, column=1, sticky="ns")
        queue_h_scroll.grid(row=1, column=0, sticky="ew")
        
        queue_frame.grid_rowconfigure(0, weight=1)
        queue_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.queue_context_menu = tk.Menu(queue_frame, tearoff=0)
        self.queue_context_menu.add_command(label="Remove from Queue", command=self.remove_from_queue)
        self.queue_context_menu.add_command(label="Move to Top", command=self.move_to_top)
        self.queue_context_menu.add_command(label="Retry Upload", command=self.retry_upload)
        
        self.queue_tree.bind("<Button-3>", self.show_queue_context_menu)
        
    def create_log_section(self, parent):
        """Create upload log section."""
        log_frame = ttk.LabelFrame(parent, text="Upload Log")
        log_frame.pack(fill=tk.X)
        
        # Log text widget
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(log_controls, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="Save Log", command=self.save_log).pack(side=tk.LEFT, padx=(10, 0))
        
    def start_bulk_upload(self, patients: List[PatientData]):
        """Start bulk upload of multiple patients."""
        self.upload_queue = patients.copy()
        self.upload_stats["total"] = len(patients)
        self.upload_stats["completed"] = 0
        self.upload_stats["failed"] = 0
        self.upload_stats["skipped"] = 0
        self.upload_stats["start_time"] = datetime.now()
        
        self.populate_queue_tree()
        self.start_btn.config(state="normal")
        self.log_message(f"Added {len(patients)} patients to upload queue")
        
    def populate_queue_tree(self):
        """Populate the queue tree with patients."""
        # Clear existing items
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
            
        for patient in self.upload_queue:
            status = patient.upload_status if hasattr(patient, 'upload_status') else "Pending"
            file_count = len(patient.get_all_files())
            estimated_size = self.estimate_patient_size(patient)
            
            self.queue_tree.insert(
                "",
                tk.END,
                text=patient.patient_id,
                values=(status, file_count, estimated_size),
                tags=(status.lower(),)
            )
            
        # Configure tags
        self.queue_tree.tag_configure("pending", foreground="blue")
        self.queue_tree.tag_configure("processing", foreground="purple")
        self.queue_tree.tag_configure("uploading", foreground="orange")
        self.queue_tree.tag_configure("completed", foreground="green")
        self.queue_tree.tag_configure("failed", foreground="red")
        self.queue_tree.tag_configure("skipped", foreground="gray")
        
    def estimate_patient_size(self, patient: PatientData) -> str:
        """Estimate the total size of patient files."""
        total_size = 0
        try:
            for file_data in patient.get_all_files():
                if hasattr(file_data, 'path') and file_data.path:
                    try:
                        total_size += os.path.getsize(file_data.path)
                    except:
                        pass
        except:
            pass
            
        # Format size
        if total_size < 1024:
            return f"{total_size} B"
        elif total_size < 1024 * 1024:
            return f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            return f"{total_size / (1024 * 1024):.1f} MB"
        else:
            return f"{total_size / (1024 * 1024 * 1024):.1f} GB"
            
    def start_upload(self):
        """Start the upload process."""
        if not self.upload_queue:
            messagebox.showinfo("Info", "No patients in upload queue")
            return
            
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        
        self.log_message("Starting upload process...")
        
        # Start upload thread
        self.upload_thread = threading.Thread(target=self.upload_worker, daemon=True)
        self.upload_thread.start()
        
    def upload_worker(self):
        """Worker thread for uploading patients with TF4M integration."""
        while self.upload_queue:
            patient = self.upload_queue.pop(0)
            self.current_upload = patient
            
            # Update UI
            self.frame.after(0, lambda p=patient: self.current_patient_var.set(f"Processing: {p.patient_id}"))
            self.frame.after(0, lambda p=patient: self.update_queue_item_status(p.patient_id, "Processing"))
            
            # Check upload cache status first
            #cache_status = self.cache.get_upload_status(patient.folder_path)
            cache_status = False
            if cache_status and cache_status.get('status') == 'uploaded':
                # Skip already uploaded patients
                self.upload_stats["skipped"] += 1
                self.frame.after(0, lambda p=patient: self.update_queue_item_status(p.patient_id, "Skipped"))
                self.frame.after(0, lambda p=patient: self.log_message(f"⏩ {p.patient_id}: Already uploaded, skipping"))
                self.frame.after(0, self.update_overall_progress)
                continue
            
            # Update cache: mark as uploading
            self.cache.update_upload_status(patient.folder_path, "uploading")
            
            # Upload patient
            def progress_callback(*args):
                """Handle progress updates with flexible arguments.
                Can be called as:
                - progress_callback(message) for status updates
                - progress_callback(current, total, message) for file progress
                """
                if len(args) == 1:
                    # Just a status message
                    message = args[0]
                    self.frame.after(0, lambda m=message: self.log_message(f"  {m}"))
                elif len(args) == 3:
                    # File progress: current, total, message
                    current, total, message = args
                    self.frame.after(0, lambda c=current, t=total, m=message: self.update_current_progress(c, t, m))
                
            def completion_callback(success, message, patient_ref=patient):
                if success:
                    self.upload_stats["completed"] += 1
                    
                    # Try to extract remote patient ID from success message
                    remote_patient_id = None
                    if "patient '" in message and "'" in message:
                        # Extract patient name for ID lookup
                        try:
                            # This would need to be implemented based on actual TF4M response
                            remote_patient_id = None  # Placeholder
                        except:
                            pass
                    
                    # Update cache with successful upload
                    self.cache.update_upload_status(
                        patient_ref.folder_path, 
                        "uploaded", 
                        remote_patient_id=remote_patient_id
                    )
                    
                    self.frame.after(0, lambda p=patient_ref: self.update_queue_item_status(p.patient_id, "Completed"))
                    self.frame.after(0, lambda p=patient_ref, m=message: self.log_message(f"✓ {p.patient_id}: {m}"))
                else:
                    self.upload_stats["failed"] += 1
                    
                    # Update cache with failed upload
                    self.cache.update_upload_status(
                        patient_ref.folder_path, 
                        "failed", 
                        error_message=message
                    )
                    
                    self.frame.after(0, lambda p=patient_ref: self.update_queue_item_status(p.patient_id, "Failed"))
                    self.frame.after(0, lambda p=patient_ref, m=message: self.log_message(f"✗ {p.patient_id}: {m}"))
                    
                self.frame.after(0, self.update_overall_progress)
                
            try:
                self.frame.after(0, lambda p=patient: self.update_queue_item_status(p.patient_id, "Uploading"))
                
                # Get delete_before_reupload setting
                delete_before_reupload = self.settings.get("delete_before_reupload", True)
                
                success, message = self.api_client.upload_patient_data(
                    patient, 
                    progress_callback,
                    delete_before_reupload=delete_before_reupload
                )
                completion_callback(success, message)
            except Exception as e:
                completion_callback(False, str(e))
                
        # Upload complete
        self.frame.after(0, self.upload_complete)
        
    def update_current_progress(self, current: int, total: int, message: str):
        """Update current patient progress."""
        progress = (current / total * 100) if total > 0 else 0
        self.current_progress.config(value=progress)
        self.current_label_var.set(f"{current}/{total}")
        
    def update_overall_progress(self):
        """Update overall progress."""
        completed = self.upload_stats["completed"] + self.upload_stats["failed"] + self.upload_stats["skipped"]
        total = self.upload_stats["total"]
        progress = (completed / total * 100) if total > 0 else 0
        
        self.overall_progress.config(value=progress)
        self.overall_label_var.set(f"{completed}/{total} ({progress:.1f}%)")
        
        # Update statistics
        stats_text = f"Completed: {self.upload_stats['completed']}, Failed: {self.upload_stats['failed']}"
        if self.upload_stats['skipped'] > 0:
            stats_text += f", Skipped: {self.upload_stats['skipped']}"
        self.stats_var.set(stats_text)
        
        # Estimate completion time
        if self.upload_stats["start_time"] and completed > 0:
            elapsed = datetime.now() - self.upload_stats["start_time"]
            avg_time_per_patient = elapsed / completed
            remaining = total - completed
            eta = datetime.now() + (avg_time_per_patient * remaining)
            self.eta_var.set(f"ETA: {eta.strftime('%H:%M:%S')}")
            
    def update_queue_item_status(self, patient_id: str, status: str):
        """Update the status of a queue item."""
        for item in self.queue_tree.get_children():
            if self.queue_tree.item(item, "text") == patient_id:
                values = list(self.queue_tree.item(item, "values"))
                values[0] = status
                self.queue_tree.item(item, values=values, tags=(status.lower(),))
                break
                
    def upload_complete(self):
        """Handle upload completion."""
        self.current_upload = None
        self.current_patient_var.set("Upload complete")
        self.current_progress.config(value=0)
        self.current_label_var.set("")
        
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        
        completed = self.upload_stats["completed"]
        failed = self.upload_stats["failed"]
        skipped = self.upload_stats["skipped"]
        total = self.upload_stats["total"]
        
        self.log_message(f"Upload complete: {completed} successful, {failed} failed, {skipped} skipped out of {total} patients")
        
        if failed > 0:
            messagebox.showwarning("Upload Complete", 
                                 f"Upload completed with {failed} failures and {skipped} skipped.\nCheck the log for details.")
        else:
            messagebox.showinfo("Upload Complete", 
                               f"All patients processed successfully!\n{completed} uploaded, {skipped} already up-to-date.")
            
    def pause_upload(self):
        """Pause the upload process."""
        # Implementation would depend on how we want to handle pausing
        # For now, just disable the button
        self.pause_btn.config(state="disabled")
        self.log_message("Upload paused")
        
    def stop_upload(self):
        """Stop the upload process."""
        # Clear the queue to stop further uploads
        self.upload_queue.clear()
        self.log_message("Upload stopped by user")
        
    def clear_queue(self):
        """Clear the upload queue."""
        self.upload_queue.clear()
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        self.log_message("Upload queue cleared")
        
    def show_queue_context_menu(self, event):
        """Show context menu for queue items."""
        item = self.queue_tree.identify_row(event.y)
        if item:
            self.queue_tree.selection_set(item)
            self.queue_context_menu.post(event.x_root, event.y_root)
            
    def remove_from_queue(self):
        """Remove selected item from queue."""
        selection = self.queue_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        patient_id = self.queue_tree.item(item, "text")
        
        # Remove from queue
        self.upload_queue = [p for p in self.upload_queue if p.patient_id != patient_id]
        self.queue_tree.delete(item)
        
        self.log_message(f"Removed {patient_id} from queue")
        
    def move_to_top(self):
        """Move selected item to top of queue."""
        selection = self.queue_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        patient_id = self.queue_tree.item(item, "text")
        
        # Find and move patient in queue
        patient = None
        for i, p in enumerate(self.upload_queue):
            if p.patient_id == patient_id:
                patient = self.upload_queue.pop(i)
                break
                
        if patient:
            self.upload_queue.insert(0, patient)
            self.populate_queue_tree()
            self.log_message(f"Moved {patient_id} to top of queue")
            
    def retry_upload(self):
        """Retry upload for selected patient."""
        selection = self.queue_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        patient_id = self.queue_tree.item(item, "text")
        
        # Find patient and add back to queue
        # This would require keeping a reference to failed patients
        self.log_message(f"Retry not yet implemented for {patient_id}")
        
    def log_message(self, message: str):
        """Add a message to the upload log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def clear_log(self):
        """Clear the upload log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def save_log(self):
        """Save the upload log to a file."""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Save Upload Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {str(e)}")
    
    def _load_settings(self):
        """Load settings from settings.json."""
        settings_file = "settings.json"
        default_settings = {
            "delete_before_reupload": True
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
        except Exception:
            pass  # Use default settings if loading fails
            
        return default_settings
