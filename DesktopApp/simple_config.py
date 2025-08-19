#!/usr/bin/env python3
"""
Simple configuration window test
"""

import tkinter as tk
from tkinter import messagebox

def create_simple_config_window():
    """Create a simple configuration window"""
    print("Creating simple config window...")
    
    # Create the window
    config_window = tk.Toplevel()
    config_window.title("Simple Position Configuration")
    config_window.geometry("400x300")
    config_window.resizable(False, False)
    
    # Center the window
    config_window.update_idletasks()
    x = (config_window.winfo_screenwidth() // 2) - (400 // 2)
    y = (config_window.winfo_screenheight() // 2) - (300 // 2)
    config_window.geometry(f"400x300+{x}+{y}")
    
    # Make window stay on top
    config_window.attributes('-topmost', True)
    config_window.deiconify()
    config_window.lift()
    config_window.focus_force()
    
    # Add content
    title = tk.Label(config_window, text="Position Configuration", font=("Arial", 16, "bold"))
    title.pack(pady=20)
    
    status = tk.Label(config_window, text="Configuration window is working!", fg="green")
    status.pack(pady=10)
    
    # Add some buttons
    player_btn = tk.Button(config_window, text="Set Player Area", 
                          command=lambda: messagebox.showinfo("Info", "Player area button clicked"))
    player_btn.pack(pady=5)
    
    banker_btn = tk.Button(config_window, text="Set Banker Area", 
                          command=lambda: messagebox.showinfo("Info", "Banker area button clicked"))
    banker_btn.pack(pady=5)
    
    cancel_btn = tk.Button(config_window, text="Set Cancel Button", 
                          command=lambda: messagebox.showinfo("Info", "Cancel button clicked"))
    cancel_btn.pack(pady=5)
    
    close_btn = tk.Button(config_window, text="Close", 
                         command=config_window.destroy, bg="red", fg="white")
    close_btn.pack(pady=20)
    
    print("Simple config window created successfully!")
    return config_window

def main():
    """Main function"""
    # Create main window
    root = tk.Tk()
    root.title("Test Simple Config")
    root.geometry("300x200")
    
    def open_simple_config():
        print("Opening simple config...")
        try:
            create_simple_config_window()
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"Failed to create window: {e}")
    
    # Add button
    btn = tk.Button(root, text="Open Simple Config", command=open_simple_config,
                   bg="green", fg="white", font=("Arial", 12))
    btn.pack(pady=50)
    
    print("Test window ready. Click the button to test simple config.")
    root.mainloop()

if __name__ == "__main__":
    main() 