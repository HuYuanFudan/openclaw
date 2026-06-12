#!/usr/bin/env python3
"""更多细粒度 - 实际控制人类型/资本背景/省份/地区/违规类型/币种 分布"""
from py2neo import Graph
import json

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

# 1) P25xx 编码对应 违规类型
print("[1] P25xx 编码 → 违规类型映射...")
code_to_vt = {}
for code in ['P2501', 'P2502', 'P2503', 'P2504', 'P2505', 'P2506', 'P2509', 'P2510', 'P2511', 'P2512', 'P2513', 'P2514', 'P2515', 'P2524', 'P2599']:
    q = f"""
    MATCH (v:Violation)
    WHERE v.`违规类型编码` = '{code}'
    WITH v.`违规类型` as vt, count(*) as c
    ORDER BY c DESC LIMIT 1
    RETURN vt, c
    """
    res = list(graph.run(q).data())
    if res:
        code_to_vt[code] = (res[0]['vt'], res[0]['c'])
        print(f"  {code}: {res[0]['vt'][:50]} ({res[0]['c']})")

# 2) 实际控制人类型
print("\n[2] 实际控制人类型分布...")
q = """
MATCH (c:Company)
WHERE c.`实际控制人类型[截止日期]最新` IS NOT NULL
WITH c.`实际控制人类型[截止日期]最新` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 10
"""
for r in graph.run(q).data():
    print(f"  {r['t']}: {r['c']}")

# 3) 资本背景 Company
print("\n[3] Company 资本背景分布...")
q = """
MATCH (c:Company)
WHERE c.`资本背景` IS NOT NULL
WITH c.`资本背景` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 10
"""
for r in graph.run(q).data():
    print(f"  {r['t']}: {r['c']}")

# 4) Company 行业（二级） TOP
print("\n[4] Company 行业（二级）分布...")
q = """
MATCH (c:Company)
WHERE c.`行业（二级）` IS NOT NULL
WITH c.`行业（二级）` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 15
"""
for r in graph.run(q).data():
    print(f"  {r['t']}: {r['c']}")

# 5) Company 省份分布
print("\n[5] Company 省份分布...")
q = """
MATCH (c:Company)
WHERE c.`省份` IS NOT NULL
WITH c.`省份` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 15
"""
for r in graph.run(q).data():
    print(f"  {r['t']}: {r['c']}")

# 6) Violation 类型 + 处罚金额 区间分布
print("\n[6] Violation 处罚金额区间分布...")
q = """
MATCH (v:Violation)
WHERE v.`处罚金额-上市公司` IS NOT NULL AND v.`处罚金额-上市公司` <> ''
WITH v.`处罚金额-上市公司` as amt
WITH amt, toFloat(amt) as a
WHERE a > 0
WITH
  CASE
    WHEN a < 100000 THEN '<10万'
    WHEN a < 1000000 THEN '10-100万'
    WHEN a < 10000000 THEN '100-1000万'
    WHEN a < 100000000 THEN '1000万-1亿'
    ELSE '>1亿'
  END as bucket, count(*) as c
RETURN bucket, c
ORDER BY c DESC
"""
for r in graph.run(q).data():
    print(f"  {r['bucket']}: {r['c']}")

# 7) Violation 公告发布机构
print("\n[7] Violation 公告发布机构分布...")
q = """
MATCH (v:Violation)
WHERE v.`公告发布机构` IS NOT NULL AND v.`公告发布机构` <> ''
WITH v.`公告发布机构` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 10
"""
for r in graph.run(q).data():
    print(f"  {r['t']}: {r['c']}")

# 8) Violation 处分措施
print("\n[8] Violation 处分措施分布...")
q = """
MATCH (v:Violation)
WHERE v.`处分措施` IS NOT NULL AND v.`处分措施` <> ''
WITH v.`处分措施` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 10
"""
for r in graph.run(q).data():
    print(f"  {r['t'][:50]}: {r['c']}")

# 9) Violation 处罚方式
print("\n[9] Violation 处罚方式分布...")
q = """
MATCH (v:Violation)
WHERE v.`处罚方式-上市公司` IS NOT NULL AND v.`处罚方式-上市公司` <> ''
WITH v.`处罚方式-上市公司` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 10
"""
for r in graph.run(q).data():
    print(f"  {r['t']}: {r['c']}")

# 10) 子公司持股比例 区间
print("\n[10] 子公司直接持股比例区间...")
q = """
MATCH ()-[r:子公司]->()
WHERE r.`直接持股_百分比` IS NOT NULL AND r.`直接持股_百分比` <> ''
WITH toFloat(r.`直接持股_百分比`) as pct
WITH
  CASE
    WHEN pct = 100 THEN '100%(全资)'
    WHEN pct >= 50 THEN '50-99%(控股)'
    WHEN pct > 0 THEN '1-49%(参股)'
    WHEN pct = 0 THEN '0%'
    ELSE '未知'
  END as bucket, count(*) as c
RETURN bucket, c
ORDER BY c DESC
"""
for r in graph.run(q).data():
    print(f"  {r['bucket']}: {r['c']}")

# 11) Litigation 币种
print("\n[11] Litigation 币种分布...")
q = """
MATCH (l:Litigation)
WHERE l.`币种` IS NOT NULL
WITH l.`币种` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 8
"""
for r in graph.run(q).data():
    print(f"  {r['t']}: {r['c']}")

# 12) Litigation 涉案金额 区间
print("\n[12] Litigation 涉案金额区间分布...")
q = """
MATCH (l:Litigation)
WHERE l.`涉案金额` IS NOT NULL
WITH l.`涉案金额` as amt
WITH amt, toFloat(amt) as a
WHERE a > 0
WITH
  CASE
    WHEN a < 100 THEN '<100万'
    WHEN a < 1000 THEN '100-1000万'
    WHEN a < 10000 THEN '1000万-1亿'
    ELSE '>1亿'
  END as bucket, count(*) as c
RETURN bucket, c
ORDER BY c DESC
"""
for r in graph.run(q).data():
    print(f"  {r['bucket']}: {r['c']}")

# 13) PLEDGE 用途码
print("\n[13] PLEDGE 用途 PurposeCode 分布...")
q = """
MATCH ()-[r:PLEDGE]->()
WHERE r.`PurposeCode` IS NOT NULL AND r.`PurposeCode` <> ''
WITH r.`PurposeCode` as t, count(*) as c
RETURN t, c
ORDER BY c DESC LIMIT 8
"""
for r in graph.run(q).data():
    print(f"  {r['t']}: {r['c']}")

# 14) A_security 风险警示 TOP 行业
print("\n[14] 风险警示公司行业分布...")
q = """
MATCH (a:A_security)
WHERE a.`是否属于风险警示板[交易日期]最新` = '是'
MATCH (c:Company)-[:`A股证券_公司资料`]->(a)
WHERE c.`行业（二级）` IS NOT NULL
WITH c.`行业（二级）` as ind, count(*) as c
RETURN ind, c
ORDER BY c DESC LIMIT 8
"""
for r in graph.run(q).data():
    print(f"  {r['ind']}: {r['c']}")
