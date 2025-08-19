#!/usr/bin/env python3
"""
Startup script for Bet Automation
This script checks for missing assets and provides guidance before launching
"""

import os
import sys
import subprocess
from pathlib import Path

def check_missing_assets():
    """Check for missing asset files and return list"""
    missing = []
    
    # Check config file
    if not os.path.exists("config.json"):
        missing.append("config.json")
        return missing
    
    try:
        import json
        with open("config.json", 'r') as f:
            config = json.load(f)
        
        templates = config.get('templates', {})
        
        # Check main templates
        for area in ['player_area', 'banker_area', 'cancel_button']:
            path = templates.get(area)
            if path and not os.path.exists(path):
                missing.append(path)
        
        # Check chip templates
        chips = templates.get('chips', {})
        for amount, path in chips.items():
            if not os.path.exists(path):
                missing.append(path)
                
    except Exception as e:
        missing.append(f"Error reading config: {e}")
    
    return missing

def main():
    """Main startup function"""
    print("🚀 Starting Bet Automation...")
    print("=" * 40)
    
    # Check for missing assets
    missing_assets = check_missing_assets()
    
    if missing_assets:
        print("⚠️ Some asset files are missing:")
        for asset in missing_assets:
            print(f"   - {asset}")
        
        print("\n💡 The macro interface will work without these files!")
        print("   Image recognition mode may not function properly.")
        print("\nTo fix missing assets:")
        print("1. Run: python check_assets.py")
        print("2. Add the missing files to the assets/ directory")
        print("3. Or use the macro interface which doesn't need these files")
        
        response = input("\nContinue anyway? (y/n): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Exiting...")
            return
    
    print("\n✅ Starting application...")
    print("💡 Tip: Use 'Macro (Position-based)' mode for best results!")
    
    # Launch the main application
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")

if __name__ == "__main__":
    main() 