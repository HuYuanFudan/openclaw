#!/usr/bin/env python3
"""全面扫描图谱中蕴含的金融风险知识"""
from py2neo import Graph
import json
import re
from collections import Counter

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

report = {}

# ========== 1. MetaKnowledge 元知识风险类型 ==========
print("[1] MetaKnowledge 风险知识...")
mk_query = """
MATCH (n:MetaKnowledge)
WHERE n.core_conclusion IS NOT NULL OR n.risk_guidance IS NOT NULL
RETURN n.id as id,
       n.core_conclusion as conclusion,
       n.risk_guidance as risk,
       n.related_event as event,
       n.premise as premise
LIMIT 300
"""
mks = list(graph.run(mk_query).data())
print(f"  元知识节点 {len(mks)} 条")

# 按关键词分类
risk_categories = {
    '系统性风险': ['系统性', '系统风险', '系统性金融风险'],
    '市场风险': ['市场风险', '股票市场', '债市', '国债', '股市波动', '股灾', '股指', '期货'],
    '信用风险': ['信用', '违约', '偿债', '债务'],
    '流动性风险': ['流动性', '资金链'],
    '操作风险': ['操作风险', '内控', '合规', '违规'],
    '法律/监管风险': ['法律', '诉讼', '监管', '合规', '违法'],
    '宏观经济/政策风险': ['宏观经济', '货币政策', '财政', '利率', '汇率', '通胀', '地方债', '政府债务'],
    '风险对冲/缓释': ['对冲', '避险', '缓释', '跨市场', '资产配置'],
    '信息披露/治理风险': ['信息披露', '披露不实', '虚假记载', '推迟披露', '重大遗漏', '公司治理'],
    '杠杆/质押风险': ['杠杆', '质押', '股权质押', '担保'],
    '关联/传染风险': ['关联', '传染', '集团', '子公司风险'],
}
mk_classified = {k: [] for k in risk_categories}
mk_classified['其他'] = []
for m in mks:
    text = (m.get('conclusion') or '') + (m.get('risk') or '') + (m.get('premise') or '')
    matched = False
    for cat, kws in risk_categories.items():
        if any(kw in text for kw in kws):
            mk_classified[cat].append({
                'id': m.get('id'),
                'conclusion': (m.get('conclusion') or '')[:180],
                'risk': (m.get('risk') or '')[:180],
                'event': (m.get('event') or '')[:120],
            })
            matched = True
            break
    if not matched:
        mk_classified['其他'].append({
            'id': m.get('id'),
            'conclusion': (m.get('conclusion') or '')[:180],
            'risk': (m.get('risk') or '')[:180],
        })

mk_summary = []
for cat, items in mk_classified.items():
    if items:
        mk_summary.append({'category': cat, 'count': len(items), 'samples': items[:3]})
        print(f"  {cat}: {len(items)} 条")
report['meta_knowledge'] = mk_summary

# ========== 2. Violation 违规行为类别（节点属性） ==========
print("\n[2] Violation 违规行为编码...")
vio_query = """
MATCH (v:Violation)
WHERE v.`违规类型编码` IS NOT NULL
RETURN v.`违规类型编码` as code, count(*) as c
ORDER BY c DESC LIMIT 20
"""
vio_codes = []
for r in graph.run(vio_query).data():
    vio_codes.append({'code': r.get('code'), 'count': r.get('c')})
    print(f"  {r.get('code')}: {r.get('c')}")
report['violation_codes'] = vio_codes

# ========== 3. Violation 处理单位（监管来源） ==========
print("\n[3] Violation 处理单位（监管来源）...")
vio_unit_q = """
MATCH (v:Violation)
WHERE v.`处理单位` IS NOT NULL
RETURN v.`处理单位` as unit, count(*) as c
ORDER BY c DESC LIMIT 10
"""
report['violation_units'] = [{'unit': r['unit'], 'count': r['c']} for r in graph.run(vio_unit_q).data()]

# ========== 4. Litigation 司法类型/事件类型/司法进程 ==========
print("\n[4] Litigation 司法类型/事件类型/司法进程...")
for field in ['司法类型', '事件类型', '司法进程', '执行状态编码', '公告类型']:
    q = f"""
    MATCH (l:Litigation)
    WHERE l.`{field}` IS NOT NULL
    RETURN l.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 8
    """
    res = [{'value': r['v'], 'count': r['c']} for r in graph.run(q).data()]
    report[f'litigation_{field}'] = res
    print(f"  {field}: {res[:3]}")

