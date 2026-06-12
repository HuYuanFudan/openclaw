#!/usr/bin/env python3
"""从详细报告中抽取核心违规类型，做归一化映射"""
import json

with open('/home/huyuan/openclaw/kg_detailed_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 违规类型归一化
def normalize_violation_type(t):
    """把复合违规类型归一化到核心类别"""
    # 去除重复的"其他"等
    parts = [p.strip() for p in t.replace(';', '、').split('、') if p.strip() and p.strip() != '其他']
    if not parts:
        return '其他'
    # 取出最核心的非"其他"类型
    return parts[0]

# 归一化
normalized = {}
for t, c in data['violation_types'].items():
    norm = normalize_violation_type(t)
    normalized[norm] = normalized.get(norm, 0) + c

normalized_sorted = dict(sorted(normalized.items(), key=lambda x: -x[1]))
print("归一化违规类型 TOP 20:")
for i, (k, v) in enumerate(list(normalized_sorted.items())[:20], 1):
    print(f"  {i}. {k}: {v}")

# 保留 TOP 10 作为可视化
top_violation = list(normalized_sorted.items())[:10]
data['violation_types_top10'] = top_violation

# 原告-被告行业关联矩阵 TOP 10
top_matrix = sorted(data['plaintiff_defendant_matrix'], key=lambda x: -x['count'])[:15]
data['top_plaintiff_defendant_pairs'] = top_matrix
print(f"\n原告-被告行业关联 TOP 5:")
for m in top_matrix[:5]:
    print(f"  {m['plaintiff_industry']} -> {m['defendant_industry']}: {m['count']}")

# 高风险公司
data['high_risk_top10'] = data['high_risk_companies'][:10]

with open('/home/huyuan/openclaw/kg_detailed_report.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n精简完成")
