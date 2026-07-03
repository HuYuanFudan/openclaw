# financialKG

金融知识图谱前后端仓库。

- 前端：`front/`（Vue 3 + Element Plus + axios + D3.js + mathlive）
- 后端：`knowledgegraph/`（Django 4.2 + DRF + SimpleJWT + py2neo + SQLite + Celery）
- 数据扫描脚本：仓库根目录下的 `scan_*.py`、`inspect_litigation.py`、`refine_violation_types.py` 等
- 离线关系抽取脚本：`lsydata/data/financedata/laguanxi.py`（基于 Ollama / qwen2.5:32b）
- 详细分析报告：[`knowledgegraph/仓库详细分析报告.md`](knowledgegraph/仓库详细分析报告.md)
- 工作汇报：[`工作汇报.md`](工作汇报.md)、[`新闻关系提取功能汇报.md`](新闻关系提取功能汇报.md)、[`跨文档实体关系抽取功能开发汇报.md`](跨文档实体关系抽取功能开发汇报.md)

## 仓库结构

```text
openclaw/
├── front/                          # 前端项目（Vue 3）
│   ├── src/
│   │   ├── router/index.js         # 路由定义
│   │   ├── main.js                 # axios/Element Plus 全局配置
│   │   ├── views/                  # 各功能页面
│   │   ├── data/kg_report.js       # 知识图谱报告静态数据（约 117MB）
│   │   └── components/
│   ├── public/                     # 跨文档抽取数据集等静态资源
│   └── package.json
├── knowledgegraph/                 # 后端项目（Django）
│   ├── knowledgegraph/
│   │   ├── settings.py             # Django 配置（含硬编码密钥与 Neo4j 地址）
│   │   ├── urls.py                 # URL 路由
│   │   ├── views.py                # 视图（节点/关系/元知识/新闻关系抽取）
│   │   ├── models.py               # CustomUser / MetaKnowledge / Formula / Variable
│   │   ├── relation_extractor.py   # 基于 Ollama 的关系抽取器
│   │   ├── management/commands/    # create_custom_users / create_metaknowledge
│   │   ├── companynameparser/      # 公司名相似度匹配
│   │   ├── permissions.py          # IsNeo4jUser / IsMetaKnowledgeUser
│   │   └── decorators.py           # neo4j_user_required / metaknowledge_user_required
│   ├── requirements.txt
│   ├── uwsgi.ini                   # uWSGI 部署配置（含硬编码旧路径）
│   ├── db.sqlite3
│   └── 仓库详细分析报告.md
├── lsydata/data/financedata/       # 离线关系预测脚本与数据
│   ├── laguanxi.py                 # 调 Ollama 预测 7 类关系
│   ├── test.md
│   ├── 完整_已知实体匹配/
│   └── 完整_已知实体匹配_关系预测结果1/
├── 后端开发/                        # 后端开发与功能汇报文档
├── scan_*.py                       # 9 个图谱扫描脚本（详见下文）
├── inspect_litigation.py
├── refine_violation_types.py
├── map_to_kg_relations.py
├── reclassify_relations.py
├── kg_*.json                       # 4 份扫描结果报告
├── reclassified_relations.json
├── same_event_relations.json
└── *.md                            # 各类汇报与决策文档
```

## 运行前准备

你至少需要准备：

