#!/usr/bin/env python3
"""
Demo script for the Macro Interface
This script demonstrates how to use the macro interface programmatically
"""

import json
import time
from macro_interface import MacroInterface, SelectionMode
from macro_betting import MacroBaccarat

def demo_macro_interface():
    """Demonstrate the macro interface functionality"""
    print("=== Macro Interface Demo ===\n")
    
    # Create macro interface
    macro = MacroInterface("demo_macro_config.json")
    betting = MacroBaccarat(macro, logger=print)
    
    print("1. Creating sample configuration...")
    
    # Create sample positions (these would normally be set by user clicking)
    sample_positions = {
        'player_area': {'x': 200, 'y': 300, 'width': 80, 'height': 60, 'name': ''},
        'banker_area': {'x': 400, 'y': 300, 'width': 80, 'height': 60, 'name': ''},
        'cancel_button': {'x': 600, 'y': 500, 'width': 60, 'height': 40, 'name': ''}
    }
    
    # Create sample chips
    sample_chips = [
        {'amount': 1000, 'position': {'x': 50, 'y': 600, 'width': 50, 'height': 50, 'name': 'chip_1000'}},
        {'amount': 25000, 'position': {'x': 120, 'y': 600, 'width': 50, 'height': 50, 'name': 'chip_25000'}},
        {'amount': 125000, 'position': {'x': 190, 'y': 600, 'width': 50, 'height': 50, 'name': 'chip_125000'}},
        {'amount': 500000, 'position': {'x': 260, 'y': 600, 'width': 50, 'height': 50, 'name': 'chip_500000'}},
        {'amount': 1000000, 'position': {'x': 330, 'y': 600, 'width': 50, 'height': 50, 'name': 'chip_1000000'}}
    ]
    
    # Load sample data into macro interface
    for name, pos_data in sample_positions.items():
        from dataclasses import dataclass
        Position = dataclass(frozen=True, slots=True)
        position = Position(**pos_data)
        macro.positions[name] = position
    
    for chip_data in sample_chips:
        from dataclasses import dataclass
        Position = dataclass(frozen=True, slots=True)
        ChipConfig = dataclass(frozen=True, slots=True)
        position = Position(**chip_data['position'])
        chip = ChipConfig(amount=chip_data['amount'], position=position)
        macro.chips.append(chip)
    
    # Save configuration
    macro.save_config()
    print("✓ Sample configuration created and saved")
    
    print("\n2. Checking configuration status...")
    if betting.is_configured():
        print("✓ All required positions are configured")
    else:
        print("✗ Configuration incomplete")
        return
    
    print("\n3. Testing chip composition...")
    test_amounts = [1000, 25000, 125000, 500000, 1000000, 175000, 750000]
    
    for amount in test_amounts:
        plan = betting.compose_amount(amount)
        if plan:
            print(f"  {amount:,} → {plan}")
        else:
            print(f"  {amount:,} → Cannot compose")
    
    print("\n4. Testing position retrieval...")
    
    # Test bet area positions
    player_pos = betting.get_bet_area_position('Player')
    banker_pos = betting.get_bet_area_position('Banker')
    cancel_pos = betting.get_cancel_button_position()
    
    print(f"  Player area: ({player_pos.x}, {player_pos.y})")
    print(f"  Banker area: ({banker_pos.x}, {banker_pos.y})")
    print(f"  Cancel button: ({cancel_pos.x}, {cancel_pos.y})")
    
    # Test chip positions
    for amount in [1000, 25000, 125000]:
        chip_pos = betting.get_chip_position(amount)
        if chip_pos:
            print(f"  Chip {amount:,}: ({chip_pos.x}, {chip_pos.y})")
        else:
            print(f"  Chip {amount:,}: Not found")
    
    print("\n5. Configuration summary:")
    print(f"  Bet areas configured: {len(macro.positions)}")
    print(f"  Chips configured: {len(macro.chips)}")
    print(f"  Available chip amounts: {[chip.amount for chip in macro.chips]}")
    
    print("\n6. Sample betting simulation (without actual clicking):")
    print("  Note: This is a simulation - no actual clicking will occur")
    
    # Simulate bet placement
    test_bets = [
        (1000, 'Player'),
        (25000, 'Banker'),
        (175000, 'Player'),  # This will use composition
        (1000000, 'Banker')
    ]
    
    for amount, side in test_bets:
        print(f"\n  Placing {amount:,} bet on {side}:")
        
        # Check if exact chip exists
        exact_chip = betting.get_chip_position(amount)
        if exact_chip:
            print(f"    ✓ Exact chip found at ({exact_chip.x}, {exact_chip.y})")
        else:
            # Check composition
            plan = betting.compose_amount(amount)
            if plan:
                print(f"    ✓ Composition plan: {plan}")
                for chip_amount in plan:
                    chip_pos = betting.get_chip_position(chip_amount)
                    print(f"      - {chip_amount:,} at ({chip_pos.x}, {chip_pos.y})")
            else:
                print(f"    ✗ Cannot compose amount {amount:,}")
        
        # Get bet area
        area_pos = betting.get_bet_area_position(side)
        print(f"    ✓ {side} area at ({area_pos.x}, {area_pos.y})")
    
    print("\n=== Demo Complete ===")
    print("\nTo use the actual interface:")
    print("1. Run: python main.py")
    print("2. Login and click 'Configure Positions'")
    print("3. Click on screen positions for each area")
    print("4. Add custom chip amounts as needed")
    print("5. Save configuration and start betting!")

if __name__ == "__main__":
    demo_macro_interface() 