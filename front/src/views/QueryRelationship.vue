<template>
  <div>
    <h1>关系查询</h1>
    
    <!-- 测试功能区域 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>测试工具</span>
          <el-button type="primary" @click="loadTestCases" :loading="loadingTestCases">
            {{ loadingTestCases ? '加载中...' : '加载测试用例' }}
          </el-button>
        </div>
      </template>
      
      <!-- 关系统计信息 -->
      <div v-if="testStats" style="margin-bottom: 20px;">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="关系类型总数">{{ testStats.total_relationship_types }}</el-descriptions-item>
          <el-descriptions-item label="关系总数">{{ testStats.total_relationships }}</el-descriptions-item>
          <el-descriptions-item label="测试用例数">{{ testStats.positive_test_cases?.length || 0 }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- 关系类型分布 -->
        <div style="margin-top: 10px;">
          <strong>关系类型分布：</strong>
          <el-tag v-for="(count, relType) in testStats.relationship_distribution" :key="relType" size="small">
            {{ relType }}: {{ count }}
          </el-tag>
        </div>
      </div>
      
      <!-- 正向测试用例 -->
      <div v-if="positiveTestCases.length > 0">
        <h3>正向测试用例（共{{ positiveTestCases.length }}条）</h3>
        <el-table :data="positiveTestCases" border size="small" style="width: 100%; margin-bottom: 10px;">
          <el-table-column prop="relation_type" label="关系类型" width="120" />
          <el-table-column prop="company1" label="公司1" />
          <el-table-column prop="company2" label="公司2" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" @click="fillTestCase(scope.row)">测试</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 负向测试用例 -->
      <div v-if="negativeTestCases.length > 0">
        <h3>负向测试用例（共{{ negativeTestCases.length }}条）</h3>
        <el-table :data="negativeTestCases" border size="small" style="width: 100%;">
          <el-table-column prop="test_id" label="测试ID" width="100" />
          <el-table-column prop="company1" label="公司1" />
          <el-table-column prop="company2" label="公司2" />
          <el-table-column prop="expected_result" label="预期结果" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" type="danger" @click="fillTestCase(scope.row)">测试</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <div v-if="!loadingTestCases && !testStats" style="text-align: center; color: #999;">
        点击"加载测试用例"按钮获取图谱中的关系统计和测试案例
      </div>
    </el-card>
    
    <!-- 查询表单区域 -->
    <h2>公司1</h2>
    <el-form :model="formCompany1" ref="formRef1" label-width="120px">
      <el-form-item label="公司名称">
        <el-input v-model="formCompany1.company_name" placeholder="请输入公司名称" />
      </el-form-item>
      <el-form-item label="社会信用代码">
        <el-input v-model="formCompany1.credit_number" placeholder="请输入社会信用代码" />
      </el-form-item>
    </el-form>
    
    <h2>公司2</h2>
    <el-form :model="formCompany2" ref="formRef2" label-width="120px">
      <el-form-item label="公司名称">
        <el-input v-model="formCompany2.company_name" placeholder="请输入公司名称" />
      </el-form-item>
      <el-form-item label="社会信用代码">
        <el-input v-model="formCompany2.credit_number" placeholder="请输入社会信用代码" />
      </el-form-item>
    </el-form>
    
    <el-form-item>
      <el-button type="primary" :disabled="false" @click="submitQuery">
        查询
      </el-button>
      <el-button @click="resetForm">重置</el-button>
    </el-form-item>
    
    <!-- 查询结果区域 -->
    <div v-if="queryFinished">
      <el-descriptions title="关系信息" v-if="data.length">
        <el-descriptions-item v-for="(relationship, index) in data" :key="index" label="关系描述">
          <div>
            <strong>公司1:</strong>
            <div>公司名称: {{ relationship.start_node.company_name }}</div>
            <div>社会信用代码: {{ relationship.start_node.credit_number }}</div>

            <strong>公司2:</strong>
            <div>公司名称: {{ relationship.end_node.company_name }}</div>
            <div>社会信用代码: {{ relationship.end_node.credit_number }}</div>

            <strong>关系类型:</strong>
            <div>{{ relationship.relation_type }}</div>

            <strong>附加属性:</strong>
            <div>
              <div>日期: {{ relationship.attributes.date }}</div>
              <div>ID: {{ relationship.attributes.id }}</div>
            </div>
          </div>
        </el-descriptions-item>
      </el-descriptions>
      
      <!-- 空结果提示 -->
      <el-empty v-else description="查不到两个公司的关系" :image-size="100">
        <el-button type="primary" @click="resetForm">重新查询</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      formCompany1: {
        company_name: '',
        credit_number: ''
      },
      formCompany2: {
        company_name: '',
        credit_number: ''
      },
      data: [],
      queryFinished: false,
      testStats: null,
      positiveTestCases: [],
      negativeTestCases: [],
      loadingTestCases: false
    };
  },
  methods: {
    submitQuery() {
      const queryParams1 = this.createQueryParams(this.formCompany1);
      const queryParams2 = this.createQueryParams(this.formCompany2);

      if (queryParams1.length === 0) {
        alert('请输入公司1信息');
        return;
      }
      if (queryParams2.length === 0) {
        alert('请输入公司2信息');
        return;
      }
      const queryParams = {
        company1: queryParams1,
        company2: queryParams2,
      };

      this.fetchData(queryParams);
    },
    
    createQueryParams(form) {
      return Object.entries(form)
        // eslint-disable-next-line
        .filter(([key, value]) => value)
        .map(([key, value]) => ({ label: key, value }));
    },

    async fetchData(params) {
      try {
        const response = await axios.post('/api/queryrelationship/', params);

        if (response.data.status === 'success') {
          this.handleSuccess(response.data.relationships);
        } else {
          alert(response.data.message);
          this.queryFinished = true;
          this.data = [];
        }
      } catch (error) {
        console.error('请求失败:', error);
        alert('请求失败，请重试');
        this.queryFinished = true;
      }
    },

    handleSuccess(responseData) {
      this.data = responseData;
      this.queryFinished = true;
    },

    resetForm() {
      this.formCompany1 = {
        company_name: '',
        credit_number: ''
      };
      this.formCompany2 = {
        company_name: '',
        credit_number: ''
      };
      this.data = [];
      this.queryFinished = false;
    },

    async loadTestCases() {
      this.loadingTestCases = true;
      try {
        const response = await axios.get('/api/relation_test_cases/');
        if (response.data.status === 'success') {
          this.testStats = response.data;
          this.positiveTestCases = response.data.positive_test_cases || [];
          this.negativeTestCases = response.data.negative_test_cases || [];
        } else {
          alert('加载测试用例失败');
        }
      } catch (error) {
        console.error('加载测试用例失败:', error);
        alert('加载测试用例失败，请重试');
      } finally {
        this.loadingTestCases = false;
      }
    },

    fillTestCase(caseData) {
      this.formCompany1.company_name = caseData.company1 || '';
      this.formCompany2.company_name = caseData.company2 || '';
      this.formCompany1.credit_number = '';
      this.formCompany2.credit_number = '';
      this.data = [];
      this.queryFinished = false;
      // 自动执行查询
      this.submitQuery();
    }
  }
};
</script>

<style scoped>
h1 {
  margin-bottom: 20px;
}
h2 {
  margin-top: 30px;
  margin-bottom: 15px;
}
h3 {
  margin-top: 15px;
  margin-bottom: 10px;
  font-size: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dialog-footer {
  text-align: right;
}
</style>
