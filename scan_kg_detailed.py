#!/usr/bin/env python3
"""
深度扫描知识图谱，生成细粒度数据：
1. 违规事件(Violation) 涉及的主体行业分布
2. 诉讼仲裁(Litigation) 案件的主体/客体行业分布
3. 金融风险类型分析 (PLEDGE/GUARANTEES/起诉 等)
"""
from py2neo import Graph
import json

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

def infer_industry_company(c):
    """从 Company 节点属性推断行业"""
    main_business = c.get('主营业务', '') or c.get('business_scope', '') or ''
    company_type = c.get('公司类型', '') or c.get('company_type', '') or ''
    name = c.get('name', '') or c.get('公司中文名称', '')
    text = f"{main_business} {company_type} {name}".lower()
    if not text.strip():
        return '未知'
    industry_keywords = {
        '互联网': ['互联网', '网络', '软件', '信息技术', '电子商务', '电商', '游戏', '科技', '数字'],
        '银行': ['银行', '金融', '信贷', '储蓄', '贷款'],
        '保险': ['保险', '人寿', '财险', '再保险'],
        '证券': ['证券', '券商', '投行', '期货', '信托'],
        '房地产': ['房地产', '地产', '物业', '建筑', '房地产开发', '置业'],
        '医药生物': ['医药', '生物', '制药', '药品', '医疗', '医院', '疫苗', '健康'],
        '食品饮料': ['食品', '饮料', '酒水', '白酒', '啤酒', '乳业', '农业', '养殖', '食品加工'],
        '家电': ['家电', '电器', '空调', '冰箱', '洗衣机', '彩电', '智能家居'],
        '汽车': ['汽车', '整车', '新能源汽车', '电动车', '轿车', '卡车', '客车', '零部件'],
        '石油化工': ['石油', '化工', '化学', '能源', '煤炭', '天然气', '石化'],
        '机械设备': ['机械', '设备', '重工', '机床', '制造', '工业'],
        '电子元件': ['电子', '半导体', '芯片', '集成电路', '元器件', '面板', '显示器'],
        '新能源': ['新能源', '光伏', '风电', '太阳能', '锂电池', '储能', '电池'],
        '通信': ['通信', '电信', '移动', '联通', '网络设备', '通讯', '5g'],
        '交通运输': ['交通', '运输', '物流', '航运', '航空', '铁路', '港口', '快递'],
        '传媒': ['传媒', '广告', '影视', '出版', '媒体', '文化', '游戏'],
        '公用事业': ['电力', '水务', '燃气', '供热', '环保', '公共事业'],
        '商贸零售': ['零售', '商贸', '百货', '超市', '连锁', '贸易', '批发'],
        '纺织服装': ['纺织', '服装', '服饰', '家纺', '面料'],
        '建筑材料': ['建材', '水泥', '玻璃', '陶瓷', '钢材'],
        '有色金属': ['有色', '金属', '稀土', '黄金', '铜', '铝', '锌', '矿业'],
        '钢铁': ['钢铁', '冶炼', '炼钢'],
        '国防军工': ['军工', '国防', '航天', '航空装备', '兵器', '船舶'],
    }
    for industry, keywords in industry_keywords.items():
        for kw in keywords:
            if kw in text:
                return industry
    if '制造' in text:
        return '制造业'
    if '服务' in text or '咨询' in text:
        return '服务业'
    return '其他'

def get_company_industry_map(limit=20000):
    """构建公司名 -> 行业 的映射（采样）"""
    print("[1/5] 采样公司节点推断行业...")
    query = """
    MATCH (c:Company) 
    WHERE c.`主营业务` IS NOT NULL OR c.`公司类型` IS NOT NULL OR c.`公司中文名称` IS NOT NULL
    RETURN c.`公司中文名称` as name, c.`主营业务` as business, c.`公司类型` as type
    LIMIT $limit
    """
    result = list(graph.run(query, limit=limit).data())
    print(f"   采样 {len(result)} 家公司")
    mapping = {}
    for r in result:
        name = r.get('name')
        if name:
            ind = infer_industry_company({'name': name, '主营业务': r.get('business'), '公司类型': r.get('type')})
            mapping[name] = ind
    return mapping

