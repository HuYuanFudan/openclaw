import re
import opencc
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertModel, AutoTokenizer
import torch
from .parseror import Parser

bank_mapping = {
    "工行": "中国工商银行",
    "农行": "中国农业银行",
    "中行": "中国银行",
    "建行": "中国建设银行",
    "交行": "交通银行",
    "邮储银行": "中国邮政储蓄银行",
    "招行": "招商银行",
    "民生银行": "中国民生银行",
    "浦发": "浦发银行",
    "中信": "中信银行",
    "光大": "中国光大银行",
    "华夏": "华夏银行",
    "广发": "广发银行",
    "兴业": "兴业银行",
    "平安": "平安银行",
    "恒丰": "恒丰银行",
    "浙商": "浙商银行",
    "渤海": "渤海银行",
    "徽商": "徽商银行",
    "农业银行": "中国农业银行",
    "工商银行": "中国工商银行",
    "建设银行": "中国建设银行",
    "农商行": "农村商业银行",
}

BERT_PATH = r'D:\huggingface_model\bert-base-chinese'
model = BertModel.from_pretrained(BERT_PATH)
tokenizer = AutoTokenizer.from_pretrained(BERT_PATH)
model.eval()


def replace_bank_name(input_str):
    for short_name, full_name in bank_mapping.items():
        input_str = input_str.replace(short_name, full_name)
    return input_str

keywords = ["股份", "有限公司", "集团", "责任", "有限责任公司", "分行", "营业部", "控股", "股权", "投资", "贸易", "市"]

def remove_keywords(input_str):
    pattern = "|".join(map(re.escape, keywords))
    result = re.sub(pattern, "", input_str)
    return result

def move_parentheses_content(input_str):
    pattern = r'[（(](.*?)[）)]'
    matches = re.findall(pattern, input_str)
    result = re.sub(pattern, '', input_str)
    if matches:
        result = ' '.join(matches) + ' ' + result
    return result.strip()

def traditional_to_simplified(input_str):
    converter = opencc.OpenCC('t2s')
    simplified_str = converter.convert(input_str)
    return simplified_str


def pre(str):
    str = traditional_to_simplified(str)
    str = replace_bank_name(str)
    str = move_parentheses_content(str)
    str = remove_keywords(str)
    return str.replace(" ", "")

def is_branch_company(suffix):
    # 定义分公司关键词列表
    branch_keywords = ["分行", "支行", "分公司", "营业部", "办事处", "分部", "分店", "代表处"]

    # 检查 suffix 是否包含任意分公司关键词
    for keyword in branch_keywords:
        if keyword in suffix:
            return True
    return False

def calculate_company_similarity(com1, com2):
    par = Parser()
    parser = par.parse
    company1 = parser(com1)
    company2 = parser(com2)
    print("4")
    industry1 = company1['trade']
    industry2 = company2['trade']

    inputs1 = tokenizer(industry1, return_tensors="pt", padding=True, truncation=True, max_length=128)
    inputs2 = tokenizer(industry2, return_tensors="pt", padding=True, truncation=True, max_length=128)

    with torch.no_grad():
        outputs1 = model(**inputs1)
        outputs2 = model(**inputs2)

    embedding1 = outputs1.pooler_output  # [1, hidden_size]
    embedding2 = outputs2.pooler_output  # [1, hidden_size]

    embedding1 = embedding1.numpy()
    embedding2 = embedding2.numpy()
    industry_sim = cosine_similarity(embedding1, embedding2)[0][0]

    company1_name = company1['brand']
    company2_name = company2['brand']

    # 对公司名称进行编码
    name_similarity  = 0
    if company2_name != '' and company1_name != '':
        inputs1 = tokenizer(company1_name, return_tensors="pt", padding=True, truncation=True, max_length=128)
        inputs2 = tokenizer(company2_name, return_tensors="pt", padding=True, truncation=True, max_length=128)

        # 使用 BERT 计算嵌入
        with torch.no_grad():
            outputs1 = model(**inputs1)
            outputs2 = model(**inputs2)

        # 提取池化后的句向量（BERT 的 [CLS] token 表示）
        embedding1 = outputs1.pooler_output  # [1, hidden_size]
        embedding2 = outputs2.pooler_output  # [1, hidden_size]

        # 转换为 NumPy 格式以便计算余弦相似度
        embedding1 = embedding1.numpy()
        embedding2 = embedding2.numpy()

        # 计算公司名称的余弦相似度
        name_similarity = cosine_similarity(embedding1, embedding2)[0][0]

    if((name_similarity * 80 + industry_sim * 20) > 95):
        return 1
    else:
        return 0

if __name__ == "__main__":
    company1 = "深圳市腾讯科技有限公司"
    company2 = "腾讯"
    par = Parser()
    parser = par.parse
    com1 = parser(company1)
    com2 = parser(company2)
    similarity_score = calculate_company_similarity(com1, com2)
    print(f"公司1: {company1}")
    print(f"公司2: {company2}")
    print(f"匹配相似度分数: {similarity_score:.2f}")