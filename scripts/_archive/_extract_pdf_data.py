# -*- coding: utf-8 -*-
"""Extract executive grant allocation tables from all 11 companies' draft PDFs"""
import pdfplumber
import os
import json
import re

BASE = r'C:\Users\hexk\OneDrive\Desktop\股权激励\可比公司公告'
OUTPUT = r'C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_grants.json'

companies = {
    '上海建科': '上海建科',
    '东方创业': '东方创业',
    '国泰海通': '国泰海通',
    '华建集团': '华建集团',
    '华谊集团': '华谊集团',
    '锦江酒店': '锦江酒店',
    '上港集团': '上港集团',
    '上海机场': '上海机场',
    '外服控股': '外服控股',
    '赢合科技': '赢合科技',
    '申能股份': '申能股份',
}

def find_draft_pdf(company_dir):
    """Find the main draft PDF (prefer 草案 over 摘要/修订稿)"""
    all_pdfs = []
    for root, dirs, files in os.walk(company_dir):
        for f in files:
            if f.endswith('.pdf') and '草案' in f and '摘要' not in f:
                all_pdfs.append(os.path.join(root, f))
    # Prefer shorter name (original draft) over longer (revised etc)
    all_pdfs.sort(key=len)
    return all_pdfs[0] if all_pdfs else None

def extract_allocation_table(pdf_path):
    """Extract the executive allocation table from the PDF"""
    results = {'executives': [], 'summary': None}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row and any(cell and ('获授' in str(cell) or '限制性股票数量' in str(cell) or '占授予总数' in str(cell)) for cell in row):
                            # Found allocation table
                            for r in table:
                                if not r:
                                    continue
                                cells = [str(c).strip() if c else '' for c in r]
                                # Look for name + position + shares pattern
                                join_str = ' | '.join(cells)
                                if '合计' in join_str:
                                    results['summary'] = cells
                                elif any(pos in join_str for pos in ['董事','总裁','副总','财务总','董事会秘书','监事']):
                                    # Try to find name and shares
                                    nums = re.findall(r'[\d,\.]+', join_str)
                                    name = ''
                                    for c in cells:
                                        c_clean = c.replace('\n','').strip()
                                        if c_clean and len(c_clean) <= 5 and c_clean not in name:
                                            name = c_clean
                                    results['executives'].append({
                                        'row': cells,
                                        'text': join_str
                                    })
    except Exception as e:
        print(f'  ERROR: {e}')
    return results

all_data = {}
for display_name, dir_name in companies.items():
    company_path = os.path.join(BASE, dir_name)
    if not os.path.isdir(company_path):
        print(f'{display_name}: directory not found at {company_path}')
        continue
    pdf_path = find_draft_pdf(company_path)
    if not pdf_path:
        print(f'{display_name}: no draft PDF found')
        continue
    print(f'{display_name}: {os.path.basename(pdf_path)}')
    data = extract_allocation_table(pdf_path)
    all_data[display_name] = data
    if data['executives']:
        print(f'  Found {len(data["executives"])} executive rows')
        for e in data['executives'][:5]:
            print(f'    {e["text"][:80]}')
    else:
        print(f'  No executive rows found')
    if data['summary']:
        print(f'  Summary: {" | ".join(data["summary"])[:80]}')
    print()

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
print(f'Output saved to {OUTPUT}')
