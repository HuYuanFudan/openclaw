#!/usr/bin/env python3
"""
对"同事件提及"关系进行更精准的分类
"""

import json
import re

def classify_relation(rel_data):
    """
    根据证据句和新闻内容对关系进行分类
    返回更精准的关系类型
    """
    evidence = rel_data.get('evidence', '') or ''
    news = rel_data.get('news', {}) or {}
    title = news.get('title', '') or ''
    content = news.get('content', '') or ''
    abstract = news.get('abstract', '') or ''

    combined = evidence + title + abstract + content

    # 分类规则（按优先级排序）

    # 1. 高管履历关联 - 最具体的关系
    if any(kw in combined for kw in ['就职于', '任职于', '曾任', '原任', '履历显示', '此前就职', '兼任']):
        if any(kw in combined for kw in ['董事', '高管', '经理', '独立董事']):
            return '高管履历关联'

    # 2. 法律纠纷/仲裁
    if any(kw in combined for kw in ['仲裁', '诉讼', '状告', '起诉', '索赔', '追讨']):
        if '原告' in combined or '被告' in combined or '申请人' in combined:
            return '法律纠纷'

    # 3. IPO周报/审核类新闻
    if any(kw in title for kw in ['IPO周报', '注册制IPO']):
        if '中止' in combined:
            return 'IPO中止'
        elif '终止' in combined or '撤回' in combined:
            return 'IPO终止'
        elif '暂缓' in combined or '暂缓表决' in combined:
            return 'IPO暂缓'
        elif '过会' in combined:
            return 'IPO同批过会'
        elif '注册生效' in combined:
            return 'IPO注册生效'
        else:
            return 'IPO审核相关'

    # 4. IPO同批上会/审核
    if any(kw in title for kw in ['上会', '过会', '暂缓', '审议', 'IPO直通车']):
        if '暂缓' in combined:
            return 'IPO暂缓'
        elif '过会' in combined or '通过' in combined:
            return 'IPO同批过会'
        elif '上会' in combined:
            return 'IPO同批上会'
        else:
            return 'IPO审核相关'

    # 5. IPO被否/失败
    if any(kw in combined for kw in ['IPO被否', '被否决', '未获通过', '上会未获通过']):
        return 'IPO被否'

    # 6. IPO中止（因事务所等共同原因）
    if '中止冲击波' in title or '中止IPO' in combined:
        return 'IPO中止'

    # 7. IPO终止/撤回名单
    if any(kw in title for kw in ['终止IPO', '终止排队', '撤回材料']):
        return 'IPO终止'

    # 8. 监管处罚/点名
    if any(kw in combined for kw in ['被点名', '飞检', '通报批评', '行政处罚', '监管措施']):
        return '监管处罚名单'

    # 9. 红黑榜/诚信评级
    if any(kw in combined for kw in ['红黑榜', '诚信', '黑名单']):
        return '诚信评级关联'

    # 10. 行业排名/榜单/表彰
    if any(kw in title for kw in ['百强', '排名', '榜单', '进入省', '通报表扬', '表彰']):
        return '行业排名/榜单'

    # 11. 中介机构关联
    if any(kw in title for kw in ['中介机构', '保荐', '会所', '律所', '过会项目数排名', '券商']):
        return '中介机构关联'

    # 12. 同一保荐/券商关联
    if '国元证券' in combined or '证券股份有限公司' in combined:
        if any(kw in combined for kw in ['关于', '核查意见', '独立财务顾问']):
            return '券商保荐关联'

    # 13. 业绩对比/盈利预警
    if any(kw in title for kw in ['业绩', '盈利预警', '收入', '财报', '市盈率']):
        return '业绩对比'

    # 14. 公告汇总/日报
    if any(kw in title for kw in ['公告严选', '公告日报', '每日', '公告汇总', '快报']):
        return '公告汇总'

    # 15. 行业对比分析
    if any(kw in combined for kw in ['行业领头', '领头羊', '市场份额', '可比公司']):
        return '行业对比分析'

    # 16. 审计机构关联
    if '续聘' in title and '审计机构' in combined:
        return '审计机构关联'

    # 17. 碳排放/环保履约
    if any(kw in combined for kw in ['碳市场', '碳排放', '排污', '环保']):
        return '环保履约关联'

    # 18. 招标/竞标关联
    if any(kw in combined for kw in ['招标', '中标', '竞标', '资格预审', '采购']):
        return '招标竞标关联'

    # 19. 同日上市
    if '同日上市' in combined or '股票将于' in combined:
        return '同日上市'

    # 20. 区域/地方新闻
    if any(kw in title for kw in ['安徽省', '合肥市', '安庆', '淮南', '蚌埠', '平舆县']):
        return '区域新闻关联'

    # 21. 行业综述/数据概览
    if any(kw in title for kw in ['概览', '动态', '舆情', '数据榜']):
        return '行业综述'

    # 22. IPO申报关联
    if any(kw in combined for kw in ['首发申请', '申报材料', '拟IPO']):
        return 'IPO申报关联'

    # 23. 同行对比/可比公司
    if '同行' in combined or '可比公司' in combined:
        return '同行对比'

    # 24. 品牌/产品关联（假冒等）
    if any(kw in combined for kw in ['假冒', '商标', '品牌']):
        return '品牌商标关联'

    # 25. 破产/债权关联
    if any(kw in combined for kw in ['破产', '债权人', '清偿']):
        return '破产债权关联'

    # 26. 股权转让
    if any(kw in combined for kw in ['转让占', '股权转让', '受让']):
        return '股权转让'

    # 27. 检验检测关联
    if any(kw in title for kw in ['检验检测', '检测结果', '检验结果']):
        return '检验检测关联'

    # 28. IPO终止审查
    if any(kw in combined for kw in ['终止审查', '撤单']):
        return 'IPO终止'

    # 29. 同行产品/供应商列举
    if any(kw in combined for kw in ['发动机', '供应商', '配套']):
        return '同行产品列举'

    # 默认分类 - 列举类新闻
    if '、' in evidence and evidence.count('、') >= 3:
        return '列举式并列提及'

    return '同事件提及'

