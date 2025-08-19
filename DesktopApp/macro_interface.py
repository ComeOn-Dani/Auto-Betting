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
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    
                # Load positions
                for name, pos_data in data.get('positions', {}).items():
                    self.positions[name] = Position(**pos_data)
                    
                # Load chips
                self.chips = []
                for chip_data in data.get('chips', []):
                    position = Position(**chip_data['position'])
                    self.chips.append(ChipConfig(
                        amount=chip_data['amount'],
                        position=position
                    ))
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save current positions and chip configurations"""
        data = {
            'positions': {name: asdict(pos) for name, pos in self.positions.items()},
            'chips': [{'amount': chip.amount, 'position': asdict(chip.position)} for chip in self.chips]
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def start_position_selection(self, mode: SelectionMode = SelectionMode.NONE, callback: Optional[Callable] = None):
        """Start position selection mode"""
        self.selection_mode = mode
        self.on_position_selected = callback
        self._create_selection_window()
        self._create_overlay_window()
    
    def _create_selection_window(self):
        """Create the main selection interface window"""
        print("Creating selection window...")  # Debug
        
        # Create the window
        self.selection_window = tk.Toplevel()
        self.selection_window.title("Position Selection")
        self.selection_window.geometry("560x720")
        self.selection_window.resizable(False, False)
        
        # Center the window
        self.selection_window.update_idletasks()
        x = (self.selection_window.winfo_screenwidth() // 2) - (560 // 2)
        y = (self.selection_window.winfo_screenheight() // 2) - (720 // 2)
        self.selection_window.geometry(f"560x720+{x}+{y}")
        
        # Make window stay on top and visible
        self.selection_window.attributes('-topmost', True)
        self.selection_window.deiconify()
        self.selection_window.lift()
        self.selection_window.focus_force()
        
        # Removed temporary test label
        print("Building selection UI...")  # Debug
        self._build_selection_ui()
        print("Selection window created successfully")  # Debug
    
    def _build_selection_ui(self):
        """Build the selection interface UI"""
        # Title
        title_label = tk.Label(self.selection_window, text="Position Selection", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(self.selection_window, 
                               text="Click 'Select Position' for each area,\nthen click on the screen where you want to place it.",
                               font=("Arial", 10), justify="center")
        instructions.pack(pady=10)
        
        # Main areas frame
        areas_frame = ttk.LabelFrame(self.selection_window, text="Betting Areas", padding=10)
        areas_frame.pack(fill="x", padx=10, pady=5)
        
        # Player Area
        player_frame = tk.Frame(areas_frame)
        player_frame.pack(fill="x", pady=5)
        tk.Label(player_frame, text="Player Bet Area:").pack(side="left")
        self.player_status = tk.Label(player_frame, text="Not set", fg="red")
        self.player_status.pack(side="right")
        tk.Button(player_frame, text="Select Position", 
                 command=lambda: self._start_area_selection(SelectionMode.PLAYER_AREA)).pack(side="right", padx=5)
        
        # Banker Area
        banker_frame = tk.Frame(areas_frame)
        banker_frame.pack(fill="x", pady=5)
        tk.Label(banker_frame, text="Banker Bet Area:").pack(side="left")
        self.banker_status = tk.Label(banker_frame, text="Not set", fg="red")
        self.banker_status.pack(side="right")
        tk.Button(banker_frame, text="Select Position", 
                 command=lambda: self._start_area_selection(SelectionMode.BANKER_AREA)).pack(side="right", padx=5)
        
        # Cancel Button
        cancel_frame = tk.Frame(areas_frame)
        cancel_frame.pack(fill="x", pady=5)
        tk.Label(cancel_frame, text="Cancel Button:").pack(side="left")
        self.cancel_status = tk.Label(cancel_frame, text="Not set", fg="red")
        self.cancel_status.pack(side="right")
        tk.Button(cancel_frame, text="Select Position", 
                 command=lambda: self._start_area_selection(SelectionMode.CANCEL_BUTTON)).pack(side="right", padx=5)
        
        # Chips frame
        chips_frame = ttk.LabelFrame(self.selection_window, text="Chips", padding=10)
        chips_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # All chips frame (predefined + custom)
        all_chips_frame = tk.Frame(chips_frame)
        all_chips_frame.pack(fill="both", expand=True, pady=5)
        
        # Predefined chip amounts
        self.predefined_chips = [1000, 25000, 125000, 500000, 1250000, 2500000, 5000000, 50000000]
        self.chip_entries = {}
        self.chip_status_labels = {}
        
        # Create predefined chips using pack layout
        for i, amount in enumerate(self.predefined_chips):
            chip_frame = tk.Frame(all_chips_frame)
            chip_frame.pack(fill="x", pady=2)
            
            # Editable amount entry
            amount_var = tk.StringVar(value=str(amount))
            amount_entry = tk.Entry(chip_frame, textvariable=amount_var, width=15)
            amount_entry.pack(side="left", padx=5)
            self.chip_entries[amount] = amount_var
            
            # Position status label
            status_label = tk.Label(chip_frame, text="Not set", fg="red", width=15)
            status_label.pack(side="left", padx=5)
            self.chip_status_labels[amount] = status_label
            
            # Select position button
            select_btn = tk.Button(chip_frame, text="Select Position", 
                                 command=lambda a=amount: self._select_chip_position(a))
            select_btn.pack(side="right", padx=5)
        
        # Separator
        ttk.Separator(chips_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Add custom chip button
        add_chip_btn = tk.Button(chips_frame, text="+ Add Custom Chip", 
                                command=self._add_custom_chip, bg="#4CAF50", fg="white")
        add_chip_btn.pack(pady=5)
        
        # Custom chips list (for chips not in predefined list)
        self.chips_canvas = tk.Canvas(chips_frame, height=100)
        chips_scrollbar = ttk.Scrollbar(chips_frame, orient="vertical", command=self.chips_canvas.yview)
        self.custom_chips_frame = tk.Frame(self.chips_canvas)
        
        self.chips_canvas.configure(yscrollcommand=chips_scrollbar.set)
        
        self.chips_canvas.pack(side="left", fill="both", expand=True)
        chips_scrollbar.pack(side="right", fill="y")
        
        self.chips_canvas.create_window((0, 0), window=self.custom_chips_frame, anchor="nw")
        self.custom_chips_frame.bind("<Configure>", lambda e: self.chips_canvas.configure(scrollregion=self.chips_canvas.bbox("all")))
        
        # Action buttons
        actions_frame = tk.Frame(self.selection_window)
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        # View All Positions button
        view_positions_btn = tk.Button(actions_frame, text="View All Positions", 
                                      command=self._view_all_positions, bg="#FF9800", fg="white")
        view_positions_btn.pack(side="left", padx=5)
        
        # Show All Positions button (visual indicators)
        show_positions_btn = tk.Button(actions_frame, text="Show All Positions", 
                                      command=self._show_all_positions_visual, bg="#9C27B0", fg="white")
        show_positions_btn.pack(side="left", padx=5)
        
        save_btn = tk.Button(actions_frame, text="Save Configuration", 
                            command=self._save_and_close, bg="#2196F3", fg="white")
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = tk.Button(actions_frame, text="Cancel", 
                              command=self._cancel_selection)
        cancel_btn.pack(side="right", padx=5)
        
        # Update status displays
        self._update_status_displays()
        self._refresh_chips_list()
    
    def _view_all_positions(self):
        """Show all configured positions in a popup window"""
        # Create popup window
        popup = tk.Toplevel(self.selection_window)
        popup.title("All Configured Positions")
        popup.geometry("400x500")
        popup.resizable(False, False)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (500 // 2)
        popup.geometry(f"400x500+{x}+{y}")
        
        # Make popup stay on top
        popup.attributes('-topmost', True)
        popup.lift()
        popup.focus_force()
        
        # Title
        title_label = tk.Label(popup, text="Configured Positions", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(popup, height=400)
        scrollbar = tk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Betting Areas Section
        areas_frame = tk.LabelFrame(scrollable_frame, text="Betting Areas", font=("Arial", 10, "bold"))
        areas_frame.pack(fill="x", padx=5, pady=5)
        
        # Player Area
        if 'player_area' in self.positions:
            pos = self.positions['player_area']
            tk.Label(areas_frame, text=f"Player Bet Area: ({pos.x}, {pos.y})", fg="green").pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(areas_frame, text="Player Bet Area: Not set", fg="red").pack(anchor="w", padx=10, pady=2)
        
        # Banker Area
        if 'banker_area' in self.positions:
            pos = self.positions['banker_area']
            tk.Label(areas_frame, text=f"Banker Bet Area: ({pos.x}, {pos.y})", fg="green").pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(areas_frame, text="Banker Bet Area: Not set", fg="red").pack(anchor="w", padx=10, pady=2)
        
        # Cancel Button
        if 'cancel_button' in self.positions:
            pos = self.positions['cancel_button']
            tk.Label(areas_frame, text=f"Cancel Button: ({pos.x}, {pos.y})", fg="green").pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(areas_frame, text="Cancel Button: Not set", fg="red").pack(anchor="w", padx=10, pady=2)
        
        # Chips Section
        chips_frame = tk.LabelFrame(scrollable_frame, text="Chips", font=("Arial", 10, "bold"))
        chips_frame.pack(fill="x", padx=5, pady=5)
        
        if self.chips:
            # Sort chips by amount
            sorted_chips = sorted(self.chips, key=lambda x: x.amount)
            for chip in sorted_chips:
                if chip.position:
                    tk.Label(chips_frame, text=f"{chip.amount:,}: ({chip.position.x}, {chip.position.y})", fg="green").pack(anchor="w", padx=10, pady=2)
                else:
                    tk.Label(chips_frame, text=f"{chip.amount:,}: Not set", fg="red").pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(chips_frame, text="No chips configured", fg="gray").pack(anchor="w", padx=10, pady=2)
        
        # Summary
        summary_frame = tk.LabelFrame(scrollable_frame, text="Summary", font=("Arial", 10, "bold"))
        summary_frame.pack(fill="x", padx=5, pady=5)
        
        total_positions = len(self.positions)
        total_chips = len(self.chips)
        configured_chips = sum(1 for chip in self.chips if chip.position)
        
        tk.Label(summary_frame, text=f"Betting Areas: {total_positions}/3 configured").pack(anchor="w", padx=10, pady=2)
        tk.Label(summary_frame, text=f"Chips: {configured_chips}/{total_chips} with positions (optional)").pack(anchor="w", padx=10, pady=2)
        
        # Status indicator
        if total_positions == 3:
            tk.Label(summary_frame, text="✅ Ready for betting", fg="green", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(summary_frame, text="❌ Missing required positions", fg="red", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=2)
        
        # Close button
        close_btn = tk.Button(popup, text="Close", command=popup.destroy, bg="#4CAF50", fg="white")
        close_btn.pack(pady=10)
    
    def _show_all_positions_visual(self):
        """Show visual indicators for all configured positions on screen"""
        # Create a fullscreen overlay to show position indicators
        indicator_window = tk.Toplevel()
        indicator_window.attributes('-alpha', 0.8)
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
        
        # Draw indicators for betting areas
        for area_name, position in self.positions.items():
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
            
            # Draw circle indicator
            radius = 30
            x, y = position.x, position.y
            canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                             outline=color, width=3, fill=color, stipple="gray50")
            
            # Draw label
            canvas.create_text(x, y, text=label, fill="white", 
                             font=("Arial", 12, "bold"))
            
            # Draw coordinates
            canvas.create_text(x, y+40, text=f"({x}, {y})", fill="white", 
                             font=("Arial", 10))
        
        # Draw indicators for chips
        for chip in self.chips:
            if chip.position:
                x, y = chip.position.x, chip.position.y
                
                # Draw square indicator for chips
                size = 25
                canvas.create_rectangle(x-size, y-size, x+size, y+size, 
                                      outline="yellow", width=3, fill="yellow", stipple="gray25")
                
                # Draw chip amount
                canvas.create_text(x, y, text=str(chip.amount), fill="black", 
                                 font=("Arial", 10, "bold"))
                
                # Draw coordinates
                canvas.create_text(x, y+35, text=f"({x}, {y})", fill="yellow", 
                                 font=("Arial", 9))
        
        # Add instructions at the bottom
        canvas.create_text(screen_width//2, screen_height-50, 
                         text="Visual Position Display - Press ESC or Click to Close", 
                         fill="white", font=("Arial", 16, "bold"))
        
        # Bind close events
        def close_indicator(event=None):
            indicator_window.destroy()
        
        indicator_window.bind("<Button-1>", close_indicator)
        indicator_window.bind("<Key>", lambda e: close_indicator() if e.keysym == 'Escape' else None)
        indicator_window.focus_set()
        
        # Auto-close after 10 seconds
        indicator_window.after(10000, close_indicator)
    
    def _on_key_press(self, event):
        """Handle key press events on overlay"""
        if event.keysym == 'Escape':
            self._cancel_overlay()
    
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
        """Handle click on overlay window"""
        if self.selection_mode == SelectionMode.NONE:
            return
        
        # Clear the mouse circle
        if hasattr(self, 'mouse_canvas') and self.mouse_canvas:
            self.mouse_canvas.delete("mouse_circle")
        
        # Get click position relative to screen (absolute coordinates)
        x, y = event.x_root, event.y_root
        
        # Debug information
        print(f"Click captured: event.x={event.x}, event.y={event.y}")
        print(f"Screen coordinates: event.x_root={event.x_root}, event.y_root={event.y_root}")
        print(f"Final position stored: ({x}, {y})")
        
        # Create position with default size (can be adjusted later)
        position = Position(x=x, y=y, width=50, height=50, name="")
        
        # Store position based on mode
        if self.selection_mode == SelectionMode.PLAYER_AREA:
            self.positions['player_area'] = position
            print(f"Stored Player area at: ({x}, {y})")
        elif self.selection_mode == SelectionMode.BANKER_AREA:
            self.positions['banker_area'] = position
            print(f"Stored Banker area at: ({x}, {y})")
        elif self.selection_mode == SelectionMode.CANCEL_BUTTON:
            self.positions['cancel_button'] = position
            print(f"Stored Cancel button at: ({x}, {y})")
        elif self.selection_mode == SelectionMode.CHIP:
            # For chips, use the pending amount or get it from user
            if hasattr(self, '_pending_chip_amount'):
                amount = self._pending_chip_amount
                delattr(self, '_pending_chip_amount')  # Clear the pending amount
            else:
                # Fallback: get amount from user
                self._get_chip_amount_and_save(x, y)
                return

            # Save the chip position
            position = Position(x=x, y=y, width=50, height=50, name=f"chip_{amount}")

            # Check if chip already exists
            existing_chip = next((chip for chip in self.chips if chip.amount == amount), None)
            if existing_chip:
                existing_chip.position = position
                print(f"Updated chip {amount} position to: ({x}, {y})")
            else:
                self.chips.append(ChipConfig(amount=amount, position=position))
                print(f"Added new chip {amount} at: ({x}, {y})")

            # Hide overlay and update UI
            # Release grab if set
            try:
                if self.overlay_window:
                    self.overlay_window.grab_release()
            except:
                pass
                
            self.overlay_window.withdraw()
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
            
            self._update_status_displays()
            self._refresh_chips_list()
            return
        
        # Hide overlay and update UI
        # Release grab if set
        try:
            if self.overlay_window:
                self.overlay_window.grab_release()
        except:
            pass
            
        self.overlay_window.withdraw()
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
            
            self.overlay_window.withdraw()
            self.selection_mode = SelectionMode.NONE
            self._refresh_chips_list()
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
        except:
            pass
            
        self.overlay_window.withdraw()
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
            self._show_overlay_instructions()
    
    def _update_status_displays(self):
        """Update the status labels for each area"""
        if hasattr(self, 'player_status'):
            if 'player_area' in self.positions:
                pos = self.positions['player_area']
                self.player_status.config(text=f"({pos.x}, {pos.y})", fg="green")
            else:
                self.player_status.config(text="Not set", fg="red")
        
        if hasattr(self, 'banker_status'):
            if 'banker_area' in self.positions:
                pos = self.positions['banker_area']
                self.banker_status.config(text=f"({pos.x}, {pos.y})", fg="green")
            else:
                self.banker_status.config(text="Not set", fg="red")
        
        if hasattr(self, 'cancel_status'):
            if 'cancel_button' in self.positions:
                pos = self.positions['cancel_button']
                self.cancel_status.config(text=f"({pos.x}, {pos.y})", fg="green")
            else:
                self.cancel_status.config(text="Not set", fg="red")
        
        # Update chip status labels
        if hasattr(self, 'chip_status_labels'):
            for amount, status_label in self.chip_status_labels.items():
                # Find chip with this amount
                chip = next((c for c in self.chips if c.amount == amount), None)
                if chip and chip.position:
                    status_label.config(text=f"({chip.position.x}, {chip.position.y})", fg="green")
                else:
                    status_label.config(text="Not set", fg="red")
    
    def _refresh_chips_list(self):
        """Refresh the custom chips list display"""
        # Clear existing widgets
        for widget in self.custom_chips_frame.winfo_children():
            widget.destroy()
        
        # Filter out predefined chips and sort custom chips by amount
        custom_chips = [chip for chip in self.chips if chip.amount not in self.predefined_chips]
        sorted_chips = sorted(custom_chips, key=lambda x: x.amount)
        
        if not sorted_chips:
            tk.Label(self.custom_chips_frame, text="No custom chips added yet", fg="gray").pack(pady=10)
            return
        
        for chip in sorted_chips:
            chip_frame = tk.Frame(self.custom_chips_frame)
            chip_frame.pack(fill="x", pady=2)
            
            # Editable amount entry
            amount_var = tk.StringVar(value=str(chip.amount))
            amount_entry = tk.Entry(chip_frame, textvariable=amount_var, width=15)
            amount_entry.pack(side="left", padx=5)
            
            # Position status
            status_text = f"({chip.position.x}, {chip.position.y})" if chip.position else "Not set"
            status_color = "green" if chip.position else "red"
            status_label = tk.Label(chip_frame, text=status_text, fg=status_color, width=15)
            status_label.pack(side="left", padx=5)
            
            # Select position button
            select_btn = tk.Button(chip_frame, text="Select Position", 
                                 command=lambda c=chip: self._reselect_chip(c))
            select_btn.pack(side="right", padx=5)
            
            # Remove button
            remove_btn = tk.Button(chip_frame, text="Remove", 
                                 command=lambda c=chip: self._remove_chip(c))
            remove_btn.pack(side="right", padx=5)
    
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
        self._show_overlay_instructions()
    
    def _remove_chip(self, chip: ChipConfig):
        """Remove a chip from the list"""
        if messagebox.askyesno("Remove Chip", f"Remove chip {chip.amount}?"):
            self.chips.remove(chip)
            self._refresh_chips_list()
            # Bring the message box to front
            if self.selection_window:
                self.selection_window.lift()
                self.selection_window.focus_force()
    
    def _save_and_close(self):
        """Save configuration and close selection window"""
        # Check if all required positions are set
        required_positions = ['player_area', 'banker_area', 'cancel_button']
        missing = [pos for pos in required_positions if pos not in self.positions]
        
        if missing:
            msg = messagebox.showwarning("Missing Positions", 
                                f"Please set the following positions:\n{', '.join(missing)}")
            # Bring the message box to front
            if self.selection_window:
                self.selection_window.lift()
                self.selection_window.focus_force()
            return

        # Save configuration
        self.save_config()
        
        # Close windows
        if self.selection_window:
            self.selection_window.destroy()
        if self.overlay_window:
            self.overlay_window.destroy()
        
        # Call callback if provided
        if self.on_position_selected:
            self.on_position_selected()
        
        msg = messagebox.showinfo("Success", "Configuration saved successfully!")
		# Bring the message box to front
        if self.selection_window:
            self.selection_window.lift()
            self.selection_window.focus_force()
    
    def _cancel_selection(self):
        """Cancel the selection process"""
        if messagebox.askyesno("Cancel", "Are you sure you want to cancel? All changes will be lost."):
            if self.selection_window:
                self.selection_window.destroy()
            if self.overlay_window:
                self.overlay_window.destroy()
    
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