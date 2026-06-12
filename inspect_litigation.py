#!/usr/bin/env python3
"""查看 Litigation 节点的结构和所有关联关系"""
from py2neo import Graph
graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

print("=== Litigation 节点属性 ===")
sample = list(graph.run("MATCH (l:Litigation) RETURN l LIMIT 2").data())
if sample:
    print("属性:", dict(sample[0]['l']))

print("\n=== Litigation 节点的所有关系类型 ===")
rel_types = list(graph.run("""
MATCH (l:Litigation)-[r]-() 
RETURN type(r) as rel, count(r) as cnt 
ORDER BY cnt DESC
""").data())
for r in rel_types:
    print(f"  {r['rel']}: {r['cnt']}")

print("\n=== Violation 节点属性 ===")
sample = list(graph.run("MATCH (v:Violation) RETURN v LIMIT 1").data())
if sample:
    print("属性:", dict(sample[0]['v']))

print("\n=== Violation 节点的所有关系类型 ===")
rel_types = list(graph.run("""
MATCH (v:Violation)-[r]-() 
RETURN type(r) as rel, count(r) as cnt 
ORDER BY cnt DESC
""").data())
for r in rel_types:
    print(f"  {r['rel']}: {r['cnt']}")

print("\n=== 案件类型分布(详细) ===")
case_types = list(graph.run("""
MATCH (l:Litigation)
WITH l, keys(l) as kk
RETURN kk, count(l) as cnt
""").data())
print("Litigation 节点键:", case_types[:3] if case_types else '无')

# 查看一些 Litigation 节点的具体内容
print("\n=== Litigation 样例 ===")
samples = list(graph.run("MATCH (l:Litigation) RETURN properties(l) as props LIMIT 5").data())
for s in samples:
    print(s['props'])