def violation_subject_industries(industry_map):
    """违规事件的主体的行业分布"""
    print("[2/5] 违规事件主体行业分布...")
    # 违规事件 -> 主体公司
    query = """
    MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
    WITH v, collect(DISTINCT c.`公司中文名称`)[0] as company_name
    RETURN company_name
    LIMIT 5000
    """
    rows = list(graph.run(query).data())
    ind_count = {}
    no_match = 0
    for r in rows:
        cn = r.get('company_name')
        if not cn:
            no_match += 1
            continue
        ind = industry_map.get(cn, '其他')
        ind_count[ind] = ind_count.get(ind, 0) + 1
    print(f"   {len(rows)} 条违规记录, {no_match} 条主体未知")
    return dict(sorted(ind_count.items(), key=lambda x: -x[1]))

def litigation_party_industries(industry_map):
    """诉讼仲裁案件的主体/客体行业分布"""
    print("[3/5] 诉讼仲裁案件主体/客体行业分布...")
    # 主体：Company -[诉讼仲裁]-> Litigation，客体：Litigation 关联的另一个公司
    # 通过 Litigation -> Company 的"被诉"或者"起诉"关系
    query_subject = """
    MATCH (c:Company)-[r:`诉讼仲裁`]->(l:Litigation)
    WITH l, collect(DISTINCT c.`公司中文名称`)[0] as plaintiff
    RETURN plaintiff
    LIMIT 5000
    """
    rows_subj = list(graph.run(query_subject).data())
    subject_ind = {}
    for r in rows_subj:
        cn = r.get('plaintiff')
        if cn:
            ind = industry_map.get(cn, '其他')
            subject_ind[ind] = subject_ind.get(ind, 0) + 1
    # 客体 - 通过 Litigation 的属性或反向关系查找
    query_object = """
    MATCH (l:Litigation)-[r:`被诉`|`被告`|`诉讼关联`]->(c:Company)
    WITH l, collect(DISTINCT c.`公司中文名称`)[0] as defendant
    RETURN defendant
    LIMIT 5000
    """
    rows_obj = list(graph.run(query_object).data())
    object_ind = {}
    for r in rows_obj:
        cn = r.get('defendant')
        if cn:
            ind = industry_map.get(cn, '其他')
            object_ind[ind] = object_ind.get(ind, 0) + 1
    print(f"   主体记录 {len(rows_subj)} 条, 客体记录 {len(rows_obj)} 条")
    return {
        'subject': dict(sorted(subject_ind.items(), key=lambda x: -x[1])),
        'object': dict(sorted(object_ind.items(), key=lambda x: -x[1]))
    }

def financial_risk_distribution(industry_map):
    """金融风险类型分布"""
    print("[4/5] 金融风险类型分析...")
    risks = {}
    # PLEDGE 质押
    pledge_q = """
    MATCH (c:Company)-[r:PLEDGE]->(target:Company)
    WITH c, collect(DISTINCT target.`公司中文名称`)[0] as pledge_to
    RETURN c.`公司中文名称` as pledger, pledge_to
    LIMIT 3000
    """
    rows = list(graph.run(pledge_q).data())
    pledge_ind = {}
    for r in rows:
        cn = r.get('pledger')
        if cn:
            ind = industry_map.get(cn, '其他')
            pledge_ind[ind] = pledge_ind.get(ind, 0) + 1
    risks['PLEDGE_质押'] = dict(sorted(pledge_ind.items(), key=lambda x: -x[1]))
    print(f"   PLEDGE: {len(rows)} 条")

    # GUARANTEES 担保
    gua_q = """
    MATCH (c:Company)-[r:GUARANTEES]->(target:Company)
    WITH c, collect(DISTINCT target.`公司中文名称`)[0] as gua_to
    RETURN c.`公司中文名称` as guarantor, gua_to
    LIMIT 3000
    """
    rows = list(graph.run(gua_q).data())
    gua_ind = {}
    for r in rows:
        cn = r.get('guarantor')
        if cn:
            ind = industry_map.get(cn, '其他')
            gua_ind[ind] = gua_ind.get(ind, 0) + 1
    risks['GUARANTEES_担保'] = dict(sorted(gua_ind.items(), key=lambda x: -x[1]))
    print(f"   GUARANTEES: {len(rows)} 条")

    # 起诉 - 金融风险中的"原告起诉"
    sue_q = """
    MATCH (c:Company)-[r:`起诉`]->(target:Company)
    WITH c, collect(DISTINCT target.`公司中文名称`)[0] as sued
    RETURN c.`公司中文名称` as suer, sued
    LIMIT 3000
    """
    rows = list(graph.run(sue_q).data())
    sue_ind = {}
    for r in rows:
        cn = r.get('suer')
        if cn:
            ind = industry_map.get(cn, '其他')
            sue_ind[ind] = sue_ind.get(ind, 0) + 1
    risks['起诉_原告'] = dict(sorted(sue_ind.items(), key=lambda x: -x[1]))
    print(f"   起诉: {len(rows)} 条")

    # 违规事件类型分布
    vio_type_q = """
    MATCH (v:Violation)
    RETURN v.`违规类型` as vtype, count(v) as cnt
    ORDER BY cnt DESC
    LIMIT 20
    """
    vio_types = [(r.get('vtype') or '未分类', r.get('cnt')) for r in graph.run(vio_type_q).data()]
    risks['违规类型分布'] = {k: v for k, v in vio_types}
    print(f"   违规类型数: {len(vio_types)}")

    # 诉讼案件类型分布
    lit_type_q = """
    MATCH (l:Litigation)
    RETURN l.`案件类型` as ltype, count(l) as cnt
    ORDER BY cnt DESC
    LIMIT 20
    """
    lit_types = [(r.get('ltype') or '未分类', r.get('cnt')) for r in graph.run(lit_type_q).data()]
    risks['诉讼类型分布'] = {k: v for k, v in lit_types}
    print(f"   诉讼类型数: {len(lit_types)}")

    return risks

