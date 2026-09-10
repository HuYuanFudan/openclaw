-- ============================================
-- Neo4j 知识图谱索引与约束创建脚本
-- 执行方式：在 Neo4j Browser 中逐条执行，或neo4j-shell批量执行
-- 执行前建议：先备份数据库（neo4j-admin dump）
-- ============================================

-- ============================================
-- 第一部分：唯一约束（Unique Constraints）
-- 作用：确保字段唯一性，同时自动创建索引
-- 注意：如果存在重复数据，约束创建会失败，需要先清理
-- ============================================

-- 1. 公司中文名称唯一约束
-- 原因：views.py:472/515/516/640 共4处按公司名查重，最频繁的查询条件
-- 效果：查重从O(n)扫描变为O(1)点查，同时杜绝重复写入
CREATE CONSTRAINT company_name_unique IF NOT EXISTS
FOR (c:Company) REQUIRE c.`公司中文名称` IS UNIQUE;

-- 2. 社会信用代码唯一约束
-- 原因：views.py:401/419/438 共3处按信用代码查重，删除/更新操作使用
-- 效果：同上，同时作为企业的唯一标识
CREATE CONSTRAINT company_credit_unique IF NOT EXISTS
FOR (c:Company) REQUIRE c.`社会信用代码` IS UNIQUE;

-- ============================================
-- 第二部分：普通索引（Indexes）
-- 作用：加速查询，不强制唯一性
-- ============================================

-- 3. A股证券代码索引
-- 原因：按股票代码查询公司，上市公司相关操作
-- 使用场景：前端搜索、关联证券信息
CREATE INDEX company_astock_idx IF NOT EXISTS
FOR (c:Company) ON (c.`A股证券代码`);

-- 4. B股证券代码索引
CREATE INDEX company_bstock_idx IF NOT EXISTS
FOR (c:Company) ON (c.`B股证券代码`);

-- 5. 股票简称索引
-- 原因：ST/*ST 风险警示查询（views.py:1663 风险警示统计）
CREATE INDEX company_abbr_idx IF NOT EXISTS
FOR (c:Company) ON (c.`股票简称`);

-- 6. 所属行业索引
-- 原因：行业分布统计、按行业筛选
CREATE INDEX company_industry_idx IF NOT EXISTS
FOR (c:Company) ON (c.`所属行业`);

-- ============================================
-- 第三部分：Violation 节点索引
-- ============================================

-- 7. 违规类型索引
-- 原因：views.py:1547 按违规类型过滤（信息披露违规统计）
-- 效果：加速违规事件分类查询
CREATE INDEX violation_type_idx IF NOT EXISTS
FOR (v:Violation) ON (v.`违规类型`);

-- 8. 处罚日期索引
-- 原因：按时间范围查询违规记录，时间序列分析
CREATE INDEX violation_date_idx IF NOT EXISTS
FOR (v:Violation) ON (v.`处罚日期`);

-- 9. 处理单位索引
-- 原因：views.py:1636 按处理单位过滤（监管处罚统计）
CREATE INDEX violation_authority_idx IF NOT EXISTS
FOR (v:Violation) ON (v.`处理单位`);

-- ============================================
-- 第四部分：Litigation 节点索引
-- ============================================

-- 10. 立案日期索引
-- 原因：诉讼案件时间序列分析
CREATE INDEX litigation_date_idx IF NOT EXISTS
FOR (l:Litigation) ON (l.`立案日期`);

-- 11. 案件类型索引
CREATE INDEX litigation_type_idx IF NOT EXISTS
FOR (l:Litigation) ON (l.`案件类型`);

-- ============================================
-- 第五部分：MetaKnowledge 节点索引
-- ============================================

-- 12. 风险类型索引
-- 原因：风险知识分类查询
CREATE INDEX metaknowledge_risk_idx IF NOT EXISTS
FOR (m:MetaKnowledge) ON (m.`风险类型`);

-- ============================================
-- 验证命令（创建后执行）
-- ============================================

-- 查看所有约束
SHOW CONSTRAINTS;

-- 查看所有索引
SHOW INDEXES;

-- 测试查询是否走索引（查看执行计划）
EXPLAIN MATCH (c:Company) WHERE c.`公司中文名称` = '万科企业股份有限公司' RETURN c;
EXPLAIN MATCH (c:Company) WHERE c.`社会信用代码` = '91440300192181490G' RETURN c;

-- ============================================
-- 可选：如果约束创建失败，先执行去重（需要 APOC 插件）
-- ============================================

-- 查找重复公司名
-- MATCH (c:Company)
-- WITH c.`公司中文名称` AS name, count(*) AS cnt
-- WHERE cnt > 1
-- RETURN name, cnt
-- ORDER BY cnt DESC
-- LIMIT 20;

-- 合并重复节点（谨慎执行）
-- MATCH (c:Company {`公司中文名称`: '重复的公司名'})
-- WITH c ORDER BY id(c)
-- WITH collect(c) AS nodes
-- CALL apoc.refactor.mergeNodes(nodes, {properties: 'combine', mergeRels: true})
-- YIELD node
-- RETURN node;
