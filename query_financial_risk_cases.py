#!/usr/bin/env python3
"""
查询Neo4j知识图谱中的金融风险案例数据
用于丰富"图谱金融风险知识"页面的展示
"""
from py2neo import Graph
import json

# 连接Neo4j
graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

def query_guarantee_cases():
    """1. 对外担保风险案例：查询有GUARANTEES关系的公司案例"""
    print("=" * 80)
    print("【1. 对外担保风险案例 - GUARANTEES关系】")
    print("=" * 80)
    
    # 查询Cypher语句
    cypher = """
    MATCH (c1:Company)-[r:GUARANTEES]->(c2:Company)
    RETURN c1.`公司中文名称` as 担保方,
           c2.`公司中文名称` as 被担保方,
           r.`担保金额` as 担保金额,
           r.`担保期限` as 担保期限,
           r.`债务类型` as 债务类型,
           r.`债权人类型` as 债权人类型,
           r.`币种` as 币种
    ORDER BY r.`担保金额` DESC
    LIMIT 10
    """
    
    print("\n【Cypher查询语句】")
    print(cypher)
    
    results = list(graph.run(cypher).data())
    
    print(f"\n【查询结果】共 {len(results)} 条案例")
    print("-" * 80)
    
    cases = []
    for i, r in enumerate(results, 1):
        case = {
            "公司名称": r.get('担保方', 'N/A'),
            "风险类型": "对外担保风险",
            "关系类型": "GUARANTEES",
            "涉及公司": r.get('被担保方', 'N/A'),
            "担保金额": r.get('担保金额', 'N/A'),
            "担保期限": r.get('担保期限', 'N/A'),
            "债务类型": r.get('债务类型', 'N/A'),
            "债权人类型": r.get('债权人类型', 'N/A'),
            "币种": r.get('币种', 'N/A')
        }
        cases.append(case)
        print(f"\n案例 {i}:")
        print(f"  担保方: {case['公司名称']}")
        print(f"  被担保方: {case['涉及公司']}")
        print(f"  担保金额: {case['担保金额']} {case['币种']}")
        print(f"  担保期限: {case['担保期限']}")
        print(f"  债务类型: {case['债务类型']}")
    
    # 统计总数
    count_cypher = "MATCH ()-[r:GUARANTEES]->() RETURN count(r) as total"
    total = graph.run(count_cypher).data()[0]['total']
    print(f"\n【统计】对外担保关系总数: {total}")
    
    return cases, total

def query_pledge_cases():
    """2. 股权质押风险案例：查询有PLEDGE关系的公司案例"""
    print("\n" + "=" * 80)
    print("【2. 股权质押风险案例 - PLEDGE关系】")
    print("=" * 80)
    
    cypher = """
    MATCH (c1:Company)-[r:PLEDGE]->(c2:Company)
    RETURN c1.`公司中文名称` as 质押方,
           c2.`公司中文名称` as 质权方,
           r.`质押股数` as 质押股数,
           r.`质押用途编码` as 质押用途,
           r.`质押方类型编码` as 质押方类型,
           r.`质押比例` as 质押比例,
           r.`变动原因` as 变动原因
    ORDER BY r.`质押股数` DESC
    LIMIT 10
    """
    
    print("\n【Cypher查询语句】")
    print(cypher)
    
    results = list(graph.run(cypher).data())
    
    print(f"\n【查询结果】共 {len(results)} 条案例")
    print("-" * 80)
    
    cases = []
    for i, r in enumerate(results, 1):
        case = {
            "公司名称": r.get('质押方', 'N/A'),
            "风险类型": "股权质押风险",
            "关系类型": "PLEDGE",
            "涉及公司": r.get('质权方', 'N/A'),
            "质押股数": r.get('质押股数', 'N/A'),
            "质押比例": r.get('质押比例', 'N/A'),
            "质押用途": r.get('质押用途', 'N/A'),
            "质押方类型": r.get('质押方类型', 'N/A'),
            "变动原因": r.get('变动原因', 'N/A')
        }
        cases.append(case)
        print(f"\n案例 {i}:")
        print(f"  质押方: {case['公司名称']}")
        print(f"  质权方: {case['涉及公司']}")
        print(f"  质押股数: {case['质押股数']}")
        print(f"  质押比例: {case['质押比例']}")
        print(f"  质押用途: {case['质押用途']}")
    
    count_cypher = "MATCH ()-[r:PLEDGE]->() RETURN count(r) as total"
    total = graph.run(count_cypher).data()[0]['total']
    print(f"\n【统计】股权质押关系总数: {total}")
    
    return cases, total

