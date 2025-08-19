#!/usr/bin/env python3
"""
Asset checker for Bet Automation
This script checks for required asset files and provides guidance
"""

import os
import json
from pathlib import Path

def check_assets():
    """Check for required asset files"""
    print("🔍 Checking Bet Automation Assets")
    print("=" * 50)
    
    # Load config to see what assets are expected
    config_file = "config.json"
    if not os.path.exists(config_file):
        print("❌ config.json not found")
        return False
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    templates = config.get('templates', {})
    
    # Check main area templates
    print("\n📁 Main Area Templates:")
    main_areas = ['player_area', 'banker_area', 'cancel_button']
    missing_main = []
    
    for area in main_areas:
        path = templates.get(area)
        if path and os.path.exists(path):
            print(f"  ✅ {area}: {path}")
        else:
            print(f"  ❌ {area}: {path} (missing)")
            missing_main.append(area)
    
    # Check chip templates
    print("\n🎰 Chip Templates:")
    chips = templates.get('chips', {})
    missing_chips = []
    
    for amount, path in chips.items():
        if os.path.exists(path):
            print(f"  ✅ {amount}: {path}")
        else:
            print(f"  ❌ {amount}: {path} (missing)")
            missing_chips.append(amount)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"  Main areas: {len(main_areas) - len(missing_main)}/{len(main_areas)} found")
    print(f"  Chips: {len(chips) - len(missing_chips)}/{len(chips)} found")
    
    if missing_main or missing_chips:
        print("\n⚠️ Missing Assets Detected")
        print("\nThe macro interface will work without these files, but image recognition mode will not function properly.")
        print("\nTo obtain the missing assets:")
        print("1. Take screenshots of your game interface")
        print("2. Crop the images to include only the relevant areas")
        print("3. Save them with the exact names shown above")
        print("4. Place them in the assets/ directory")
        
        if missing_main:
            print(f"\nMissing main areas: {', '.join(missing_main)}")
        if missing_chips:
            print(f"\nMissing chips: {', '.join(missing_chips)}")
        
        print("\n💡 Tip: You can use the macro interface without these assets!")
        print("   The macro mode uses position-based clicking instead of image recognition.")
        
        return False
    else:
        print("\n✅ All assets found! Both macro and image recognition modes are available.")
        return True

def create_asset_directories():
    """Create asset directories if they don't exist"""
    print("\n📁 Creating asset directories...")
    
    directories = [
        "assets",
        "assets/chips"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}/")
    
    print("\n📝 Next steps:")
    print("1. Add your game screenshots to the assets/ directory")
    print("2. Or use the macro interface which doesn't require these files")

def main():
    """Main function"""
    assets_ok = check_assets()
    
    if not assets_ok:
        create_asset_directories()
    
    print("\n🎯 Recommendation:")
    if assets_ok:
        print("✅ You can use both macro and image recognition modes")
    else:
        print("💡 Use the macro interface - it's faster and more reliable!")
        print("   Run: python main.py")
        print("   Select 'Macro (Position-based)' mode")
        print("   Click 'Configure Positions' to set up")

if __name__ == "__main__":
    main() 