# ========== 5. 子公司关系：是否退出、设立方式 ==========
print("\n[5] 子公司关系风险特征...")
sub_q = """
MATCH ()-[r:子公司]->()
WHERE r.`是否退出` IS NOT NULL
RETURN r.`是否退出` as v, count(*) as c
ORDER BY c DESC
"""
report['subsidiary_exited'] = [{'value': r['v'], 'count': r['c']} for r in graph.run(sub_q).data()]

sub_q2 = """
MATCH ()-[r:子公司]->()
WHERE r.`设立方式` IS NOT NULL
RETURN r.`设立方式` as v, count(*) as c
ORDER BY c DESC LIMIT 10
"""
report['subsidiary_setup'] = [{'value': r['v'], 'count': r['c']} for r in graph.run(sub_q2).data()]

# ========== 6. PLEDGE 质押用途 / 质押方类型 ==========
print("\n[6] PLEDGE 质押风险特征...")
for field in ['PurposeCode', 'PledgorTypeCode', 'PledgeeCatergory', 'ChangeReason', 'JointPledgeSeq']:
    q = f"""
    MATCH ()-[r:PLEDGE]->()
    WHERE r.`{field}` IS NOT NULL
    RETURN r.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 8
    """
    res = [{'value': str(r['v']), 'count': r['c']} for r in graph.run(q).data()]
    report[f'pledge_{field}'] = res
    print(f"  {field}: {res[:3]}")

# ========== 7. GUARANTEES 担保类型 / 债务类型 ==========
print("\n[7] GUARANTEES 担保风险特征...")
for field in ['GuaranteeTerm', 'LoanWayID', 'CreditorType', 'PledgeUseFor', 'CurrencyCode', 'RelateToGuarantee', 'RelateToCreditor']:
    q = f"""
    MATCH ()-[r:GUARANTEES]->()
    WHERE r.`{field}` IS NOT NULL
    RETURN r.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 6
    """
    res = [{'value': str(r['v']), 'count': r['c']} for r in graph.run(q).data()]
    report[f'guarantee_{field}'] = res
    print(f"  {field}: {res[:3]}")

# ========== 8. 客户/供应商 关系：企业规模、资本背景、经营状态、地区 ==========
print("\n[8] 客户/供应商 关系风险特征...")
for rel_name in ['客户', '供应商']:
    for field in ['企业规模', '资本背景', '经营状态', '地区', '行业（二级）']:
        q = f"""
        MATCH ()-[r:`{rel_name}`]->()
        WHERE r.`{field}` IS NOT NULL
        RETURN r.`{field}` as v, count(*) as c
        ORDER BY c DESC LIMIT 6
        """
        res = [{'value': str(r['v']), 'count': r['c']} for r in graph.run(q).data()]
        report[f'{rel_name}_{field}'] = res

# ========== 9. 客户/供应商 风险特征：失信、注销、吊销等 ==========
print("\n[9] 客户/供应商 经营异常统计...")
risk_status = ['注销', '吊销', '撤销', '迁出', '停业', '清算']
risk_count = {'客户': {}, '供应商': {}}
for rel_name in ['客户', '供应商']:
    q = f"""
    MATCH ()-[r:`{rel_name}`]->()
    WHERE r.`经营状态` IS NOT NULL
    WITH r.`经营状态` as st, count(*) as c
    RETURN st, c
    """
    for r in graph.run(q).data():
        st = r['st']
        for k in risk_status:
            if k in st:
                risk_count[rel_name][k] = risk_count[rel_name].get(k, 0) + r['c']
                break
report['risk_customer_status'] = risk_count

# ========== 10. 起诉关系中事件类型 / 司法进程 ==========
print("\n[10] 起诉关系风险特征...")
for field in ['事件类型', '司法进程', '公告类型']:
    q = f"""
    MATCH ()-[r:起诉]->()
    WHERE r.`{field}` IS NOT NULL
    RETURN r.`{field}` as v, count(*) as c
    ORDER BY c DESC LIMIT 6
    """
    res = [{'value': str(r['v']), 'count': r['c']} for r in graph.run(q).data()]
    report[f'sue_{field}'] = res

# ========== 11. 起诉关系 - 损益影响 ==========
print("\n[11] 起诉 损益影响分布...")
loss_q = """
MATCH ()-[r:起诉]->()
WHERE r.`损益影响` IS NOT NULL
RETURN r.`损益影响` as v, count(*) as c
ORDER BY c DESC LIMIT 10
"""
report['sue_loss'] = [{'value': str(r['v']), 'count': r['c']} for r in graph.run(loss_q).data()]

