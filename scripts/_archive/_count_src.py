import re, os, sys
sys.stdout.reconfigure(encoding="utf-8")
path = os.path.join("scripts", "gen_bb0_comparison.py")
with open(path, "r", encoding="utf-8") as f:
    c = f.read()
for kw in [chr(20108)+chr(32426)+chr(24066)+chr(22330)+chr(22238)+chr(36141), chr(23450)+chr(21521)+chr(24066)+chr(22330)+chr(22238)+chr(36141)]:
    print(f"{kw}: {c.count(kw)}")