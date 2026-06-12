#!/usr/bin/env python3
"""
深度扫描：基于 Litigation 节点的属性字段（起诉方/应诉方/涉案缘由/涉案金额）做行业推断
"""
from py2neo import Graph
import json
import re

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

def infer_industry_from_text(text):
    """从文本（公司名/案件内容）推断行业"""
    if not text:
        return '未知'
    text_l = text.lower()
    industry_keywords = {
        '房地产': ['房地产', '地产', '物业', '置业', '城建', '建筑工程', '建筑', '置业', '置业', '房产', '住宅', '商业地产', '金科', '万科', '碧桂园', '保利', '中海', '融创', '恒大'],
        '银行': ['银行', '工商', '建设银行', '中国银行', '农业银行', '招商银行', '浦发', '民生', '兴业', '信贷', '金融'],
        '保险': ['保险', '人寿', '财险', '平安', '太平洋', '人保', '国寿'],
        '证券': ['证券', '券商', '中信', '华泰', '海通', '国泰', '招商证券', '广发', '国信'],
        '互联网': ['互联网', '网络', '软件', '科技', '信息技术', '电子商务', '电商', '游戏', '数字', '阿里', '腾讯', '百度', '京东', '美团', '字节', '华为', '小米', '联想'],
        '医药生物': ['医药', '生物', '制药', '药品', '医疗', '医院', '疫苗', '健康', '恒瑞', '复星', '药明', '国药'],
        '食品饮料': ['食品', '饮料', '酒水', '白酒', '啤酒', '乳业', '农业', '养殖', '茅台', '五粮液', '海天', '伊利', '蒙牛', '哇哈哈', '老干妈'],
        '家电': ['家电', '电器', '空调', '冰箱', '洗衣机', '彩电', '智能家居', '美的', '格力', '海尔', '海信', '长虹', 'TCL', '创维'],
        '汽车': ['汽车', '整车', '新能源车', '电动车', '轿车', '卡车', '客车', '零部件', '比亚迪', '蔚来', '理想', '小鹏', '吉利', '长城', '长安', '上汽', '广汽'],
        '石油化工': ['石油', '化工', '化学', '能源', '煤炭', '天然气', '石化', '中石油', '中石化', '中海油', '万华'],
        '机械设备': ['机械', '设备', '重工', '机床', '制造', '工业', '三一', '徐工', '中联', '卡特'],
        '电子元件': ['电子', '半导体', '芯片', '集成电路', '元器件', '面板', '显示器', '京东方', '韦尔', '歌尔', '立讯', '蓝思'],
        '新能源': ['新能源', '光伏', '风电', '太阳能', '锂电池', '储能', '电池', '宁德', '隆基', '金风', '阳光', '比亚迪'],
        '通信': ['通信', '电信', '移动', '联通', '网络设备', '通讯', '5g', '中兴', '华为', '烽火', '信维'],
        '交通运输': ['交通', '运输', '物流', '航运', '航空', '铁路', '港口', '快递', '顺丰', '圆通', '申通', '中通', '韵达', '德邦', '国航', '东航', '南航', '海航', '中外运'],
        '传媒': ['传媒', '广告', '影视', '出版', '媒体', '文化', '游戏', '分众', '光线', '万达', '华谊'],
        '公用事业': ['电力', '水务', '燃气', '供热', '环保', '公共事业', '国电', '华能', '大唐', '华电', '国投'],
        '商贸零售': ['零售', '商贸', '百货', '超市', '连锁', '贸易', '批发', '苏宁', '国美', '永辉', '大商', '王府井'],
        '纺织服装': ['纺织', '服装', '服饰', '家纺', '面料', '雅戈尔', '海澜', '森马', '太平鸟', '安踏', '李宁', '特步'],
        '建筑材料': ['建材', '水泥', '玻璃', '陶瓷', '钢材', '海螺', '冀东', '金隅', '南玻', '福耀'],
        '有色金属': ['有色', '金属', '稀土', '黄金', '铜', '铝', '锌', '矿业', '紫金', '江西铜业', '中国铝业'],
        '钢铁': ['钢铁', '冶炼', '炼钢', '宝钢', '武钢', '鞍钢', '河钢'],
        '国防军工': ['军工', '国防', '航天', '航空装备', '兵器', '船舶', '中国船舶', '中航', '航天科技', '航天科工'],
    }
    for industry, keywords in industry_keywords.items():
        for kw in keywords:
            if kw in text_l or kw in text:
                return industry
    if '制造' in text:
        return '制造业'
    if '服务' in text or '咨询' in text:
        return '服务业'
    if '管理' in text or '投资' in text or '控股' in text or '集团' in text:
        return '投资控股'
    return '其他'