def query_violation_cases():
    """3. 违规事件案例：查询有"违规事件"关系的Violation节点案例"""
    print("\n" + "=" * 80)
    print("【3. 违规事件案例 - 违规事件关系】")
    print("=" * 80)
    
    cypher = """
    MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
    RETURN c.`公司中文名称` as 公司名称,
           v.`违规类型` as 违规类型,
           v.`违规类型编码` as 违规类型编码,
           v.`处罚日期` as 处罚日期,
           v.`处罚金额` as 处罚金额,
           v.`处理单位` as 处理单位,
           v.`违规事实摘要` as 违规事实摘要
    ORDER BY v.`处罚日期` DESC
    LIMIT 10
    """
    
    print("\n【Cypher查询语句】")
    print(cypher)
    
    results = list(graph.run(cypher).data())
    
    print(f"\n【查询结果】共 {len(results)} 条案例")
    print("-" * 80)
    
    cases = []
    for i, r in enumerate(results, 1):
        case = {
            "公司名称": r.get('公司名称', 'N/A'),
            "风险类型": "违规事件",
            "关系类型": "违规事件",
            "违规类型": r.get('违规类型', 'N/A'),
            "违规类型编码": r.get('违规类型编码', 'N/A'),
            "处罚日期": r.get('处罚日期', 'N/A'),
            "处罚金额": r.get('处罚金额', 'N/A'),
            "处理单位": r.get('处理单位', 'N/A'),
            "违规事实摘要": (r.get('违规事实摘要', '') or '')[:100] + "..." if r.get('违规事实摘要') else 'N/A'
        }
        cases.append(case)
        print(f"\n案例 {i}:")
        print(f"  公司名称: {case['公司名称']}")
        print(f"  违规类型: {case['违规类型']}")
        print(f"  处罚日期: {case['处罚日期']}")
        print(f"  处罚金额: {case['处罚金额']}")
        print(f"  处理单位: {case['处理单位']}")
        print(f"  违规摘要: {case['违规事实摘要']}")
    
    count_cypher = "MATCH ()-[r:`违规事件`]->() RETURN count(r) as total"
    total = graph.run(count_cypher).data()[0]['total']
    print(f"\n【统计】违规事件关系总数: {total}")
    
    return cases, total

