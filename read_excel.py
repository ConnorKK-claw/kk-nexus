import openpyxl
wb = openpyxl.load_workbook('C:\\Users\\hexk\\OneDrive\\文档\\New project 6\\参考文件.xlsx')
ws = wb['Sheet1']
print('Merged cells:', list(ws.merged_cells.ranges))
print()
for r in range(1, 16):
    row_data = []
    for c in range(1, 12):
        cell = ws.cell(row=r, column=c)
        row_data.append(repr(cell.value))
    print('|'.join(row_data))
