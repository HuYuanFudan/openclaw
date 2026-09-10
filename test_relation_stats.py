#!/usr/bin/env python3
"""
测试脚本：统计7474端口Neo4j中的关系数量和种类，设计测试用例
"""
from py2neo import Graph

def get_graph_connection():
    """尝试连接不同端口的Neo4j"""
    connections = [
        ("neo4j://10.176.22.62:7687", "neo4j", "neo4j6008"),
        ("bolt://10.176.22.62:7687", "neo4j", "neo4j6008"),
        ("http://10.176.22.62:7474", "neo4j", "neo4j6008"),
        ("http://localhost:7474", "neo4j", "neo4j"),
        ("bolt://localhost:7687", "neo4j", "neo4j"),
    ]
    
    for uri, user, password in connections:
        try:
            print(f"尝试连接: {uri}")
            graph = Graph(uri, auth=(user, password))
            # 测试连接
            graph.run("RETURN 1").data()
            print(f"成功连接: {uri}")
            return graph, uri
        except Exception as e:
            print(f"连接失败: {uri}, 错误: {str(e)[:50]}")
    
    print("无法连接到任何Neo4j数据库")
    return None, None

def analyze_graph(graph):
    """分析图谱结构"""
    print("\n" + "=" * 70)
    print("1. 节点统计")
    print("=" * 70)
    
    # 总节点数
    total_nodes = graph.run("MATCH (n) RETURN count(n) AS c").data()[0]["c"]
    print(f"总节点数: {total_nodes}")
    
    # 节点标签分布
    label_rows = graph.run("""
        MATCH (n)
        UNWIND labels(n) AS label
        RETURN label, count(*) AS cnt
        ORDER BY cnt DESC
    """).data()
    print("\n节点标签分布:")
    for row in label_rows:
        print(f"  {row['label']}: {row['cnt']}")
    
    print("\n" + "=" * 70)
    print("2. 关系统计")
    print("=" * 70)
    
    # 总关系数
    total_rels = graph.run("MATCH ()-[r]->() RETURN count(r) AS c").data()[0]["c"]
    print(f"总关系数: {total_rels}")
    
    # 关系类型分布
    rel_rows = graph.run("""
        MATCH ()-[r]->()
        RETURN type(r) AS relType, count(*) AS cnt
        ORDER BY cnt DESC
    """).data()
    
    print("\n关系类型分布:")
    rel_types = []
    for row in rel_rows:
        rel_types.append(row['relType'])
        print(f"  {row['relType']}: {row['cnt']}")
    
    return rel_types

def find_test_cases(graph, rel_types):
    """为每种关系类型找到测试案例"""
    print("\n" + "=" * 70)
    print("3. 各关系类型测试案例")
    print("=" * 70)
    
    test_cases = {}
    
    for rel_type in rel_types:
        # 查询该关系类型的示例
        # 处理中文关系类型需要反引号
        rel_pattern = f"`{rel_type}`" if any('\u4e00' <= c <= '\u9fff' for c in rel_type) else rel_type
        
        query = f"""
            MATCH (c1:Company)-[r:{rel_pattern}]->(c2:Company)
            RETURN c1.`公司中文名称` as company1, c2.`公司中文名称` as company2, type(r) as rel_type
            LIMIT 3
        """
        
        try:
            results = graph.run(query).data()
            if results:
                print(f"\n关系类型: {rel_type}")
                test_cases[rel_type] = []
                for i, row in enumerate(results, 1):
                    print(f"  案例 {i}: {row['company1']} -> {row['company2']}")
                    test_cases[rel_type].append({
                        'company1': row['company1'],
                        'company2': row['company2'],
                        'relation_type': row['rel_type']
                    })
            else:
                print(f"\n关系类型: {rel_type} - 无Company节点之间的关系")
        except Exception as e:
            print(f"\n关系类型: {rel_type} - 查询失败: {str(e)}")
    
    return test_cases

def generate_test_report(test_cases):
    """生成测试报告"""
    print("\n" + "=" * 70)
    print("4. 测试用例汇总")
    print("=" * 70)
    
    report = {
        'total_test_cases': 0,
        'cases': []
    }
    
    for rel_type, cases in test_cases.items():
        for case in cases:
            report['total_test_cases'] += 1
            report['cases'].append({
                'test_id': f"TC_{len(report['cases']):03d}",
                'relation_type': rel_type,
                'company1': case['company1'],
                'company2': case['company2'],
                'expected_result': f"应返回{rel_type}关系",
                'test_type': 'positive'
            })
    
    # 添加一些负向测试用例
    print("\n正向测试用例:")
    for case in report['cases']:
        print(f"  {case['test_id']}: {case['company1']} <-> {case['company2']} [{case['relation_type']}]")
    
    # 负向测试用例
    print("\n负向测试用例:")
    negative_cases = [
        {'test_id': 'TC_N001', 'company1': '不存在的公司ABC123', 'company2': '测试公司XYZ', 'expected_result': '查不到两个公司的关系'},
        {'test_id': 'TC_N002', 'company1': '江西正邦科技股份有限公司', 'company2': '阿里巴巴集团控股有限公司', 'expected_result': '查不到两个公司的关系'},
        {'test_id': 'TC_N003', 'company1': '', 'company2': '', 'expected_result': '请输入公司信息'},
    ]
    
    for case in negative_cases:
        print(f"  {case['test_id']}: {case['company1']} <-> {case['company2']}")
    
    return report, negative_cases

if __name__ == "__main__":
    graph, uri = get_graph_connection()
    
    if graph:
        print(f"\n已连接到Neo4j: {uri}")
        
        # 分析图谱
        rel_types = analyze_graph(graph)
        
        # 查找测试案例
        test_cases = find_test_cases(graph, rel_types)
        
        # 生成测试报告
        report, negative_cases = generate_test_report(test_cases)
        
        print("\n" + "=" * 70)
        print("5. 使用说明")
        print("=" * 70)
        print("""
测试步骤：
1. 打开前端关系查询页面: http://localhost:8080/queryrelationship
2. 根据上述正向测试用例，输入公司名称进行查询
3. 验证是否能正确返回关系信息
4. 测试负向用例，验证错误提示是否正确

测试要点：
- 中文关系类型（如诉讼仲裁）是否能正确查询
- 公司名称模糊匹配是否生效
- 查询不到关系时是否显示"查不到两个公司的关系"
- 空输入是否有提示
""")
