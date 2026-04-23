# 功能实现计划：文档输入 + 本地32B（Ollama）论元抽取与时序识别

## 1. 目标与范围（按你的确认）
- 输入：`纯文本`、`PDF`、`Word(docx)`
- 推理：调用本地 `Ollama` 的 32B 模型
- 输出：先返回 JSON（v1 不强制入库）
- 抽取内容：`论元 + 时间信息 + 证据句 + 置信度`

---

## 2. 关键改动文件

### 修改现有文件
1. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/views.py`
   - 新增 `DocumentExtractView(APIView)`，统一处理 text 与 file 两种输入。
2. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/urls.py`
   - 新增路由：`path('extract/', DocumentExtractView.as_view(), name='document_extract')`。
3. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/settings.py`
   - 新增配置：`OLLAMA_BASE_URL`、`OLLAMA_MODEL`、`OLLAMA_TIMEOUT`、`MAX_DOCUMENT_SIZE_MB`、`MAX_DOCUMENT_CHARS`。
4. `/home/ubuntu/code/financialKG/knowledgegraph/requirements.txt`
   - 新增文档解析依赖：`python-docx`、`PyPDF2`。

### 新增文件（最小必要）
5. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/services/ollama_client.py`
   - 封装 Ollama HTTP 调用（超时、错误码、响应解析）。
6. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/services/document_parser.py`
   - 解析 txt/pdf/docx 为纯文本。
7. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/services/prompts.py`
   - 固定 system prompt + 用户文本模板。
8. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/services/extraction_service.py`
   - 编排流程：解析文档 → 调用模型 → JSON校验/清洗 → 结构化返回。
9. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/services/__init__.py`
10. `/home/ubuntu/code/financialKG/knowledgegraph/knowledgegraph/tests/test_document_extract.py`

---

## 3. API 设计（v1）

### Endpoint
- `POST /extract/`

### 输入
- `application/json`
```json
{ "text": "..." }
```
- `multipart/form-data`
  - `file`: `.txt | .pdf | .docx`

### 输出（成功）
```json
{
  "status": "success",
  "data": {
    "arguments": [
      {
        "subject": "...",
        "predicate": "...",
        "object": "...",
        "temporal": {
          "raw": "2024年三季度",
          "normalized": "2024-Q3",
          "type": "period"
        },
        "evidence": "原文证据句",
        "confidence": 0.91
      }
    ],
    "metadata": {
      "model": "<ollama_model>",
      "input_chars": 1234
    }
  }
}
```

### 输出（失败）
```json
{
  "status": "error",
  "error_code": "MODEL_UNAVAILABLE | INVALID_FORMAT | OVERSIZED_DOC | PARSE_FAILURE | EXTRACTION_FAILED",
  "message": "..."
}
```

---

## 4. 实现步骤（执行顺序）
1. 在 `requirements.txt` 增加 `python-docx`、`PyPDF2`。
2. 在 `settings.py` 增加 Ollama 与文档大小配置。
3. 新增 `services/document_parser.py`：
   - 文本直通；PDF/DOCX 抽取文本；限制文件大小与字符数。
4. 新增 `services/prompts.py`：
   - 固定抽取指令，要求“仅返回 JSON”。
5. 新增 `services/ollama_client.py`：
   - 调 `/api/chat`，处理超时、连接失败、非200响应。
6. 新增 `services/extraction_service.py`：
   - 清洗模型输出（去 markdown 代码块）并做 JSON schema 校验。
7. 在 `views.py` 新增 `DocumentExtractView`：
   - 统一接收 text/file，调用 service，映射错误到 HTTP 状态码。
8. 在 `urls.py` 注册 `/extract/`。
9. 编写 `test_document_extract.py`（单测 + 接口测试，模型调用 mock）。

---

## 5. 安全与稳健性要求
- 不执行用户文本中的“指令”，仅把文本作为抽取对象。
- 模型输出必须 JSON 解析通过才返回成功。
- 限制文件大小与输入字符数，避免超大文档拖垮服务。
- 只允许 `.txt/.pdf/.docx`，并校验 MIME/扩展名。
- 记录错误日志时不落原文全文（避免敏感信息泄露）。

---

## 6. 测试计划
- 文本输入成功路径。
- PDF/DOCX 解析成功路径。
- 空输入、非法格式、超大文件。
- Ollama 不可达/超时。
- 模型返回非 JSON。
- 响应结构字段完整性：`arguments[].subject/predicate/object/temporal/evidence/confidence`。

---

## 7. 验收标准
- `POST /extract/` 能稳定处理 text/pdf/docx。
- 能返回“论元 + 时间 + 证据句 + 置信度”的结构化 JSON。
- 错误场景返回明确 `error_code` 与对应状态码。
- 测试覆盖核心流程与主要异常场景。
