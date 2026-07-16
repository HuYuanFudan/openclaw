# Cypher高级查询功能开发汇报

## 一、项目背景

为提升知识图谱管理系统的查询分析能力，在"节点操作-查询节点"和"节点操作-模糊匹配"页面中集成Neo4j Cypher高级查询功能，实现对知识图谱的深度分析与可视化展示。

---

## 二、开发内容

### 2.1 后端API开发

**文件位置：** `knowledgegraph/knowledgegraph/views.py`

新增四个API视图类，共计约274行代码：

| API类名 | 路由 | 功能说明 |
|---------|------|----------|
| `CypherSubgraphView` | `/cypher_subgraph/` | N跳子图查询 |
| `RiskPathView` | `/risk_path/` | 风险分析 |
| `RelationDistributionView` | `/relation_distribution/` | 关系类型分布 |
| `RelatedCompanyNetworkView` | `/related_company_network/` | 关联公司网络 |

### 2.2 路由配置

**文件位置：** `knowledgegraph/knowledgegraph/urls.py`

新增四条路由：
```python
path('cypher_subgraph/', CypherSubgraphView.as_view()),
path('risk_path/', RiskPathView.as_view()),
path('relation_distribution/', RelationDistributionView.as_view()),
path('related_company_network/', RelatedCompanyNetworkView.as_view()),
```

### 2.3 前端页面改造

#### 2.3.1 查询节点页面 (QueryNode.vue)

**变更统计：** +251行

**新增功能：**
- 表格新增"操作"列，包含"查看详情"按钮
- 公司详情对话框（el-dialog）
- 高级Cypher查询区域（四个查询按钮）
- 各查询结果的可视化展示区域

**新增数据属性：**
```javascript
dialogVisible: false,
companyDetails: {},
loadingStates: {
  subgraph: false,
  riskPath: false,
  relation: false,
  network: false
},
subgraphResult: {},
riskPathResult: {},
relationDistResult: {},
relatedNetworkResult: {}
```

**新增方法：**
- `viewDetails(row)` - 查看公司详情
- `querySubgraph()` - N跳子图查询
- `queryRiskPath()` - 风险分析查询
- `queryRelationDistribution()` - 关系类型分布查询
- `queryRelatedCompanyNetwork()` - 关联公司网络查询

#### 2.3.2 模糊匹配页面 (Fuzzy_match.vue)

**变更统计：** +364行（与QueryNode.vue功能一致）

**新增功能：**
- 与QueryNode.vue相同的Cypher查询功能
- 表格操作列
- 公司详情对话框
- 四个Cypher查询按钮及结果展示

---

## 三、功能详解

### 3.1 N跳子图查询

**功能描述：** 从指定公司节点出发，查询1-5跳范围内的所有节点和关系，可视化展示子图结构。

**参数：**
- `credit_number`: 社会信用代码
- `hops`: 跳数（1-5）

**返回数据：**
```json
{
  "nodes": [{"name": "公司名", "type": "节点类型"}],
  "edges": [{"source": "起点", "target": "终点", "relation": "关系类型"}],
  "node_count": 节点数量,
  "edge_count": 边数量
}
```

**Cypher查询语句：**
```cypher
MATCH path = (start:Company {`社会信用代码`: $credit_number})-[*1..{hops}]-(end)
WHERE NOT end:MetaKnowledge
RETURN start.`公司中文名称` as start_name,
       end.`公司中文名称` as end_name,
       [rel in relationships(path) | type(rel)] as rel_types,
       length(path) as path_length,
       labels(end) as end_labels
ORDER BY path_length
LIMIT 100
```

### 3.2 风险分析

**功能描述：** 查询某公司到违规/诉讼节点的最短路径，帮助识别潜在风险传导链。

**参数：**
- `credit_number`: 社会信用代码

**返回数据：**
```json
{
  "violation_paths": [
    {
      "company": "公司名",
      "violation_type": "违规类型",
      "handler": "处理单位",
      "penalty_date": "处罚日期",
      "path_length": 路径长度
    }
  ],
  "litigation_paths": [
    {
      "company": "公司名",
      "case_reason": "涉案缘由",
      "amount": "涉案金额",
      "litigation_type": "司法类型",
      "path_length": 路径长度
    }
  ]
}
```

