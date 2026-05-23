#!/usr/bin/env python3
"""
测试关系抽取功能
"""
import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledgegraph.relation_extractor import RelationExtractor

def test_extractor():
    print("=== 测试关系抽取器 ===")
    
    # 初始化抽取器
    extractor = RelationExtractor()
    
    # 测试1: 获取公司列表
    companies = extractor.get_all_companies()
    print(f"1. 公司列表长度: {len(companies)}")
    print(f"   前5家公司: {companies[:5]}")
    
    # 检查数据集中存在的公司
    test_companies = ['科大讯飞股份有限公司', '爱尔眼科医院集团股份有限公司', '华厦眼科医院集团股份有限公司']
    print("\n2. 检查测试公司是否在列表中:")
    for company in test_companies:
        exists = company in companies
        print(f"   {'✓' if exists else '✗'} {company}")
    
    # 测试3: 从新闻中提取关系（使用数据集中已存在的公司）
    test_news = {
        "title": "爱尔眼科与华厦眼科行业对比分析报告",
        "source": "新浪财经",
        "time": "2025-10-18 12:33",
        "url": "https://finance.sina.com.cn/article/xxx",
        "abstract": "作为行业领头羊，爱尔眼科医院集团与华厦眼科医院集团在不断扩大业务版图的同时，也频频展示其社会责任担当。",
        "content": "中国眼科医疗市场近年来蓬勃发展，其中民营眼科医院的发展尤为迅速。作为行业领头羊，爱尔眼科医院集团股份有限公司（以下简称爱尔眼科）与华厦眼科医院集团股份有限公司（以下简称华厦眼科）在不断扩大业务版图的同时，也频频展示其社会责任担当。两家公司经常被作为可比公司进行行业对比分析。"
    }
    
    print("\n3. 测试新闻关系提取:")
    print(f"   新闻标题: {test_news['title']}")
    
    relations = extractor.extract_from_news(test_news)
    
    if relations:
        print(f"   提取到 {len(relations)} 条关系:")
        for i, rel in enumerate(relations, 1):
            print(f"   [{i}] {rel['company1']} -> {rel['relation']} -> {rel['company2']}")
            print(f"      证据: {rel['evidence']}")
    else:
        print("   未提取到关系")
    
    # 测试4: 添加关系
    print("\n4. 测试添加关系:")
    try:
        extractor.add_relation(
            company1="爱尔眼科医院集团股份有限公司",
            company2="华厦眼科医院集团股份有限公司",
            relation="行业对比分析",
            evidence="作为行业领头羊，爱尔眼科与华厦眼科经常被作为可比公司进行对比",
            news=test_news
        )
        print("   ✓ 关系添加成功")
    except Exception as e:
        print(f"   ✗ 添加失败: {e}")
    
    # 测试5: 查询关系
    print("\n5. 测试查询关系:")
    rels = extractor.get_relations_by_company("爱尔眼科医院集团股份有限公司")
    if rels:
        print(f"   爱尔眼科的关系数量: {len(rels)}")
        for target_company, info in rels.items():
            print(f"   - {target_company}: {info['relation']}")
    else:
        print("   未查询到关系")
    
    # 测试6: 添加新公司
    print("\n6. 测试添加新公司:")
    new_company = "华为技术有限公司"
    if new_company not in companies:
        extractor.add_new_company(new_company)
        print(f"   ✓ 新公司 '{new_company}' 添加成功")
        print(f"   公司列表更新后长度: {len(extractor.get_all_companies())}")
    else:
        print(f"   公司 '{new_company}' 已存在")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_extractor()