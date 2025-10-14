#!/usr/bin/env python3
"""
Simple test to check if tkinter is working.
"""

try:
    import tkinter as tk
    print("Tkinter import successful")
    
    # Try to create a simple window
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("300x200")
    
    label = tk.Label(root, text="Tkinter is working!")
    label.pack(pady=50)
    
    button = tk.Button(root, text="Close", command=root.quit)
    button.pack()
    
    print("Tkinter window created successfully")
    root.mainloop()
    
except Exception as e:
    print(f"Tkinter error: {e}")
    print("You may need to install tkinter or fix your Python installation")
    input("Press Enter to continue...")
