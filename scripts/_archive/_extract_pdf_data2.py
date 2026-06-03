# -*- coding: utf-8 -*-
"""Fast extraction of executive grant allocation tables from draft PDFs"""
import pdfplumber
import os
import json

BASE = r'C:\Users\hexk\OneDrive\Desktop\股权激励\可比公司公告'
OUTPUT = r'C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_grants.json'

companies = [
    ('上海建科', '上海建科'),
    ('东方创业', '东方创业'),
    ('国泰海通', '国泰海通'),
    ('华建集团', '华建集团'),
    ('华谊集团', '华谊集团'),
    ('锦江酒店', '锦江酒店'),
    ('上港集团', '上港集团'),
    ('上海机场', '上海机场'),
    ('外服控股', '外服控股'),
    ('赢合科技', '赢合科技'),
    ('申能股份', '申能股份'),
]

def find_draft_pdf(company_dir):
    candidates = []
    for root, dirs, files in os.walk(company_dir):
        for f in files:
            if f.lower().endswith('.pdf') and '草案' in f and '摘要' not in f:
                candidates.append(os.path.join(root, f))
    candidates.sort(key=len)
    return candidates[0] if candidates else None

def extract_table(pdf_path):
    result = {'executives': [], 'categories': [], 'total': None}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:30]:
                tables = page.extract_tables()
                for table in tables:
                    # Check if this looks like an allocation table
                    header_text = ' '.join([str(c) for c in (table[0] if table else []) if c])
                    if '限制性股票数量' not in header_text and '占授予' not in header_text:
                        continue
                    for row in table[1:]:
                        cells = [str(c).replace('\n','').strip() if c else '' for c in (row or [])]
                        line = ' | '.join(cells)
                        # Skip empty/header rows
                        if not any(c for c in cells if c):
                            continue
                        if '姓名' in line or '职位' in line or '限制性' in line:
                            continue
                        result['raw_rows'].append(cells)
                        if '合计' in line:
                            result['total'] = cells
                        elif any(pos in line for pos in ['董事','总裁','副总','财务总','董秘','监事','总经']):
                            result['executives'].append(cells)
                        elif '中层' in line or '核心' in line or '骨干' in line or '其他人' in line:
                            result['categories'].append(cells)
    except Exception as e:
        result['error'] = str(e)
    return result

all_data = {}
for display_name, dir_name in companies:
    cp = os.path.join(BASE, dir_name)
    if not os.path.isdir(cp):
        print(f'{display_name}: dir not found')
        continue
    pdf = find_draft_pdf(cp)
    if not pdf:
        print(f'{display_name}: no draft PDF')
        continue
    print(f'Processing {display_name}...')
    result = extract_table(pdf)
    result['pdf_name'] = os.path.basename(pdf)
    all_data[display_name] = result
    print(f'  Found {len(result["executives"])} exec rows, {len(result["categories"])} cat rows')

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
print(f'\nDone! Saved to {OUTPUT}')
