# -*- coding: utf-8 -*-
"""
WIND to ASI layer classifier.
Reads expanded universe CSV, assigns ASI layers to WIND stocks.
Outputs updated asi_stocks.py content.
"""
import sys, os, csv
sys.stdout.reconfigure(encoding="utf-8")

VAULT = os.path.expanduser("~/.codex/skills/serenity-a-share-investor")
RAW = os.path.join(VAULT, "vault", "raw", "agent")
SCRIPTS = os.path.join(VAULT, "scripts")

def read_expanded_csv():
    """Read the latest expanded universe CSV."""
    files = sorted([f for f in os.listdir(RAW) if f.endswith("-asi-expanded-universe.csv")], reverse=True)
    if not files:
        print("ERROR: No expanded universe CSV found")
        sys.exit(1)
    path = os.path.join(RAW, files[0])
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def get_secid(code):
    if code.startswith("6"): return f"1.{code}"
    elif code.startswith("0") or code.startswith("3"): return f"0.{code}"
    return f"1.{code}"

def classify_layer(name, wind_l3, wind_l4):
    """Determine ASI layer from stock name + WIND classification."""
    # Priority 1: Existing 94 ASI layer mapping (exact name match)
    # These will be preserved by name matching below
    
    # Priority 2: Equipment keywords (WIND L3=半导体材料与设备)
    equip_kw = ["中微", "华海清科", "拓荆", "北方华创", "盛美", "中科飞测", "万业", "至纯", 
                "天准", "华峰测控", "芯源微", "精测电子", "华兴源创", "晶盛机电", 
                "长川科技", "金海通", "联", "富创", "新莱应材", "正帆科技", "微导",
                "华海诚", "赛腾", "矽电", "金海通"]
    for kw in equip_kw:
        if kw in name:
            return "半导体设备"
    
    # Priority 3: Material keywords
    material_kw = ["安集", "鼎龙", "沪硅", "晶瑞", "华特", "江丰", "南大光电", "格林达",
                   "立昂微", "金宏气体", "雅克", "容大感光", "上海新阳", "飞凯材料",
                   "阿石创", "中晶", "三孚新科", "艾森", "天承", "江化", "德邦",
                   "莱特", "中船", "唯特偶", "康强", "宝明", "大方", "天洋"]
    for kw in material_kw:
        if kw in name:
            return "半导体材料"
    
    # Priority 4: Power semiconductor keywords
    power_kw = ["斯达", "时代电气", "士兰", "宏微", "新洁能", "扬杰", "台基",
                "东微", "天岳", "三安", "华润微", "华微", "捷捷", "派瑞",
                "芯导", "银河", "上海贝岭", "晶合集成", "燕东", "功率"]
    for kw in power_kw:
        if kw in name:
            return "功率半导体"
    
    # Priority 5: Packaging/Test keywords
    pkg_kw = ["长电", "通富", "华天", "甬矽", "伟测", "利扬", "晶方", "气派", 
              "颀中", "汇成", "蓝箭", "封测"]
    for kw in pkg_kw:
        if kw in name:
            return "先进封测"
    
    # Priority 6: Storage/Memory keywords
    mem_kw = ["佰维", "德明利", "东芯", "朗科", "存储", "闪存", "兆易", "澜起", "君正"]
    for kw in mem_kw:
        if kw in name:
            return "存储互连"
    
    # Priority 7: Optical communication keywords
    opt_kw = ["光迅", "中际", "新易盛", "天孚", "源杰", "长光华芯", "德科立",
              "光库", "华工", "联特", "腾景", "太辰光", "仕佳", "铭普", "东田"]
    for kw in opt_kw:
        if kw in name:
            return "光通信"
    
    # Priority 8: PCB/Server keywords
    pcb_kw = ["沪电", "深南", "生益", "胜宏", "景旺", "鹏鼎", "东山", "兴森", 
              "崇达", "依顿", "奥士康", "超声", "中京", "方正", "PCB", "CCL"]
    for kw in pcb_kw:
        if kw in name:
            return "服务器配套(PCB)"
    
    # Priority 9: FPGA keywords
    fpga_kw = ["复旦微", "安路"]
    for kw in fpga_kw:
        if kw in name:
            return "算力芯片(FPGA)"
    
    # Priority 10: WIND L3 based assignment for unclassified
    # IC Design companies go to chip design bucket
    if wind_l3 == "半导体产品" or wind_l4 == "集成电路":
        return "芯片设计(待归类)"
    
    # Everything else stays with WIND prefix
    return f"WIND.{wind_l3}" if wind_l3 else "WIND.半导体"

def main():
    rows = read_expanded_csv()
    print(f"Loaded {len(rows)} stocks from expanded universe CSV")
    
    # Build new STOCKS list
    new_stocks = []
    layer_counts = {}
    
    for r in rows:
        code = r["code"]
        name = r["name"]
        
        # Determine layer
        if r["method"] in ("name_match", "manual", "existing"):
            # Keep existing layer assignment
            layer = r["layer"]
        else:
            # WIND stock: classify by name + WIND fields
            wind_l3 = r.get("wind_l3", "")
            wind_l4 = r.get("wind_l4", "")
            layer = classify_layer(name, wind_l3, wind_l4)
        
        stock = {
            "code": code,
            "name": name,
            "layer": layer,
            "secid": get_secid(code),
        }
        # Add WIND fields if available
        for wf in ["wind_l1", "wind_l2", "wind_l3", "wind_l4"]:
            if r.get(wf):
                stock[wf] = r[wf]
        
        new_stocks.append(stock)
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
    
    # Print summary
    print(f"\nLayer distribution ({len(new_stocks)} stocks):")
    for l, c in sorted(layer_counts.items(), key=lambda x: -x[1]):
        print(f"  {l}: {c}")
    
    # Generate asi_stocks.py content
    lines = []
    lines.append('# -*- coding: utf-8 -*-')
    lines.append('"""Shared ASI stock universe - generated by classify_wind_to_asi.py"""')
    lines.append('')
    lines.append('STOCKS = [')
    
    for s in new_stocks:
        # Compact format: one line per stock
        d = {"code": s["code"], "name": s["name"], "layer": s["layer"], "secid": s["secid"]}
        for wf in ["wind_l1", "wind_l2", "wind_l3", "wind_l4"]:
            if wf in s:
                d[wf] = s[wf]
        lines.append(f"    {d},")
    
    lines.append(']')
    lines.append('')
    
    # Add helper
    lines.append('def get_layer_list():')
    lines.append('    layers = {}')
    lines.append('    for s in STOCKS:')
    lines.append('        l = s["layer"]')
    lines.append('        layers[l] = layers.get(l, 0) + 1')
    lines.append('    return layers')
    lines.append('')
    lines.append('if __name__ == "__main__":')
    lines.append('    layers = get_layer_list()')
    lines.append('    print(f"ASI Universe: {len(STOCKS)} stocks, {len(layers)} layers")')
    lines.append('    for l, c in sorted(layers.items()):')
    lines.append('        print(f"  {l}: {c}")')
    
    output = "\n".join(lines)
    
    # Write
    output_path = os.path.join(SCRIPTS, "asi_stocks.py")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\nWritten: {output_path}")
    print(f"New stocks file: {len(new_stocks)} entries")

if __name__ == "__main__":
    main()
