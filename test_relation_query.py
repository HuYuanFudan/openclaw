#!/usr/bin/env python3
"""测试关系查询功能：查找担保和诉讼仲裁关系的真实案例"""
from py2neo import Graph

# 连接Neo4j数据库
graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

print("=" * 60)
print("测试1：查询担保关系（GUARANTEES）案例")
print("=" * 60)

# 查询担保关系的示例
guarantee_query = """
    MATCH (c1:Company)-[r:GUARANTEES]->(c2:Company)
    RETURN c1.`公司中文名称` as company1, c2.`公司中文名称` as company2, 
           type(r) as relation_type, r.GuaranteeAmount as amount, r.SignDate as date
    LIMIT 10
"""
guarantee_results = graph.run(guarantee_query).data()

if guarantee_results:
    print(f"找到 {len(guarantee_results)} 条担保关系：")
    for i, row in enumerate(guarantee_results, 1):
        print(f"\n案例 {i}:")
        print(f"  公司1: {row['company1']}")
        print(f"  公司2: {row['company2']}")
        print(f"  关系类型: {row['relation_type']}")
        print(f"  担保金额: {row['amount']}")
        print(f"  签约日期: {row['date']}")
else:
    print("未找到担保关系")

print("\n" + "=" * 60)
print("测试2：查询诉讼仲裁关系案例")
print("=" * 60)

# 查询诉讼仲裁关系的示例
lawsuit_query = """
    MATCH (c1:Company)-[r:`诉讼仲裁`]->(c2:Company)
    RETURN c1.`公司中文名称` as company1, c2.`公司中文名称` as company2, 
           type(r) as relation_type
    LIMIT 10
"""
lawsuit_results = graph.run(lawsuit_query).data()

if lawsuit_results:
    print(f"找到 {len(lawsuit_results)} 条诉讼仲裁关系：")
    for i, row in enumerate(lawsuit_results, 1):
        print(f"\n案例 {i}:")
        print(f"  公司1: {row['company1']}")
        print(f"  公司2: {row['company2']}")
        print(f"  关系类型: {row['relation_type']}")
else:
    print("未找到诉讼仲裁关系")

print("\n" + "=" * 60)
print("测试3：查询质押关系（PLEDGE）案例")
print("=" * 60)

# 查询质押关系的示例
pledge_query = """
    MATCH (c1:Company)-[r:PLEDGE]->(c2:Company)
    RETURN c1.`公司中文名称` as company1, c2.`公司中文名称` as company2, 
           type(r) as relation_type, r.Amount as amount, r.StartDate as date
    LIMIT 10
"""
pledge_results = graph.run(pledge_query).data()

if pledge_results:
    print(f"找到 {len(pledge_results)} 条质押关系：")
    for i, row in enumerate(pledge_results, 1):
        print(f"\n案例 {i}:")
        print(f"  公司1: {row['company1']}")
        print(f"  公司2: {row['company2']}")
        print(f"  关系类型: {row['relation_type']}")
        print(f"  金额: {row['amount']}")
        print(f"  开始日期: {row['date']}")
else:
    print("未找到质押关系")

print("\n" + "=" * 60)
print("测试4：查询所有关系类型及其数量")
print("=" * 60)

# 查询所有关系类型
rel_types_query = """
    MATCH ()-[r]->()
    RETURN type(r) as relType, count(*) as cnt
    ORDER BY cnt DESC
"""
rel_types_results = graph.run(rel_types_query).data()

print("关系类型分布：")
for row in rel_types_results:
    print(f"  {row['relType']}: {row['cnt']} 条")

print("\n" + "=" * 60)
print("测试5：测试公司名称模糊匹配")
print("=" * 60)

# 测试模糊匹配（使用之前用户提到的公司名称）
test_companies = [
    "江西正邦科技股份有限公司",
    "江西正邦养殖有限公司",
    "正邦",
]

for company_name in test_companies:
    match_query = f"""
        MATCH (n:Company)
        WHERE n.`公司中文名称` CONTAINS '{company_name}' 
           OR n.`公司曾用名` CONTAINS '{company_name}'
        RETURN n.`公司中文名称` as name, n.`社会信用代码` as credit
        LIMIT 5
    """
    results = graph.run(match_query).data()
    print(f"\n搜索 '{company_name}' 的结果：")
    if results:
        for row in results:
            print(f"  - {row['name']} ({row['credit']})")
    else:
        print(f"  未找到匹配的公司")
