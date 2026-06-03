# -*- coding: utf-8 -*-
"""Search for accounting treatment of equity incentives"""
import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Try to search Bing for relevant info
search_terms = [
    "股权激励 会计处理 计入薪酬 每年分摊 限制性股票 CAS 11",
    "股份支付 等待期 分摊 高管薪酬 年报披露",
    "上市公司股权激励 薪酬总额 会计口径 包含股权激励报酬",
]

for term in search_terms:
    url = f"https://www.bing.com/search?q={urllib.parse.quote(term)}&cc=cn&setlang=zh-Hans"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        content = resp.read().decode("utf-8", errors="ignore")
        import re
        # Find snippets that contain relevant info
        texts = re.findall(r'>([^<]{50,300})<', content)
        print(f"\n=== Search: {term[:30]}... ===")
        found = 0
        for t in texts:
            if any(kw in t for kw in ["薪酬","报酬","股份支付","摊销","分摊","每年","限制性","股权激励报酬"]):
                if found < 5:
                    print(f"  {t.strip()}")
                    found += 1
    except Exception as e:
        print(f"Error: {e}")
