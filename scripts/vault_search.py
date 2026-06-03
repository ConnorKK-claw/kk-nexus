#!/usr/bin/env python3
"""重定向到全局 vault_search.py。"""
import sys, os, subprocess
global_script = os.path.join(os.environ["USERPROFILE"], ".codex", "bin", "vault_search.py")
if os.path.exists(global_script):
    result = subprocess.run([sys.executable, global_script] + sys.argv[1:])
    sys.exit(result.returncode)
else:
    print("[ERR] 全局 vault_search.py 未找到")
    print(f"    术期路径: {global_script}")
    sys.exit(1)
