# -*- coding: utf-8 -*-
"""Search key Chinese accounting resources"""
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Access direct sources about CAS 11 share-based payment
urls = [
    "https://www.gov.cn/gongbao/content/2006/content_304942.htm",
    "https://kjs.mof.gov.cn/zt/zhengcefabu/2006/200806/t20080618_46215.html",
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        content = resp.read().decode("utf-8", errors="ignore")
        import re
        text = re.sub(r"<[^>]+>", "", content)
        lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 20]
        print(f"\n=== {url} ({len(lines)} lines) ===")
        for l in lines[:30]:
            print(l[:300])
    except Exception as e:
        print(f"{url}: {e}")
