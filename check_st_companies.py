#!/usr/bin/env python3
from py2neo import Graph

graph = Graph('neo4j://10.176.22.62:7687', auth=('neo4j', 'neo4j6008'))

# 检查证券简称字段
result = graph.run("MATCH (c:Company) WHERE c.`证券简称` IS NOT NULL RETURN c.`证券简称` LIMIT 10").data()
print('证券简称示例:', [r['c.`证券简称`'] for r in result])

# 检查是否有ST公司（证券简称）
result2 = graph.run("MATCH (c:Company) WHERE c.`证券简称` IS NOT NULL AND (c.`证券简称` CONTAINS 'ST' OR c.`证券简称` CONTAINS '*ST') RETURN c.`证券简称` LIMIT 10").data()
print('证券简称ST公司:', [r['c.`证券简称`'] for r in result2])

# 检查股票简称字段
result3 = graph.run("MATCH (c:Company) WHERE c.`股票简称` IS NOT NULL RETURN c.`股票简称` LIMIT 10").data()
print('股票简称示例:', [r['c.`股票简称`'] for r in result3])

# 检查股票简称中是否有ST
result4 = graph.run("MATCH (c:Company) WHERE c.`股票简称` IS NOT NULL AND (c.`股票简称` CONTAINS 'ST' OR c.`股票简称` CONTAINS '*ST') RETURN c.`股票简称` LIMIT 10").data()
print('股票简称ST公司:', [r['c.`股票简称`'] for r in result4])

# 检查A股证券代码字段
result5 = graph.run("MATCH (c:Company) WHERE c.`A股证券代码` IS NOT NULL RETURN c.`A股证券代码`, c.`公司中文名称` LIMIT 10").data()
print('A股证券代码示例:', result5)
