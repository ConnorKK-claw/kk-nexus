# -*- coding: utf-8 -*-
import pdfplumber
import os

base = r'C:\Users\hexk\OneDrive\Desktop\股权激励\可比公司公告\华谊集团'
pdf_name = '华谊集团：A股限制性股票激励计划（草案）.pdf'
pdf_path = os.path.join(base, pdf_name)

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if tables:
            for j, table in enumerate(tables):
                for row in table:
                    if row and any(cell and ('获授' in str(cell) or '董事' in str(cell) or '高管' in str(cell) or '监事' in str(cell)) for cell in row):
                        print(f'=== Page {i+1}, Table {j+1} ===')
                        for r in table:
                            print(r)
                        print()
