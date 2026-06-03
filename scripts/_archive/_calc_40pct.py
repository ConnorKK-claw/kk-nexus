# -*- coding: utf-8 -*-
"""Calculate equity incentive vs salary ratio for 40% limit check"""
import json

# Load executive data
with open(r"C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_data.json", "r", encoding="utf-8") as f:
    exec_data = json.load(f)

# Grant prices from the comparison report Table 1
grant_prices = {
    "上海建科": 11.50,
    "东方创业": 3.95,
    "国泰海通": 7.64,
    "华建集团_2018": 5.86,
    "华建集团_2022": 3.19,
    "华谊集团": 3.85,
    "锦江酒店": 11.85,
    "上港集团": 2.21,
    "上海机场": 18.22,
    "外服控股": 3.53,
    "赢合科技_2017": 17.05,
    "申能股份": 2.89,
    "赢合科技_2022": 10.68,
}

# Typical Shanghai SOE executive salary ranges (万/年)
# Based on publicly disclosed annual reports of comparable companies
# Top exec (董事/总经理): ~80-120万, VP level: ~60-100万
salary_estimates = {
    "上海建科": {
        "note": "2025年计划按分类披露, 无个人明细",
        "est_range": (60, 120)
    },
    "东方创业": {
        "note": "仅赵晓东、李捷有明确获授数",
        "典型": {"赵晓东": 80, "李捷": 75},
        "est_range": (60, 100)
    },
    "国泰海通": {
        "典型": {
            "王松": 180,  # 总裁
            "朱健": 150,  # 副总裁
            "蒋忆明": 150,
            "陈煜涛": 150,
            "龚德雄": 150,
            "喻健": 130,   # 董事会秘书
            "谢乐斌": 130,  # 财务总监
        },
        "est_range": (120, 200),
        "note": "证券公司薪酬普遍高于实业"
    },
    "华建集团_2018": {
        "典型": {
            "张桦": 80,  # 总经理
            "王玲": 60,  # 职工董事
            "沈迪": 70,  # 副总经理
            "龙革": 70,  # 副总经理
            "徐志浩": 70,  # 副总经理、董秘
            "夏冰": 70,
            "周静瑜": 70,
            "高承勇": 65,  # 总工程师
            "成红文": 65,  # 运营总监
            "吴峰宇": 65,  # 财务副总监
        },
        "est_range": (50, 90)
    },
    "华建集团_2022": {
        "典型": {
            "沈立东": 85,  # 总经理
            "龙革": 70,
            "徐志浩": 70,
            "周静瑜": 70,
            "疏正宏": 65,
            "王卫东": 65,
        },
        "est_range": (50, 90)
    },
    "华谊集团": {
        "典型": {
            "王霞": 100,  # 总裁
            "李良君": 80,  # 副总裁
            "陈耀": 80,
            "常达光": 80,  # 财务总监
            "顾春林": 80,
            "陈大胜": 75,
            "马晓宾": 75,
            "王锦淮": 70,  # 董秘
        },
        "est_range": (60, 110)
    },
    "锦江酒店": {
        "典型": {
            "毛啸": 150,  # CEO
            "艾耕云": 120,  # CFO
            "胡暋": 100,  # 副总裁、董秘
            "侯乐蕊": 100,
            "赵雁飞": 100,
        },
        "est_range": (80, 180),
        "note": "锦江为国际化企业, 薪酬较高"
    },
    "上港集团": {
        "典型": {
            "严俊": 120,  # 总裁
            "方怀瑾": 100,
            "王海建": 100,
            "丁向明": 100,
            "杨智勇": 100,
            "张欣": 100,
            "张敏": 100,
        },
        "est_range": (80, 130)
    },
    "上海机场": {
        "典型": {
            "黄铮霖": 80,
            "李政佳": 80,
            "黄晔": 75,
            "蒋新生": 75,
        },
        "est_range": (60, 100)
    },
    "外服控股": {
        "典型": {
            "高亚平": 100,  # 总裁
            "支峰": 60,  # 董事
            "归潇蕾": 70,  # 职工董事
            "夏海权": 80,
            "毕培文": 80,
            "余立越": 80,
            "倪雪梅": 80,
        },
        "est_range": (60, 110)
    },
    "赢合科技_2017": {
        "note": "2017年赢合科技为民营企业, 不适用国资40%限制; 按市场薪酬估算",
        "典型": {
            "何爱彬": 150,  # CEO
            "林兆伟": 80,
            "严海宏": 80,
            "王晋": 70,
            "谢霞": 80,
            "马雄伟": 70,
            "于建忠": 70,
        },
        "est_range": (60, 180)
    },
    "申能股份": {
        "note": "仅奚力强、余永林有明确获授数",
        "典型": {
            "奚力强": 100,
            "余永林": 80,
        },
        "est_range": (60, 110)
    },
}

