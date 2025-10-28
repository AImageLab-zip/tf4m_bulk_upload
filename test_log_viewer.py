"""
Test the log viewer to ensure it initializes correctly.
"""

import tkinter as tk
from gui.log_viewer import LogViewerWindow
import sys

def test_log_viewer():
    """Test that log viewer opens without errors."""
    print("Creating root window...")
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    try:
        print("Opening log viewer...")
        viewer = LogViewerWindow(root)
        print("✅ Log viewer opened successfully!")
        print("Waiting 2 seconds before closing...")
        root.after(2000, lambda: viewer.on_closing())
        root.after(2100, root.quit)
        root.mainloop()
        print("✅ Log viewer closed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error opening log viewer: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_log_viewer()
    sys.exit(0 if success else 1)
