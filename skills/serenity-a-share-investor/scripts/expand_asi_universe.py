# -*- coding: utf-8 -*-
"""
006 Employee - Expand ASI Stock Universe
Scans all A-share stocks by name keywords AND WIND industry classification.
"""
import sys, os, csv, json, datetime, time, math, tempfile, zipfile, re, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8")

VAULT = os.path.expanduser("~/.codex/skills/serenity-a-share-investor")
RAW = os.path.join(VAULT, "vault", "raw", "agent")
TODAY = datetime.date.today().strftime("%Y-%m-%d")

# ========== Layer keyword map (keep existing) ==========
LAYER_KEYWORDS = [
    ("算力芯片(ASIC)", ["海光信息", "寒武纪", "龙芯中科"]),
    ("算力芯片(FPGA)", ["复旦微电", "安路科技"]),
    ("存储互连", ["澜起科技", "兆易创新", "北京君正", "深科技"]),
    ("半导体设备", ["中微公司", "华海清科", "拓荆科技", "北方华创", "盛美上海", "中科飞测", "万业企业", "至纯科技", "天准科技", "华峰测控", "长川科技", "芯源微", "精测电子", "华兴源创", "晶盛机电", "金海通", "联动科技", "富创精密", "新莱应材", "正帆科技", "微导纳米"]),
    ("半导体材料", ["安集科技", "鼎龙股份", "沪硅产业", "晶瑞电材", "华特气体", "江丰电子", "南大光电", "格林达", "立昂微", "金宏气体", "雅克科技", "容大感光", "上海新阳", "飞凯材料", "阿石创", "中晶科技", "三孚新科", "艾森股份", "天承科技"]),
    ("先进封测", ["长电科技", "通富微电", "华天科技", "甬矽电子", "伟测科技", "利扬芯片", "晶方科技", "气派科技", "颀中科技", "汇成股份"]),
    ("光通信", ["中际旭创", "新易盛", "天孚通信", "源杰科技", "长光华芯", "德科立", "光库科技", "光迅科技", "华工科技", "联特科技", "腾景科技", "太辰光", "仕佳光子"]),
    ("EDA/IP", ["华大九天", "芯原股份", "概伦电子", "广立微"]),
    ("服务器配套(PCB)", ["沪电股份", "深南电路", "生益科技", "胜宏科技", "景旺电子", "鹏鼎控股", "东山精密", "兴森科技", "崇达技术"]),
    ("服务器配套(电源散热)", ["欧陆通", "英维克", "高澜股份", "申菱环境"]),
    ("功率半导体", ["斯达半导", "时代电气", "士兰微", "宏微科技", "新洁能", "扬杰科技", "台基股份", "东微半导", "天岳先进"]),
]

MANUAL_CURATIONS = [
    {"layer": "半导体材料", "code": "300346", "name": "南大光电", "reason": "光刻胶/前驱体"},
    {"layer": "先进封测", "code": "002185", "name": "华天科技", "reason": "OSAT封测"},
    {"layer": "先进封测", "code": "688362", "name": "甬矽电子", "reason": "先进封装"},
    {"layer": "先进封测", "code": "688372", "name": "伟测科技", "reason": "第三方测试"},
    {"layer": "光通信", "code": "688048", "name": "长光华芯", "reason": "光芯片"},
    {"layer": "光通信", "code": "688205", "name": "德科立", "reason": "光模块上游"},
    {"layer": "功率半导体", "code": "600460", "name": "士兰微", "reason": "功率IDM"},
    {"layer": "功率半导体", "code": "688187", "name": "时代电气", "reason": "IGBT"},
    {"layer": "功率半导体", "code": "688711", "name": "宏微科技", "reason": "IGBT模块"},
    {"layer": "服务器配套(PCB)", "code": "002436", "name": "兴森科技", "reason": "FCBGA基板/PCB"},
    {"layer": "服务器配套(PCB)", "code": "601138", "name": "工业富联", "reason": "AI服务器代工"},
]

