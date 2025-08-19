#!/usr/bin/env python3
"""
Debug script for configuration button
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from macro_interface import MacroInterface, SelectionMode
    print("✓ MacroInterface imported successfully")
except Exception as e:
    print(f"✗ Error importing MacroInterface: {e}")
    sys.exit(1)

def debug_config_button():
    """Debug the configuration button functionality"""
    print("🔍 Debugging Configuration Button")
    print("=" * 40)
    
    # Create main window
    root = tk.Tk()
    root.title("Debug Config Button")
    root.geometry("400x300")
    
    # Create macro interface
    print("Creating MacroInterface...")
    macro = MacroInterface()
    print("✓ MacroInterface created")
    
    def test_button_click():
        """Test button click handler"""
        print("🔘 Button clicked!")
        messagebox.showinfo("Debug", "Button click registered!")
        
        print("Opening configuration...")
        try:
            macro.start_position_selection(SelectionMode.NONE, lambda: print("Config completed"))
            print("✓ Configuration window should be open")
        except Exception as e:
            print(f"✗ Error opening configuration: {e}")
            messagebox.showerror("Error", f"Failed to open config: {e}")
    
    # Add test button
    btn = tk.Button(root, text="Test Configure Positions", 
                   command=test_button_click,
                   bg="blue", fg="white", font=("Arial", 12))
    btn.pack(pady=50)
    
    # Add status
    status = tk.Label(root, text="Click the button to test configuration")
    status.pack(pady=20)
    
    print("✓ Debug window created")
    print("Click the button to test configuration window")
    
    root.mainloop()

if __name__ == "__main__":
    debug_config_button() 