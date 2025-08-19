#!/usr/bin/env python3
"""
Simple test for configuration window after fixing indentation
"""

import tkinter as tk
from tkinter import messagebox
from macro_interface import MacroInterface, SelectionMode

def test_config():
    """Test the configuration window"""
    print("Testing configuration window...")
    
    # Create main window
    root = tk.Tk()
    root.title("Test Config Window")
    root.geometry("300x200")
    
    # Create macro interface
    macro = MacroInterface()
    
    def open_config():
        print("Opening configuration...")
        try:
            macro.start_position_selection(SelectionMode.NONE, lambda: print("Config completed"))
            print("Configuration window should be open now!")
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"Failed to open config: {e}")
    
    # Add button
    btn = tk.Button(root, text="Open Configuration", command=open_config, 
                   bg="green", fg="white", font=("Arial", 12))
    btn.pack(pady=50)
    
    print("Test window ready. Click the button to test configuration.")
    root.mainloop()

if __name__ == "__main__":
    test_config() 