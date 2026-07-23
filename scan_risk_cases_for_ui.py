#!/usr/bin/env python3
"""
扫描知识图谱，为五大风险类型下的15个子类获取真实案例数据
输出格式适合前端展示
"""
from py2neo import Graph
import json

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

def get_sample_cases(query, limit=5):
    """执行Cypher查询并返回案例列表"""
    try:
        results = list(graph.run(query).data())
        return results[:limit]
    except Exception as e:
        print(f"  查询失败: {e}")
        return []

def count_relations(rel_name):
    """统计关系数量"""
    try:
        cypher = f"MATCH ()-[r:`{rel_name}`]->() RETURN count(r) as total"
        result = graph.run(cypher).data()
        return result[0]['total'] if result else 0
    except:
        return 0

def count_nodes(label):
    """统计节点数量"""
    try:
        cypher = f"MATCH (n:`{label}`) RETURN count(n) as total"
        result = graph.run(cypher).data()
        return result[0]['total'] if result else 0
    except:
        return 0

# ============================================================
# 1. 市场风险 (Market Risk)
# ============================================================
print("=" * 60)
print("【市场风险】")
print("=" * 60)

market_risk = {
    "name": "市场风险",
    "description": "因市场价格（股价、利率、汇率等）波动导致的损失风险",
    "sub_types": [
        {
            "name": "股债对冲效应",
            "description": "股票与国债现货存在显著互相对冲效应，可作为资产配置工具",
            "cases": get_sample_cases("""
                MATCH (n:MetaKnowledge)
                WHERE n.core_conclusion CONTAINS '股票' OR n.core_conclusion CONTAINS '国债' OR n.core_conclusion CONTAINS '对冲'
                RETURN n.id as id, n.core_conclusion as conclusion, n.risk_guidance as risk_guidance, n.related_event as related_event
                LIMIT 5
            """),
            "count": count_nodes("MetaKnowledge")
        },
        {
            "name": "灾难风险溢价",
            "description": "灾难风险可解释中国股市约39.5%的股权溢价",
            "cases": get_sample_cases("""
                MATCH (n:MetaKnowledge)
                WHERE n.core_conclusion CONTAINS '灾难' OR n.core_conclusion CONTAINS '风险溢价' OR n.core_conclusion CONTAINS '尾部风险'
                RETURN n.id as id, n.core_conclusion as conclusion, n.risk_guidance as risk_guidance, n.related_event as related_event
                LIMIT 5
            """),
            "count": count_nodes("MetaKnowledge")
        },
        {
            "name": "期货对冲局限",
            "description": "股指期货与国债期货之间不存在显著对冲效应",
            "cases": get_sample_cases("""
                MATCH (n:MetaKnowledge)
                WHERE n.core_conclusion CONTAINS '期货' OR n.core_conclusion CONTAINS '股指期货' OR n.core_conclusion CONTAINS '国债期货'
                RETURN n.id as id, n.core_conclusion as conclusion, n.risk_guidance as risk_guidance, n.related_event as related_event
                LIMIT 5
            """),
            "count": count_nodes("MetaKnowledge")
        }
    ]
}

# ============================================================
# 2. 信用风险 (Credit Risk)
# ============================================================
print("\n" + "=" * 60)
print("【信用风险】")
print("=" * 60)

credit_risk = {
    "name": "信用风险",
    "description": "交易对手未能履行约定契约中的义务而造成经济损失的风险",
    "sub_types": [
        {
            "name": "对外担保风险",
            "description": "对外担保形成或有负债，担保对象多为上市公司子公司",
            "cases": get_sample_cases("""
                MATCH (c1:Company)-[r:GUARANTEES]->(c2:Company)
                RETURN c1.`公司中文名称` as guarantor, c2.`公司中文名称` as guaranteed, 
                       r.`担保金额` as amount, r.`担保期限` as term, r.`债务类型` as debt_type
                ORDER BY r.`担保金额` DESC
                LIMIT 5
            """),
            "count": count_relations("GUARANTEES")
        },
        {
            "name": "股权质押风险",
            "description": "股东质押股权融资存在平仓、爆仓及控制权变更风险",
            "cases": get_sample_cases("""
                MATCH (c1:Company)-[r:PLEDGE]->(c2:Company)
                RETURN c1.`公司中文名称` as pledgor, c2.`公司中文名称` as pledgee,
                       r.`质押股数` as shares, r.`质押比例` as ratio, r.`质押用途编码` as purpose
                ORDER BY r.`质押股数` DESC
                LIMIT 5
            """),
            "count": count_relations("PLEDGE")
        },
        {
            "name": "影子银行信用",
            "description": "抵押率是影响高风险企业融资成本和信贷规模的关键变量",
            "cases": get_sample_cases("""
                MATCH (c1:Company)-[r:GUARANTEES]->(c2:Company)
                WHERE r.`担保金额` IS NOT NULL
                RETURN c1.`公司中文名称` as company, c2.`公司中文名称` as target,
                       r.`担保金额` as amount, r.`债权人类型` as creditor_type,
                       r.`债务类型` as debt_type
                ORDER BY r.`担保金额` DESC
                LIMIT 5
            """),
            "count": count_relations("GUARANTEES")
        }
    ]
}