# ========== 12. Company 行业（属性）和风险 ==========
print("\n[12] Company 行业分布（如果有此属性）...")
ind_q = """
MATCH (c:Company)
WHERE c.`所属行业` IS NOT NULL
RETURN c.`所属行业` as ind, count(*) as c
ORDER BY c DESC LIMIT 15
"""
ind_res = [{'industry': r['ind'], 'count': r['c']} for r in graph.run(ind_q).data()]
report['company_industries'] = ind_res
print(f"  行业属性数据: {len(ind_res)} 类")

# ========== 13. 风险类型汇总（金融风险大类） ==========
financial_risk_overview = [
    {'name': '信息披露风险', 'icon': 'document', 'color': '#e6a23c',
     'sources': ['Violation 违规类型（推迟披露/虚假记载/重大遗漏）', '公告日期/公告类型'],
     'count': 18776, 'desc': '上市公司未按法规及时、准确、完整披露信息'},
    {'name': '监管处罚风险', 'icon': 'warning', 'color': '#f56c6c',
     'sources': ['Violation 处理单位（深交所/上交所/证监会/地方监管局）'],
     'count': 18776, 'desc': '被监管机构立案调查、行政处罚、纪律处分等'},
    {'name': '股权质押风险', 'icon': 'coin', 'color': '#ff7e00',
     'sources': ['PLEDGE 关系 + PurposeCode/ChangeReason/PledgorTypeCode'],
     'count': 20863, 'desc': '股东出质股权融资，平仓/爆仓/控制权变更'},
    {'name': '对外担保风险', 'icon': 'connection', 'color': '#f56c6c',
     'sources': ['GUARANTEES 关系 + LoanWayID/CreditorType'],
     'count': 14825, 'desc': '为他人债务担保，形成或有负债'},
    {'name': '诉讼仲裁风险', 'icon': 'scale', 'color': '#409eff',
     'sources': ['Litigation 节点 + 司法类型/事件类型/司法进程/涉案金额'],
     'count': 73681, 'desc': '作为原告/被告卷入司法案件'},
    {'name': '客户集中度风险', 'icon': 'user', 'color': '#67c23a',
     'sources': ['客户 关系 + 企业规模/资本背景/合作总金额'],
     'count': 98247, 'desc': '重大客户依赖与客户经营异常'},
    {'name': '供应链风险', 'icon': 'box', 'color': '#1abc9c',
     'sources': ['供应商 关系 + 经营状态/地区/资质标签'],
     'count': 82472, 'desc': '核心供应商断供/违约/经营异常'},
    {'name': '子公司管控风险', 'icon': 'office-building', 'color': '#9b59b6',
     'sources': ['子公司 关系 + 是否退出/直接持股_百分比'],
     'count': 227459, 'desc': '子公司失控、退出、股权稀释'},
    {'name': '宏观经济/政策风险', 'icon': 'data-analysis', 'color': '#795548',
     'sources': ['MetaKnowledge 元知识 + core_conclusion/risk_guidance'],
     'count': 201, 'desc': '利率/汇率/财政/货币政策变化'},
    {'name': '跨市场对冲风险', 'icon': 'refresh', 'color': '#00bcd4',
     'sources': ['MetaKnowledge 股债跷跷板/期货对冲结论'],
     'count': 35, 'desc': '股债/股期跨市场风险传导与对冲'},
    {'name': '地方债务传染风险', 'icon': 'money', 'color': '#607d8b',
     'sources': ['MetaKnowledge 地方公共债务/隐性债务'],
     'count': 8, 'desc': '地方债扩张传导至企业的资源配置效率风险'},
    {'name': '系统性金融风险', 'icon': 'warning-filled', 'color': '#c0392b',
     'sources': ['MetaKnowledge 系统性金融风险/区域金融稳定'],
     'count': 12, 'desc': '跨行业跨市场的金融体系稳定性风险'},
]
report['financial_risk_overview'] = financial_risk_overview

# 保存
with open('/home/huyuan/openclaw/kg_financial_risk.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("\n保存到 kg_financial_risk.json")
print(f"  MetaKnowledge 分类: {len(mk_summary)} 类")
print(f"  Violation 类型: {len(vio_codes)}")
print(f"  担保字段: {len([k for k in report if k.startswith('guarantee_')])}")
print(f"  质押字段: {len([k for k in report if k.startswith('pledge_')])}")