def violation_case_timeline():
    """违规事件时间趋势"""
    print("[5/5] 违规事件/诉讼案件时间趋势...")
    vio_time = """
    MATCH (v:Violation)
    WHERE v.`处罚日期` IS NOT NULL
    RETURN v.`处罚日期` as dt, count(v) as cnt
    ORDER BY dt DESC
    LIMIT 50
    """
    vio_timeline = [(str(r.get('dt'))[:10], r.get('cnt')) for r in graph.run(vio_time).data()]
    lit_time = """
    MATCH (l:Litigation)
    WHERE l.`立案日期` IS NOT NULL
    RETURN l.`立案日期` as dt, count(l) as cnt
    ORDER BY dt DESC
    LIMIT 50
    """
    lit_timeline = [(str(r.get('dt'))[:10], r.get('cnt')) for r in graph.run(lit_time).data()]
    return {
        'violation': vio_timeline,
        'litigation': lit_timeline
    }

def get_risk_summary(industry_map):
    """金融风险综合统计"""
    # 公司关联风险事件总数 Top 10
    risk_company_q = """
    MATCH (c:Company)-[r1:`违规事件`|`诉讼仲裁`|`起诉`]->()
    WITH c, count(r1) as risk_count
    ORDER BY risk_count DESC
    LIMIT 20
    RETURN c.`公司中文名称` as name, risk_count
    """
    risk_companies = [(r.get('name'), r.get('risk_count')) for r in graph.run(risk_company_q).data()]
    return risk_companies

def main():
    print("=" * 70)
    print("知识图谱细粒度数据扫描")
    print("=" * 70)

    industry_map = get_company_industry_map()

    violation_data = violation_subject_industries(industry_map)
    litigation_data = litigation_party_industries(industry_map)
    risk_data = financial_risk_distribution(industry_map)
    timeline = violation_case_timeline()
    risk_companies = get_risk_summary(industry_map)

    output = {
        'violation_industries': violation_data,
        'litigation_industries': litigation_data,
        'financial_risks': risk_data,
        'timeline': timeline,
        'high_risk_companies': risk_companies,
        'industry_map_size': len(industry_map)
    }

    with open('/home/huyuan/openclaw/kg_detailed_report.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("扫描完成")
    print(f"  行业映射: {len(industry_map)} 家公司")
    print(f"  违规事件行业数: {len(violation_data)}")
    print(f"  诉讼主体行业数: {len(litigation_data['subject'])}")
    print(f"  诉讼客体行业数: {len(litigation_data['object'])}")
    print(f"  高风险公司 Top: {len(risk_companies)}")
    print("=" * 70)
    return output

if __name__ == '__main__':
    main()
