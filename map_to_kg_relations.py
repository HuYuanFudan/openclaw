#!/usr/bin/env python3
"""
将项目关系类型映射到知识图谱中的关系类型
"""

import json

# 知识图谱中的关系类型（从Neo4j获取）
KG_RELATIONSHIPS = [
    "所属城市",
    "拥有公司",
    "A股证券_公司资料",
    "违规事件",
    "子公司",
    "B股证券_公司资料",
    "GUARANTEES",
    "PLEDGE",
    "港股证券_公司资料",
    "客户",
    "供应商",
    "诉讼仲裁",
    "起诉",
]

# 项目关系类型到知识图谱关系类型的映射
# 格式: 项目关系类型 -> (图谱关系类型, 置信度, 说明)
RELATIONSHIP_MAPPING = {
    # ===== 直接匹配（高置信度）=====
    "起诉": ("起诉", "高", "完全匹配"),
    "子公司/控股": ("子公司", "高", "子公司关系直接匹配"),
    "子公司": ("子公司", "高", "子公司关系直接匹配"),
    "供应/采购": ("供应商", "高", "供应链关系，选择供应商作为代表"),
    "供应商": ("供应商", "高", "直接匹配"),
    "客户": ("客户", "高", "直接匹配"),

    # ===== 语义相近（中置信度）=====
    "监管处罚名单": ("违规事件", "中", "监管处罚与违规事件语义相近"),
    "法律纠纷": ("诉讼仲裁", "中", "法律纠纷映射到诉讼仲裁"),
    "持股/股东": ("GUARANTEES", "中", "股权关联映射到担保关系（最接近）"),
    "减持/增持": ("GUARANTEES", "中", "股权变动映射到担保关系"),
    "股权转让": ("GUARANTEES", "中", "股权转让映射到担保关系"),
    "投资/收购": ("拥有公司", "中", "投资收购意味着拥有关系"),

    # ===== 扩展映射（低置信度，建议扩展图谱）=====
    "保荐/承销": ("拥有公司", "低", "建议图谱增加'保荐/承销'关系"),
    "券商保荐关联": ("拥有公司", "低", "建议图谱增加'保荐/承销'关系"),
    "合作": ("拥有公司", "低", "建议图谱增加'合作'关系"),
    "竞争": (None, "无", "建议图谱增加'竞争'关系"),

    # ===== IPO相关（建议扩展图谱）=====
    "IPO中止": (None, "无", "建议图谱增加'IPO相关'关系"),
    "IPO暂缓": (None, "无", "建议图谱增加'IPO相关'关系"),
    "IPO终止": (None, "无", "建议图谱增加'IPO相关'关系"),
    "IPO被否": (None, "无", "建议图谱增加'IPO相关'关系"),
    "IPO申报关联": (None, "无", "建议图谱增加'IPO相关'关系"),
    "IPO同批过会": (None, "无", "建议图谱增加'IPO相关'关系"),
    "IPO同批上会": (None, "无", "建议图谱增加'IPO相关'关系"),

    # ===== 行业/业务关联（弱关联，建议扩展图谱）=====
    "列举式并列提及": (None, "无", "弱关联，不建议映射"),
    "同事件提及": (None, "无", "弱关联，不建议映射"),
    "业绩对比": (None, "无", "建议图谱增加'业绩对比'关系"),
    "行业对比分析": (None, "无", "建议图谱增加'行业对比'关系"),
    "环保履约关联": (None, "无", "建议图谱增加'环保履约'关系"),
    "高管履历关联": (None, "无", "建议图谱增加'高管关联'关系"),
    "行业排名/榜单": (None, "无", "建议图谱增加'榜单关联'关系"),
    "审计机构关联": (None, "无", "建议图谱增加'审计机构'关系"),
    "品牌商标关联": (None, "无", "建议图谱增加'品牌商标'关系"),
    "公告汇总": (None, "无", "弱关联，不建议映射"),
    "检验检测关联": (None, "无", "建议图谱增加'检验检测'关系"),
    "同行对比": (None, "无", "建议图谱增加'同行对比'关系"),
    "区域新闻关联": (None, "无", "建议图谱增加'区域关联'关系"),
    "同行产品列举": (None, "无", "建议图谱增加'产品关联'关系"),
    "同日上市": (None, "无", "建议图谱增加'同日上市'关系"),
    "招标竞标关联": (None, "无", "建议图谱增加'招标竞标'关系"),
}

