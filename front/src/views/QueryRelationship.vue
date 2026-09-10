<template>
  <div>
    <h1>关系查询</h1>

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
      queryFinished: false
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
</style>
