import sys, requests
sys.stdout.reconfigure(encoding='utf-8')
codes = ['688783','688729','688167','301297','688545','688432','688549','688785','688727','688652','688605','688233','688378','002213','688478','688662']
hd = {'User-Agent': 'Mozilla/5.0'}
px = {'http':'', 'https':''}
for code in codes:
    prefix = 'SH' if code.startswith('6') else 'SZ'
    url = f'https://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/PageAjax?code={prefix}{code}'
    try:
        r = requests.get(url, headers=hd, proxies=px, timeout=10)
        data = r.json()
        biz = data.get('MAIN_BUSINESS', '')
        print(f'{code}: {biz[:150]}')
    except Exception as e:
        print(f'{code}: ERROR {e}')
