import urllib.request, json, ssl, re, sys
sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://www.gov.cn/gongbao/content/2006/content_304942.htm",  # 175号文
    "https://baike.baidu.com/item/国有控股上市公司（境内）实施股权激励试行办法",
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        content = resp.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", "", content)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        print(f"\n=== {url} ===")
        for l in lines[:200]:
            if any(kw in l for kw in ["授予价值","薪酬","报酬","股份支付","限制性","股权激励","摊销","40%","30%","总水平","人均","激励对象"]):
                print(l[:300])
    except Exception as e:
        print(f"{url}: {e}")
