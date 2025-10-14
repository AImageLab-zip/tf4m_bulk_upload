"""
Patient browser widget for viewing and managing patient data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
import os

from core.models import ProjectData, PatientData, DataType
from core.project_manager import ProjectManager
from .bulk_mapping_dialog import BulkMappingDialog

class PatientBrowser:
    """Widget for browsing and managing patient data."""
    
    def __init__(self, parent, project_manager: ProjectManager):
        self.parent = parent
        self.project_manager = project_manager
        self.project_data: Optional[ProjectData] = None
        self.current_patient: Optional[PatientData] = None
        self.data_type_labels = {}  # Initialize dictionary for completeness overview
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.frame = ttk.Frame(self.parent)
        
        # Create paned window for split view
        self.paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - patient list
        self.create_patient_list()
        
        # Right panel - patient details
        self.create_patient_details()
        
    def create_patient_list(self):
        """Create the patient list widget."""
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=1)
        
        # Header
        ttk.Label(left_frame, text="Patients", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Filter controls
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', self.filter_patients)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Status filter
        self.status_filter_var = tk.StringVar(value="all")
        status_frame = ttk.Frame(left_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        status_combo = ttk.Combobox(
            status_frame, 
            textvariable=self.status_filter_var,
            values=["all", "complete", "incomplete"],
            state="readonly",
            width=15
        )
        status_combo.pack(side=tk.LEFT, padx=(5, 0))
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_patients())
        
        # Patient list
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for patient list
        columns = ("status", "missing", "files")
        self.patient_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings")
        
        # Configure columns
        self.patient_tree.heading("#0", text="Patient ID")
        self.patient_tree.heading("status", text="Status")
        self.patient_tree.heading("missing", text="Missing")
        self.patient_tree.heading("files", text="Files")
        
        self.patient_tree.column("#0", width=150)
        self.patient_tree.column("status", width=80)
        self.patient_tree.column("missing", width=60)
        self.patient_tree.column("files", width=60)
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.patient_tree.yview)
        self.patient_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.patient_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.patient_tree.bind('<<TreeviewSelect>>', self.on_patient_select)
        
    def create_patient_details(self):
        """Create the patient details widget."""
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=2)
        
        # Header
        self.details_header = ttk.Label(right_frame, text="Select a patient to view details", 
                                       font=("Arial", 12, "bold"))
        self.details_header.pack(pady=(0, 10))
        
        # Toolbar for patient actions
        self.create_patient_toolbar(right_frame)
        
        # Notebook for different detail tabs
        self.details_notebook = ttk.Notebook(right_frame)
        self.details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Files tab
        self.create_files_tab()
        
        # Conflicts tab
        self.create_conflicts_tab()
        
    def create_patient_toolbar(self, parent):
        """Create toolbar with patient actions."""
        self.toolbar_frame = ttk.Frame(parent)
        self.toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Bulk mapping button
        self.bulk_mapping_btn = ttk.Button(
            self.toolbar_frame, 
            text="🎯 Bulk Mapping", 
            command=self.open_bulk_mapping,
            state=tk.DISABLED
        )
        self.bulk_mapping_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Smart auto-map button (quick action)
        self.smart_map_btn = ttk.Button(
            self.toolbar_frame,
            text="🚀 Smart Auto-Map",
            command=self.run_smart_auto_map,
            state=tk.DISABLED
        )
        self.smart_map_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Separator
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Manual completion controls
        self.manual_complete_var = tk.BooleanVar()
        self.manual_complete_cb = ttk.Checkbutton(
            self.toolbar_frame,
            text="✓ Manually Complete",
            variable=self.manual_complete_var,
            command=self.toggle_manual_completion,
            state=tk.DISABLED
        )
        self.manual_complete_cb.pack(side=tk.LEFT, padx=(0, 5))
        
        # Another separator
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Status info
        self.status_label = ttk.Label(self.toolbar_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
    def create_files_tab(self):
        """Create the files tab."""
        files_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(files_frame, text="Files")
        
        # Completeness Overview Section
        self.create_completeness_overview(files_frame)
        
        # Separator
        ttk.Separator(files_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Files treeview section
        tree_label = ttk.Label(files_frame, text="All Files", font=("Arial", 10, "bold"))
        tree_label.pack(anchor=tk.W, padx=5)
        
        tree_container = ttk.Frame(files_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Files treeview
        file_columns = ("type", "path", "status")
        self.files_tree = ttk.Treeview(tree_container, columns=file_columns, show="tree headings")
        
        # Configure columns
        self.files_tree.heading("#0", text="Filename")
        self.files_tree.heading("type", text="Type")
        self.files_tree.heading("path", text="Path")
        self.files_tree.heading("status", text="Status")
        
        self.files_tree.column("#0", width=250)
        self.files_tree.column("type", width=120)
        self.files_tree.column("path", width=300)
        self.files_tree.column("status", width=80)
        
        # Configure styles for adaptive row heights
        style = ttk.Style()
        style.configure("FilesPreview.Treeview", rowheight=25)  # Default compact height
        self.files_tree.configure(style="FilesPreview.Treeview")
        
        # Image cache to prevent garbage collection
        self.image_cache = {}
        
        # Scrollbars
        files_v_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.files_tree.yview)
        files_h_scroll = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=files_v_scroll.set, xscrollcommand=files_h_scroll.set)
        
        # Pack widgets
        self.files_tree.grid(row=0, column=0, sticky="nsew")
        files_v_scroll.grid(row=0, column=1, sticky="ns")
        files_h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Context menu for files
        self.files_context_menu = tk.Menu(tree_container, tearoff=0)
        self.files_context_menu.add_command(label="Reassign Type...", command=self.reassign_file_type)
        self.files_context_menu.add_command(label="Open File", command=self.open_file)
        self.files_context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)
        
        self.files_tree.bind("<Button-3>", self.show_files_context_menu)
        self.files_tree.bind("<Double-1>", self.on_file_double_click)
        
    def on_file_double_click(self, event):
        """Handle double-click on file items."""
        item = self.files_tree.selection()[0] if self.files_tree.selection() else None
        if not item:
            return
            
        # Get the file path from the item
        values = self.files_tree.item(item, "values")
        if len(values) >= 2:  # Has path column
            file_path = values[1]  # Path is second column
            
            # Check if it's an image file
            if file_path and self.is_image_file(file_path):
                self.show_image_preview(file_path)
            else:
                self.open_file()  # Default file opening behavior
    
    def is_image_file(self, file_path):
        """Check if file is a supported image format (excluding DICOM/STL)."""
        file_lower = file_path.lower()
        
        # Skip DICOM and STL files
        if file_lower.endswith('.dcm') or file_lower.endswith('.stl'):
            return False
            
        # Check for supported image formats
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif')
        return any(file_lower.endswith(fmt) for fmt in supported_formats)
    
    def show_image_preview(self, file_path):
        """Show a larger preview of an image file."""
        try:
            from PIL import Image, ImageTk
            import os
            
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "File not found!")
                return
                
            # Create preview window
            preview_window = tk.Toplevel(self.parent)
            preview_window.title(f"Image Preview - {os.path.basename(file_path)}")
            preview_window.geometry("800x600")
            
            # Create frame for image
            image_frame = ttk.Frame(preview_window)
            image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Load and display image
            image = Image.open(file_path)
            
            # Calculate size to fit window while preserving aspect ratio
            max_size = (750, 550)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            
            # Create label to display image
            image_label = ttk.Label(image_frame, image=photo)
            image_label.pack(expand=True)
            
            # Keep a reference to prevent garbage collection
            image_label.image = photo
            
            # Add file info
            info_frame = ttk.Frame(preview_window)
            info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            ttk.Label(info_frame, text=f"File: {os.path.basename(file_path)}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Path: {file_path}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Size: {image.size[0]} x {image.size[1]} pixels").pack(anchor=tk.W)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not preview image: {str(e)}")
        
    def create_completeness_overview(self, parent):
        """Create a comprehensive completeness overview section."""
        overview_frame = ttk.LabelFrame(parent, text="📊 Patient Data Completeness Overview")
        overview_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create grid layout for data types
        self.data_type_labels = {}
        
        # Header row
        header_frame = ttk.Frame(overview_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="Data Type", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Label(header_frame, text="Status", font=("Arial", 9, "bold")).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Label(header_frame, text="Count", font=("Arial", 9, "bold")).grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
        ttk.Label(header_frame, text="Details", font=("Arial", 9, "bold")).grid(row=0, column=3, sticky=tk.W)
        
        # Data type rows
        self.data_type_frame = ttk.Frame(overview_frame)
        self.data_type_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Define required data types with descriptions
        self.required_data_types = [
            (DataType.CBCT_DICOM, "🦷 CBCT DICOM Files", "Required", "Cone beam CT scan slices"),
            (DataType.IOS_UPPER, "🔝 IOS Upper Jaw", "Required", "Upper jaw intraoral scan (STL)"),
            (DataType.IOS_LOWER, "🔽 IOS Lower Jaw", "Required", "Lower jaw intraoral scan (STL)"),
            (DataType.TELERADIOGRAPHY, "📻 Teleradiography", "Required", "Lateral cephalometric X-ray"),
            (DataType.ORTHOPANTOMOGRAPHY, "🔬 Orthopantomography", "Required", "Panoramic X-ray"),
            (DataType.INTRAORAL_PHOTO, "📸 Intraoral Photos", "Optional", "Clinical photographs")
        ]
        
        # Create labels for each data type
        for i, (data_type, display_name, requirement, description) in enumerate(self.required_data_types):
            row_frame = ttk.Frame(self.data_type_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            # Data type name
            name_label = ttk.Label(row_frame, text=display_name, font=("Arial", 9))
            name_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
            
            # Status indicator
            status_label = ttk.Label(row_frame, text="❓ Unknown", font=("Arial", 9))
            status_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
            
            # Count
            count_label = ttk.Label(row_frame, text="0", font=("Arial", 9))
            count_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
            
            # Details
            details_label = ttk.Label(row_frame, text=description, font=("Arial", 8), foreground="gray")
            details_label.grid(row=0, column=3, sticky=tk.W)
            
            # Store references for updating
            self.data_type_labels[data_type] = {
                'status': status_label,
                'count': count_label,
                'details': details_label,
                'requirement': requirement
            }
        
        # Overall status section
        status_summary_frame = ttk.Frame(overview_frame)
        status_summary_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        self.overall_status_label = ttk.Label(
            status_summary_frame, 
            text="Select a patient to view completeness status",
            font=("Arial", 11, "bold")
        )
        self.overall_status_label.pack(side=tk.LEFT)
        
        # Unmatched files indicator
        self.unmatched_files_label = ttk.Label(
            status_summary_frame,
            text="",
            font=("Arial", 9)
        )
        self.unmatched_files_label.pack(side=tk.RIGHT)
        
    def create_conflicts_tab(self):
        """Create the conflicts/issues tab."""
        conflicts_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(conflicts_frame, text="Issues")
        
        # Issues text widget
        self.issues_text = tk.Text(conflicts_frame, wrap=tk.WORD, state=tk.DISABLED)
        issues_scrollbar = ttk.Scrollbar(conflicts_frame, orient=tk.VERTICAL, command=self.issues_text.yview)
        self.issues_text.configure(yscrollcommand=issues_scrollbar.set)
        
        self.issues_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        issues_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def load_project_data(self, project_data: ProjectData):
        """Load project data into the browser."""
        self.project_data = project_data
        self.populate_patient_list()
        
    def populate_patient_list(self):
        """Populate the patient list."""
        # Clear existing items
        for item in self.patient_tree.get_children():
            self.patient_tree.delete(item)
            
        if not self.project_data:
            return
            
        for patient in self.project_data.patients:
            is_complete = patient.is_complete()
            missing_count = len(patient.get_missing_data_types())
            total_files = len(patient.get_all_files())
            
            # Determine status text and tag
            if patient.manually_complete:
                status_text = "✓M"  # M for Manual
                status = "manual"
            elif is_complete:
                status_text = "✓"
                status = "complete"
            else:
                status_text = "⚠"
                status = "incomplete"
            
            self.patient_tree.insert(
                "", 
                tk.END, 
                text=patient.patient_id,
                values=(status_text, missing_count, total_files),
                tags=(status,)
            )
        
        # Configure tags for visual styling
        self.patient_tree.tag_configure("complete", foreground="green")
        self.patient_tree.tag_configure("incomplete", foreground="orange")
        self.patient_tree.tag_configure("manual", foreground="blue")
    
    def update_patient_list(self):
        """Update the patient list (alias for populate_patient_list)."""
        self.populate_patient_list()
        
    def filter_patients(self, *args):
        """Filter the patient list based on current filters."""
        if not self.project_data:
            return
            
        # Get filter values
        text_filter = self.filter_var.get().lower()
        status_filter = self.status_filter_var.get()
        
        # Clear current items
        for item in self.patient_tree.get_children():
            self.patient_tree.delete(item)
            
        # Apply filters
        for patient in self.project_data.patients:
            # Text filter
            if text_filter and text_filter not in patient.patient_id.lower():
                continue
                
            # Status filter
            is_complete = patient.is_complete()
            if status_filter == "complete" and not is_complete:
                continue
            elif status_filter == "incomplete" and is_complete:
                continue
                
            # Add patient to tree with proper status indication
            missing_count = len(patient.get_missing_data_types())
            total_files = len(patient.get_all_files())
            
            # Determine status text and tag
            if patient.manually_complete:
                status_text = "✓M"  # M for Manual
                status = "manual"
            elif is_complete:
                status_text = "✓"
                status = "complete"
            else:
                status_text = "⚠"
                status = "incomplete"
            
            self.patient_tree.insert(
                "",
                tk.END,
                text=patient.patient_id,
                values=(status_text, missing_count, total_files),
                tags=(status,)
            )
            
    def on_patient_select(self, event):
        """Handle patient selection."""
        selection = self.patient_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        patient_id = self.patient_tree.item(item, "text")
        
        # Find patient data
        patient = self.project_manager.get_patient_by_id(patient_id)
        if patient:
            self.show_patient_details(patient)
            
    def show_patient_details(self, patient: PatientData):
        """Show details for the selected patient."""
        self.current_patient = patient
        self.details_header.config(text=f"Patient: {patient.patient_id}")
        
        # Enable toolbar buttons
        self.bulk_mapping_btn.config(state=tk.NORMAL)
        self.smart_map_btn.config(state=tk.NORMAL)
        self.manual_complete_cb.config(state=tk.NORMAL)
        
        # Update manual completion checkbox
        self.manual_complete_var.set(patient.manually_complete)
        
        # Update status label
        unmatched_count = len(patient.unmatched_files)
        missing_types = len(patient.get_missing_data_types())
        
        if patient.manually_complete:
            status_text = "✅ Manually Complete"
            self.status_label.config(text=status_text, foreground="blue")
        elif unmatched_count > 0 or missing_types > 0:
            self.status_label.config(
                text=f"⚠️ {unmatched_count} unmatched files, {missing_types} missing types",
                foreground="red"
            )
        else:
            self.status_label.config(text="✅ Complete", foreground="green")
        
        # Update completeness overview
        self.update_completeness_overview(patient)
        
        # Update files tab
        self.populate_files_tree(patient)
        
        # Update issues tab
        self.populate_issues_text(patient)
        
    def update_completeness_overview(self, patient: PatientData):
        """Update the completeness overview section."""
        missing_types = patient.get_missing_data_types()
        
        # Update each data type status
        for data_type, display_name, requirement, description in self.required_data_types:
            labels = self.data_type_labels[data_type]
            
            # Determine status and count
            if data_type == DataType.CBCT_DICOM:
                count = len(patient.cbct_files)
                status = "✅ Present" if count > 0 else "❌ Missing"
                status_color = "green" if count > 0 else "red"
                details_text = f"{count} DICOM files found" if count > 0 else "No CBCT DICOM files detected"
                
            elif data_type == DataType.IOS_UPPER:
                has_file = patient.ios_upper is not None
                count = 1 if has_file else 0
                status = "✅ Present" if has_file else "❌ Missing"
                status_color = "green" if has_file else "red"
                details_text = f"File: {patient.ios_upper.filename}" if has_file else "No upper jaw scan found"
                
            elif data_type == DataType.IOS_LOWER:
                has_file = patient.ios_lower is not None
                count = 1 if has_file else 0
                status = "✅ Present" if has_file else "❌ Missing"
                status_color = "green" if has_file else "red"
                details_text = f"File: {patient.ios_lower.filename}" if has_file else "No lower jaw scan found"
                
            elif data_type == DataType.TELERADIOGRAPHY:
                has_file = patient.teleradiography is not None
                count = 1 if has_file else 0
                status = "✅ Present" if has_file else "❌ Missing"
                status_color = "green" if has_file else "red"
                details_text = f"File: {patient.teleradiography.filename}" if has_file else "No teleradiography found"
                
            elif data_type == DataType.ORTHOPANTOMOGRAPHY:
                has_file = patient.orthopantomography is not None
                count = 1 if has_file else 0
                status = "✅ Present" if has_file else "❌ Missing"
                status_color = "green" if has_file else "red"
                details_text = f"File: {patient.orthopantomography.filename}" if has_file else "No orthopantomography found"
                
            elif data_type == DataType.INTRAORAL_PHOTO:
                count = len(patient.intraoral_photos)
                status = "✅ Present" if count > 0 else "⚠️ Optional"
                status_color = "green" if count > 0 else "orange"
                details_text = f"{count} intraoral photos found" if count > 0 else "No intraoral photos (optional)"
            
            else:
                count = 0
                status = "❓ Unknown"
                status_color = "gray"
                details_text = "Unknown data type"
            
            # Update labels
            labels['status'].config(text=status, foreground=status_color)
            labels['count'].config(text=str(count))
            labels['details'].config(text=details_text)
        
        # Update overall status
        required_missing = [dt for dt in missing_types if dt != DataType.INTRAORAL_PHOTO]
        unmatched_count = len(patient.unmatched_files)
        
        if not required_missing and unmatched_count == 0:
            overall_status = "✅ COMPLETE - All required data types present"
            overall_color = "green"
        elif required_missing:
            missing_names = [dt.value.replace('_', ' ').title() for dt in required_missing]
            overall_status = f"❌ INCOMPLETE - Missing: {', '.join(missing_names)}"
            overall_color = "red"
        elif unmatched_count > 0:
            overall_status = f"⚠️ NEEDS ATTENTION - {unmatched_count} unmatched files"
            overall_color = "orange"
        else:
            overall_status = "❓ Status unknown"
            overall_color = "gray"
        
        self.overall_status_label.config(text=overall_status, foreground=overall_color)
        
        # Update unmatched files indicator
        if unmatched_count > 0:
            self.unmatched_files_label.config(
                text=f"📄 {unmatched_count} unmatched files need mapping",
                foreground="orange"
            )
        else:
            self.unmatched_files_label.config(text="", foreground="black")
    
    def create_thumbnail(self, file_path, size=(100, 70)):
        """Create a thumbnail for image files."""
        try:
            # Check if it's an image file and not DICOM/STL
            file_lower = file_path.lower()
            
            # Skip DICOM and STL files
            if file_lower.endswith('.dcm') or file_lower.endswith('.stl'):
                return None
                
            # Check for supported image formats
            supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif')
            if not any(file_lower.endswith(fmt) for fmt in supported_formats):
                return None
                
            # Check if already cached
            cache_key = f"{file_path}_{size}"
            if cache_key in self.image_cache:
                return self.image_cache[cache_key]
                
            # Import PIL here to avoid import errors if not available
            from PIL import Image, ImageTk
            import os
            
            # Check if file exists and is not empty
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return None
                
            # Open and process image
            with Image.open(file_path) as image:
                # Convert RGBA to RGB if necessary (for JPEG compatibility)
                if image.mode in ('RGBA', 'LA'):
                    # Create white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'RGBA':
                        background.paste(image, mask=image.split()[-1])
                    else:
                        background.paste(image)
                    image = background
                elif image.mode == 'P':
                    image = image.convert('RGB')
                    
                # Create thumbnail while preserving aspect ratio
                image_copy = image.copy()
                image_copy.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Create a new image with padding to center the thumbnail
                thumb_width, thumb_height = image_copy.size
                max_width, max_height = size
                
                # Create a new image with light gray background for better contrast
                padded_image = Image.new('RGB', size, (248, 248, 248))
                
                # Calculate position to center the thumbnail
                x = (max_width - thumb_width) // 2
                y = (max_height - thumb_height) // 2
                
                # Paste the thumbnail onto the padded image
                padded_image.paste(image_copy, (x, y))
                
                # Create PhotoImage
                photo = ImageTk.PhotoImage(padded_image)
                
                # Cache the image (limit cache size to prevent memory issues)
                if len(self.image_cache) > 50:  # Clear cache if it gets too large
                    self.image_cache.clear()
                    
                self.image_cache[cache_key] = photo
                
                return photo
            
        except Exception as e:
            # Silently fail for unsupported files or errors
            print(f"Warning: Could not create thumbnail for {file_path}: {e}")
            return None
        
    def populate_files_tree(self, patient: PatientData):
        """Populate the files tree with patient files grouped by type."""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Separate excluded files from regular files
        excluded_files = []
        
        # Helper function to filter and collect excluded files
        def filter_excluded(files_list):
            """Separate excluded files from a list and return non-excluded files"""
            if not files_list:
                return []
            regular = []
            for file_data in files_list:
                if file_data and file_data.data_type == DataType.EXCLUDE:
                    excluded_files.append(file_data)
                else:
                    regular.append(file_data)
            return regular
        
        # Filter CBCT files
        cbct_files_filtered = filter_excluded(patient.cbct_files)
        
        # Filter IOS files
        ios_upper_filtered = []
        if patient.ios_upper:
            if patient.ios_upper.data_type == DataType.EXCLUDE:
                excluded_files.append(patient.ios_upper)
            else:
                ios_upper_filtered = [patient.ios_upper]
        
        ios_lower_filtered = []
        if patient.ios_lower:
            if patient.ios_lower.data_type == DataType.EXCLUDE:
                excluded_files.append(patient.ios_lower)
            else:
                ios_lower_filtered = [patient.ios_lower]
        
        # Filter teleradiography
        teleradiography_filtered = []
        if patient.teleradiography:
            if patient.teleradiography.data_type == DataType.EXCLUDE:
                excluded_files.append(patient.teleradiography)
            else:
                teleradiography_filtered = [patient.teleradiography]
        
        # Filter orthopantomography
        orthopantomography_filtered = []
        if patient.orthopantomography:
            if patient.orthopantomography.data_type == DataType.EXCLUDE:
                excluded_files.append(patient.orthopantomography)
            else:
                orthopantomography_filtered = [patient.orthopantomography]
        
        # Filter intraoral photos
        intraoral_filtered = filter_excluded(patient.intraoral_photos)
        
        # Group files by data type (now with filtered lists)
        file_groups = {
            "🦷 CBCT DICOM": cbct_files_filtered,
            "🔝 IOS Upper": ios_upper_filtered,
            "🔽 IOS Lower": ios_lower_filtered,
            "📻 Teleradiography": teleradiography_filtered,
            "🔬 Orthopantomography": orthopantomography_filtered,
            "📸 Intraoral Photos": intraoral_filtered,
            "❓ Unmatched Files": patient.unmatched_files
        }
        
        # Add NIfTI conversion info for CBCT
        cbct_group_name = "🦷 CBCT DICOM"
        if cbct_files_filtered:
            if patient.nifti_conversion_status == "completed" and patient.nifti_conversion_path:
                nifti_info = patient.nifti_conversion_info
                size_info = f" - NIfTI: {nifti_info.get('file_size_mb', 'Unknown')} MB" if nifti_info else ""
                cbct_group_name = f"🦷 CBCT DICOM (✓ Converted{size_info})"
            elif patient.nifti_conversion_status == "converting":
                cbct_group_name = "🦷 CBCT DICOM (🔄 Converting...)"
            elif patient.nifti_conversion_status == "failed":
                cbct_group_name = "🦷 CBCT DICOM (❌ Conversion Failed)"
            else:
                cbct_group_name = "🦷 CBCT DICOM (⏳ Not Converted)"
        
        # Add zip package group if it exists
        zip_group_name = None
        if patient.zip_package_path and os.path.exists(patient.zip_package_path):
            zip_info = patient.zip_package_info
            size_info = f" ({zip_info.get('file_size_mb', 'Unknown')} MB)" if zip_info else ""
            zip_group_name = f"📦 Patient Package{size_info}"
        
        # Update the group name in the dictionary
        if "🦷 CBCT DICOM" in file_groups:
            file_groups[cbct_group_name] = file_groups.pop("🦷 CBCT DICOM")
        
        # Add zip package group if it exists
        if zip_group_name and patient.zip_package_path:
            file_groups[zip_group_name] = [type('ZipFileData', (), {
                'path': patient.zip_package_path,
                'filename': os.path.basename(patient.zip_package_path),
                'data_type': None,
                'status': None
            })()]
        
        # Add excluded files group at the end if there are any
        if excluded_files:
            file_groups[f"🚫 Excluded Files"] = excluded_files
        
        # Determine if we have any image files that need previews
        has_image_files = False
        total_image_files = 0
        
        for group_name, files in file_groups.items():
            for file_data in files:
                if self.is_image_file(file_data.path):
                    has_image_files = True
                    total_image_files += 1
        
        # Set appropriate row height based on content
        style = ttk.Style()
        
        # Use tall rows if we have any image files (simplified logic)
        if has_image_files:
            style.configure("FilesPreview.Treeview", rowheight=80)
        else:
            style.configure("FilesPreview.Treeview", rowheight=25)
        
        # Add groups to tree
        for group_name, files in file_groups.items():
            if not files:  # Skip empty groups
                continue
            
            # Determine if this group should be expanded by default
            # Expand: Teleradiography, Orthopantomography, and Intraoral Photos
            should_expand = any(keyword in group_name for keyword in [
                "Teleradiography", 
                "Orthopantomography", 
                "Intraoral Photos"
            ])
                
            # Create group header
            group_id = self.files_tree.insert(
                "",
                tk.END,
                text=f"{group_name} ({len(files)} files)",
                values=("", "", ""),
                open=should_expand
            )
            
            # Configure group header appearance
            if "🚫" in group_name:
                self.files_tree.set(group_id, "status", "EXCLUDED")
                group_tag = "excluded_group"
            elif "❓" in group_name:
                self.files_tree.set(group_id, "status", "NEEDS MAPPING")
                group_tag = "unmatched_group"
            elif len(files) > 0:
                self.files_tree.set(group_id, "status", "COMPLETE")
                group_tag = "complete_group" 
            else:
                self.files_tree.set(group_id, "status", "MISSING")
                group_tag = "missing_group"
                
            self.files_tree.item(group_id, tags=(group_tag,))
            
            # Determine if we should show thumbnails for this view
            # Simplified: always show thumbnails for image files
            show_thumbnails = has_image_files
            
            # Add files to group
            for file_data in files:
                # Handle special zip package file
                if hasattr(file_data, 'filename') and file_data.filename.endswith('.zip') and "Package" in group_name:
                    file_id = self.files_tree.insert(
                        group_id,
                        tk.END,
                        text=file_data.filename,
                        values=("ZIP Package", file_data.path, "packaged"),
                        tags=("packaged",)
                    )
                    continue
                
                data_type = file_data.data_type.value if file_data.data_type else "Unknown"
                status = file_data.status.value if hasattr(file_data, 'status') else "Unknown"
                
                # Check if file is excluded
                is_excluded = file_data.data_type == DataType.EXCLUDE
                # Check if we're in the excluded group (don't duplicate the EXCLUDED label)
                in_excluded_group = "🚫" in group_name
                
                # Create thumbnail for image files
                thumbnail = None
                
                if self.is_image_file(file_data.path):
                    # Always try to create thumbnails for image files
                    thumbnail = self.create_thumbnail(file_data.path, size=(100, 70))
                    if thumbnail:
                        print(f"✅ Created thumbnail for: {file_data.filename}")
                    else:
                        print(f"❌ Failed to create thumbnail for: {file_data.filename}")
                
                # Only add "(EXCLUDED)" prefix if NOT in excluded group (to avoid redundancy)
                if is_excluded and not in_excluded_group:
                    display_name = f"🚫 {file_data.filename} (EXCLUDED)"
                else:
                    display_name = file_data.filename
                    
                file_tags = (status, "excluded") if is_excluded else (status,)
                
                file_id = self.files_tree.insert(
                    group_id,
                    tk.END,
                    text=display_name,
                    values=(data_type, file_data.path, status),
                    tags=file_tags,
                    image=thumbnail if thumbnail else ""
                )
            
            # Add NIfTI file for CBCT group if it exists
            if "CBCT DICOM" in group_name and patient.nifti_conversion_path and os.path.exists(patient.nifti_conversion_path):
                nifti_file_id = self.files_tree.insert(
                    group_id,
                    tk.END,
                    text=f"📁 {os.path.basename(patient.nifti_conversion_path)} (Converted NIfTI)",
                    values=("NIfTI", patient.nifti_conversion_path, "converted"),
                    tags=("converted",)
                )
        
        # Configure tags for visual feedback
        self.files_tree.tag_configure("matched", foreground="green")
        self.files_tree.tag_configure("unmatched", foreground="red") 
        self.files_tree.tag_configure("manual", foreground="blue", font=("Arial", 9, "bold"))
        self.files_tree.tag_configure("ambiguous", foreground="orange")
        self.files_tree.tag_configure("converted", foreground="blue", font=("Arial", 9, "italic"))
        self.files_tree.tag_configure("packaged", foreground="purple", font=("Arial", 9, "bold"))
        self.files_tree.tag_configure("excluded", foreground="gray", font=("Arial", 9, "italic"))
        
        # Configure group tags
        self.files_tree.tag_configure("complete_group", foreground="green", font=("Arial", 10, "bold"))
        self.files_tree.tag_configure("unmatched_group", foreground="red", font=("Arial", 10, "bold"))
        self.files_tree.tag_configure("missing_group", foreground="gray", font=("Arial", 10, "bold"))
        self.files_tree.tag_configure("excluded_group", foreground="gray", font=("Arial", 10, "bold"))
        
    def populate_issues_text(self, patient: PatientData):
        """Populate the issues text widget."""
        self.issues_text.config(state=tk.NORMAL)
        self.issues_text.delete(1.0, tk.END)
        
        # Missing data types
        missing_types = patient.get_missing_data_types()
        if missing_types:
            self.issues_text.insert(tk.END, "MISSING DATA TYPES:\n")
            for data_type in missing_types:
                self.issues_text.insert(tk.END, f"  - {data_type.value}\n")
            self.issues_text.insert(tk.END, "\n")
            
        # Unmatched files
        if patient.unmatched_files:
            self.issues_text.insert(tk.END, "UNMATCHED FILES:\n")
            for file_data in patient.unmatched_files:
                self.issues_text.insert(tk.END, f"  - {file_data.filename} ({file_data.path})\n")
            self.issues_text.insert(tk.END, "\n")
            
        # Validation errors
        if patient.validation_errors:
            self.issues_text.insert(tk.END, "VALIDATION ERRORS:\n")
            for error in patient.validation_errors:
                self.issues_text.insert(tk.END, f"  - {error}\n")
            self.issues_text.insert(tk.END, "\n")
            
        if not missing_types and not patient.unmatched_files and not patient.validation_errors:
            self.issues_text.insert(tk.END, "No issues found. Patient data is complete!")
            
        self.issues_text.config(state=tk.DISABLED)
        
    def show_files_context_menu(self, event):
        """Show context menu for files tree."""
        item = self.files_tree.identify_row(event.y)
        if item:
            self.files_tree.selection_set(item)
            self.files_context_menu.post(event.x_root, event.y_root)
            
    def reassign_file_type(self):
        """Reassign the type of the selected file."""
        selection = self.files_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        filename = self.files_tree.item(item, "text")
        file_path = self.files_tree.item(item, "values")[1]
        
        # Check if file still exists
        if not os.path.exists(file_path):
            result = messagebox.askyesno(
                "File Not Found",
                f"The file no longer exists:\n\n{filename}\n\n"
                f"Path: {file_path}\n\n"
                f"The file may have been moved or deleted from the patient folder.\n\n"
                f"Do you want to remove this file from the patient data and cache?",
                icon='warning'
            )
            if result:
                # Remove the file from patient data
                success, message = self._remove_missing_file_from_patient(file_path)
                if success:
                    # Update cache to reflect the removal
                    self._update_patient_cache()
                    
                    # Refresh the display
                    self.show_patient_details(self.current_patient)
                    self.populate_patient_list()
                    
                    messagebox.showinfo("Success", f"File removed from patient data and cache:\n\n{filename}\n\n{message}")
                else:
                    messagebox.showerror("Error", f"Failed to remove file from patient data.\n\n{message}")
            return
        
        # Create dialog for type selection
        dialog = ReassignTypeDialog(self.frame, filename)
        new_type = dialog.result
        
        if new_type:
            # Update the file assignment
            success = self.project_manager.update_patient_file_assignment(
                self.current_patient.patient_id,
                file_path,
                new_type
            )
            
            if success:
                # Update cache with manual reassignment
                self._update_patient_cache()
                
                # Refresh the display
                self.show_patient_details(self.current_patient)
                self.populate_patient_list()  # Update patient list status
                messagebox.showinfo("Success", f"File type updated to {new_type.value}")
            else:
                messagebox.showerror(
                    "Error", 
                    f"Failed to update file type.\n\n"
                    f"File: {filename}\n"
                    f"Path: {file_path}\n\n"
                    f"The file may have been moved or deleted.\n"
                    f"Try reloading the patient folder."
                )
    
    def _remove_missing_file_from_patient(self, file_path: str) -> tuple[bool, str]:
        """Remove a missing file from the current patient's data.
        
        Returns:
            tuple[bool, str]: (success, message) where message explains the result
        """
        if not self.current_patient:
            return False, "No patient is currently selected"
        
        patient = self.current_patient
        
        # Find and remove the file from all lists
        removed = False
        location = None
        
        # Check unmatched files
        for f in patient.unmatched_files[:]:  # Use slice to avoid modification during iteration
            if f.path == file_path:
                patient.unmatched_files.remove(f)
                removed = True
                location = "Unmatched files"
                break
        
        # Check CBCT files
        if not removed:
            for f in patient.cbct_files[:]:
                if f.path == file_path:
                    patient.cbct_files.remove(f)
                    removed = True
                    location = "CBCT files"
                    break
        
        # Check IOS upper
        if not removed and patient.ios_upper and patient.ios_upper.path == file_path:
            patient.ios_upper = None
            removed = True
            location = "IOS Upper scan"
        
        # Check IOS lower
        if not removed and patient.ios_lower and patient.ios_lower.path == file_path:
            patient.ios_lower = None
            removed = True
            location = "IOS Lower scan"
        
        # Check intraoral photos
        if not removed:
            for f in patient.intraoral_photos[:]:
                if f.path == file_path:
                    patient.intraoral_photos.remove(f)
                    removed = True
                    location = "Intraoral photos"
                    break
        
        # Check teleradiography
        if not removed and patient.teleradiography and patient.teleradiography.path == file_path:
            patient.teleradiography = None
            removed = True
            location = "Teleradiography"
        
        # Check orthopantomography
        if not removed and patient.orthopantomography and patient.orthopantomography.path == file_path:
            patient.orthopantomography = None
            removed = True
            location = "Orthopantomography (Panoramic)"
        
        if removed:
            return True, f"File removed from {location}"
        else:
            return False, f"File not found in patient data.\n\nPath: {file_path}\n\nThe file may have already been removed or was never part of this patient's records."
                
    def open_file(self):
        """Open the selected file with default application."""
        selection = self.files_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        file_path = self.files_tree.item(item, "values")[1]
        
        try:
            os.startfile(file_path)  # Windows
        except AttributeError:
            try:
                os.system(f'open "{file_path}"')  # macOS
            except:
                os.system(f'xdg-open "{file_path}"')  # Linux
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")
            
    def show_in_explorer(self):
        """Show the selected file in Windows Explorer."""
        selection = self.files_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        file_path = self.files_tree.item(item, "values")[1]
        
        try:
            os.system(f'explorer /select,"{file_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"Could not show file in explorer: {str(e)}")
    
    def open_bulk_mapping(self):
        """Open the bulk mapping dialog."""
        if not hasattr(self, 'current_patient') or not self.current_patient:
            messagebox.showwarning("No Patient Selected", "Please select a patient first.")
            return
            
        if not self.current_patient.unmatched_files:
            messagebox.showinfo("No Unmatched Files", 
                              "This patient has no unmatched files to map.")
            return
            
        # Open bulk mapping dialog
        dialog = BulkMappingDialog(
            self.parent, 
            self.current_patient, 
            callback=self.on_bulk_mapping_complete
        )
        
    def run_smart_auto_map(self):
        """Run smart auto-mapping for the current patient."""
        if not hasattr(self, 'current_patient') or not self.current_patient:
            messagebox.showwarning("No Patient Selected", "Please select a patient first.")
            return
            
        if not self.current_patient.unmatched_files:
            messagebox.showinfo("No Unmatched Files", 
                              "This patient has no unmatched files to map.")
            return
            
        # Confirm action
        result = messagebox.askyesno(
            "Smart Auto-Mapping",
            f"Run smart auto-mapping on {len(self.current_patient.unmatched_files)} unmatched files?\n\n"
            f"This will automatically map files based on common patterns like:\n"
            f"• .dcm files → CBCT DICOM\n"
            f"• .stl files with 'upper' → IOS Upper\n"
            f"• .stl files with 'lower' → IOS Lower"
        )
        
        if not result:
            return
            
        # Run smart auto-mapping
        mappings_made = 0
        files_to_remove = []
        
        from core.models import MatchStatus  # Import here to avoid circular imports
        
        for file_data in self.current_patient.unmatched_files:
            filename_lower = file_data.filename.lower()
            suggested_type = None
            
            # CBCT DICOM detection
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
                file_data.data_type = suggested_type
                file_data.confidence = 0.8
                file_data.status = MatchStatus.MATCHED
                
                self._assign_file_to_patient(file_data, suggested_type)
                files_to_remove.append(file_data)
                mappings_made += 1
        
        # Remove mapped files
        for file_data in files_to_remove:
            self.current_patient.unmatched_files.remove(file_data)
        
        # Update cache with auto-mapping changes
        if mappings_made > 0:
            self._update_patient_cache()
            
        # Show results
        if mappings_made > 0:
            messagebox.showinfo(
                "Smart Auto-Mapping Complete",
                f"Successfully auto-mapped {mappings_made} files!\n\n"
                f"Remaining unmatched files: {len(self.current_patient.unmatched_files)}"
            )
            
            # Refresh display
            self.show_patient_details(self.current_patient)
            self.populate_patient_list()  # Update patient list status
        else:
            messagebox.showinfo(
                "Smart Auto-Mapping Complete",
                "No files could be auto-mapped based on common patterns.\n\n"
                "Try using the Bulk Mapping dialog for more mapping options."
            )
    
    def _assign_file_to_patient(self, file_data, data_type):
        """Assign a file to the appropriate patient data attribute."""
        if data_type == DataType.CBCT_DICOM:
            self.current_patient.cbct_files.append(file_data)
        elif data_type == DataType.IOS_UPPER:
            self.current_patient.ios_upper = file_data
        elif data_type == DataType.IOS_LOWER:
            self.current_patient.ios_lower = file_data
        elif data_type == DataType.TELERADIOGRAPHY:
            self.current_patient.teleradiography = file_data
        elif data_type == DataType.ORTHOPANTOMOGRAPHY:
            self.current_patient.orthopantomography = file_data
        elif data_type == DataType.INTRAORAL_PHOTO:
            self.current_patient.intraoral_photos.append(file_data)
        
        # Update cache with manual assignment
        self._update_patient_cache()
    
    def on_bulk_mapping_complete(self):
        """Called when bulk mapping dialog is completed."""
        # Update cache with bulk mapping changes
        self._update_patient_cache()
        
        # Refresh the patient display
        self.show_patient_details(self.current_patient)
        self.populate_patient_list()  # Update patient list status
        
        # Show completion message
        unmatched_count = len(self.current_patient.unmatched_files)
        missing_count = len(self.current_patient.get_missing_data_types())
        
        if unmatched_count == 0 and missing_count == 0:
            messagebox.showinfo(
                "Mapping Complete",
                f"🎉 Patient {self.current_patient.patient_id} is now complete!\n\n"
                f"✅ All files have been mapped\n"
                f"✅ All required data types are present"
            )
        else:
            status_parts = []
            if missing_count > 0:
                missing_types = self.current_patient.get_missing_data_types()
                missing_names = [dt.value.replace('_', ' ').title() for dt in missing_types]
                status_parts.append(f"❌ Still missing: {', '.join(missing_names)}")
            if unmatched_count > 0:
                status_parts.append(f"📄 {unmatched_count} files still unmatched")
                
            messagebox.showinfo(
                "Mapping Updated",
                f"Bulk mapping completed for {self.current_patient.patient_id}.\n\n" + 
                "\n".join(status_parts)
            )
    
    def get_widget(self):
        """Get the main widget frame."""
        return self.frame
    
    def toggle_manual_completion(self):
        """Toggle manual completion status for the current patient."""
        if not self.current_patient:
            messagebox.showwarning("Warning", "No patient selected!")
            return
        
        # Toggle the status
        self.current_patient.manually_complete = not getattr(self.current_patient, 'manually_complete', False)
        
        # Update the checkbox
        self.manual_complete_var.set(self.current_patient.manually_complete)
        
        # Update cache with new manual completion status
        self._update_patient_cache()
        
        # Refresh the patient list to show updated status
        self.update_patient_list()
        
        # Show confirmation message
        status = "complete" if self.current_patient.manually_complete else "incomplete"
        messagebox.showinfo("Success", f"Patient '{self.current_patient.patient_id}' marked as manually {status}.")
    
    def set_manual_completion(self, complete: bool):
        """Set manual completion status for the current patient."""
        if not self.current_patient:
            return
        
        self.current_patient.manually_complete = complete
        
        # Update cache with new manual completion status
        self._update_patient_cache()
        
        self.update_patient_list()
    
    def update_manual_completion_controls(self):
        """Update the manual completion controls based on current patient."""
        if self.current_patient and hasattr(self, 'manual_complete_var'):
            manually_complete = getattr(self.current_patient, 'manually_complete', False)
            self.manual_complete_var.set(manually_complete)
            
            # Enable/disable controls based on selection
            if hasattr(self, 'manual_complete_cb'):
                self.manual_complete_cb.configure(state='normal')
        elif hasattr(self, 'manual_complete_cb'):
            self.manual_complete_cb.configure(state='disabled')
    
    def _update_patient_cache(self):
        """Update cache with current patient data after manual changes."""
        if self.current_patient and hasattr(self.project_manager, 'file_analyzer'):
            self.project_manager.file_analyzer.update_cache(self.current_patient)
    
    def clear_patient_cache(self):
        """Clear cache for current patient."""
        if self.current_patient and hasattr(self.project_manager, 'file_analyzer'):
            self.project_manager.file_analyzer.invalidate_cache(self.current_patient.folder_path)
            messagebox.showinfo("Cache Cleared", f"Cache cleared for {self.current_patient.patient_id}")
    
    def view_cache_stats(self):
        """Show cache statistics."""
        if hasattr(self.project_manager, 'file_analyzer'):
            stats = self.project_manager.file_analyzer.get_cache_stats()
            
            message = f"""Cache Statistics:
            
