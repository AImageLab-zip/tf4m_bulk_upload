"""
Log viewer window for viewing application logs.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import logging
from datetime import datetime

class LogViewerWindow:
    """Window for viewing application logs."""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Console Log Viewer")
        self.window.geometry("900x600")
        
        # Initialize auto-refresh variables first (before setup_ui)
        self.auto_refresh = tk.BooleanVar(value=False)
        self.refresh_id = None
        
        # Get log file path
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        self.log_file = os.path.join(self.log_dir, "tf4m_app.log")
        
        # Setup UI and bind close event
        self.setup_ui()
        self.load_log_file()
        
        # Handle window close event to clean up auto-refresh
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Setup the user interface."""
        # Toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Refresh", command=self.load_log_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Clear", command=self.clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save As...", command=self.save_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Open Log Folder", command=self.open_log_folder).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Auto-refresh checkbox
        ttk.Checkbutton(
            toolbar, 
            text="Auto-refresh (2s)", 
            variable=self.auto_refresh,
            command=self.toggle_auto_refresh
        ).pack(side=tk.LEFT, padx=2)
        
        # Filter frame
        filter_frame = ttk.LabelFrame(self.window, text="Filter")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Level:").pack(side=tk.LEFT, padx=5)
        
        self.filter_var = tk.StringVar(value="ALL")
        levels = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, values=levels, width=10, state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.load_log_file())
        
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", lambda e: self.load_log_file())
        
        ttk.Button(filter_frame, text="Search", command=self.load_log_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Clear Filter", command=self.clear_filter).pack(side=tk.LEFT, padx=2)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(self.window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text widget with scrollbars
        self.text_widget = tk.Text(
            text_frame, 
            wrap=tk.NONE, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        
        self.text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        # Configure text tags for different log levels
        self.text_widget.tag_config("DEBUG", foreground="#808080")
        self.text_widget.tag_config("INFO", foreground="#4ec9b0")
        self.text_widget.tag_config("WARNING", foreground="#dcdcaa")
        self.text_widget.tag_config("ERROR", foreground="#f48771")
        self.text_widget.tag_config("CRITICAL", foreground="#ff0000", background="#4d0000")
        self.text_widget.tag_config("SEARCH", background="#264f78")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def load_log_file(self):
        """Load and display the log file."""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        
        if not os.path.exists(self.log_file):
            self.text_widget.insert(tk.END, f"Log file not found: {self.log_file}\n")
            self.text_widget.config(state=tk.DISABLED)
            self.status_var.set("Log file not found")
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            filter_level = self.filter_var.get()
            search_text = self.search_var.get().lower()
            
            displayed_lines = 0
            for line in lines:
                # Apply level filter
                if filter_level != "ALL":
                    if f" - {filter_level} - " not in line:
                        continue
                
                # Apply search filter
                if search_text and search_text not in line.lower():
                    continue
                
                # Insert line with appropriate tag
                start_pos = self.text_widget.index(tk.INSERT)
                self.text_widget.insert(tk.END, line)
                
                # Color code by log level
                for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    if f" - {level} - " in line:
                        end_pos = self.text_widget.index(tk.INSERT)
                        self.text_widget.tag_add(level, start_pos, end_pos)
                        break
                
                # Highlight search text
                if search_text:
                    self.highlight_search_text(start_pos, line, search_text)
                
                displayed_lines += 1
            
            # Scroll to end
            self.text_widget.see(tk.END)
            
            total_lines = len(lines)
            file_size = os.path.getsize(self.log_file)
            self.status_var.set(f"Loaded {displayed_lines} of {total_lines} lines | File size: {file_size:,} bytes")
            
        except Exception as e:
            self.text_widget.insert(tk.END, f"Error loading log file: {e}\n")
            self.status_var.set(f"Error: {e}")
        
        self.text_widget.config(state=tk.DISABLED)
    
    def highlight_search_text(self, line_start, line, search_text):
        """Highlight search text in the line."""
        line_lower = line.lower()
        start = 0
        while True:
            pos = line_lower.find(search_text, start)
            if pos == -1:
                break
            
            # Calculate text widget positions
            search_start = f"{line_start}+{pos}c"
            search_end = f"{line_start}+{pos + len(search_text)}c"
            self.text_widget.tag_add("SEARCH", search_start, search_end)
            start = pos + len(search_text)
    
    def clear_filter(self):
        """Clear all filters."""
        self.filter_var.set("ALL")
        self.search_var.set("")
        self.load_log_file()
    
    def clear_log(self):
        """Clear the log file."""
        if messagebox.askyesno("Clear Log", "Are you sure you want to clear the log file?"):
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Log cleared\n")
                self.load_log_file()
                logging.info("Log file cleared by user")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear log: {e}")
    
    def save_log(self):
        """Save log to a different file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import shutil
                shutil.copy2(self.log_file, filename)
                messagebox.showinfo("Success", f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def open_log_folder(self):
        """Open the log folder in file explorer."""
        try:
            if os.path.exists(self.log_dir):
                os.startfile(self.log_dir)
            else:
                messagebox.showerror("Error", f"Log directory not found: {self.log_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log folder: {e}")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh of log file."""
        if self.auto_refresh.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def start_auto_refresh(self):
        """Start auto-refresh timer."""
        self.load_log_file()
        self.refresh_id = self.window.after(2000, self.start_auto_refresh)
    
    def stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self.refresh_id:
            self.window.after_cancel(self.refresh_id)
            self.refresh_id = None
    
    def on_closing(self):
        """Handle window close event - clean up auto-refresh timer."""
        self.stop_auto_refresh()
        self.window.destroy()
