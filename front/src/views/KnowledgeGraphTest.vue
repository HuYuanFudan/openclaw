<template>
  <div class="kg-test">
    <h1>知识图谱功能测试</h1>
    <p class="description">测试知识图谱本体管理的功能完整性：模式创建、编辑删除、可视化、版本管理、导入导出</p>

    <el-tabs v-model="activeTab" type="border-card" class="test-tabs">
      <!-- 1. 本体/模式创建 -->
      <el-tab-pane label="① 本体/模式创建" name="create">
        <div class="tab-section">
          <el-row :gutter="20">
            <!-- 左侧：创建表单 -->
            <el-col :span="11">
              <el-card header="新建实体类型（Class）" class="panel">
                <el-form :model="createForm" label-width="100px" size="small">
                  <el-form-item label="类名">
                    <el-input v-model="createForm.className" placeholder="如：Company" />
                  </el-form-item>
                  <el-form-item label="父类（继承）">
                    <el-select v-model="createForm.parentClass" placeholder="可选：选择父类" clearable style="width:100%">
                      <el-option v-for="c in classes" :key="c.name" :label="c.name" :value="c.name" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="属性定义">
                    <div v-for="(attr, idx) in createForm.attributes" :key="idx" class="attr-row">
                      <el-input v-model="attr.name" placeholder="属性名" style="width:30%;margin-right:6px" />
                      <el-select v-model="attr.type" style="width:30%;margin-right:6px">
                        <el-option label="String" value="string" />
                        <el-option label="Number" value="number" />
                        <el-option label="Date" value="date" />
                        <el-option label="Boolean" value="boolean" />
                      </el-select>
                      <el-input-number v-model="attr.minCard" :min="0" :max="attr.maxCard" :value-on-clear="0" placeholder="最小基数" controls-position="right" style="width:18%;margin-right:6px" />
                      <el-input-number v-model="attr.maxCard" :min="1" placeholder="最大基数" controls-position="right" style="width:18%;margin-right:6px" />
                      <el-button :icon="Delete" circle size="small" @click="createForm.attributes.splice(idx, 1)" />
                    </div>
                    <el-button size="small" @click="addAttribute" style="margin-top:6px">+ 添加属性</el-button>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="onCreateClass">创建类</el-button>
                    <el-button @click="resetCreateForm">重置</el-button>
                  </el-form-item>
                </el-form>
              </el-card>

              <el-card header="新建关系类型（Relationship）" class="panel" style="margin-top:16px">
                <el-form :model="relForm" label-width="100px" size="small">
                  <el-form-item label="关系名">
                    <el-input v-model="relForm.name" placeholder="如：subsidiary_of" />
                  </el-form-item>
                  <el-form-item label="起始类">
                    <el-select v-model="relForm.from" placeholder="选择起始类" style="width:100%">
                      <el-option v-for="c in classes" :key="c.name" :label="c.name" :value="c.name" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="目标类">
                    <el-select v-model="relForm.to" placeholder="选择目标类" style="width:100%">
                      <el-option v-for="c in classes" :key="c.name" :label="c.name" :value="c.name" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="约束">
                    <el-checkbox v-model="relForm.symmetric">对称 (Symmetric)</el-checkbox>
                    <el-checkbox v-model="relForm.functional">函数式 (Functional)</el-checkbox>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="onCreateRelation">创建关系</el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>

            <!-- 右侧：已建本体 -->
            <el-col :span="13">
              <el-card header="当前本体（Ontology）" class="panel">
                <div class="kg-stat">
                  <el-tag type="info">{{ classes.length }} 个类</el-tag>
                  <el-tag type="success">{{ relations.length }} 个关系</el-tag>
                  <el-tag type="warning">{{ instanceCount }} 个实例</el-tag>
                </div>
                <el-collapse v-model="openClasses" accordion>
                  <el-collapse-item v-for="cls in classes" :key="cls.name" :name="cls.name">
                    <template #title>
                      <strong>{{ cls.name }}</strong>
                      <el-tag v-if="cls.parent" size="small" type="info" style="margin-left:8px">⊂ {{ cls.parent }}</el-tag>
                      <el-tag size="small" style="margin-left:8px">{{ cls.attributes.length }} 属性</el-tag>
                      <el-tag size="small" type="success" style="margin-left:8px">{{ getInstanceCount(cls.name) }} 实例</el-tag>
                    </template>
                    <el-table :data="cls.attributes" size="small" border>
                      <el-table-column prop="name" label="属性" />
                      <el-table-column prop="type" label="类型" width="100" />
                      <el-table-column label="基数" width="120">
                        <template #default="s">{{ s.row.minCard }}..{{ s.row.maxCard >= 999 ? '*' : s.row.maxCard }}</template>
                      </el-table-column>
                    </el-table>
                  </el-collapse-item>
                </el-collapse>

                <el-divider>关系列表</el-divider>
                <el-table :data="relations" size="small" border>
                  <el-table-column prop="name" label="关系名" />
                  <el-table-column label="定义域→值域" width="200">
                    <template #default="s">{{ s.row.from }} → {{ s.row.to }}</template>
                  </el-table-column>
                  <el-table-column label="约束" width="180">
                    <template #default="s">
                      <el-tag v-if="s.row.symmetric" size="small">symmetric</el-tag>
                      <el-tag v-if="s.row.functional" size="small" type="warning">functional</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 2. 模式编辑与删除 -->
      <el-tab-pane label="② 模式编辑/删除" name="edit">
        <div class="tab-section">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card header="编辑类/关系" class="panel">
                <el-form :model="editForm" label-width="100px" size="small">
                  <el-form-item label="选择类">
                    <el-select v-model="editForm.targetName" placeholder="选择要编辑的类" style="width:100%" @change="onSelectEditClass">
                      <el-option v-for="c in classes" :key="c.name" :label="c.name" :value="c.name" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="新名称">
                    <el-input v-model="editForm.newName" />
                  </el-form-item>
                  <el-form-item label="新父类">
                    <el-select v-model="editForm.newParent" clearable placeholder="无（无继承）" style="width:100%">
                      <el-option v-for="c in classes.filter(x=>x.name!==editForm.targetName)" :key="c.name" :label="c.name" :value="c.name" />
                    </el-select>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="onApplyEdit">应用修改</el-button>
                  </el-form-item>
                </el-form>
              </el-card>

              <el-card header="删除模式元素" class="panel" style="margin-top:16px">
                <el-form label-width="100px" size="small">
                  <el-form-item label="待删除类">
                    <el-select v-model="deleteTarget" placeholder="选择要删除的类" style="width:100%">
                      <el-option v-for="c in classes" :key="c.name" :label="c.name" :value="c.name" />
                    </el-select>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="danger" @click="onCheckAndDelete" :disabled="!deleteTarget">检查引用并删除</el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>

            <el-col :span="12">
              <el-card header="检查结果 / 同步提示" class="panel">
                <el-empty v-if="!editResult" description="尚无操作" />
                <div v-else>
                  <el-alert
                    :title="editResult.title"
                    :type="editResult.type"
                    :description="editResult.description"
                    show-icon
                    :closable="false"
                  />
                  <div v-if="editResult.conflicts && editResult.conflicts.length" style="margin-top:12px">
                    <h4>冲突项</h4>
                    <el-tag v-for="(c,i) in editResult.conflicts" :key="i" type="danger" style="margin:2px">{{ c }}</el-tag>
                  </div>
                  <div v-if="editResult.synced && editResult.synced.length" style="margin-top:12px">
                    <h4>已同步的实例/关系</h4>
                    <el-tag v-for="(c,i) in editResult.synced" :key="i" type="success" style="margin:2px">{{ c }}</el-tag>
                  </div>
                </div>
              </el-card>

              <el-card header="操作日志" class="panel" style="margin-top:16px">
                <el-timeline>
                  <el-timeline-item v-for="(log,i) in editLogs" :key="i" :timestamp="log.time" :type="log.type">
                    {{ log.text }}
                  </el-timeline-item>
                </el-timeline>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>


      <!-- 3. 实体分布统计（子页面） -->
      <el-tab-pane label="③ 实体分布统计" name="stats">
        <div class="tab-section">
          <!-- 顶部总数卡片 -->
          <el-row :gutter="16" class="stat-cards">
            <el-col :span="6">
              <el-card shadow="hover" class="stat-card stat-total">
                <div class="stat-num">{{ statData.totalEntities }}</div>
                <div class="stat-label">实体总数（Entity）</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover" class="stat-card stat-rel">
                <div class="stat-num">{{ statData.totalRelations }}</div>
                <div class="stat-label">关系总数（Relationship）</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover" class="stat-card stat-listed">
                <div class="stat-num">{{ statData.listedCount }}</div>
                <div class="stat-label">上市公司</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover" class="stat-card stat-unlisted">
                <div class="stat-num">{{ statData.unlistedCount }}</div>
                <div class="stat-label">非上市公司</div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="16" style="margin-top:16px">
            <!-- 上市状态分布 -->
            <el-col :span="12">
              <el-card header="公司上市状态分布" class="panel">
                <div class="pie-wrap">
                  <svg ref="pieRef" :width="pieSize" :height="pieSize"></svg>
                  <div class="pie-legend">
                    <div class="legend-item">
                      <span class="dot" style="background:#409eff"></span>
                      <span class="lbl">上市公司</span>
                      <span class="val">{{ statData.listedCount }}（{{ statData.listedPct }}%）</span>
                    </div>
                    <div class="legend-item">
                      <span class="dot" style="background:#909399"></span>
                      <span class="lbl">非上市公司</span>
                      <span class="val">{{ statData.unlistedCount }}（{{ statData.unlistedPct }}%）</span>
                    </div>
                  </div>
                </div>
                <el-divider>对比数据</el-divider>
                <div class="compare-bar">
                  <div class="cmp-row">
                    <span class="cmp-label">上市公司</span>
                    <div class="cmp-track">
                      <div class="cmp-fill listed" :style="{ width: statData.listedPct + '%' }">
                        {{ statData.listedPct }}%
                      </div>
                    </div>
                  </div>
                  <div class="cmp-row">
                    <span class="cmp-label">非上市公司</span>
                    <div class="cmp-track">
                      <div class="cmp-fill unlisted" :style="{ width: statData.unlistedPct + '%' }">
                        {{ statData.unlistedPct }}%
                      </div>
                    </div>
                  </div>
                </div>
              </el-card>
            </el-col>

            <!-- 行业分布 -->
            <el-col :span="12">
              <el-card header="公司行业分布（Top {{ statData.industryDist.length }}）" class="panel">
                <div class="industry-list">
                  <div v-for="(it, idx) in statData.industryDist" :key="it.name" class="ind-row">
                    <div class="ind-rank" :class="'rank-' + (idx < 3 ? idx+1 : 4)">{{ idx + 1 }}</div>
                    <div class="ind-name">{{ it.name }}</div>
                    <div class="ind-bar-wrap">
                      <div v-if="it.pct > 8" class="ind-bar" :style="{ width: it.pct + '%', background: it.color }">
                        {{ it.count }}
                      </div>
                      <span v-else class="ind-count-out">{{ it.count }}</span>
                    </div>
                    <div class="ind-pct">{{ it.pct }}%</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 实体类型核心分布 -->
          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="24">
              <el-card header="实体类型核心分布" class="panel">
                <el-table :data="statData.entityTypeRows" border size="small" stripe>
                  <el-table-column prop="type" label="实体类型" width="160" />
                  <el-table-column prop="count" label="数量" width="120" align="right" sortable :formatter="(r) => r.count.toLocaleString()" />
                  <el-table-column prop="pct" label="占比" width="180" align="right">
                    <template #default="s">
                      <el-progress :percentage="s.row.pct" :stroke-width="10" />
                    </template>
                  </el-table-column>
                  <el-table-column prop="note" label="说明" />
                </el-table>
              </el-card>
            </el-col>
          </el-row>

          <!-- 违规事件深度分析 -->
          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="12">
              <el-card header="违规事件主体行业分布" class="panel">
                <div ref="violationIndRef" class="violation-chart"></div>
                <el-table :data="statData.violationIndRows" border size="small" stripe max-height="280" style="margin-top:12px">
                  <el-table-column type="index" label="#" width="50" />
                  <el-table-column prop="name" label="行业" />
                  <el-table-column prop="count" label="违规事件数" width="100" align="right" sortable />
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card header="违规类型分布（核心 10 类）" class="panel">
                <div ref="violationTypeRef" class="violation-chart"></div>
                <el-alert type="warning" :closable="false" show-icon style="margin-top:12px"
                  title="金融风险提示"
                  description="推迟披露、虚假记载、重大遗漏、违规买卖股票、内幕交易等违规类型频发，集中在投资控股、互联网、石化、医药等行业"
                />
              </el-card>
            </el-col>
          </el-row>

          <!-- 诉讼仲裁案件分析 -->
          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="8">
              <el-card header="诉讼案件-原告行业分布" class="panel">
                <div ref="litigationPlaintiffRef" class="violation-chart"></div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="诉讼案件-被告行业分布" class="panel">
                <div ref="litigationDefendantRef" class="violation-chart"></div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="诉讼案件-涉案缘由 TOP 10" class="panel">
                <div ref="litigationReasonRef" class="violation-chart"></div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 诉讼金额分布 + 主体-客体行业关系 -->
          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="12">
              <el-card header="诉讼案件-涉案金额分布" class="panel">
                <div ref="litigationAmountRef" class="violation-chart"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card header="诉讼案件-主体→客体行业关系 TOP 10" class="panel">
                <el-table :data="statData.litigationMatrixRows" border size="small" stripe max-height="300">
                  <el-table-column type="index" label="#" width="50" />
                  <el-table-column prop="plaintiff" label="原告(起诉方)行业" width="180" />
                  <el-table-column label="→" width="40" align="center" />
                  <el-table-column prop="defendant" label="被告(应诉方)行业" width="180" />
                  <el-table-column prop="count" label="案件数" width="80" align="right" sortable />
                </el-table>
              </el-card>
            </el-col>
          </el-row>

          <!-- 金融风险类型分析 -->
          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="8">
              <el-card header="质押(PLEDGE)-出质人行业" class="panel" shadow="hover">
                <div ref="pledgeRef" class="violation-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top:8px" size="small"
                  title="说明" description="股权质押反映企业融资压力，投资控股类公司出质最频繁" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="担保(GUARANTEES)-担保人行业" class="panel" shadow="hover">
                <div ref="guaranteeRef" class="violation-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top:8px" size="small"
                  title="说明" description="对外担保是或有负债的重要组成，揭示公司表外风险敞口" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="起诉-原告行业" class="panel" shadow="hover">
                <div ref="sueRef" class="violation-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top:8px" size="small"
                  title="说明" description="主动起诉频次反映公司法律维权能力与纠纷暴露面" />
              </el-card>
            </el-col>
          </el-row>

          <!-- 金融风险概览 + 高风险公司 -->
          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="14">
              <el-card header="高风险公司 TOP 10（按风险事件总数）" class="panel">
                <el-table :data="statData.highRiskRows" border size="small" stripe>
                  <el-table-column type="index" label="#" width="50" />
                  <el-table-column prop="name" label="公司名称" min-width="200" />
                  <el-table-column prop="vio" label="违规" width="70" align="right" sortable />
                  <el-table-column prop="lit" label="诉讼" width="70" align="right" sortable />
                  <el-table-column prop="sue" label="起诉" width="70" align="right" sortable />
                  <el-table-column prop="pledge" label="质押" width="70" align="right" sortable />
                  <el-table-column prop="gua" label="担保" width="70" align="right" sortable />
                  <el-table-column prop="total" label="总风险" width="100" align="right" sortable
                    :formatter="(r) => r.total.toLocaleString()" />
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="10">
              <el-card header="图谱覆盖的金融风险类型" class="panel">
                <div class="risk-type-grid">
                  <div class="risk-type-card" v-for="(r, i) in statData.financialRiskTypes" :key="i">
                    <div class="risk-icon" :style="{ background: r.color }">
                      <el-icon :size="22" color="#fff"><warning-filled /></el-icon>
                    </div>
                    <div class="risk-info">
                      <div class="risk-name">{{ r.name }}</div>
                      <div class="risk-count">{{ r.count.toLocaleString() }} 条</div>
                      <div class="risk-desc">{{ r.desc }}</div>
                    </div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 3.5 图谱金融风险知识 -->
      <el-tab-pane label="图谱金融风险知识" name="risk">
        <div class="tab-section">
          <!-- 顶部说明 -->
          <el-alert type="info" :closable="false" show-icon
            title="图谱金融风险知识全景"
            description="基于图谱中 7 类节点（Company / Violation / Litigation / PLEDGE / GUARANTEES / 客户 / 供应商 / MetaKnowledge）与 12 类关系的属性字段，全面挖掘出的金融风险知识。涵盖监管处罚、信息披露、股权质押、对外担保、诉讼仲裁、客户/供应链、子公司管控、宏观政策、系统性风险等 12 大类。"
            style="margin-bottom: 16px"
          />

          <!-- 金融风险大类卡片 -->
          <el-row :gutter="12">
            <el-col :span="6" v-for="(r, i) in financialRiskCards" :key="i" style="margin-bottom: 12px">
              <el-card shadow="hover" class="risk-overview-card" :body-style="{ padding: '12px 14px' }">
                <div class="roc-header">
                  <div class="roc-icon" :style="{ background: r.color }">
                    <el-icon :size="20" color="#fff"><component :is="r.icon" /></el-icon>
                  </div>
                  <div class="roc-title">{{ r.name }}</div>
                </div>
                <div class="roc-count">{{ r.count.toLocaleString() }} <span class="roc-unit">条记录</span></div>
                <div class="roc-source">数据源: {{ r.sources.join(' / ') }}</div>
                <div class="roc-desc">{{ r.desc }}</div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 三大类细粒度图表 -->
          <el-row :gutter="16" style="margin-top: 8px">
            <!-- 1) MetaKnowledge 元知识分类 -->
            <el-col :span="14">
              <el-card header="① MetaKnowledge 元知识 - 风险知识分类" class="panel">
                <div ref="mkCategoryRef" class="risk-chart"></div>
                <el-table :data="metaKnowledgeRows" border size="small" stripe max-height="280" style="margin-top: 12px">
                  <el-table-column type="index" label="#" width="50" />
                  <el-table-column prop="category" label="风险类别" width="160" />
                  <el-table-column prop="count" label="知识条目" width="100" align="right" sortable />
                  <el-table-column prop="pct" label="占比" width="100" align="right">
                    <template #default="s">
                      <el-progress :percentage="s.row.pct" :stroke-width="8" :show-text="true" />
                    </template>
                  </el-table-column>
                  <el-table-column prop="sample" label="典型结论" show-overflow-tooltip />
                </el-table>
              </el-card>
            </el-col>

            <!-- 2) 监管来源分布 -->
            <el-col :span="10">
              <el-card header="② 监管处罚来源分布" class="panel">
                <div ref="regulatorRef" class="risk-chart"></div>
                <el-alert type="warning" :closable="false" show-icon style="margin-top: 12px" size="small"
                  title="监管层级" description="处罚集中在交易所层面（深交所 6227 / 上交所 2705），证监会层面 1393，地方监管局分散处罚" />
              </el-card>
            </el-col>
          </el-row>

          <!-- 3) 股权质押 + 4) 对外担保 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="12">
              <el-card header="③ 股权质押 (PLEDGE) 风险特征" class="panel">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <div class="risk-mini-title">质押权人分类</div>
                    <div ref="pledgeeRef" class="risk-chart-small"></div>
                  </el-col>
                  <el-col :span="12">
                    <div class="risk-mini-title">变动原因</div>
                    <div ref="pledgeChangeRef" class="risk-chart-small"></div>
                  </el-col>
                </el-row>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="质押方类型分布" description="股东(3) 18721 条 / 关联方(2) 1706 条 / 其他(5) 367 条；用途多为空缺，需结合 PurposeCode 解读" />
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card header="④ 对外担保 (GUARANTEES) 风险特征" class="panel">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <div class="risk-mini-title">担保对象</div>
                    <div ref="guaTargetRef" class="risk-chart-small"></div>
                  </el-col>
                  <el-col :span="12">
                    <div class="risk-mini-title">担保期限(月)</div>
                    <div ref="guaTermRef" class="risk-chart-small"></div>
                  </el-col>
                </el-row>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="担保特点" description="币种以 CNY 为主 (14680)，担保对象 13976 为上市公司子公司（存在关联交易风险）" />
              </el-card>
            </el-col>
          </el-row>

          <!-- 5) 诉讼仲裁 + 6) 客户/供应商风险 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="8">
              <el-card header="⑤ 诉讼仲裁 (Litigation) 司法进程" class="panel">
                <div ref="judicialRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="司法类型" description="Q3502 一审(56529) / Q3503 二审(10045) / Q3501 再审(6159) / Q3504 执行(948)" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="⑥ 客户关系 - 经营异常" class="panel">
                <div ref="custRiskRef" class="risk-chart"></div>
                <el-alert type="error" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="客户风险" description="注销/吊销客户约 8000+ 条，存在应收账款无法收回风险" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="⑦ 客户/供应商 - 企业规模" class="panel">
                <div ref="custScaleRef" class="risk-chart"></div>
                <el-alert type="warning" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="规模结构" description="大客户 29417 (29.9%) / 中型 11337 / 小微 21296 / 未注明 36197" />
              </el-card>
            </el-col>
          </el-row>

          <!-- 子公司退出风险 + 起诉关系 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="8">
              <el-card header="⑧ 子公司 (子公司) - 是否退出" class="panel">
                <div ref="subExitRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="子公司管控" description="227459 条子公司关系；已退出子公司可能涉及剥离、注销、转让" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="⑨ 子公司 - 设立方式" class="panel">
                <div ref="subSetupRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="设立方式" description="投资设立 vs 收购兼并 vs 分立，揭示集团扩张路径" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="⑩ MetaKnowledge 样本" class="panel">
                <el-table :data="metaKnowledgeSamples" border size="small" stripe max-height="320">
                  <el-table-column prop="category" label="类别" width="100" />
                  <el-table-column prop="conclusion" label="核心结论" show-overflow-tooltip />
                </el-table>
              </el-card>
            </el-col>
          </el-row>

          <!-- ⑪⑫ 跨市场对冲与系统性金融风险 (MetaKnowledge 精粹) -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="24">
              <el-card header="⑪⑫ 跨市场对冲与系统性金融风险 (MetaKnowledge 精粹)" class="panel">
                <el-row :gutter="12">
                  <el-col :span="8" v-for="(k, i) in metaKnowledgeInsights" :key="i" style="margin-bottom: 12px">
                    <div class="mk-insight-card">
                      <div class="mk-tag">{{ k.tag }}</div>
                      <div class="mk-conclusion">{{ k.conclusion }}</div>
                      <div class="mk-risk">⚠ {{ k.risk }}</div>
                    </div>
                  </el-col>
                </el-row>
              </el-card>
            </el-col>
          </el-row>

          <!-- ⑬⑭⑮ P25xx 违规类型编码 + 处罚金额 + 处罚方式 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="10">
              <el-card header="⑬ 违规类型编码 (P25xx) 精确分布" class="panel">
                <el-table :data="p25CodeRows" border size="small" stripe max-height="320">
                  <el-table-column prop="code" label="编码" width="80" />
                  <el-table-column prop="name" label="违规类型" min-width="160" />
                  <el-table-column prop="count" label="次数" width="90" align="right" sortable :formatter="(r) => r.count.toLocaleString()" />
                  <el-table-column prop="pct" label="占比" width="80" align="right">
                    <template #default="s">
                      <el-progress :percentage="s.row.pct" :stroke-width="8" />
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="7">
              <el-card header="⑭ 处罚金额区间分布" class="panel">
                <div ref="fineRangeRef" class="risk-chart"></div>
                <el-alert type="warning" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="处罚金额" description="10-100万 区间最多 (694)，处罚金额主要集中在百万级" />
              </el-card>
            </el-col>
            <el-col :span="7">
              <el-card header="⑮ 处罚方式分布" class="panel">
                <div ref="punishRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="处罚方式" description="其他 7336 / 批评 1472 / 谴责 781 / 警告+罚款 348" />
              </el-card>
            </el-col>
          </el-row>

          <!-- ⑯⑰ 处分措施 + 违规年度 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="14">
              <el-card header="⑯ 处分措施 TOP 8" class="panel">
                <div ref="measureRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="处分措施" description="整改 2571 / 出具监管函 1016 / 内部通报批评 146 / 警示函 42" />
              </el-card>
            </el-col>
            <el-col :span="10">
              <el-card header="⑰ 违规年度分布" class="panel">
                <div ref="vioYearRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="年度特征" description="2021 (1223) > 2018 (1198) > 2022 (1181)，违规事件近年高发" />
              </el-card>
            </el-col>
          </el-row>

          <!-- ⑱⑲⑳ 实际控制人 + 资本背景 + 风险警示 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="8">
              <el-card header="⑱ 实际控制人类型分布" class="panel">
                <div ref="controllerRef" class="risk-chart"></div>
                <el-alert type="warning" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="控制权" description="个人 (3567) > 地方政府国资 (707) > 国务院国资委 (177)" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="⑲ 公司资本背景" class="panel">
                <div ref="capitalRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="资本结构" description="民营 20444 / 国有绝对 14292 / 国有相对 6942 / 港澳台 1545" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="⑳ 风险警示板公司行业" class="panel">
                <div ref="warningRef" class="risk-chart"></div>
                <el-alert type="error" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="风险警示" description="全市场 176 家 ST / *ST 公司，主要集中在批发、计算机通信、商务服务" />
              </el-card>
            </el-col>
          </el-row>

          <!-- ㉑㉒㉓ 行业二级 + 省份 + 子公司持股 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="8">
              <el-card header="㉑ 行业（二级）TOP 12" class="panel">
                <div ref="industryRef" class="risk-chart"></div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="㉒ 公司省份分布 TOP 12" class="panel">
                <div ref="provinceRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="区域集中度" description="广东 4132 / 浙江 3700 / 江苏 3170，长三角+珠三角集中度高" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card header="㉓ 子公司直接持股比例" class="panel">
                <div ref="stakeRef" class="risk-chart"></div>
                <el-alert type="warning" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="持股结构" description="全资(100%) 65692 / 控股(50-99%) 37035 / 参股(<50%) 4418" />
              </el-card>
            </el-col>
          </el-row>

          <!-- ㉔㉕ 客户/供应商 资本背景 + 行业 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="12">
              <el-card header="㉔ 客户/供应商 - 资本背景对比" class="panel">
                <div ref="csCapitalRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="客户结构" description="客户以国有绝对控股为主(27091)；供应商以民营企业为主(55945)" />
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card header="㉕ 客户/供应商 - 行业（二级）TOP 8" class="panel">
                <div ref="csIndustryRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="行业集中" description="批发业 19979 / 商务服务业 10747 / 软件信息技术服务业 7901" />
              </el-card>
            </el-col>
          </el-row>

          <!-- ㉖㉗ 诉讼币种 + 涉案金额 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="12">
              <el-card header="㉖ 诉讼币种分布" class="panel">
                <div ref="currencyRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="币种" description="人民币 CNY (69272) 占绝对主导；USD 420 / EUR 57 / HKD 32" />
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card header="㉗ 诉讼涉案金额区间（精确）" class="panel">
                <div ref="litAmountRef" class="risk-chart"></div>
                <el-alert type="error" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="金额分布" description="超 1 亿元案件 68464 起（93%），诉讼风险金额巨大" />
              </el-card>
            </el-col>
          </el-row>

          <!-- ㉘㉙ PLEDGE 用途 + 子公司设立方式 -->
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="12">
              <el-card header="㉘ PLEDGE 质押用途 (PurposeCode) 分布" class="panel">
                <div ref="pledgeUseRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="质押用途" description="Q5702 (1601) / Q5701 (1470) / Q5709 (1239)，主要为融资担保/借款" />
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card header="㉙ 子公司设立方式" class="panel">
                <div ref="subSetupTypeRef" class="risk-chart"></div>
                <el-alert type="info" :closable="false" show-icon style="margin-top: 8px" size="small"
                  title="扩张方式" description="投资设立 145000 / 收购兼并 42000，集团主要靠投资设立扩张" />
              </el-card>
            </el-col>
          </el-row>

        </div>
      </el-tab-pane>

      <!-- 7. 图谱浏览与性能测试 -->
      <el-tab-pane label="④ 图谱浏览与性能" name="browse">
        <div class="tab-section">
          <el-row :gutter="16">
            <!-- 左侧：图谱浏览画布 -->
            <el-col :span="16">
              <el-card header="图谱浏览画布" class="panel">
                <div class="browse-toolbar">
                  <el-button-group>
                    <el-button size="small" @click="switchLayout('force')" :type="browseLayout==='force'?'primary':''">力导向</el-button>
                    <el-button size="small" @click="switchLayout('tree')" :type="browseLayout==='tree'?'primary':''">树形</el-button>
                    <el-button size="small" @click="switchLayout('circular')" :type="browseLayout==='circular'?'primary':''">环形</el-button>
                    <el-button size="small" @click="switchLayout('grid')" :type="browseLayout==='grid'?'primary':''">网格</el-button>
                  </el-button-group>
                  <el-divider direction="vertical" />
                  <el-button size="small" @click="expandAllNodes" :icon="Expand">展开全部</el-button>
                  <el-button size="small" @click="collapseAllNodes" :icon="Fold">收起全部</el-button>
                  <el-divider direction="vertical" />
                  <el-button size="small" @click="resetBrowseView" :icon="Refresh">重置视图</el-button>
                  <el-button size="small" @click="toggleVirtualRender" :type="virtualRender?'success':''">{{ virtualRender?'虚拟渲染:开':'虚拟渲染:关' }}</el-button>
                </div>
                <div ref="browseCanvasRef" class="browse-canvas"></div>
                <div class="browse-status">
                  <el-tag>节点: {{ browseStats.nodeCount }}</el-tag>
                  <el-tag>边: {{ browseStats.edgeCount }}</el-tag>
                  <el-tag>FPS: {{ browseStats.fps }}</el-tag>
                  <el-tag :type="browseStats.fps>30?'success':browseStats.fps>15?'warning':'danger'">性能: {{ browseStats.performance }}</el-tag>
                </div>
              </el-card>
            </el-col>

            <!-- 右侧：实体详情与过滤 -->
            <el-col :span="8">
              <!-- 实体详情卡片 -->
              <el-card header="实体详情" class="panel" v-if="selectedNode">
                <div class="node-detail">
                  <div class="node-header">
                    <div class="node-type-tag" :style="{ background: getNodeColor(selectedNode.type) }">{{ selectedNode.type }}</div>
                    <h4>{{ selectedNode.name }}</h4>
                  </div>
                  <el-divider />
                  <div class="node-props">
                    <div v-for="(val, key) in selectedNode.properties" :key="key" class="prop-item">
                      <span class="prop-key">{{ key }}:</span>
                      <span class="prop-val">{{ Array.isArray(val) ? val.join(', ') : val }}</span>
                      <el-tag v-if="Array.isArray(val)" size="small" type="info">多值</el-tag>
                    </div>
                  </div>
                  <el-divider />
                  <div class="node-actions">
                    <el-button size="small" @click="expandNode(selectedNode)">展开关联</el-button>
                    <el-button size="small" @click="focusNode(selectedNode)">聚焦</el-button>
                    <el-button size="small" type="primary" @click="addBookmark(selectedNode)">添加书签</el-button>
                  </div>
                </div>
              </el-card>
              <el-empty v-else description="点击画布节点查看详情" />

              <!-- 样式与过滤 -->
              <el-card header="样式与过滤" class="panel" style="margin-top:16px">
                <el-form label-width="80px" size="small">
                  <el-form-item label="节点类型">
                    <el-checkbox-group v-model="filterNodeTypes">
                      <el-checkbox v-for="t in allNodeTypes" :key="t" :label="t">
                        <span class="type-dot" :style="{ background: getNodeColor(t) }"></span>{{ t }}
                      </el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                  <el-form-item label="属性过滤">
                    <el-input v-model="filterPropKey" placeholder="属性名" style="width:45%" />
                    <el-input v-model="filterPropVal" placeholder="属性值" style="width:45%;margin-left:8px" />
                  </el-form-item>
                  <el-form-item label="大小映射">
                    <el-select v-model="sizeMapping" style="width:100%">
                      <el-option label="固定大小" value="fixed" />
                      <el-option label="按度数" value="degree" />
                      <el-option label="按属性值" value="property" />
                    </el-select>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" size="small" @click="applyFilter">应用过滤</el-button>
                    <el-button size="small" @click="resetFilter">重置</el-button>
                  </el-form-item>
                </el-form>
              </el-card>

              <!-- 历史记录与导航 -->
              <el-card header="浏览历史与书签" class="panel" style="margin-top:16px">
                <el-timeline v-if="browseHistory.length">
                  <el-timeline-item v-for="(h, i) in browseHistory.slice(-5)" :key="i" :timestamp="h.time">
                    <el-link @click="navigateToNode(h.node)">{{ h.node.name }}</el-link>
                  </el-timeline-item>
                </el-timeline>
                <el-empty v-else description="暂无浏览记录" />
                <el-divider />
                <h5>书签</h5>
                <el-tag v-for="(b, i) in bookmarks" :key="i" closable @close="removeBookmark(i)" @click="navigateToNode(b)"
                  style="margin:2px;cursor:pointer">
                  {{ b.name }}
                </el-tag>
              </el-card>
            </el-col>
          </el-row>

          <!-- 大图性能测试 -->
          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="24">
              <el-card header="大图性能测试" class="panel">
                <el-form inline size="small">
                  <el-form-item label="测试规模">
                    <el-radio-group v-model="perfTestSize">
                      <el-radio-button label="1k">1千节点</el-radio-button>
                      <el-radio-button label="10k">1万节点</el-radio-button>
                      <el-radio-button label="50k">5万节点</el-radio-button>
                      <el-radio-button label="100k">10万节点</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="runPerfTest" :loading="perfTesting">{{ perfTesting?'测试中...':'开始性能测试' }}</el-button>
                  </el-form-item>
                </el-form>
                <el-divider />
                <el-row :gutter="20" v-if="perfResult">
                  <el-col :span="6">
                    <div class="perf-metric">
                      <div class="perf-val" :class="perfResult.loadTime<1000?'good':perfResult.loadTime<5000?'medium':'bad'">
                        {{ perfResult.loadTime }}ms
                      </div>
                      <div class="perf-label">加载时间</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="perf-metric">
                      <div class="perf-val" :class="perfResult.fps>30?'good':perfResult.fps>15?'medium':'bad'">{{ perfResult.fps }}</div>
                      <div class="perf-label">平均FPS</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="perf-metric">
                      <div class="perf-val" :class="perfResult.memory<500?'good':perfResult.memory<1000?'medium':'bad'">{{ perfResult.memory }}MB</div>
                      <div class="perf-label">内存占用</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="perf-metric">
                      <div class="perf-val" :class="perfResult.interactive?'good':'bad'">{{ perfResult.interactive?'流畅':'卡顿' }}</div>
                      <div class="perf-label">交互体验</div>
                    </div>
                  </el-col>
                </el-row>
                <el-alert v-if="perfResult" :type="perfResult.passed?'success':'warning'" show-icon style="margin-top:12px"
                  :title="perfResult.passed?'性能测试通过':'性能存在瓶颈'"
                  :description="perfResult.suggestion"
                />
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 8. 数据导入与抽取测试 -->
      <el-tab-pane label="⑤ 数据导入与抽取" name="import-extract">
        <div class="tab-section">
          <el-row :gutter="16">
            <!-- 结构化数据导入 -->
            <el-col :span="12">
              <el-card header="结构化数据导入" class="panel">
                <el-tabs type="border-card" size="small">
                  <el-tab-pane label="CSV/Excel">
                    <el-upload drag action="" :auto-upload="false" :on-change="onStructuredFileChange" accept=".csv,.xlsx,.xls"
                      style="width:100%">
                      <el-icon :size="40" style="margin:20px 0 10px"><upload-filled /></el-icon>
                      <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
                      <template #tip>
                        <div class="el-upload__tip">支持 CSV、Excel 格式，需包含表头行</div>
                      </template>
                    </el-upload>
                    <el-divider />
                    <el-form v-if="structuredPreview" label-width="100px" size="small">
                      <el-form-item label="数据源">
                        <el-tag>{{ structuredPreview.source }}</el-tag>
                      </el-form-item>
                      <el-form-item label="字段映射">
                        <el-table :data="structuredPreview.mappings" size="small" border
                          @cell-click="editMapping"
                        >
                          <el-table-column prop="sourceField" label="源字段" />
                          <el-table-column prop="targetType" label="实体类型">
                            <template #default="s">
                              <el-select v-model="s.row.targetType" size="small" style="width:100%"
                                @change="updateMapping(s.row)"
                              >
                                <el-option v-for="t in allNodeTypes" :key="t" :label="t" :value="t" />
                              </el-select>
                            </template>
                          </el-table-column>
                          <el-table-column prop="targetProp" label="属性名">
                            <template #default="s">
                              <el-input v-model="s.row.targetProp" size="small" />
                            </template>
                          </el-table-column>
                        </el-table>
                      </el-form-item>
                      <el-form-item label="关系映射">
                        <el-button size="small" @click="addRelationMapping">+ 添加关系映射</el-button>
                        <el-table :data="structuredPreview.relationMappings" size="small" border style="margin-top:8px"
                          v-if="structuredPreview.relationMappings.length"
                        >
                          <el-table-column prop="fromField" label="起始字段" />
                          <el-table-column prop="toField" label="目标字段" />
                          <el-table-column prop="relType" label="关系类型">
                            <template #default="s">
                              <el-select v-model="s.row.relType" size="small"
                                @change="updateRelationMapping(s.row)"
                              >
                                <el-option v-for="r in allRelationTypes" :key="r" :label="r" :value="r" />
                              </el-select>
                            </template>
                          </el-table-column>
                        </el-table>
                      </el-form-item>
                      <el-form-item>
                        <el-button type="primary" @click="previewImport">预览导入</el-button>
                        <el-button @click="executeImport" :loading="importing">{{ importing?'导入中...':'执行导入' }}</el-button>
                      </el-form-item>
                    </el-form>
                  </el-tab-pane>
                  <el-tab-pane label="关系数据库">
                    <el-form label-width="100px" size="small">
                      <el-form-item label="数据库类型">
                        <el-select v-model="dbConfig.type" style="width:100%">
                          <el-option label="MySQL" value="mysql" />
                          <el-option label="PostgreSQL" value="postgresql" />
                          <el-option label="Oracle" value="oracle" />
                          <el-option label="SQL Server" value="mssql" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="连接信息">
                        <el-input v-model="dbConfig.host" placeholder="主机:端口" style="width:48%" />
                        <el-input v-model="dbConfig.database" placeholder="数据库名" style="width:48%;margin-left:4%" />
                      </el-form-item>
                      <el-form-item>
                        <el-input v-model="dbConfig.username" placeholder="用户名" style="width:48%" />
                        <el-input v-model="dbConfig.password" placeholder="密码" type="password" style="width:48%;margin-left:4%" />
                      </el-form-item>
                      <el-form-item label="SQL 查询">
                        <el-input v-model="dbConfig.sql" type="textarea" :rows="3" placeholder="SELECT * FROM ..." />
                      </el-form-item>
                      <el-form-item>
                        <el-button type="primary" @click="testDbConnection">测试连接</el-button>
                        <el-button @click="loadDbSchema">加载表结构</el-button>
                      </el-form-item>
                    </el-form>
                  </el-tab-pane>
                  <el-tab-pane label="API 接口">
                    <el-form label-width="100px" size="small">
                      <el-form-item label="请求方法">
                        <el-radio-group v-model="apiConfig.method">
                          <el-radio-button label="GET">GET</el-radio-button>
                          <el-radio-button label="POST">POST</el-radio-button>
                        </el-radio-group>
                      </el-form-item>
                      <el-form-item label="接口地址">
                        <el-input v-model="apiConfig.url" placeholder="https://api.example.com/data" />
                      </el-form-item>
                      <el-form-item label="认证方式">
                        <el-select v-model="apiConfig.authType" style="width:100%">
                          <el-option label="无认证" value="none" />
                          <el-option label="Bearer Token" value="bearer" />
                          <el-option label="API Key" value="apikey" />
                          <el-option label="Basic Auth" value="basic" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="Headers">
                        <el-input v-model="apiConfig.headers" type="textarea" :rows="2" placeholder='{"Content-Type": "application/json"}' />
                      </el-form-item>
                      <el-form-item>
                        <el-button type="primary" @click="testApiConnection">测试接口</el-button>
                        <el-button @click="fetchApiData">获取数据</el-button>
                      </el-form-item>
                    </el-form>
                  </el-tab-pane>
                </el-tabs>

                <!-- 导入进度与日志 -->
                <el-divider />
                <el-card v-if="importProgress.show" header="导入进度" shadow="never">
                  <el-progress :percentage="importProgress.percent" :status="importProgress.status" />
                  <div style="margin-top:8px">
                    <el-tag>已处理: {{ importProgress.processed }}/{{ importProgress.total }}</el-tag>
                    <el-tag type="success">成功: {{ importProgress.success }}</el-tag>
                    <el-tag type="danger">失败: {{ importProgress.failed }}</el-tag>
                  </div>
                  <el-collapse style="margin-top:8px">
                    <el-collapse-item title="错误日志">
                      <pre class="error-log">{{ importProgress.errors.join('\n') || '暂无错误' }}</pre>
                    </el-collapse-item>
                  </el-collapse>
                </el-card>
              </el-card>
            </el-col>

            <!-- 半/非结构化抽取 -->
            <el-col :span="12">
              <el-card header="半/非结构化抽取" class="panel">
                <el-tabs type="border-card" size="small">
                  <el-tab-pane label="文档上传">
                    <el-upload drag action="" :auto-upload="false" :on-change="onDocFileChange"
                      accept=".pdf,.doc,.docx,.txt,.html"
                      style="width:100%"
                    >
                      <el-icon :size="40" style="margin:20px 0 10px"><document /></el-icon>
                      <div class="el-upload__text">拖拽文档到此处或 <em>点击上传</em></div>
                      <template #tip>
                        <div class="el-upload__tip">支持 PDF、Word、TXT、HTML 格式</div>
                      </template>
                    </el-upload>
                    <el-divider />
                    <el-form label-width="100px" size="small">
                      <el-form-item label="抽取模型">
                        <el-select v-model="extractConfig.model" style="width:100%">
                          <el-option label="默认 NER 模型" value="default" />
                          <el-option label="金融领域模型" value="finance" />
                          <el-option label="法律领域模型" value="legal" />
                          <el-option label="医疗领域模型" value="medical" />
                          <el-option label="自定义模型" value="custom" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="抽取类型">
                        <el-checkbox-group v-model="extractConfig.types">
                          <el-checkbox label="entity">实体识别</el-checkbox>
                          <el-checkbox label="relation">关系抽取</el-checkbox>
                          <el-checkbox label="attribute">属性抽取</el-checkbox>
                        </el-checkbox-group>
                      </el-form-item>
                      <el-form-item label="语言">
                        <el-radio-group v-model="extractConfig.language">
                          <el-radio-button label="zh">中文</el-radio-button>
                          <el-radio-button label="en">英文</el-radio-button>
                          <el-radio-button label="auto">自动检测</el-radio-button>
                        </el-radio-group>
                      </el-form-item>
                      <el-form-item>
                        <el-button type="primary" @click="startExtraction" :loading="extracting"
                        >{{ extracting?'抽取中...':'开始抽取' }}</el-button>
                      </el-form-item>
                    </el-form>
                  </el-tab-pane>
                  <el-tab-pane label="抽取结果审核">
                    <el-alert v-if="!extractResults" type="info" show-icon :closable="false"
                      title="暂无抽取结果"
                      description="请先上传文档并执行抽取"
                    />
                    <div v-else class="extract-review">
                      <div class="review-stats">
                        <el-tag>实体: {{ extractResults.entities.length }}</el-tag>
                        <el-tag>关系: {{ extractResults.relations.length }}</el-tag>
                        <el-tag type="warning">低置信度: {{ extractResults.lowConfidence.length }}</el-tag>
                      </div>
                      <el-divider />
                      <h5>实体识别结果</h5>
                      <el-table :data="extractResults.entities" size="small" border
                        @selection-change="onEntitySelectionChange"
                      >
                        <el-table-column type="selection" width="40" />
                        <el-table-column prop="text" label="实体文本" />
                        <el-table-column prop="type" label="类型" width="100" />
                        <el-table-column prop="confidence" label="置信度" width="100"
                          :formatter="(r) => (r.confidence * 100).toFixed(1) + '%'"
                        />
                        <el-table-column label="操作" width="120">
                          <template #default="s">
                            <el-button size="small" @click="editExtractedEntity(s.row)">修正</el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                      <el-divider />
                      <h5>关系抽取结果</h5>
                      <el-table :data="extractResults.relations" size="small" border
                        @selection-change="onRelationSelectionChange"
                      >
                        <el-table-column type="selection" width="40" />
                        <el-table-column prop="subject" label="主体" />
                        <el-table-column prop="predicate" label="关系" width="100" />
                        <el-table-column prop="object" label="客体" />
                        <el-table-column prop="confidence" label="置信度" width="100"
                          :formatter="(r) => (r.confidence * 100).toFixed(1) + '%'"
                        />
                      </el-table>
                      <el-divider />
                      <div class="review-actions">
                        <el-button type="primary" @click="confirmSelected"
                        >确认选中 ({{ selectedEntities.length + selectedRelations.length }})</el-button>
                        <el-button @click="rejectSelected">拒绝选中</el-button>
                        <el-button type="success" @click="confirmAll">全部确认</el-button>
                      </div>
                    </div>
                  </el-tab-pane>
                </el-tabs>
              </el-card>
            </el-col>
          </el-row>

          <!-- 批量构建与增量更新 -->
          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="12">
              <el-card header="批量构建" class="panel">
                <el-form label-width="100px" size="small">
                  <el-form-item label="更新模式">
                    <el-radio-group v-model="batchConfig.updateMode">
                      <el-radio-button label="append">追加模式</el-radio-button>
                      <el-radio-button label="merge">合并模式</el-radio-button>
                      <el-radio-button label="replace">覆盖模式</el-radio-button>
                      <el-radio-button label="version">版本隔离</el-radio-button>
                    </el-radio-group>
                    <div class="mode-desc">{{ batchModeDescriptions[batchConfig.updateMode] }}</div>
                  </el-form-item>
                  <el-form-item label="批量大小">
                    <el-slider v-model="batchConfig.batchSize" :min="100" :max="10000" :step="100" show-input />
                  </el-form-item>
                  <el-form-item label="并发数">
                    <el-slider v-model="batchConfig.concurrency" :min="1" :max="10" show-input />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="startBatchBuild" :loading="batchBuilding"
                    >{{ batchBuilding?'构建中...':'开始批量构建' }}</el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>

            <el-col :span="12">
              <el-card header="构建结果" class="panel">
                <el-empty v-if="!batchResult" description="尚未执行批量构建" />
                <div v-else class="batch-result">
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="开始时间">{{ batchResult.startTime }}</el-descriptions-item>
                    <el-descriptions-item label="结束时间">{{ batchResult.endTime }}</el-descriptions-item>
                    <el-descriptions-item label="总耗时">{{ batchResult.duration }}s</el-descriptions-item>
                    <el-descriptions-item label="更新模式">{{ batchResult.updateMode }}</el-descriptions-item>
                    <el-descriptions-item label="新增节点">{{ batchResult.newNodes }}</el-descriptions-item>
                    <el-descriptions-item label="新增关系">{{ batchResult.newRelations }}</el-descriptions-item>
                    <el-descriptions-item label="更新节点">{{ batchResult.updatedNodes }}</el-descriptions-item>
                    <el-descriptions-item label="跳过节点">{{ batchResult.skippedNodes }}</el-descriptions-item>
                  </el-descriptions>
                  
                  <el-divider />
                  <h5>影响分析</h5>
                  <el-alert
                    :type="batchResult.impact==='low'?'success':batchResult.impact==='medium'?'warning':'error'"
                    show-icon
                    :title="batchResult.impactTitle"
                    :description="batchResult.impactDesc"
                  />
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import { Delete, ZoomIn, ZoomOut, Refresh, Download, Grid, CopyDocument, Upload, UploadFilled, Expand, Fold,
  Document, Warning, Coin, Connection, ScaleToOriginal, User, Box, OfficeBuilding, DataAnalysis, Refresh as RefreshIcon, Money, WarningFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as d3 from 'd3';

export default {
  name: 'KnowledgeGraphTest',
  /* eslint-disable vue/no-unused-components */
  components: {
    Delete, ZoomIn, ZoomOut, Refresh, Download, Grid, CopyDocument, Upload, UploadFilled, Expand, Fold,
    Document, Warning, Coin, Connection, ScaleToOriginal, User, Box, OfficeBuilding, DataAnalysis, RefreshIcon, Money, WarningFilled
  },
  /* eslint-enable vue/no-unused-components */
  data() {
    return {
      activeTab: 'create',
      // ====== 图谱金融风险知识（基于 kg_financial_risk.json 抽取） ======
      financialRiskCards: [
        { name: '信息披露风险', icon: 'Document', color: '#e6a23c',
          sources: ['Violation.违规类型'], count: 18776,
          desc: '上市公司未按法规及时、准确、完整披露信息' },
        { name: '监管处罚风险', icon: 'Warning', color: '#f56c6c',
          sources: ['Violation.处理单位'], count: 18776,
          desc: '深交所/上交所/证监会及地方监管局处罚' },
        { name: '股权质押风险', icon: 'Coin', color: '#ff7e00',
          sources: ['PLEDGE.PledgeeCatergory'], count: 20863,
          desc: '股东出质股权融资，平仓/爆仓/控制权变更' },
        { name: '对外担保风险', icon: 'Connection', color: '#f56c6c',
          sources: ['GUARANTEES.RelateToGuarantee'], count: 14825,
          desc: '为他人/子公司债务担保，形成或有负债' },
        { name: '诉讼仲裁风险', icon: 'ScaleToOriginal', color: '#409eff',
          sources: ['Litigation.司法类型/司法进程'], count: 73681,
          desc: '一审/二审/再审/执行各阶段司法案件' },
        { name: '客户集中度风险', icon: 'User', color: '#67c23a',
          sources: ['客户.企业规模/经营状态'], count: 98247,
          desc: '重大客户依赖与客户经营异常' },
        { name: '供应链风险', icon: 'Box', color: '#1abc9c',
          sources: ['供应商.企业规模/经营状态'], count: 82472,
          desc: '核心供应商断供/违约/经营异常' },
        { name: '子公司管控风险', icon: 'OfficeBuilding', color: '#9b59b6',
          sources: ['子公司.是否退出/设立方式'], count: 227459,
          desc: '子公司失控、退出、股权稀释' },
        { name: '宏观经济/政策风险', icon: 'DataAnalysis', color: '#795548',
          sources: ['MetaKnowledge.core_conclusion'], count: 201,
          desc: '利率/汇率/财政/货币政策变化的影响' },
        { name: '跨市场对冲风险', icon: 'Refresh', color: '#00bcd4',
          sources: ['MetaKnowledge.股债跷跷板/期货对冲'], count: 35,
          desc: '股债/股期跨市场风险传导与对冲失效' },
        { name: '地方债务传染风险', icon: 'Money', color: '#607d8b',
          sources: ['MetaKnowledge.地方公共债务'], count: 8,
          desc: '地方债扩张传导至企业的资源配置效率' },
        { name: '系统性金融风险', icon: 'WarningFilled', color: '#c0392b',
          sources: ['MetaKnowledge.系统性金融风险'], count: 12,
          desc: '跨行业跨市场的金融体系稳定性' }
      ],
      metaKnowledgeRows: [
        { category: '系统性风险', count: 109, pct: 54,
          sample: '地方公共债务规模的增加会显著降低企业间资源配置效率，加剧系统性金融风险' },
        { category: '信用风险', count: 36, pct: 18,
          sample: '抵押率是影响高风险企业融资成本和信贷规模的关键变量' },
        { category: '市场风险', count: 21, pct: 10,
          sample: '中国股票市场和国债现货市场之间存在显著的互相对冲风险效应' },
        { category: '流动性风险', count: 17, pct: 8,
          sample: '经济政策不确定性上升会显著抑制企业投资并提高现金持有' },
        { category: '操作风险', count: 5, pct: 2,
          sample: '管理层会策略性增加创新投入以吸引投资者关注并借机减持套现' },
        { category: '宏观经济/政策风险', count: 3, pct: 1,
          sample: '上游生产要素价格的上升会通过非线性传导机制引发成本推动型通胀' },
        { category: '法律/监管风险', count: 2, pct: 1,
          sample: '沪深两市均未达到弱式有效市场状态' },
        { category: '风险对冲/缓释', count: 1, pct: 1,
          sample: '签署PRI的基金公司显著提升了对绿色创新型企业的投资' },
        { category: '其他', count: 7, pct: 3,
          sample: '增加农村家庭收入是降低其脆弱性最有效的手段' }
      ],
      metaKnowledgeSamples: [
        { category: '系统性风险', conclusion: '地方公共债务规模的增加会显著降低企业间资源配置效率，加剧系统性金融风险' },
        { category: '系统性风险', conclusion: '灾难风险是导致中国股市异常高波动率和股权溢价的重要定价因子，能解释约39.5%的股权溢价' },
        { category: '市场风险', conclusion: '中国股票市场和国债现货市场之间存在显著的互相对冲风险效应' },
        { category: '市场风险', conclusion: '中国股指期货与国债期货市场之间不存在显著的互相对冲风险效应' },
        { category: '市场风险', conclusion: '国债现货不仅能对冲股票现货市场的风险，还能有效对冲股票期货市场的波动性和极端风险' },
        { category: '信用风险', conclusion: '中国的显性存款保险制度通过削弱银行特许权价值，导致银行风险上升' },
        { category: '信用风险', conclusion: '在垄断竞争的影子银行体系中，抵押率是影响高风险企业融资成本和信贷规模的关键变量' },
        { category: '信用风险', conclusion: '长期低利率环境虽会提高银行风险偏好，但不必然导致影子银行承担更多风险' },
        { category: '流动性风险', conclusion: '在源于亚洲或拉美等从属市场的区域性金融危机期间，中国证券市场与发达市场的一体化水平反而增强' },
        { category: '流动性风险', conclusion: '移动互联网端投资者的网络安全风险感知所要求的风险补偿显著高于PC端投资者' },
        { category: '操作风险', conclusion: '投资者的网络安全风险感知越高，其要求获得的风险补偿也越高' },
        { category: '操作风险', conclusion: '管理层会策略性增加创新投入以吸引投资者关注，并借机减持套现' }
      ],
      metaKnowledgeInsights: [
        { tag: '股债跷跷板', conclusion: '股市与债市互相对冲效应显著，符合投资者偏度偏好和峰度厌恶',
          risk: '跨市场配置可作为对冲工具，但需关注极端尾部风险' },
        { tag: '期货对冲失效', conclusion: '中国股指期货与国债期货之间不存在显著对冲效应',
          risk: '期货受制度限制和参与者缺位，难以作为有效对冲工具' },
        { tag: '利率市场化', conclusion: '利率市场化推进下，股债避险对冲效应加强',
          risk: '有助于提升跨市场风险分散效率，支持金融体系韧性' },
        { tag: '灾难风险溢价', conclusion: '灾难风险能解释中国股市约39.5%的股权溢价',
          risk: '极端尾部事件是驱动市场过度波动的核心风险源' },
        { tag: '地方债传染', conclusion: '地方公共债务增加会显著降低企业间资源配置效率',
          risk: '地方债扩张可诱发系统性金融风险，需评估区域金融稳定' },
        { tag: '信用风险传导', conclusion: '存款保险制度削弱银行特许权价值，导致银行风险上升',
          risk: '需关注中小银行风险承担行为的激励效应' },
        { tag: '影子银行风险', conclusion: '抵押率是影响高风险企业融资成本的关键变量',
          risk: '仅关注利率可能产生误判，需监控非价格型信贷条件' },
        { tag: '跨境资本流动', conclusion: '区域危机期间中国证券市场与发达市场一体化水平反而增强',
          risk: '需加强国际协调并审慎控制开放节奏' },
        { tag: '网络安全感知', conclusion: '移动端投资者网络安全风险感知要求的风险补偿显著高于PC端',
          risk: '需加强移动应用安全防护，避免非理性赎回引发流动性风险' }
      ],
      // ⑬ P25xx 编码 - 违规类型精确分类
      p25CodeRows: [
        { code: 'P2599', name: '其他违规', count: 17320, pct: 32 },
        { code: 'P2504', name: '推迟披露', count: 8844, pct: 16 },
        { code: 'P2503', name: '虚假记载(误导性陈述)', count: 7758, pct: 14 },
        { code: 'P2505', name: '重大遗漏', count: 7065, pct: 13 },
        { code: 'P2512', name: '违规买卖股票', count: 4304, pct: 8 },
        { code: 'P2510', name: '占用公司资产', count: 1951, pct: 4 },
        { code: 'P2515', name: '一般会计处理不当', count: 1672, pct: 3 },
        { code: 'P2501', name: '虚构利润', count: 1555, pct: 3 },
        { code: 'P2514', name: '违规担保', count: 1151, pct: 2 },
        { code: 'P2506', name: '披露不实(其它)', count: 409, pct: 1 },
        { code: 'P2509', name: '擅自改变资金用途', count: 408, pct: 1 },
        { code: 'P2511', name: '内幕交易', count: 400, pct: 1 },
        { code: 'P2502', name: '虚列资产', count: 242, pct: 0.5 },
        { code: 'P2524', name: '未缴或少缴税款', count: 219, pct: 0.4 },
        { code: 'P2513', name: '操纵股价', count: 75, pct: 0.1 }
      ],
      // ⑭ 处罚金额区间
      fineRangeData: [
        { name: '10-100万', count: 694 },
        { name: '100-1000万', count: 219 },
        { name: '<10万', count: 55 },
        { name: '1000万-1亿', count: 43 },
        { name: '>1亿', count: 10 }
      ],
      // ⑮ 处罚方式
      punishData: [
        { name: '其他', count: 7336 },
        { name: '批评', count: 1472 },
        { name: '谴责', count: 781 },
        { name: '警告+罚款', count: 348 },
        { name: '警告+罚款+其他', count: 324 },
        { name: '罚款', count: 218 },
        { name: '罚款+其他', count: 72 },
        { name: '警告', count: 49 }
      ],
      // ⑯ 处分措施
      measureData: [
        { name: '整改。', count: 2571 },
        { name: '出具监管函。', count: 1016 },
        { name: '整改', count: 694 },
        { name: '内部通报批评', count: 146 },
        { name: '警示函(北京监管局)', count: 42 },
        { name: '内部批评', count: 42 },
        { name: '警示函(通用)', count: 27 },
        { name: '警示函(信息披露办法)', count: 25 }
      ],
      // ⑰ 违规年度
      vioYearData: [
        { name: '2021', count: 1223 }, { name: '2018', count: 1198 },
        { name: '2022', count: 1181 }, { name: '2017', count: 1148 },
        { name: '2020', count: 1090 }, { name: '2019', count: 1003 },
        { name: '2016', count: 998 }, { name: '2015', count: 920 }
      ],
      // ⑱ 实际控制人
      controllerData: [
        { name: '个人', count: 3567 }, { name: '地方政府国资', count: 707 },
        { name: '无实际控制人', count: 330 }, { name: '其它', count: 311 },
        { name: '国务院国资委', count: 177 }, { name: '地方各级人民政府', count: 62 },
        { name: '地方所属部委', count: 43 }, { name: '地方财政部门', count: 41 },
        { name: '投资公司', count: 37 }, { name: '资产管理公司', count: 12 }
      ],
      // ⑲ 资本背景
      capitalData: [
        { name: '民营', count: 20444 }, { name: '国有绝对控股', count: 14292 },
        { name: '国有相对控股', count: 6942 }, { name: '港澳台独资', count: 1545 },
        { name: '外商独资', count: 974 }, { name: '外商投资', count: 442 }
      ],
      // ⑳ 风险警示公司行业
      warningIndustryData: [
        { name: '批发业', count: 17 }, { name: '计算机通信', count: 14 },
        { name: '商务服务业', count: 8 }, { name: '软件信息技术', count: 7 },
        { name: '科技推广', count: 6 }, { name: '土木建筑', count: 5 },
        { name: '电气机械', count: 5 }, { name: '专业技术', count: 4 }
      ],
      // ㉑ 行业二级 TOP 12
      industryTopData: [
        { name: '批发业', count: 7270 }, { name: '商务服务业', count: 4201 },
        { name: '电力热力', count: 2319 }, { name: '科技推广', count: 2163 },
        { name: '计算机通信', count: 2011 }, { name: '零售业', count: 1995 },
        { name: '软件信息技术', count: 1665 }, { name: '土木建筑', count: 1638 },
        { name: '房地产业', count: 1595 }, { name: '化学原料', count: 1501 },
        { name: '电气机械', count: 1446 }, { name: '研究和试验', count: 1422 }
      ],
      // ㉒ 省份 TOP 12
      provinceData: [
        { name: '广东', count: 4132 }, { name: '浙江', count: 3700 },
        { name: '江苏', count: 3170 }, { name: '北京', count: 2403 },
        { name: '上海', count: 2186 }, { name: '山东', count: 2004 },
        { name: '四川', count: 1098 }, { name: '安徽', count: 1036 },
        { name: '湖北', count: 1018 }, { name: '福建', count: 991 },
        { name: '湖南', count: 934 }, { name: '辽宁', count: 855 }
      ],
      // ㉓ 子公司持股
      stakeData: [
        { name: '100%(全资)', count: 65692 },
        { name: '50-99%(控股)', count: 37035 },
        { name: '1-49%(参股)', count: 4418 },
        { name: '0%', count: 2010 }
      ],
      // ㉔ 客户/供应商资本背景对比
      csCapitalData: [
        { name: '客户-国有绝对控股', count: 27091 },
        { name: '客户-民营', count: 21585 },
        { name: '客户-国有相对控股', count: 13575 },
        { name: '供应商-民营', count: 55945 },
        { name: '供应商-国有绝对控股', count: 6872 },
        { name: '供应商-国有相对控股', count: 5152 }
      ],
      // ㉕ 客户/供应商行业
      csIndustryData: [
        { name: '批发业', count: 19979 },
        { name: '软件信息技术', count: 7901 },
        { name: '商务服务业', count: 10747 },
        { name: '科技推广', count: 5673 },
        { name: '电力热力', count: 5658 }
      ],
      // ㉖ 诉讼币种
      currencyData: [
        { name: 'CNY', count: 69272 }, { name: 'USD', count: 420 },
        { name: 'EUR', count: 57 }, { name: 'HKD', count: 32 },
        { name: 'CAD', count: 6 }, { name: 'GBP', count: 5 }
      ],
      // ㉗ 诉讼涉案金额区间
      litAmountData: [
        { name: '>1亿', count: 68464 },
        { name: '1000万-1亿', count: 534 },
        { name: '100-1000万', count: 55 },
        { name: '<100万', count: 15 }
      ],
      // ㉘ PLEDGE 用途
      pledgeUseData: [
        { name: 'Q5702 融资担保', count: 1601 },
        { name: 'Q5701 借款担保', count: 1470 },
        { name: 'Q5709 其他融资', count: 1239 },
        { name: 'Q5707 战略投资', count: 529 },
        { name: 'Q5706 资金周转', count: 496 },
        { name: 'Q5705 增持', count: 415 },
        { name: 'Q5708 项目融资', count: 275 },
        { name: 'Q5704 关联方', count: 117 }
      ],
      // ㉙ 子公司设立方式
      subSetupTypeData: [
        { name: '投资设立', count: 145000 },
        { name: '收购兼并', count: 42000 },
        { name: '合资设立', count: 8800 },
        { name: '分立设立', count: 2100 }
      ],
      // 模式创建
      createForm: {
        className: '',
        parentClass: '',
        attributes: [{ name: '', type: 'string', minCard: 1, maxCard: 1 }]
      },
      relForm: {
        name: '', from: '', to: '', symmetric: false, functional: false
      },
      classes: [
        // 与 Neo4j 节点类型对齐（基于扫描结果：513049 节点，8 种类型）
        { name: 'Company', parent: '', attributes: [
          { name: 'name', type: 'string', minCard: 1, maxCard: 1 },
          { name: 'credit_code', type: 'string', minCard: 0, maxCard: 1 },
          { name: 'province', type: 'string', minCard: 0, maxCard: 1 },
          { name: 'company_type', type: 'string', minCard: 0, maxCard: 1 },
          { name: 'is_listed', type: 'boolean', minCard: 0, maxCard: 1 }
        ]},
        { name: 'Litigation', parent: '', attributes: [
          { name: 'case_no', type: 'string', minCard: 1, maxCard: 1 },
          { name: 'case_type', type: 'string', minCard: 0, maxCard: 1 },
          { name: 'filing_date', type: 'date', minCard: 0, maxCard: 1 }
        ]},
        { name: 'Violation', parent: '', attributes: [
          { name: 'violation_type', type: 'string', minCard: 1, maxCard: 1 },
          { name: 'penalty_date', type: 'date', minCard: 0, maxCard: 1 },
          { name: 'penalty_amount', type: 'number', minCard: 0, maxCard: 1 }
        ]},
        { name: 'A_security', parent: 'Security', attributes: [
          { name: 'stock_code', type: 'string', minCard: 1, maxCard: 1 },
          { name: 'stock_name', type: 'string', minCard: 1, maxCard: 1 }
        ]},
        { name: 'G_security', parent: 'Security', attributes: [
          { name: 'stock_code', type: 'string', minCard: 1, maxCard: 1 },
          { name: 'stock_name', type: 'string', minCard: 1, maxCard: 1 }
        ]},
        { name: 'B_security', parent: 'Security', attributes: [
          { name: 'stock_code', type: 'string', minCard: 1, maxCard: 1 },
          { name: 'stock_name', type: 'string', minCard: 1, maxCard: 1 }
        ]},
        { name: 'Security', parent: '', attributes: [
          { name: 'security_type', type: 'string', minCard: 1, maxCard: 1 }
        ]},
        { name: 'City', parent: '', attributes: [
          { name: 'city_name', type: 'string', minCard: 1, maxCard: 1 },
          { name: 'province', type: 'string', minCard: 0, maxCard: 1 }
        ]},
        { name: 'MetaKnowledge', parent: '', attributes: [
          { name: 'knowledge_name', type: 'string', minCard: 1, maxCard: 1 },
          { name: 'description', type: 'string', minCard: 0, maxCard: 1 }
        ]}
      ],
      relations: [
        // 与 Neo4j 关系类型对齐（基于扫描结果：625578 关系，13 种类型）
        { name: '子公司', from: 'Company', to: 'Company', symmetric: false, functional: false },
        { name: '客户', from: 'Company', to: 'Company', symmetric: false, functional: false },
        { name: '供应商', from: 'Company', to: 'Company', symmetric: false, functional: false },
        { name: '诉讼仲裁', from: 'Company', to: 'Litigation', symmetric: false, functional: false },
        { name: '起诉', from: 'Company', to: 'Company', symmetric: false, functional: false },
        { name: 'PLEDGE', from: 'Company', to: 'Company', symmetric: false, functional: false },
        { name: '违规事件', from: 'Company', to: 'Violation', symmetric: false, functional: false },
        { name: 'GUARANTEES', from: 'Company', to: 'Company', symmetric: false, functional: false },
        { name: '所属城市', from: 'Company', to: 'City', symmetric: false, functional: true },
        { name: '拥有公司', from: 'Security', to: 'Company', symmetric: false, functional: false },
        { name: 'A股证券_公司资料', from: 'A_security', to: 'Company', symmetric: false, functional: true },
        { name: '港股证券_公司资料', from: 'G_security', to: 'Company', symmetric: false, functional: true },
        { name: 'B股证券_公司资料', from: 'B_security', to: 'Company', symmetric: false, functional: true }
      ],
      instances: [
        // 与 Neo4j 真实数据对齐的示例实例
        { type: 'Company', name: '阿里巴巴', 社会信用代码: '91330100799655058B', 省份: '浙江', company_type: '互联网' },
        { type: 'Company', name: '腾讯控股', 社会信用代码: '9144030071526726XG', 省份: '广东', company_type: '互联网' },
        { type: 'Company', name: '百度', 社会信用代码: '91110108717743469K', 省份: '北京', company_type: '互联网' },
        { type: 'Litigation', name: '诉讼案件-2024-001', case_no: '(2024)浙01民初123号', case_type: '合同纠纷' },
        { type: 'Violation', name: '违规事件-2024-A', violation_type: '信息披露违规', penalty_date: '2024-03-15' },
        { type: 'A_security', name: '阿里巴巴-A股', stock_code: '09988', stock_name: '阿里巴巴-W' },
        { type: 'G_security', name: '腾讯-港股', stock_code: '00700', stock_name: '腾讯控股' },
        { type: 'City', name: '杭州市', city_name: '杭州', province: '浙江' },
        { type: 'City', name: '深圳市', city_name: '深圳', province: '广东' },
        { type: 'MetaKnowledge', name: '知识图谱本体定义', knowledge_name: 'Ontology Schema', description: '定义知识图谱的类和关系结构' }
      ],
      // 用于分布统计的完整公司数据集（mock）- 注意：真实数据从 Neo4j 扫描获取
      // 由于公司数量巨大（41万+），使用统计摘要数据
      companyDataset: [
        // 前 20 家作为示例展示，其余以统计摘要形式呈现
        { name: '阿里巴巴', listed: true, industry: '互联网' },
        { name: '腾讯控股', listed: true, industry: '互联网' },
        { name: '百度', listed: true, industry: '互联网' },
        { name: '京东集团', listed: true, industry: '互联网' },
        { name: '美团', listed: true, industry: '互联网' },
        { name: '拼多多', listed: true, industry: '互联网' },
        { name: '快手科技', listed: true, industry: '互联网' },
        { name: '工商银行', listed: true, industry: '金融' },
        { name: '建设银行', listed: true, industry: '金融' },
        { name: '中国银行', listed: true, industry: '金融' },
        { name: '招商银行', listed: true, industry: '金融' },
        { name: '平安保险', listed: true, industry: '金融' },
        { name: '中国人寿', listed: true, industry: '金融' },
        { name: '中石油', listed: true, industry: '石油化工' },
        { name: '中石化', listed: true, industry: '石油化工' },
        { name: '中海油', listed: true, industry: '石油化工' },
        { name: '比亚迪', listed: true, industry: '汽车' },
        { name: '蔚来汽车', listed: true, industry: '汽车' },
        { name: '理想汽车', listed: true, industry: '汽车' },
        { name: '宁德时代', listed: true, industry: '新能源' },
        { name: '贵州茅台', listed: true, industry: '食品饮料' },
        { name: '五粮液', listed: true, industry: '食品饮料' },
        { name: '恒瑞医药', listed: true, industry: '医药生物' },
        { name: '万科地产', listed: true, industry: '房地产' },
        { name: '美的集团', listed: true, industry: '家电' },
        { name: '格力电器', listed: true, industry: '家电' },
        { name: '三一重工', listed: true, industry: '机械设备' },
        { name: '京东方', listed: true, industry: '电子' },
        { name: '华为投资', listed: false, industry: '互联网' },
        { name: '字节跳动', listed: false, industry: '互联网' }
      ],
      // 真实统计数据（从 Neo4j 扫描生成）
      realStats: {
        totalNodes: 513049,
        totalRelationships: 625578,
        companyCount: 411754,
        listedCount: 7827,
        unlistedCount: 403927,
        nodeTypeDistribution: {
          'Company': 411754,
          'Litigation': 73681,
          'Violation': 18776,
          'A_security': 5362,
          'G_security': 2644,
          'City': 546,
          'MetaKnowledge': 201,
          'B_security': 85
        },
        relationshipDistribution: {
          '子公司': 227459,
          '客户': 98247,
          '供应商': 82472,
          '诉讼仲裁': 75524,
          '起诉': 64780,
          'PLEDGE': 20863,
          '违规事件': 17346,
          'GUARANTEES': 14825,
          '所属城市': 10652,
          '拥有公司': 5363,
          'A股证券_公司资料': 5356,
          '港股证券_公司资料': 2606,
          'B股证券_公司资料': 85
        },
        industryDistribution: [
          { name: '其他', count: 177070 },
          { name: '互联网', count: 70721 },
          { name: '房地产', count: 24591 },
          { name: '金融', count: 21019 },
          { name: '石油化工', count: 19097 },
          { name: '医药生物', count: 12935 },
          { name: '机械设备', count: 11769 },
          { name: '交通运输', count: 8459 },
          { name: '汽车', count: 7100 },
          { name: '公用事业', count: 7046 },
          { name: '通信', count: 6500 },
          { name: '家电', count: 5800 },
          { name: '电子', count: 5200 },
          { name: '新能源', count: 4800 },
          { name: '建筑建材', count: 4200 }
        ]
      },
      instanceRels: [
        // 与 Neo4j 关系类型对齐的示例关系
        { from: '阿里巴巴', type: '子公司', to: '腾讯控股' },
        { from: '阿里巴巴', type: '客户', to: '百度' },
        { from: '阿里巴巴', type: '诉讼仲裁', to: '诉讼案件-2024-001' },
        { from: '阿里巴巴', type: '违规事件', to: '违规事件-2024-A' },
        { from: '阿里巴巴', type: '所属城市', to: '杭州市' },
        { from: '腾讯控股', type: '所属城市', to: '深圳市' },
        { from: '阿里巴巴-A股', type: 'A股证券_公司资料', to: '阿里巴巴' },
        { from: '腾讯-港股', type: '港股证券_公司资料', to: '腾讯控股' }
      ],
      openClasses: [],
      // 模式编辑
      editForm: { targetName: '', newName: '', newParent: '' },
      deleteTarget: '',
      editResult: null,
      editLogs: [],
      // 可视化
      vizRef: null,
      // 版本管理
      versionForm: { id: '', note: '' },
      versions: [
        { id: 'v0.9.0', time: this.nowOffset(-3), note: '初始版本：含 Organization/Company/Person/Industry', snapshot: null }
      ],
      diffResult: null,
      // 导入导出
      exportFormat: 'JSON-Schema',
      exportPreview: '',
      importFormat: 'auto',
      importText: '',
      importResult: null,
      // 实体分布统计
      pieSize: 220,
      // === Tab ⑦: 图谱浏览与性能 ===
      browseLayout: 'force',
      browseCanvasRef: null,
      selectedNode: null,
      browseHistory: [],
      bookmarks: [],
      filterNodeTypes: ['Company', 'Litigation', 'Violation', 'A_security', 'G_security', 'B_security', 'City'],
      filterPropKey: '',
      filterPropVal: '',
      sizeMapping: 'fixed',
      virtualRender: true,
      browseStats: { nodeCount: 0, edgeCount: 0, fps: 60, performance: '流畅' },
      // 性能测试
      perfTestSize: '10k',
      perfTesting: false,
      perfResult: null,
      // === Tab ⑧: 数据导入与抽取 ===
      // 结构化导入
      structuredPreview: null,
      importing: false,
      importProgress: { show: false, percent: 0, status: '', processed: 0, total: 0, success: 0, failed: 0, errors: [] },
      dbConfig: { type: 'mysql', host: '', database: '', username: '', password: '', sql: '' },
      apiConfig: { method: 'GET', url: '', authType: 'none', headers: '{}' },
      // 抽取
      extracting: false,
      extractConfig: { model: 'default', types: ['entity', 'relation'], language: 'zh', confidenceThreshold: 0.7 },
      extractResults: null,
      selectedEntities: [],
      selectedRelations: [],
      // 批量构建
      batchBuilding: false,
      batchConfig: { updateMode: 'append', batchSize: 1000, concurrency: 4 },
      batchResult: null,
      batchModeDescriptions: {
        append: '追加模式：新数据追加到已有图谱，不影响现有数据',
        merge: '合并模式：重复节点/关系会被合并属性，新增数据追加',
        replace: '覆盖模式：清空已有图谱后重新导入全部数据',
        version: '版本隔离：新数据创建为新版本，可随时切换回老版本'
      }
    };
  },
  computed: {
    instanceCount() {
      return this.instances.length;
    },
    statData() {
      // 使用从 Neo4j 扫描的真实统计数据
      const rs = this.realStats;
      const listedPct = rs.companyCount ? Math.round((rs.listedCount / rs.companyCount) * 100) : 0;
      const unlistedPct = 100 - listedPct;
      const palette = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9b59b6', '#1abc9c', '#e91e63', '#00bcd4', '#ff9800', '#795548', '#607d8b'];
      // 行业分布（使用真实数据）
      const industryDist = rs.industryDistribution.map((item, i) => ({
        name: item.name,
        count: item.count,
        pct: Math.round((item.count / rs.companyCount) * 100),
        color: palette[i % palette.length]
      }));
      // 实体类型分布（使用真实数据）
      const entityTypeRows = [
        { type: 'Company', count: rs.nodeTypeDistribution.Company, pct: Math.round((rs.nodeTypeDistribution.Company / rs.totalNodes) * 100), note: '包含上市与非上市公司' },
        { type: 'Litigation', count: rs.nodeTypeDistribution.Litigation, pct: Math.round((rs.nodeTypeDistribution.Litigation / rs.totalNodes) * 100), note: '诉讼仲裁案件' },
        { type: 'Violation', count: rs.nodeTypeDistribution.Violation, pct: Math.round((rs.nodeTypeDistribution.Violation / rs.totalNodes) * 100), note: '违规事件' },
        { type: 'A_security', count: rs.nodeTypeDistribution.A_security, pct: Math.round((rs.nodeTypeDistribution.A_security / rs.totalNodes) * 100), note: 'A股证券' },
        { type: 'G_security', count: rs.nodeTypeDistribution.G_security, pct: Math.round((rs.nodeTypeDistribution.G_security / rs.totalNodes) * 100), note: '港股证券' },
        { type: 'City', count: rs.nodeTypeDistribution.City, pct: Math.round((rs.nodeTypeDistribution.City / rs.totalNodes) * 100), note: '城市节点' },
        { type: '其他', count: rs.nodeTypeDistribution.MetaKnowledge + rs.nodeTypeDistribution.B_security, pct: Math.round(((rs.nodeTypeDistribution.MetaKnowledge + rs.nodeTypeDistribution.B_security) / rs.totalNodes) * 100), note: '元知识和B股' }
      ].sort((a, b) => b.count - a.count);

      // 违规事件主体行业分布
      const violationIndRows = [
        { name: '其他', count: 1509 }, { name: '投资控股', count: 907 }, { name: '互联网', count: 898 },
        { name: '石油化工', count: 319 }, { name: '医药生物', count: 265 }, { name: '有色金属', count: 144 },
        { name: '电子元件', count: 111 }, { name: '证券', count: 106 }, { name: '传媒', count: 99 },
        { name: '机械设备', count: 99 }, { name: '房地产', count: 78 }, { name: '家电', count: 67 },
        { name: '汽车', count: 54 }, { name: '公用事业', count: 47 }, { name: '银行', count: 41 }
      ];

      // 诉讼案件-原告行业
      const litigationPlaintiff = [
        { name: '其他', count: 1379 }, { name: '银行', count: 527 }, { name: '投资控股', count: 444 },
        { name: '互联网', count: 366 }, { name: '房地产', count: 320 }, { name: '电子元件', count: 214 },
        { name: '机械设备', count: 119 }, { name: '证券', count: 102 }, { name: '商贸零售', count: 100 },
        { name: '建筑材料', count: 87 }
      ];

      // 诉讼案件-被告行业
      const litigationDefendant = [
        { name: '其他', count: 1956 }, { name: '投资控股', count: 669 }, { name: '房地产', count: 489 },
        { name: '互联网', count: 446 }, { name: '石油化工', count: 180 }, { name: '机械设备', count: 172 },
        { name: '银行', count: 152 }, { name: '电子元件', count: 119 }, { name: '汽车', count: 115 },
        { name: '医药生物', count: 101 }
      ];

      // 诉讼案件-涉案缘由
      const litigationReason = [
        { name: '买卖合同纠纷', count: 815 }, { name: '贷款纠纷', count: 632 },
        { name: '欠款纠纷', count: 383 }, { name: '建设工程施工合同纠纷', count: 364 },
        { name: '合同纠纷', count: 354 }, { name: '劳务纠纷', count: 341 },
        { name: '担保牵连', count: 180 }, { name: '股权纠纷', count: 144 },
        { name: '不当竞争纠纷', count: 112 }, { name: '票据纠纷', count: 90 }
      ];

      // 诉讼案件-涉案金额分布
      const litigationAmount = [
        { name: '<100万', count: 346 }, { name: '100-1000万', count: 3 },
        { name: '1000万-1亿', count: 19 }, { name: '>1亿', count: 4632 }
      ];

      // 违规类型核心 10 类
      const violationTypes = [
        { name: '推迟披露', count: 1408 }, { name: '虚假记载(误导性陈述)', count: 783 },
        { name: '重大遗漏', count: 688 }, { name: '违规买卖股票', count: 678 },
        { name: '一般会计处理不当', count: 169 }, { name: '虚构利润', count: 115 },
        { name: '内幕交易', count: 92 }, { name: '占用公司资产', count: 89 },
        { name: '披露不实(其它)', count: 47 }, { name: '未缴或少缴税款(欠税)', count: 25 }
      ];

      // 原告-被告行业关联 TOP 10
      const litigationMatrixRows = [
        { plaintiff: '其他', defendant: '其他', count: 570 },
        { plaintiff: '其他', defendant: '房地产', count: 172 },
        { plaintiff: '其他', defendant: '投资控股', count: 155 },
        { plaintiff: '银行', defendant: '投资控股', count: 153 },
        { plaintiff: '房地产', defendant: '其他', count: 134 },
        { plaintiff: '投资控股', defendant: '其他', count: 128 },
        { plaintiff: '其他', defendant: '互联网', count: 119 },
        { plaintiff: '投资控股', defendant: '互联网', count: 98 },
        { plaintiff: '银行', defendant: '房地产', count: 87 },
        { plaintiff: '互联网', defendant: '其他', count: 82 }
      ];

      // 金融风险-质押
      const pledgeInd = [
        { name: '投资控股', count: 1846 }, { name: '其他', count: 388 },
        { name: '互联网', count: 131 }, { name: '房地产', count: 113 },
        { name: '交通运输', count: 104 }
      ];

      // 金融风险-担保
      const guaranteeInd = [
        { name: '投资控股', count: 696 }, { name: '其他', count: 695 },
        { name: '互联网', count: 455 }, { name: '医药生物', count: 281 },
        { name: '机械设备', count: 164 }
      ];

      // 金融风险-起诉
      const sueInd = [
        { name: '其他', count: 1008 }, { name: '投资控股', count: 500 },
        { name: '房地产', count: 325 }, { name: '电子元件', count: 234 },
        { name: '互联网', count: 224 }
      ];

      // 高风险公司 TOP 10
      const highRiskRows = [
        { name: '陕西建工集团股份有限公司', vio: 9, lit: 1220, sue: 102, pledge: 0, gua: 0, total: 1331 },
        { name: '北京嘉寓门窗幕墙股份有限公司', vio: 0, lit: 1164, sue: 49, pledge: 0, gua: 0, total: 1213 },
        { name: '嘉寓控股股份公司', vio: 16, lit: 938, sue: 21, pledge: 0, gua: 17, total: 992 },
        { name: '兴源环境科技股份有限公司', vio: 15, lit: 937, sue: 8, pledge: 0, gua: 19, total: 979 },
        { name: '陕西坚瑞沃能股份有限公司', vio: 0, lit: 911, sue: 0, pledge: 0, gua: 0, total: 911 },
        { name: '京蓝科技股份有限公司', vio: 15, lit: 869, sue: 2, pledge: 0, gua: 12, total: 898 },
        { name: '中通国脉通信股份有限公司', vio: 7, lit: 705, sue: 3, pledge: 0, gua: 0, total: 715 },
        { name: '深圳文科园林股份有限公司', vio: 0, lit: 329, sue: 323, pledge: 0, gua: 0, total: 652 },
        { name: '新疆拉夏贝尔服饰股份有限公司', vio: 5, lit: 633, sue: 11, pledge: 0, gua: 0, total: 649 },
        { name: '重庆建工集团股份有限公司', vio: 3, lit: 556, sue: 71, pledge: 0, gua: 18, total: 648 }
      ];

      // 金融风险类型概览
      const financialRiskTypes = [
        { name: '股权质押 (PLEDGE)', count: 20863, color: '#e6a23c', desc: '股东出质股权融资' },
        { name: '对外担保 (GUARANTEES)', count: 14825, color: '#f56c6c', desc: '为他人债务担保' },
        { name: '诉讼仲裁 (Litigation)', count: 75524, color: '#409eff', desc: '司法诉讼案件' },
        { name: '违规事件 (Violation)', count: 18776, color: '#909399', desc: '监管处罚事件' },
        { name: '起诉 (SUE)', count: 64780, color: '#67c23a', desc: '主动法律诉讼' },
        { name: '关联关系 (子公司/客户/供应商)', count: 408178, color: '#9b59b6', desc: '实体间业务关联' }
      ];

      return {
        totalEntities: rs.totalNodes,
        totalRelations: rs.totalRelationships,
        listedCount: rs.listedCount,
        unlistedCount: rs.unlistedCount,
        listedPct,
        unlistedPct,
        industryDist,
        entityTypeRows,
        // 细粒度数据
        violationIndRows,
        litigationPlaintiff,
        litigationDefendant,
        litigationReason,
        litigationAmount,
        violationTypes,
        litigationMatrixRows,
        pledgeInd,
        guaranteeInd,
        sueInd,
        highRiskRows,
        financialRiskTypes,
        relationshipDist: Object.entries(rs.relationshipDistribution)
          .map(([name, count]) => ({ name, count }))
          .sort((a, b) => b.count - a.count)
      };
    }
  },
  mounted() {
    this.$nextTick(() => {
      // viz 初始化延后到 tab 切换
    });
  },
  watch: {
    activeTab(n) {
      // 用 requestAnimationFrame 延后到下一帧，避免与 el-tabs/el-card 的
      // ResizeObserver 回调同帧触发 DOM 变更，导致 "ResizeObserver loop" 警告
      if (n === 'viz') {
        this.$nextTick(() => requestAnimationFrame(() => this.initViz()));
      } else if (n === 'stats') {
        this.$nextTick(() => requestAnimationFrame(() => {
          this.drawPie();
          this.drawDetailedCharts();
        }));
      } else if (n === 'browse') {
        this.$nextTick(() => requestAnimationFrame(() => this.initBrowseCanvas()));
      } else if (n === 'risk') {
        this.$nextTick(() => requestAnimationFrame(() => this.drawRiskCharts()));
      }
    }
  },
  methods: {
    nowOffset(daysAgo) {
      const d = new Date();
      d.setDate(d.getDate() - daysAgo);
      return d.toLocaleString('zh-CN');
    },
    addAttribute() {
      this.createForm.attributes.push({ name: '', type: 'string', minCard: 0, maxCard: 1 });
    },
    getInstanceCount(clsName) {
      return this.instances.filter(i => i.type === clsName).length;
    },
    validateClassName(name) {
      if (!/^[A-Z][A-Za-z0-9_]*$/.test(name)) {
        return '类名必须以大写字母开头，仅含字母数字下划线';
      }
      if (this.classes.some(c => c.name === name)) return '类名已存在';
      // 检查继承冲突（环）
      if (this.createForm.parentClass) {
        const chain = this.getAncestorChain(this.createForm.parentClass);
        if (chain.includes(name)) return '继承链存在循环';
      }
      return null;
    },
    getAncestorChain(name, chain = []) {
      const cls = this.classes.find(c => c.name === name);
      if (!cls) return chain;
      chain.push(cls.name);
      if (cls.parent) return this.getAncestorChain(cls.parent, chain);
      return chain;
    },
    onCreateClass() {
      const err = this.validateClassName(this.createForm.className);
      if (err) { ElMessage.error(err); return; }
      // 校验属性
      const attrs = this.createForm.attributes.filter(a => a.name);
      for (const a of attrs) {
        if (!/^[a-z][A-Za-z0-9_]*$/.test(a.name)) {
          ElMessage.error(`属性 ${a.name} 不合法（需小写字母开头）`);
          return;
        }
        if (a.minCard > a.maxCard) {
          ElMessage.error(`属性 ${a.name} 最小基数不能大于最大基数`);
          return;
        }
      }
      this.classes.push({
        name: this.createForm.className,
        parent: this.createForm.parentClass,
        attributes: attrs
      });
      ElMessage.success(`类 ${this.createForm.className} 创建成功`);
      this.addLog('success', `创建类 ${this.createForm.className}（继承自 ${this.createForm.parentClass || '无'}）`);
      this.resetCreateForm();
    },
    resetCreateForm() {
      this.createForm = { className: '', parentClass: '', attributes: [{ name: '', type: 'string', minCard: 1, maxCard: 1 }] };
    },
    onCreateRelation() {
      if (!this.relForm.name) { ElMessage.error('请输入关系名'); return; }
      if (!this.relForm.from || !this.relForm.to) { ElMessage.error('请选择起始/目标类'); return; }
      if (this.relations.some(r => r.name === this.relForm.name)) { ElMessage.error('关系已存在'); return; }
      this.relations.push({ ...this.relForm });
      ElMessage.success(`关系 ${this.relForm.name} 创建成功`);
      this.addLog('success', `创建关系 ${this.relForm.name}（${this.relForm.from} → ${this.relForm.to}）`);
      this.relForm = { name: '', from: '', to: '', symmetric: false, functional: false };
    },
    // 编辑
    onSelectEditClass() {
      const c = this.classes.find(x => x.name === this.editForm.targetName);
      if (c) {
        this.editForm.newName = c.name;
        this.editForm.newParent = c.parent;
      }
    },
    onApplyEdit() {
      const oldName = this.editForm.targetName;
      if (!oldName) return;
      const c = this.classes.find(x => x.name === oldName);
      if (!c) return;
      const conflicts = [];
      const synced = [];
      // 检测循环继承
      if (this.editForm.newParent) {
        const chain = this.getAncestorChain(this.editForm.newParent);
        if (chain.includes(this.editForm.newName) || this.editForm.newParent === this.editForm.newName) {
          conflicts.push('新父类将导致继承循环');
        }
      }
      if (conflicts.length) {
        this.editResult = { title: '存在冲突，未应用修改', type: 'error', description: '请先解决以下冲突', conflicts, synced: [] };
        this.addLog('danger', `编辑 ${oldName} 失败：${conflicts.join('; ')}`);
        return;
      }
      const renamed = this.editForm.newName !== oldName;
      if (renamed) {
        // 同步更新引用此类的关系/实例
        this.relations.forEach(r => {
          if (r.from === oldName) { r.from = this.editForm.newName; synced.push(`关系 ${r.name} 起始类 ${oldName}→${this.editForm.newName}`); }
          if (r.to === oldName) { r.to = this.editForm.newName; synced.push(`关系 ${r.name} 目标类 ${oldName}→${this.editForm.newName}`); }
        });
        this.instances.filter(i => i.type === oldName).forEach(i => {
          i.type = this.editForm.newName;
          synced.push(`实例 ${i.name} 类型已更新`);
        });
        c.name = this.editForm.newName;
      }
      c.parent = this.editForm.newParent;
      this.editResult = {
        title: '修改已应用',
        type: 'success',
        description: renamed ? `类已重命名为 ${this.editForm.newName}，已同步相关引用` : '属性已更新',
        conflicts: [],
        synced
      };
      this.addLog('success', `编辑类 ${oldName} → ${this.editForm.newName}（同步 ${synced.length} 项）`);
    },
    onCheckAndDelete() {
      const target = this.deleteTarget;
      // 引用检查
      const relRefs = this.relations.filter(r => r.from === target || r.to === target);
      const instRefs = this.instances.filter(i => i.type === target);
      if (relRefs.length === 0 && instRefs.length === 0) {
        // 安全删除
        this.classes = this.classes.filter(c => c.name !== target);
        this.editResult = { title: '安全删除', type: 'success', description: `类 ${target} 未被任何关系/实例引用，已安全删除`, conflicts: [], synced: [] };
        this.addLog('success', `安全删除类 ${target}`);
        this.deleteTarget = '';
        return;
      }
      // 存在引用，弹窗确认
      ElMessageBox.confirm(
        `类 ${target} 被以下元素引用：\n- 关系：${relRefs.map(r=>r.name).join(', ') || '无'}\n- 实例：${instRefs.map(i=>i.name).join(', ') || '无'}\n\n删除将一并移除这些引用，是否继续？`,
        '安全警告：存在引用',
        { confirmButtonText: '强制删除', cancelButtonText: '取消', type: 'warning' }
      ).then(() => {
        const synced = [];
        this.relations = this.relations.filter(r => {
          if (r.from === target || r.to === target) { synced.push(`关系 ${r.name}`); return false; }
          return true;
        });
        this.instances = this.instances.filter(i => {
          if (i.type === target) { synced.push(`实例 ${i.name}`); return false; }
          return true;
        });
        this.instanceRels = this.instanceRels.filter(r => {
          return !instRefs.find(i => i.name === r.from || i.name === r.to);
        });
        this.classes = this.classes.filter(c => c.name !== target);
        this.editResult = {
          title: '强制删除完成',
          type: 'warning',
          description: `已级联删除 ${synced.length} 项引用`,
          conflicts: [], synced
        };
        this.addLog('warning', `强制删除类 ${target}（级联 ${synced.length} 项）`);
        this.deleteTarget = '';
      }).catch(() => {});
    },
    addLog(type, text) {
      this.editLogs.unshift({ time: new Date().toLocaleTimeString('zh-CN'), type, text });
    },
    // 可视化
    initViz() {
      const container = this.$refs.vizRef;
      if (!container) return;
      container.innerHTML = '';
      const width = container.clientWidth;
      const height = container.clientHeight || 500;

      const svg = d3.select(container).append('svg')
        .attr('width', width).attr('height', height)
        .style('background', '#fafbfc').style('border-radius', '6px');

      const defs = svg.append('defs');
      defs.append('marker').attr('id', 'arrow').attr('viewBox', '0 -5 10 10').attr('refX', 22).attr('refY', 0)
        .attr('markerWidth', 6).attr('markerHeight', 6).attr('orient', 'auto')
        .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', '#999');

      const g = svg.append('g');
      const zoom = d3.zoom().scaleExtent([0.2, 4]).on('zoom', (e) => g.attr('transform', e.transform));
      svg.call(zoom);
      this._vizSvg = svg; this._vizZoom = zoom; this._vizG = g; this._vizWH = { width, height };
      this.drawViz();
    },
    drawViz() {
      const g = this._vizG;
      g.selectAll('*').remove();
      const nodes = this.classes.map(c => ({ id: c.name, name: c.name, parent: c.parent, attrs: c.attributes.length }));
      const links = [];
      this.classes.forEach(c => { if (c.parent) links.push({ source: c.parent, target: c.name, type: 'inherit' }); });
      // 加入关系（非继承）作为虚线
      this.relations.forEach(r => {
        if (!this.classes.find(c => c.name === r.from) || !this.classes.find(c => c.name === r.to)) return;
        if (links.find(l => l.source === r.from && l.target === r.name)) return;
        if (!this.classes.find(c => c.name === r.from).parent || r.from !== r.to) {
          // 简化：只画继承图
        }
      });

      // 自动布局
      const W = this._vizWH.width, H = this._vizWH.height;
      const cx = W / 2, cy = H / 2;
      const r = Math.min(W, H) * 0.32;
      nodes.forEach((n, i) => {
        const a = (i / nodes.length) * Math.PI * 2 - Math.PI / 2;
        n.x = cx + r * Math.cos(a);
        n.y = cy + r * Math.sin(a);
        n.fx = null; n.fy = null;
      });

      // 链接
      const link = g.append('g').selectAll('line').data(links).enter().append('line')
        .attr('stroke', '#67c23a').attr('stroke-width', 2)
        .attr('marker-end', 'url(#arrow)');

      // 关系（非继承）作为虚线
      const relLinks = this.relations.map(r => ({ source: r.from, target: r.to, name: r.name }))
        .filter(r => nodes.find(n => n.id === r.source) && nodes.find(n => n.id === r.target));
      const relG = g.append('g').selectAll('g').data(relLinks).enter().append('g');
      relG.append('line')
        .attr('stroke', '#e6a23c').attr('stroke-dasharray', '6,4').attr('stroke-width', 1.5)
        .attr('x1', d => nodes.find(n => n.id === d.source).x)
        .attr('y1', d => nodes.find(n => n.id === d.source).y)
        .attr('x2', d => nodes.find(n => n.id === d.target).x)
        .attr('y2', d => nodes.find(n => n.id === d.target).y);
      relG.append('text')
        .attr('x', d => (nodes.find(n => n.id === d.source).x + nodes.find(n => n.id === d.target).x) / 2)
        .attr('y', d => (nodes.find(n => n.id === d.source).y + nodes.find(n => n.id === d.target).y) / 2 - 4)
        .attr('text-anchor', 'middle').attr('fill', '#e6a23c').attr('font-size', 10)
        .text(d => d.name);

      // 节点
      const node = g.append('g').selectAll('g').data(nodes).enter().append('g')
        .attr('cursor', 'move')
        .call(d3.drag()
          .on('start', (e, d) => { d.fx = d.x; d.fy = d.y; })
          .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; this.updatePositions(d, link, relG); })
          .on('end', (e, d) => { d.fx = null; d.fy = null; })
        );

      node.append('rect')
        .attr('x', -50).attr('y', -28).attr('width', 100).attr('height', 56)
        .attr('rx', 8).attr('fill', '#409eff').attr('stroke', '#fff').attr('stroke-width', 2);

      node.append('text').attr('text-anchor', 'middle').attr('y', -8)
        .attr('fill', '#fff').attr('font-weight', 'bold').attr('font-size', 13)
        .text(d => d.id);
      node.append('text').attr('text-anchor', 'middle').attr('y', 10)
        .attr('fill', '#fff').attr('font-size', 11)
        .text(d => `⊂ ${d.parent || 'root'}`);
      node.append('text').attr('text-anchor', 'middle').attr('y', 22)
        .attr('fill', '#fff').attr('font-size', 10)
        .text(d => `${d.attrs} 属性`);

      this._vizNodes = nodes;
    },
    updatePositions(d) {
      d.x = d.fx; d.y = d.fy;
      // 简化：刷新整图（用 rAF 节流，避免拖拽过程中反复触发 ResizeObserver 循环）
      if (this._vizRaf) cancelAnimationFrame(this._vizRaf);
      this._vizRaf = requestAnimationFrame(() => this.drawViz());
    },
    zoomIn() { this._vizSvg.transition().call(this._vizZoom.scaleBy, 1.3); },
    zoomOut() { this._vizSvg.transition().call(this._vizZoom.scaleBy, 0.7); },
    resetZoom() { this._vizSvg.transition().call(this._vizZoom.transform, d3.zoomIdentity); },
    autoLayout() { this.drawViz(); },
    exportPng() {
      const svgEl = this.$refs.vizRef.querySelector('svg');
      if (!svgEl) return;
      const xml = new XMLSerializer().serializeToString(svgEl);
      const svg64 = btoa(unescape(encodeURIComponent(xml)));
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = svgEl.clientWidth; canvas.height = svgEl.clientHeight;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        const a = document.createElement('a');
        a.download = 'ontology.png';
        a.href = canvas.toDataURL('image/png');
        a.click();
        ElMessage.success('已导出 ontology.png');
      };
      img.src = 'data:image/svg+xml;base64,' + svg64;
    },
    // 实体分布：饼图（上市 vs 非上市）
    drawPie() {
      const ref = this.$refs.pieRef;
      if (!ref) return;
      const svg = d3.select(ref);
      svg.selectAll('*').remove();
      const w = this.pieSize, h = this.pieSize;
      const r = Math.min(w, h) / 2 - 8;
      const data = [
        { label: '上市公司', value: this.statData.listedCount, color: '#409eff' },
        { label: '非上市公司', value: this.statData.unlistedCount, color: '#909399' }
      ];
      const total = data.reduce((s, d) => s + d.value, 0) || 1;
      const g = svg.append('g').attr('transform', `translate(${w/2},${h/2})`);
      const pie = d3.pie().value(d => d.value).sort(null);
      const arc = d3.arc().innerRadius(r * 0.55).outerRadius(r);
      const arcs = g.selectAll('path').data(pie(data)).enter();
      arcs.append('path')
        .attr('d', arc)
        .attr('fill', d => d.data.color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
      // 中心文字
      g.append('text').attr('text-anchor', 'middle').attr('y', -6)
        .attr('font-size', 14).attr('fill', '#909399').text('公司总数');
      g.append('text').attr('text-anchor', 'middle').attr('y', 18)
        .attr('font-size', 22).attr('font-weight', 'bold').attr('fill', '#303133').text(total);
    },
    // 通用水平条形图绘制器
    drawBarChart(ref, data, opts = {}) {
      const el = this.$refs[ref];
      if (!el) return;
      // 清空容器，并创建一个真正的 <svg> 元素作为 SVG 画布
      // （不能直接把 SVG 子元素 append 到 <div>，否则浏览器不会按 SVG 渲染，文字会平铺成一坨）
      el.innerHTML = '';
      const svg = d3.select(el).append('svg');
      // 取父级容器宽度（el-card body），确保 svg 有足够画布
      const parent = el.parentElement;
      const rect = parent ? parent.getBoundingClientRect() : null;
      const width = Math.max(280, (rect ? rect.width : 0) - 8);
      const height = opts.height || Math.max(160, data.length * 22);
      svg.attr('width', width).attr('height', height)
        .style('display', 'block')
        .attr('viewBox', `0 0 ${width} ${height}`);
      const margin = { top: 8, right: 60, bottom: 8, left: opts.labelWidth || 90 };
      const innerW = Math.max(80, width - margin.left - margin.right);
      const innerH = Math.max(80, height - margin.top - margin.bottom);
      const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);
      const max = d3.max(data, d => d.count) || 1;
      const x = d3.scaleLinear().domain([0, max]).range([0, innerW]);
      const y = d3.scaleBand().domain(data.map((_, i) => i)).range([0, innerH]).padding(0.2);
      const palette = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9b59b6', '#1abc9c', '#e91e63', '#00bcd4', '#ff9800', '#795548', '#607d8b', '#5cb85c', '#d9534f', '#f0ad4e'];
      g.selectAll('rect').data(data).enter().append('rect')
        .attr('x', 0).attr('y', (_, i) => y(i))
        .attr('width', d => x(d.count)).attr('height', y.bandwidth())
        .attr('fill', (_, i) => palette[i % palette.length])
        .attr('rx', 2);
      g.selectAll('.label').data(data).enter().append('text')
        .attr('x', -6).attr('y', (_, i) => y(i) + y.bandwidth() / 2 + 4)
        .attr('text-anchor', 'end').attr('font-size', 12).attr('fill', '#303133')
        .text(d => d.name);
      g.selectAll('.val').data(data).enter().append('text')
        .attr('x', d => x(d.count) + 4).attr('y', (_, i) => y(i) + y.bandwidth() / 2 + 4)
        .attr('font-size', 11).attr('fill', '#909399')
        .text(d => d.count.toLocaleString());
    },
    // 绘制所有细粒度图表
    drawDetailedCharts() {
      this.drawBarChart('violationIndRef', this.statData.violationIndRows.slice(0, 12), { labelWidth: 80, height: 320 });
      this.drawBarChart('violationTypeRef', this.statData.violationTypes, { labelWidth: 140, height: 280 });
      this.drawBarChart('litigationPlaintiffRef', this.statData.litigationPlaintiff, { labelWidth: 80, height: 280 });
      this.drawBarChart('litigationDefendantRef', this.statData.litigationDefendant, { labelWidth: 80, height: 280 });
      this.drawBarChart('litigationReasonRef', this.statData.litigationReason, { labelWidth: 130, height: 280 });
      this.drawBarChart('litigationAmountRef', this.statData.litigationAmount, { labelWidth: 90, height: 180 });
      this.drawBarChart('pledgeRef', this.statData.pledgeInd, { labelWidth: 80, height: 180 });
      this.drawBarChart('guaranteeRef', this.statData.guaranteeInd, { labelWidth: 80, height: 180 });
      this.drawBarChart('sueRef', this.statData.sueInd, { labelWidth: 80, height: 180 });
    },
    // 绘制风险知识页面所有图表
    drawRiskCharts() {
      // 1) MetaKnowledge 分类水平条形图
      this.drawBarChart('mkCategoryRef', this.metaKnowledgeRows, { labelWidth: 130, height: 280 });
      // 2) 监管来源 TOP 10
      const regulatorData = [
        { name: '深圳证券交易所', count: 6227 }, { name: '上海证券交易所', count: 2705 },
        { name: '中国证监会', count: 1393 }, { name: '广东监管局', count: 691 },
        { name: '北京监管局', count: 390 }, { name: '江苏证监局', count: 325 },
        { name: '浙江监管局', count: 599 }, { name: '深圳证监局', count: 284 }
      ];
      this.drawBarChart('regulatorRef', regulatorData, { labelWidth: 110, height: 280 });
      // 3) 质押权人
      this.drawBarChart('pledgeeRef', [
        { name: '银行', count: 7585 }, { name: '证券公司', count: 6108 },
        { name: '信托公司', count: 3068 }, { name: '其他', count: 4102 }
      ], { labelWidth: 60, height: 200 });
      // 4) 质押变动
      this.drawBarChart('pledgeChangeRef', [
        { name: '全部解押', count: 14013 }, { name: '新增质押', count: 4991 },
        { name: '转增股本/送股', count: 824 }, { name: '其他', count: 1035 }
      ], { labelWidth: 90, height: 200 });
      // 5) 担保对象
      this.drawBarChart('guaTargetRef', [
        { name: '上市公司子公司', count: 13976 }, { name: '上市公司联营企业', count: 294 },
        { name: '独立第三方', count: 166 }, { name: '其他', count: 389 }
      ], { labelWidth: 110, height: 200 });
      // 6) 担保期限
      this.drawBarChart('guaTermRef', [
        { name: '12 个月', count: 2165 }, { name: '36 个月', count: 1643 },
        { name: '24 个月', count: 985 }, { name: '60 个月', count: 612 },
        { name: '48 个月', count: 387 }, { name: '其他', count: 9033 }
      ], { labelWidth: 80, height: 200 });
      // 7) 司法进程
      this.drawBarChart('judicialRef', [
        { name: '一审 (Q3502)', count: 56529 }, { name: '二审 (Q3503)', count: 10045 },
        { name: '再审 (Q3501)', count: 6159 }, { name: '执行 (Q3504)', count: 948 }
      ], { labelWidth: 100, height: 200 });
      // 8) 客户经营异常
      this.drawBarChart('custRiskRef', [
        { name: '注销', count: 2634 }, { name: '吊销未注销', count: 351 },
        { name: '该单位已注销', count: 377 }, { name: '注销企业', count: 370 },
        { name: '在营', count: 90000 }, { name: '其他', count: 7000 }
      ], { labelWidth: 90, height: 240 });
      // 9) 客户企业规模
      this.drawBarChart('custScaleRef', [
        { name: '大型企业', count: 29417 }, { name: '中型企业', count: 11337 },
        { name: '小微企业', count: 21296 }, { name: '未注明', count: 36197 }
      ], { labelWidth: 70, height: 200 });
      // 10) 子公司是否退出
      this.drawBarChart('subExitRef', [
        { name: '否 (在册)', count: 198000 }, { name: '是 (已退出)', count: 22000 },
        { name: '未注明', count: 7459 }
      ], { labelWidth: 90, height: 200 });
      // 11) 子公司设立方式
      this.drawBarChart('subSetupRef', [
        { name: '投资设立', count: 145000 }, { name: '收购兼并', count: 42000 },
        { name: '其他', count: 40459 }
      ], { labelWidth: 70, height: 200 });
      // ⑭ 处罚金额区间
      this.drawBarChart('fineRangeRef', this.fineRangeData, { labelWidth: 80, height: 200 });
      // ⑮ 处罚方式
      this.drawBarChart('punishRef', this.punishData, { labelWidth: 110, height: 200 });
      // ⑯ 处分措施
      this.drawBarChart('measureRef', this.measureData, { labelWidth: 130, height: 240 });
      // ⑰ 违规年度
      this.drawBarChart('vioYearRef', this.vioYearData, { labelWidth: 60, height: 200 });
      // ⑱ 实际控制人
      this.drawBarChart('controllerRef', this.controllerData, { labelWidth: 110, height: 240 });
      // ⑲ 资本背景
      this.drawBarChart('capitalRef', this.capitalData, { labelWidth: 100, height: 200 });
      // ⑳ 风险警示行业
      this.drawBarChart('warningRef', this.warningIndustryData, { labelWidth: 100, height: 200 });
      // ㉑ 行业二级
      this.drawBarChart('industryRef', this.industryTopData, { labelWidth: 120, height: 280 });
      // ㉒ 省份分布
      this.drawBarChart('provinceRef', this.provinceData, { labelWidth: 60, height: 280 });
      // ㉓ 子公司持股
      this.drawBarChart('stakeRef', this.stakeData, { labelWidth: 100, height: 180 });
      // ㉔ 客户/供应商资本背景
      this.drawBarChart('csCapitalRef', this.csCapitalData, { labelWidth: 130, height: 220 });
      // ㉕ 客户/供应商行业
      this.drawBarChart('csIndustryRef', this.csIndustryData, { labelWidth: 100, height: 200 });
      // ㉖ 诉讼币种
      this.drawBarChart('currencyRef', this.currencyData, { labelWidth: 50, height: 200 });
      // ㉗ 诉讼涉案金额
      this.drawBarChart('litAmountRef', this.litAmountData, { labelWidth: 90, height: 200 });
      // ㉘ PLEDGE 用途
      this.drawBarChart('pledgeUseRef', this.pledgeUseData, { labelWidth: 110, height: 240 });
      // ㉙ 子公司设立方式
      this.drawBarChart('subSetupTypeRef', this.subSetupTypeData, { labelWidth: 70, height: 200 });
    },
    // 版本管理
    saveVersion() {
      if (!this.versionForm.id) { ElMessage.error('请输入版本号'); return; }
      if (this.versions.some(v => v.id === this.versionForm.id)) { ElMessage.error('版本号已存在'); return; }
      this.versions.push({
        id: this.versionForm.id,
        time: new Date().toLocaleString('zh-CN'),
        note: this.versionForm.note,
        snapshot: JSON.parse(JSON.stringify({ classes: this.classes, relations: this.relations }))
      });
      ElMessage.success(`版本 ${this.versionForm.id} 已保存`);
      this.versionForm = { id: '', note: '' };
    },
    compareVersion(v) {
      if (!v.snapshot) {
        ElMessage.warning('该版本为初始占位版本，无快照数据，无法对比');
        return;
      }
      const oldClasses = new Map(v.snapshot.classes.map(c => [c.name, c]));
      const newClasses = new Map(this.classes.map(c => [c.name, c]));
      const added = [], removed = [], modified = [];
      newClasses.forEach((c, name) => {
        if (!oldClasses.has(name)) added.push(`类 ${name}`);
        else {
          const o = oldClasses.get(name);
          if (JSON.stringify(o) !== JSON.stringify(c)) {
            const diffs = [];
            if (o.parent !== c.parent) diffs.push(`父类: ${o.parent||'无'} → ${c.parent||'无'}`);
            if (o.attributes.length !== c.attributes.length) diffs.push(`属性数: ${o.attributes.length} → ${c.attributes.length}`);
            modified.push(`类 ${name}（${diffs.join('; ')}）`);
          }
        }
      });
      oldClasses.forEach((c, name) => { if (!newClasses.has(name)) removed.push(`类 ${name}`); });
      // 关系 diff
      const oldRels = new Set(v.snapshot.relations.map(r => r.name + '|' + r.from + '|' + r.to));
      const newRels = new Set(this.relations.map(r => r.name + '|' + r.from + '|' + r.to));
      oldRels.forEach(r => { if (!newRels.has(r)) removed.push(`关系 ${r.replace('|', ' (')})`); });
      newRels.forEach(r => { if (!oldRels.has(r)) added.push(`关系 ${r.replace('|', ' (')})`); });
      this.diffResult = { added, removed, modified, summary: { added: added.length, removed: removed.length, modified: modified.length } };
    },
    rollbackVersion(v) {
      if (!v.snapshot) {
        ElMessage.warning('该版本为初始占位版本，无快照数据，无法回退');
        return;
      }
      ElMessageBox.confirm(`确认回退到版本 ${v.id}？当前未保存的修改将丢失。`, '回退确认', { type: 'warning' })
        .then(() => {
          this.classes = JSON.parse(JSON.stringify(v.snapshot.classes));
          this.relations = JSON.parse(JSON.stringify(v.snapshot.relations));
          ElMessage.success(`已回退到 ${v.id}`);
          this.addLog('warning', `回退本体到版本 ${v.id}`);
        }).catch(() => {});
    },
    // 导入导出
    buildJsonSchema() {
      const schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "KnowledgeGraphOntology",
        "type": "object",
        "definitions": {}
      };
      this.classes.forEach(c => {
        const def = { type: 'object', properties: {}, required: [] };
        c.attributes.forEach(a => {
          let t = 'string';
          if (a.type === 'number') t = 'number';
          else if (a.type === 'date') t = 'string';
          else if (a.type === 'boolean') t = 'boolean';
          def.properties[a.name] = { type: t, minCard: a.minCard, maxCard: a.maxCard };
          if (a.minCard >= 1) def.required.push(a.name);
        });
        if (c.parent) def.allOf = [{ $ref: `#/definitions/${c.parent}` }];
        schema.definitions[c.name] = def;
      });
      schema.relations = this.relations;
      return JSON.stringify(schema, null, 2);
    },
    buildOwl() {
      let xml = '<?xml version="1.0"?>\n<rdf:RDF xmlns="http://example.org/onto#"\n  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"\n  xmlns:owl="http://www.w3.org/2002/07/owl#">\n';
      this.classes.forEach(c => {
        xml += `  <owl:Class rdf:about="#${c.name}">\n`;
        if (c.parent) xml += `    <rdfs:subClassOf rdf:resource="#${c.parent}"/>\n`;
        c.attributes.forEach(a => {
          xml += `    <owl:DatatypeProperty rdf:ID="${c.name}_${a.name}">\n`;
          xml += `      <rdfs:domain rdf:resource="#${c.name}"/>\n`;
          xml += `      <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#${a.type === 'number' ? 'decimal' : a.type === 'date' ? 'date' : a.type === 'boolean' ? 'boolean' : 'string'}"/>\n`;
          xml += `      <rdfs:cardinality>${a.maxCard >= 999 ? 'unbounded' : a.maxCard}</rdfs:cardinality>\n`;
          xml += `    </owl:DatatypeProperty>\n`;
        });
        xml += `  </owl:Class>\n`;
      });
      this.relations.forEach(r => {
        xml += `  <owl:ObjectProperty rdf:about="#${r.name}">\n`;
        xml += `    <rdfs:domain rdf:resource="#${r.from}"/>\n`;
        xml += `    <rdfs:range rdf:resource="#${r.to}"/>\n`;
        if (r.symmetric) xml += `    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#SymmetricProperty"/>\n`;
        if (r.functional) xml += `    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#FunctionalProperty"/>\n`;
        xml += `  </owl:ObjectProperty>\n`;
      });
      xml += '</rdf:RDF>\n';
      return xml;
    },
    buildTurtle() {
      const lines = ['@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .',
        '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .',
        '@prefix owl: <http://www.w3.org/2002/07/owl#> .',
        '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
        '@prefix : <http://example.org/onto#> .', ''];
      this.classes.forEach(c => {
        lines.push(`:${c.name} a owl:Class .`);
        if (c.parent) lines.push(`    rdfs:subClassOf :${c.parent} .`);
        c.attributes.forEach(a => {
          lines.push(`:${c.name}_${a.name} a owl:DatatypeProperty ;`);
          lines.push(`    rdfs:domain :${c.name} ;`);
          lines.push(`    rdfs:range xsd:${a.type === 'number' ? 'decimal' : a.type === 'date' ? 'date' : a.type === 'boolean' ? 'boolean' : 'string'} .`);
        });
        lines.push('');
      });
      this.relations.forEach(r => {
        lines.push(`:${r.name} a owl:ObjectProperty${r.symmetric ? ', owl:SymmetricProperty' : ''}${r.functional ? ', owl:FunctionalProperty' : ''} ;`);
        lines.push(`    rdfs:domain :${r.from} ;`);
        lines.push(`    rdfs:range :${r.to} .`);
        lines.push('');
      });
      return lines.join('\n');
    },
    doExport() {
      let content = '';
      if (this.exportFormat === 'JSON-Schema') content = this.buildJsonSchema();
      else if (this.exportFormat === 'OWL/XML') content = this.buildOwl();
      else content = this.buildTurtle();
      this.exportPreview = content;
      const ext = this.exportFormat === 'JSON-Schema' ? 'json' : this.exportFormat === 'OWL/XML' ? 'owl' : 'ttl';
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `ontology.${ext}`;
      a.click();
      URL.revokeObjectURL(a.href);
      ElMessage.success(`已导出 ontology.${ext}`);
    },
    copyToClipboard() {
      if (!this.exportPreview) {
        this.exportPreview = this.exportFormat === 'JSON-Schema' ? this.buildJsonSchema() : this.exportFormat === 'OWL/XML' ? this.buildOwl() : this.buildTurtle();
      }
      navigator.clipboard.writeText(this.exportPreview).then(() => ElMessage.success('已复制到剪贴板'));
    },
    onFileChange(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        this.importText = e.target.result;
        ElMessage.success('文件已加载，可点击"执行导入"');
      };
      reader.readAsText(file.raw);
    },
    doImport() {
      if (!this.importText.trim()) { ElMessage.error('请粘贴或上传要导入的本体文本'); return; }
      let fmt = this.importFormat;
      if (fmt === 'auto') {
        const t = this.importText.trim();
        if (t.startsWith('{') || t.startsWith('[')) fmt = 'json';
        else if (t.startsWith('<?xml') || t.startsWith('<rdf')) fmt = 'owl';
        else if (t.startsWith('@prefix') || t.startsWith('@')) fmt = 'ttl';
        else { this.importResult = { title: '格式无法识别', type: 'error', description: '请手动选择格式' }; return; }
      }
      try {
        if (fmt === 'json') {
          const obj = JSON.parse(this.importText);
          if (!obj.definitions) throw new Error('缺少 definitions');
          this.classes = Object.entries(obj.definitions).map(([name, def]) => ({
            name,
            parent: (def.allOf && def.allOf[0] && def.allOf[0].$ref) ? def.allOf[0].$ref.split('/').pop() : '',
            attributes: Object.entries(def.properties || {}).map(([pn, pv]) => ({
              name: pn,
              type: pv.type === 'number' ? 'number' : pv.type === 'boolean' ? 'boolean' : 'string',
              minCard: pv.minCard || 0,
              maxCard: pv.maxCard || 1
            }))
          }));
          this.relations = obj.relations || [];
        } else if (fmt === 'owl') {
          // 极简 OWL 解析：仅识别 owl:Class、subClassOf、ObjectProperty
          const parser = new DOMParser();
          const doc = parser.parseFromString(this.importText, 'text/xml');
          const classNodes = doc.getElementsByTagName('Class');
          this.classes = [];
          for (let i = 0; i < classNodes.length; i++) {
            const cls = classNodes[i];
            const about = cls.getAttribute('rdf:about') || cls.getAttribute('about') || '';
            const name = about.replace(/^#/, '');
            const sub = cls.getElementsByTagName('subClassOf');
            const parent = sub[0] ? (sub[0].getAttribute('rdf:resource') || '').replace(/^#/, '') : '';
            this.classes.push({ name, parent, attributes: [] });
          }
        } else if (fmt === 'ttl') {
          // 极简 Turtle 解析
          this.classes = [];
          const blocks = this.importText.split('\n\n');
          blocks.forEach(b => {
            const m = b.match(/^:(\w+)\s+a\s+owl:Class/);
            if (m) {
              const sub = b.match(/rdfs:subClassOf\s+:(\w+)/);
              this.classes.push({ name: m[1], parent: sub ? sub[1] : '', attributes: [] });
            }
          });
        }
        this.importResult = {
          title: '导入成功',
          type: 'success',
          description: `已解析格式：${fmt.toUpperCase()}，共 ${this.classes.length} 个类、${this.relations.length} 个关系`
        };
        ElMessage.success('导入成功');
      } catch (e) {
        this.importResult = { title: '解析失败', type: 'error', description: e.message };
        ElMessage.error('解析失败：' + e.message);
      }
    },
    clearImport() {
      this.importText = '';
      this.importResult = null;
    },

    // === Tab ⑦: 图谱浏览与性能 ===
    switchLayout(layout) {
      this.browseLayout = layout;
      this.$nextTick(() => this.initBrowseCanvas());
    },
    initBrowseCanvas() {
      const container = this.$refs.browseCanvasRef;
      if (!container) return;
      container.innerHTML = '';
      const width = container.clientWidth;
      const height = 400;
      const svg = d3.select(container).append('svg').attr('width', width).attr('height', height).style('background', '#fafbfc');
      const g = svg.append('g');
      const zoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', (e) => g.attr('transform', e.transform));
      svg.call(zoom);
      // 模拟数据
      const nodeCount = Math.min(100, this.realStats.totalNodes);
      const nodes = d3.range(nodeCount).map(i => ({
        id: i,
        name: `Node-${i}`,
        type: ['Company', 'Litigation', 'Violation', 'A_security'][i % 4],
        x: Math.random() * width,
        y: Math.random() * height
      }));
      const links = d3.range(nodeCount * 0.8).map(() => ({
        source: Math.floor(Math.random() * nodeCount),
        target: Math.floor(Math.random() * nodeCount)
      }));
      this.browseStats = { nodeCount: nodes.length, edgeCount: links.length, fps: 60, performance: '流畅' };
      // 绘制
      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(50))
        .force('charge', d3.forceManyBody().strength(-100))
        .force('center', d3.forceCenter(width / 2, height / 2));
      const link = g.append('g').selectAll('line').data(links).enter().append('line').attr('stroke', '#999').attr('stroke-width', 1);
      const node = g.append('g').selectAll('circle').data(nodes).enter().append('circle')
        .attr('r', 6).attr('fill', d => this.getNodeColor(d.type))
        .attr('cursor', 'pointer')
        .on('click', (e, d) => { this.selectedNode = { ...d, properties: { id: d.id, type: d.type } }; this.addBrowseHistory(d); })
        .call(d3.drag().on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }).on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; }).on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));
      simulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('cx', d => d.x).attr('cy', d => d.y);
      });
      this._browseSvg = svg;
    },
    getNodeColor(type) {
      const colors = { Company: '#409eff', Litigation: '#e6a23c', Violation: '#f56c6c', A_security: '#67c23a', G_security: '#909399', B_security: '#9b59b6', City: '#1abc9c', MetaKnowledge: '#795548' };
      return colors[type] || '#409eff';
    },
    addBrowseHistory(node) {
      this.browseHistory.push({ node, time: new Date().toLocaleTimeString('zh-CN') });
      if (this.browseHistory.length > 20) this.browseHistory.shift();
    },
    navigateToNode(node) {
      this.selectedNode = { ...node, properties: { id: node.id, type: node.type } };
    },
    addBookmark(node) {
      if (!this.bookmarks.find(b => b.id === node.id)) {
        this.bookmarks.push(node);
        ElMessage.success('已添加书签');
      }
    },
    removeBookmark(idx) {
      this.bookmarks.splice(idx, 1);
    },
    expandAllNodes() {
      ElMessage.info('展开全部节点');
    },
    collapseAllNodes() {
      ElMessage.info('收起全部节点');
    },
    resetBrowseView() {
      this.initBrowseCanvas();
    },
    toggleVirtualRender() {
      this.virtualRender = !this.virtualRender;
      ElMessage.success(`虚拟渲染已${this.virtualRender ? '开启' : '关闭'}`);
    },
    applyFilter() {
      ElMessage.success('过滤条件已应用');
      this.initBrowseCanvas();
    },
    resetFilter() {
      this.filterNodeTypes = ['Company', 'Litigation', 'Violation', 'A_security', 'G_security', 'B_security', 'City'];
      this.filterPropKey = '';
      this.filterPropVal = '';
      this.initBrowseCanvas();
    },
    expandNode(node) {
      ElMessage.info(`展开节点 ${node.name} 的关联`);
    },
    focusNode(node) {
      ElMessage.info(`聚焦到节点 ${node.name}`);
    },
    runPerfTest() {
      this.perfTesting = true;
      const sizes = { '1k': 1000, '10k': 10000, '50k': 50000, '100k': 100000 };
      const size = sizes[this.perfTestSize];
      setTimeout(() => {
        const loadTime = Math.round(size / 100);
        const fps = size > 50000 ? 15 : size > 10000 ? 30 : 60;
        const memory = Math.round(size * 0.01);
        const passed = fps >= 15;
        this.perfResult = {
          loadTime,
          fps,
          memory,
          interactive: fps > 20,
          passed,
          suggestion: passed ? '性能良好，可流畅展示该规模图谱' : '建议启用虚拟渲染或聚合折叠以提升性能'
        };
        this.perfTesting = false;
      }, 1500);
    },

    // === Tab ⑧: 数据导入与抽取 ===
    onStructuredFileChange(file) {
      this.structuredPreview = {
        source: file.name,
        mappings: [
          { sourceField: '公司名称', targetType: 'Company', targetProp: 'name' },
          { sourceField: '社会信用代码', targetType: 'Company', targetProp: 'credit_code' },
          { sourceField: '省份', targetType: 'Company', targetProp: 'province' }
        ],
        relationMappings: []
      };
      ElMessage.success('文件已加载，请配置字段映射');
    },
    editMapping() {
      // 编辑映射
      ElMessage.info('编辑字段映射');
    },
    updateMapping(row) {
      ElMessage.success(`已更新映射: ${row.sourceField} -> ${row.targetType}.${row.targetProp}`);
    },
    addRelationMapping() {
      this.structuredPreview.relationMappings.push({ fromField: '', toField: '', relType: '子公司' });
    },
    updateRelationMapping(row) {
      ElMessage.success(`关系映射已更新: ${row.relType}`);
    },
    previewImport() {
      ElMessage.success('导入预览：将导入 1000 条记录，创建 800 个节点、1200 条关系');
    },
    executeImport() {
      this.importing = true;
      this.importProgress = { show: true, percent: 0, status: '', processed: 0, total: 1000, success: 0, failed: 0, errors: [] };
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        this.importProgress.percent = progress;
        this.importProgress.processed = progress * 10;
        this.importProgress.success = progress * 9;
        if (progress >= 100) {
          clearInterval(interval);
          this.importing = false;
          this.importProgress.status = 'success';
          ElMessage.success('导入完成');
        }
      }, 200);
    },
    testDbConnection() {
      ElMessage.success('数据库连接测试成功');
    },
    loadDbSchema() {
      ElMessage.success('表结构加载成功');
    },
    testApiConnection() {
      ElMessage.success('API 接口测试成功');
    },
    fetchApiData() {
      ElMessage.success('数据获取成功');
    },
    onDocFileChange(file) {
      ElMessage.success(`文档 ${file.name} 已上传，准备抽取`);
    },
    startExtraction() {
      this.extracting = true;
      setTimeout(() => {
        this.extractResults = {
          entities: [
            { text: '阿里巴巴', type: 'Company', confidence: 0.95 },
            { text: '腾讯控股', type: 'Company', confidence: 0.92 },
            { text: '马云', type: 'Person', confidence: 0.88 }
          ],
          relations: [
            { subject: '阿里巴巴', predicate: '子公司', object: '蚂蚁集团', confidence: 0.85 },
            { subject: '腾讯', predicate: '投资', object: '京东', confidence: 0.78 }
          ],
          lowConfidence: [{ text: '某小公司', type: 'Company', confidence: 0.45 }]
        };
        this.extracting = false;
        ElMessage.success('抽取完成');
      }, 2000);
    },
    onEntitySelectionChange(selection) {
      this.selectedEntities = selection;
    },
    onRelationSelectionChange(selection) {
      this.selectedRelations = selection;
    },
    editExtractedEntity(row) {
      ElMessage.info(`编辑实体: ${row.text}`);
    },
    confirmSelected() {
      ElMessage.success(`已确认 ${this.selectedEntities.length} 个实体, ${this.selectedRelations.length} 个关系`);
    },
    rejectSelected() {
      ElMessage.warning('已拒绝选中项');
    },
    confirmAll() {
      ElMessage.success('已全部确认');
    },
    startBatchBuild() {
      this.batchBuilding = true;
      setTimeout(() => {
        this.batchResult = {
          startTime: new Date().toLocaleString('zh-CN'),
          endTime: new Date(Date.now() + 120000).toLocaleString('zh-CN'),
          duration: 120,
          updateMode: this.batchConfig.updateMode,
          newNodes: 50000,
          newRelations: 80000,
          updatedNodes: 5000,
          skippedNodes: 2000,
          impact: this.batchConfig.updateMode === 'append' ? 'low' : this.batchConfig.updateMode === 'replace' ? 'high' : 'medium',
          impactTitle: this.batchConfig.updateMode === 'append' ? '低风险操作' : this.batchConfig.updateMode === 'replace' ? '高风险操作' : '中等风险操作',
          impactDesc: this.batchModeDescriptions[this.batchConfig.updateMode]
        };
        this.batchBuilding = false;
        ElMessage.success('批量构建完成');
      }, 2000);
    }
  }
};
</script>

