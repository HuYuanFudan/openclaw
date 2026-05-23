#!/usr/bin/env python3
"""
测试使用Ollama进行关系抽取
"""
import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledgegraph.relation_extractor import RelationExtractor

def read_test_news(file_path):
    """读取测试新闻文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析新闻内容
    lines = content.strip().split('\n')
    
    news = {
        "title": lines[0] if lines else "",
        "source": "上交所股票",
        "time": lines[1].split()[0] if len(lines) > 1 else "",
        "url": "https://example.com/news",
        "abstract": lines[2] if len(lines) > 2 else "",
        "content": "\n".join(lines[4:]) if len(lines) > 4 else ""
    }
    
    return news

def test_with_ollama():
    print("=== 测试使用Ollama进行关系抽取 ===")
    print(f"日期: 2026-05-21")
    print()
    
    # 初始化抽取器（使用Ollama）
    extractor = RelationExtractor(use_ollama=True, ollama_model="qwen3.6:27b")
    
    # 获取公司列表
    companies = extractor.get_all_companies()
    print(f"1. 预定义公司列表长度: {len(companies)}")
    
    # 读取测试新闻
    news_path = "/home/huyuan/openclaw/lsydata/data/financedata/test.md"
    print(f"\n2. 读取测试新闻: {news_path}")
    news = read_test_news(news_path)
    print(f"   标题: {news['title']}")
    print(f"   来源: {news['source']}")
    print(f"   时间: {news['time']}")
    print(f"   摘要: {news['abstract'][:100]}...")
    
    # 提取公司
    full_text = f"{news['title']} {news['abstract']} {news['content']}"
    found_companies = extractor.extract_companies(full_text)
    print(f"\n3. 识别到的公司:")
    for company in found_companies:
        print(f"   ✓ {company}")
    
    # 提取关系
    print(f"\n4. 提取公司关系（使用Ollama模型）:")
    relations = extractor.extract_from_news(news)
    
    if relations:
        print(f"   共提取到 {len(relations)} 条关系:")
        for i, rel in enumerate(relations, 1):
            print(f"\n   [{i}]")
            print(f"      公司A: {rel['company1']}")
            print(f"      公司B: {rel['company2']}")
            print(f"      关系类型: {rel['relation']}")
            print(f"      证据: {rel['evidence']}")
            
            # 保存关系
            extractor.add_relation(
                company1=rel['company1'],
                company2=rel['company2'],
                relation=rel['relation'],
                evidence=rel['evidence'],
                news=rel['news']
            )
            print(f"      ✓ 已保存到数据集")
    else:
        print("   未提取到关系")
    
    # 查询验证
    print("\n5. 查询验证:")
    for company in found_companies:
        rels = extractor.get_relations_by_company(company)
        if rels:
            print(f"   {company} 的关系:")
            for target, info in rels.items():
                print(f"      - {target}: {info['relation']}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_with_ollama()