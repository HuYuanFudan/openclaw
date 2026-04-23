<template>
  <div class="container">
    <el-row type="flex" justify="center" align="middle">
      <el-col :span="12">
        <el-form>
          <el-form-item label="公司名称">
            <el-input
              v-model="form.company_name"
              placeholder="请输入公司名称"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
          <el-form-item label="社会信用代码">
            <el-input
              v-model="form.credit_number"
              placeholder="请输入统一社会信用代码"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
          <el-form-item label="法定代表人">
            <el-input
              v-model="form.legal_representative"
              placeholder="请输入法定代表人"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
          <el-form-item label="证券代码">
            <el-input
              v-model="form.security_code"
              placeholder="请输入证券代码"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
          <el-form-item label="股票简称">
            <el-input
              v-model="form.stock_abbreviation"
              placeholder="请输入股票简称"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
        </el-form>
      </el-col>
      <el-col :span="12">
        <el-button
          type="primary"
          :disabled="!isButtonEnabled"
          @click="submitQuery"
          size="medium"
          style="margin-left: 20px;"
        >
          查询
        </el-button>
      </el-col>
    </el-row>

    <el-table
      v-if="companyResults.length > 0"
      :data="companyResults"
      style="width: 100%; margin-top: 30px;"
      stripe
    >
      <el-table-column prop="company_name" label="公司中文名称" width="250px"></el-table-column>
      <el-table-column prop="credit_number" label="社会信用代码" width="250px"></el-table-column>
      <el-table-column label="操作" width="150px">
        <template v-slot:default="scope">
          <el-button @click="viewDetails(scope.row)" type="text" size="small">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model='dialogVisible'
      title="公司详情"
      @close="closeDialog"
    >
      <el-form label-width="120px">
        <el-form-item label="公司中文名称">
          <el-input v-model="companyDetails.company_name" disabled></el-input>
        </el-form-item>
        <el-form-item label="社会信用代码">
          <el-input v-model="companyDetails.credit_number" disabled></el-input>
        </el-form-item>
        <el-form-item label="英文名称">
          <el-input v-model="companyDetails.english_name" disabled></el-input>
        </el-form-item>
        <el-form-item label="法定代表人">
          <el-input v-model="companyDetails.legal_representative" disabled></el-input>
        </el-form-item>
        <el-form-item label="证券代码">
          <el-input v-model="companyDetails.security_code" disabled></el-input>
        </el-form-item>
        <el-form-item label="股票简称">
          <el-input v-model="companyDetails.stock_abbreviation" disabled></el-input>
        </el-form-item>
      </el-form>
      <span class="dialog-footer">
        <el-button @click="closeDialog">返回</el-button>
      </span>
    </el-dialog>

    <div style="margin-top: 20px; text-align: center; color: #888;">
      暂无匹配结果
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      form: {
        company_name: '',
        credit_number: '',
        legal_representative: '',
        security_code: '',
        stock_abbreviation: '',
      },
      companyResults: [],
      dialogVisible: false,  // 控制对话框的显示
      companyDetails: {},    // 存储公司详情
    };
  },
  computed: {
    isButtonEnabled() {
      const filledCount = Object.values(this.form).filter(value => value).length;
      return filledCount > 0;
    },
  },
  methods: {
    async submitQuery() {
      const queryParams = Object.entries(this.form)
      // eslint-disable-next-line
        .filter(([key, value]) => value)
        .map(([key, value]) => ({ label: key, value }));

      try {
        const response = await axios.post('http://10.176.22.62:8001/querynode/', queryParams);
        if (response.data && Array.isArray(response.data)) {
          this.companyResults = response.data;
        } else {
          this.companyResults = [];
        }
      } catch (error) {
        console.error('请求失败:', error);
        this.$message.error('查询失败，请稍后重试');
      }
    },

    // 查看详情按钮点击事件
    async viewDetails(row) {
      try {
        const response = await axios.post('http://10.176.22.62:8001/qynodedtil/', {
          credit_number: row.credit_number,
        });

        if (response.data) {
          this.companyDetails = response.data;  // 设置公司详情
          this.dialogVisible = true;  // 打开对话框
        } else {
          this.$message.error('未能找到该公司详情');
        }
      } catch (error) {
        console.error('请求失败:', error);
        this.$message.error('查询公司详情失败，请稍后重试');
      }
    },

    // 关闭对话框
    closeDialog() {
      this.dialogVisible = false;
    },
  },
};
</script>
<style scoped>
.container {
  padding: 20px;
}
</style>