def main():
    # 读取数据
    with open('/home/huyuan/openclaw/same_event_relations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 对每条关系进行重新分类
    results = []
    type_count = {}

    for rel in data:
        new_type = classify_relation(rel)
        rel['new_relation_type'] = new_type
        type_count[new_type] = type_count.get(new_type, 0) + 1
        results.append(rel)

    # 输出分类统计
    print("="*60)
    print("重新分类结果统计")
    print("="*60)
    print(f"\n总数: {len(results)}条\n")

    print("各类型分布:")
    for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}条")

    # 保存结果
    output_file = '/home/huyuan/openclaw/reclassified_relations.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")

    # 生成详细报告
    report = []
    report.append("# 同事件提及关系重新分类报告\n")
    report.append(f"处理时间: 2026-05-14\n")
    report.append(f"原始数据: 214条'同事件提及'关系\n")
    report.append(f"重新分类后: {len(results)}条\n")
    report.append("\n## 分类结果统计\n")
    report.append("| 关系类型 | 数量 | 占比 |")
    report.append("|----------|------|------|")
    for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
        pct = f"{c/len(results)*100:.1f}%"
        report.append(f"| {t} | {c} | {pct} |")

    # 每种类型的典型例子
    report.append("\n## 各类型典型示例\n")
    for rel_type in sorted(type_count.keys()):
        report.append(f"\n### {rel_type}")
        examples = [r for r in results if r['new_relation_type'] == rel_type][:3]
        for i, ex in enumerate(examples, 1):
            report.append(f"\n**示例{i}:**")
            report.append(f"- 公司A: {ex['company1']}")
            report.append(f"- 公司B: {ex['company2']}")
            report.append(f"- 证据: {ex['evidence'][:150]}...")
            report.append(f"- 新闻: {ex['news'].get('title', '无标题')}")

    with open('/home/huyuan/openclaw/关系重新分类报告.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print(f"详细报告已保存到: /home/huyuan/openclaw/关系重新分类报告.md")

if __name__ == '__main__':
    main()
