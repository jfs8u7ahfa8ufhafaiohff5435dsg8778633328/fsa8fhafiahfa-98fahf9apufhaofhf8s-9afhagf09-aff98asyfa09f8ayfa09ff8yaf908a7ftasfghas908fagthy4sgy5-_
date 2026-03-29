#!/usr/bin/env python3
"""
DRCM Updater
Created by: Dev_Z / ipad_halobuck
"""

import urllib.request
import os
import sys
import shutil
from pathlib import Path

def main():
    print("=" * 50)
    print("         DRCM Updater")
    print("=" * 50)
    print()
    print("Checking for updates...")
    print()

    # Script name to update
    script_name = "drcm_startup.py"
    github_url = f"https://raw.githubusercontent.com/jfs8u7ahfa8ufhafaiohff5435dsg8778633328/fsa8fhafiahfa-98fahf9apufhaofhf8s-9afhagf09-aff98asyfa09f8ayfa09ff8yaf908a7ftasfghas908fagthy4sgy5-_/refs/heads/main/{script_name}"

    # Temp file for download
    temp_file = Path(script_name + ".new")
    current_file = Path(script_name)

    print(f"Downloading latest {script_name}...")

    try:
        # Download the latest version
        req = urllib.request.Request(github_url)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(temp_file, 'wb') as f:
                f.write(response.read())

        print("Download successful!")
        print()
        print("Updating...")

        # Delete old file and rename new one
        if current_file.exists():
            current_file.unlink()
            print("Old script removed.")

        shutil.move(str(temp_file), str(current_file))

        print("Update complete!")
        print()
        print("New version installed.")
        print()
        print(f"You can now run {script_name} again.")

    except Exception as e:
        print(f"Download failed: {e}")
        if temp_file.exists():
            temp_file.unlink()

    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
