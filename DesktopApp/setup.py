#!/usr/bin/env python3
"""
Setup script for Bet Automation Macro Interface
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_sample_config():
    """Create sample configuration if it doesn't exist"""
    config_file = "config.json"
    if not os.path.exists(config_file):
        print("\n⚙️ Creating sample configuration...")
        sample_config = {
            "controller": {
                "http_url": "http://localhost:3000",
                "ws_url": "ws://localhost:3000"
            },
            "templates": {
                "match_threshold": 0.8,
                "max_search_time_ms": 5000,
                "player_area": "assets/player_area.png",
                "banker_area": "assets/banker_area.png",
                "cancel_button": "assets/cancel_button.png",
                "chips": {
                    "1000": "assets/chips/1000.png",
                    "25000": "assets/chips/25000.png",
                    "125000": "assets/chips/125000.png",
                    "250000": "assets/chips/250000.png",
                    "500000": "assets/chips/500000.png",
                    "1250000": "assets/chips/1250000.png",
                    "2500000": "assets/chips/2500000.png",
                    "5000000": "assets/chips/5000000.png",
                    "50000000": "assets/chips/50000000.png"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        print("✅ Sample configuration created")
    else:
        print("✅ Configuration file already exists")

def check_assets():
    """Check if asset files exist"""
    print("\n🎨 Checking asset files...")
    assets_dir = Path("assets")
    if not assets_dir.exists():
        print("⚠️ Assets directory not found")
        print("   You may need to copy asset files from the original installation")
        return False
    
    required_files = [
        "player_area.png",
        "banker_area.png", 
        "cancel_button.png"
    ]
    
    missing_files = []
    for file in required_files:
        if not (assets_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️ Missing asset files: {', '.join(missing_files)}")
        print("   The macro interface will work without these files")
        return False
    
    print("✅ Asset files found")
    return True

def run_demo():
    """Run the demo script"""
    print("\n🎯 Running macro interface demo...")
    try:
        subprocess.check_call([sys.executable, "demo_macro.py"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Demo failed: {e}")
        return False
    except FileNotFoundError:
        print("⚠️ Demo script not found")
        return False

def main():
    """Main setup function"""
    print("🚀 Bet Automation Macro Interface Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Create sample config
    create_sample_config()
    
    # Check assets
    check_assets()
    
    # Run demo
    demo_success = run_demo()
    
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("\n📋 Next steps:")
    print("1. Run: python main.py")
    print("2. Login with your credentials")
    print("3. Click 'Configure Positions' to set up macro positions")
    print("4. Select 'Macro (Position-based)' mode")
    print("5. Start betting!")
    
    if demo_success:
        print("\n✅ Demo completed successfully - macro interface is working!")
    else:
        print("\n⚠️ Demo failed - check the error messages above")
    
    print("\n📖 For more information, see README_MACRO.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 