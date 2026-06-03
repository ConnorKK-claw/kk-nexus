# -*- coding: utf-8 -*-
import pdfplumber, os, json

BASE = r'C:\Users\hexk\OneDrive\Desktop\股权激励\可比公司公告'
OUTPUT = r'C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_grants.json'

companies = [
    ('上海建科','上海建科'),('东方创业','东方创业'),('国泰海通','国泰海通'),
    ('华建集团','华建集团'),('华谊集团','华谊集团'),('锦江酒店','锦江酒店'),
    ('上港集团','上港集团'),('上海机场','上海机场'),('外服控股','外服控股'),
    ('赢合科技','赢合科技'),('申能股份','申能股份'),
]

def find_pdf(cd):
    cands = []
    for r,d,files in os.walk(cd):
        for f in files:
            if f.lower().endswith('.pdf') and '草案' in f and '摘要' not in f:
                cands.append(os.path.join(r,f))
    cands.sort(key=len)
    return cands[0] if cands else None

all_data = {}
for dname, dr in companies:
    cp = os.path.join(BASE, dr)
    if not os.path.isdir(cp):
        print(f'{dname}: no dir'); continue
    pdf = find_pdf(cp)
    if not pdf:
        print(f'{dname}: no pdf'); continue
    print(f'{dname}: {os.path.basename(pdf)[:40]}...')
    res = {'execs':[],'cats':[],'total':None,'pdf':os.path.basename(pdf)}
    try:
        with pdfplumber.open(pdf) as pp:
            for pg in pp.pages[:25]:
                text = pg.extract_text() or ''
                if '限制性股票数量' not in text and '占授予' not in text:
                    continue
                for tbl in (pg.extract_tables() or []):
                    if not tbl: continue
                    h = ' '.join(str(c or '') for c in tbl[0])
                    if '限制性股票数量' not in h and '占授予' not in h:
                        continue
                    for row in tbl[1:]:
                        cells = [str(c or '').replace('\n','').strip() for c in row]
                        line = ' | '.join(cells)
                        if not any(cells): continue
                        if '姓名' in line or '职位' in line: continue
                        if '合计' in line: res['total']=cells
                        elif any(p in line for p in ['董事','总裁','副总','财务总','董秘','监事','总经','书记']):
                            res['execs'].append(cells)
                        elif any(p in line for p in ['中层','核心','骨干','其他员','管理技术']):
                            res['cats'].append(cells)
    except Exception as e:
        res['error']=str(e)
    all_data[dname]=res
    print(f'  execs={len(res["execs"])}, cats={len(res["cats"])}')

with open(OUTPUT,'w',encoding='utf-8') as f:
    json.dump(all_data,f,ensure_ascii=False,indent=2)
print(f'\nSaved to {OUTPUT}')
