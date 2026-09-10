from py2neo import Graph, NodeMatcher, Node, Relationship, RelationshipMatcher
from django.http import JsonResponse, HttpResponse, FileResponse
import json
import os
import threading
import time
import pandas as pd
from io import BytesIO
import io
from django.core.cache import cache
from datetime import datetime
from django.views.decorators.http import require_GET
# from .companynameparser.namematcher import calculate_company_similarity
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework import status
from .serializers import MetaKnowledgeSerializer
from rest_framework import viewsets
from django.shortcuts import render
from .relation_extractor import RelationExtractor

# 初始化关系抽取器
extractor = RelationExtractor()

def index(request):
    return render(request, 'index.html')

from .models import MetaKnowledge, Formula, Variable, FormulaVariable
from .decorators import neo4j_user_required
from .permissions import IsMetaKnowledgeUser
import xlsxwriter
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .permissions import IsNeo4jUser
from django.db import transaction
from rest_framework.decorators import action

graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))
matcher = NodeMatcher(graph)

# graph = Graph("neo4j://localhost:7687", auth=("neo4j", "1598273166wsy."))
matcher = NodeMatcher(graph)
rmatcher = RelationshipMatcher(graph)

# ============================================================
# 本地元知识数据：新一批元知识暂不导入图谱，直接从 jsonl 文件读取，
# 与图谱中的 MetaKnowledge 节点一起支撑"图谱金融风险知识"页面。
# ============================================================
LOCAL_META_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'metaknowledge', 'metaknowledge.jsonl'
)

_local_meta_cache = {'mtime': None, 'data': []}

