#!/usr/bin/env python3
"""
DRCM Setup
Created by: Dev_Z / ipad_halobuck
"""

import urllib.request
import subprocess
import sys
import shutil
import os
import zipfile
import json
from pathlib import Path

def main():
    print("=" * 60)
    print("         DRCM Setup")
    print("=" * 60)
    print()
    print("         Created by: Dev_Z / ipad_halobuck")
    print()
    print("=" * 60)
    print()

    # Get user's paths
    user_home = Path.home()
    downloads_dir = user_home / "Downloads"
    drcm_dir = downloads_dir / "Drcm"
    drcm_script = drcm_dir / "drcm.py"
    version_file = drcm_dir / "version.txt"

    # GitHub URLs
    github_base = "https://raw.githubusercontent.com/jfs8u7ahfa8ufhafaiohff5435dsg8778633328/fsa8fhafiahfa-98fahf9apufhaofhf8s-9afhagf09-aff98asyfa09f8ayfa09ff8yaf908a7ftasfghas908fagthy4sgy5-_/refs/heads/main"
    drcm_url = f"{github_base}/drcm.py"
    version_url = f"{github_base}/version.txt"

    # Create folder
    drcm_dir.mkdir(parents=True, exist_ok=True)

    # Get remote version
    remote_version = "1.0.0"
    try:
        req = urllib.request.Request(version_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            remote_version = response.read().decode().strip()
    except Exception as e:
        print(f"Could not get version: {e}")

    print(f"Version: {remote_version}")
    print()

    # Download drcm.py
    print("Downloading DRCM...")
    temp_file = drcm_dir / "drcm_temp.py"

    try:
        req = urllib.request.Request(drcm_url)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(temp_file, 'wb') as f:
                f.write(response.read())

        # Try to obfuscate with PyArmor if available
        print("Checking for PyArmor...")
        obf_available = False
        try:
            result = subprocess.run([sys.executable, "-m", "pyarmor", "--version"], 
                                   capture_output=True, timeout=5)
            obf_available = result.returncode == 0
        except:
            obf_available = False

        if obf_available:
            print("Obfuscating with PyArmor...")
            obf_result = subprocess.run(
                [sys.executable, "-m", "pyarmor", "obfuscate", "--output", str(drcm_dir / "obf"), str(temp_file)],
                capture_output=True, text=True
            )

            # Find obfuscated file
            obf_file = None
            obf_dir = drcm_dir / "obf"
            if obf_dir.exists():
                for f in obf_dir.rglob("*.py"):
                    if f.name != "drcm_temp.py":
                        obf_file = f
                        break

            if obf_file and obf_file.exists():
                shutil.copy2(obf_file, drcm_script)
                shutil.rmtree(obf_dir, ignore_errors=True)
                print("Obfuscation successful!")
            else:
                shutil.copy2(temp_file, drcm_script)
                print("Obfuscation failed, using original.")
        else:
            print("PyArmor not installed, using original script.")
            shutil.copy2(temp_file, drcm_script)

        temp_file.unlink()

        # Save version
        with open(version_file, 'w') as f:
            f.write(remote_version)

        print("Setup complete!")
        print()
        print("Launching DRCM...")
        print()

        # Launch DRCM
        subprocess.Popen([sys.executable, str(drcm_script)])

    except Exception as e:
        print(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