# ========== WIND layer mapping ==========
# Map WIND L2 to our ASI layer names
WIND_TO_ASI_LAYER = {
    # WIND L2 names -> ASI layer name
    "半导体": "半导体(待定)",  # sub-classified later by L3/L4
    "硬件设备": "硬件设备(待定)",
    "电气设备": "功率/电气(待定)",
}

def get_secid(code):
    if code.startswith("6"): return f"1.{code}"
    elif code.startswith("0") or code.startswith("3"): return f"0.{code}"
    return f"1.{code}"

# ========== WIND Excel reading ==========
def repair_xlsx(path):
    """Fix broken named styles in xlsx file."""
    tmp = os.path.join(tempfile.gettempdir(), "_wind_repaired.xlsx")
    with zipfile.ZipFile(path, "r") as zin:
        with zipfile.ZipFile(tmp, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "xl/styles.xml":
                    root = ET.fromstring(data)
                    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                    for cellStyles in root.findall(".//s:cellStyles", ns):
                        for cs in list(cellStyles):
                            if cs.get("name") is None:
                                cellStyles.remove(cs)
                    data = ET.tostring(root, xml_declaration=True, encoding="UTF-8")
                zout.writestr(item, data)
    return tmp

def read_wind_classification(wind_path):
    """Read WIND Excel and return dict of code -> {code, name, L1, L2, L3, L4}"""
    import pandas as pd
    import xml.etree.ElementTree as ET
    repaired = repair_xlsx(wind_path)
    df = pd.read_excel(repaired, engine="openpyxl")
    cols = list(df.columns)
    code_col, name_col = cols[0], cols[1]
    l1_col, l2_col, l3_col, l4_col = cols[2], cols[3], cols[4], cols[5]
    
    result = {}
    for _, row in df.iterrows():
        raw_code = str(row[code_col]).strip().upper()
        norm = raw_code.replace(".SZ", "").replace(".SH", "")
        result[norm] = {
            "wind_code": raw_code,
            "name": str(row[name_col]).strip(),
            "wind_l1": str(row[l1_col]).strip(),
            "wind_l2": str(row[l2_col]).strip(),
            "wind_l3": str(row[l3_col]).strip(),
            "wind_l4": str(row[l4_col]).strip(),
        }
    return result

# ========== Core functions ==========
def fetch_all_stocks():
    import akshare as ak
    print("Fetching all A-share stocks...")
    df = ak.stock_info_a_code_name()
    print(f"Got {len(df)} stocks")
    df["name"] = df["name"].str.replace(" ", "", regex=False)
    return df

def match_by_keywords(df, layer_keywords):
    results = []
    seen = {}
    for layer, keywords in layer_keywords:
        for kw in keywords:
            mask = df["name"].str.contains(kw, na=False, regex=False)
            matched = df[mask]
            for _, row in matched.iterrows():
                code = row["code"]
                name = row["name"]
                if code in seen:
                    existing = seen[code]
                    existing["layer"] = existing["layer"] + "/" + layer
                    existing["kw"] = existing["kw"] + "," + kw
                else:
                    seen[code] = {"code": code, "name": name, "layer": layer,
                        "kw": kw, "method": "name_match", "secid": get_secid(code)}
    return list(seen.values())

def add_manual_curations(results, manual_list):
    existing_codes = {r["code"] for r in results}
    for m in manual_list:
        if m["code"] in existing_codes:
            for r in results:
                if r["code"] == m["code"]:
                    r["layer"] = m["layer"]
                    r["kw"] = r.get("kw", "") + "(manual_curation)"
                    r["method"] = r["method"] + "+manual"
        else:
            results.append({"code": m["code"], "name": m["name"], "layer": m["layer"],
                "kw": m["reason"], "method": "manual", "secid": get_secid(m["code"])})
    return results

def expand_from_wind(wind_map, target_l2, min_mcap=50, exclude_keywords=None):
    """Expand candidates from WIND classification.
    target_l2: str or list of WIND L2 names to include.
    min_mcap: minimum market cap in 亿.
    exclude_keywords: exclude stocks whose name contains these keywords.
    """
    if isinstance(target_l2, str):
        target_l2 = [target_l2]
    if exclude_keywords is None:
        exclude_keywords = ["ST", "*"]
    
    candidates = []
    for code, info in wind_map.items():
        if info["wind_l2"] in target_l2:
            # Check exclude keywords
            excluded = False
            for ek in exclude_keywords:
                if ek in info["name"] or ek in code:
                    excluded = True
                    break
            if excluded:
                continue
            candidates.append({
                "code": code,
                "name": info["name"],
                "layer": f"WIND.{info['wind_l2']}",
                "kw": f"wind={info['wind_l3']}>{info['wind_l4']}",
                "method": "wind",
                "secid": get_secid(code),
                "wind_l1": info["wind_l1"],
                "wind_l2": info["wind_l2"],
                "wind_l3": info["wind_l3"],
                "wind_l4": info["wind_l4"],
            })
    print(f"  WIND {target_l2}: {len(candidates)} candidates (before mcap filter)")
    return candidates

def fetch_market_data(candidates):
    import requests
    px = {"http": "", "https": ""}
    hd = {"User-Agent": "Mozilla/5.0"}
    sh_codes = [s["code"] for s in candidates if s["secid"].startswith("1")]
    sz_codes = [s["code"] for s in candidates if s["secid"].startswith("0")]
    if not sh_codes and not sz_codes:
        return candidates
    all_q = "sh" + ",sh".join(sh_codes) if sh_codes else ""
    if sz_codes: all_q += ",sz" + ",sz".join(sz_codes)
    url = f"http://qt.gtimg.cn/q={all_q}"
    try:
        resp = requests.get(url, headers=hd, proxies=px, timeout=15)
        resp.encoding = "gbk"
        text = resp.text
    except Exception as e:
        print(f"  Market data error: {e}")
        return candidates
    market_map = {}
    for line in text.strip().split("\n"):
        if not line.strip(): continue
        try:
            start = line.find('\"')
            end = line.rfind('\"')
            if start < 0 or end <= start: continue
            parts = line[start+1:end].split("~")
            if len(parts) < 46: continue
            code = parts[2]
            price = float(parts[3]) if parts[3] else 0
            pe = float(parts[39]) if parts[39] else 0
            total_cap = float(parts[45]) if parts[45] and parts[45] != "0" else 0
            flow_cap = float(parts[44]) if parts[44] else 0
            cap = total_cap if total_cap > 0 else flow_cap
            # Tencent API returns cap in 亿 already
            market_map[code] = {"price": price, "pe_ttm": pe, "mkt_cap": cap}
        except:
            continue
    for s in candidates:
        code = s["code"]
        md = market_map.get(code, {})
        s["price"] = md.get("price", 0)
        s["pe_ttm"] = md.get("pe_ttm", 0)
        s["mkt_cap"] = md.get("mkt_cap", 0)
    return candidates

def dedup_and_rank(candidates):
    seen_codes = {}
    deduped = []
    for s in candidates:
        if s["code"] not in seen_codes:
            seen_codes[s["code"]] = True
            deduped.append(s)
    deduped.sort(key=lambda x: x.get("mkt_cap", 0), reverse=True)
    layers = {}
    for s in deduped:
        layer = s["layer"]
        layers.setdefault(layer, []).append(s)
    ranked = []
    for layer, stocks in layers.items():
        for i, s in enumerate(stocks):
            s["layer_rank"] = i + 1
            ranked.append(s)
    return ranked

def assign_asi_layer_from_wind(wind_l2, wind_l3, wind_l4, name):
    """Map WIND classification to our ASI layer system."""
    # Semiconductor products: check name for IC design type
    if wind_l2 == "半导体":
        if wind_l3 == "半导体材料与设备":
            # Check name for equipment vs material
            equip_kw = ["设备", "测试", "分选", "探针", "华创", "中微", "华海", "拓荆", "盛美", "至纯"]
            for kw in equip_kw:
                if kw in name:
                    return "半导体设备(待定)"
            return "半导体材料(待定)"
        elif wind_l3 == "半导体产品":
            # IC design companies - will classify by function later
            return "芯片设计(待定)"
    return f"WIND.{wind_l2}(待定)"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Expand ASI stock universe")
    parser.add_argument("--wind-file", help="Path to WIND classification Excel")
    parser.add_argument("--wind-layer", nargs="*", default=["半导体"], 
        help="WIND L2 layers to expand from (default: 半导体)")
    parser.add_argument("--min-mcap", type=float, default=20.0,
        help="Minimum market cap in 亿 (default: 20)")
    parser.add_argument("--output", default=None, help="Output CSV path")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"ASI Universe Expansion v2 - {TODAY}")
    print("=" * 60)
    
    all_stocks = fetch_all_stocks()
    
    # Phase 1: Name keyword matching (existing logic)
    print(f"\n[Phase 1] Keyword matching...")
    matched = match_by_keywords(all_stocks, LAYER_KEYWORDS)
    matched = add_manual_curations(matched, MANUAL_CURATIONS)
    print(f"  Name keyword + manual: {len(matched)}")
    
    # Phase 2: WIND expansion
    if args.wind_file and os.path.exists(args.wind_file):
        print(f"\n[Phase 2] WIND expansion from {args.wind_file}...")
        wind_map = read_wind_classification(args.wind_file)
        wind_results = []
        for layer_name in args.wind_layer:
            candidates = expand_from_wind(wind_map, layer_name, 
                min_mcap=args.min_mcap, exclude_keywords=["ST", "*", "退"])
            wind_results.extend(candidates)
        
        # Fetch market data for WIND candidates
        print(f"  Fetching market data for {len(wind_results)} WIND candidates...")
        wind_results = fetch_market_data(wind_results)
        
        # Filter by mcap
        before = len(wind_results)
        wind_results = [s for s in wind_results if s.get("mkt_cap", 0) >= args.min_mcap]
        print(f"  After mcap>={args.min_mcap}亿 filter: {len(wind_results)} (removed {before - len(wind_results)})")
        
        # Assign ASI layers
        for s in wind_results:
            s["asi_layer"] = assign_asi_layer_from_wind(
                s.get("wind_l2", ""), s.get("wind_l3", ""), 
                s.get("wind_l4", ""), s["name"])
        
        # Merge: existing name_matched stocks take priority
        existing_codes = {s["code"] for s in matched}
        new_from_wind = [s for s in wind_results if s["code"] not in existing_codes]
        print(f"  New from WIND: {len(new_from_wind)} (already have {len(wind_results) - len(new_from_wind)})")
        matched.extend(new_from_wind)
    
    # Final: dedup, rank, output
    print(f"\n[Phase 3] Final processing...")
    ranked = dedup_and_rank(matched)
    
    # Build output fieldnames (extensible)
    base_fields = ["code", "name", "layer", "method", "kw", "secid", "price", "pe_ttm", "mkt_cap", "layer_rank"]
    wind_fields = ["wind_l1", "wind_l2", "wind_l3", "wind_l4", "asi_layer"]
    
    csv_path = args.output or os.path.join(RAW, f"{TODAY}-asi-expanded-universe.csv")
    os.makedirs(os.path.dirname(csv_path) if os.path.dirname(csv_path) else RAW, exist_ok=True)
    
    fieldnames = base_fields + [f for f in wind_fields if any(f in s for s in ranked)]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in ranked:
            row = {fn: s.get(fn, "") for fn in fieldnames}
            writer.writerow(row)
    print(f"\nOutput: {csv_path} ({len(ranked)} stocks)")
    
    # Summary
    layers = {}
    for s in ranked:
        layers.setdefault(s["layer"], []).append(s)
    print(f"\n=== Summary: {len(ranked)} stocks, {len(layers)} layers ===")
    for layer in sorted(layers.keys()):
        stocks = layers[layer]
        tops = [f"#{s['layer_rank']} {s['name']}({s.get('mkt_cap',0):.0f}亿)" for s in stocks[:3]]
        extra = f" +{len(stocks)-3}" if len(stocks) > 3 else ""
        print(f"  [{layer}] {len(stocks)}: {', '.join(tops)}{extra}")
    
    print(f"\nDone!")

if __name__ == "__main__":
    main()

