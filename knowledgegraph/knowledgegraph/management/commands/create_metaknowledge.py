# insert_meta_knowledge.py

import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knowledgegraph.settings')  # 替换为你的项目的 settings.py 路径
django.setup()

from knowledgegraph.models import MetaKnowledge  # 替换为你的 MetaKnowledge 模型所在的应用名称

# 示例元知识数据
meta_knowledge_data = [
    {"description": "国际贸易的变动可能对各经济体的商业周期、外国投资等产生显著冲击，从而引发金融市场的风险联动。", "formula": ""},
    {"description": "在受到极端风险冲击时，单个市场金融系统的偿付能力将大幅下滑，并会实施相应的信贷紧缩政策，从而使得风险经由跨境借贷网络传导至相互关联的金融系统。", "formula": ""},
    {"description": "产业链某一环节的负面冲击也会经由产业贸易、纵向并购、资产负债表等途径传导至上下游部门，使得产业链与供应链受阻、中断，进而驱动金融风险的跨行业、跨市场传染。", "formula": ""},
    {"description": "当宏观经济整体趋好时，受抵押物价值上涨、信贷供给趋于宽松等因素影响，资产价格泡沫被大幅推高。而随着经济恶化，大量资金的回撤将使得资产价格泡沫破裂，诱使金融机构抛售资产，引发系统性金融风险。", "formula": ""},
    {"description": "宏观经济的疲软可能放大投资者的恐慌情绪，提高经济政策的不确定性，使得投资者下调预期甚至大量抛售证券，进一步影响金融机构的流动性，甚至引发资本市场剧烈震荡。", "formula": ""},
    {"description": "规模较大的金融机构更偏好采用短期债务融资的方式以获取高额回报，从而大幅提升了机构的风险敞口。", "formula": ""},
    {"description": "影子银行业务使得金融机构、企业间的关联更为紧密，加剧金融系统的复杂性与脆弱性，显著提高了风险传染可能。", "formula": ""}
]

# 插入元知识数据
for data in meta_knowledge_data:
    meta_knowledge = MetaKnowledge(description=data['description'], formula=data['formula'])
    meta_knowledge.save()

print("元知识插入成功！")
