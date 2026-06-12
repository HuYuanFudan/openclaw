#!/usr/bin/env python3
"""精确计算 P25xx 编码的全量出现频次"""
from py2neo import Graph
graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

# 拆分所有 P25xx 编码
q = """
MATCH (v:Violation)
WHERE v.`违规类型编码` IS NOT NULL
WITH v.`违规类型编码` as code
RETURN code
LIMIT 100000
"""
all_codes = []
for r in graph.run(q).data():
    code = r['code']
    # 拆分复合编码 P2503、P2599
    for c in code.replace('、', ';').split(';'):
        c = c.strip()
        if c:
            all_codes.append(c)

from collections import Counter
cnt = Counter(all_codes)
print("P25xx 全量编码统计:")
for code, c in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"  {code}: {c}")
print(f"  合计: {sum(cnt.values())}")
