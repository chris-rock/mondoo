# Copyright (c) Mondoo, Inc.
# SPDX-License-Identifier: BUSL-1.1

import requests
from typing import List, Dict, Set
import sys
import argparse

# Define expected files per endpoint
EXPECTED_FILES = {
    "mondoo": {
        "darwin": ["darwin_universal.pkg"],
        "linux": [
            "linux_386.deb", "linux_386.rpm",
            "linux_amd64.deb", "linux_amd64.rpm",
            "linux_arm64.deb", "linux_arm64.rpm",
            "linux_armv6.deb", "linux_armv6.rpm",
            "linux_armv7.deb", "linux_armv7.rpm",
            "linux_ppc64le.deb", "linux_ppc64le.rpm"
        ],
        "windows": ["windows_amd64.msi", "windows_arm64.msi"]
    },
    "cnquery": {
        "darwin": ["darwin_universal.pkg"],
        "linux": [
            "linux_amd64.deb", "linux_amd64.rpm",
            "linux_arm64.deb", "linux_arm64.rpm"
        ],
        "windows": ["windows_amd64.msi"]
    },
    "cnspec": {
        "darwin": ["darwin_universal.pkg"],
        "linux": [
            "linux_amd64.deb", "linux_amd64.rpm",
            "linux_arm64.deb", "linux_arm64.rpm"
        ],
        "windows": ["windows_amd64.msi"]
    }
}

def human_size(size_in_bytes: int) -> str:
    """Convert bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 500.0:
            return f"{size_in_bytes:3.1f}{unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f}GB"

def validate_release_files(url: str, expected_files: Dict[str, List[str]], min_size: int = 500) -> List[str]:
    """
    Validates that all expected file types are present in a release.
    
    Args:
        url: The URL of the release JSON endpoint
        expected_files: Dictionary of platform-specific expected file suffixes
        min_size: Minimum required file size
    
    Returns:
        List of error messages, empty if validation successful
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        errors = []
        found_files = {}  # Store filename and size
        version = data.get('version', '')
        
        print(f"\nValidating version: {version}")
        print(f"{'File':<30} {'Status':<10} {'Size':<10}")
        print("-" * 50)
        
        # First, collect all files from the release
        for file in data.get('files', []):
            filename = file.get('filename', '')
            size = file.get('size', 0)
            
            if 'checksums' in filename.lower():
                continue
                
            # Extract the file suffix
            for platform, suffixes in expected_files.items():
                for suffix in suffixes:
                    if filename.endswith(f"{version}_{suffix}"):
                        found_files[f"{platform}_{suffix}"] = size
        
        # Check each expected file
        for platform, suffixes in expected_files.items():
            for suffix in suffixes:
                expected = f"{platform}_{suffix}"
                if expected in found_files:
                    size = found_files[expected]
                    status = "FOUND" if size >= min_size else "SMALL"
                    if size < min_size:
                        errors.append(f"File size too small ({size} bytes): {suffix}")
                    print(f"{suffix:<30} {status:<10} {human_size(size):<10}")
                else:
                    errors.append(f"Missing expected file: {suffix}")
                    print(f"{suffix:<30} {'MISSING':<10} {'N/A':<10}")
        
        if errors:
            print("\nErrors detected:")
            for error in errors:
                print(f"- {error}")
        else:
            print("\nAll files validated successfully")
            
        return errors
        
    except requests.exceptions.RequestException as e:
        return [f"Failed to fetch release data: {str(e)}"]
    except ValueError as e:
        return [f"Failed to parse JSON data: {str(e)}"]

def main():
    parser = argparse.ArgumentParser(description='Validate release files for Mondoo products')
    parser.add_argument('product', choices=['mondoo', 'cnquery', 'cnspec'], help='Product to validate')
    args = parser.parse_args()
    
    endpoints = {
        "mondoo": "https://releases.mondoo.com/mondoo/latest.json",
        "cnquery": "https://releases.mondoo.com/cnquery/latest.json",
        "cnspec": "https://releases.mondoo.com/cnspec/latest.json"
    }
    
    url = endpoints[args.product]
    print(f"\nValidating {args.product} release at {url}")
    errors = validate_release_files(url, EXPECTED_FILES[args.product])
    
    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
