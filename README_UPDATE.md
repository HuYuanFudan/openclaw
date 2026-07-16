# README.md 更新内容

## 需要添加到 README.md 的变更

### 1. 工作汇报文档链接（第10行后添加）

```markdown
- 本次重构汇报：[`WORK_REPORT.md`](WORK_REPORT.md)
```

### 2. 后端 API 列表新增（第164行后添加）

```markdown
| `/graph_stats/` | GET | `GraphStatsView` | 获取知识图谱核心统计指标（节点/关系/行业分布） |
```

### 3. 页面列表更新（第138行修改）

将：
```markdown
| `/kg-test` | `KnowledgeGraphTest.vue` | 知识图谱功能测试（5 个子页面） |
```

改为：
```markdown
| `/kg-test` | `KnowledgeGraphTest.vue` | 知识图谱功能测试（实体分布统计、图谱金融风险知识） |
```

### 4. 新增章节：金融风险分类（建议在数据扫描脚本章节后添加）

```markdown
## 金融风险分类体系

图谱金融风险知识页面采用五大类风险分类框架（基于巴塞尔协议）：

| 风险类型 | 数据来源 | 核心指标 | 典型风险点 |
|----------|----------|----------|------------|
| 市场风险 | MetaKnowledge、证券市场数据 | 股债对冲效应、灾难风险溢价 | 极端尾部风险、市场过度波动 |
| 信用风险 | GUARANTEES、PLEDGE、担保质押 | 对外担保、股权质押、客户异常 | 或有负债、平仓爆仓风险 |
| 操作风险 | Violation、违规处罚记录 | 信息披露违规、管理层行为 | 内部控制缺陷、道德风险 |
| 流动性风险 | MetaKnowledge、投资者行为 | 现金持有、跨境资本流动 | 赎回压力、政策不确定性 |
| 声誉风险 | Violation、Litigation、处罚诉讼 | 监管处罚、诉讼仲裁、ST/*ST | 负面舆情、投资者信心 |

原12大类风险已重构为上述五大类，详见 [`WORK_REPORT.md`](WORK_REPORT.md)。
```

---

请手动将以上内容添加到 README.md 对应位置，然后执行：

```bash
git add README.md
git commit -m "docs: 更新 README.md，添加重构内容说明"
git push origin main
```