# ============================================================
# 3. 操作风险 (Operational Risk)
# ============================================================
print("\n" + "=" * 60)
print("【操作风险】")
print("=" * 60)

operational_risk = {
    "name": "操作风险",
    "description": "由不完善或有问题的内部程序、人员、系统或外部事件所造成损失的风险",
    "sub_types": [
        {
            "name": "信息披露违规",
            "description": "推迟披露、虚假记载、重大遗漏等违规类型频发",
            "cases": get_sample_cases("""
                MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
                WHERE v.`违规类型` CONTAINS '披露' OR v.`违规类型` CONTAINS '虚假' OR v.`违规类型` CONTAINS '遗漏'
                RETURN c.`公司中文名称` as company, v.`违规类型` as violation_type,
                       v.`处罚日期` as penalty_date, v.`处罚金额` as penalty_amount,
                       v.`处理单位` as authority, v.`违规事实摘要` as summary
                ORDER BY v.`处罚日期` DESC
                LIMIT 5
            """),
            "count": count_relations("违规事件")
        },
        {
            "name": "管理层策略性行为",
            "description": "管理层可能策略性增加创新投入以吸引投资者关注并借机减持套现",
            "cases": get_sample_cases("""
                MATCH (n:MetaKnowledge)
                WHERE n.core_conclusion CONTAINS '管理层' OR n.core_conclusion CONTAINS '减持' OR n.core_conclusion CONTAINS '创新投入'
                RETURN n.id as id, n.core_conclusion as conclusion, n.risk_guidance as risk_guidance, n.related_event as related_event
                LIMIT 5
            """),
            "count": count_nodes("MetaKnowledge")
        },
        {
            "name": "网络安全感知",
            "description": "移动端投资者网络安全风险感知要求更高的风险补偿",
            "cases": get_sample_cases("""
                MATCH (n:MetaKnowledge)
                WHERE n.core_conclusion CONTAINS '网络安全' OR n.core_conclusion CONTAINS '移动端' OR n.core_conclusion CONTAINS '投资者行为'
                RETURN n.id as id, n.core_conclusion as conclusion, n.risk_guidance as risk_guidance, n.related_event as related_event
                LIMIT 5
            """),
            "count": count_nodes("MetaKnowledge")
        }
    ]
}

# ============================================================
# 4. 流动性风险 (Liquidity Risk)
# ============================================================
print("\n" + "=" * 60)
print("【流动性风险】")
print("=" * 60)

