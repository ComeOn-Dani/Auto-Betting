import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Tuple, Callable
import threading
import time
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class Position:
    x: int
    y: int
    width: int
    height: int
    name: str

@dataclass
class ChipConfig:
    amount: int
    position: Position

class SelectionMode(Enum):
    NONE = "none"
    PLAYER_AREA = "player_area"
    BANKER_AREA = "banker_area"
    CANCEL_BUTTON = "cancel_button"
    CHIP = "chip"

class MacroInterface:
    def __init__(self, config_path: str = "macro_config.json"):
        self.config_path = config_path
        self.positions: Dict[str, Position] = {}
        self.chips: List[ChipConfig] = []
        self.selection_mode = SelectionMode.NONE
        self.on_position_selected: Optional[Callable] = None
        self.selection_window: Optional[tk.Toplevel] = None
        self.overlay_window: Optional[tk.Toplevel] = None
        self.load_config()
        
    def load_config(self):
        """Load saved positions and chip configurations"""
        # Define predefined chip amounts
        self.predefined_chips = [1000, 25000, 125000, 500000, 1250000, 2500000, 5000000, 50000000]
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    
                # Load positions
                for name, pos_data in data.get('positions', {}).items():
                    self.positions[name] = Position(**pos_data)
                    print(f"Loaded position: {name} at ({pos_data['x']}, {pos_data['y']})")
                    
                # Load chips
                self.chips = []
                for chip_data in data.get('chips', []):
                    position = Position(**chip_data['position'])
                    self.chips.append(ChipConfig(
                        amount=chip_data['amount'],
                        position=position
                    ))
                    print(f"Loaded chip: {chip_data['amount']} at ({position.x}, {position.y})")
                
                print(f"Configuration loaded successfully from {self.config_path}")
                print(f"Loaded {len(self.positions)} positions and {len(self.chips)} chips")
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            print(f"Config file not found: {self.config_path}")
        
        # Ensure all predefined chips exist in the config (with default positions if not set)
        self._ensure_predefined_chips_exist()
    
    def _ensure_predefined_chips_exist(self):
        """Ensure all initial chips exist in the config with default positions if not set"""
        print("Ensuring initial chips exist in config...")
        
        # Initial chip amounts
        initial_chips = [1000, 25000, 125000, 500000, 1250000, 2500000, 5000000, 50000000]
        
        for amount in initial_chips:
            # Check if chip already exists
            existing_chip = next((chip for chip in self.chips if chip.amount == amount), None)
            
            if not existing_chip:
                # Create chip with default position (not set)
                default_position = Position(x=0, y=0, width=50, height=50, name=f"chip_{amount}")
                new_chip = ChipConfig(amount=amount, position=default_position)
                self.chips.append(new_chip)
                print(f"Added initial chip {amount} with default position")
        
        # Save the updated config immediately
        self.save_config()
        print("Initial chips ensured and config saved")
    
    def save_config(self):
        """Save current positions and chip configurations"""
        data = {
            'positions': {name: asdict(pos) for name, pos in self.positions.items()},
            'chips': [{'amount': chip.amount, 'position': asdict(chip.position)} for chip in self.chips]
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Configuration saved successfully to {self.config_path}")
            print(f"Saved {len(self.positions)} positions and {len(self.chips)} chips")
            for name, pos in self.positions.items():
                print(f"  - {name}: ({pos.x}, {pos.y})")
            for chip in self.chips:
                print(f"  - Chip {chip.amount}: ({chip.position.x}, {chip.position.y})")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def start_position_selection(self, mode: SelectionMode = SelectionMode.NONE, callback: Optional[Callable] = None):
        """Start position selection mode"""
        # Reload data from config file every time window opens
        self.load_config()
        
        self.selection_mode = mode
        self.on_position_selected = callback
        self._create_selection_window()
        self._create_overlay_window()
    
    def _create_selection_window(self):
        """Create the main selection interface window"""
        print("Creating selection window...")  # Debug
        
        # Create the window
        self.selection_window = tk.Toplevel()
        self.selection_window.title("Configure Macro Positions")
        self.selection_window.resizable(True, True)  # Allow resizing
        
        # Make window stay on top and visible
        self.selection_window.attributes('-topmost', True)
        self.selection_window.deiconify()
        self.selection_window.lift()
        self.selection_window.focus_force()
        
        # Add window close event handling
        self.selection_window.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Build the UI first
        print("Building selection UI...")  # Debug
        self._build_selection_ui()
        
        # Now size the window to fit content
        self.selection_window.update_idletasks()
        width = self.selection_window.winfo_reqwidth()
        height = self.selection_window.winfo_reqheight()
        
        # Add some padding
        width += 20
        height += 20
        
        # Ensure minimum height for better usability
        min_height = 800
        if height < min_height:
            height = min_height
        
        # Center the window
        x = (self.selection_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.selection_window.winfo_screenheight() // 2) - (height // 2)
        self.selection_window.geometry(f"{width}x{height}+{x}+{y}")
        
        print("Selection window created successfully")  # Debug
    
    def _build_selection_ui(self):
        """Build the selection interface UI"""
        print("Building selection UI...")  # Debug
        
        # Main container
        main_frame = tk.Frame(self.selection_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Configure Macro Positions", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Action buttons below title
        title_actions_frame = tk.Frame(main_frame)
        title_actions_frame.pack(fill="x", pady=(0, 10))
        
        # Show All Positions button (visual indicators)
        show_positions_btn = tk.Button(title_actions_frame, text="Show All Positions", 
                                      command=self._show_all_positions_visual, bg="#9C27B0", fg="white")
        show_positions_btn.pack(side="left", padx=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Betting Areas Section
        areas_frame = tk.LabelFrame(scrollable_frame, text="Betting Areas (Required)", font=("Arial", 10, "bold"))
        areas_frame.pack(fill="x", padx=5, pady=5)
        
        # Player Area
        player_frame = tk.Frame(areas_frame)
        player_frame.pack(fill="x", pady=2)
        
        player_label = tk.Label(player_frame, text="Player Bet Area:")
        player_label.pack(side="left", padx=5)
        
        self.player_status_label = tk.Label(player_frame, text="Not set", fg="red")
        self.player_status_label.pack(side="left", padx=5)
        
        player_btn = tk.Button(player_frame, text="Select Position", 
                              command=lambda: self._start_area_selection(SelectionMode.PLAYER_AREA))
        player_btn.pack(side="right", padx=5)
        
        # Banker Area
        banker_frame = tk.Frame(areas_frame)
        banker_frame.pack(fill="x", pady=2)
        
        banker_label = tk.Label(banker_frame, text="Banker Bet Area:")
        banker_label.pack(side="left", padx=5)
        
        self.banker_status_label = tk.Label(banker_frame, text="Not set", fg="red")
        self.banker_status_label.pack(side="left", padx=5)
        
        banker_btn = tk.Button(banker_frame, text="Select Position", 
                              command=lambda: self._start_area_selection(SelectionMode.BANKER_AREA))
        banker_btn.pack(side="right", padx=5)
        
        # Cancel Button
        cancel_frame = tk.Frame(areas_frame)
        cancel_frame.pack(fill="x", pady=2)
        
        cancel_label = tk.Label(cancel_frame, text="Cancel Button:")
        cancel_label.pack(side="left", padx=5)
        
        self.cancel_status_label = tk.Label(cancel_frame, text="Not set", fg="red")
        self.cancel_status_label.pack(side="left", padx=5)
        
        cancel_btn = tk.Button(cancel_frame, text="Select Position", 
                              command=lambda: self._start_area_selection(SelectionMode.CANCEL_BUTTON))
        cancel_btn.pack(side="right", padx=5)
        
        # Chips Section
        chips_frame = tk.LabelFrame(scrollable_frame, text="Chips", font=("Arial", 10, "bold"))
        chips_frame.pack(fill="x", padx=5, pady=5)
        
        # Initialize chip tracking dictionaries
        self.chip_entries = {}
        self.chip_status_labels = {}
        
        # Create all chips (8 initial chips + any existing custom chips)
        all_chip_amounts = set()
        
        # Add predefined amounts if not already in config
        initial_chips = [1000, 25000, 125000, 500000, 1250000, 2500000, 5000000, 50000000]
        for amount in initial_chips:
            all_chip_amounts.add(amount)
        
        # Add any existing chips from config
        for chip in self.chips:
            all_chip_amounts.add(chip.amount)
        
        # Sort all chip amounts
        sorted_amounts = sorted(all_chip_amounts)
        
        # Create chip entries for all amounts
        for amount in sorted_amounts:
            chip_frame = tk.Frame(chips_frame)
            chip_frame.pack(fill="x", pady=2)
            
            # Editable amount entry
            amount_var = tk.StringVar(value=str(amount))
            amount_entry = tk.Entry(chip_frame, textvariable=amount_var, width=15)
            amount_entry.pack(side="left", padx=5)
            # Bind to save changes immediately when user finishes editing
            amount_entry.bind('<FocusOut>', lambda e, amt=amount, var=amount_var: self._on_chip_amount_changed(amt, var))
            amount_entry.bind('<Return>', lambda e, amt=amount, var=amount_var: self._on_chip_amount_changed(amt, var))
            self.chip_entries[amount] = amount_var
            
            # Position status label
            status_label = tk.Label(chip_frame, text="Not set", fg="red", width=15)
            status_label.pack(side="left", padx=5)
            self.chip_status_labels[amount] = status_label
            
            # Select position button
            select_btn = tk.Button(chip_frame, text="Select Position", 
                                 command=lambda a=amount: self._select_chip_position(a))
            select_btn.pack(side="right", padx=5)
            
            # Remove button
            remove_btn = tk.Button(chip_frame, text="Remove", 
                                 command=lambda a=amount: self._remove_chip_by_amount(a))
            remove_btn.pack(side="right", padx=5)
        
        # Separator
        ttk.Separator(chips_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Add custom chip button
        add_chip_btn = tk.Button(chips_frame, text="+ Add Custom Chip", 
                                command=self._add_custom_chip, bg="#4CAF50", fg="white")
        add_chip_btn.pack(pady=5)
        
        # Pack the scrollable content
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update status displays
        self._update_status_displays()
        
        # Add key bindings for closing window
        self.selection_window.bind("<Key>", self._on_key_press)
        self.selection_window.focus_set()
    
    def _show_all_positions_visual(self):
        """Show visual indicators for all configured positions on screen"""
        # Create a fullscreen overlay to show position indicators
        indicator_window = tk.Toplevel()
        indicator_window.attributes('-alpha', 0.3)  # Much more transparent overlay (30% opacity)
        indicator_window.attributes('-topmost', True)
        indicator_window.overrideredirect(True)
        indicator_window.configure(bg='black')
        
        # Make it cover all screens
        screen_width = indicator_window.winfo_screenwidth()
        screen_height = indicator_window.winfo_screenheight()
        indicator_window.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Create canvas for drawing indicators
        canvas = tk.Canvas(indicator_window, bg='black', highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        # Helper function to format chip amounts
        def format_amount(amount):
            if amount >= 1000000:
                # Remove trailing zeros and decimal point if not needed
                formatted = f"{amount/1000000:.2f}"
                # Remove trailing zeros and decimal point
                formatted = formatted.rstrip('0').rstrip('.')
                return f"{formatted}M"
            elif amount >= 1000:
                return f"{amount//1000}K"
            else:
                return str(amount)
        
        # Draw indicators for betting areas (smaller, transparent circles)
        for area_name, position in self.positions.items():
            if position.x > 0 and position.y > 0:  # Only show if position is set
                color = "green"
                if area_name == "player_area":
                    label = "PLAYER"
                    color = "blue"
                elif area_name == "banker_area":
                    label = "BANKER"
                    color = "red"
                elif area_name == "cancel_button":
                    label = "CANCEL"
                    color = "orange"
                else:
                    label = area_name.upper()
                
                # Draw much smaller circle indicator with higher transparency
                radius = 12  # Much smaller radius
                x, y = position.x, position.y
                canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                                 outline=color, width=1, fill=color, stipple="gray75")  # 75% transparency
                
                # Draw smaller label with clear, solid text
                canvas.create_text(x, y, text=label, fill="white", 
                                 font=("Arial", 8, "bold"), stipple="")  # No stipple for clear text
        
        # Draw indicators for chips (small circles with maximum transparency)
        for chip in self.chips:
            if chip.position and chip.position.x > 0 and chip.position.y > 0:
                x, y = chip.position.x, chip.position.y
                
                # Draw small circle indicator for chips with maximum transparency
                radius = 8  # Small circle radius
                canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                                 outline="yellow", width=1, fill="yellow", stipple="gray50")  # 50% transparency (more visible)
                
                # Draw chip amount in short format below the circle with clear, solid text
                short_amount = format_amount(chip.amount)
                canvas.create_text(x, y+15, text=short_amount, fill="yellow", 
                                 font=("Arial", 8, "bold"), stipple="")  # No stipple for clear text
        
        # Add instructions at the top of the screen with more visible color
        canvas.create_text(screen_width//2, 50, 
                         text="Visual Position Display - Press ESC or Click to Close", 
                         fill="yellow", font=("Arial", 16, "bold"), stipple="")  # Bright yellow color for visibility
        
        # Bind close events
        def close_indicator(event=None):
            indicator_window.destroy()
        
        indicator_window.bind("<Button-1>", close_indicator)
        indicator_window.bind("<Key>", lambda e: close_indicator() if e.keysym == 'Escape' else None)
        indicator_window.focus_set()
        
        # Auto-close after 10 seconds
        indicator_window.after(10000, close_indicator)
    
    def _on_key_press(self, event):
        """Handle key press events"""
        if event.keysym == 'Escape':
            # Check if we're in overlay mode or selection window mode
            if hasattr(self, 'overlay_window') and self.overlay_window and self.overlay_window.winfo_viewable():
                # In overlay mode - cancel selection
                self._cancel_overlay()
            else:
                # In selection window mode - close window
                self._close_configuration()
        elif event.state & 0x20000 and event.keysym == 'F4':  # Alt+F4
            # Close selection window
            self._close_configuration()
    
    def _on_mouse_motion(self, event):
        """Handle mouse motion to show circle at mouse position"""
        if not hasattr(self, 'mouse_canvas') or not self.mouse_canvas:
            return
            
        # Clear previous circle
        self.mouse_canvas.delete("mouse_circle")
        
        # Use screen-based coordinates for both circle and display
        screen_x, screen_y = event.x_root, event.y_root
        
        # Convert screen coordinates to canvas coordinates for drawing
        # Since canvas covers the entire screen starting at (0,0), screen coords = canvas coords
        canvas_x, canvas_y = screen_x, screen_y
        
        # But we need to account for the overlay window position
        overlay_x = self.overlay_window.winfo_x()
        overlay_y = self.overlay_window.winfo_y()
        
        # Calculate relative position on canvas
        canvas_x = screen_x - overlay_x
        canvas_y = screen_y - overlay_y
        
        radius = 15  # Circle radius
        
        # Create a semi-transparent red circle at canvas coordinates
        self.mouse_canvas.create_oval(
            canvas_x - radius, canvas_y - radius, 
            canvas_x + radius, canvas_y + radius,
            fill="red", 
            stipple="gray50",  # This creates 50% alpha effect
            tags="mouse_circle"
        )
        
        # Add a border to make it more visible
        self.mouse_canvas.create_oval(
            canvas_x - radius, canvas_y - radius, 
            canvas_x + radius, canvas_y + radius,
            outline="white", 
            width=2,
            tags="mouse_circle"
        )
        
        # Update instruction label with screen-based cursor position
        if hasattr(self, 'instruction_label'):
            mode_text = {
                SelectionMode.PLAYER_AREA: "Player Bet Area",
                SelectionMode.BANKER_AREA: "Banker Bet Area", 
                SelectionMode.CANCEL_BUTTON: "Cancel Button",
                SelectionMode.CHIP: "Chip Position"
            }.get(self.selection_mode, "Unknown")
            
            self.instruction_label.config(
                text=f"Click to select {mode_text}\nPress ESC to return\nCursor: ({screen_x}, {screen_y})"
            )
    
    def _start_area_selection(self, mode: SelectionMode):
        """Start selection for a specific area"""
        self.selection_mode = mode
        # Minimize the configuration window and main window to allow comfortable clicking
        try:
            import tkinter as tk
            # Minimize the configuration window
            if self.selection_window:
                self.selection_window.iconify()
            # Try to minimize the root window if available
            root = self.selection_window.master if self.selection_window else None
            if isinstance(root, tk.Tk):
                root.iconify()
        except Exception:
            pass
        self._show_overlay_instructions()
    
    def _show_overlay_instructions(self):
        """Show instructions on the overlay window"""
        if self.overlay_window:
            self.overlay_window.deiconify()
            self.overlay_window.lift()
            self.overlay_window.focus_force()
            self.overlay_window.attributes('-topmost', True)
            
            print(f"Overlay window shown, size: {self.overlay_window.winfo_width()}x{self.overlay_window.winfo_height()}")  # Debug
            
            # Grab focus to ensure visibility
            try:
                self.overlay_window.grab_set()
            except:
                pass  # Ignore if grab fails
            
            # Update instruction text based on selection mode
            mode_text = {
                SelectionMode.PLAYER_AREA: "Player Bet Area",
                SelectionMode.BANKER_AREA: "Banker Bet Area", 
                SelectionMode.CANCEL_BUTTON: "Cancel Button",
                SelectionMode.CHIP: "Chip Position"
            }.get(self.selection_mode, "Unknown")
            
            # Update the instruction label
            if hasattr(self, 'instruction_label'):
                # Get current mouse position for initial display
                try:
                    import win32api
                    x, y = win32api.GetCursorPos()
                    cursor_text = f"Cursor: ({x}, {y})"
                except:
                    cursor_text = "Cursor: (0, 0)"
                
                self.instruction_label.config(
                    text=f"Click to select {mode_text}\nPress ESC to return\n{cursor_text}"
                )
                # Ensure label is visible
                self.instruction_label.lift()
                
                print(f"Instruction label updated with text: {self.instruction_label.cget('text')}")  # Debug
            
            self.overlay_window.title(f"Select {mode_text}")
            
            print(f"Overlay window shown for {mode_text}")  # Debug
    
    def _create_overlay_window(self):
        """Create transparent overlay window for position selection"""
        print("Creating overlay window...")  # Debug
        
        try:
            self.overlay_window = tk.Toplevel()
            self.overlay_window.attributes('-alpha', 0.5)
            self.overlay_window.attributes('-topmost', True)
            self.overlay_window.overrideredirect(True)
            self.overlay_window.configure(bg='gray20')  # Set a dark background
            
            # Make it cover the entire screen
            screen_width = self.overlay_window.winfo_screenwidth()
            screen_height = self.overlay_window.winfo_screenheight()
            self.overlay_window.geometry(f"{screen_width}x{screen_height}+0+0")
            
            print(f"Overlay window size: {screen_width}x{screen_height}")  # Debug
            
            # Add instruction label at the TOP (50% alpha) - CREATE FIRST
            instruction_frame = tk.Frame(self.overlay_window, bg="yellow", relief="raised", bd=3)
            instruction_frame.place(relx=0.5, rely=0.05, anchor="center")
            
            print(f"Instruction frame created at relx=0.5, rely=0.05")  # Debug
            
            # Get current mouse position for initial display
            try:
                import win32api
                x, y = win32api.GetCursorPos()
                cursor_text = f"Cursor: ({x}, {y})"
            except:
                cursor_text = "Cursor: (0, 0)"
            
            self.instruction_label = tk.Label(instruction_frame, 
                                             text=f"Click to select position\nPress ESC to return\n{cursor_text}",
                                             font=("Arial", 16, "bold"),
                                             bg="yellow", fg="black",
                                             padx=20, pady=10)
            self.instruction_label.pack()
            
            print(f"Instruction label created with text: {self.instruction_label.cget('text')}")  # Debug
            
            # Create canvas for drawing the mouse circle - CREATE AFTER instruction frame
            self.mouse_canvas = tk.Canvas(self.overlay_window, highlightthickness=0)
            self.mouse_canvas.place(x=0, y=0, width=screen_width, height=screen_height)
            
            # Ensure instruction frame is visible above canvas
            instruction_frame.lift()
            
            # Bind mouse events to the window (not canvas) for correct coordinates
            self.overlay_window.bind("<Button-1>", self._on_overlay_click)
            self.overlay_window.bind("<Key>", self._on_key_press)
            self.overlay_window.bind("<Motion>", self._on_mouse_motion)
            
            # Initially hide the overlay
            self.overlay_window.withdraw()
            
            print("Overlay window created successfully")  # Debug
            
        except Exception as e:
            print(f"Error creating overlay window: {e}")
            raise
    
    def _on_overlay_click(self, event):
        """Handle click on overlay to set position"""
        x, y = event.x_root, event.y_root
        print(f"Position selected: ({x}, {y}) for mode: {self.selection_mode}")  # Debug
        
        # Get monitor information for the selected coordinates
        try:
            from cv_utils import get_monitor_for_coordinates
            target_monitor = get_monitor_for_coordinates(x, y)
            monitor_info = f"Monitor: {target_monitor['left']},{target_monitor['top']} {target_monitor['width']}x{target_monitor['height']}"
            print(f"Selected position on {monitor_info}")
        except Exception as e:
            print(f"Could not determine monitor: {e}")
            monitor_info = "Monitor: Unknown"
        
        # Clear the mouse circle
        if hasattr(self, 'mouse_canvas') and self.mouse_canvas:
            self.mouse_canvas.delete("mouse_circle")
        
        # Store position based on selection mode
        if self.selection_mode == SelectionMode.PLAYER_AREA:
            self.positions['player_area'] = Position(x=x, y=y, width=50, height=50, name='player_area')
            print(f"Player area set at ({x}, {y}) - {monitor_info}")
        elif self.selection_mode == SelectionMode.BANKER_AREA:
            self.positions['banker_area'] = Position(x=x, y=y, width=50, height=50, name='banker_area')
            print(f"Banker area set at ({x}, {y}) - {monitor_info}")
        elif self.selection_mode == SelectionMode.CANCEL_BUTTON:
            self.positions['cancel_button'] = Position(x=x, y=y, width=50, height=50, name='cancel_button')
            print(f"Cancel button set at ({x}, {y}) - {monitor_info}")
        elif self.selection_mode == SelectionMode.CHIP:
            if hasattr(self, '_pending_chip_amount') and self._pending_chip_amount:
                amount = self._pending_chip_amount
                position = Position(x=x, y=y, width=50, height=50, name=f"chip_{amount}")
                
                # Check if chip already exists
                existing_chip = next((chip for chip in self.chips if chip.amount == amount), None)
                if existing_chip:
                    existing_chip.position = position
                    print(f"Updated chip {amount} position to ({x}, {y}) - {monitor_info}")
                else:
                    self.chips.append(ChipConfig(amount=amount, position=position))
                    print(f"Added new chip {amount} at ({x}, {y}) - {monitor_info}")
                
                # Clear pending amount
                self._pending_chip_amount = None
                
                # Handle reselecting chip
                if hasattr(self, '_reselecting_chip') and self._reselecting_chip:
                    self._reselecting_chip = None
        
        # Save configuration immediately
        self._update_chip_amounts_from_entries()
        self.save_config()
        print("Configuration saved immediately")
        
        # Properly reset selection mode and release grab
        print(f"Resetting selection mode from {self.selection_mode} to NONE")  # Debug
        self.selection_mode = SelectionMode.NONE
        
        # Release grab if set
        try:
            if self.overlay_window:
                self.overlay_window.grab_release()
                print("Released overlay grab")  # Debug
        except:
            pass
        
        # Hide overlay
        self.overlay_window.withdraw()
        print("Overlay window hidden")  # Debug
        
        # Restore the configuration window and main window
        try:
            if self.selection_window:
                self.selection_window.deiconify()
                self.selection_window.lift()
                self.selection_window.focus_force()
            root = self.selection_window.master
            if isinstance(root, tk.Tk):
                root.deiconify()
                root.lift()
                root.focus_force()
        except Exception:
            pass
        
        self._update_status_displays()

    def _get_chip_amount_and_save(self, x: int, y: int):
        """Get chip amount from user and save position (fallback method)"""
        amount = simpledialog.askinteger("Chip Amount", 
                                        "Enter the chip amount:",
                                        minvalue=1, maxvalue=999999999)
        if amount is not None:
            position = Position(x=x, y=y, width=50, height=50, name=f"chip_{amount}")
            
            # Check if chip already exists
            existing_chip = next((chip for chip in self.chips if chip.amount == amount), None)
            if existing_chip:
                existing_chip.position = position
            else:
                self.chips.append(ChipConfig(amount=amount, position=position))
            
            # Save configuration immediately
            self._update_chip_amounts_from_entries()
            self.save_config()
            print("Chip configuration saved immediately")
            
            # Properly reset selection mode and release grab
            self.selection_mode = SelectionMode.NONE
            
            # Release grab if set
            try:
                if self.overlay_window:
                    self.overlay_window.grab_release()
            except:
                pass
            
            self.overlay_window.withdraw()
            msg = messagebox.showinfo("Chip Added", f"Chip {amount} set at ({x}, {y})")
            # Bring the message box to front
            if self.selection_window:
                self.selection_window.lift()
                self.selection_window.focus_force()
    
    def _cancel_overlay(self):
        """Cancel overlay selection"""
        print("Canceling overlay selection")  # Debug
        
        # Clear the mouse circle
        if hasattr(self, 'mouse_canvas') and self.mouse_canvas:
            self.mouse_canvas.delete("mouse_circle")
        
        # Release grab if set
        try:
            if self.overlay_window:
                self.overlay_window.grab_release()
                print("Released overlay grab (cancel)")  # Debug
        except:
            pass
            
        self.overlay_window.withdraw()
        print(f"Resetting selection mode from {self.selection_mode} to NONE (cancel)")  # Debug
        self.selection_mode = SelectionMode.NONE
        
        # Restore the configuration window and main window
        try:
            import tkinter as tk
            if self.selection_window:
                self.selection_window.deiconify()
                self.selection_window.lift()
                self.selection_window.focus_force()
                root = self.selection_window.master
                if isinstance(root, tk.Tk):
                    root.deiconify()
                    root.lift()
                    root.focus_force()
        except Exception:
            pass
    
    def _select_chip_position(self, original_amount: int):
        """Select position for a predefined chip"""
        # Get the current amount from the entry field
        amount_var = self.chip_entries.get(original_amount)
        if amount_var:
            try:
                amount = int(amount_var.get())
                if amount <= 0:
                    messagebox.showerror("Invalid Amount", "Please enter a valid positive amount")
                    return
            except ValueError:
                messagebox.showerror("Invalid Amount", "Please enter a valid number")
                return
        else:
            amount = original_amount
        
        # Store the amount for later position selection
        self._pending_chip_amount = amount
        # Start position selection for this chip
        self.selection_mode = SelectionMode.CHIP
        # Minimize the configuration window to allow comfortable clicking
        try:
            import tkinter as tk
            if self.selection_window:
                self.selection_window.iconify()
            root = self.selection_window.master if self.selection_window else None
            if isinstance(root, tk.Tk):
                root.iconify()
        except Exception:
            pass
        self._show_overlay_instructions()

    def _add_custom_chip(self):
        """Add a custom chip with manual amount input"""
        amount = simpledialog.askinteger("Custom Chip", 
                                        "Enter the chip amount:",
                                        minvalue=1, maxvalue=999999999)
        if amount is not None:
            # Check if chip already exists
            if any(chip.amount == amount for chip in self.chips):
                msg = messagebox.showwarning("Duplicate Chip", f"Chip {amount} already exists!")
                # Bring the message box to front
                if self.selection_window:
                    self.selection_window.lift()
                    self.selection_window.focus_force()
                return
            
            # Store the amount for later position selection
            self._pending_chip_amount = amount
            # Start position selection for this chip
            self.selection_mode = SelectionMode.CHIP
            # Minimize the configuration window to allow comfortable clicking
            try:
                import tkinter as tk
                if self.selection_window:
                    self.selection_window.iconify()
                root = self.selection_window.master if self.selection_window else None
                if isinstance(root, tk.Tk):
                    root.iconify()
            except Exception:
                pass
            # Show the overlay window for position selection
            self._show_overlay_instructions()
    
    def _on_chip_amount_changed(self, original_amount: int, amount_var: tk.StringVar):
        """Handle chip amount changes and save immediately"""
        try:
            new_amount = int(amount_var.get())
            if new_amount > 0 and new_amount != original_amount:
                print(f"Chip amount changed from {original_amount} to {new_amount}")
                
                # Find and update the chip
                chip_found = False
                for chip in self.chips:
                    if chip.amount == original_amount:
                        chip.amount = new_amount
                        print(f"Updated chip amount in memory from {original_amount} to {new_amount}")
                        chip_found = True
                        break
                
                if not chip_found:
                    # If chip doesn't exist yet, create it (without position)
                    new_chip = ChipConfig(amount=new_amount, position=Position(x=0, y=0, width=50, height=50, name=f"chip_{new_amount}"))
                    self.chips.append(new_chip)
                    print(f"Added new chip with amount {new_amount}")
                
                # Save configuration immediately
                self.save_config()
                print(f"Configuration saved immediately after chip amount change")
                
                # Rebuild the UI to reflect the new amount
                self._rebuild_chip_ui()
                
        except ValueError:
            print(f"Invalid amount entered: {amount_var.get()}")
            # Revert to original amount
            amount_var.set(str(original_amount))

    def _update_status_displays(self):
        """Update the status labels for each area"""
        if hasattr(self, 'player_status_label'):
            if 'player_area' in self.positions:
                pos = self.positions['player_area']
                self.player_status_label.config(text=f"({pos.x}, {pos.y})", fg="green")
            else:
                self.player_status_label.config(text="Not set", fg="red")
        
        if hasattr(self, 'banker_status_label'):
            if 'banker_area' in self.positions:
                pos = self.positions['banker_area']
                self.banker_status_label.config(text=f"({pos.x}, {pos.y})", fg="green")
            else:
                self.banker_status_label.config(text="Not set", fg="red")
        
        if hasattr(self, 'cancel_status_label'):
            if 'cancel_button' in self.positions:
                pos = self.positions['cancel_button']
                self.cancel_status_label.config(text=f"({pos.x}, {pos.y})", fg="green")
            else:
                self.cancel_status_label.config(text="Not set", fg="red")
        
        # Update chip status labels
        if hasattr(self, 'chip_status_labels'):
            for amount, status_label in self.chip_status_labels.items():
                # Find chip with this amount
                chip = next((c for c in self.chips if c.amount == amount), None)
                if chip and chip.position and chip.position.x > 0:
                    status_label.config(text=f"({chip.position.x}, {chip.position.y})", fg="green")
                else:
                    status_label.config(text="Not set", fg="red")
    
    def _reselect_chip(self, chip: ChipConfig):
        """Reselect position for a chip"""
        self.selection_mode = SelectionMode.CHIP
        # Store reference to chip being reselected
        self._reselecting_chip = chip
        # Store the amount for position selection
        self._pending_chip_amount = chip.amount
        # Minimize the configuration window to allow comfortable clicking
        try:
            import tkinter as tk
            if self.selection_window:
                self.selection_window.iconify()
            root = self.selection_window.master if self.selection_window else None
            if isinstance(root, tk.Tk):
                root.iconify()
        except Exception:
            pass
        # Create and show the overlay window for position selection
        self._create_overlay_window()
    
    def _remove_chip(self, chip: ChipConfig):
        """Remove a chip from the list"""
        if messagebox.askyesno("Remove Chip", f"Remove chip {chip.amount}?"):
            self.chips.remove(chip)
            # Save configuration immediately after removing chip
            self.save_config()
            print(f"Removed chip {chip.amount} and saved configuration")
            self._rebuild_chip_ui()
            # Bring the message box to front
            if self.selection_window and self.selection_window.winfo_exists():
                self.selection_window.lift()
                self.selection_window.focus_force()
    
    def _remove_chip_by_amount(self, amount: int):
        """Remove a chip by amount"""
        # Find the chip with this amount
        chip_to_remove = next((chip for chip in self.chips if chip.amount == amount), None)
        
        if chip_to_remove:
            if messagebox.askyesno("Remove Chip", f"Remove chip {amount}?"):
                self.chips.remove(chip_to_remove)
                # Save configuration immediately after removing chip
                self.save_config()
                print(f"Removed chip {amount} and saved configuration")
                # Refresh the UI to rebuild the chip list
                self._rebuild_chip_ui()
                # Bring the message box to front
                if self.selection_window and self.selection_window.winfo_exists():
                    self.selection_window.lift()
                    self.selection_window.focus_force()
        else:
            messagebox.showwarning("Chip Not Found", f"Chip {amount} not found in configuration.")

    def _rebuild_chip_ui(self):
        """Rebuild the chip UI after changes"""
        if hasattr(self, 'selection_window') and self.selection_window:
            # Rebuild the entire UI to reflect changes
            self._build_selection_ui()
    
    def _update_chip_amounts_from_entries(self):
        """Update chip amounts from the entry fields"""
        print("Updating chip amounts from entry fields...")
        
        # Update predefined chips
        for original_amount, amount_var in self.chip_entries.items():
            try:
                new_amount = int(amount_var.get())
                if new_amount > 0:
                    # Find the chip with the original amount and update it
                    chip_found = False
                    for chip in self.chips:
                        if chip.amount == original_amount:
                            old_amount = chip.amount
                            chip.amount = new_amount
                            print(f"Updated chip amount from {old_amount} to {new_amount}")
                            chip_found = True
                            break
                    
                    if not chip_found:
                        # If chip doesn't exist yet, create it (without position)
                        new_chip = ChipConfig(amount=new_amount, position=Position(x=0, y=0, width=50, height=50, name=f"chip_{new_amount}"))
                        self.chips.append(new_chip)
                        print(f"Added new chip with amount {new_amount}")
            except ValueError:
                print(f"Invalid amount for chip {original_amount}: {amount_var.get()}")
        
        # Update custom chips (if any entry fields exist for them)
        # This part is no longer needed as custom chips are managed by the unified chip system
        # The _rebuild_chip_ui method handles rebuilding the entire chip UI.
        # The _update_chip_amounts_from_entries method is now primarily for predefined chips.
        # The _on_chip_amount_changed method handles custom chip amount changes.
        # The _reselect_chip method handles reselecting a custom chip.
        # The _remove_chip_by_amount method handles removing a custom chip by amount.
        # The _rebuild_chip_ui method handles rebuilding the entire chip UI.

        print(f"Updated {len(self.chips)} chips with new amounts")
    
    def _cancel_selection(self):
        """Cancel the selection process"""
        if messagebox.askyesno("Cancel", "Are you sure you want to cancel? All changes will be lost."):
            if self.selection_window:
                self.selection_window.destroy()
            if self.overlay_window:
                self.overlay_window.destroy()
    
    def _close_without_save(self):
        """Close the selection window (changes are already auto-saved)"""
        # Close windows
        if self.selection_window:
            self.selection_window.destroy()
        if self.overlay_window:
            self.overlay_window.destroy()
        
        # Call callback if provided
        if self.on_position_selected:
            self.on_position_selected()
    
    def _close_configuration(self):
        """Close the selection window (changes are already auto-saved)"""
        # Close windows
        if self.selection_window:
            self.selection_window.destroy()
        if self.overlay_window:
            self.overlay_window.destroy()
        
        # Call callback if provided
        if self.on_position_selected:
            self.on_position_selected()

    def _on_window_close(self):
        """Handle window close event to save configuration"""
        # Since all changes are auto-saved, just close the window
        try:
            # Close windows
            if self.selection_window:
                self.selection_window.destroy()
            if self.overlay_window:
                self.overlay_window.destroy()
            
            # Call callback if provided
            if self.on_position_selected:
                self.on_position_selected()
                
        except Exception as e:
            print(f"Error during window close: {e}")
            # Ensure windows are destroyed even if there's an error
            try:
                if self.selection_window:
                    self.selection_window.destroy()
                if self.overlay_window:
                    self.overlay_window.destroy()
            except:
                pass

    def get_position(self, name: str) -> Optional[Position]:
        """Get a saved position by name"""
        return self.positions.get(name)
    
    def get_chip_position(self, amount: int) -> Optional[Position]:
        """Get position for a specific chip amount"""
        for chip in self.chips:
            if chip.amount == amount:
                return chip.position
        return None
    
    def get_all_chips(self) -> List[ChipConfig]:
        """Get all configured chips"""
        return self.chips.copy()
    
    def is_configured(self) -> bool:
        """Check if all required positions are configured"""
        required_positions = ['player_area', 'banker_area', 'cancel_button']
        return all(pos in self.positions for pos in required_positions) 