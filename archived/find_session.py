#!/usr/bin/env python3
"""Find the v3.4.9 session file"""
import json, os, glob

# Check where session_v348.jsonl was copied from (read the parse_v347.py to find pattern)
# The sessions are stored under ~/.openclaw somewhere
# Let's check the UNC path from Windows
base = r"\\wsl$\Ubuntu\home\skottbie\.openclaw"
print(f"Checking base: {base}")
print(f"Exists: {os.path.exists(base)}")

# List directories
for item in os.listdir(base):
    path = os.path.join(base, item)
    if os.path.isdir(path):
        print(f"  DIR: {item}")
    else:
        print(f"  FILE: {item} ({os.path.getsize(path)} bytes)")

# Find all transcript.jsonl files
print("\nSearching for transcript.jsonl files...")
for root, dirs, files in os.walk(base):
    for f in files:
        if f == "transcript.jsonl":
            full = os.path.join(root, f)
            size = os.path.getsize(full)
            mtime = os.path.getmtime(full)
            import datetime
            dt = datetime.datetime.fromtimestamp(mtime)
            print(f"  {dt.strftime('%Y-%m-%d %H:%M')} | {size:>8} bytes | {full}")
