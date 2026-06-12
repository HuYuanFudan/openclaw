#!/usr/bin/env python3
"""深度挖掘 - 抽取所有未探索的金融风险相关字段细分"""
from py2neo import Graph
import json

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

# 1) Litigation 节点的"事件类型/审理机构/币种/损益影响/司法类型" - 都是代码
print("[1] Litigation 详细属性 - 之前没分析的...")
for field in ['审理机构', '币种', '公司ID', '证券ID', '公告类型', '应诉(被申请)方与上市公司关系编码', '执行状态编码']:
    q = f"""
    MATCH (l:Litigation)
    WHERE l.`{field}` IS NOT NULL
    RETURN l.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 6
    """
    res = list(graph.run(q).data())
    print(f"  {field}: {[(r['v'], r['c']) for r in res[:4]]}")

# 2) Violation 节点的"违规行为/违反法规/公告发布机构/处分措施"
print("\n[2] Violation 节点详细属性...")
for field in ['处分措施', '违规行为', '违反的法律法规', '公告发布机构', '上市公司是否违规', '处罚金额-上市公司', '处罚方式-上市公司', '违规年度']:
    q = f"""
    MATCH (v:Violation)
    WHERE v.`{field}` IS NOT NULL AND v.`{field}` <> ''
    RETURN v.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 5
    """
    res = list(graph.run(q).data())
    if res:
        print(f"  {field}: {[(r['v'][:60], r['c']) for r in res[:3]]}")

# 3) PLEDGE 边上的其他字段
print("\n[3] PLEDGE 边全部字段细分...")
for field in ['RelateToPledge', 'Pledgee', 'Pledgor', 'ShortName', 'Symbol', 'PledgeName', 'LoanAmount']:
    q = f"""
    MATCH ()-[r:PLEDGE]->()
    WHERE r.`{field}` IS NOT NULL AND r.`{field}` <> ''
    RETURN r.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 5
    """
    res = list(graph.run(q).data())
    if res:
        print(f"  {field}: {[(str(r['v'])[:60], r['c']) for r in res[:3]]}")

# 4) GUARANTEES 边上的其他字段
print("\n[4] GUARANTEES 边全部字段细分...")
for field in ['Symbol', 'ActualGuaranteeAmount', 'LoanAmount', 'MarketValue', 'TermDescription', 'StartDate', 'SignDate']:
    q = f"""
    MATCH ()-[r:GUARANTEES]->()
    WHERE r.`{field}` IS NOT NULL AND r.`{field}` <> ''
    RETURN r.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 4
    """
    res = list(graph.run(q).data())
    if res:
        print(f"  {field}: {[(str(r['v'])[:60], r['c']) for r in res[:2]]}")

# 5) 客户/供应商 边上的"资本背景"、"行业（二级）"、"地区"
print("\n[5] 客户/供应商 边 - 资本背景/行业/地区...")
for rel in ['客户', '供应商']:
    for field in ['资本背景', '行业（二级）', '地区']:
        q = f"""
        MATCH ()-[r:`{rel}`]->()
        WHERE r.`{field}` IS NOT NULL AND r.`{field}` <> ''
        RETURN r.`{field}` as v, count(*) as c
        ORDER BY c DESC LIMIT 6
        """
        res = list(graph.run(q).data())
        if res:
            print(f"  {rel}.{field}: {[(r['v'][:40], r['c']) for r in res[:4]]}")

# 6) 子公司 边上的"直接持股_百分比" 分布
print("\n[6] 子公司 持股比例分布...")
q = """
MATCH ()-[r:子公司]->()
WHERE r.`直接持股_百分比` IS NOT NULL AND r.`直接持股_百分比` <> ''
WITH r.`直接持股_百分比` as pct, count(*) as c
RETURN pct, c
ORDER BY c DESC LIMIT 8
"""
for r in graph.run(q).data():
    print(f"  {r['pct']}: {r['c']}")

# 7) Violation 节点的"违规类型编码" 全部 vs 之前只看 top20
print("\n[7] Violation 编码完整（可能编码对应的是违规类型）...")
# 取出 P25 编码开头的归类
q = """
MATCH (v:Violation)
WHERE v.`违规类型编码` IS NOT NULL
WITH v.`违规类型编码` as code, count(*) as c
RETURN code, c
ORDER BY c DESC
"""
# 抽取 P25 开头编码
code_count = {}
for r in graph.run(q).data():
    code = r['code']
    # 拆分复合编码
    for c in code.replace('、', ';').split(';'):
        c = c.strip()
        if c:
            code_count[c] = code_count.get(c, 0) + r['c']
code_sorted = sorted(code_count.items(), key=lambda x: -x[1])[:15]
print("  P25xx 编码分类:")
for c, n in code_sorted:
    print(f"    {c}: {n}")

# 8) Company 节点上的所有属性
print("\n[8] Company 节点属性 keys...")
q = "MATCH (c:Company) RETURN c LIMIT 1"
res = list(graph.run(q).data())
if res:
    n = res[0]['c']
    print("  Keys:", list(n.keys())[:20])

# 9) A_security/G_security 节点上的"是否风险警示" 等
print("\n[9] A_security 风险警示...")
q = """
MATCH (a:A_security)
WHERE a.`是否属于风险警示板[交易日期]最新` IS NOT NULL
RETURN a.`是否属于风险警示板[交易日期]最新` as v, count(*) as c
ORDER BY c DESC LIMIT 5
"""
for r in graph.run(q).data():
    print(f"  {r['v']}: {r['c']}")

# 10) A_security 上的"是否ST" 类字段
print("\n[10] A_security 是否特别处理...")
for field in ['是否ST', '是否*ST', '是否暂停上市', '所属市场', '上市板']:
    q = f"""
    MATCH (a:A_security)
    WHERE a.`{field}` IS NOT NULL
    RETURN a.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 5
    """
    res = list(graph.run(q).data())
    if res:
        print(f"  {field}: {[(r['v'], r['c']) for r in res[:3]]}")

# 11) 违规类型 (P25xx 编码) 映射
print("\n[11] 尝试通过 违规类型 字段对应到 P25xx 编码...")
q = """
MATCH (v:Violation)
WHERE v.`违规类型` IS NOT NULL AND v.`违规类型编码` IS NOT NULL
WITH v.`违规类型` as vt, v.`违规类型编码` as vc
WHERE vc = 'P2599'
RETURN vt, count(*) as c
ORDER BY c DESC LIMIT 10
"""
for r in graph.run(q).data():
    print(f"  {r['vt']}: {r['c']}")