def get_kg_relation(project_relation):
    """获取项目关系对应的图谱关系"""
    if project_relation in RELATIONSHIP_MAPPING:
        kg_rel, confidence, note = RELATIONSHIP_MAPPING[project_relation]
        return kg_rel, confidence, note
    return None, "无", "未定义映射"

def main():
    # 读取数据
    with open('/home/huyuan/openclaw/front/public/cross_doc_dataset_updated.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    relations = data['relations']

    # 统计原始关系类型
    original_types = {}
    for company1, targets in relations.items():
        for company2, rel_data in targets.items():
            rel_type = rel_data.get('relation', '未知')
            original_types[rel_type] = original_types.get(rel_type, 0) + 1

    print("=" * 70)
    print("项目关系类型到知识图谱关系类型映射")
    print("=" * 70)
    print()

    # 输出映射表
    print("| 项目关系类型 | 数量 | 图谱关系类型 | 置信度 | 说明 |")
    print("|--------------|------|--------------|--------|------|")
    for rel_type, count in sorted(original_types.items(), key=lambda x: -x[1]):
        kg_rel, confidence, note = get_kg_relation(rel_type)
        kg_display = kg_rel if kg_rel else "-"
        print(f"| {rel_type} | {count} | {kg_display} | {confidence} | {note} |")

    print()
    print("=" * 70)
    print("更新数据集...")
    print("=" * 70)

    # 更新关系类型
    updated_count = 0
    new_types_count = {}
    for company1, targets in relations.items():
        for company2, rel_data in targets.items():
            old_type = rel_data.get('relation', '')
            kg_rel, confidence, note = get_kg_relation(old_type)
            if kg_rel:
                rel_data['relation'] = kg_rel
                rel_data['original_relation'] = old_type  # 保留原始关系类型
                rel_data['mapping_confidence'] = confidence
                updated_count += 1
                new_types_count[kg_rel] = new_types_count.get(kg_rel, 0) + 1

    # 输出更新后的统计
    print(f"\n成功映射: {updated_count} 条关系")
    print("\n映射后图谱关系类型分布:")
    for rel_type, count in sorted(new_types_count.items(), key=lambda x: -x[1]):
        print(f"  {rel_type}: {count}条")

    # 保存更新后的数据
    output_file = '/home/huyuan/openclaw/front/public/cross_doc_dataset_kg_mapped.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n已保存映射后数据到: {output_file}")

    # 生成映射报告
    report = []
    report.append("# 关系类型映射报告\n")
    report.append(f"映射时间: 2026-05-14\n")
    report.append(f"\n## 知识图谱关系类型（共{len(KG_RELATIONSHIPS)}种）\n")
    for rel in KG_RELATIONSHIPS:
        report.append(f"- {rel}")

    report.append("\n## 映射统计\n")
    report.append(f"- 原始关系总数: {sum(original_types.values())}条")
    report.append(f"- 成功映射: {updated_count}条")
    report.append(f"- 未映射: {sum(original_types.values()) - updated_count}条（弱关联或建议扩展图谱）")

    report.append("\n## 映射详情\n")
    report.append("| 项目关系类型 | 数量 | 图谱关系类型 | 置信度 | 说明 |")
    report.append("|--------------|------|--------------|--------|------|")
    for rel_type, count in sorted(original_types.items(), key=lambda x: -x[1]):
        kg_rel, confidence, note = get_kg_relation(rel_type)
        kg_display = kg_rel if kg_rel else "-"
        report.append(f"| {rel_type} | {count} | {kg_display} | {confidence} | {note} |")

    report.append("\n## 建议扩展的图谱关系类型\n")
    suggested = set()
    for rel_type, (kg_rel, confidence, note) in RELATIONSHIP_MAPPING.items():
        if kg_rel is None and "建议图谱增加" in note:
            suggested_rel = note.replace("建议图谱增加'", "").replace("'关系", "")
            suggested.add(suggested_rel)
    for s in sorted(suggested):
        report.append(f"- {s}")

    with open('/home/huyuan/openclaw/关系类型映射报告.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print("\n映射报告已保存到: /home/huyuan/openclaw/关系类型映射报告.md")

if __name__ == '__main__':
    main()
