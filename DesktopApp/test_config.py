#!/usr/bin/env python3
"""
Test script for configuration window
"""

import tkinter as tk
from tkinter import messagebox
from macro_interface import MacroInterface, SelectionMode

def test_config_window():
    """Test the configuration window"""
    print("Testing configuration window...")
    
    # Create main window
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("300x200")
    
    # Create macro interface
    macro = MacroInterface()
    
    def open_config():
        print("Button clicked - opening config...")
        try:
            macro.start_position_selection(SelectionMode.NONE, lambda: print("Config completed"))
            print("Config window should be open now")
        except Exception as e:
            print(f"Error opening config: {e}")
            messagebox.showerror("Error", f"Failed to open config: {e}")
    
    # Add test button
    btn = tk.Button(root, text="Test Configure Positions", command=open_config, 
                   bg="blue", fg="white", font=("Arial", 12))
    btn.pack(pady=50)
    
    # Add status label
    status = tk.Label(root, text="Click the button to test configuration window")
    status.pack(pady=20)
    
    print("Test window created. Click the button to test configuration.")
    root.mainloop()

if __name__ == "__main__":
    test_config_window() 