def violation_subject():
    """违规事件主体行业分布（使用 Violation 节点的 公司全称/证券简称 字段）"""
    print("[1] 违规事件主体行业分布...")
    query = """
    MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
    WITH v, c
    RETURN c.`公司中文名称` as company, v.`违规类型` as vtype, v.`处罚日期` as pdate
    LIMIT 5000
    """
    rows = list(graph.run(query).data())
    ind_count = {}
    type_count = {}
    for r in rows:
        cn = r.get('company') or ''
        ind = infer_industry_from_text(cn)
        ind_count[ind] = ind_count.get(ind, 0) + 1
        vtype = r.get('vtype') or '未分类'
        type_count[vtype] = type_count.get(vtype, 0) + 1
    print(f"   {len(rows)} 条")
    return dict(sorted(ind_count.items(), key=lambda x: -x[1])), dict(sorted(type_count.items(), key=lambda x: -x[1]))

def litigation_party_industries():
    """诉讼案件主体/客体行业分布（从 Litigation 节点的属性提取起诉方/应诉方）"""
    print("[2] 诉讼案件主体/客体行业分布...")
    query = """
    MATCH (l:Litigation)
    WHERE l.`起诉(申请)方` IS NOT NULL
    RETURN l.`起诉(申请)方` as plaintiff, 
           l.`应诉(被申请)方` as defendant,
           l.`涉案缘由` as reason,
           l.`涉案金额` as amount,
           l.`公告日期` as pdate
    LIMIT 5000
    """
    rows = list(graph.run(query).data())
    print(f"   {len(rows)} 条")
    plaintiff_ind = {}
    defendant_ind = {}
    reason_count = {}
    amount_dist = {'<100万': 0, '100-1000万': 0, '1000万-1亿': 0, '>1亿': 0, '未知': 0}
    plaintiff_industry_for_defendant_industry = {}  # 主体行业 -> 客体行业 关联
    for r in rows:
        p = (r.get('plaintiff') or '').strip()
        d = (r.get('defendant') or '').strip()
        reason = (r.get('reason') or '未分类').strip()
        amount = r.get('amount') or '0'
        # 取第一个公司名（起诉方/应诉方可能是多公司）
        p_first = p.split(',')[0].split('，')[0].strip()
        d_first = d.split(',')[0].split('，')[0].strip()
        if p_first and not '个人' in p_first[:5]:
            pi = infer_industry_from_text(p_first)
            plaintiff_ind[pi] = plaintiff_ind.get(pi, 0) + 1
        if d_first and not '个人' in d_first[:5]:
            di = infer_industry_from_text(d_first)
            defendant_ind[di] = defendant_ind.get(di, 0) + 1
            if p_first and not '个人' in p_first[:5]:
                key = (pi, di)
                plaintiff_industry_for_defendant_industry[key] = plaintiff_industry_for_defendant_industry.get(key, 0) + 1
        reason_count[reason] = reason_count.get(reason, 0) + 1
        # 涉案金额分布
        try:
            amt = float(str(amount).replace(',', ''))
            if amt < 100:
                amount_dist['<100万'] += 1
            elif amt < 1000:
                amount_dist['100-1000万'] += 1
            elif amt < 10000:
                amount_dist['1000万-1亿'] += 1
            else:
                amount_dist['>1亿'] += 1
        except:
            amount_dist['未知'] += 1
    return {
        'plaintiff': dict(sorted(plaintiff_ind.items(), key=lambda x: -x[1])),
        'defendant': dict(sorted(defendant_ind.items(), key=lambda x: -x[1])),
        'reason': dict(sorted(reason_count.items(), key=lambda x: -x[1])),
        'amount': amount_dist,
        'matrix': plaintiff_industry_for_defendant_industry
    }