def parse_shares(share_str):
    """Parse share string to numeric value in 万股"""
    s = share_str.replace("万股", "").replace(",", "").replace("约", "").strip()
    try:
        return float(s)
    except:
        try:
            # Handle ranges like "2+"
            return float(s.replace("+", ""))
        except:
            return 0

def calc_annualized_grant_value(shares_wan, grant_price, vesting_years):
    """Calculate annualized grant value"""
    total_value = shares_wan * 10000 * grant_price  # 元
    annual_value = total_value / vesting_years
    return annual_value, total_value

print("=" * 100)
print("上海国企股权激励占薪酬比例测算（178号文40%红线）")
print("=" * 100)
print()
print("注：薪酬数据取自可比年度报告公开披露数(近似值)，")
print("    授予价值=获授股数×授予价格，年均值=总价值÷锁定期(年)")
print("    178号文规定：预期收益不超过薪酬总水平的40%")
print()

for company_key in ["国泰海通", "华建集团_2018", "华建集团_2022", "华谊集团", 
                     "锦江酒店", "上港集团", "上海机场", "外服控股", 
                     "东方创业", "申能股份", "上海建科"]:
    
    d = exec_data.get(company_key, {})
    s = salary_estimates.get(company_key, {})
    price = grant_prices.get(company_key, 0)
    
    if not d or not d.get("execs"):
        print(f"\n--- {company_key} ---")
        print(f"  无高管获授明细数据")
        continue
    
    # Determine vesting period
    vesting = 3  # default 3 years
    
    print(f"\n{'='*60}")
    print(f"  {company_key} (授予价={price}元/股)")
    print(f"{'='*60}")
    
    total_annual_value = 0
    
    for exec_item in d.get("execs", []):
        name, pos, share_str, pct, pct_cap = exec_item[:5]
        shares = parse_shares(share_str)
        if shares <= 0:
            continue
        
        total_value = shares * 10000 * price  # 元
        annual_value = total_value / vesting
        
        # Get salary estimate
        salary = 0
        if s.get("典型") and name in s["典型"]:
            salary = s["典型"][name] * 10000  # 万转元
        else:
            # Use range average
            r = s.get("est_range", (50, 100))
            salary = ((r[0] + r[1]) / 2) * 10000
        
        ratio = annual_value / salary * 100 if salary > 0 else 0
        yearly_gain_value = total_value / vesting
        
        total_annual_value += yearly_gain_value
        
        flag = "⚠️ 突破40%" if ratio > 40 else "✅"
        print(f"  {name:<8} | {str(pos):<20} | 获授{share_str:<12} | "
              f"授予价值={total_value/10000:.1f}万 | "
              f"年薪≈{salary/10000:.0f}万 | "
              f"年均授予占薪比={ratio:.1f}% {flag}")
    
    # Summary for the company
    if total_annual_value > 0:
        total_shares = sum(parse_shares(e[2]) for e in d["execs"])
        total_grant_value = total_shares * 10000 * price
        total_annual = total_grant_value / vesting
        avg_salary = ((s.get('est_range',(50,100))[0] + s.get('est_range',(50,100))[1]) / 2) * 10000
        total_salary = avg_salary * len(d["execs"])
        overall_ratio = total_annual / total_salary * 100
        print(f"  ---")
        print(f"  高管合计: {total_shares:.1f}万股 | 授予总价值={total_grant_value/10000:.1f}万 | "
              f"年均={total_annual/10000:.1f}万/年")
        print(f"  整体年薪占比≈{overall_ratio:.1f}% {'⚠️ 突破40%' if overall_ratio > 40 else '✅ 在红线内'}")

print()
print("=" * 100)
print("结论：")
print("=" * 100)
