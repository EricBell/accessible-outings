import argparse
import json
import hashlib
import os
from pathlib import Path
import re

VERSION_FILE = Path(__file__).parent / "version.json"
TARGET_FILE = Path(__file__).parent / "templates/base.html"

def load_version():
    if VERSION_FILE.exists():
        with open(VERSION_FILE, "r") as f:
            data = json.load(f)
        return data
    else:
        return {
            "version": [1, 0, 0],
            "file_hashes": {}
        }

def save_version(data):
    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def update_html_version(version):
    # Update the version number in base.html
    with open(TARGET_FILE, "r") as f:
        lines = f.readlines()
    new_lines = []
    found = False
    for line in lines:
        if "Built with accessibility in mind." in line:
            # Replace or append version number
            if "version" in line:
                new_line = re.sub(r'version\s+\d+\.\d+\.\d+', f'version {".".join(map(str, version))}', line)
            else:
                new_line = line.rstrip() + f' <span class="text-muted" style="font-size:0.9em;">version {".".join(map(str, version))}</span>\n'
            new_lines.append(new_line)
            found = True
        else:
            new_lines.append(line)
    if not found:
        # fallback: append to end
        new_lines.append(f'<!-- version {".".join(map(str, version))} -->\n')
    with open(TARGET_FILE, "w") as f:
        f.writelines(new_lines)

def main():
    import re
    parser = argparse.ArgumentParser(description="Manage version number and file hashes.")
    parser.add_argument("command", choices=["major", "minor", "patch", "info", "check"], help="Version operation")
    parser.add_argument("--file", default=str(TARGET_FILE), help="File to check for changes (default: base.html)")
    args = parser.parse_args()

    data = load_version()
    version = data["version"]
    file_hashes = data.get("file_hashes", {})
    file_path = Path(args.file)
    file_key = str(file_path.resolve())

    if args.command == "major":
        version[0] += 1
        version[1] = 0
        version[2] = 0
        print(f"Updated to version {'.'.join(map(str, version))}")
    elif args.command == "minor":
        version[1] += 1
        version[2] = 0
        print(f"Updated to version {'.'.join(map(str, version))}")
    elif args.command == "patch":
        version[2] += 1
        print(f"Updated to version {'.'.join(map(str, version))}")
    elif args.command == "info":
        print(f"Current version: {'.'.join(map(str, version))}")
        return
    elif args.command == "check":
        current_hash = get_file_hash(file_path)
        last_hash = file_hashes.get(file_key)
        if last_hash != current_hash:
            version[2] += 1
            print(f"File changed. Patch version incremented to {'.'.join(map(str, version))}")
            file_hashes[file_key] = current_hash
        else:
            print("No changes detected.")
    else:
        parser.print_help()
        return

    # Always update version in HTML and save version.json except for info
    if args.command != "info":
        update_html_version(version)
        data["version"] = version
        data["file_hashes"] = file_hashes
        save_version(data)

if __name__ == "__main__":
    main()