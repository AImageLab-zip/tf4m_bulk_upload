"""
Bulk file mapping dialog for the GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import re

from core.models import PatientData, DataType, MatchStatus, FileData

class BulkMappingDialog:
    """Dialog for bulk file mapping operations."""
    
    def __init__(self, parent, patient_data: PatientData, callback=None):
        self.parent = parent
        self.patient_data = patient_data
        self.callback = callback
        self.dialog = None
        self.result = None
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create the bulk mapping dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Bulk Mapping - {self.patient_data.patient_id}")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"800x600+{x}+{y}")
        
        self.setup_ui()
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
    def setup_ui(self):
        """Setup the user interface."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title and status
        self.create_header(main_frame)
        
        # Notebook for different mapping methods
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Smart auto-mapping tab
        self.create_smart_mapping_tab()
        
        # Pattern mapping tab
        self.create_pattern_mapping_tab()
        
        # Bulk assignment tab
        self.create_bulk_assignment_tab()
        
        # Interactive mapping tab
        self.create_interactive_mapping_tab()
        
        # Buttons
        self.create_buttons(main_frame)
        
    def create_header(self, parent):
        """Create header with patient info and status."""
        header_frame = ttk.LabelFrame(parent, text="Patient Information")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Patient info
        ttk.Label(info_frame, text=f"Patient: {self.patient_data.patient_id}", 
                 font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        all_files = self.patient_data.get_all_files()
        unmatched_count = len(self.patient_data.unmatched_files)
        matched_count = len(all_files) - unmatched_count
        
        ttk.Label(info_frame, text=f"Total Files: {len(all_files)} | "
                                  f"Matched: {matched_count} | "
                                  f"Unmatched: {unmatched_count}").pack(anchor=tk.W)
        
        # Missing data types
        missing_types = self.patient_data.get_missing_data_types()
        if missing_types:
            missing_str = ", ".join([dt.value for dt in missing_types])
            ttk.Label(info_frame, text=f"Missing: {missing_str}", 
                     foreground="red").pack(anchor=tk.W)
        else:
            ttk.Label(info_frame, text="All required data types present", 
                     foreground="green").pack(anchor=tk.W)
    
    def create_smart_mapping_tab(self):
        """Create smart auto-mapping tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎯 Smart Auto-Mapping")
        
        # Description
        desc_frame = ttk.LabelFrame(frame, text="Description")
        desc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        desc_text = ("Smart auto-mapping analyzes file names and extensions to automatically "
                    "assign them to the correct data types. This is the recommended starting point.")
        ttk.Label(desc_frame, text=desc_text, wraplength=700, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Options
        options_frame = ttk.LabelFrame(frame, text="Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.smart_cbct_var = tk.BooleanVar(value=True)
        self.smart_stl_var = tk.BooleanVar(value=True)
        self.smart_images_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Auto-map DICOM files (.dcm) to CBCT", 
                       variable=self.smart_cbct_var).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="Auto-map STL files to IOS scans", 
                       variable=self.smart_stl_var).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="Auto-map image files to appropriate types", 
                       variable=self.smart_images_var).pack(anchor=tk.W, padx=10, pady=2)
        
        # Run button
        ttk.Button(options_frame, text="🚀 Run Smart Auto-Mapping", 
                  command=self.run_smart_mapping).pack(pady=10)
        
        # Results
        self.smart_results_text = tk.Text(frame, height=10, state=tk.DISABLED)
        self.smart_results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        smart_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.smart_results_text.yview)
        self.smart_results_text.configure(yscrollcommand=smart_scroll.set)
        
    def create_pattern_mapping_tab(self):
        """Create pattern-based mapping tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔍 Pattern Mapping")
        
        # Description
        desc_frame = ttk.LabelFrame(frame, text="Description")
        desc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        desc_text = ("Pattern mapping allows you to select files based on filename patterns "
                    "and assign them to a specific data type.")
        ttk.Label(desc_frame, text=desc_text, wraplength=700, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Controls
        controls_frame = ttk.LabelFrame(frame, text="Pattern Configuration")
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Pattern entry
        pattern_row = ttk.Frame(controls_frame)
        pattern_row.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(pattern_row, text="Pattern:").pack(side=tk.LEFT)
        self.pattern_entry = ttk.Entry(pattern_row, width=30)
        self.pattern_entry.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(pattern_row, text="Preview", command=self.preview_pattern).pack(side=tk.LEFT, padx=5)
        
        # Examples
        examples_frame = ttk.Frame(controls_frame)
        examples_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(examples_frame, text="Examples: dcm, slice, upper, stl, .jpg").pack(side=tk.LEFT)
        
        # Data type selection
        type_row = ttk.Frame(controls_frame)
        type_row.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(type_row, text="Assign to:").pack(side=tk.LEFT)
        self.pattern_type_var = tk.StringVar()
        type_combo = ttk.Combobox(type_row, textvariable=self.pattern_type_var, 
                                 values=self.get_data_type_names(), state="readonly", width=25)
        type_combo.pack(side=tk.LEFT, padx=(10, 5))
        type_combo.set("CBCT DICOM")
        
        ttk.Button(type_row, text="🎯 Map Selected Files", 
                  command=self.run_pattern_mapping).pack(side=tk.LEFT, padx=10)
        
        # Preview area
        preview_frame = ttk.LabelFrame(frame, text="File Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.pattern_preview_tree = ttk.Treeview(preview_frame, columns=("path",), show="tree headings")
        self.pattern_preview_tree.heading("#0", text="Filename")
        self.pattern_preview_tree.heading("path", text="Path")
        self.pattern_preview_tree.column("#0", width=200)
        self.pattern_preview_tree.column("path", width=400)
        
        preview_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, 
                                     command=self.pattern_preview_tree.yview)
        self.pattern_preview_tree.configure(yscrollcommand=preview_scroll.set)
        
        self.pattern_preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_bulk_assignment_tab(self):
        """Create bulk assignment tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📋 Bulk Assignment")
        
        # Description
        desc_frame = ttk.LabelFrame(frame, text="Description")
        desc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        desc_text = ("Bulk assignment allows you to assign ALL unmatched files to a single "
                    "data type. Use this when you know all remaining files belong to one category.")
        ttk.Label(desc_frame, text=desc_text, wraplength=700, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Controls
        controls_frame = ttk.LabelFrame(frame, text="Assignment Configuration")
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        control_row = ttk.Frame(controls_frame)
        control_row.pack(padx=10, pady=10)
        
        ttk.Label(control_row, text="Assign ALL unmatched files to:").pack(side=tk.LEFT)
        
        self.bulk_type_var = tk.StringVar()
        bulk_combo = ttk.Combobox(control_row, textvariable=self.bulk_type_var,
                                 values=self.get_data_type_names(), state="readonly", width=25)
        bulk_combo.pack(side=tk.LEFT, padx=(10, 5))
        bulk_combo.set("CBCT DICOM")
        
        ttk.Button(control_row, text="📋 Assign All Files", 
                  command=self.run_bulk_assignment).pack(side=tk.LEFT, padx=10)
        
        # Warning
        warning_frame = ttk.Frame(frame)
        warning_frame.pack(fill=tk.X, padx=10, pady=10)
        
        warning_text = ("⚠️ WARNING: This will assign ALL unmatched files to the selected type. "
                       "This action affects all files at once!")
        ttk.Label(warning_frame, text=warning_text, wraplength=700, 
                 foreground="red", font=("Arial", 10, "bold")).pack()
        
        # File list
        list_frame = ttk.LabelFrame(frame, text="Files to be Assigned")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.bulk_files_listbox = tk.Listbox(list_frame)
        bulk_list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                        command=self.bulk_files_listbox.yview)
        self.bulk_files_listbox.configure(yscrollcommand=bulk_list_scroll.set)
        
        self.bulk_files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bulk_list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_bulk_file_list()
        
    def create_interactive_mapping_tab(self):
        """Create interactive mapping tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎮 Interactive Mapping")
        
        # Description
        desc_frame = ttk.LabelFrame(frame, text="Description")
        desc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        desc_text = ("Interactive mapping allows you to go through unmatched files one by one "
                    "and manually assign them to the correct data types.")
        ttk.Label(desc_frame, text=desc_text, wraplength=700, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Current file info
        self.current_file_frame = ttk.LabelFrame(frame, text="Current File")
        self.current_file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.current_file_label = ttk.Label(self.current_file_frame, text="No files to map", 
                                           font=("Arial", 12, "bold"))
        self.current_file_label.pack(padx=10, pady=5)
        
        self.current_path_label = ttk.Label(self.current_file_frame, text="")
        self.current_path_label.pack(padx=10, pady=5)
        
        # Data type selection
        selection_frame = ttk.LabelFrame(frame, text="Assign to Data Type")
        selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.interactive_type_var = tk.StringVar()
        
        # Create radio buttons for data types
        self.data_type_buttons = {}
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(padx=10, pady=10)
        
        data_types = [
            (DataType.CBCT_DICOM, "🦷 CBCT DICOM"),
            (DataType.IOS_UPPER, "🔝 IOS Upper"),
            (DataType.IOS_LOWER, "🔽 IOS Lower"),
            (DataType.TELERADIOGRAPHY, "📻 Teleradiography"),
            (DataType.ORTHOPANTOMOGRAPHY, "🔬 Orthopantomography"),
            (DataType.INTRAORAL_PHOTO, "📸 Intraoral Photo")
        ]
        
        for i, (data_type, label) in enumerate(data_types):
            btn = ttk.Radiobutton(button_frame, text=label, 
                                 variable=self.interactive_type_var,
                                 value=data_type.value)
            btn.grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=2)
            self.data_type_buttons[data_type] = btn
            
        # Navigation buttons
        nav_frame = ttk.Frame(selection_frame)
        nav_frame.pack(padx=10, pady=10)
        
        ttk.Button(nav_frame, text="⏮️ Previous", command=self.interactive_previous).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="✅ Assign & Next", command=self.interactive_assign_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="⏭️ Skip", command=self.interactive_skip).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="⏸️ Finish", command=self.interactive_finish).pack(side=tk.LEFT, padx=5)
        
        # Progress
        progress_frame = ttk.Frame(frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.interactive_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.interactive_progress.pack(fill=tk.X, pady=5)
        
        self.interactive_progress_label = ttk.Label(progress_frame, text="")
        self.interactive_progress_label.pack()
        
        # Initialize interactive mode
        self.interactive_index = 0
        self.interactive_files = self.patient_data.unmatched_files[:]
        self.update_interactive_display()
        
    def create_buttons(self, parent):
        """Create dialog buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="✅ Apply Changes", 
                  command=self.on_apply).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="❌ Cancel", 
                  command=self.on_cancel).pack(side=tk.RIGHT)
        
    def get_data_type_names(self):
        """Get list of data type names for comboboxes."""
        return [
            "CBCT DICOM",
            "IOS Upper", 
            "IOS Lower",
            "Teleradiography",
            "Orthopantomography",
            "Intraoral Photo"
        ]
        
    def get_data_type_from_name(self, name):
        """Convert display name to DataType enum."""
        mapping = {
            "CBCT DICOM": DataType.CBCT_DICOM,
            "IOS Upper": DataType.IOS_UPPER,
            "IOS Lower": DataType.IOS_LOWER,
            "Teleradiography": DataType.TELERADIOGRAPHY,
            "Orthopantomography": DataType.ORTHOPANTOMOGRAPHY,
            "Intraoral Photo": DataType.INTRAORAL_PHOTO
        }
        return mapping.get(name)
        
    def run_smart_mapping(self):
        """Run smart auto-mapping."""
        self.smart_results_text.config(state=tk.NORMAL)
        self.smart_results_text.delete(1.0, tk.END)
        
        mappings_made = 0
        files_to_remove = []
        
        self.smart_results_text.insert(tk.END, "🎯 Starting Smart Auto-Mapping...\n\n")
        
        for file_data in self.patient_data.unmatched_files:
            filename_lower = file_data.filename.lower()
            suggested_type = None
            
            # CBCT DICOM detection
            if self.smart_cbct_var.get() and (
                filename_lower.endswith('.dcm') or 
                'slice' in filename_lower or 
                '3d' in filename_lower or
                'cbct' in filename_lower):
                suggested_type = DataType.CBCT_DICOM
                
            # STL file patterns
            elif self.smart_stl_var.get() and filename_lower.endswith('.stl'):
                if any(keyword in filename_lower for keyword in ['upper', 'max', 'superiore', 'mascella', 'mascellare', 'maxilla', 'maxillari', 'maxillar','maxillary']):
                    suggested_type = DataType.IOS_UPPER
                elif any(keyword in filename_lower for keyword in ['lower', 'man', 'inferiore', 'mandibola', 'mandibolar', 'mandible', 'mandibular']):
                    suggested_type = DataType.IOS_LOWER
                    
            if suggested_type:
                self.smart_results_text.insert(tk.END, f"📄 {file_data.filename} → {suggested_type.value}\n")
                
                file_data.data_type = suggested_type
                file_data.confidence = 0.8
                file_data.status = MatchStatus.MATCHED
                
                self.assign_file_to_patient(file_data)
                files_to_remove.append(file_data)
                mappings_made += 1
        
        # Remove mapped files
        for file_data in files_to_remove:
            self.patient_data.unmatched_files.remove(file_data)
            
        self.smart_results_text.insert(tk.END, f"\n✅ Auto-mapped {mappings_made} files\n")
        
        if mappings_made == 0:
            self.smart_results_text.insert(tk.END, "ℹ️ No files could be auto-mapped.\n")
            
        self.smart_results_text.config(state=tk.DISABLED)
        
        # Update other tabs
        self.update_bulk_file_list()
        self.interactive_files = self.patient_data.unmatched_files[:]
        self.interactive_index = 0
        self.update_interactive_display()
        
    def preview_pattern(self):
        """Preview files matching the current pattern."""
        pattern = self.pattern_entry.get().strip().lower()
        if not pattern:
            return
            
        # Clear previous results
        for item in self.pattern_preview_tree.get_children():
            self.pattern_preview_tree.delete(item)
            
        matching_files = []
        for file_data in self.patient_data.unmatched_files:
            if pattern in file_data.filename.lower():
                matching_files.append(file_data)
                
        for file_data in matching_files:
            self.pattern_preview_tree.insert("", "end", text=file_data.filename, 
                                            values=(file_data.path,))
    
    def run_pattern_mapping(self):
        """Run pattern-based mapping."""
        pattern = self.pattern_entry.get().strip().lower()
        type_name = self.pattern_type_var.get()
        
        if not pattern or not type_name:
            messagebox.showerror("Error", "Please enter a pattern and select a data type.")
            return
            
        data_type = self.get_data_type_from_name(type_name)
        if not data_type:
            messagebox.showerror("Error", "Invalid data type selected.")
            return
            
        # Find matching files
        matching_files = []
        for file_data in self.patient_data.unmatched_files:
            if pattern in file_data.filename.lower():
                matching_files.append(file_data)
                
        if not matching_files:
            messagebox.showinfo("No Matches", f"No files found matching pattern '{pattern}'")
            return
            
        # Confirm mapping
        result = messagebox.askyesno("Confirm Mapping", 
                                   f"Map {len(matching_files)} files to {type_name}?")
        if not result:
            return
            
        # Map the files
        for file_data in matching_files:
            file_data.data_type = data_type
            file_data.confidence = 0.9
            file_data.status = MatchStatus.MATCHED
            
            self.assign_file_to_patient(file_data)
            self.patient_data.unmatched_files.remove(file_data)
            
        messagebox.showinfo("Success", f"Mapped {len(matching_files)} files to {type_name}")
        
        # Update displays
        self.preview_pattern()
        self.update_bulk_file_list()
        self.interactive_files = self.patient_data.unmatched_files[:]
        self.interactive_index = 0
        self.update_interactive_display()
        
    def run_bulk_assignment(self):
        """Run bulk assignment of all files."""
        type_name = self.bulk_type_var.get()
        
        if not type_name:
            messagebox.showerror("Error", "Please select a data type.")
            return
            
        data_type = self.get_data_type_from_name(type_name)
        if not data_type:
            messagebox.showerror("Error", "Invalid data type selected.")
            return
            
        if not self.patient_data.unmatched_files:
            messagebox.showinfo("No Files", "No unmatched files to assign.")
            return
            
        # Confirm bulk assignment
        result = messagebox.askyesno("Confirm Bulk Assignment", 
                                   f"Assign ALL {len(self.patient_data.unmatched_files)} "
                                   f"unmatched files to {type_name}?\n\n"
                                   f"This action cannot be undone!")
        if not result:
            return
            
        # Assign all files
        files_to_assign = self.patient_data.unmatched_files[:]
        for file_data in files_to_assign:
            file_data.data_type = data_type
            file_data.confidence = 0.7
            file_data.status = MatchStatus.MATCHED
            
            self.assign_file_to_patient(file_data)
            self.patient_data.unmatched_files.remove(file_data)
            
        messagebox.showinfo("Success", f"Assigned all {len(files_to_assign)} files to {type_name}")
        
        # Update displays
        self.update_bulk_file_list()
        self.interactive_files = self.patient_data.unmatched_files[:]
        self.interactive_index = 0
        self.update_interactive_display()
        
    def update_bulk_file_list(self):
        """Update the bulk assignment file list."""
        self.bulk_files_listbox.delete(0, tk.END)
        for file_data in self.patient_data.unmatched_files:
            self.bulk_files_listbox.insert(tk.END, file_data.filename)
            
    def update_interactive_display(self):
        """Update the interactive mapping display."""
        if not self.interactive_files:
            self.current_file_label.config(text="No more files to map")
            self.current_path_label.config(text="")
            self.interactive_progress_label.config(text="Complete!")
            self.interactive_progress.config(value=100)
            return
            
        if self.interactive_index >= len(self.interactive_files):
            self.current_file_label.config(text="All files processed")
            self.current_path_label.config(text="")
            self.interactive_progress_label.config(text="Complete!")
            self.interactive_progress.config(value=100)
            return
            
        current_file = self.interactive_files[self.interactive_index]
        self.current_file_label.config(text=current_file.filename)
        self.current_path_label.config(text=current_file.path)
        
        # Update progress
        total_files = len(self.interactive_files)
        progress = ((self.interactive_index + 1) / total_files) * 100 if total_files > 0 else 100
        self.interactive_progress.config(value=progress)
        self.interactive_progress_label.config(text=f"File {self.interactive_index + 1} of {total_files}")
        
    def interactive_previous(self):
        """Go to previous file in interactive mode."""
        if self.interactive_index > 0:
            self.interactive_index -= 1
            self.update_interactive_display()
            
    def interactive_assign_next(self):
        """Assign current file and go to next."""
        if not self.interactive_files or self.interactive_index >= len(self.interactive_files):
            return
            
        type_value = self.interactive_type_var.get()
        if not type_value:
            messagebox.showerror("Error", "Please select a data type.")
            return
            
        # Convert value to DataType enum
        data_type = None
        for dt in DataType:
            if dt.value == type_value:
                data_type = dt
                break
                
        if not data_type:
            messagebox.showerror("Error", "Invalid data type selected.")
            return
            
        # Assign the file
        current_file = self.interactive_files[self.interactive_index]
        current_file.data_type = data_type
        current_file.confidence = 1.0
        current_file.status = MatchStatus.MATCHED
        
        self.assign_file_to_patient(current_file)
        self.patient_data.unmatched_files.remove(current_file)
        self.interactive_files.remove(current_file)
        
        # Don't increment index since we removed a file
        self.update_interactive_display()
        self.update_bulk_file_list()
        
    def interactive_skip(self):
        """Skip current file."""
        self.interactive_index += 1
        self.update_interactive_display()
        
    def interactive_finish(self):
        """Finish interactive mapping."""
        self.interactive_index = len(self.interactive_files)
        self.update_interactive_display()
        
    def assign_file_to_patient(self, file_data):
        """Assign a file to the appropriate patient data attribute."""
        if file_data.data_type == DataType.CBCT_DICOM:
            self.patient_data.cbct_files.append(file_data)
        elif file_data.data_type == DataType.IOS_UPPER:
            self.patient_data.ios_upper = file_data
        elif file_data.data_type == DataType.IOS_LOWER:
            self.patient_data.ios_lower = file_data
        elif file_data.data_type == DataType.TELERADIOGRAPHY:
            self.patient_data.teleradiography = file_data
        elif file_data.data_type == DataType.ORTHOPANTOMOGRAPHY:
            self.patient_data.orthopantomography = file_data
        elif file_data.data_type == DataType.INTRAORAL_PHOTO:
            self.patient_data.intraoral_photos.append(file_data)
            
    def on_apply(self):
        """Apply changes and close dialog."""
        self.result = "apply"
        if self.callback:
            self.callback()
        self.dialog.destroy()
        
    def on_cancel(self):
        """Cancel and close dialog."""
        self.result = "cancel"
        self.dialog.destroy()
