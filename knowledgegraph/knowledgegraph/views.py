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
            query = f'''
            MATCH (n:Company)
            WHERE n.`公司中文名称` CONTAINS "{company_name}" OR n.`曾用名` CONTAINS "{company_name}"
            RETURN n
            '''
            result = graph.run(query).data()
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
            query = f'''
            MATCH (n:Company)
            WHERE n.`公司中文名称` CONTAINS "{company_name}" OR n.`曾用名` CONTAINS "{company_name}"
            RETURN n
            '''
            result = graph.run(query).data()
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