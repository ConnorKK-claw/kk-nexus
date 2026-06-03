import urllib.request
import json
import ssl

# Use a simple search API to find relevant information
# Bing search API or similar

# Let me try to access a few relevant pages
urls = [
    "https://wiki.mbalib.com/wiki/%E8%82%A1%E4%BB%BD%E6%94%AF%E4%BB%98",
    "https://www.gov.cn/gongbao/content/2006/content_304942.htm",
]

for url in urls:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        content = resp.read().decode("utf-8", errors="ignore")
        # Extract text
        import re
        text = re.sub(r"<[^>]+>", "", content)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        print(f"\n=== {url} ===")
        for l in lines[:100]:
            if any(kw in l for kw in ["薪酬","报酬","股份支付","限制性","股权激励","摊销","分摊","每年"]):
                print(l[:200])
    except Exception as e:
        print(f"{url}: {e}")
