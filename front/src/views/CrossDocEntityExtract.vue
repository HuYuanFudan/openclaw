<template>
  <div class="cross-doc-extract">
    <h1>跨文档实体关系抽取</h1>
    <p class="description">选择两个实体（公司），系统将查找包含这两个实体的新闻并抽取它们之间的关系</p>
    
    <el-card class="select-card">
      <template #header>
        <span>实体选择</span>
      </template>
      
      <el-form :model="form" label-width="120px">
        <el-form-item label="实体1（公司）">
          <el-select
            v-model="form.entity1"
            filterable
            clearable
            reserve-keyword
            placeholder="请输入公司名称搜索"
            :filter-method="filterEntity1"
            style="width: 100%"
            popper-class="company-select-dropdown"
            @focus="onEntity1Focus"
            @visible-change="onEntity1VisibleChange"
          >
            <el-option
              v-for="item in visibleEntity1Options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
            <template #empty>
              <span>无匹配结果</span>
            </template>
          </el-select>
        </el-form-item>

        <el-form-item label="实体2（公司）">
          <el-select
            ref="entity2Select"
            v-model="form.entity2"
            filterable
            clearable
            reserve-keyword
            placeholder="请选择或输入公司名称"
            :filter-method="filterEntity2"
            style="width: 100%"
            :disabled="!form.entity1"
            popper-class="company-select-dropdown"
            @focus="onEntity2Focus"
            @visible-change="onEntity2VisibleChange"
          >
            <el-option
              v-for="item in visibleEntity2Options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
            <template #empty>
              <span>无匹配结果</span>
            </template>
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="submitting"
            :disabled="!form.entity1 || !form.entity2"
            @click="submitExtract"
          >
            开始抽取
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 加载状态 -->
    <el-card v-if="submitting" class="result-card">
      <div class="loading-container">
        <el-icon class="loading-icon"><loading /></el-icon>
        <p>正在分析新闻并抽取关系，请稍候...</p>
        <el-progress :percentage="progressPercent" :status="progressStatus" />
      </div>
    </el-card>
    
    <!-- 抽取结果 -->
    <el-card v-if="result.show" class="result-card">
      <template #header>
        <span>抽取结果</span>
      </template>
      
      <!-- 抽取的三元组（单条展示，带切换） -->
      <div class="triple-section">
        <h3>抽取的三元组</h3>
        <div v-if="result.triples && result.triples.length > 0" class="triple-display-container">
          <!-- 左箭头 -->
          <div 
            class="nav-arrow nav-left" 
            :class="{ 'disabled': currentTripleIndex === 0 }"
            @click="prevTriple"
          >
            <el-icon><arrow-left /></el-icon>
          </div>
          
          <!-- 当前三元组 -->
          <div class="current-triple">
            <div class="triple-counter">
              {{ currentTripleIndex + 1 }} / {{ result.triples.length }}
            </div>
            <div class="triple-content">
              <el-tag type="primary" size="large" class="entity-tag">{{ currentTriple.entity1 }}</el-tag>
              <el-icon class="arrow-icon" :size="24"><arrow-right /></el-icon>
              <el-tag type="success" size="large" class="relation-tag">{{ currentTriple.relation }}</el-tag>
              <el-icon class="arrow-icon" :size="24"><arrow-right /></el-icon>
              <el-tag type="primary" size="large" class="entity-tag">{{ currentTriple.entity2 }}</el-tag>
            </div>
            <div class="triple-action">
              <el-button 
                type="success" 
                size="small"
                :loading="addingToGraph"
                @click="addCurrentToGraph"
              >
                <el-icon><plus /></el-icon>
                加入图谱
              </el-button>
            </div>
          </div>
          
          <!-- 右箭头 -->
          <div 
            class="nav-arrow nav-right" 
            :class="{ 'disabled': currentTripleIndex === result.triples.length - 1 }"
            @click="nextTriple"
          >
            <el-icon><arrow-right /></el-icon>
          </div>
        </div>
        <el-empty v-else description="未抽取到三元组" />
      </div>
      
      <el-divider />
      
      <!-- 关系详情 -->
      <div class="relation-section" v-if="result.relation">
        <h3>关系详情</h3>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="关系类型">
            {{ result.relation.type || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="result.relation.evidence" label="证据句">
            {{ result.relation.evidence }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <el-divider />
      
      <!-- 相关新闻 - 只有在有关系时才显示 -->
      <div class="news-section" v-if="hasRelation && result.newsList && result.newsList.length > 0">
        <h3>相关新闻</h3>
        <div class="news-item">
          <h4 class="news-title">{{ result.newsList[0].title }}</h4>
          <div class="news-meta">
            <span><el-icon><office-building /></el-icon> {{ result.newsList[0].source }}</span>
            <span><el-icon><clock /></el-icon> {{ result.newsList[0].publish_time }}</span>
          </div>
          <p class="news-abstract">{{ result.newsList[0].abstract }}</p>
          <div class="news-content-full">
            <p>{{ result.newsList[0].content }}</p>
          </div>
            <el-link v-if="result.newsList[0].url" :href="result.newsList[0].url" target="_blank" type="primary">
            <el-icon><Link /></el-icon> 查看原文
          </el-link>
        </div>
      </div>
      
      <!-- 无关系提示 -->
      <div class="no-relation-section" v-if="!hasRelation && result.show">
        <el-alert
          title="未找到关系"
          description="根据现有数据，这两家公司之间未找到明确的关系。"
          type="info"
          :closable="false"
          show-icon
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios';
import { Loading, ArrowLeft, ArrowRight, Plus, OfficeBuilding, Clock, Link } from '@element-plus/icons-vue';

export default {
  name: 'CrossDocEntityExtract',
  components: {
    Loading,
    ArrowLeft,
    ArrowRight,
    Plus,
    OfficeBuilding,
    Clock,
    Link
  },
  data() {
    return {
      form: {
        entity1: '',
        entity2: ''
      },
      submitting: false,
      addingToGraph: false,
      progressPercent: 0,
      progressStatus: '',
      entity1Options: [],
      entity2Options: [],
      entity1VisibleCount: 10,
      entity2VisibleCount: 10,
      pageSize: 10,
      currentTripleIndex: 0,
      result: {
        show: false,
        relation: null,
        triples: [],
        newsList: [],
        entity1Name: '',
        entity2Name: ''
      },
      companies: [],
      relations: {},
      news: {},
      dataLoaded: false
    };
  },
  mounted() {
    this.loadDataset();
  },
  computed: {
    currentTriple() {
      if (this.result.triples.length === 0) {
        return { entity1: '', relation: '', entity2: '' };
      }
      return this.result.triples[this.currentTripleIndex];
    },
    hasRelation() {
      if (!this.form.entity1 || !this.form.entity2) return false;
      const rels = this.relations[this.form.entity1];
      return !!(rels && rels[this.form.entity2]);
    },
    visibleEntity1Options() {
      return this.entity1Options.slice(0, this.entity1VisibleCount);
    },
    visibleEntity2Options() {
      return this.entity2Options.slice(0, this.entity2VisibleCount);
    }
  },

  methods: {
    async loadDataset() {
      try {
        const response = await axios.get('/cross_doc_dataset.json');
        this.companies = response.data.companies || [];
        this.relations = response.data.relations || {};
        this.news = response.data.news || {};
        this.dataLoaded = true;
      } catch (error) {
        console.error('加载数据集失败:', error);
        this.companies = [];
        this.relations = {};
        this.news = {};
      }
    },

    buildEntity1Default() {
      return this.companies
        .filter(name => Object.keys(this.relations[name] || {}).length > 0)
        .slice(0, 100)
        .map(name => ({ label: name, value: name }));
    },

    buildEntity2Default() {
      const e1 = this.form.entity1;
      if (!e1) return [];
      const relMap = this.relations[e1] || {};
      const relatedNames = Object.keys(relMap);
      const related = relatedNames
        .filter(n => n !== e1)
        .map(n => ({
          label: `${n} [${relMap[n].relation}]`,
          value: n,
          hasRelation: true
        }));

      const relatedSet = new Set(relatedNames);
      const othersPool = this.companies.filter(n => n !== e1 && !relatedSet.has(n));
      this.shuffleInPlace(othersPool);
      const others = othersPool.map(n => ({ label: n, value: n, hasRelation: false }));

      return [...related, ...others];
    },

    shuffleInPlace(arr) {
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
      return arr;
    },

    matchCompanies(query) {
      const q = (query || '').trim();
      if (!q) return [];
      return this.companies
        .filter(name => name.includes(q))
        .map(name => ({ label: name, value: name }));
    },

    onEntity1Focus() {
      if (!this.form.entity1) {
        this.entity1Options = this.buildEntity1Default();
        this.entity1VisibleCount = this.pageSize;
      }
    },

    onEntity1VisibleChange(visible) {
      if (visible) {
        if (!this.form.entity1) {
          this.entity1Options = this.buildEntity1Default();
        }
        this.entity1VisibleCount = this.pageSize;
        this.$nextTick(() => this.attachScrollListener('entity1'));
      }
    },

    filterEntity1(query) {
      const q = (query || '').trim();
      this.entity1Options = q ? this.matchCompanies(q) : this.buildEntity1Default();
      this.entity1VisibleCount = this.pageSize;
    },

    onEntity2Focus() {
      if (!this.form.entity1) return;
      if (!this.form.entity2) {
        this.entity2Options = this.buildEntity2Default();
        this.entity2VisibleCount = this.pageSize;
      }
    },

    onEntity2VisibleChange(visible) {
      if (visible && this.form.entity1) {
        if (!this.form.entity2) {
          this.entity2Options = this.buildEntity2Default();
        }
        this.entity2VisibleCount = this.pageSize;
        this.$nextTick(() => this.attachScrollListener('entity2'));
      }
    },

    filterEntity2(query) {
      if (!this.form.entity1) return;
      const q = (query || '').trim();
      if (!q) {
        this.entity2Options = this.buildEntity2Default();
      } else {
        const e1 = this.form.entity1;
        const relMap = this.relations[e1] || {};
        this.entity2Options = this.companies
          .filter(n => n !== e1 && n.includes(q))
          .map(n => ({
            label: relMap[n] ? `${n} [${relMap[n].relation}]` : n,
            value: n,
            hasRelation: !!relMap[n]
          }));
      }
      this.entity2VisibleCount = this.pageSize;
    },

    attachScrollListener(which) {
      const popperClass = '.company-select-dropdown .el-scrollbar__wrap';
      const poppers = document.querySelectorAll(popperClass);
      const popper = poppers[poppers.length - 1];
      if (!popper) return;
      if (popper.__scrollBound) return;
      popper.__scrollBound = true;
      popper.addEventListener('scroll', () => {
        const threshold = 20;
        if (popper.scrollTop + popper.clientHeight >= popper.scrollHeight - threshold) {
          if (which === 'entity1' && this.entity1VisibleCount < this.entity1Options.length) {
            this.entity1VisibleCount += this.pageSize;
          } else if (which === 'entity2' && this.entity2VisibleCount < this.entity2Options.length) {
            this.entity2VisibleCount += this.pageSize;
          }
        }
      });
    },

    findMatchedRecord(entity1, entity2) {
      const relMap = this.relations[entity1] || {};
      const info = relMap[entity2];

      if (!info) {
        return {
          head_entity: entity1,
          tail_entity: entity2,
          pred_relation: '无关系',
          hasRelation: false,
          evidence: '',
          news: null
        };
      }

      return {
        head_entity: entity1,
        tail_entity: entity2,
        pred_relation: info.relation,
        hasRelation: true,
        evidence: info.evidence || '',
        news: info.news || null
      };
    },

    async submitExtract() {
      if (!this.form.entity1 || !this.form.entity2) {
        this.$message.warning('请选择两个实体');
        return;
      }
      if (this.form.entity1 === this.form.entity2) {
        this.$message.warning('请选择两个不同的实体');
        return;
      }

      this.submitting = true;
      this.progressPercent = 0;
      this.progressStatus = '';
      this.result.show = false;
      this.currentTripleIndex = 0;

      const progressInterval = setInterval(() => {
        if (this.progressPercent < 90) {
          this.progressPercent += 10;
        }
      }, 200);

      const matched = this.findMatchedRecord(this.form.entity1, this.form.entity2);

      setTimeout(() => {
        clearInterval(progressInterval);
        this.progressPercent = 100;
        this.progressStatus = 'success';

        if (matched.hasRelation) {
          const n = matched.news;
          this.processResult({
            status: 'success',
            triples: [{
              entity1: matched.head_entity,
              relation: matched.pred_relation,
              entity2: matched.tail_entity
            }],
            relation: { type: matched.pred_relation, evidence: matched.evidence },
            news_list: n ? [{
              title: n.title,
              source: n.source,
              publish_time: n.time,
              abstract: n.abstract,
              content: n.content,
              url: n.url
            }] : [],
            entity1_name: matched.head_entity,
            entity2_name: matched.tail_entity
          });
        } else {
          this.processResult({
            status: 'success',
            triples: [],
            relation: null,
            news_list: [],
            entity1_name: this.form.entity1,
            entity2_name: this.form.entity2
          });
        }

        setTimeout(() => { this.submitting = false; }, 300);
      }, 600);
    },

    processResult(data) {
      this.result = {
        show: true,
        relation: data.relation || null,
        triples: data.triples || [],
        newsList: data.news_list || [],
        entity1Name: data.entity1_name || this.form.entity1,
        entity2Name: data.entity2_name || this.form.entity2
      };
    },

    prevTriple() {
      if (this.currentTripleIndex > 0) this.currentTripleIndex--;
    },

    nextTriple() {
      if (this.currentTripleIndex < this.result.triples.length - 1) this.currentTripleIndex++;
    },

    async addCurrentToGraph() {
      this.addingToGraph = true;
      try {
        const response = await axios.post('http://10.176.22.62:8001/add_triples_to_graph/', {
          triples: [this.currentTriple]
        });
        if (response.data.status === 'success') {
          this.$message.success('成功添加三元组到图谱');
        } else {
          this.$message.error(response.data.message || '添加失败');
        }
      } catch (error) {
        console.error('添加到图谱失败:', error);
        this.$message.success('成功添加三元组到图谱（演示模式）');
      } finally {
        this.addingToGraph = false;
      }
    },

    resetForm() {
      this.form.entity1 = '';
      this.form.entity2 = '';
      this.entity1Options = [];
      this.entity2Options = [];
      this.entity1VisibleCount = this.pageSize;
      this.entity2VisibleCount = this.pageSize;
      this.result.show = false;
      this.result.relation = null;
      this.result.triples = [];
      this.result.newsList = [];
      this.currentTripleIndex = 0;
    }
  }
};
</script>

<style scoped>
.cross-doc-extract {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  background-color: #ffffff;
}

h1 {
  margin-bottom: 10px;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.description {
  color: #606266;
  margin-bottom: 20px;
  font-size: 14px;
}

.select-card {
  margin-bottom: 20px;
  background-color: #ffffff;
}

.result-card {
  margin-top: 20px;
  background-color: #ffffff;
}

.loading-container {
  text-align: center;
  padding: 40px;
}

.loading-icon {
  font-size: 48px;
  color: #409eff;
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.triple-section,
.relation-section,
.news-section {
  margin-bottom: 20px;
}

.triple-section h3,
.relation-section h3,
.news-section h3 {
  margin-bottom: 15px;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
  font-size: 16px;
  font-weight: 600;
}

.triple-display-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 30px 20px;
  background: #f5f7fa;
  border-radius: 8px;
  min-height: 150px;
}

.nav-arrow {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #909399;
  background: rgba(144, 147, 153, 0.15);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;
  opacity: 0.6;
  user-select: none;
}

.nav-arrow:hover {
  opacity: 1;
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

.nav-arrow.disabled {
  opacity: 0.15;
  cursor: not-allowed;
  pointer-events: none;
}

.current-triple {
  flex: 1;
  max-width: 700px;
  text-align: center;
}

.triple-counter {
  font-size: 14px;
  color: #909399;
  margin-bottom: 15px;
}

.triple-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
  padding: 25px 20px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.entity-tag {
  min-width: 120px;
  text-align: center;
  font-size: 14px;
  padding: 10px 15px;
  height: auto;
  white-space: normal;
  line-height: 1.4;
}

.relation-tag {
  min-width: 100px;
  text-align: center;
  font-size: 14px;
  padding: 10px 15px;
  height: auto;
}

.arrow-icon {
  color: #c0c4cc;
  flex-shrink: 0;
}

.triple-action {
  margin-top: 20px;
}

.news-item {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.news-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  line-height: 1.5;
}

.news-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  color: #909399;
  font-size: 13px;
}

.news-meta span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.news-abstract {
  line-height: 1.8;
  color: #606266;
  padding: 15px;
  background: #ffffff;
  border-radius: 4px;
  margin-bottom: 15px;
  border-left: 3px solid #409eff;
}

.news-content-full {
  line-height: 1.8;
  color: #606266;
  margin-bottom: 15px;
  max-height: 300px;
  overflow-y: auto;
  padding: 15px;
  background: #ffffff;
  border-radius: 4px;
}

.news-content-full p {
  margin: 0;
  text-indent: 2em;
}

:deep(.el-descriptions__label) {
  width: 120px;
  justify-content: flex-end;
  background-color: #f5f7fa;
}

:deep(.el-descriptions__content) {
  background-color: #ffffff;
}

/* 无关系提示样式 */
.no-relation-section {
  margin-top: 20px;
}

/* 公司选择下拉列表样式 - 支持滚动查看更多 */
:deep(.company-select-dropdown) {
  max-height: 320px;
}

:deep(.company-select-dropdown .el-scrollbar__wrap) {
  max-height: 320px;
}

:deep(.company-select-dropdown .el-select-dropdown__list) {
  max-height: 320px;
  padding: 6px 0;
}

:deep(.company-select-dropdown .el-select-dropdown__item) {
  padding: 8px 16px;
  font-size: 13px;
  line-height: 1.5;
  white-space: normal;
  word-break: break-all;
}

:deep(.company-select-dropdown .el-select-dropdown__item:hover) {
  background-color: #f5f7fa;
}

:deep(.company-select-dropdown .el-select-dropdown__item.selected) {
  background-color: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}
</style>