def query_litigation_cases():
    """4. 诉讼仲裁案例：查询Litigation节点案例"""
    print("\n" + "=" * 80)
    print("【4. 诉讼仲裁案例 - Litigation节点】")
    print("=" * 80)
    
    cypher = """
    MATCH (l:Litigation)
    RETURN l.`起诉(申请)方` as 起诉方,
           l.`应诉(被申请)方` as 应诉方,
           l.`涉案缘由` as 涉案缘由,
           l.`涉案金额` as 涉案金额,
           l.`司法类型` as 司法类型,
           l.`事件类型` as 事件类型,
           l.`司法进程` as 司法进程,
           l.`公告日期` as 公告日期
    ORDER BY l.`涉案金额` DESC
    LIMIT 10
    """
    
    print("\n【Cypher查询语句】")
    print(cypher)
    
    results = list(graph.run(cypher).data())
    
    print(f"\n【查询结果】共 {len(results)} 条案例")
    print("-" * 80)
    
    cases = []
    for i, r in enumerate(results, 1):
        case = {
            "公司名称": r.get('起诉方', 'N/A'),
            "风险类型": "诉讼仲裁",
            "节点类型": "Litigation",
            "起诉方": r.get('起诉方', 'N/A'),
            "应诉方": r.get('应诉方', 'N/A'),
            "涉案缘由": r.get('涉案缘由', 'N/A'),
            "涉案金额": r.get('涉案金额', 'N/A'),
            "司法类型": r.get('司法类型', 'N/A'),
            "事件类型": r.get('事件类型', 'N/A'),
            "司法进程": r.get('司法进程', 'N/A'),
            "公告日期": r.get('公告日期', 'N/A')
        }
        cases.append(case)
        print(f"\n案例 {i}:")
        print(f"  起诉方: {case['起诉方']}")
        print(f"  应诉方: {case['应诉方']}")
        print(f"  涉案缘由: {case['涉案缘由']}")
        print(f"  涉案金额: {case['涉案金额']} 万元")
        print(f"  司法类型: {case['司法类型']}")
        print(f"  司法进程: {case['司法进程']}")
    
    count_cypher = "MATCH (l:Litigation) RETURN count(l) as total"
    total = graph.run(count_cypher).data()[0]['total']
    print(f"\n【统计】Litigation节点总数: {total}")
    
    return cases, total

def query_sue_cases():
    """5. 起诉案例：查询有"起诉"关系的公司案例"""
    print("\n" + "=" * 80)
    print("【5. 起诉案例 - 起诉关系】")
    print("=" * 80)
    
    cypher = """
    MATCH (c1:Company)-[r:`起诉`]->(c2:Company)
    RETURN c1.`公司中文名称` as 原告,
           c2.`公司中文名称` as 被告,
           r.`事件类型` as 事件类型,
           r.`司法进程` as 司法进程,
           r.`公告类型` as 公告类型,
           r.`损益影响` as 损益影响,
           r.`公告日期` as 公告日期
    LIMIT 10
    """
    
    print("\n【Cypher查询语句】")
    print(cypher)
    
    results = list(graph.run(cypher).data())
    
    print(f"\n【查询结果】共 {len(results)} 条案例")
    print("-" * 80)
    
    cases = []
    for i, r in enumerate(results, 1):
        case = {
            "公司名称": r.get('原告', 'N/A'),
            "风险类型": "起诉",
            "关系类型": "起诉",
            "原告": r.get('原告', 'N/A'),
            "被告": r.get('被告', 'N/A'),
            "事件类型": r.get('事件类型', 'N/A'),
            "司法进程": r.get('司法进程', 'N/A'),
            "公告类型": r.get('公告类型', 'N/A'),
            "损益影响": r.get('损益影响', 'N/A'),
            "公告日期": r.get('公告日期', 'N/A')
        }
        cases.append(case)
        print(f"\n案例 {i}:")
        print(f"  原告: {case['原告']}")
        print(f"  被告: {case['被告']}")
        print(f"  事件类型: {case['事件类型']}")
        print(f"  司法进程: {case['司法进程']}")
        print(f"  损益影响: {case['损益影响']}")
    
    count_cypher = "MATCH ()-[r:`起诉`]->() RETURN count(r) as total"
    total = graph.run(count_cypher).data()[0]['total']
    print(f"\n【统计】起诉关系总数: {total}")
    
    return cases, total

