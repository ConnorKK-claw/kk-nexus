import os, pdfplumber, requests
TMP = r"C:/Users/hexk/OneDrive/文档/New project 6/_pdf_cache"
os.makedirs(TMP, exist_ok=True)

# 案例数据: [名称, 股票代码, 授予价, 年报PDF, [姓名, 获授万股, 年薪万]...]
CASES = [
    ["上海机场", "600009", 18.22, "http://static.cninfo.com.cn/finalpage/2024-03-30/1219461720.PDF",
     [["黄铮霖",4.69,101.04],["李政佳",4.69,24.83],["黄晔",4.00,86.14],["蒋新生",4.00,0]]],
    ["申能股份", "600642", 2.89, "http://static.cninfo.com.cn/finalpage/2022-04-09/1212855228.PDF",
     [["奚力强",56.9,114.91],["余永林",51.2,106.51],["谢峰",51.2,106.51],["舒彤",45.1,106.44],["刘先军",51.2,106.51]]]
]

print("=" * 80)
print("高管授予价值/薪酬总水平 40%上限检查")
print("  E=授予价值(万元) = 获授股数*授予价/10000")
print("  S=税前年薪(万元,来自年报报酬表)")
print("  间隔期=2年")
print("=" * 80)

for c in CASES:
    print()
    print("--- " + c[0] + " (授予价:" + str(c[2]) + "元) ---")
    header = "  " + "姓名".ljust(8) + " 获授万股 授予价值 年薪(万) E/(S*2)% E/((S+E)*2)%"
    print(header)
    print("  " + "-" * 55)
    for e in c[4]:
        g = round(e[1] * 10000 * c[2] / 10000, 1)
        s = e[2]
        if s > 0:
            r1 = round(g / (s * 2) * 100, 1)
            r2 = round(g / ((s + g) * 2) * 100, 1)
        else:
            r1 = 0; r2 = 0
        line = "  " + e[0].ljust(8) + " " + str(e[1]).rjust(8) + " " + str(g).rjust(8) + " " + str(s).rjust(8)
        line += " " + str(r1).rjust(7) + "%" + " " + str(r2).rjust(10) + "%"
        print(line)
    print("  " + "-" * 55)
    print("  注: 40%上限; 蒋新生2024年上任无2023年薪数据; 李政佳4个月年薪")

print()
print("=" * 80)
print("扩展: 其他9家案例")
print("  上海建科(不含高管)、华建集团(含高管无个人明细)、东方创业/国泰君安/")
print("  华谊集团/锦江酒店/上港集团/外服控股/赢合科技(需补充高管获授明细)")
print("=" * 80)