Total Cached Patients: {stats['total_entries']}
Total Matched Files: {stats['total_matched_files']}
Total Unmatched Files: {stats['total_unmatched_files']}
Cache Size: {stats['cache_size_bytes'] / 1024:.1f} KB

Cache File: {stats['cache_file']}
Oldest Entry: {stats['oldest_entry'] or 'None'}
Newest Entry: {stats['newest_entry'] or 'None'}"""
            
            messagebox.showinfo("Cache Statistics", message)
        else:
            messagebox.showwarning("Cache Unavailable", "Cache system is not available")
    
    def clear_all_cache(self):
        """Clear all cache entries."""
        if hasattr(self.project_manager, 'file_analyzer'):
            result = messagebox.askyesno(
                "Clear All Cache", 
                "Are you sure you want to clear all cached patient data?\n\n"
                "This will remove all saved file assignments and you'll need to "
                "re-map files when reloading patients."
            )
            if result:
                self.project_manager.file_analyzer.clear_all_cache()
                messagebox.showinfo("Cache Cleared", "All cache entries have been cleared")
        else:
            messagebox.showwarning("Cache Unavailable", "Cache system is not available")


class ReassignTypeDialog:
    """Dialog for reassigning file types."""
    
    def __init__(self, parent, filename):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Reassign Type - {filename}")
        self.dialog.geometry("400x380")  # Height for data type options
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets(filename)
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
        
    def create_widgets(self, filename):
        """Create dialog widgets."""
        # Header
        header_label = ttk.Label(self.dialog, text=f"Select new type for: {filename}", 
                                font=("Arial", 10, "bold"))
        header_label.pack(pady=10)
        
        # Type selection
        self.type_var = tk.StringVar()
        
        type_frame = ttk.LabelFrame(self.dialog, text="Data Type")
        type_frame.pack(fill=tk.X, padx=20, pady=10)
        
        types = [
            (DataType.CBCT_DICOM, "CBCT DICOM Files"),
            (DataType.IOS_UPPER, "IOS Upper Scan"),
            (DataType.IOS_LOWER, "IOS Lower Scan"),
            (DataType.INTRAORAL_PHOTO, "Intraoral Photo"),
            (DataType.TELERADIOGRAPHY, "Teleradiography"),
            (DataType.ORTHOPANTOMOGRAPHY, "Orthopantomography"),
            (DataType.EXCLUDE, "Exclude from Upload")
        ]
        
        for data_type, description in types:
            rb = ttk.Radiobutton(
                type_frame,
                text=description,
                variable=self.type_var,
                value=data_type.value
            )
            rb.pack(anchor=tk.W, padx=10, pady=2)
        
        # Add info label for exclude option
        info_label = ttk.Label(self.dialog, 
                              text="Note: Excluded files will not be uploaded to TF4M",
                              foreground="gray")
        info_label.pack(pady=(0, 10))
            
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT)
        
    def ok(self):
        """Handle OK button."""
        selected_type = self.type_var.get()
        if selected_type:
            self.result = DataType(selected_type)
        self.dialog.destroy()
        
    def cancel(self):
        """Handle Cancel button."""
        self.dialog.destroy()
