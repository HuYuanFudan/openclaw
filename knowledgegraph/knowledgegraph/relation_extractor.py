import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import requests

class RelationExtractor:
    def __init__(self, dataset_path: str = None, use_ollama: bool = True, ollama_model: str = "qwen3.6:27b"):
        """
        初始化关系抽取器
        
        Args:
            dataset_path: JSON数据集文件路径
            use_ollama: 是否使用Ollama进行关系分类
            ollama_model: Ollama模型名称
        """
        if dataset_path is None:
            dataset_path = Path(__file__).parent.parent.parent / "front" / "public" / "cross_doc_dataset_updated.json"
        
        self.dataset_path = Path(dataset_path)
        self.companies = []
        self.relations = {}
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.ollama_url = "http://localhost:11434/api/generate"
        
        self._load_dataset()
        
        self.relation_types = [
            "起诉", "保荐/承销", "投资/收购", "子公司/控股", "合作", 
            "供应/采购", "减持/增持", "竞争", "高管履历关联", "法律纠纷",
            "IPO审核状态", "监管处罚名单", "行业对比分析", "业绩对比", 
            "公告汇总", "审计机构关联", "环保履约关联", "招标竞标关联",
            "品牌商标关联", "股权转让", "同事件提及"
        ]

    def _load_dataset(self):
        """加载现有的JSON数据集"""
        if self.dataset_path.exists():
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.companies = data.get('companies', [])
                self.relations = data.get('relations', {})
        else:
            self.companies = []
            self.relations = {}

    def _save_dataset(self):
        """保存数据集到JSON文件"""
        data = {
            "companies": self.companies,
            "relations": self.relations
        }
        with open(self.dataset_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def extract_companies(self, text: str) -> List[str]:
        """
        从文本中识别公司名称
        
        Args:
            text: 新闻文本
            
        Returns:
            识别到的公司名称列表
        """
        found_companies = []
        for company in self.companies:
            if company in text:
                found_companies.append(company)
        return list(set(found_companies))

    def _call_ollama(self, prompt: str) -> str:
        """
        调用Ollama进行关系分类
        
        Args:
            prompt: 提示词
            
        Returns:
            模型返回的关系类型
        """
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "max_tokens": 50
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"Ollama请求失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"Ollama调用异常: {str(e)}")
            return None

    def determine_relation(self, text: str, company1: str, company2: str) -> str:
        """
        判定两家公司之间的关系类型
        
        Args:
            text: 新闻文本
            company1: 公司1名称
            company2: 公司2名称
            
        Returns:
            关系类型字符串
        """
        if self.use_ollama:
            return self._determine_relation_with_ollama(text, company1, company2)
        else:
            return self._determine_relation_with_keywords(text)

    def _determine_relation_with_ollama(self, text: str, company1: str, company2: str) -> str:
        """
        使用Ollama进行关系分类
        
        Args:
            text: 新闻文本
            company1: 公司1名称
            company2: 公司2名称
            
        Returns:
            关系类型字符串
        """
        # 构建提示词
        relation_types_str = "\n".join([f"- {rt}" for rt in self.relation_types])
        
        prompt = f"""
        请分析以下新闻文本中两家公司之间的关系，并从给定的关系类型列表中选择最合适的一个。

        新闻文本：
        {text[:1000]}...

        公司A：{company1}
        公司B：{company2}

        关系类型列表：
        {relation_types_str}

        请只返回关系类型名称，不要添加其他解释。
        """
        
        result = self._call_ollama(prompt)
        
        if result and result in self.relation_types:
            return result
        else:
            # 如果Ollama返回无效结果，使用关键词匹配作为备选
            return self._determine_relation_with_keywords(text)

    def _determine_relation_with_keywords(self, text: str) -> str:
        """
        使用关键词匹配进行关系分类（备用方案）
        
        Args:
            text: 新闻文本
            
        Returns:
            关系类型字符串
        """
        relation_keywords = {
            "起诉": ["起诉", "诉讼", "原告", "被告", "索赔", "纠纷", "状告", "控告"],
            "保荐/承销": ["保荐", "承销", "主承销", "承销商", "保荐机构", "核查意见"],
            "投资/收购": ["收购", "入股", "参股", "并购", "投资", "控股", "收购价"],
            "子公司/控股": ["子公司", "控股", "母公司", "全资", "控股子公司"],
            "合作": ["合作", "战略合作", "协议", "签署", "联合", "协同"],
            "供应/采购": ["供应", "采购", "供应商", "客户", "供货", "订单"],
            "减持/增持": ["减持", "增持", "持股", "股权", "股份"],
            "竞争": ["竞争", "竞争对手", "同业", "市场份额"],
            "高管履历关联": ["就职于", "曾任", "兼任", "董事", "高管", "独立董事"],
            "法律纠纷": ["仲裁", "诉讼", "索赔", "原告", "被告"],
            "IPO审核状态": ["IPO", "上会", "过会", "暂缓", "中止", "终止", "被否"],
            "监管处罚名单": ["处罚", "点名", "通报批评", "行政处罚", "飞检"],
            "行业对比分析": ["对比", "领头羊", "可比公司", "市场份额", "行业排名"],
            "业绩对比": ["业绩", "盈利", "市盈率", "营收", "净利润"],
            "公告汇总": ["公告", "日报", "快报", "严选"],
            "审计机构关联": ["审计", "续聘", "会计师", "会所"],
            "环保履约关联": ["环保", "碳市场", "排污", "碳排放"],
            "招标竞标关联": ["招标", "中标", "竞标", "资格预审"],
            "品牌商标关联": ["商标", "品牌", "假冒", "侵权"],
            "股权转让": ["股权转让", "转让", "受让"],
            "同事件提及": ["提及", "涉及", "关于"]
        }
        
        for relation_type, keywords in relation_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return relation_type
        return "同事件提及"

    def extract_evidence(self, text: str, company1: str, company2: str) -> str:
        """
        提取关系证据句
        
        Args:
            text: 新闻文本
            company1: 公司1名称
            company2: 公司2名称
            
        Returns:
            证据句子
        """
        sentences = re.split(r'[。！？；]', text)
        for sentence in sentences:
            if company1 in sentence and company2 in sentence:
                return sentence.strip()
        
        return text[:200] + "..." if len(text) > 200 else text

    def extract_from_news(self, news: Dict) -> List[Dict]:
        """
        从单篇新闻中提取所有公司关系
        
        Args:
            news: 新闻字典，包含 title, source, time, url, abstract, content
            
        Returns:
            关系列表，每个关系包含 company1, company2, relation, evidence, news
        """
        full_text = f"{news.get('title', '')} {news.get('abstract', '')} {news.get('content', '')}"
        found_companies = self.extract_companies(full_text)
        
        results = []
        for i, company1 in enumerate(found_companies):
            for j, company2 in enumerate(found_companies):
                if i != j:
                    relation_type = self.determine_relation(full_text, company1, company2)
                    evidence = self.extract_evidence(full_text, company1, company2)
                    
                    results.append({
                        "company1": company1,
                        "company2": company2,
                        "relation": relation_type,
                        "evidence": evidence,
                        "news": news
                    })
        
        return results

    def add_relation(self, company1: str, company2: str, relation: str, evidence: str, news: Dict):
        """
        添加关系到数据集
        
        Args:
            company1: 公司1名称
            company2: 公司2名称
            relation: 关系类型
            evidence: 证据句
            news: 新闻信息
        """
        if company1 not in self.relations:
            self.relations[company1] = {}
        
        if company2 not in self.relations[company1]:
            self.relations[company1][company2] = {
                "relation": relation,
                "evidence": evidence,
                "news": news
            }
        
        self._save_dataset()

    def add_new_company(self, company_name: str):
        """
        添加新公司到公司列表
        
        Args:
            company_name: 公司名称
        """
        if company_name not in self.companies:
            self.companies.append(company_name)
            self._save_dataset()

    def get_relations_by_company(self, company_name: str) -> Dict:
        """
        获取指定公司的所有关系
        
        Args:
            company_name: 公司名称
            
        Returns:
            关系字典
        """
        return self.relations.get(company_name, {})

    def get_all_relations(self) -> Dict:
        """获取所有关系"""
        return self.relations

    def get_all_companies(self) -> List[str]:
        """获取所有公司"""
        return self.companies