def financial_risk_industries():
    """金融风险关联的行业分布"""
    print("[3] 金融风险行业分布...")
    risks = {}
    # 质押 PLEDGE
    q1 = """
    MATCH (c:Company)-[r:PLEDGE]->(t:Company)
    RETURN c.`公司中文名称` as pledger, t.`公司中文名称` as target
    LIMIT 3000
    """
    rows = list(graph.run(q1).data())
    pledge_ind = {}
    for r in rows:
        cn = r.get('pledger') or ''
        ind = infer_industry_from_text(cn)
        pledge_ind[ind] = pledge_ind.get(ind, 0) + 1
    risks['PLEDGE_质押'] = dict(sorted(pledge_ind.items(), key=lambda x: -x[1]))
    print(f"   PLEDGE: {len(rows)}")

    # 担保 GUARANTEES
    q2 = """
    MATCH (c:Company)-[r:GUARANTEES]->(t:Company)
    RETURN c.`公司中文名称` as guarantor
    LIMIT 3000
    """
    rows = list(graph.run(q2).data())
    gua_ind = {}
    for r in rows:
        cn = r.get('guarantor') or ''
        ind = infer_industry_from_text(cn)
        gua_ind[ind] = gua_ind.get(ind, 0) + 1
    risks['GUARANTEES_担保'] = dict(sorted(gua_ind.items(), key=lambda x: -x[1]))
    print(f"   GUARANTEES: {len(rows)}")

    # 起诉
    q3 = """
    MATCH (c:Company)-[r:`起诉`]->(t:Company)
    RETURN c.`公司中文名称` as suer
    LIMIT 3000
    """
    rows = list(graph.run(q3).data())
    sue_ind = {}
    for r in rows:
        cn = r.get('suer') or ''
        ind = infer_industry_from_text(cn)
        sue_ind[ind] = sue_ind.get(ind, 0) + 1
    risks['起诉_原告'] = dict(sorted(sue_ind.items(), key=lambda x: -x[1]))
    print(f"   起诉: {len(rows)}")

    return risks

def high_risk_companies():
    """高风险公司 TOP 20"""
    print("[4] 高风险公司 TOP 20...")
    q = """
    MATCH (c:Company)
    OPTIONAL MATCH (c)-[r1:`违规事件`]->()
    OPTIONAL MATCH (c)-[r2:`诉讼仲裁`]->()
    OPTIONAL MATCH (c)-[r3:`起诉`]->()
    OPTIONAL MATCH (c)-[r4:PLEDGE]->()
    OPTIONAL MATCH (c)-[r5:GUARANTEES]->()
    WITH c,
         count(DISTINCT r1) as vio,
         count(DISTINCT r2) as lit,
         count(DISTINCT r3) as sue,
         count(DISTINCT r4) as pledge,
         count(DISTINCT r5) as gua,
         (count(DISTINCT r1) + count(DISTINCT r2) + count(DISTINCT r3) + count(DISTINCT r4) + count(DISTINCT r5)) as total_risk
    WHERE total_risk > 0
    RETURN c.`公司中文名称` as name, vio, lit, sue, pledge, gua, total_risk
    ORDER BY total_risk DESC
    LIMIT 30
    """
    rows = list(graph.run(q).data())
    return rows

