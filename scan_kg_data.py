#!/usr/bin/env python3
"""
扫描 Neo4j 知识图谱，生成数据报告
用于更新前端测试页面的统计数据
"""
from py2neo import Graph
import json

# 连接 Neo4j
graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))

def get_node_stats():
    """获取节点统计"""
    # 所有节点标签
    labels_query = """
    CALL db.labels() YIELD label
    RETURN label
    """
    labels = [r['label'] for r in graph.run(labels_query).data()]
    
    # 每个标签的节点数
    label_counts = {}
    for label in labels:
        count_query = f"MATCH (n:{label}) RETURN count(n) as cnt"
        cnt = graph.run(count_query).data()[0]['cnt']
        label_counts[label] = cnt
    
    # 总节点数
    total_nodes = sum(label_counts.values())
    
    return {
        'total_nodes': total_nodes,
        'label_counts': label_counts,
        'labels': labels
    }

def get_relationship_stats():
    """获取关系统计"""
    # 所有关系类型
    types_query = """
    CALL db.relationshipTypes() YIELD relationshipType
    RETURN relationshipType
    """
    rel_types = [r['relationshipType'] for r in graph.run(types_query).data()]
    
    # 每种关系的数量
    rel_counts = {}
    for rel_type in rel_types:
        count_query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as cnt"
        cnt = graph.run(count_query).data()[0]['cnt']
        rel_counts[rel_type] = cnt
    
    # 总关系数
    total_rels_query = "MATCH ()-[r]->() RETURN count(r) as cnt"
    total_rels = graph.run(total_rels_query).data()[0]['cnt']
    
    return {
        'total_relationships': total_rels,
        'relationship_types': rel_types,
        'relationship_counts': rel_counts
    }

def get_company_details():
    """获取公司详细信息"""
    # 检查 Company 节点有哪些属性
    sample_query = """
    MATCH (c:Company) 
    RETURN c 
    LIMIT 1
    """
    sample = graph.run(sample_query).data()
    
    if not sample:
        return []
    
    # 获取所有公司
    companies_query = """
    MATCH (c:Company) 
    RETURN c.`公司中文名称` as name,
           c.`A股证券代码` as a_code,
           c.`B股证券代码` as b_code,
           c.`证券代码` as stock_code,
           c.`主营业务` as main_business,
           c.`公司类型` as company_type
    """
    
    companies = graph.run(companies_query).data()
    
    # 处理上市状态和行业
    result = []
    for c in companies:
        name = c.get('name', '')
        if not name:
            continue
            
        # 判断上市状态：有证券代码即为上市公司
        a_code = c.get('a_code', '')
        b_code = c.get('b_code', '')
        stock_code = c.get('stock_code', '')
        
        is_listed = bool(a_code or b_code or stock_code)
        
        # 推断行业（从主营业务或公司类型）
        main_business = c.get('main_business', '')
        company_type = c.get('company_type', '')
        
        industry = infer_industry(main_business, company_type, name)
        
        result.append({
            'name': name,
            'listed': is_listed,
            'industry': industry,
            'main_business': main_business[:50] if main_business else ''
        })
    
    return result

