#!/usr/bin/env python3
"""全面扫描图谱：所有节点 label、关系 type、每个 label 的关键属性、每种关系的两端属性"""
from py2neo import Graph
import json

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

report = {}

# 1) 所有节点 label
print("== 节点 Label ==")
labels = list(graph.run("CALL db.labels() YIELD label RETURN label").data())
report['labels'] = [l['label'] for l in labels]
print(report['labels'])

# 2) 每个 label 的样本属性
print("\n== 各 label 样本属性 ==")
label_samples = {}
for lbl in report['labels']:
    q = f"MATCH (n:`{lbl}`) RETURN n LIMIT 1"
    sample = list(graph.run(q).data())
    if sample:
        n = sample[0]['n']
        # 节点 -> dict
        keys = list(n.keys()) if hasattr(n, 'keys') else []
        label_samples[lbl] = keys
        print(f"  {lbl}: {keys[:15]}{'...' if len(keys)>15 else ''}")
report['label_samples'] = label_samples

# 3) 所有关系 type
print("\n== 关系 Type ==")
rel_types = list(graph.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType").data())
report['relationship_types'] = [r['relationshipType'] for r in rel_types]
print(report['relationship_types'])

# 4) 每种关系的样本属性
print("\n== 各关系样本属性 ==")
rel_samples = {}
for rt in report['relationship_types']:
    q = f"MATCH ()-[r:`{rt}`]->() RETURN r LIMIT 1"
    sample = list(graph.run(q).data())
    if sample:
        r = sample[0]['r']
        keys = list(r.keys()) if hasattr(r, 'keys') else []
        rel_samples[rt] = keys
        print(f"  {rt}: {keys[:15]}{'...' if len(keys)>15 else ''}")
report['rel_samples'] = rel_samples

# 5) 每种关系涉及哪些 label
print("\n== 关系两端的 label ==")
rel_endpoints = {}
for rt in report['relationship_types']:
    q = f"MATCH (a)-[r:`{rt}`]->(b) RETURN DISTINCT labels(a) as a, labels(b) as b LIMIT 5"
    eps = list(graph.run(q).data())
    if eps:
        # 合并所有可能
        all_a = set()
        all_b = set()
        for e in eps:
            for x in e['a']: all_a.add(x)
            for x in e['b']: all_b.add(x)
        rel_endpoints[rt] = {'from': sorted(all_a), 'to': sorted(all_b)}
        print(f"  {rt}: {sorted(all_a)} -> {sorted(all_b)}")
report['rel_endpoints'] = rel_endpoints

# 6) 每个 label 节点数量
print("\n== Label 计数 ==")
label_count = {}
for lbl in report['labels']:
    q = f"MATCH (n:`{lbl}`) RETURN count(n) as c"
    res = list(graph.run(q).data())
    if res:
        label_count[lbl] = res[0]['c']
        print(f"  {lbl}: {res[0]['c']}")
report['label_count'] = label_count

# 7) 每种关系计数
print("\n== 关系计数 ==")
rel_count = {}
for rt in report['relationship_types']:
    q = f"MATCH ()-[r:`{rt}`]->() RETURN count(r) as c"
    res = list(graph.run(q).data())
    if res:
        rel_count[rt] = res[0]['c']
        print(f"  {rt}: {res[0]['c']}")
report['rel_count'] = rel_count

with open('/home/huyuan/openclaw/kg_universal_scan.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("\n保存到 kg_universal_scan.json")