def violation_industry_amount():
    """违规事件各行业的处罚金额分布"""
    print("[5] 违规事件金额分布...")
    q = """
    MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
    WHERE v.`处罚金额` IS NOT NULL
    RETURN c.`公司中文名称` as company, v.`处罚金额` as amount, v.`违规类型` as vtype
    LIMIT 2000
    """
    rows = list(graph.run(q).data())
    ind_amount = {}
    for r in rows:
        cn = r.get('company') or ''
        try:
            amt = float(str(r.get('amount') or 0).replace(',', ''))
        except:
            amt = 0
        ind = infer_industry_from_text(cn)
        ind_amount[ind] = ind_amount.get(ind, 0) + amt
    return dict(sorted(ind_amount.items(), key=lambda x: -x[1]))

def main():
    print("=" * 70)
    print("知识图谱细粒度深度扫描")
    print("=" * 70)

    violation_ind, violation_type = violation_subject()
    litigation_data = litigation_party_industries()
    risk_data = financial_risk_industries()
    high_risk = high_risk_companies()
    violation_amount = violation_industry_amount()

    output = {
        'violation_industries': violation_ind,
        'violation_types': violation_type,
        'litigation_industries': {k: v for k, v in litigation_data.items() if k != 'matrix'},
        'financial_risks': risk_data,
        'high_risk_companies': [dict(r) for r in high_risk],
        'violation_amount_by_industry': violation_amount,
        'plaintiff_defendant_matrix': [{'plaintiff_industry': k[0], 'defendant_industry': k[1], 'count': v} for k, v in litigation_data['matrix'].items()]
    }

    with open('/home/huyuan/openclaw/kg_detailed_report.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 生成可读摘要
    print("\n" + "=" * 70)
    print("【违规事件主体行业 TOP 10】")
    for i, (k, v) in enumerate(list(violation_ind.items())[:10], 1):
        print(f"  {i}. {k}: {v}")

    print("\n【诉讼案件-原告(起诉方)行业 TOP 10】")
    for i, (k, v) in enumerate(list(litigation_data['plaintiff'].items())[:10], 1):
        print(f"  {i}. {k}: {v}")

    print("\n【诉讼案件-被告(应诉方)行业 TOP 10】")
    for i, (k, v) in enumerate(list(litigation_data['defendant'].items())[:10], 1):
        print(f"  {i}. {k}: {v}")

    print("\n【诉讼案件-涉案缘由 TOP 10】")
    for i, (k, v) in enumerate(list(litigation_data['reason'].items())[:10], 1):
        print(f"  {i}. {k}: {v}")

    print("\n【诉讼案件-涉案金额分布】")
    for k, v in litigation_data['amount'].items():
        print(f"  {k}: {v}")

    print("\n【金融风险-质押(PLEDGE)主体行业 TOP 5】")
    for i, (k, v) in enumerate(list(risk_data['PLEDGE_质押'].items())[:5], 1):
        print(f"  {i}. {k}: {v}")

    print("\n【金融风险-担保(GUARANTEES)主体行业 TOP 5】")
    for i, (k, v) in enumerate(list(risk_data['GUARANTEES_担保'].items())[:5], 1):
        print(f"  {i}. {k}: {v}")

    print("\n【金融风险-起诉主体行业 TOP 5】")
    for i, (k, v) in enumerate(list(risk_data['起诉_原告'].items())[:5], 1):
        print(f"  {i}. {k}: {v}")

    print("\n【高风险公司 TOP 10】")
    for r in high_risk[:10]:
        print(f"  {r.get('name')}: 总风险{r.get('total_risk')} (违规{r.get('vio')},诉讼{r.get('lit')},起诉{r.get('sue')},质押{r.get('pledge')},担保{r.get('gua')})")

    print("\n" + "=" * 70)
    print("报告已保存: /home/huyuan/openclaw/kg_detailed_report.json")

if __name__ == '__main__':
    main()
