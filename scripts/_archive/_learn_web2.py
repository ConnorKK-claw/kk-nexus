import urllib.request, json, ssl, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = ['https://finance.sina.com.cn/stock/s/2020-09-18/doc-iivhvpwy7851379.shtml']
for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        content = resp.read().decode('utf-8','ignore')
        text = re.sub(r'<[^>]+>', '', content)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for l in lines:
            if any(kw in l for kw in ['薪酬','人均','股权激励','授予','上港','华建']):
                print(l[:300])
    except Exception as e:
        print(f'{url}: {e}')

