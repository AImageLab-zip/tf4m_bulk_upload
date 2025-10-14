"""
Settings dialog for configuring TF4M API connection and other preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

from core.api_client import TF4MAPIClient, APIClient

class SettingsDialog:
    """Dialog for application settings."""
    
    def __init__(self, parent, api_client):
        self.parent = parent
        self.api_client = api_client
        self.settings_file = "settings.json"
        
        # Load existing settings
        self.settings = self.load_settings()
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("TF4M Settings")
        self.dialog.geometry("500x700")  # Increased height to show all controls
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
        
        self.create_widgets()
        self.load_current_values()
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
        
    def center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        """Create dialog widgets."""
        # Create notebook for different setting categories
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # TF4M API Settings tab
        self.create_tf4m_api_tab(notebook)
        
        # Upload Settings tab
        self.create_upload_tab(notebook)
        
        # Analysis Settings tab
        self.create_analysis_tab(notebook)
        
        # Buttons frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Apply", command=self.apply).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT)
        
    def create_tf4m_api_tab(self, notebook):
        """Create the TF4M API settings tab."""
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text="TF4M API Connection")
        
        # API URL
        ttk.Label(api_frame, text="TF4M Server URL:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.api_url_var = tk.StringVar()
        url_entry = ttk.Entry(api_frame, textvariable=self.api_url_var, width=50)
        url_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        # Add default URL suggestion
        url_help = ttk.Label(api_frame, text="Default: http://pdor.ing.unimore.it:8080", 
                           foreground="gray", font=("TkDefaultFont", 8))
        url_help.grid(row=1, column=1, sticky="w", padx=10)
        
        # Username
        ttk.Label(api_frame, text="Username:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(api_frame, textvariable=self.username_var, width=50)
        username_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=10)
        
        # Password
        ttk.Label(api_frame, text="Password:").grid(row=3, column=0, sticky="w", padx=10, pady=10)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(api_frame, textvariable=self.password_var, width=50, show="*")
        password_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=10)
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar()
        show_password_cb = ttk.Checkbutton(
            api_frame, 
            text="Show Password", 
            variable=self.show_password_var,
            command=lambda: password_entry.config(show="" if self.show_password_var.get() else "*")
        )
        show_password_cb.grid(row=4, column=1, sticky="w", padx=10)
        
        # Authentication info
        auth_info_frame = ttk.LabelFrame(api_frame, text="Authentication Info")
        auth_info_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        
        auth_info_text = tk.Text(auth_info_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        auth_info_text.pack(fill=tk.X, padx=10, pady=10)
        
        info_text = (
            "TF4M uses session-based authentication with Django. You need valid credentials "
            "with upload permissions (annotator, admin, or student_dev roles). "
            "Contact your system administrator if you need access."
        )
        
        auth_info_text.config(state=tk.NORMAL)
        auth_info_text.insert(tk.END, info_text)
        auth_info_text.config(state=tk.DISABLED)
        
        # Connection status
        self.connection_status_var = tk.StringVar(value="Not tested")
        status_frame = ttk.Frame(api_frame)
        status_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ttk.Label(status_frame, text="Connection Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.connection_status_var)
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Configure grid weights
        api_frame.grid_columnconfigure(1, weight=1)
    
    def create_upload_tab(self, notebook):
        """Create the upload settings tab."""
        upload_frame = ttk.Frame(notebook)
        notebook.add(upload_frame, text="Upload")
        
        # Upload behavior settings
        behavior_frame = ttk.LabelFrame(upload_frame, text="Upload Behavior")
        behavior_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Delete and reupload option
        self.delete_before_reupload_var = tk.BooleanVar()
        delete_cb = ttk.Checkbutton(
            behavior_frame,
            text="Delete existing patient before reupload",
            variable=self.delete_before_reupload_var
        )
        delete_cb.pack(anchor=tk.W, padx=10, pady=10)
        
        # Help text for delete option
        help_text = tk.Text(behavior_frame, height=6, wrap=tk.WORD, state=tk.DISABLED, 
                           relief=tk.FLAT, borderwidth=0)
        help_text.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        help_content = (
            "When enabled (recommended):\n"
            "• If a patient already exists on the server, it will be deleted and recreated\n"
            "• All files will be uploaded fresh to ensure data consistency\n"
            "• This is the safest option since the API doesn't support partial updates\n\n"
            "When disabled:\n"
            "• Existing patients will be skipped if they already have files\n"
            "• May result in incomplete or outdated data on the server"
        )
        
        help_text.config(state=tk.NORMAL)
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
        
    def create_analysis_tab(self, notebook):
        """Create the analysis settings tab."""
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="Analysis")
        
        # File analysis settings
        file_frame = ttk.LabelFrame(analysis_frame, text="File Analysis")
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Confidence threshold
        ttk.Label(file_frame, text="Minimum Confidence Threshold:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.confidence_var = tk.DoubleVar()
        confidence_scale = ttk.Scale(
            file_frame, 
            from_=0.0, 
            to=1.0, 
            variable=self.confidence_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        confidence_scale.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        self.confidence_label_var = tk.StringVar()
        ttk.Label(file_frame, textvariable=self.confidence_label_var).grid(row=0, column=2, padx=10, pady=10)
        
        # Update label when scale changes
        confidence_scale.config(command=lambda v: self.confidence_label_var.set(f"{float(v):.1%}"))
        
        # Include subfolders
        self.include_subfolders_var = tk.BooleanVar()
        ttk.Checkbutton(
            file_frame,
            text="Include files in subfolders",
            variable=self.include_subfolders_var
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=5)
        
        # Case sensitive matching
        self.case_sensitive_var = tk.BooleanVar()
        ttk.Checkbutton(
            file_frame,
            text="Case sensitive filename matching",
            variable=self.case_sensitive_var
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=5)
        
        # Folder patterns
        patterns_frame = ttk.LabelFrame(analysis_frame, text="Folder Name Patterns")
        patterns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # CBCT patterns
        ttk.Label(patterns_frame, text="CBCT Folder Patterns:").grid(row=0, column=0, sticky="nw", padx=10, pady=10)
        self.cbct_patterns_var = tk.StringVar()
        cbct_text = tk.Text(patterns_frame, height=3, width=40)
        cbct_text.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        # IOS patterns
        ttk.Label(patterns_frame, text="IOS Folder Patterns:").grid(row=1, column=0, sticky="nw", padx=10, pady=10)
        self.ios_patterns_var = tk.StringVar()
        ios_text = tk.Text(patterns_frame, height=3, width=40)
        ios_text.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        
        # Store text widgets for later use
        self.cbct_patterns_text = cbct_text
        self.ios_patterns_text = ios_text
        
        # Configure column weights
        file_frame.grid_columnconfigure(1, weight=1)
        patterns_frame.grid_columnconfigure(1, weight=1)
        
    def load_current_values(self):
        """Load current values into the form."""
        # TF4M API settings
        self.api_url_var.set(self.settings.get("api_url", "http://pdor.ing.unimore.it:8080"))
        self.username_var.set(self.settings.get("username", ""))
        self.password_var.set(self.settings.get("password", ""))
        
        # Upload settings
        self.delete_before_reupload_var.set(self.settings.get("delete_before_reupload", True))
        
        # Analysis settings
        self.confidence_var.set(self.settings.get("confidence_threshold", 0.5))
        self.confidence_label_var.set(f"{self.confidence_var.get():.1%}")
        self.include_subfolders_var.set(self.settings.get("include_subfolders", True))
        self.case_sensitive_var.set(self.settings.get("case_sensitive", False))
        
        # Patterns
        cbct_patterns = self.settings.get("cbct_patterns", ["cbct", "cone.*beam", "3d", "dicom", "ct"])
        ios_patterns = self.settings.get("ios_patterns", ["scansioni", "scan", "ios", "intraoral.*scan", "stl"])
        
        self.cbct_patterns_text.insert(1.0, "\n".join(cbct_patterns))
        self.ios_patterns_text.insert(1.0, "\n".join(ios_patterns))
        
    def test_connection(self):
        """Test the TF4M API connection with current settings."""
        # Temporarily update API client with current settings
        old_url = self.api_client.base_url
        old_username = getattr(self.api_client, 'username', None)
        old_password = getattr(self.api_client, 'password', None)
        
        try:
            self.api_client.set_base_url(self.api_url_var.get())
            self.api_client.set_credentials(self.username_var.get(), self.password_var.get())
            
            success, message = self.api_client.test_connection()
            
            if success:
                self.connection_status_var.set("✓ Connected")
                self.status_label.config(foreground="green")
                messagebox.showinfo("Connection Test", "Connection to TF4M successful!")
            else:
                self.connection_status_var.set("✗ Failed")
                self.status_label.config(foreground="red")
                messagebox.showerror("Connection Test", f"Connection failed: {message}")
                
        finally:
            # Restore original settings
            self.api_client.set_base_url(old_url)
            if old_username and old_password:
                self.api_client.set_credentials(old_username, old_password)
            
    def apply(self):
        """Apply the current settings."""
        # Validate settings
        if not self.api_url_var.get():
            messagebox.showerror("Error", "TF4M Server URL is required")
            return
            
        if not self.username_var.get():
            messagebox.showerror("Error", "Username is required")
            return
            
        if not self.password_var.get():
            messagebox.showerror("Error", "Password is required")
            return
            
        # Update settings
        self.settings.update({
            "api_url": self.api_url_var.get(),
            "username": self.username_var.get(),
            "password": self.password_var.get(),  # Note: storing password in plain text for now
            "delete_before_reupload": self.delete_before_reupload_var.get(),
            "confidence_threshold": self.confidence_var.get(),
            "include_subfolders": self.include_subfolders_var.get(),
            "case_sensitive": self.case_sensitive_var.get(),
            "cbct_patterns": [p.strip() for p in self.cbct_patterns_text.get(1.0, tk.END).strip().split("\n") if p.strip()],
            "ios_patterns": [p.strip() for p in self.ios_patterns_text.get(1.0, tk.END).strip().split("\n") if p.strip()]
        })
        
        # Save settings
        self.save_settings()
        
        # Update API client
        self.api_client.set_base_url(self.settings["api_url"])
        self.api_client.set_credentials(self.settings["username"], self.settings["password"])
        
        messagebox.showinfo("Settings", "TF4M settings applied successfully")
        
    def ok(self):
        """Apply settings and close dialog."""
        self.apply()
        self.dialog.destroy()
        
    def cancel(self):
        """Close dialog without applying."""
        self.dialog.destroy()
        
    def load_settings(self):
        """Load settings from file."""
        default_settings = {
            "api_url": "http://pdor.ing.unimore.it:8080",
            "username": "",
            "password": "",
            "delete_before_reupload": True,  # Default to enabled for safety
            "confidence_threshold": 0.5,
            "include_subfolders": True,
            "case_sensitive": False,
            "cbct_patterns": ["cbct", "cone.*beam", "3d", "dicom", "ct"],
            "ios_patterns": ["scansioni", "scan", "ios", "intraoral.*scan", "stl"]
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
        except Exception:
            pass  # Use default settings if loading fails
            
        return default_settings
        
    def save_settings(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