- Python 3（建议 3.8+）
- pip
- Node.js 与 npm
- 可访问的 Neo4j 实例（当前默认连接 `neo4j://10.176.22.62:7687`，账号 `neo4j` / 密码 `neo4j6008`，见 [knowledgegraph/knowledgegraph/views.py:37](knowledgegraph/knowledgegraph/views.py#L37)）
- 可选：Redis（Celery broker，默认 `redis://localhost:8000/0`，见 [knowledgegraph/knowledgegraph/settings.py:168](knowledgegraph/knowledgegraph/settings.py#L168)）
- 可选：Ollama（关系抽取用，模型 `qwen3.6:27b` / `qwen2.5:32b`）

当前仓库**没有**提供 `Dockerfile`、`docker-compose` 或 `.env` 文件；很多配置仍写死在代码里。

## 后端启动

```bash
cd /home/huyuan/openclaw/knowledgegraph
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8001
```

说明：

- 这里建议先跑在 `8001`，因为当前前端很多页面把后端地址直接写成了 `:8001`，例如 [front/src/views/Login_neo4j.vue:66](front/src/views/Login_neo4j.vue#L66)、[front/src/views/QueryNode.vue:149](front/src/views/QueryNode.vue#L149)。
- 如果你改成 `8000` 或其他端口，需要同步调整前端页面里的硬编码地址。
- 部分前端页面（如 [AddRelationship_excel.vue:112](front/src/views/AddRelationship_excel.vue#L112)）使用 `http://localhost:8001/`，部分页面（如 [AllMetaknowledge.vue:81](front/src/views/AllMetaknowledge.vue#L81)）使用 `http://10.176.22.62:8001/`，两套地址都需要按本机环境调整。

### 可选：初始化默认用户

仅在**全新 SQLite 数据库**场景下再执行：

```bash
cd /home/huyuan/openclaw/knowledgegraph
source .venv/bin/activate
python manage.py create_custom_users
```

注意：

- 该命令定义在 [knowledgegraph/knowledgegraph/management/commands/create_custom_users.py:4](knowledgegraph/knowledgegraph/management/commands/create_custom_users.py#L4)。
- 默认创建两个用户：`neo4j` / `neo4j6008`（图谱用户），`metaknowledge` / `metaknowledge6008`（元知识用户）。
- 如果数据库里已经有这些用户，就不要重复执行。

## 前端启动

```bash
cd /home/huyuan/openclaw/front
npm install
npm run serve
```

前端构建命令：

```bash
cd /home/huyuan/openclaw/front
npm run build
```

主要依赖见 [front/package.json](front/package.json)：`vue@^3.2.13`、`vue-router@^4.4.5`、`element-plus@^2.8.3`、`axios@^1.7.7`、`d3@^7.9.0`、`mathlive@^0.103.0`。

## 当前可见的主要页面

路由定义见 [front/src/router/index.js:18](front/src/router/index.js#L18)：

| 路径 | 组件 | 功能 |
|------|------|------|
| `/login` | `Login_neo4j.vue` | 登录 |
| `/home` | `HomeView.vue` | 主容器（左侧菜单切换子组件，需登录） |
| `/addnode` | `AddNode.vue` | 单独添加节点 |
| `/deletenode` | `DeleteNode.vue` | 删除节点 |
| `/querynode` | `QueryNode.vue` | 查询节点 |
| `/queryrelationship` | `QueryRelationship.vue` | 查询关系 |
| `/allgraph` | `AllGraph.vue` | 全图谱（直接请求 Neo4j `:7474`） |
| `/allmetaknowledge` | `AllMetaknowledge.vue` | 元知识列表 |
| `/addmetaknowledge` | `AddMetaKnowledge.vue` | 添加元知识 |
| `/formula` | `formula.vue` | 公式编辑 |
| `/cross-doc-extract` | `CrossDocEntityExtract.vue` | 跨文档实体关系抽取 |
| `/evidence-decision` | `EvidenceEnhancedDecision.vue` | 证据增强决策（菜单中已隐藏） |
| `/kg-test` | `KnowledgeGraphTest.vue` | 知识图谱功能测试（5 个子页面） |

`HomeView.vue` 通过 `showComponent` 在主区域切换的子组件还包括：`AddNode_excel`、`QueryNode_excel`、`CompareName`、`Fuzzy_match`、`SubGraph`、`AddRelationship_excel` 等。

## 后端 API 一览

URL 路由定义见 [knowledgegraph/knowledgegraph/urls.py](knowledgegraph/knowledgegraph/urls.py)：

| 路径 | 方法 | 视图 | 说明 |
|------|------|------|------|
| `/login/` | POST | `MyTokenObtainPairView` | 登录，返回 JWT access/refresh |
| `/addnode/` | POST | `AddNodeView` | 单独添加公司节点 |
| `/addnodeexcel/` | POST | `AddNodeExcelView` | Excel 批量添加节点 |
| `/querynode/` | POST | `query_node` | 按条件查询公司 |
| `/deletenode/` | POST | `DeleteNodeView` | 按社会信用代码删除节点 |
| `/addrelationshipexcel/` | POST | `AddRelationshipExcelView` | Excel 批量添加关系 |
| `/queryrelationship/` | POST | `query_relationship` | 查询两公司间关系 |
| `/querynodeexcel/` | POST | `query_node_excel` | Excel 批量查询公司，返回带"是否在图谱中"列的 xlsx |
| `/fuzzymatch/` | POST | `fuzzymatch` | 按公司名/曾用名模糊匹配 |
| `/fmatexcel/` | POST | `fmatexcel` | 模糊匹配结果导出为 Excel |
| `/qynodedtil/` | POST | `qynodedtil` | 按社会信用代码查询公司详情 |
| `/getprogress/` | GET | `getprogress` | 获取批量任务进度（基于 Django cache） |
| `/meta/allmetaknowledge/` | CRUD | `MetaKnowledgeViewSet` | 元知识 + 公式 + 变量增删改查 |
| `/extract_relation/` | POST | `ExtractRelationView` | 新闻文本关系抽取（调 `RelationExtractor`） |
| `/query_relations/` | POST | `QueryRelationsView` | 按公司名查询抽取到的关系 |
| `/get_companies/` | GET | `GetAllCompaniesView` | 获取所有已收录公司列表 |
| `/add_company/` | POST | `AddCompanyView` | 新增公司到抽取数据集 |

新闻关系抽取依赖 [knowledgegraph/knowledgegraph/relation_extractor.py](knowledgegraph/knowledgegraph/relation_extractor.py)，默认使用 Ollama（`http://localhost:11434/api/generate`，模型 `qwen3.6:27b`），并将结果写入 `front/public/cross_doc_dataset_updated.json`。

## 数据扫描脚本

仓库根目录下有一组对 Neo4j 图谱做离线扫描的 Python 脚本，输出 4 份 JSON 报告：

| 脚本 | 用途 |
|------|------|
| [scan_kg_data.py](scan_kg_data.py) | 基础扫描：节点/关系总数、公司上市状态、行业分布 |
| [scan_kg_detailed.py](scan_kg_detailed.py) | 详细扫描：违规事件行业分布、诉讼案件原被告行业、涉案缘由 |
| [scan_kg_detailed2.py](scan_kg_detailed2.py) | 二次详细扫描：违规类型细化、诉讼金额区间、金融风险类型 |
| [scan_universal.py](scan_universal.py) | 全量扫描：遍历所有 label 和关系 type 的全部属性字段 |
| [scan_deep_fields.py](scan_deep_fields.py) | 深度挖掘：MetaKnowledge/Company/PLEDGE/GUARANTEES 等详细属性 |
| [scan_financial_risk.py](scan_financial_risk.py) | 风险分类：将 MetaKnowledge 分类为 9 类风险 |
| [scan_extra_fields.py](scan_extra_fields.py) | 额外字段：实际控制人类型、资本背景、省份分布 |
| [scan_more_finer.py](scan_more_finer.py) | 更细粒度：处罚金额区间、处分措施、违规年度 |
| [scan_p25x_full.py](scan_p25x_full.py) | P25xx 违规类型编码全量扫描 |
| [refine_violation_types.py](refine_violation_types.py) | 违规类型归一化与精炼 |
| [inspect_litigation.py](inspect_litigation.py) | 诉讼案件字段探查 |
| [map_to_kg_relations.py](map_to_kg_relations.py) | 关系类型映射 |
| [reclassify_relations.py](reclassify_relations.py) | 关系重新分类 |

输出报告：`kg_data_report.json`、`kg_detailed_report.json`、`kg_financial_risk.json`、`kg_universal_scan.json`、`reclassified_relations.json`、`same_event_relations.json`。

注意：这些脚本里 Neo4j 连接地址同样硬编码为 `neo4j://10.176.22.62:7687`，迁移环境时需要手动修改。

## 推荐的本地联调方式

当前仓库最接近"可直接体验"的方式是：

1. 先启动 Django，并监听 `8001`
2. 再启动 Vue 开发服务器（默认 `8080`）
3. 把前端开发地址加入后端 CORS 白名单（见下文）
4. 打开前端登录页，先验证登录、查节点、查关系、元知识列表、跨文档抽取这几条主链路

## 使用时必须注意的几个问题

### 1. 前端接口地址没有统一

虽然 [front/src/main.js:60](front/src/main.js#L60) 设置了 axios `baseURL`，但很多页面没有使用它，而是直接写死地址，例如：

- `http://10.176.22.62:8001/...`：[Login_neo4j.vue:66](front/src/views/Login_neo4j.vue#L66)、[AllMetaknowledge.vue:81](front/src/views/AllMetaknowledge.vue#L81)、[AddMetaKnowledge.vue:89](front/src/views/AddMetaKnowledge.vue#L89)、[CrossDocEntityExtract.vue:538](front/src/views/CrossDocEntityExtract.vue#L538)、[Fuzzy_match.vue:71](front/src/views/Fuzzy_match.vue#L71)、[QueryNode_excel.vue:71](front/src/views/QueryNode_excel.vue#L71)、[SubGraph.vue:58](front/src/views/SubGraph.vue#L58)
- `http://localhost:8001/...`：[AddRelationship_excel.vue:112](front/src/views/AddRelationship_excel.vue#L112)
- 直连 Neo4j `:7474`：[AllGraph.vue:20](front/src/views/AllGraph.vue#L20)

如果你不是在原来的固定服务器环境运行，通常需要把这些地址改成你当前机器的地址。

### 2. 本地开发可能会遇到 CORS

当前后端 CORS 白名单在 [knowledgegraph/knowledgegraph/settings.py:27](knowledgegraph/knowledgegraph/settings.py#L27)，只允许固定来源：

```python
CORS_ALLOWED_ORIGINS = [
    "http://10.176.22.62:8080",
    "http://172.29.192.1:8080"
]
```

如果你本地直接 `npm run serve`，很可能还需要把你的前端地址（如 `http://localhost:8080`）加进 CORS 白名单，并同步更新 `CSRF_TRUSTED_ORIGINS`。

### 3. 登录 token 键名不一致

- [front/src/main.js:55](front/src/main.js#L55) 读取 `jwt_token`
- [front/src/views/Login_neo4j.vue:72](front/src/views/Login_neo4j.vue#L72) 写入 `access_token`
- [front/src/router/index.js:77](front/src/router/index.js#L77) 也读取 `access_token`

这会导致刷新页面后，请求头和登录态判断可能不一致。

### 4. 不要直接使用旧的元知识初始化脚本

[knowledgegraph/knowledgegraph/management/commands/create_metaknowledge.py:25](knowledgegraph/knowledgegraph/management/commands/create_metaknowledge.py#L25) 仍在引用已经删除的字段（`formula`），不适合作为当前初始化方案；它实际上是一个独立运行的脚本而非标准 Django management command。

### 5. 后端默认权限完全放开

[knowledgegraph/knowledgegraph/settings.py:75](knowledgegraph/knowledgegraph/settings.py#L75) 中 `DEFAULT_PERMISSION_CLASSES` 为 `AllowAny`，并且绝大多数视图的 `permission_classes = []`，因此节点/关系/元知识接口实际上不需要登录即可访问。仅在 `MetaKnowledgeViewSet` 等少数地方通过 `IsNeo4jUser` / `IsMetaKnowledgeUser` 做了用户类型校验。

## 部署相关提醒

- [knowledgegraph/uwsgi.ini:4](knowledgegraph/uwsgi.ini#L4) 仍是旧机器绝对路径 `/home/wangsiyuan/wsy/financial_knowledgegraph_tool/knowledgegraph`，部署前必须先改。
- 后端里硬编码的 Neo4j 连接配置：[knowledgegraph/knowledgegraph/views.py:37](knowledgegraph/knowledgegraph/views.py#L37)。
- Django `SECRET_KEY` 也直接写在 [knowledgegraph/knowledgegraph/settings.py:23](knowledgegraph/knowledgegraph/settings.py#L23)。
- `DEBUG = True`、`ALLOWED_HOSTS = ['*']`，生产部署前需要收紧。
- Celery broker 默认指向 `redis://localhost:8000/0`（注意端口是 8000，与一般 Redis 6379 不同），见 [knowledgegraph/knowledgegraph/settings.py:168](knowledgegraph/knowledgegraph/settings.py#L168)。

## 离线关系预测（lsydata）

[lsydata/data/financedata/laguanxi.py](lsydata/data/financedata/laguanxi.py) 是一套独立的离线脚本，读取 `完整_已知实体匹配/` 下的输入，调用本地 Ollama（`qwen2.5:32b`，`http://localhost:11434`）对每对公司预测 7 类关系：无关系、子公司、起诉、客户、供应商、担保、质押，并把结果写入 `完整_已知实体匹配_关系预测结果1/`。脚本里的输入/输出路径硬编码为 `/home/lushiyin/data/financedata/...`，迁移时需要修改。

## 建议你先看什么

如果你刚接手这个仓库，建议按下面顺序阅读：

1. `README.md`
2. [front/src/router/index.js](front/src/router/index.js)
3. [front/src/main.js](front/src/main.js)
4. [front/src/views/HomeView.vue](front/src/views/HomeView.vue)
5. [knowledgegraph/knowledgegraph/urls.py](knowledgegraph/knowledgegraph/urls.py)
6. [knowledgegraph/knowledgegraph/views.py](knowledgegraph/knowledgegraph/views.py)
7. [knowledgegraph/knowledgegraph/relation_extractor.py](knowledgegraph/knowledgegraph/relation_extractor.py)
8. [knowledgegraph/仓库详细分析报告.md](knowledgegraph/仓库详细分析报告.md)
9. [工作汇报.md](工作汇报.md)
