# 知识图谱三元组/四元组可加入判定方案（推荐实现）

## 1) 目标与已确认需求

目标：新增一个“判定接口”，输入三元组或带时序四元组，输出该事实是否可加入知识图谱，并给出理由与判断依据。

已确认需求：
- 判定方式：**规则校验 + 打分**。
- 输出形式：**布尔 + 原因**（并包含冲突信息/判断依据）。
- 时序支持：同时支持**时点**与**区间**。
- 实体标识：**社会信用代码 + 公司中文名称都支持**（优先信用代码，名称兜底）。
- 未出现过的关系类型：输出理由并进入**人工复核**。
- 执行范围：**判定后可选写入**（例如 `commit=true` 时写入）。

---

## 2) 现有代码落点（基于当前仓库）

- Neo4j连接与匹配器：`knowledgegraph/views.py:37-42`
- 关系存在性检查（可复用）：`knowledgegraph/views.py:178-196`（`QueryRelationship_byname`）
- 关系批量新增逻辑（可复用写入模式）：`knowledgegraph/views.py:330-377`（`AddRelationshipExcelView`）
- 节点查询/匹配模式（可复用实体存在检查）：`knowledgegraph/views.py:135-168`、`knowledgegraph/views.py:378-436`
- 路由入口：`knowledgegraph/urls.py:25-43`
- 项目配置：`knowledgegraph/settings.py:90-102`

---

## 3) 接口契约（单一路径）

### 3.1 请求
`POST /fact-admission/`

```json
{
  "subject": {"id_type": "credit_number|company_name", "id_value": "..."},
  "predicate": "投资",
  "object": {"id_type": "credit_number|company_name", "id_value": "..."},
  "temporal": {
    "mode": "instant|interval",
    "event_time": "2025-01-01T00:00:00Z",
    "start_time": "2025-01-01T00:00:00Z",
    "end_time": "2025-12-31T00:00:00Z"
  },
  "attributes": {},
  "commit": false
}
```

说明：
- 三元组：可不传 `temporal`。
- 四元组（时点）：`mode=instant` + `event_time`。
- 四元组（区间）：`mode=interval` + `start_time/end_time`。
- `commit` 默认 `false`；仅判定不写入。

### 3.2 响应
```json
{
  "can_add": false,
  "reasons": ["predicate 未在现有关系类型中出现"],
  "decision_basis": {
    "score": 0.58,
    "threshold": 0.65,
    "hard_checks": {
      "subject_exists": true,
      "object_exists": true,
      "duplicate_relation": false,
      "temporal_conflict": false
    }
  },
  "conflicts": [],
  "review_required": true,
  "written": false
}
```

---

## 4) 判定流水线

### Layer A：结构校验（失败即拒绝）
- 必填字段完整性（subject/predicate/object）。
- `id_type` 只能是 `credit_number|company_name`。
- temporal 校验：
  - `instant` 必须有 `event_time`；
  - `interval` 必须有 `start_time/end_time` 且 `start_time <= end_time`。

### Layer B：图一致性校验（硬规则）
- 主体/客体实体存在性（优先社会信用代码，其次公司中文名称）。
- 重复关系检测（复用 `QueryRelationship_byname` 思路）。
- 时序冲突检测：
  - 区间与既有区间重叠；
  - 时点落入既有排斥区间（若业务定义有排斥关系）。

### Layer C：评分层（无需训练新模型）
- 使用规则特征加权打分（如：实体存在、无重复、无冲突、关系类型是否已知等）。
- 阈值读取配置（例如 `FACT_ADMISSION_THRESHOLD`）。

### Layer D：结论层
- 若触发硬拒绝：`can_add=false`。
- 若 `predicate` 为新类型：`review_required=true`，并输出判断依据（可设置 `can_add=false` 进入人工复核）。
- 其余按 `score >= threshold` 决定 `can_add`。
- 若 `can_add=true 且 commit=true`：执行关系写入；否则仅返回判定。

---

## 5) 代码改动计划（最小改动优先）

### 修改文件 1：`/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/views.py`
- 新增 `FactAdmissionView(APIView)`（POST）。
- 在该文件内新增少量私有辅助函数（先不拆新模块，降低改动面）：
  - 实体解析与查询（支持双标识）
  - 重复关系检测
  - 时序冲突检测
  - 评分计算与结论组装
  - 可选写入（复用 `Relationship(...)` + `graph.create(...)` 模式，参考 `views.py:355-356`）

### 修改文件 2：`/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/urls.py`
- 增加路由：`path('fact-admission/', views.FactAdmissionView.as_view(), name='fact_admission')`

### 修改文件 3：`/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/settings.py`
- 增加阈值配置，例如：`FACT_ADMISSION_THRESHOLD = 0.65`

> 备注：如实现中发现 `views.py` 过大，再将辅助逻辑抽到 `knowledgegraph/admission_service.py`，但作为第二步优化，不作为首选路径。

---

## 6) 测试计划（实施时执行）

- 三元组通过：实体存在、关系不重复、无冲突 -> `can_add=true`
- 时点四元组通过：`mode=instant` 合法 -> `can_add=true`
- 区间四元组通过：`start<=end` 且无重叠冲突 -> `can_add=true`
- 缺字段/非法时间 -> `can_add=false`
- 主体或客体不存在 -> `can_add=false`
- 已有同向同类型关系 -> `can_add=false`
- predicate 新类型 -> `review_required=true`，返回清晰 `reasons` 与 `decision_basis`
- `commit=true` 且通过时验证成功写入；`commit=false` 确认不写入

---

## 7) 交付顺序

1. 先实现“仅判定（commit=false）”全流程与返回结构。
2. 再加“可选写入（commit=true）”。
3. 最后补充阈值配置与测试用例。

该方案保持最小改动，直接贴合现有 `views.py + urls.py` 结构，可快速落地并便于后续迭代。