def query_violation_by_unit():
    """6. 监管处罚案例：查询Violation节点中不同处理单位的案例"""
    print("\n" + "=" * 80)
    print("【6. 监管处罚案例 - 按处理单位分类】")
    print("=" * 80)
    
    # 首先查询处理单位分布
    unit_cypher = """
    MATCH (v:Violation)
    WHERE v.`处理单位` IS NOT NULL
    RETURN v.`处理单位` as 处理单位, count(*) as 案例数
    ORDER BY 案例数 DESC
    LIMIT 10
    """
    
    print("\n【Cypher查询语句 - 处理单位分布】")
    print(unit_cypher)
    
    unit_results = list(graph.run(unit_cypher).data())
    
    print(f"\n【处理单位分布】")
    print("-" * 80)
    for r in unit_results:
        print(f"  {r.get('处理单位', 'N/A')}: {r.get('案例数', 0)} 条")
    
    # 查询具体案例
    cypher = """
    MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
    WHERE v.`处理单位` IS NOT NULL
    RETURN c.`公司中文名称` as 公司名称,
           v.`处理单位` as 处理单位,
           v.`违规类型` as 违规类型,
           v.`处罚日期` as 处罚日期,
           v.`处罚金额` as 处罚金额,
           v.`处罚结果` as 处罚结果
    ORDER BY v.`处罚日期` DESC
    LIMIT 15
    """
    
    print("\n【Cypher查询语句 - 具体案例】")
    print(cypher)
    
    results = list(graph.run(cypher).data())
    
    print(f"\n【查询结果】共 {len(results)} 条案例")
    print("-" * 80)
    
    cases = []
    for i, r in enumerate(results, 1):
        case = {
            "公司名称": r.get('公司名称', 'N/A'),
            "风险类型": "监管处罚",
            "关系类型": "违规事件",
            "处理单位": r.get('处理单位', 'N/A'),
            "违规类型": r.get('违规类型', 'N/A'),
            "处罚日期": r.get('处罚日期', 'N/A'),
            "处罚金额": r.get('处罚金额', 'N/A'),
            "处罚结果": r.get('处罚结果', 'N/A')
        }
        cases.append(case)
        print(f"\n案例 {i}:")
        print(f"  公司名称: {case['公司名称']}")
        print(f"  处理单位: {case['处理单位']}")
        print(f"  违规类型: {case['违规类型']}")
        print(f"  处罚日期: {case['处罚日期']}")
        print(f"  处罚金额: {case['处罚金额']}")
        print(f"  处罚结果: {case['处罚结果']}")
    
    return cases, unit_results

def main():
    print("=" * 80)
    print("Neo4j 知识图谱金融风险案例数据查询")
    print("=" * 80)
    print(f"连接地址: neo4j://10.176.22.62:7687")
    print(f"数据库: Neo4j 金融知识图谱")
    print("=" * 80)
    
    all_results = {}
    
    # 1. 对外担保风险案例
    guarantee_cases, guarantee_total = query_guarantee_cases()
    all_results['guarantee'] = {'cases': guarantee_cases, 'total': guarantee_total}
    
    # 2. 股权质押风险案例
    pledge_cases, pledge_total = query_pledge_cases()
    all_results['pledge'] = {'cases': pledge_cases, 'total': pledge_total}
    
    # 3. 违规事件案例
    violation_cases, violation_total = query_violation_cases()
    all_results['violation'] = {'cases': violation_cases, 'total': violation_total}
    
    # 4. 诉讼仲裁案例
    litigation_cases, litigation_total = query_litigation_cases()
    all_results['litigation'] = {'cases': litigation_cases, 'total': litigation_total}
    
    # 5. 起诉案例
    sue_cases, sue_total = query_sue_cases()
    all_results['sue'] = {'cases': sue_cases, 'total': sue_total}
    
    # 6. 监管处罚案例
    penalty_cases, unit_stats = query_violation_by_unit()
    all_results['penalty'] = {'cases': penalty_cases, 'unit_stats': unit_stats}
    
    # 保存结果到JSON文件
    output_file = '/home/huyuan/openclaw/financial_risk_cases.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # 打印汇总
    print("\n" + "=" * 80)
    print("【数据汇总】")
    print("=" * 80)
    print(f"1. 对外担保风险案例: {guarantee_total} 条")
    print(f"2. 股权质押风险案例: {pledge_total} 条")
    print(f"3. 违规事件案例: {violation_total} 条")
    print(f"4. 诉讼仲裁案例: {litigation_total} 条")
    print(f"5. 起诉案例: {sue_total} 条")
    print(f"6. 监管处罚案例: {len(penalty_cases)} 条")
    print("-" * 80)
    print(f"\n数据已保存到: {output_file}")
    print("=" * 80)

if __name__ == '__main__':
    main()
