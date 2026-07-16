from py2neo import Graph, NodeMatcher, Node, Relationship, RelationshipMatcher
from django.http import JsonResponse, HttpResponse, FileResponse
import json
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
            query_conditions.append(f"n.公司中文名称 = '{value}'")
        elif label == "credit_number" and value:
            query_conditions.append(f"n.社会信用代码 = '{value}'")
        elif label == "english_name" and value:
            query_conditions.append(f"n.英文名称 = '{value}'")
        elif label == "legal_representative" and value:
            query_conditions.append(f"n.法定代表人 = '{value}'")
        elif label == "security_code" and value:
            query_conditions.append(f"n.证券代码 = '{value}'")
        elif label == "stock_abbreviation" and value:
            query_conditions.append(f"n.股票简称 = '{value}'")

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
def QueryRelationship(node1, node2, relationship):
    query = ''
    if relationship:
        query = f"MATCH (c1:Company)-[r:{relationship}]->(c2:Company) WHERE c1.`社会信用代码` = '{node1}' AND c2.`社会信用代码` = '{node2}' RETURN type(r) as relationship_type, r"
    else:
        query = f"MATCH (c1:Company)-[r]->(c2:Company) WHERE c1.`社会信用代码` = '{node1}' AND c2.`社会信用代码` = '{node2}' RETURN type(r) as relationship_type, r"
    result = graph.run(query).data()
    relationship = str(result[0]['r'])
    return relationship.__str__().encode("utf-8").decode("unicode_escape")
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
            node = matcher.match("Company").where(f"_.社会信用代码= '{credit_number}'").first()
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
        node = matcher.match("Company").where(f"_.社会信用代码= '{ credit_number }'").first()
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
            node = matcher.match("Company").where(f"_.社会信用代码 = '{credit_number}'").first()
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
                    node = matcher.match("Company").where(f"_.公司中文名称='{company_name}'").first()
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
                node1 = matcher.match("Company").where(f"_.公司中文名称= '{company1}'").first()
                node2 = matcher.match("Company").where(f"_.公司中文名称= '{company2}'").first()
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
            relation_name = data['relation_name']
            print(f"[query_relationship] 收到请求 - company1: {data.get('company1')}, company2: {data.get('company2')}, relation_name: {relation_name}")
            
            if data['company1'] and data['company2']:
                label1 = data['company1'][0]['label']
                value1 = data['company1'][0]['value']
                label2 = data['company2'][0]['label']
                value2 = data['company2'][0]['value']
                print(f"[query_relationship] 查询公司1 - label: {label1}, value: {value1}")
                print(f"[query_relationship] 查询公司2 - label: {label2}, value: {value2}")
                
                node1 = None
                node2 = None
                if label1 == 'company_name':
                    node1 = matcher.match("Company").where(f"_.公司中文名称= '{value1}'").first()
                elif label1 == 'credit_number':
                    node1 = matcher.match("Company").where(f"_.社会信用代码= '{value1}'").first()
                if label2 == 'company_name':
                    node2 = matcher.match("Company").where(f"_.公司中文名称= '{value2}'").first()
                elif label2 == 'credit_number':
                    node2 = matcher.match("Company").where(f"_.社会信用代码= '{value2}'").first()
                
                print(f"[query_relationship] 查询结果 - node1: {node1 is not None}, node2: {node2 is not None}")
                
                if not node1 or not node2 and not relation_name:
                    print(f"[query_relationship] 错误: 公司不存在 - node1存在: {node1 is not None}, node2存在: {node2 is not None}, relation_name: {relation_name}")
                    return JsonResponse({'status': 'error', 'message': 'company not existed'})
                elif node1 and node2:
                    com1 = dict(node1)
                    com2 = dict(node2)
                    print(f"[query_relationship] 开始查询关系 - 公司1代码: {com1['社会信用代码']}, 公司2代码: {com2['社会信用代码']}, 关系类型: {relation_name}")
                    relation_data = QueryRelationship(com1['社会信用代码'], com2['社会信用代码'], relation_name)
                    if not relation_data:
                        print(f"[query_relationship] 错误: 关系不存在 - 公司1: {com1['社会信用代码']}, 公司2: {com2['社会信用代码']}, 关系: {relation_name}")
                        return JsonResponse({'status': 'error', 'message': 'no relationship exists'})
                    else:
                        formatted_relation_data = format_relationship_data(relation_data)
                        print(f"[query_relationship] 成功: 找到 {len(formatted_relation_data)} 条关系数据")
                        return JsonResponse({'status': 'success', 'relationships': formatted_relation_data})
            elif relation_name:
                print(f"[query_relationship] 仅查询关系类型: {relation_name}")
                relation_data = QueryRelationship_withnonode(relation_name)
                formatted_relation_data = format_relationship_data(relation_data)
                print(f"[query_relationship] 成功: 找到 {len(formatted_relation_data)} 条关系数据")
                return JsonResponse({'status': 'success', 'relationships': formatted_relation_data})
            else:
                print(f"[query_relationship] 警告: 参数不足，请重试")
                return JsonResponse({'status': 'success', 'message': 'please try again'})
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
            df["公司是否在知识图谱中"] = [
                "是" if matcher.match("Company").where(f"_.公司中文名称= '{company}'").first() else "否"
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