def infer_industry(main_business, company_type, name):
    """根据主营业务推断行业"""
    text = f"{main_business} {company_type} {name}".lower()
    
    # 关键词映射
    industry_keywords = {
        '银行': ['银行', '金融', '信贷', '储蓄', '贷款'],
        '保险': ['保险', '人寿', '财险', '再保险'],
        '证券': ['证券', '券商', '投行', '期货', '信托'],
        '房地产': ['房地产', '地产', '物业', '建筑', '房地产开发', '置业'],
        '互联网': ['互联网', '网络', '软件', '信息技术', '电子商务', '电商', '游戏', '科技'],
        '通信': ['通信', '电信', '移动', '联通', '网络设备', '通讯'],
        '医药生物': ['医药', '生物', '制药', '药品', '医疗', '医院', '疫苗'],
        '食品饮料': ['食品', '饮料', '酒水', '白酒', '啤酒', '乳业', '农业'],
        '家电': ['家电', '电器', '空调', '冰箱', '洗衣机', '彩电'],
        '汽车': ['汽车', '整车', '新能源汽车', '电动车', '轿车', '卡车'],
        '石油化工': ['石油', '化工', '化学', '能源', '煤炭', '天然气'],
        '机械设备': ['机械', '设备', '重工', '机床', '制造'],
        '电子': ['电子', '半导体', '芯片', '集成电路', '元器件'],
        '新能源': ['新能源', '光伏', '风电', '太阳能', '锂电池', '储能'],
        '交通运输': ['交通', '运输', '物流', '航运', '航空', '铁路', '港口'],
        '传媒': ['传媒', '广告', '影视', '出版', '媒体', '文化'],
        '公用事业': ['电力', '水务', '燃气', '供热', '环保'],
        '商贸零售': ['零售', '商贸', '百货', '超市', '连锁'],
        '纺织服装': ['纺织', '服装', '服饰', '家纺'],
        '建筑材料': ['建材', '水泥', '玻璃', '陶瓷'],
        '有色金属': ['有色', '金属', '稀土', '黄金', '铜', '铝'],
        '钢铁': ['钢铁', '冶炼'],
        '国防军工': ['军工', '国防', '航天', '航空装备'],
    }
    
    for industry, keywords in industry_keywords.items():
        for kw in keywords:
            if kw in text:
                return industry
    
    # 默认行业
    if '金融' in text or '投资' in text:
        return '金融'
    if '制造' in text:
        return '制造业'
    
    return '其他'

def generate_report():
    """生成完整数据报告"""
    print("=" * 60)
    print("知识图谱数据扫描报告")
    print("=" * 60)
    
    # 节点统计
    node_stats = get_node_stats()
    print(f"\n【节点统计】")
    print(f"总节点数: {node_stats['total_nodes']}")
    print(f"节点类型分布:")
    for label, cnt in sorted(node_stats['label_counts'].items(), key=lambda x: -x[1]):
        print(f"  - {label}: {cnt}")
    
    # 关系统计
    rel_stats = get_relationship_stats()
    print(f"\n【关系统计】")
    print(f"总关系数: {rel_stats['total_relationships']}")
    print(f"关系类型分布:")
    for rel_type, cnt in sorted(rel_stats['relationship_counts'].items(), key=lambda x: -x[1]):
        print(f"  - {rel_type}: {cnt}")
    
    # 公司详情
    companies = get_company_details()
    print(f"\n【公司统计】")
    print(f"公司总数: {len(companies)}")
    
    listed = [c for c in companies if c['listed']]
    unlisted = [c for c in companies if not c['listed']]
    print(f"  - 上市公司: {len(listed)}")
    print(f"  - 非上市公司: {len(unlisted)}")
    
    # 行业分布
    industry_dist = {}
    for c in companies:
        ind = c['industry']
        industry_dist[ind] = industry_dist.get(ind, 0) + 1
    
    print(f"\n【行业分布 Top 10】")
    for ind, cnt in sorted(industry_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {ind}: {cnt}")
    
    # 生成前端可用的数据文件
    output = {
        'scan_time': str(graph.run("RETURN datetime() as now").data()[0]['now']),
        'node_stats': node_stats,
        'relationship_stats': rel_stats,
        'companies': companies,
        'industry_distribution': industry_dist,
        'listed_stats': {
            'listed': len(listed),
            'unlisted': len(unlisted)
        }
    }
    
    # 保存 JSON
    with open('/home/huyuan/openclaw/kg_data_report.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 保存前端直接可用的 JS 数据
    js_content = f"""// 知识图谱数据报告 - 自动生成
// 扫描时间: {output['scan_time']}

export const kgDataReport = {json.dumps(output, ensure_ascii=False, indent=2)};

// 公司数据集（用于测试页面）
export const companyDataset = {json.dumps(companies, ensure_ascii=False, indent=2)};
"""
    
    with open('/home/huyuan/openclaw/front/src/data/kg_report.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"\n【输出文件】")
    print(f"  - JSON报告: /home/huyuan/openclaw/kg_data_report.json")
    print(f"  - JS数据: /home/huyuan/openclaw/front/src/data/kg_report.js")
    print("=" * 60)
    
    return output

if __name__ == '__main__':
    try:
        report = generate_report()
        print("\n扫描完成!")
    except Exception as e:
        print(f"扫描失败: {e}")
        import traceback
        traceback.print_exc()