**Cypher查询语句：**
```cypher
// 违规路径
MATCH (c:Company {`社会信用代码`: $credit_number})
MATCH (v:Violation)
MATCH path = shortestPath((c)-[*1..5]-(v))
RETURN c.`公司中文名称` as company,
       v.`违规类型` as violation_type,
       v.`处理单位` as handler,
       v.`处罚日期` as penalty_date,
       length(path) as path_length
LIMIT 5

// 诉讼路径
MATCH (c:Company {`社会信用代码`: $credit_number})
MATCH (l:Litigation)
MATCH path = shortestPath((c)-[*1..5]-(l))
RETURN c.`公司中文名称` as company,
       l.`涉案缘由` as case_reason,
       l.`涉案金额` as amount,
       l.`司法类型` as litigation_type,
       length(path) as path_length
LIMIT 5
```

### 3.3 关系类型分布

**功能描述：** 统计某节点涉及的所有关系类型和数量，区分出边和入边。

**参数：**
- `credit_number`: 社会信用代码

**返回数据：**
```json
{
  "company_name": "公司名称",
  "outgoing_relations": [
    {"type": "关系类型", "count": 数量, "target_labels": ["目标节点类型"]}
  ],
  "incoming_relations": [
    {"type": "关系类型", "count": 数量, "source_labels": ["来源节点类型"]}
  ],
  "total_outgoing": 出边总数,
  "total_incoming": 入边总数
}
```

**Cypher查询语句：**
```cypher
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
```

### 3.4 关联公司网络

**功能描述：** 查询某公司的子公司、客户、供应商、母公司等关联公司网络。

**参数：**
- `credit_number`: 社会信用代码

**返回数据：**
```json
{
  "company_name": "公司名称",
  "subsidiaries": ["子公司1", "子公司2"],
  "customers": ["客户1", "客户2"],
  "suppliers": ["供应商1", "供应商2"],
  "parents": ["母公司"],
  "sub_count": 子公司数量,
  "cust_count": 客户数量,
  "supplier_count": 供应商数量
}
```

**Cypher查询语句：**
```cypher
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
```

---

## 四、界面变更

### 4.1 查询节点页面

**变更前：** 仅显示查询结果表格，无详情查看功能

**变更后：**
- 表格新增"操作"列，包含"查看详情"按钮
- 点击"查看详情"弹出对话框
- 对话框显示公司详情及四个Cypher查询按钮
- 点击按钮展示查询结果

### 4.2 模糊匹配页面

**变更前：** 仅显示模糊匹配结果表格，支持Excel下载

**变更后：**
- 新增"操作"列和"查看详情"按钮
- 完整的Cypher查询功能（与查询节点页面一致）

---

## 五、代码变更统计

| 文件 | 新增行 | 删除行 | 净增加 |
|------|--------|--------|--------|
| `front/src/views/QueryNode.vue` | 251 | 0 | +251 |
| `front/src/views/Fuzzy_match.vue` | 364 | 30 | +334 |
| `front/src/views/KnowledgeGraphTest.vue` | 51 | 0 | +51 |
| `knowledgegraph/knowledgegraph/views.py` | 274 | 0 | +274 |
| `knowledgegraph/knowledgegraph/urls.py` | 11 | 0 | +11 |
| **总计** | **951** | **30** | **+921** |

---

## 六、技术要点

### 6.1 前端状态管理

使用多个独立的loading状态控制按钮加载动画：
```javascript
loadingStates: {
  subgraph: false,
  riskPath: false,
  relation: false,
  network: false
}
```

### 6.2 错误处理

所有API调用均包含try-catch错误处理，并通过Element Plus的$message组件提示用户。

### 6.3 数据可视化

- 子图结果使用表格展示节点和边列表
- 风险分析使用分组表格展示违规和诉讼记录
- 关系分布使用双列布局展示出入边统计
- 关联公司使用分组列表展示各类关联方

---

## 七、后续建议

1. **子图可视化：** 使用D3.js对N跳子图进行图形化展示
2. **路径高亮：** 在全图谱中高亮显示风险路径
3. **导出功能：** 支持将查询结果导出为Excel或PDF
4. **性能优化：** 对大规模子图查询添加分页和限制

---

**文档生成时间：** 2026-07-02  
**开发负责人：** AI Assistant  
**版本：** v1.1
