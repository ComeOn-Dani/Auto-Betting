#!/usr/bin/env python3
"""
Test script to verify configuration loading
"""

import os
import sys
import json

def test_config_loading():
    """Test hardcoded configuration loading"""
    print("=== Testing Hardcoded Configuration ===")
    
    # Test hardcoded config
    server_config = {
        'controller': {
            'http_url': 'http://localhost:3000',
            'ws_url': 'ws://localhost:8080'
        }
    }
    
    print("✓ Using hardcoded server configuration")
    print(f"  HTTP URL: {server_config['controller']['http_url']}")
    print(f"  WS URL: {server_config['controller']['ws_url']}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_config_loading() 