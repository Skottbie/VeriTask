#!/usr/bin/env python3
"""Find the v3.4.9 session file by scanning all .jsonl files"""
import os, datetime

base = r"\\wsl$\Ubuntu\home\skottbie\.openclaw"

# Find ALL .jsonl files
print("All .jsonl files:")
results = []
for root, dirs, files in os.walk(base):
    # Skip venv and node_modules
    dirs[:] = [d for d in dirs if d not in ('venv', 'node_modules', '.git')]
    for f in files:
        if f.endswith('.jsonl'):
            full = os.path.join(root, f)
            try:
                size = os.path.getsize(full)
                mtime = os.path.getmtime(full)
                dt = datetime.datetime.fromtimestamp(mtime)
                results.append((mtime, dt, size, full))
            except:
                pass

results.sort(reverse=True)
for mtime, dt, size, full in results[:15]:
    rel = full.replace(base + "\\", "")
    print(f"  {dt.strftime('%Y-%m-%d %H:%M')} | {size:>8} bytes | {rel}")
