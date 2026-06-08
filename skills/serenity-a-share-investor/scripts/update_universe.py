# -*- coding: utf-8 -*-
"""Universe re-classifier: uniform layers + exclusions + chip design layer"""
import sys, os, csv
sys.stdout.reconfigure(encoding='utf-8')

VAULT = os.path.join(os.path.dirname(__file__), '..')
RAW = os.path.join(VAULT, 'vault', 'raw', 'agent')
SCRIPTS = os.path.dirname(__file__)

RENAME_MAP = {
    '算力芯片(ASIC)': '算力芯片',
    '算力芯片(FPGA)': '算力芯片',
    '芯片设计(待归类)': '芯片设计',
    '服务器配套(PCB)': '服务器配套',
    '服务器配套(电源散热)': '服务器配套',
}

EXCLUDED = {'300323','300102','300303','300708','300241','002449','688378'}

# Manual layer override for specific codes
MANUAL_LAYER = {
    '688729': '半导体设备', '688785': '半导体设备', '688652': '半导体设备',
    '688605': '半导体设备', '688478': '半导体设备', '301297': '半导体设备',
    '688783': '半导体材料', '688545': '半导体材料', '688432': '半导体材料',
    '688549': '半导体材料', '688727': '半导体材料', '688233': '半导体材料',
    '688167': '光通信', '002213': '存储互连', '688662': '服务器配套',
}

# Keyword matchers for WIND stocks (same as original classify_wind_to_asi.py)
KEYWORD_MATCHERS = [
    (['中微','华海清科','拓荆','北方华创','盛美','中科飞测','万业','至纯',
      '天准','华峰测控','芯源微','精测电子','华兴源创','晶盛机电',
      '长川科技','金海通','联','富创','新莱应材','正帆科技','微导',
      '华海诚','赛腾','矽电'], '半导体设备'),
    (['安集','鼎龙','沪硅','晶瑞','华特','江丰','南大光电','格林达',
      '立昂微','金宏气体','雅克','容大感光','上海新阳','飞凯材料',
      '阿石创','中晶','三孚新科','艾森','天承','江化','德邦',
      '莱特','中船','唯特偶','康强','宝明','大方','天洋'], '半导体材料'),
    (['斯达','时代电气','士兰','宏微','新洁能','扬杰','台基',
      '东微','天岳','三安','华润微','华微','捷捷','派瑞',
      '芯导','银河','上海贝岭','晶合集成','燕东'], '功率半导体'),
    (['长电','通富','华天','甬矽','伟测','利扬','晶方','气派',
      '颀中','汇成','蓝箭'], '先进封测'),
    (['佰维','德明利','东芯','朗科','兆易','澜起','君正'], '存储互连'),
    (['光迅','中际','新易盛','天孚','源杰','长光华芯','德科立',
      '光库','华工','联特','腾景','太辰光','仕佳','铭普','东田'], '光通信'),
    (['沪电','深南','生益','胜宏','景旺','鹏鼎','东山','兴森',
      '崇达','依顿','奥士康','超声','中京','方正'], '服务器配套'),
    (['复旦微','安路'], '算力芯片'),
    (['欧陆通','英维克','高澜股份','申菱环境'], '服务器配套'),
    (['斯达半导','时代电气','宏微科技','新洁能','扬杰科技','台基股份',
      '东微半导','天岳先进'], '功率半导体'),
]

def get_secid(code):
    return f'1.{code}' if code.startswith('6') else f'0.{code}'

def keyword_classify(name):
    for kws, layer in KEYWORD_MATCHERS:
        for kw in kws:
            if kw in name:
                return layer
    return None

def main():
    files = sorted([f for f in os.listdir(RAW) if f.endswith('-asi-expanded-universe.csv')], reverse=True)
    rows = list(csv.DictReader(open(os.path.join(RAW, files[0]), 'r', encoding='utf-8')))
    print(f'Loaded {len(rows)} stocks')
    
    new_stocks = []
    excluded = []
    layer_counts = {}
    
    for r in rows:
        code = r['code']
        name = r['name']
        old_layer = r['layer']
        method = r.get('method', '')
        
        # 1. Exclusions
        if code in EXCLUDED:
            excluded.append(code)
            continue
        
        # 2. Manual override
        if code in MANUAL_LAYER:
            new_layer = MANUAL_LAYER[code]
        # 3. Direct rename (existing layers from original 94)
        elif old_layer in RENAME_MAP:
            new_layer = RENAME_MAP[old_layer]
        # 4. Existing non-WIND layer that's already correct
        elif not old_layer.startswith('WIND.'):
            new_layer = old_layer
        # 5. WIND stock: try keyword matching
        else:
            kw_layer = keyword_classify(name)
            if kw_layer:
                new_layer = kw_layer
            else:
                new_layer = '芯片设计'
        
        stock = {'code':code,'name':name,'layer':new_layer,'secid':get_secid(code)}
        for wf in ['wind_l1','wind_l2','wind_l3','wind_l4']:
            if r.get(wf):
                stock[wf] = r[wf]
        new_stocks.append(stock)
        layer_counts[new_layer] = layer_counts.get(new_layer, 0) + 1
    
    print(f'Excluded: {len(excluded)} stocks')
    print(f'\\nLayers ({len(new_stocks)} stocks):')
    for l,c in sorted(layer_counts.items(), key=lambda x:-x[1]):
        print(f'  {l}: {c}')
    
    # Generate asi_stocks.py
    lines = ['# -*- coding: utf-8 -*-', '"""ASI stock universe - 221 stocks, 12 layers"""', '', 'STOCKS = [']
    for s in new_stocks:
        d = {'code':s['code'],'name':s['name'],'layer':s['layer'],'secid':s['secid']}
        for wf in ['wind_l1','wind_l2','wind_l3','wind_l4']:
            if wf in s: d[wf] = s[wf]
        lines.append(f'    {d},')
    lines += [']', '', 'def get_layer_list():', '    layers = {}',
              '    for s in STOCKS: l = s["layer"]; layers[l] = layers.get(l,0)+1',
              '    return layers', '', 'if __name__ == "__main__":',
              '    layers = get_layer_list()',
              '    print(f"Universe: {len(STOCKS)} stocks, {len(layers)} layers")',
              '    for l,c in sorted(layers.items()): print(f"  {l}: {c}")']
    
    with open(os.path.join(SCRIPTS, 'asi_stocks.py'), 'w', encoding='utf-8') as f:
        f.write('\\n'.join(lines))
    print(f'\\nWritten: asi_stocks.py ({len(new_stocks)} stocks)')
    
    # Verify no WIND prefix remains
    wind_remain = [s for s in new_stocks if 'WIND' in s['layer'] or '(待归类)' in s['layer']]
    if wind_remain:
        print(f'WARNING: {len(wind_remain)} stocks with unclean layer names:')
        for s in wind_remain:
            print(f'  {s["code"]} {s["name"]}: {s["layer"]}')

if __name__ == '__main__':
    main()