def get_local_metaknowledge():
    """读取本地 metaknowledge.jsonl 全部元知识（按文件修改时间缓存）"""
    try:
        if not os.path.exists(LOCAL_META_PATH):
            return []
        mtime = os.path.getmtime(LOCAL_META_PATH)
        if _local_meta_cache['mtime'] != mtime:
            items = []
            with open(LOCAL_META_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            _local_meta_cache['mtime'] = mtime
            _local_meta_cache['data'] = items
        return _local_meta_cache['data']
    except Exception as e:
        print(f"读取本地元知识失败: {e}")
        return []

def match_local_metaknowledge(keywords):
    """返回"核心结论"命中任一关键词的本地元知识列表"""
    if not keywords:
        return get_local_metaknowledge()
    return [
        m for m in get_local_metaknowledge()
        if any(kw in (m.get('核心结论') or '') for kw in keywords)
    ]

chinese_to_english = {
    "公司中文名称": "company_name",
    "社会信用代码": "credit_number",
    "省份": "province",
    "公司类型": "company_type",
    "市": "city",
    "区县信息": "district_info",
    "主营业务": "main_business",
    "A股证券代码": "a_stock_code",
    "组织形式": "organization_form",
    "证券名称": "security_name",
    "股票简称": "stock_abbreviation",
    "证券代码": "security_code",
    "董事会秘书代码": "board_secretary_code",
    "经营范围": "business_scope",
    "注册地址": "registered_address",
    "法定代表人": "legal_representative",
    "公司曾用名": "former_company_name",
    "公司电话": "company_phone",
    "公司简介": "company_profile",
    "英文名称": "english_name",
    "B股证券代码": "b_stock_code",
    "实际控制人": "actual_controller",
}

english_to_chinese = {v: k for k, v in chinese_to_english.items()}
def translate_labels(data, to_english=True):
    if to_english:
        return {chinese_to_english.get(k, k): v for k, v in data.items()}
    else:
        return {english_to_chinese.get(k, k): v for k, v in data.items()}
def create_company(data):
    graph.run("""
        CREATE (c:Company {
            `公司中文名称`: $company_name,
            `社会信用代码`: $credit_number,
            `省份`: $province,
            `公司类型`: $company_type,
            `市`: $city,
            `区县信息`: $district_info,
            `主营业务`: $main_business,
            `A股证券代码`: $a_stock_code,
            `组织形式`: $organization_form,
            `证券名称`: $security_name,
            `股票简称`: $stock_abbreviation,
            `证券代码`: $security_code,
            `董事会秘书代码`: $board_secretary_code,
            `经营范围`: $business_scope,
            `注册地址`: $registered_address,
            `法定代表人`: $legal_representative,
            `公司曾用名`: $former_company_name,
            `公司电话`: $company_phone,
            `公司简介`: $company_profile,
            `英文名称`: $english_name,
            `B股证券代码`: $b_stock_code,
            `实际控制人`: $actual_controller
        })
    """, **data)
class MyTokenObtainPairView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            
            if not username or not password:
                return Response(
                    {'error': 'Username and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = authenticate(username=username, password=password)

            if user is None:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def Querynodes(data):
    query_conditions = []
    for condition in data:
        label = condition['label']
        value = condition['value']
        if label == "company_name" and value:
            query_conditions.append(f"coalesce(n.公司中文名称, '') CONTAINS '{value}'")
        elif label == "credit_number" and value:
            query_conditions.append(f"coalesce(n.社会信用代码, '') CONTAINS '{value}'")
        elif label == "english_name" and value:
            query_conditions.append(f"coalesce(n.英文名称, '') CONTAINS '{value}'")
        elif label == "legal_representative" and value:
            query_conditions.append(f"coalesce(n.法定代表人, '') CONTAINS '{value}'")
        elif label == "security_code" and value:
            query_conditions.append(f"coalesce(n.证券代码, '') CONTAINS '{value}'")
        elif label == "stock_abbreviation" and value:
            query_conditions.append(f"coalesce(n.股票简称, '') CONTAINS '{value}'")

    if not query_conditions:
        return {"message": "至少提供一个查询条件"}
    query_condition_str = " AND ".join(query_conditions)
    query = f"MATCH (n:Company) WHERE {query_condition_str} RETURN n"
    result = graph.run(query).data()
    if result:
        company_results = []
        for record in result:
            company_info = record['n']
            company_results.append({
                "company_name": company_info.get('公司中文名称', ''),
                "credit_number": company_info.get('社会信用代码', ''),
            })
        return company_results
    else:
        return {"message": "未找到符合条件的公司"}
# 关系类型中文到英文的映射（数据库中存在的关系类型：所属城市, 拥有公司, A股证券_公司资料, 违规事件, 子公司, B股证券_公司资料, GUARANTEES, PLEDGE, 港股证券_公司资料, 客户, 供应商, 诉讼仲裁, 起诉）
relation_cn_to_en = {
    '质押': 'PLEDGE',
    '担保': 'GUARANTEES',
    '诉讼仲裁': '诉讼仲裁',
    '客户': '客户',
    '供应商': '供应商',
    '子公司': '子公司',
    '起诉': '起诉',
    '违规事件': '违规事件',
    '拥有公司': '拥有公司',
    '所属城市': '所属城市',
}

def normalize_company_name(name):
    """
    规范化公司名称：统一公司名称格式，去除冗余后缀
    """
    if not name:
        return name
    
    # 处理重复的"有限公司"，如"有限公司公司" -> "有限公司"
    name = name.replace('有限公司公司', '有限公司')
    # 处理"股份有限公司公司" -> "股份有限公司"
    name = name.replace('股份有限公司公司', '股份有限公司')
    
    # 统一公司类型后缀
    name = name.replace('有限责任公司', '有限公司')
    name = name.replace('股份公司', '股份有限公司')
    name = name.replace('责任公司', '有限公司')
    
    # 去除多余的空格和标点
    name = name.strip()
    name = name.replace('　', '')  # 去除全角空格
    
    return name

def find_company_nodes(keyword):
    """
    根据关键词查找公司节点（支持模糊匹配）
    返回匹配的公司节点列表
    """
    # 规范化关键词，处理重复后缀
    keyword = normalize_company_name(keyword)
    
    # 判断是社会信用代码还是公司名称
    is_credit = len(keyword) == 18 and keyword.isdigit()
    
    if is_credit:
        query = f"MATCH (n:Company) WHERE n.`社会信用代码` = '{keyword}' RETURN n LIMIT 10"
    else:
        # 优先精确匹配，再模糊匹配
        query = f"""
            MATCH (n:Company) 
            WHERE n.`公司中文名称` = '{keyword}' 
               OR n.`公司中文名称` CONTAINS '{keyword}'
               OR n.`公司曾用名` CONTAINS '{keyword}'
               OR '{keyword}' CONTAINS n.`公司中文名称`
            RETURN n 
            ORDER BY CASE WHEN n.`公司中文名称` = '{keyword}' THEN 0 ELSE 1 END
            LIMIT 10
        """
    
    result = graph.run(query).data()
    return [record['n'] for record in result]

def QueryRelationship(node1, node2, relationship=None):
    """
    查询两个公司之间的关系（支持模糊匹配和无关系类型查询）
    node1, node2: 公司中文名称或社会信用代码
    relationship: 关系类型（可选，为空时查询所有关系）
    """
    print(f"[QueryRelationship] 开始查询 - 公司1: '{node1}', 公司2: '{node2}', 关系类型: '{relationship}'")
    
    # 关系类型中文转英文
    if relationship and relationship in relation_cn_to_en:
        print(f"[QueryRelationship] 关系类型映射: {relationship} -> {relation_cn_to_en[relationship]}")
        relationship = relation_cn_to_en[relationship]
    
    # 判断是否为社会信用代码
    is_credit1 = len(node1) == 18 and node1.isdigit()
    is_credit2 = len(node2) == 18 and node2.isdigit()
    
    relationships = []
    seen = set()  # 去重
    
    # 构建查询条件
    if is_credit1 and is_credit2:
        # 两个都是信用代码
        query = f"""
            MATCH (c1:Company)-[r]-(c2:Company) 
            WHERE (c1.`社会信用代码` = '{node1}' AND c2.`社会信用代码` = '{node2}')
               OR (c1.`社会信用代码` = '{node2}' AND c2.`社会信用代码` = '{node1}')
            RETURN type(r) as relationship_type, c1, c2, r
        """
    elif is_credit1:
        # 公司1是信用代码，公司2是名称
        query = f"""
            MATCH (c1:Company)-[r]-(c2:Company) 
            WHERE c1.`社会信用代码` = '{node1}' 
              AND (c2.`公司中文名称` CONTAINS '{node2}' OR '{node2}' CONTAINS c2.`公司中文名称`)
            RETURN type(r) as relationship_type, c1, c2, r
            UNION ALL
            MATCH (c1:Company)-[r]-(c2:Company) 
            WHERE c2.`社会信用代码` = '{node1}' 
              AND (c1.`公司中文名称` CONTAINS '{node2}' OR '{node2}' CONTAINS c1.`公司中文名称`)
            RETURN type(r) as relationship_type, c1, c2, r
        """
    elif is_credit2:
        # 公司2是信用代码，公司1是名称
        query = f"""
            MATCH (c1:Company)-[r]-(c2:Company) 
            WHERE c2.`社会信用代码` = '{node2}' 
              AND (c1.`公司中文名称` CONTAINS '{node1}' OR '{node1}' CONTAINS c1.`公司中文名称`)
            RETURN type(r) as relationship_type, c1, c2, r
            UNION ALL
            MATCH (c1:Company)-[r]-(c2:Company) 
            WHERE c1.`社会信用代码` = '{node2}' 
              AND (c2.`公司中文名称` CONTAINS '{node1}' OR '{node1}' CONTAINS c2.`公司中文名称`)
            RETURN type(r) as relationship_type, c1, c2, r
        """
    else:
        # 两个都是公司名称，使用模糊匹配
        query = f"""
            MATCH (c1:Company)-[r]-(c2:Company) 
            WHERE (c1.`公司中文名称` CONTAINS '{node1}' OR '{node1}' CONTAINS c1.`公司中文名称`)
              AND (c2.`公司中文名称` CONTAINS '{node2}' OR '{node2}' CONTAINS c2.`公司中文名称`)
              AND c1 <> c2
            RETURN type(r) as relationship_type, c1, c2, r
        """
    
    print(f"[QueryRelationship] 执行查询: {query[:200]}...")
    try:
        result = graph.run(query).data()
        print(f"[QueryRelationship] 查询结果: {len(result)} 条")
        
        for record in result:
            c1 = record['c1']
            c2 = record['c2']
            rel = record['r']
            rel_type = record['relationship_type']
            
            # 去重
            key = tuple(sorted([c1.get('社会信用代码', ''), c2.get('社会信用代码', '')])) + (rel_type,)
            if key in seen:
                continue
            seen.add(key)
            
            print(f"[QueryRelationship] 找到关系: {c1.get('公司中文名称', '')} -{rel_type}-> {c2.get('公司中文名称', '')}")
            
            relationships.append({
                'start_node': {
                    'company_name': c1.get('公司中文名称', ''),
                    'credit_number': c1.get('社会信用代码', '')
                },
                'end_node': {
                    'company_name': c2.get('公司中文名称', ''),
                    'credit_number': c2.get('社会信用代码', '')
                },
                'relation_type': rel_type,
                'attributes': dict(rel)
            })
    except Exception as e:
        print(f"[QueryRelationship] 查询异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"[QueryRelationship] 查询完成，共找到 {len(relationships)} 条关系")
    return relationships
def QueryRelationship_byname(node1, node2, relationship):
    query = ''
    if relationship:
        query = f"MATCH (c1:Company)-[r:{relationship}]->(c2:Company) WHERE c1.`公司中文名称` = '{node1}' AND c2.`公司中文名称` = '{node2}' RETURN type(r) as relationship_type, r"
    else:
        query = f"MATCH (c1:Company)-[r]->(c2:Company) WHERE c1.`公司中文名称` = '{node1}' AND c2.`公司中文名称` = '{node2}' RETURN type(r) as relationship_type, r"
    result = graph.run(query)
    relationships = []
    for record in result:
        relationship_type = record["relationship_type"]
        relationship_properties = dict(record["r"])
        relationships.append({
            "type": relationship_type,
            "properties": relationship_properties
        })
    if relationships:
        return True
    else:
        return False
def QueryRelationship_withnonode(relation_name):
    query = f"MATCH ()-[r:{relation_name}]->()  RETURN type(r) as relationship_type, r LIMIT 1"
    result = graph.run(query).data()
    relationship = str(result[0]['r'])
    # relationships = []
    # for record in result:
    #     relationship_type = record["relationship_type"]
    #     relationship_properties = dict(record["r"])
    #     relationships.append({
    #         "type": relationship_type,
    #         "properties": relationship_properties
    #     })
    return relationship.__str__().encode("utf-8").decode("unicode_escape")

def query_node(request):
    if request.method == 'POST':
        dat = json.loads(request.body)
        nodes = Querynodes(dat)
        if nodes:
            return JsonResponse(nodes, safe=False)
        else:
            return JsonResponse({'status': 'error', 'message': '未找到符合条件的公司'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
def print_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(type(data))
        print(data)
        return JsonResponse({'status': 'success', 'message': 'Node added'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
class AddNodeView(APIView):
    permission_classes = []
    def post(self, request):
        try:
            print(request.user.user_type)
        except AttributeError:
            pass
        try:
            data = json.loads(request.body)
            credit_number = data["credit_number"]
            # 使用参数化查询替代字符串拼接，提升性能并防止注入
            result = graph.run(
                "MATCH (c:Company) WHERE c.`社会信用代码`=$code RETURN c LIMIT 1",
                code=credit_number
            ).data()
            node = result[0]['c'] if result else None
            if not node:
                create_company(data)
                return JsonResponse({'status': 'success', 'message': 'Node added'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Node existed'})
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'status': 'error', 'message': 'Invalid data format'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    def get(self, request):
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
def add_node(request):
    if request.method == 'POST':
        print(request.user)
        print(request.user.user_type)
        data = json.loads(request.body)
        credit_number = data["credit_number"]
        # 使用参数化查询替代字符串拼接，提升性能并防止注入
        result = graph.run(
            "MATCH (c:Company) WHERE c.`社会信用代码`=$code RETURN c LIMIT 1",
            code=credit_number
        ).data()
        node = result[0]['c'] if result else None
        if not node:
            create_company(data)
        else:
            JsonResponse({'status': 'error', 'message': 'Node existed'})
        return JsonResponse({'status': 'success', 'message': 'Node added'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
class DeleteNodeView(APIView):
    permission_classes = []
    def post(self, request):
        try:
            data = request.data
            credit_number = data.get('credit_number')
            print(credit_number)
            if not credit_number:
                return Response(
                    {'status': 'error', 'message': 'Missing credit_number'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # 使用参数化查询替代字符串拼接，提升性能并防止注入
            result = graph.run(
                "MATCH (c:Company) WHERE c.`社会信用代码`=$code RETURN c LIMIT 1",
                code=credit_number
            ).data()
            node = result[0]['c'] if result else None
            if node:
                graph.delete(node)
                return Response(
                    {'status': 'success', 'message': 'delete successful'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'status': 'error', 'message': '没有此节点'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def get(self, request):
        return Response(
            {'status': 'error', 'message': 'Invalid request method'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
class AddNodeExcelView(APIView):
    permission_classes = []
    def post(self, request):
        if request.FILES:
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file, keep_default_na=False)
                df_unique = df.drop_duplicates()
                total_rows = len(df_unique)
                existing_nodes = []
                for index, row in df_unique.iterrows():
                    company_name = row['公司中文名称']
                    # 使用参数化查询替代字符串拼接，提升性能并防止注入
                    result = graph.run(
                        "MATCH (c:Company) WHERE c.`公司中文名称`=$name RETURN c LIMIT 1",
                        name=company_name
                    ).data()
                    node = result[0]['c'] if result else None
                    if not node:
                        company_node = Node("Company", **row.to_dict())
                        graph.create(company_node)
                    else:
                        existing_nodes.append(row.to_dict())
                    progress = int((index + 1) / total_rows * 100)
                    cache.set('task_progress', progress)
                if existing_nodes:
                    return JsonResponse({
                        'status': 'success',
                        'message': f'{len(existing_nodes)} 节点已存在，未添加。',
                        'existing_nodes': existing_nodes
                    })
                else:
                    return JsonResponse({'status': 'success', 'message': '所有节点已成功添加'})
            except Exception as e:
                print(f"Error: {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
class AddRelationshipExcelView(APIView):
    permission_classes = []
    def post(self, request):
        relationship_name = request.POST.get("relationship_name")
        file = request.FILES.get('file')

        if not file:
            return JsonResponse({'status': 'error', 'message': '文件错误'})
        try:
            df = pd.read_excel(file)
            total_rows = len(df)
            columns = df.columns
            failed_data = []
            id = 0
            for index, row in df.iterrows():
                id += 1
                company1 = row[columns[0]]
                company2 = row[columns[1]]
                relationship_properties = {
                    col: row[col] for col in columns[2:]
                }
                # 使用参数化查询替代字符串拼接，提升性能并防止注入
                result1 = graph.run(
                    "MATCH (c:Company) WHERE c.`公司中文名称`=$name RETURN c LIMIT 1",
                    name=company1
                ).data()
                node1 = result1[0]['c'] if result1 else None
                result2 = graph.run(
                    "MATCH (c:Company) WHERE c.`公司中文名称`=$name RETURN c LIMIT 1",
                    name=company2
                ).data()
                node2 = result2[0]['c'] if result2 else None
                if node2 and node1:
                    if not QueryRelationship_byname(company1, company2, relationship_name):
                        relationship = Relationship(node1, relationship_name, node2, **relationship_properties)
                        graph.create(relationship)
                else:
                    failed_data.append({
                        "公司1": company1,
                        "公司2": company2,
                        **relationship_properties
                    })
                progress = int((id / total_rows) * 100)
                cache.set('task_progress', progress)
            if failed_data:
                return JsonResponse({
                    'status': 'partial_success',
                    'message': '某些关系未成功添加，可能因为节点不在知识图谱中！',
                    'failed_data': failed_data
                })
            else:
                return JsonResponse({'status': 'success', 'message': '所有关系都已经成功添加'})
        except Exception as e:
            print("Error processing request:", e)
            return JsonResponse({"error": "Failed to process file"}, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        return JsonResponse({'status': 'error', 'message': 'try again'}, status=status.HTTP_400_BAD_REQUEST)
def query_relationship(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            relation_name = data.get('relation_name', '').strip() or None
            company1_data = data.get('company1', [])
            company2_data = data.get('company2', [])
            
            print(f"[query_relationship] 收到请求 - company1: {company1_data}, company2: {company2_data}, relation_name: {relation_name}")
            
            if not company1_data or not company2_data:
                return JsonResponse({'status': 'error', 'message': '请输入两个公司信息'}, status=400)
            
            # 获取公司1的查询值（名称或信用代码）
            label1 = company1_data[0]['label']
            value1 = company1_data[0]['value']
            
            # 获取公司2的查询值（名称或信用代码）
            label2 = company2_data[0]['label']
            value2 = company2_data[0]['value']
            
            # 调用QueryRelationship查询关系（支持模糊匹配）
            relation_data = QueryRelationship(value1, value2, relation_name)
            
            if not relation_data:
                print(f"[query_relationship] 未找到关系 - 公司1: {value1}, 公司2: {value2}, 关系: {relation_name}")
                return JsonResponse({'status': 'success', 'relationships': [], 'message': '未找到两个公司之间的关系'})
            else:
                print(f"[query_relationship] 成功: 找到 {len(relation_data)} 条关系数据")
                return JsonResponse({'status': 'success', 'relationships': relation_data})
        except Exception as e:
            print(f"[query_relationship] 异常错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'}, status=500)
    print(f"[query_relationship] 错误: 无效的请求方法")
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
def qynodedtil(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            credit_number = data.get('credit_number')
            if not credit_number:
                return JsonResponse({'status': 'error', 'message': '社会信用代码不能为空'}, status=400)
            query = f"""
            MATCH (n:Company)
            WHERE n.社会信用代码 = '{credit_number}'
            RETURN n
            """
            result = graph.run(query).data()
            if result:
                company_info = result[0]['n']
                company_details = {
                    'company_name': company_info.get('公司中文名称', ''),
                    'credit_number': company_info.get('社会信用代码', ''),
                    'english_name': company_info.get('英文名称', ''),
                    'legal_representative': company_info.get('法定代表人', ''),
                    'security_code': company_info.get('证券代码', ''),
                    'stock_abbreviation': company_info.get('股票简称', ''),
                }
                return JsonResponse(company_details)
            else:
                return JsonResponse({'status': 'error', 'message': '未找到该公司'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': '无效请求'}, status=400)

def format_relationship_data(relation_data):
    formatted_data = []
    for rel in relation_data:
        start_node = rel.start_node
        end_node = rel.end_node
        relation_type = rel.type
        attributes = rel.attributes
        formatted_data.append({
            'start_node': {
                'id': start_node.id,
                'company_name': start_node['公司中文名称'],
                'credit_number': start_node['社会信用代码']
            },
            'end_node': {
                'id': end_node.id,
                'company_name': end_node['公司中文名称'],
                'credit_number': end_node['社会信用代码']
            },
            'relation_type': relation_type,
            'attributes': attributes
        })

    return formatted_data
def query_node_excel(request):
    if request.method == 'POST' and request.FILES:
        excel_file = request.FILES['file']
        try:
            df = pd.read_excel(excel_file, keep_default_na=False)
            if df.columns[0] != "公司中文名称":
                return JsonResponse({'status': 'error', 'message': 'Invalid file format'}, status=400)
            # 使用参数化查询替代字符串拼接，提升性能并防止注入
            def check_company_exists(company_name):
                result = graph.run(
                    "MATCH (c:Company) WHERE c.`公司中文名称`=$name RETURN c LIMIT 1",
                    name=company_name
                ).data()
                return "是" if result else "否"
            
            df["公司是否在知识图谱中"] = [
                check_company_exists(company)
                for company in df["公司中文名称"]
            ]
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Company Status")
            output.seek(0)
            response = HttpResponse(
                output,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="公司查询结果.xlsx"'
            response["status"] = "success"
            response["message"] = "查询成功"
            return response
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
# def compare_name(request):
#     if request.method == 'POST' and request.FILES:
#         excel_file = request.FILES['file']
#         df = pd.read_excel(excel_file, sheet_name="Sheet1", keep_default_na=False)
#         company1 = df.iloc[:, 0]
#         company2 = df.iloc[:, 1]
#         results = []
#         for com1, com2 in zip(company1, company2):
#             result = calculate_company_similarity(com1, com2)
#             results.append('是' if result == 1 else '否')
#         if len(results) == len(df):
#             df['对比结果'] = results
#         excel_buffer = BytesIO()
#         df.to_excel(excel_buffer, index=False)
#         excel_buffer.seek(0)
#         response = HttpResponse(
#             excel_buffer,
#             content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#         )
#         response['Content-Disposition'] = 'attachment; filename=对比结果.xlsx'
#         response["status"] = "success"
#         response["message"] = "查询成功"
#         return response
#     return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
@require_GET
def getprogress(request):
    progress = cache.get('task_progress', 0)
    return JsonResponse({'progress': progress})
def fmatexcel(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            company_name = body.get('companyName', '').strip()
            if not company_name:
                return JsonResponse({'status': 'error', 'message': '公司名称不能为空'}, status=400)
            query = """
            MATCH (n:Company)
            WHERE coalesce(n.`公司中文名称`, '') CONTAINS $keyword
               OR coalesce(n.`公司曾用名`, '') CONTAINS $keyword
            RETURN n
            """
            result = graph.run(query, keyword=company_name).data()
            if not result:
                return JsonResponse({'status': 'error', 'message': '未找到匹配的公司'}, status=400)

            rows = [item['n'] for item in result]
            df = pd.DataFrame(rows)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Companies')
            output.seek(0)
            response = HttpResponse(output.read(),
                                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=companies.xlsx'
            return response
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '请求体不是有效的 JSON 格式'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)
class MetaKnowledgeViewSet(viewsets.ModelViewSet):
    queryset = MetaKnowledge.objects.all()
    serializer_class = MetaKnowledgeSerializer

    def list(self, request, *args, **kwargs):
        try:
            # 获取所有 MetaKnowledge 对象
            meta_knowledges = self.get_queryset()
            # 构造返回数据，包含 id 和 description
            data = [
                {
                    "id": meta_knowledge.id,
                    "description": meta_knowledge.description
                }
                for meta_knowledge in meta_knowledges
            ]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        description = request.data.get('description')
        formulas = request.data.get('formulas', [])
        variables = request.data.get('variables', [])  # 变量改为列表形式

        try:
            with transaction.atomic():  # 使用事务确保数据一致性
                # 创建 MetaKnowledge
                meta_knowledge = MetaKnowledge.objects.create(description=description)

                # 创建 Formula 并存储索引
                formula_objects = []
                for index, formula_string in enumerate(formulas, start=1):
                    formula = Formula.objects.create(meta_knowledge=meta_knowledge, formula_string=formula_string)
                    formula_objects.append((index, formula))

                formula_dict = {idx: formula for idx, formula in formula_objects}

                # 解析变量并建立 FormulaVariable 关系
                for variable_str in variables:
                    try:
                        # 解析变量格式 "1_x_公司负债率"
                        parts = variable_str.split("_", 2)
                        if len(parts) != 3:
                            continue  # 如果格式不正确，跳过

                        formula_index = int(parts[0])  # 第 n 个公式
                        variable_name = parts[1]  # 变量名称
                        variable_meaning = parts[2]  # 变量含义

                        # 确保 formula_index 存在
                        if formula_index not in formula_dict:
                            continue  # 如果公式索引不存在，跳过

                        formula = formula_dict[formula_index]

                        # 获取或创建 Variable
                        variable, created = Variable.objects.get_or_create(
                            variable_name=variable_name,
                            defaults={
                                'variable_meaning': variable_meaning,
                                'reference_count': 0
                            }
                        )

                        # 如果变量已存在，更新变量含义（如果需要）
                        if not created:
                            variable.variable_meaning = variable_meaning
                            variable.save()

                        # 创建 FormulaVariable 自动管理引用计数
                        FormulaVariable.objects.create(formula=formula, variable=variable)

                    except (ValueError, IndexError) as e:
                        print(f"Error parsing variable: {variable_str}, error: {e}")
                        continue  # 如果解析失败，跳过

                return Response({"message": "MetaKnowledge created successfully!"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            # 获取待删除的 MetaKnowledge 对象
            meta_knowledge = self.get_object()
            # 删除该 MetaKnowledge 对象相关的所有公式
            formulas = Formula.objects.filter(meta_knowledge=meta_knowledge)
            # 遍历所有公式
            for formula in formulas:
                # 获取该公式中所有的变量关系
                formula_variables = FormulaVariable.objects.filter(formula=formula)
                # 对每个公式中的变量，减少引用计数器
                for formula_variable in formula_variables:
                    variable = formula_variable.variable
                    variable.reference_count -= 1
                    # 如果引用计数器为 0，删除该变量
                    if variable.reference_count == 0:
                        variable.delete()
                    else:
                        variable.save()  # 保存引用计数器变更
                # 删除公式相关的关系
                formula_variables.delete()
                # 删除公式本身
                formula.delete()
            # 删除 MetaKnowledge 对象
            meta_knowledge.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except MetaKnowledge.DoesNotExist:
            return Response({'detail': '元知识未找到'}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, *args, **kwargs):
        try:
            meta_knowledge = self.get_object()
            # 构造返回数据
            data = {
                "id": meta_knowledge.id,
                "description": meta_knowledge.description,
                "formulas": []
            }
            # 获取所有公式
            formulas = meta_knowledge.formulas.all()
            for formula in formulas:
                # 获取公式关联的变量
                variables = formula.formula_variables.all()
                variable_data = [
                    {
                        "id": v.variable.id,
                        "variable_name": v.variable.variable_name,
                        "variable_type": v.variable.variable_meaning
                    }
                    for v in variables
                ]
                # 添加公式数据
                data["formulas"].append({
                    "id": formula.id,
                    "formula_string": formula.formula_string,
                    "variables": variable_data
                })
            return Response(data, status=status.HTTP_200_OK)
        except MetaKnowledge.DoesNotExist:
            return Response({'detail': '元知识未找到'}, status=status.HTTP_404_NOT_FOUND)
def fuzzymatch(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            company_name = body.get('companyName', '').strip()
            if not company_name:
                return JsonResponse({'error': '公司名称不能为空'}, status=400)
            query = """
            MATCH (n:Company)
            WHERE coalesce(n.`公司中文名称`, '') CONTAINS $keyword
               OR coalesce(n.`公司曾用名`, '') CONTAINS $keyword
            RETURN n
            """
            result = graph.run(query, keyword=company_name).data()
            companies = []
            for record in result:
                company = record['n']
                companies.append({
                    'name': company.get('公司中文名称', ''),
                    'social_credit_code': company.get('社会信用代码', '')
                })
            return JsonResponse({'companies': companies})
        except json.JSONDecodeError:
            return JsonResponse({'error': '请求体不是有效的 JSON 格式'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': '请求方法不正确'}, status=400)

class ExtractRelationView(APIView):
    """
    新闻关系提取API接口
    从新闻文本中自动提取公司关系并保存到数据集
    """
    permission_classes = []
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # 验证必要字段
            required_fields = ['title', 'source', 'time', 'url', 'abstract', 'content']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'status': 'error', 'message': f'缺少必要字段: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            news = {
                'title': data['title'],
                'source': data['source'],
                'time': data['time'],
                'url': data['url'],
                'abstract': data.get('abstract', ''),
                'content': data.get('content', '')
            }
            
            # 使用关系抽取器提取关系
            relations = extractor.extract_from_news(news)
            
            if not relations:
                return Response({
                    'status': 'success',
                    'message': '未识别到公司关系',
                    'extracted_relations': []
                }, status=status.HTTP_200_OK)
            
            # 保存提取的关系
            for rel in relations:
                extractor.add_relation(
                    company1=rel['company1'],
                    company2=rel['company2'],
                    relation=rel['relation'],
                    evidence=rel['evidence'],
                    news=rel['news']
                )
            
            return Response({
                'status': 'success',
                'message': f'成功提取并保存 {len(relations)} 条关系',
                'extracted_relations': relations
            }, status=status.HTTP_201_CREATED)
            
        except json.JSONDecodeError:
            return Response(
                {'status': 'error', 'message': '请求体不是有效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class QueryRelationsView(APIView):
    """
    查询公司关系API接口
    """
    permission_classes = []
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            company_name = data.get('company_name', '')
            
            if not company_name:
                return Response(
                    {'status': 'error', 'message': '公司名称不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            relations = extractor.get_relations_by_company(company_name)
            
            return Response({
                'status': 'success',
                'company': company_name,
                'relations': relations
            }, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response(
                {'status': 'error', 'message': '请求体不是有效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetAllCompaniesView(APIView):
    """
    获取所有公司列表API接口
    """
    permission_classes = []
    
    def get(self, request):
        try:
            companies = extractor.get_all_companies()
            return Response({
                'status': 'success',
                'companies': companies
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AddCompanyView(APIView):
    """
    添加新公司API接口
    """
    permission_classes = []
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            company_name = data.get('company_name', '').strip()
            
            if not company_name:
                return Response(
                    {'status': 'error', 'message': '公司名称不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            extractor.add_new_company(company_name)
            
            return Response({
                'status': 'success',
                'message': f'公司 "{company_name}" 已成功添加'
            }, status=status.HTTP_201_CREATED)
            
        except json.JSONDecodeError:
            return Response(
                {'status': 'error', 'message': '请求体不是有效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GraphStatsView(APIView):
    """
    获取知识图谱核心统计指标
    """
    permission_classes = []

    def get(self, request):
        try:
            # 1. 总节点数 / 总关系数
            total_nodes = graph.run("MATCH (n) RETURN count(n) AS c").data()[0]["c"]
            total_rels = graph.run("MATCH ()-[r]->() RETURN count(r) AS c").data()[0]["c"]

            # 2. 节点标签分布
            label_rows = graph.run("""
                MATCH (n)
                UNWIND labels(n) AS label
                RETURN label, count(*) AS cnt
                ORDER BY cnt DESC
            """).data()
            node_type_distribution = {row["label"]: row["cnt"] for row in label_rows}

            # 3. 关系类型分布
            rel_rows = graph.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS relType, count(*) AS cnt
                ORDER BY cnt DESC
            """).data()
            relationship_distribution = {row["relType"]: row["cnt"] for row in rel_rows}

            # 4. 公司相关统计
            company_count = graph.run("MATCH (n:Company) RETURN count(n) AS c").data()[0]["c"]

            # 5. 上市公司判断：存在 A股证券代码 / 证券代码 / 股票简称 任一属性视为上市公司
            listed_attrs = ["A股证券代码", "证券代码", "股票简称"]
            listed_where = " OR ".join([f"n.`{a}` IS NOT NULL" for a in listed_attrs])
            listed_count = graph.run(f"""
                MATCH (n:Company)
                WHERE {listed_where}
                RETURN count(n) AS c
            """).data()[0]["c"]
            unlisted_count = max(0, company_count - listed_count)

            # 6. 行业分布：依次尝试 行业、所属行业、主营业务、公司行业 属性
            #    对主营业务文本按关键词归类，避免长文本导致图表无法展示
            industry_distribution = []
            industry_fields = ["行业", "所属行业", "主营业务", "公司行业"]
            raw_rows = []
            for field in industry_fields:
                rows = graph.run(f"""
                    MATCH (n:Company)
                    WHERE n.`{field}` IS NOT NULL AND n.`{field}` <> ''
                    RETURN n.`{field}` AS name, count(*) AS cnt
                    ORDER BY cnt DESC
                """).data()
                if rows:
                    raw_rows = rows
                    break

            if raw_rows:
                # 行业关键词映射（按优先级匹配）
                INDUSTRY_KEYWORDS = [
                    ("医药生物", ["医药", "药品", "疫苗", "医疗器械", "医疗", "生物科技", "生物制药", "中医药", "化学药"]),
                    ("房地产", ["房地产", "房地产开发", "商业地产", "住宅开发", "物业管理", "住房租赁"]),
                    ("电子", ["电子", "电路板", "半导体", "芯片", "集成电路", "LED", "显示面板", "被动元件"]),
                    ("汽车", ["汽车", "汽车零部件", "整车", "新能源汽车", "动力电池", "汽车电子"]),
                    ("金融", ["银行", "证券", "保险", "金融", "信托", "基金", "期货", "资产管理", "融资租赁"]),
                    ("互联网", ["互联网", "软件", "信息技术", "网络", "电子商务", "大数据", "云计算", "人工智能"]),
                    ("石油化工", ["石油", "化工", "化学", "石化", "精细化工", "基础化工", "化工新材料"]),
                    ("机械设备", ["机械", "设备", "专用设备", "通用设备", "自动化设备", "工程机械", "重型机械"]),
                    ("建筑建材", ["建筑", "建材", "装饰", "装修", "水泥", "玻璃", "陶瓷", "管材", "防水材料"]),
                    ("通信", ["通信", "通讯", "电信", "5G", "光通信", "通信设备"]),
                    ("家电", ["家电", "家用电器", "空调", "冰箱", "洗衣机", "厨电", "小家电"]),
                    ("交通运输", ["交通运输", "物流", "快递", "航运", "港口", "机场", "铁路", "公路"]),
                    ("公用事业", ["公用事业", "电力", "水务", "燃气", "供热", "环保", "新能源发电"]),
                    ("新能源", ["新能源", "光伏", "风电", "锂电池", "储能", "氢能源", "核电"]),
                    ("食品饮料", ["食品", "饮料", "白酒", "啤酒", "乳制品", "调味品", "农产品", "粮油"]),
                    ("金属", ["钢铁", "有色金属", "金属", "稀土", "磁性材料", "合金"]),
                    ("纺织服装", ["纺织", "服装", "服饰", "面料", "纱线", "印染"]),
                    ("传媒", ["传媒", "广告", "文化", "影视", "游戏", "出版", "动漫"]),
                    ("商贸零售", ["零售", "批发", "商贸", "百货", "超市", "便利店", "电商"]),
                ]

                def classify_industry(text):
                    if not text:
                        return "其他"
                    text = str(text)
                    for industry, keywords in INDUSTRY_KEYWORDS:
                        for kw in keywords:
                            if kw in text:
                                return industry
                    return "其他"

                from collections import Counter
                counter = Counter()
                for row in raw_rows:
                    category = classify_industry(row["name"])
                    counter[category] += row["cnt"]

                industry_distribution = [
                    {"name": name, "count": count}
                    for name, count in counter.most_common(15)
                ]

            # 有行业信息的公司总数（用于计算行业占比）
            industry_total = sum(item["count"] for item in industry_distribution)

            return Response({
                "status": "success",
                "totalNodes": total_nodes,
                "totalRelationships": total_rels,
                "companyCount": company_count,
                "listedCount": listed_count,
                "unlistedCount": unlisted_count,
                "industryTotal": industry_total,
                "nodeTypeDistribution": node_type_distribution,
                "relationshipDistribution": relationship_distribution,
                "industryDistribution": industry_distribution
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== Cypher 高级查询功能 ====================

class CypherSubgraphView(APIView):
    """
    N跳子图查询：从指定节点出发，查询n跳范围内的所有节点和关系
    参数：credit_number（社会信用代码），hops（跳数1-5）
    """
    permission_classes = []

    def post(self, request):
        try:
            data = json.loads(request.body)
            credit_number = data.get('credit_number', '').strip()
            hops = int(data.get('hops', 2))
            hops = max(1, min(5, hops))  # 限制1-5跳

            if not credit_number:
                return Response({'status': 'error', 'message': '请提供社会信用代码'}, status=400)

            # 使用Cypher查询n跳子图
            query = f"""
            MATCH path = (start:Company {{`社会信用代码`: $credit_number}})-[*1..{hops}]-(end)
            WHERE NOT end:MetaKnowledge
            RETURN
                start.`公司中文名称` as start_name,
                end.`公司中文名称` as end_name,
                [rel in relationships(path) | type(rel)] as rel_types,
                length(path) as path_length,
                labels(end) as end_labels
            ORDER BY path_length
            LIMIT 100
            """

            result = graph.run(query, credit_number=credit_number).data()

            nodes = {}
            edges = []

            for row in result:
                start_name = row.get('start_name') or 'Unknown'
                end_name = row.get('end_name') or 'Unknown'
                rel_types = row.get('rel_types', [])

                nodes[start_name] = {'name': start_name, 'type': 'Company'}
                nodes[end_name] = {'name': end_name, 'type': row.get('end_labels', ['Unknown'])[0]}

                if rel_types:
                    edges.append({
                        'source': start_name,
                        'target': end_name,
                        'relation': rel_types[-1] if rel_types else 'RELATED'
                    })

            return Response({
                'status': 'success',
                'credit_number': credit_number,
                'hops': hops,
                'nodes': list(nodes.values()),
                'edges': edges,
                'node_count': len(nodes),
                'edge_count': len(edges)
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'status': 'error', 'message': str(e)}, status=500)


class RiskPathView(APIView):
    """
    风险路径追溯：查询某公司到违规/诉讼节点的最短路径
    参数：credit_number（社会信用代码）
    """
    permission_classes = []

    def post(self, request):
        try:
            data = json.loads(request.body)
            credit_number = data.get('credit_number', '').strip()

            if not credit_number:
                return Response({'status': 'error', 'message': '请提供社会信用代码'}, status=400)

            # 查询到Violation和Litigation的最短路径
            violation_query = """
            MATCH (c:Company {`社会信用代码`: $credit_number})
            MATCH (v:Violation)
            MATCH path = shortestPath((c)-[*1..5]-(v))
            RETURN
                c.`公司中文名称` as company,
                v.`违规类型` as violation_type,
                v.`处理单位` as handler,
                v.`处罚日期` as penalty_date,
                [rel in relationships(path) | type(rel)] as path_rels,
                length(path) as path_length
            LIMIT 5
            """

            litigation_query = """
            MATCH (c:Company {`社会信用代码`: $credit_number})
            MATCH (l:Litigation)
            MATCH path = shortestPath((c)-[*1..5]-(l))
            RETURN
                c.`公司中文名称` as company,
                l.`涉案缘由` as case_reason,
                l.`涉案金额` as amount,
                l.`司法类型` as litigation_type,
                [rel in relationships(path) | type(rel)] as path_rels,
                length(path) as path_length
            LIMIT 5
            """

            violation_paths = graph.run(violation_query, credit_number=credit_number).data()
            litigation_paths = graph.run(litigation_query, credit_number=credit_number).data()

            return Response({
                'status': 'success',
                'credit_number': credit_number,
                'violation_paths': violation_paths[:3],
                'litigation_paths': litigation_paths[:3]
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'status': 'error', 'message': str(e)}, status=500)


class RelationDistributionView(APIView):
    """
    关系类型分布：统计某节点涉及的所有关系类型和数量
    参数：credit_number（社会信用代码）
    """
    permission_classes = []

    def post(self, request):
        try:
            data = json.loads(request.body)
            credit_number = data.get('credit_number', '').strip()

            if not credit_number:
                return Response({'status': 'error', 'message': '请提供社会信用代码'}, status=400)

            query = """
            MATCH (c:Company {`社会信用代码`: $credit_number})
            OPTIONAL MATCH (c)-[r]->(out_node)
            OPTIONAL MATCH (in_node)-[r2]->(c)
            RETURN
                c.`公司中文名称` as company_name,
                type(r) as outgoing_type,
                count(distinct r) as outgoing_count,
                type(r2) as incoming_type,
                count(distinct r2) as incoming_count,
                labels(out_node) as out_labels,
                labels(in_node) as in_labels
            """

            result = graph.run(query, credit_number=credit_number).data()

            # 整理关系分布
            outgoing_relations = {}
            incoming_relations = {}
            company_name = ''

            for row in result:
                if not company_name:
                    company_name = row.get('company_name', 'Unknown')

                out_type = row.get('outgoing_type')
                out_count = row.get('outgoing_count') or 0
                if out_type and out_count > 0:
                    outgoing_relations[out_type] = {
                        'type': out_type,
                        'count': out_count,
                        'target_labels': row.get('out_labels', [])
                    }

                in_type = row.get('incoming_type')
                in_count = row.get('incoming_count') or 0
                if in_type and in_count > 0:
                    incoming_relations[in_type] = {
                        'type': in_type,
                        'count': in_count,
                        'source_labels': row.get('in_labels', [])
                    }

            return Response({
                'status': 'success',
                'credit_number': credit_number,
                'company_name': company_name,
                'outgoing_relations': list(outgoing_relations.values()),
                'incoming_relations': list(incoming_relations.values()),
                'total_outgoing': sum(r['count'] for r in outgoing_relations.values()),
                'total_incoming': sum(r['count'] for r in incoming_relations.values())
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'status': 'error', 'message': str(e)}, status=500)


class RiskCaseDataView(APIView):
    """
    获取五大风险类型下15个子类的真实案例数据
    用于前端风险类型详细分析页面展示
    """
    permission_classes = []

    def get(self, request):
        try:
            def get_sample_cases(query, limit=5):
                try:
                    results = list(graph.run(query).data())
                    return results[:limit]
                except Exception as e:
                    print(f"  查询失败: {e}")
                    return []

            def count_query(cypher, **params):
                """执行 COUNT 查询，返回 total 字段；失败返回 0"""
                try:
                    result = graph.run(cypher, **params).data()
                    return result[0]['total'] if result else 0
                except Exception as e:
                    print(f"  统计失败: {e}")
                    return 0

            def count_relations(rel_name):
                try:
                    cypher = f"MATCH ()-[r:`{rel_name}`]->() RETURN count(r) as total"
                    result = graph.run(cypher).data()
                    return result[0]['total'] if result else 0
                except:
                    return 0

            def count_nodes(label):
                try:
                    cypher = f"MATCH (n:`{label}`) RETURN count(n) as total"
                    result = graph.run(cypher).data()
                    return result[0]['total'] if result else 0
                except:
                    return 0

            def count_metaknowledge(keywords):
                """
                统计元知识条数 = 图谱中 core_conclusion 命中任一关键词的
                MetaKnowledge 节点数 + 本地 metaknowledge.jsonl 中
                "核心结论"命中任一关键词的条数（未导入图谱的新数据）。
                """
                if not keywords:
                    neo4j_count = count_nodes("MetaKnowledge")
                else:
                    cond = " OR ".join([f"n.core_conclusion CONTAINS $kw{i}" for i in range(len(keywords))])
                    params = {f"kw{i}": kw for i, kw in enumerate(keywords)}
                    cypher = f"MATCH (n:MetaKnowledge) WHERE {cond} RETURN count(n) as total"
                    neo4j_count = count_query(cypher, **params)
                return neo4j_count + len(match_local_metaknowledge(keywords))

            def get_meta_cases(keywords, limit=5):
                """
                元知识案例 = 图谱 MetaKnowledge 案例 + 本地 jsonl 案例（合并返回）。
                本地案例带 source='本地知识库' 标记，便于前端区分来源。
                """
                cases = []
                try:
                    if keywords:
                        cond = " OR ".join([f"n.core_conclusion CONTAINS $kw{i}" for i in range(len(keywords))])
                        params = {f"kw{i}": kw for i, kw in enumerate(keywords)}
                        cypher = (
                            f"MATCH (n:MetaKnowledge) WHERE {cond} "
                            f"RETURN n.id as id, n.core_conclusion as conclusion, "
                            f"n.risk_guidance as risk_guidance, n.related_event as related_event "
                            f"LIMIT {limit}"
                        )
                    else:
                        params = {}
                        cypher = (
                            f"MATCH (n:MetaKnowledge) "
                            f"RETURN n.id as id, n.core_conclusion as conclusion, "
                            f"n.risk_guidance as risk_guidance, n.related_event as related_event "
                            f"LIMIT {limit}"
                        )
                    cases = list(graph.run(cypher, **params).data())[:limit]
                except Exception as e:
                    print(f"  元知识案例查询失败: {e}")
                for m in match_local_metaknowledge(keywords)[:limit]:
                    cases.append({
                        'id': m.get('meta_id'),
                        'conclusion': m.get('核心结论'),
                        'risk_guidance': m.get('风险指导价值'),
                        'related_event': m.get('相关事件'),
                        'source': '本地知识库'
                    })
                return cases

            def count_violations(extra_where=""):
                """
                统计违规事件关系数，可附加对 Violation 节点的过滤条件。
                extra_where: 形如 "v.`违规类型` CONTAINS '披露'" 的 Cypher 片段（静态字面量，非用户输入）。
                """
                where = f"WHERE {extra_where}" if extra_where else ""
                cypher = f"MATCH (c:Company)-[r:`违规事件`]->(v:Violation) {where} RETURN count(r) as total"
                return count_query(cypher)

            # ============================================================
            # 1. 市场风险 (Market Risk)
            # ============================================================
            market_risk = {
                "name": "市场风险",
                "description": "因市场价格（股价、利率、汇率等）波动导致的损失风险",
                "sub_types": [
                    {
                        "name": "股债对冲效应",
                        "description": "股票与国债现货存在显著互相对冲效应，可作为资产配置工具",
                        "cases": get_meta_cases(['股票', '国债', '对冲']),
                        "count": count_metaknowledge(['股票', '国债', '对冲'])
                    },
                    {
                        "name": "灾难风险溢价",
                        "description": "灾难风险可解释中国股市约39.5%的股权溢价",
                        "cases": get_meta_cases(['灾难', '风险溢价', '尾部风险']),
                        "count": count_metaknowledge(['灾难', '风险溢价', '尾部风险'])
                    },
                    {
                        "name": "期货对冲局限",
                        "description": "股指期货与国债期货之间不存在显著对冲效应",
                        "cases": get_meta_cases(['期货', '股指期货', '国债期货']),
                        "count": count_metaknowledge(['期货', '股指期货', '国债期货'])
                    }
                ]
            }

            # ============================================================
            # 2. 信用风险 (Credit Risk)
            # ============================================================
            credit_risk = {
                "name": "信用风险",
                "description": "交易对手未能履行约定契约中的义务而造成经济损失的风险",
                "sub_types": [
                    {
                        "name": "对外担保风险",
                        "description": "对外担保形成或有负债，担保对象多为上市公司子公司",
                        "cases": get_sample_cases("""
                            MATCH (c1:Company)-[r:GUARANTEES]->(c2:Company)
                            RETURN c1.`公司中文名称` as guarantor, c2.`公司中文名称` as guaranteed, 
                                   r.`担保金额` as amount, r.`担保期限` as term, r.`债务类型` as debt_type,
                                   r.`债权人类型` as creditor_type, r.`担保方式` as guarantee_method
                            LIMIT 5
                        """),
                        "count": count_relations("GUARANTEES")
                    },
                    {
                        "name": "股权质押风险",
                        "description": "股东质押股权融资存在平仓、爆仓及控制权变更风险",
                        "cases": get_sample_cases("""
                            MATCH (c1:Company)-[r:PLEDGE]->(c2:Company)
                            RETURN c1.`公司中文名称` as pledgor, c2.`公司中文名称` as pledgee,
                                   r.`质押股数` as shares, r.`质押比例` as ratio, r.`质押用途编码` as purpose,
                                   r.`质押日期` as pledge_date, r.`解押日期` as release_date
                            LIMIT 5
                        """),
                        "count": count_relations("PLEDGE")
                    },
                    {
                        "name": "影子银行信用",
                        "description": "关联企业间的担保与借贷关系形成的隐性信用风险",
                        "cases": get_meta_cases(['影子银行', '隐性债务', '关联交易', '隐性信用']),
                        "count": count_metaknowledge(['影子银行', '隐性债务', '关联交易', '隐性信用'])
                    }
                ]
            }

            # ============================================================
            # 3. 操作风险 (Operational Risk)
            # ============================================================
            operational_risk = {
                "name": "操作风险",
                "description": "由不完善或有问题的内部程序、人员、系统或外部事件所造成损失的风险",
                "sub_types": [
                    {
                        "name": "信息披露违规",
                        "description": "推迟披露、虚假记载、重大遗漏等违规类型频发",
                        "cases": get_sample_cases("""
                            MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
                            WHERE v.`违规类型` CONTAINS '披露' OR v.`违规类型` CONTAINS '虚假' OR v.`违规类型` CONTAINS '遗漏'
                            RETURN c.`公司中文名称` as company, v.`违规类型` as violation_type,
                                   v.`处罚日期` as penalty_date, v.`处罚金额` as penalty_amount,
                                   v.`处理单位` as authority, v.`违规事实摘要` as summary
                            ORDER BY v.`处罚日期` DESC
                            LIMIT 5
                        """),
                        "count": count_violations("v.`违规类型` CONTAINS '披露' OR v.`违规类型` CONTAINS '虚假' OR v.`违规类型` CONTAINS '遗漏'")
                    },
                    {
                        "name": "管理层策略性行为",
                        "description": "管理层可能策略性增加创新投入以吸引投资者关注并借机减持套现",
                        "cases": get_meta_cases(['管理层', '减持', '创新投入']),
                        "count": count_metaknowledge(['管理层', '减持', '创新投入'])
                    },
                    {
                        "name": "网络安全感知",
                        "description": "移动端投资者网络安全风险感知要求更高的风险补偿",
                        "cases": get_meta_cases(['网络安全', '移动端', '投资者行为']),
                        "count": count_metaknowledge(['网络安全', '移动端', '投资者行为'])
                    }
                ]
            }

            # ============================================================
            # 4. 流动性风险 (Liquidity Risk)
            # ============================================================
            liquidity_risk = {
                "name": "流动性风险",
                "description": "企业无法及时获得充足资金或无法以合理成本及时获得充足资金的风险",
                "sub_types": [
                    {
                        "name": "政策不确定性与现金持有",
                        "description": "经济政策不确定性上升会显著抑制企业投资并提高现金持有",
                        "cases": get_meta_cases(['政策不确定性', '现金持有', '企业投资']),
                        "count": count_metaknowledge(['政策不确定性', '现金持有', '企业投资'])
                    },
                    {
                        "name": "跨境资本流动",
                        "description": "区域危机期间中国证券市场与发达市场一体化水平反而增强",
                        "cases": get_meta_cases(['跨境', '资本流动', '外资']),
                        "count": count_metaknowledge(['跨境', '资本流动', '外资'])
                    },
                    {
                        "name": "投资者行为",
                        "description": "移动端投资者网络安全风险感知越高，安全事件可能诱发赎回潮",
                        "cases": get_meta_cases(['投资者', '赎回', '行为']),
                        "count": count_metaknowledge(['投资者', '赎回', '行为'])
                    }
                ]
            }

            # ============================================================
            # 5. 声誉风险 (Reputational Risk)
            # ============================================================
            reputation_risk = {
                "name": "声誉风险",
                "description": "由负面的公众舆论、媒体报道或利益相关者评价导致企业声誉受损的风险",
                "sub_types": [
                    {
                        "name": "监管处罚",
                        "description": "深交所、上交所、证监会及地方监管局处罚事件会损害公司声誉",
                        "cases": get_sample_cases("""
                            MATCH (c:Company)-[r:`违规事件`]->(v:Violation)
                            WHERE v.`处理单位` IS NOT NULL
                            RETURN c.`公司中文名称` as company, v.`处理单位` as authority,
                                   v.`违规类型` as violation_type, v.`处罚日期` as penalty_date,
                                   v.`处罚金额` as penalty_amount, v.`处罚结果` as penalty_result
                            ORDER BY v.`处罚日期` DESC
                            LIMIT 5
                        """),
                        "count": count_violations("v.`处理单位` IS NOT NULL")
                    },
                    {
                        "name": "诉讼仲裁",
                        "description": "大额诉讼案件及司法执行信息会显著影响公司市场声誉",
                        "cases": get_sample_cases("""
                            MATCH (l:Litigation)
                            WHERE l.`起诉(申请)方` IS NOT NULL AND l.`应诉(被申请)方` IS NOT NULL
                            RETURN l.`起诉(申请)方` as plaintiff, l.`应诉(被申请)方` as defendant,
                                   l.`涉案金额` as amount, l.`涉案缘由` as reason,
                                   l.`司法类型` as judicial_type, l.`司法进程` as progress,
                                   l.`公告日期` as announce_date, l.`审理机构` as court
                            ORDER BY l.`公告日期` DESC
                            LIMIT 5
                        """),
                        "count": count_nodes("Litigation")
                    },
                    {
                        "name": "风险警示",
                        "description": "ST/*ST公司集中在批发、计算机通信、商务服务等行业",
                        "cases": get_sample_cases("""
                            MATCH (c:Company)
                            WHERE c.`股票简称` IS NOT NULL AND (c.`股票简称` CONTAINS 'ST' OR c.`股票简称` CONTAINS '*ST')
                            RETURN c.`公司中文名称` as company, c.`股票简称` as stock_abbreviation,
                                   c.`所属行业` as industry, c.`A股证券代码` as stock_code
                            LIMIT 5
                        """),
                        "count": count_query("MATCH (c:Company) WHERE c.`股票简称` IS NOT NULL AND (c.`股票简称` CONTAINS 'ST' OR c.`股票简称` CONTAINS '*ST') RETURN count(c) as total")
                    }
                ]
            }

            risk_case_data = {
                "market_risk": market_risk,
                "credit_risk": credit_risk,
                "operational_risk": operational_risk,
                "liquidity_risk": liquidity_risk,
                "reputation_risk": reputation_risk,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            return Response({
                'status': 'success',
                'data': risk_case_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'status': 'error', 'message': str(e)}, status=500)


class RelatedCompanyNetworkView(APIView):
    """
    关联公司网络：查询通过子公司、客户、供应商关系关联的公司
    参数：credit_number（社会信用代码）
    """
    permission_classes = []

    def post(self, request):
        try:
            data = json.loads(request.body)
            credit_number = data.get('credit_number', '').strip()

            if not credit_number:
                return Response({'status': 'error', 'message': '请提供社会信用代码'}, status=400)

            query = """
            MATCH (c:Company {`社会信用代码`: $credit_number})
            OPTIONAL MATCH (c)-[:`子公司`]->(sub:Company)
            OPTIONAL MATCH (c)-[:`客户`]->(cust:Company)
            OPTIONAL MATCH (c)-[:`供应商`]->(supplier:Company)
            OPTIONAL MATCH (parent:Company)-[:`子公司`]->(c)
            RETURN
                c.`公司中文名称` as company_name,
                collect(distinct sub.`公司中文名称`) as subsidiaries,
                collect(distinct cust.`公司中文名称`) as customers,
                collect(distinct supplier.`公司中文名称`) as suppliers,
                collect(distinct parent.`公司中文名称`) as parents,
                count(distinct sub) as sub_count,
                count(distinct cust) as cust_count,
                count(distinct supplier) as supplier_count
            LIMIT 1
            """

            result = graph.run(query, credit_number=credit_number).data()

            if result and len(result) > 0:
                row = result[0]
                return Response({
                    'status': 'success',
                    'credit_number': credit_number,
                    'company_name': row.get('company_name', ''),
                    'subsidiaries': [s for s in row.get('subsidiaries', []) if s][:10],
                    'customers': [c for c in row.get('customers', []) if c][:10],
                    'suppliers': [s for s in row.get('suppliers', []) if s][:10],
                    'parents': [p for p in row.get('parents', []) if p][:5],
                    'sub_count': row.get('sub_count', 0),
                    'cust_count': row.get('cust_count', 0),
                    'supplier_count': row.get('supplier_count', 0)
                })
            else:
                return Response({
                    'status': 'success',
                    'credit_number': credit_number,
                    'company_name': '',
                    'subsidiaries': [],
                    'customers': [],
                    'suppliers': [],
                    'parents': [],
                    'sub_count': 0,
                    'cust_count': 0,
                    'supplier_count': 0
                })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'status': 'error', 'message': str(e)}, status=500)


class RelationTestCasesView(APIView):
    """
    获取关系查询测试用例API
    统计图谱中所有关系类型及其数量，并为每种关系类型提供测试案例
    """
    permission_classes = []

    def get(self, request):
        try:
            # 1. 获取关系类型分布（只统计Company相关的关系）
            rel_dist_query = """
                MATCH ()-[r]->()
                RETURN type(r) AS relType, count(*) AS cnt
                ORDER BY cnt DESC
            """
            rel_dist = graph.run(rel_dist_query).data()
            relationship_distribution = {row['relType']: row['cnt'] for row in rel_dist}
            
            # 2. 专门查询Company之间的关系类型和示例
            company_rel_query = """
                MATCH (c1:Company)-[r]->(c2:Company)
                RETURN type(r) AS relType, count(*) AS cnt
                ORDER BY cnt DESC
            """
            company_rel_dist = graph.run(company_rel_query).data()
            
            # 3. 为每种Company之间的关系类型找到测试案例
            test_cases = []
            
            for row in company_rel_dist:
                rel_type = row['relType']
                rel_count = row['cnt']
                
                # 处理中文关系类型需要反引号
                rel_pattern = f"`{rel_type}`" if any('\u4e00' <= c <= '\u9fff' for c in rel_type) else rel_type
                
                # 查询Company节点之间的关系示例
                case_query = f"""
                    MATCH (c1:Company)-[r:{rel_pattern}]->(c2:Company)
                    RETURN c1.`公司中文名称` as company1, c2.`公司中文名称` as company2, type(r) as rel_type
                    LIMIT 3
                """
                
                try:
                    cases = graph.run(case_query).data()
                    if cases:
                        for case in cases:
                            test_cases.append({
                                'relation_type': rel_type,
                                'company1': case['company1'],
                                'company2': case['company2'],
                                'expected_relation': case['rel_type'],
                                'test_type': 'positive'
                            })
                except Exception as e:
                    print(f"查询关系类型 {rel_type} 失败: {str(e)}")
            
            # 4. 如果没有找到足够的测试用例，尝试更宽松的查询
            if len(test_cases) < 5:
                fallback_query = """
                    MATCH (c1:Company)-[r]-(c2:Company)
                    WHERE c1 <> c2
                    RETURN c1.`公司中文名称` as company1, c2.`公司中文名称` as company2, type(r) as rel_type
                    LIMIT 20
                """
                fallback_cases = graph.run(fallback_query).data()
                seen_pairs = set()
                
                for case in fallback_cases:
                    pair_key = (case['company1'], case['company2'], case['rel_type'])
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        test_cases.append({
                            'relation_type': case['rel_type'],
                            'company1': case['company1'],
                            'company2': case['company2'],
                            'expected_relation': case['rel_type'],
                            'test_type': 'positive'
                        })
            
            # 5. 添加负向测试用例
            negative_cases = [
                {
                    'test_id': 'TC_N001',
                    'company1': '不存在的公司ABC123',
                    'company2': '测试公司XYZ',
                    'expected_result': '查不到两个公司的关系',
                    'test_type': 'negative'
                },
                {
                    'test_id': 'TC_N002',
                    'company1': '',
                    'company2': '',
                    'expected_result': '请输入公司信息',
                    'test_type': 'negative'
                }
            ]
            
            return Response({
                'status': 'success',
                'total_relationship_types': len(rel_dist),
                'total_relationships': sum(row['cnt'] for row in rel_dist),
                'company_relationship_types': len(company_rel_dist),
                'company_relationships': sum(row['cnt'] for row in company_rel_dist),
                'relationship_distribution': relationship_distribution,
                'company_relationship_distribution': {row['relType']: row['cnt'] for row in company_rel_dist},
                'positive_test_cases': test_cases,
                'negative_test_cases': negative_cases
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'status': 'error', 'message': str(e)}, status=500)


class TestRelationQueryView(APIView):
    """
    测试关系查询API - 直接使用公司名称查询关系
    用于调试和验证关系查询功能
    """
    permission_classes = []

    def get(self, request):
        try:
            company1 = request.query_params.get('company1', '')
            company2 = request.query_params.get('company2', '')
            
            if not company1 or not company2:
                return Response({'status': 'error', 'message': '请提供company1和company2参数'}, status=400)
            
            print(f"[TestRelationQuery] 测试查询 - company1: '{company1}', company2: '{company2}'")
            
            # 直接使用公司名称进行查询
            query = f"""
                MATCH (c1:Company)-[r]-(c2:Company) 
                WHERE (c1.`公司中文名称` CONTAINS '{company1}' OR '{company1}' CONTAINS c1.`公司中文名称`)
                  AND (c2.`公司中文名称` CONTAINS '{company2}' OR '{company2}' CONTAINS c2.`公司中文名称`)
                  AND c1 <> c2
                RETURN type(r) as relationship_type, c1.`公司中文名称` as company1_name, c2.`公司中文名称` as company2_name, c1.`社会信用代码` as credit1, c2.`社会信用代码` as credit2, r
                LIMIT 20
            """
            
            print(f"[TestRelationQuery] 执行查询: {query}")
            result = graph.run(query).data()
            print(f"[TestRelationQuery] 查询结果: {len(result)} 条")
            
            relationships = []
            for record in result:
                relationships.append({
                    'relationship_type': record['relationship_type'],
                    'company1_name': record['company1_name'],
                    'company2_name': record['company2_name'],
                    'credit1': record['credit1'],
                    'credit2': record['credit2'],
                    'attributes': dict(record['r'])
                })
            
            return Response({
                'status': 'success',
                'query': query,
                'count': len(relationships),
                'relationships': relationships
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'status': 'error', 'message': str(e)}, status=500)


def _escape_cypher_identifier(name):
    """反引号转义 Cypher 标签/属性名，防止注入"""
    return '`' + str(name).replace('`', '``') + '`'


def _escape_cypher_string(s):
    """双引号转义 Cypher 字符串字面量，用于 row["字段名"] 形式的 map 取值"""
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def _get_graph_schema(graph_ref):
    """获取图谱现有节点标签与关系类型（元数据过程，无需扫描全图）"""
    labels = {r['label'] for r in graph_ref.run("CALL db.labels()").data()}
    rel_types = {r['relationshipType'] for r in graph_ref.run("CALL db.relationshipTypes()").data()}
    return labels, rel_types


class GraphSchemaView(APIView):
    """
    获取图谱 Schema：所有节点标签与关系类型（含数量，按数量降序）
    供数据导入页面的实体类型/关系类型下拉框使用
    """
    permission_classes = []

    def get(self, request):
        try:
            label_rows = graph.run("""
                MATCH (n)
                UNWIND labels(n) AS label
                RETURN label, count(*) AS cnt
                ORDER BY cnt DESC
            """).data()
            rel_rows = graph.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS relType, count(*) AS cnt
                ORDER BY cnt DESC
            """).data()
            return JsonResponse({
                'status': 'success',
                'nodeLabels': [{'name': r['label'], 'count': r['cnt']} for r in label_rows],
                'relationshipTypes': [{'name': r['relType'], 'count': r['cnt']} for r in rel_rows]
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class StructuredImportView(APIView):
    """
    结构化数据导入API（CSV/Excel）
    根据前端配置的字段映射生成 Cypher CREATE 语句，批量创建节点和关系
    mode=preview: 只生成并返回 CREATE 语句与统计，不写入图谱
    mode=execute: 分批执行 CREATE 写入，进度可通过 GET 轮询
    """
    permission_classes = []

    def get(self, request):
        # 前端轮询导入进度
        return JsonResponse({'progress': cache.get('structured_import_progress', 0)})

    def _import_relations_only(self, df, columns, relation_mappings, batch_size):
        """
        纯关系导入：不创建节点，只为图中已存在的节点创建关系
        - 端点标签/属性在映射中显式指定（fromLabel/fromProp/toLabel/toProp）
        - 支持 props: {关系属性名: 源字段} 写入关系属性
        - 逐行执行并校验创建数，精确上报端点未匹配的行
        """
        if not relation_mappings:
            return JsonResponse({'status': 'error', 'message': '关系导入模式需要至少一条关系映射'}, status=400)

        existing_labels, existing_rel_types = _get_graph_schema(graph)

        # 校验映射
        for idx, r in enumerate(relation_mappings):
            for key in ('fromField', 'fromLabel', 'fromProp', 'toField', 'toLabel', 'toProp', 'relType'):
                if not r.get(key):
                    return JsonResponse({'status': 'error', 'message': f'第 {idx + 1} 条关系映射缺少字段: {key}'}, status=400)
            for key in ('fromField', 'toField'):
                if r[key] not in columns:
                    return JsonResponse({'status': 'error', 'message': f"关系映射源字段不存在: {r[key]}"}, status=400)
            for key, valid, tip in (('fromLabel', existing_labels, '节点标签'), ('toLabel', existing_labels, '节点标签')):
                if r[key] not in valid:
                    return JsonResponse({'status': 'error', 'message': f"{tip}不存在于图谱: {r[key]}", 'validNodeLabels': sorted(valid)}, status=400)
            if r['relType'] not in existing_rel_types:
                return JsonResponse({'status': 'error', 'message': f"关系类型不存在于图谱: {r['relType']}", 'validRelationshipTypes': sorted(existing_rel_types)}, status=400)
            for rp, sf in (r.get('props') or {}).items():
                if sf not in columns:
                    return JsonResponse({'status': 'error', 'message': f"关系属性源字段不存在: {rp} <- {sf}"}, status=400)

        records = df.to_dict('records')
        cache.set('structured_import_progress', 0)
        total_created, failed, skipped_empty = 0, 0, 0
        errors = []

        try:
            for done, r in enumerate(relation_mappings):
                # 过滤端点为空的行
                rows = [row for row in records
                        if str(row.get(r['fromField'], '')).strip() and str(row.get(r['toField'], '')).strip()]
                skipped_empty += len(records) - len(rows)

                prop_clause = ', '.join(
                    f"{_escape_cypher_identifier(rp)}: row[{_escape_cypher_string(sf)}]"
                    for rp, sf in (r.get('props') or {}).items()
                )
                rel_props_sql = f' {{{prop_clause}}}' if prop_clause else ''
                stmt = (
                    f"UNWIND $rows AS row "
                    f"MATCH (a:{_escape_cypher_identifier(r['fromLabel'])} {{"
                    f"{_escape_cypher_identifier(r['fromProp'])}: row[{_escape_cypher_string(r['fromField'])}]}}) "
                    f"MATCH (b:{_escape_cypher_identifier(r['toLabel'])} {{"
                    f"{_escape_cypher_identifier(r['toProp'])}: row[{_escape_cypher_string(r['toField'])}]}}) "
                    f"CREATE (a)-[rel:{_escape_cypher_identifier(r['relType'])}{rel_props_sql}]->(b) "
                    f"RETURN count(rel) AS created"
                )

                # 逐行执行：MATCH 未命中时 CREATE 数为 0，可精确定位失败行
                for row in rows:
                    try:
                        cursor = graph.run(stmt, rows=[row])
                        data = cursor.data()
                        n = data[0]['created'] if data else 0
                        if n > 0:
                            total_created += n
                        else:
                            failed += 1
                            if len(errors) < 100:
                                errors.append({'row': row, 'error': '起点或终点节点未在图谱中匹配到'})
                    except Exception as e:
                        failed += 1
                        if len(errors) < 100:
                            errors.append({'row': row, 'error': str(e)})
                cache.set('structured_import_progress', int((done + 1) / len(relation_mappings) * 100))
        except Exception as e:
            cache.set('structured_import_progress', 0)
            return JsonResponse({'status': 'error', 'message': f'关系导入执行失败: {e}'}, status=500)

        cache.set('structured_import_progress', 100)
        print(f"[StructuredImport:relations] 完成 - 关系: {total_created}, 失败: {failed}, 空端点跳过: {skipped_empty}")
        return JsonResponse({
            'status': 'success',
            'mode': 'relations',
            'totalRows': len(records),
            'relationsCreated': total_created,
            'failedRows': failed,
            'skippedEmptyRows': skipped_empty,
            'errors': errors
        })

    def post(self, request):
        # 支持内联 records（JSON 数组）替代文件上传，供非结构化抽取结果回写等场景
        records_json = request.POST.get('records')
        if not records_json:
            file = request.FILES.get('file')
            if not file:
                return JsonResponse({'status': 'error', 'message': '请上传文件或提供 records'}, status=400)

        try:
            mappings = json.loads(request.POST.get('mappings', '{}'))
        except (TypeError, json.JSONDecodeError):
            return JsonResponse({'status': 'error', 'message': 'mappings 必须是合法 JSON'}, status=400)

        entity_mappings = mappings.get('entityMappings') or []
        relation_mappings = mappings.get('relationMappings') or []
        mode = request.POST.get('mode', 'execute')
        try:
            batch_size = max(1, int(request.POST.get('batchSize', 1000)))
        except (TypeError, ValueError):
            batch_size = 1000

        # 解析数据来源：内联 records 或上传文件
        if records_json:
            try:
                df = pd.DataFrame(json.loads(records_json))
            except (TypeError, json.JSONDecodeError) as e:
                return JsonResponse({'status': 'error', 'message': f'records 解析失败: {e}'}, status=400)
        else:
            filename = file.name.lower()
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file, keep_default_na=False)
                elif filename.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file, keep_default_na=False)
                else:
                    return JsonResponse({'status': 'error', 'message': '仅支持 CSV、Excel 格式，需包含表头行'}, status=400)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'文件解析失败: {e}'}, status=400)

        df = df.drop_duplicates().reset_index(drop=True)
        columns = list(df.columns)

        # 表头探测模式：仅返回列名，供前端生成默认字段映射
        if mode == 'headers':
            return JsonResponse({'status': 'success', 'columns': columns})

        # ============ 纯关系导入模式 ============
        # CSV 每行即一条关系，端点为图中已存在的节点（不创建节点）
        # relationMappings 需显式指定: fromField/fromLabel/fromProp/toField/toLabel/toProp/relType
        # 可选 props: {关系属性名: 源字段}
        if mode == 'relations':
            return self._import_relations_only(df, columns, relation_mappings, batch_size)

        if not entity_mappings:
            return JsonResponse({'status': 'error', 'message': '请至少配置一条实体映射'}, status=400)

        # 校验实体映射的源字段
        for m in entity_mappings:
            if m.get('sourceField') not in columns:
                return JsonResponse({'status': 'error', 'message': f"实体映射源字段不存在: {m.get('sourceField')}"}, status=400)
            if not m.get('targetType') or not m.get('targetProp'):
                return JsonResponse({'status': 'error', 'message': f"实体映射缺少实体类型或属性名: {m.get('sourceField')}"}, status=400)

        # 源字段 -> (实体类型, 属性名)，用于关系端点定位节点
        field_to_node = {m['sourceField']: (m['targetType'], m['targetProp']) for m in entity_mappings}

        # 校验关系映射
        for r in relation_mappings:
            for key in ('fromField', 'toField'):
                if r.get(key) not in field_to_node:
                    return JsonResponse({'status': 'error', 'message': f"关系映射的 {key} 未配置对应实体映射: {r.get(key)}"}, status=400)
            if not r.get('relType'):
                return JsonResponse({'status': 'error', 'message': '关系映射缺少关系类型'}, status=400)

        # 校验实体类型与关系类型必须为图谱已有类型，保证导入数据与现有本体一致
        existing_labels, existing_rel_types = _get_graph_schema(graph)
        bad_labels = sorted({m['targetType'] for m in entity_mappings} - existing_labels)
        if bad_labels:
            return JsonResponse({
                'status': 'error',
                'message': f"实体类型不存在于图谱: {', '.join(bad_labels)}",
                'validNodeLabels': sorted(existing_labels)
            }, status=400)
        bad_rels = sorted({r['relType'] for r in relation_mappings} - existing_rel_types)
        if bad_rels:
            return JsonResponse({
                'status': 'error',
                'message': f"关系类型不存在于图谱: {', '.join(bad_rels)}",
                'validRelationshipTypes': sorted(existing_rel_types)
            }, status=400)

        # 按实体类型分组生成节点 CREATE 语句
        # 同一标签内重复的属性名只保留首个映射（如"公司名称"与"担保方"都映射到
        # Company.name 时，建点用"公司名称"，"担保方"仅用于关系端点匹配），
        # 从而支持 GUARANTEES 等公司间自引用关系的导入
        node_groups = {}  # targetType -> [(targetProp, sourceField)]
        for m in entity_mappings:
            props = node_groups.setdefault(m['targetType'], [])
            if not any(tp == m['targetProp'] for tp, _ in props):
                props.append((m['targetProp'], m['sourceField']))

        node_statements = []
        for label, props in node_groups.items():
            prop_clause = ', '.join(
                f"{_escape_cypher_identifier(tp)}: row[{_escape_cypher_string(sf)}]"
                for tp, sf in props
            )
            stmt = f"UNWIND $rows AS row CREATE (n:{_escape_cypher_identifier(label)} {{{prop_clause}}})"
            node_statements.append({'targetType': label, 'cypher': stmt, 'props': props})

        # 生成关系 CREATE 语句
        relation_statements = []
        for r in relation_mappings:
            from_label, from_prop = field_to_node[r['fromField']]
            to_label, to_prop = field_to_node[r['toField']]
            stmt = (
                f"UNWIND $rows AS row "
                f"MATCH (a:{_escape_cypher_identifier(from_label)} {{"
                f"{_escape_cypher_identifier(from_prop)}: row[{_escape_cypher_string(r['fromField'])}]}}) "
                f"MATCH (b:{_escape_cypher_identifier(to_label)} {{"
                f"{_escape_cypher_identifier(to_prop)}: row[{_escape_cypher_string(r['toField'])}]}}) "
                f"CREATE (a)-[rel:{_escape_cypher_identifier(r['relType'])}]->(b) "
                f"RETURN count(rel) AS created"
            )
            relation_statements.append({
                'relType': r['relType'],
                'cypher': stmt,
                'fromField': r['fromField'],
                'toField': r['toField']
            })

        records = df.to_dict('records')
        total_rows = len(records)

        # 预览模式：返回生成的语句与统计，不写库
        if mode == 'preview':
            return JsonResponse({
                'status': 'success',
                'mode': 'preview',
                'totalRows': total_rows,
                'columns': columns,
                'nodeCount': total_rows * len(node_groups),
                'relationCount': total_rows * len(relation_statements),
                'nodeStatements': node_statements,
                'relationStatements': relation_statements,
                'sampleRows': records[:5],
                'validNodeLabels': sorted(existing_labels),
                'validRelationshipTypes': sorted(existing_rel_types)
            })

        # 执行模式：分批执行 CREATE
        cache.set('structured_import_progress', 0)
        stats = {'nodesCreated': 0, 'relationsCreated': 0, 'failedRows': 0}
        errors = []
        steps = len(node_statements) + len(relation_statements)
        done_steps = 0

        def run_in_batches(stmt, rows):
            """分批执行，批失败时降级为逐行执行以定位坏数据，返回(成功数, 失败数)"""
            created, failed = 0, 0
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                try:
                    cursor = graph.run(stmt, rows=batch)
                    cursor.data()  # 消费游标后才能读取统计
                    summary = cursor.stats()
                    created += summary.get('nodes_created', 0) + summary.get('relationships_created', 0)
                except Exception:
                    # 降级逐行执行，收集失败行
                    for row in batch:
                        try:
                            cursor = graph.run(stmt, rows=[row])
                            cursor.data()
                            summary = cursor.stats()
                            created += summary.get('nodes_created', 0) + summary.get('relationships_created', 0)
                        except Exception as row_e:
                            failed += 1
                            if len(errors) < 100:
                                errors.append({'row': row, 'error': str(row_e)})
            return created, failed

        try:
            # 1. 创建节点
            for ns in node_statements:
                created, failed = run_in_batches(ns['cypher'], records)
                stats['nodesCreated'] += created
                stats['failedRows'] += failed
                done_steps += 1
                cache.set('structured_import_progress', int(done_steps / steps * 100))

            # 2. 创建关系（过滤端点为空的行）
            for rs in relation_statements:
                rel_rows = [
                    row for row in records
                    if str(row.get(rs['fromField'], '')).strip() and str(row.get(rs['toField'], '')).strip()
                ]
                created, failed = run_in_batches(rs['cypher'], rel_rows)
                stats['relationsCreated'] += created
                stats['failedRows'] += failed
                done_steps += 1
                cache.set('structured_import_progress', int(done_steps / steps * 100))
        except Exception as e:
            cache.set('structured_import_progress', 0)
            return JsonResponse({'status': 'error', 'message': f'导入执行失败: {e}'}, status=500)

        cache.set('structured_import_progress', 100)
        print(f"[StructuredImport] 完成 - 节点: {stats['nodesCreated']}, 关系: {stats['relationsCreated']}, 失败: {stats['failedRows']}")
        return JsonResponse({
            'status': 'success',
            'mode': 'execute',
            'totalRows': total_rows,
            **stats,
            'errors': errors
        })

# 实体标签 -> 节点名属性键（抽取结果回写图谱时的对齐键，来自图谱真实 schema）
EXTRACT_NAME_PROP = {
    'Company': '公司中文名称',
    'City': '城市',
    'A_security': '证券简称',
    'G_security': '证券简称',
    'B_security': '证券简称',
    'Litigation': None,   # 案件节点无唯一名称键，v1 只建点不参与关系端点匹配
    'Violation': None,
}

# 文本可解析的文档
def _parse_document(file):
    """按扩展名解析文档为纯文本"""
    name = file.name.lower()
    if name.endswith('.txt') or name.endswith('.md'):
        return file.read().decode('utf-8', errors='ignore')
    if name.endswith('.html') or name.endswith('.htm'):
        from bs4 import BeautifulSoup
        html = file.read().decode('utf-8', errors='ignore')
        return BeautifulSoup(html, 'html.parser').get_text(separator='\n')
    if name.endswith('.docx'):
        import docx
        d = docx.Document(file)
        return '\n'.join(p.text for p in d.paragraphs if p.text.strip())
    if name.endswith('.pdf'):
        from pypdf import PdfReader
        reader = PdfReader(file)
        return '\n'.join((page.extract_text() or '') for page in reader.pages)
    if name.endswith('.doc'):
        raise ValueError('暂不支持旧版 .doc，请另存为 .docx')
    raise ValueError('不支持的文档格式，支持 PDF/Word/TXT/HTML')


def _chunk_text(text, size=1600, overlap=150):
    """按字符分块，带重叠窗口"""
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return [c for c in chunks if len(c.strip()) > 30]


def _ollama_extract(chunk_text, model):
    """调用本地 Ollama 抽取一个文本块，返回 {entities, relations}（已过滤非法类型）"""
    import requests
    from .extraction_prompt import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt, VALID_LABELS, VALID_RELATIONS
    resp = requests.post('http://localhost:11434/api/chat', json={
        'model': model or 'qwen3:32b',
        'messages': [
            {'role': 'system', 'content': EXTRACTION_SYSTEM_PROMPT},
            {'role': 'user', 'content': build_extraction_prompt(chunk_text)},
        ],
        'stream': False,
        'format': 'json',
        'options': {'temperature': 0.1, 'num_ctx': 8192},
    }, timeout=600)
    resp.raise_for_status()
    data = json.loads(resp.json()['message']['content'])
    labels = set(VALID_LABELS)
    rel_types = set(VALID_RELATIONS)
    entities = [e for e in data.get('entities', []) if e.get('label') in labels and e.get('name')]
    id_map = {e.get('id'): e for e in entities}
    relations = []
    for r in data.get('relations', []):
        if r.get('type') not in rel_types:
            continue
        f, t = id_map.get(r.get('from')), id_map.get(r.get('to'))
        if not f or not t:
            continue
        relations.append({'from': f['name'], 'to': t['name'], 'type': r['type'], 'props': r.get('props') or {}})
    return entities, relations


class UnstructuredExtractView(APIView):
    """
    半/非结构化文档抽取API
    POST: 上传文档(txt/pdf/docx/html)，后台线程分块调用本地 Ollama(qwen3:32b)
          按图谱本体抽取实体/关系，返回 task_id
    GET ?task_id=xx: 轮询进度与结果
    结果结构: {entities: [{text,type,confidence,props}], relations: [{subject,predicate,object,confidence,props}]}
    """
    permission_classes = []

    def get(self, request):
        task_id = request.GET.get('task_id', '')
        state = cache.get(f'extract_task_{task_id}') if task_id else None
        if not state:
            return JsonResponse({'status': 'error', 'message': '任务不存在或已过期'}, status=404)
        return JsonResponse(state)

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'status': 'error', 'message': '请上传文档'}, status=400)
        model = request.POST.get('model', 'qwen3:32b')

        try:
            text = _parse_document(file)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'文档解析失败: {e}'}, status=400)
        if not text.strip():
            return JsonResponse({'status': 'error', 'message': '文档内容为空'}, status=400)

        chunks = _chunk_text(text)
        task_id = f'ext_{datetime.now().strftime("%Y%m%d%H%M%S")}_{id(file) % 10000}'
        cache.set(f'extract_task_{task_id}', {
            'status': 'running', 'progress': 0, 'stage': '准备抽取',
            'totalChunks': len(chunks), 'doneChunks': 0,
        }, timeout=7200)

        thread = threading.Thread(target=self._run, args=(task_id, chunks, model), daemon=True)
        thread.start()
        return JsonResponse({'status': 'success', 'taskId': task_id, 'totalChunks': len(chunks)})

    def _run(self, task_id, chunks, model):
        def update(**kw):
            state = cache.get(f'extract_task_{task_id}') or {}
            state.update(kw)
            cache.set(f'extract_task_{task_id}', state, timeout=7200)

        all_entities = {}   # (name,label) -> props 合并
        all_relations = {}  # (from,to,type) -> props
        start_ts = time.time()
        try:
            for i, chunk in enumerate(chunks):
                elapsed = int(time.time() - start_ts)
                update(stage=f'抽取第 {i + 1}/{len(chunks)} 块（已用时 {elapsed}s，单块约 1-3 分钟）',
                       progress=max(2, int(i / len(chunks) * 95)))
                try:
                    entities, relations = _ollama_extract(chunk, model)
                except Exception as e:
                    update(stage=f'第 {i + 1} 块抽取失败已跳过: {e}')
                    continue
                for e in entities:
                    key = (e['name'], e['label'])
                    props = all_entities.get(key, {})
                    props.update(e.get('props') or {})
                    all_entities[key] = props
                for r in relations:
                    key = (r['from'], r['to'], r['type'])
                    props = all_relations.get(key, {})
                    props.update(r.get('props'))
                    all_relations[key] = props
                update(doneChunks=i + 1, progress=int((i + 1) / len(chunks) * 95))

            result = {
                'status': 'success', 'progress': 100, 'stage': '完成',
                'totalChunks': len(chunks), 'doneChunks': len(chunks),
                'result': {
                    'entities': [
                        {'text': name, 'type': label, 'confidence': 1.0, 'props': props}
                        for (name, label), props in all_entities.items()
                    ],
                    'relations': [
                        {'subject': f, 'predicate': t, 'object': o, 'confidence': 1.0, 'props': props}
                        for (f, o, t), props in all_relations.items()
                    ],
                    'lowConfidence': [],
                    'nameProps': EXTRACT_NAME_PROP,
                },
            }
            cache.set(f'extract_task_{task_id}', result, timeout=7200)
        except Exception as e:
            update(status='error', stage=f'抽取失败: {e}')


# ============================================================
# 元知识库页面：读取金融元知识库数据（library_report.md 介绍，
# papers.jsonl / metaknowledge.jsonl），提供总览统计与条目浏览
# ============================================================
META_LIB_DIR = '/home/wangluyi/MetaKnowledgeExtraction/data/metaknowledge_library'

_meta_lib_cache = {'mtime': None, 'stats': None, 'items': []}

def _load_meta_library():
    """读取 papers.jsonl / metaknowledge.jsonl 并汇总统计（按目录修改时间缓存）"""
    meta_path = os.path.join(META_LIB_DIR, 'metaknowledge.jsonl')
    papers_path = os.path.join(META_LIB_DIR, 'papers.jsonl')
    if not os.path.exists(meta_path):
        return {'stats': None, 'items': []}
    sig = os.path.getmtime(meta_path)
    if _meta_lib_cache.get('mtime') == sig:
        return {'stats': _meta_lib_cache['stats'], 'items': _meta_lib_cache['items']}

    items = []
    with open(meta_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # 论文级统计
    paper_count = 0
    papers_with_meta = 0
    per_paper_counts = []
    if os.path.exists(papers_path):
        with open(papers_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    p = json.loads(line)
                except json.JSONDecodeError:
                    continue
                paper_count += 1
                mc = p.get('meta_count') or len(p.get('metaknowledge') or [])
                if mc > 0:
                    papers_with_meta += 1
                per_paper_counts.append(mc)

    field_names = ['核心结论', '前提条件', '关键证据', '风险指导价值', '相关事件']
    field_stats = []
    for fn in field_names:
        vals = [it.get(fn) for it in items]
        nonempty = [v for v in vals if v]
        field_stats.append({
            'field': fn,
            'empty': len(items) - len(nonempty),
            'avg_len': round(sum(len(v) for v in nonempty) / len(nonempty)) if nonempty else 0,
        })

    # 每篇元知识数量分布（0-5、5+）
    dist = {}
    for c in per_paper_counts:
        key = str(min(c, 5)) + ('+' if c > 5 else '')
        dist[key] = dist.get(key, 0) + 1

    stats = {
        'paper_count': paper_count,
        'papers_with_meta': papers_with_meta,
        'meta_total': len(items),
        'avg_per_paper': round(len(items) / paper_count, 2) if paper_count else 0,
        'max_per_paper': max(per_paper_counts) if per_paper_counts else 0,
        'field_stats': field_stats,
        'per_paper_dist': dist,
    }
    _meta_lib_cache['mtime'] = sig
    _meta_lib_cache['stats'] = stats
    _meta_lib_cache['items'] = items
    return {'stats': stats, 'items': items}


class MetaKnowledgeLibraryView(APIView):
    """元知识库：总览统计 + 元知识条目（支持关键词过滤与分页）"""
    def get(self, request):
        data = _load_meta_library()
        if data['stats'] is None:
            return JsonResponse({'status': 'error', 'message': '元知识库文件不存在'}, status=404)
        items = data['items']
        kw = request.query_params.get('keyword', '').strip()
        if kw:
            items = [it for it in items if any(kw in (it.get(fn) or '') for fn in
                     ['核心结论', '前提条件', '关键证据', '风险指导价值', '相关事件', 'file_name'])]
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
        except ValueError:
            page, page_size = 1, 20
        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start:start + page_size]
        return JsonResponse({
            'status': 'success',
            'stats': data['stats'],
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': page_items,
        })
