#!/usr/bin/env python3
"""深度挖掘每个节点/关系的具体金融风险字段"""
from py2neo import Graph
import json

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

# MetaKnowledge 完整属性
print("== MetaKnowledge 完整属性 ==")
q = "MATCH (n:MetaKnowledge) RETURN n LIMIT 1"
res = list(graph.run(q).data())
if res:
    n = res[0]['n']
    print("Keys:", list(n.keys()))
    for k, v in n.items():
        if k != 'embedding':
            print(f"  {k}: {str(v)[:200]}")

# Company 关键属性
print("\n== Company 关键属性 ==")
q = "MATCH (n:Company) RETURN n LIMIT 1"
res = list(graph.run(q).data())
if res:
    n = res[0]['n']
    print("Keys:", list(n.keys()))

# GUARANTEES 完整属性
print("\n== GUARANTEES 完整属性 ==")
q = "MATCH ()-[r:GUARANTEES]->() RETURN r LIMIT 1"
res = list(graph.run(q).data())
if res:
    r = res[0]['r']
    print("Keys:", list(r.keys()))
    for k, v in r.items():
        print(f"  {k}: {str(v)[:120]}")

# PLEDGE 完整属性
print("\n== PLEDGE 完整属性 ==")
q = "MATCH ()-[r:PLEDGE]->() RETURN r LIMIT 1"
res = list(graph.run(q).data())
if res:
    r = res[0]['r']
    print("Keys:", list(r.keys()))
    for k, v in r.items():
        print(f"  {k}: {str(v)[:120]}")

# 客户 完整属性
print("\n== 客户 完整属性 ==")
q = "MATCH ()-[r:客户]->() RETURN r LIMIT 1"
res = list(graph.run(q).data())
if res:
    r = res[0]['r']
    print("Keys:", list(r.keys()))

# 供应商 完整属性
print("\n== 供应商 完整属性 ==")
q = "MATCH ()-[r:供应商]->() RETURN r LIMIT 1"
res = list(graph.run(q).data())
if res:
    r = res[0]['r']
    print("Keys:", list(r.keys()))

# Violation 完整属性
print("\n== Violation 完整属性 ==")
q = "MATCH (n:Violation) RETURN n LIMIT 1"
res = list(graph.run(q).data())
if res:
    n = res[0]['n']
    print("Keys:", list(n.keys()))
    for k, v in n.items():
        print(f"  {k}: {str(v)[:120]}")

# Litigation 完整属性
print("\n== Litigation 完整属性 ==")
q = "MATCH (n:Litigation) RETURN n LIMIT 1"
res = list(graph.run(q).data())
if res:
    n = res[0]['n']
    print("Keys:", list(n.keys()))

# 子公司 完整属性
print("\n== 子公司 完整属性 ==")
q = "MATCH ()-[r:子公司]->() RETURN r LIMIT 1"
res = list(graph.run(q).data())
if res:
    r = res[0]['r']
    print("Keys:", list(r.keys()))

# MetaKnowledge 所有节点的核心结论
print("\n== MetaKnowledge 节点核心结论样本 ==")
q = "MATCH (n:MetaKnowledge) RETURN n.id as id, n.core_conclusion as cc, n.risk_guidance as rg, n.related_event as re LIMIT 5"
for r in graph.run(q).data():
    print(f"  ID: {r.get('id')}")
    print(f"    结论: {str(r.get('cc'))[:200]}")
    print(f"    风险: {str(r.get('rg'))[:200]}")
    print(f"    事件: {str(r.get('re'))[:200]}")

# 客户关系上的"企业规模" / "经营状态" / "资质标签" 等
print("\n== 客户关系上的关键属性分布 ==")
q = """
MATCH ()-[r:客户]->()
WHERE r.`企业规模` IS NOT NULL
RETURN r.`企业规模` as scale, count(*) as c
ORDER BY c DESC LIMIT 10
"""
for r in graph.run(q).data():
    print(f"  {r.get('scale')}: {r.get('c')}")

# 客户经营状态
print("\n== 客户经营状态分布 ==")
q = """
MATCH ()-[r:客户]->()
WHERE r.`经营状态` IS NOT NULL
RETURN r.`经营状态` as status, count(*) as c
ORDER BY c DESC LIMIT 10
"""
for r in graph.run(q).data():
    print(f"  {r.get('status')}: {r.get('c')}")