liquidity_risk = {
    "name": "流动性风险",
    "description": "企业无法及时获得充足资金或无法以合理成本及时获得充足资金的风险",
    "sub_types": [
        {
            "name": "政策不确定性与现金持有",
            "description": "经济政策不确定性上升会显著抑制企业投资并提高现金持有",
            "cases": get_sample_cases("""
                MATCH (n:MetaKnowledge)
                WHERE n.core_conclusion CONTAINS '政策不确定性' OR n.core_conclusion CONTAINS '现金持有' OR n.core_conclusion CONTAINS '企业投资'
                RETURN n.id as id, n.core_conclusion as conclusion, n.risk_guidance as risk_guidance, n.related_event as related_event
                LIMIT 5
            """),
            "count": count_nodes("MetaKnowledge")
        },
        {
            "name": "跨境资本流动",
            "description": "区域危机期间中国证券市场与发达市场一体化水平反而增强",
            "cases": get_sample_cases("""
                MATCH (n:MetaKnowledge)
                WHERE n.core_conclusion CONTAINS '跨境' OR n.core_conclusion CONTAINS '资本流动' OR n.core_conclusion CONTAINS '外资'
                RETURN n.id as id, n.core_conclusion as conclusion, n.risk_guidance as risk_guidance, n.related_event as related_event
                LIMIT 5
            """),
            "count": count_nodes("MetaKnowledge")
        },
        {
            "name": "投资者行为",
            "description": "移动端投资者网络安全风险感知越高，安全事件可能诱发赎回潮",
            "cases": get_sample_cases("""
                MATCH (n:MetaKnowledge)
                WHERE n.core_conclusion CONTAINS '投资者' OR n.core_conclusion CONTAINS '赎回' OR n.core_conclusion CONTAINS '行为'
                RETURN n.id as id, n.core_conclusion as conclusion, n.risk_guidance as risk_guidance, n.related_event as related_event
                LIMIT 5
            """),
            "count": count_nodes("MetaKnowledge")
        }
    ]
}

# ============================================================
# 5. 声誉风险 (Reputational Risk)
# ============================================================
print("\n" + "=" * 60)
print("【声誉风险】")
print("=" * 60)

reputation_risk = {
    "name": "声誉风险",
    "description": "由负面的公众舆论、媒体报道或利益相关者评价导致企业声誉受损的风险",
    "sub_types": [
        {
            "name": "监管处罚",
            "description": "深交所、上交所、证监会及地方监管局处罚事件会损害公司声誉",
            "cases": get_sample_cases("""
                MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
                WHERE v.`处理单位` IS NOT NULL
                RETURN c.`公司中文名称` as company, v.`处理单位` as authority,
                       v.`违规类型` as violation_type, v.`处罚日期` as penalty_date,
                       v.`处罚金额` as penalty_amount, v.`处罚结果` as penalty_result
                ORDER BY v.`处罚日期` DESC
                LIMIT 5
            """),
            "count": count_relations("违规事件")
        },
        {
            "name": "诉讼仲裁",
            "description": "大额诉讼案件（超1亿元占比93%）及司法执行信息会显著影响公司市场声誉",
            "cases": get_sample_cases("""
                MATCH (l:Litigation)
                WHERE l.`涉案金额` IS NOT NULL AND l.`涉案金额` > 0
                RETURN l.`起诉(申请)方` as plaintiff, l.`应诉(被申请)方` as defendant,
                       l.`涉案金额` as amount, l.`涉案缘由` as reason,
                       l.`司法类型` as judicial_type, l.`司法进程` as progress,
                       l.`公告日期` as announce_date
                ORDER BY l.`涉案金额` DESC
                LIMIT 5
            """),
            "count": count_nodes("Litigation")
        },
        {
            "name": "风险警示",
            "description": "ST/*ST公司集中在批发、计算机通信、商务服务等行业",
            "cases": get_sample_cases("""
                MATCH (c:Company)
                WHERE c.`公司全称` CONTAINS 'ST' OR c.`公司中文名称` CONTAINS 'ST'
                RETURN c.`公司中文名称` as company, c.`公司全称` as full_name,
                       c.`所属行业` as industry, c.`上市状态` as status
                LIMIT 5
            """),
            "count": count_nodes("Company")
        }
    ]
}

# ============================================================
# 汇总并保存
# ============================================================
risk_case_data = {
    "market_risk": market_risk,
    "credit_risk": credit_risk,
    "operational_risk": operational_risk,
    "liquidity_risk": liquidity_risk,
    "reputation_risk": reputation_risk,
    "updated_at": "2026-07-23"
}

output_file = '/home/huyuan/openclaw/risk_case_data.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(risk_case_data, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print("【数据汇总】")
print("=" * 60)
for risk_name, risk_data in risk_case_data.items():
    if risk_name == 'updated_at':
        continue
    print(f"\n{risk_data['name']}:")
    for sub in risk_data['sub_types']:
        print(f"  - {sub['name']}: {len(sub['cases'])} 个案例, 总数据: {sub['count']}")

print(f"\n数据已保存到: {output_file}")
print("=" * 60)