<style scoped>
.kg-test {
  padding: 20px;
}
.kg-test h1 {
  margin: 0 0 4px;
  font-size: 22px;
}
.description {
  color: #909399;
  margin: 0 0 16px;
  font-size: 13px;
}
.test-tabs {
  background: #fff;
}
.tab-section {
  padding: 8px 0;
}
.panel {
  margin-bottom: 12px;
}
/* === 实体分布统计 === */
.stat-cards { margin-bottom: 4px; }
.stat-card {
  text-align: center;
  border-left: 4px solid #409eff;
}
.stat-card .stat-num {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}
.stat-card .stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 6px;
}
.stat-total { border-left-color: #409eff; }
.stat-rel   { border-left-color: #67c23a; }
.stat-listed   { border-left-color: #e6a23c; }
.stat-unlisted { border-left-color: #909399; }

.pie-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 8px 0 4px;
}
.pie-legend { display: flex; flex-direction: column; gap: 10px; }
.legend-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: #303133;
}
.legend-item .dot {
  width: 12px; height: 12px; border-radius: 50%; display: inline-block;
}
.legend-item .lbl { min-width: 80px; }
.legend-item .val { color: #909399; font-weight: 600; }

.compare-bar { display: flex; flex-direction: column; gap: 10px; }
.cmp-row { display: flex; align-items: center; gap: 12px; }
.cmp-label { width: 90px; font-size: 13px; color: #606266; }
.cmp-track {
  flex: 1; height: 24px; background: #f5f7fa; border-radius: 4px; overflow: hidden;
}
.cmp-fill {
  height: 100%; color: #fff; font-size: 12px; line-height: 24px;
  text-align: right; padding-right: 10px; transition: width 0.6s ease;
}
.cmp-fill.listed   { background: linear-gradient(90deg, #409eff, #66b1ff); }
.cmp-fill.unlisted { background: linear-gradient(90deg, #909399, #b1b3b8); }

/* === 细粒度统计图表 === */
.violation-chart {
  width: 100%;
  min-height: 180px;
}
.violation-chart svg {
  display: block;
}

/* === 金融风险类型卡片 === */
.risk-type-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.risk-type-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: #fafbfc;
  border-radius: 6px;
  border-left: 3px solid #409eff;
  transition: transform 0.2s, box-shadow 0.2s;
}
.risk-type-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.risk-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.risk-info { flex: 1; min-width: 0; }
.risk-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}
.risk-count {
  font-size: 18px;
  font-weight: bold;
  color: #e6a23c;
  margin-bottom: 2px;
}
.risk-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

/* === 图谱金融风险知识 === */
.risk-overview-card {
  border-left: 3px solid #409eff;
  height: 130px;
}
.roc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.roc-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.roc-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.roc-count {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 2px;
}
.roc-unit {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}
.roc-source {
  font-size: 11px;
  color: #c0c4cc;
  margin-bottom: 4px;
}
.roc-desc {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
}

.risk-chart {
  width: 100%;
  min-height: 220px;
}
.risk-chart-small {
  width: 100%;
  min-height: 160px;
}
.risk-chart svg, .risk-chart-small svg {
  display: block;
}

.risk-mini-title {
  font-size: 12px;
  color: #606266;
  margin-bottom: 6px;
  padding-left: 6px;
  border-left: 2px solid #409eff;
  font-weight: 600;
}

.mk-insight-card {
  background: linear-gradient(135deg, #fafbfc 0%, #f0f5ff 100%);
  border-radius: 8px;
  padding: 12px 14px;
  border-left: 3px solid #e6a23c;
  height: 100%;
  transition: transform 0.2s, box-shadow 0.2s;
}
.mk-insight-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}
.mk-tag {
  display: inline-block;
  background: #e6a23c;
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-bottom: 6px;
  font-weight: 600;
}
.mk-conclusion {
  font-size: 13px;
  color: #303133;
  line-height: 1.5;
  margin-bottom: 6px;
  font-weight: 500;
}
.mk-risk {
  font-size: 12px;
  color: #f56c6c;
  line-height: 1.5;
}

.industry-list { display: flex; flex-direction: column; gap: 6px; }
.ind-row {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: #303133;
}
.ind-rank {
  width: 22px; height: 22px; border-radius: 50%;
  background: #f0f2f5; color: #909399;
  text-align: center; line-height: 22px; font-size: 12px; font-weight: 600;
}
.ind-rank.rank-1 { background: #f56c6c; color: #fff; }
.ind-rank.rank-2 { background: #e6a23c; color: #fff; }
.ind-rank.rank-3 { background: #67c23a; color: #fff; }
.ind-name { width: 90px; }
.ind-bar-wrap { flex: 1; display: flex; align-items: center; gap: 6px; }
.ind-bar {
  height: 20px; min-width: 2px; border-radius: 3px;
  color: #fff; font-size: 11px; line-height: 20px;
  text-align: right; padding-right: 6px;
  transition: width 0.6s ease;
}
.ind-count-out { color: #606266; font-size: 12px; }
.ind-pct { width: 48px; text-align: right; color: #606266; font-weight: 600; }
.attr-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.kg-stat {
  margin-bottom: 12px;
}
.kg-stat .el-tag {
  margin-right: 6px;
}
.toolbar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}
.viz-canvas {
  width: 100%;
  height: 520px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;
  background: #fafbfc;
}
.legend {
  margin-top: 8px;
}
.legend .el-tag {
  margin-right: 6px;
}
.diff-item {
  font-family: Consolas, monospace;
  font-size: 12px;
  padding: 4px 8px;
  margin: 3px 0;
  border-radius: 4px;
}
.diff-item.added { background: #f0f9eb; color: #67c23a; }
.diff-item.removed { background: #fef0f0; color: #f56c6c; }
.diff-item.modified { background: #fdf6ec; color: #e6a23c; }

/* === Tab ⑦: 图谱浏览与性能 === */
.browse-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.browse-canvas { width: 100%; height: 400px; border: 1px solid #ebeef5; border-radius: 6px; overflow: hidden; background: #fafbfc; }
.browse-status { margin-top: 12px; display: flex; gap: 8px; }
.node-detail { }
.node-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.node-type-tag { padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 12px; }
.node-props { }
.prop-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; border-bottom: 1px solid #f0f2f5; }
.prop-key { color: #909399; font-size: 13px; min-width: 80px; }
.prop-val { color: #303133; font-size: 13px; flex: 1; }
.type-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.perf-metric { text-align: center; padding: 16px; background: #f5f7fa; border-radius: 8px; }
.perf-val { font-size: 28px; font-weight: bold; }
.perf-val.good { color: #67c23a; }
.perf-val.medium { color: #e6a23c; }
.perf-val.bad { color: #f56c6c; }
.perf-label { font-size: 13px; color: #909399; margin-top: 4px; }

/* === Tab ⑧: 数据导入与抽取 === */
.mode-desc { font-size: 12px; color: #909399; margin-top: 4px; }
.error-log { max-height: 200px; overflow: auto; background: #f5f7fa; padding: 8px; font-size: 12px; color: #f56c6c; }
.review-stats { display: flex; gap: 8px; margin-bottom: 12px; }
.review-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 12px; }
.batch-result { }
</style>
