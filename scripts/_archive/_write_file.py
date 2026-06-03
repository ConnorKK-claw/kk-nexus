#!/usr/bin/env python3
"""Helper: write a file from stdin content."""
import sys
path = sys.argv[1]
content = sys.stdin.read()
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Written: {path} ({len(content)} bytes)")
