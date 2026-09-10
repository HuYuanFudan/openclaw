<template>
  <div class="meta-library">
    <!-- 总览统计 -->
    <el-card shadow="never" class="stat-card">
      <template #header>
        <div class="card-header">
          <span>元知识库总览</span>
          <el-tag size="small" type="info">来源：《经济研究》期刊论文</el-tag>
        </div>
      </template>
      <el-row :gutter="16" v-if="stats">
        <el-col :span="5">
          <div class="stat-item">
            <div class="stat-num">{{ stats.paper_count }}</div>
            <div class="stat-label">论文总数</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="stat-item">
            <div class="stat-num">{{ stats.papers_with_meta }}</div>
            <div class="stat-label">含元知识的论文</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="stat-item">
            <div class="stat-num">{{ stats.meta_total }}</div>
            <div class="stat-label">元知识总条目</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-num">{{ stats.avg_per_paper }}</div>
            <div class="stat-label">平均每篇条数</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="stat-item">
            <div class="stat-num">{{ stats.max_per_paper }}</div>
            <div class="stat-label">单篇最多条数</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 字段统计 -->
    <el-card shadow="never" class="stat-card" v-if="stats">
      <template #header>
        <div class="card-header"><span>字段统计</span></div>
      </template>
      <el-table :data="stats.field_stats" size="small" border>
        <el-table-column prop="field" label="字段" width="140" />
        <el-table-column prop="empty" label="为空条数" width="100" />
        <el-table-column label="非空平均长度（字）">
          <template #default="{ row }">{{ row.avg_len }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 元知识列表 -->
    <el-card shadow="never" class="stat-card">
      <template #header>
        <div class="card-header">
          <span>元知识条目（共 {{ total }} 条）</span>
          <div class="search-area">
            <el-input v-model="keyword" placeholder="搜索结论/证据/论文等" clearable size="small" style="width: 220px"
              @keyup.enter="fetchList(1)" @clear="fetchList(1)" />
            <el-button type="primary" size="small" @click="fetchList(1)">搜索</el-button>
          </div>
        </div>
      </template>
      <el-table :data="items" v-loading="loading" size="small" border>
        <!-- 展开详情功能暂不开放，留作后续汇报展示
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-detail">
            <p><span class="detail-label">前提条件：</span>{{ row['前提条件'] }}</p>
            <p><span class="detail-label">关键证据：</span>{{ row['关键证据'] || '—' }}</p>
            <p><span class="detail-label">风险指导价值：</span>{{ row['风险指导价值'] }}</p>
            <p><span class="detail-label">相关事件：</span>{{ row['相关事件'] || '—' }}</p>
            <p><span class="detail-label">来源论文：</span>{{ row.file_name }}</p>
          </div>
        </template>
      </el-table-column>
      -->
        <el-table-column type="index" label="#" width="60" :index="indexOffset" />
        <el-table-column prop="核心结论" label="元知识" min-width="320" show-overflow-tooltip />
        <el-table-column prop="file_name" label="来源论文" min-width="220" show-overflow-tooltip />
      </el-table>
      <el-pagination class="pager" layout="total, prev, pager, next, sizes" :total="total" :current-page="page"
        :page-size="pageSize" :page-sizes="[10, 20, 50, 100]" @current-change="p => fetchList(p)"
        @size-change="s => { pageSize = s; fetchList(1) }" />
    </el-card>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'MetaKnowledgeLibrary',
  data() {
    return {
      stats: null,
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      keyword: '',
      loading: false,
    };
  },
  computed: {
    indexOffset() {
      return (this.page - 1) * this.pageSize + 1;
    },
  },
  mounted() {
    this.fetchList(1);
  },
  methods: {
    async fetchList(page) {
      this.loading = true;
      this.page = page || 1;
      try {
        const resp = await axios.get('/api/metaknowledge_library/', {
          params: { page: this.page, page_size: this.pageSize, keyword: this.keyword },
          timeout: 30000,
        });
        const d = resp.data;
        if (d.status === 'success') {
          this.stats = d.stats;
          this.items = d.items;
          this.total = d.total;
        }
      } catch (err) {
        this.$message.error('元知识库数据加载失败');
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.meta-library {
  padding: 16px;
}

.stat-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.search-area {
  display: flex;
  gap: 8px;
  align-items: center;
}

.stat-item {
  text-align: center;
  padding: 8px 0;
  background: #f5f7fa;
  border-radius: 6px;
}

.stat-num {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.expand-detail {
  padding: 8px 24px;
}

.expand-detail p {
  margin: 6px 0;
  line-height: 1.7;
}

.detail-label {
  font-weight: bold;
  color: #409eff;
}

.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
