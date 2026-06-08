import sys, requests, re
sys.stdout.reconfigure(encoding='utf-8')
codes = ['688783','688729','688167','301297','688545','688432','688549','688785','688727','688652','688605','688233','688378','002213','688478','688662']
hd = {'User-Agent': 'Mozilla/5.0'}
px = {'http':'', 'https':''}

# Try Eastmoney stock page to get industry
for code in codes:
    prefix = '1.' if code.startswith('6') else '0.'
    url = f'http://push2.eastmoney.com/api/qt/stock/get?secid={prefix}{code}&fields=f57,f58,f127,f140,f100'
    try:
        r = requests.get(url, headers=hd, proxies=px, timeout=10)
        d = r.json()
        data = d.get('data', {})
        # f57=code, f58=name, f127=industry, f140=biz
        name = data.get('f58', '')
        industry = data.get('f127', '')
        biz = data.get('f100', '')
        if biz:
            print(f'{code} {name}: {industry} | {str(biz)[:150]}')
        else:
            print(f'{code} {name}: {industry}')
    except Exception as e:
        print(f'{code}: ERROR {e}')
