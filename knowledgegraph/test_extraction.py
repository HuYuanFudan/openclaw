# -*- coding: utf-8 -*-
"""抽取 Prompt 实测：本地 Ollama qwen3:32b"""
import json
import requests
from knowledgegraph.extraction_prompt import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt, VALID_LABELS, VALID_RELATIONS

TEXT_1 = (
    "2024年3月，万科企业股份有限公司公告称，其全资子公司万科物流发展有限公司"
    "向中国建设银行股份有限公司深圳分行申请流动资金贷款人民币5亿元，万科企业股份有限公司"
    "为上述借款提供连带责任保证担保，担保期限不超过3年。此外，公司控股股东深圳市地铁集团有限公司"
    "质押其所持有的万科A股股份2亿股用于融资。万科企业股份有限公司注册于广东省深圳市，"
    "旗下A股证券简称为万科A、B股证券简称为万科B。"
)

TEXT_2 = (
    "根据深圳市中级人民法院公告，恒大地产集团有限公司因建设工程施工合同纠纷起诉深圳市钜盛华股份有限公司，"
    "涉案金额1.2亿元，本案尚在一审审理中。另据深交所监管函，深圳市钜盛华股份有限公司因未及时披露"
    "重大诉讼事项构成信息披露重大遗漏，被深圳证券交易所出具监管函。"
)

def extract(text):
    resp = requests.post('http://localhost:11434/api/chat', json={
        'model': 'qwen3:32b',
        'messages': [
            {'role': 'system', 'content': EXTRACTION_SYSTEM_PROMPT},
            {'role': 'user', 'content': build_extraction_prompt(text)},
        ],
        'stream': False,
        'format': 'json',
        'options': {'temperature': 0.1, 'num_ctx': 8192},
    }, timeout=600)
    data = resp.json()
    content = data['message']['content']
    return json.loads(content), data.get('eval', {})

def validate(result):
    """校验封闭词表"""
    errs = []
    labels = set(VALID_LABELS)
    rels = set(VALID_RELATIONS)
    for e in result.get('entities', []):
        if e.get('label') not in labels:
            errs.append(f"非法标签: {e.get('label')} ({e.get('name')})")
    for r in result.get('relations', []):
        if r.get('type') not in rels:
            errs.append(f"非法关系: {r.get('type')}")
        ids = {e['id'] for e in result.get('entities', [])}
        if r.get('from') not in ids or r.get('to') not in ids:
            errs.append(f"关系引用不存在的实体: {r.get('from')}->{r.get('to')}")
    return errs

for i, text in enumerate([TEXT_1, TEXT_2], 1):
    print(f'===== 文本{i} =====')
    print(text[:80], '...')
    result, stats = extract(text)
    errs = validate(result)
    print(f"实体 {len(result.get('entities', []))} 个, 关系 {len(result.get('relations', []))} 个, "
          f"耗时 {stats.get('total_duration', 0)/1e9:.1f}s")
    print('实体:')
    for e in result.get('entities', []):
        print(f"  [{e['id']}] {e.get('label')}: {e['name']} {e.get('props') or ''}")
    print('关系:')
    for r in result.get('relations', []):
        print(f"  {r['from']} -[{r['type']}]-> {r['to']}  {r.get('props') or ''}")
    print('校验:', '全部通过' if not errs else errs)
    print()
