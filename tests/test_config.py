#!/usr/bin/env python3
"""
Test Configuration Module
Provides centralized URL configuration for all test files using environment variables
"""

import os
import subprocess
import json

def get_azd_env_value(key):
    """Get a value from azd environment variables"""
    try:
        result = subprocess.run(
            ['azd', 'env', 'get-values'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))  # Go to project root
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.startswith(f'{key}='):
                    return line.split('=', 1)[1].strip('"')
    except Exception as e:
        print(f"Warning: Could not get azd env value for {key}: {e}")
    return None

def get_test_urls():
    """Get test URLs from environment variables with fallbacks"""
    
    # Try to get Azure URL from azd environment
    azure_url = get_azd_env_value('SERVICE_API_URI')
    
    # Fallback to environment variables if azd command fails
    if not azure_url:
        azure_url = os.getenv('SERVICE_API_URI', 'https://your-webapp-name.azurewebsites.net')
    
    # Local URLs (these are standard)
    local_url = os.getenv('LOCAL_SERVICE_URL', 'http://127.0.0.1:5000')
    
    return {
        'BASE_URL': local_url,  # Local popup interface (default)
        'AZURE_URL': azure_url,  # Azure popup interface (default)
        'TESTING_LOCAL': f"{local_url}/testing",  # Local detailed testing interface
        'TESTING_AZURE': f"{azure_url}/testing",  # Azure detailed testing interface
    }

# Get URLs when module is imported
URLS = get_test_urls()

# Export individual URLs for backward compatibility
BASE_URL = URLS['BASE_URL']
AZURE_URL = URLS['AZURE_URL']
TESTING_LOCAL = URLS['TESTING_LOCAL']
TESTING_AZURE = URLS['TESTING_AZURE']

if __name__ == "__main__":
    print("Test Configuration URLs:")
    for key, value in URLS.items():
        print(f"  {key}: {value}")