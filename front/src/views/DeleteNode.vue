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
          <el-icon
            @click="showDeleteDialog(scope.row.credit_number)"
            style="color: red; cursor: pointer; margin-left: 10px;"
          >
            <Delete />
          </el-icon>
        </template>
      </el-table-column>
    </el-table>

    <!-- 公司详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
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

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除确认"
      width="30%"
    >
      <span>确定要删除该公司信息吗？</span>
      <template #footer>
        <el-button @click="closeDeleteDialog">取消</el-button>
        <el-button type="primary" @click="confirmDelete">确定</el-button>
      </template>
    </el-dialog>

    <div v-if="companyResults.length === 0" style="margin-top: 20px; text-align: center; color: #888;">
      暂无匹配结果
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus';
import axios from 'axios';
import { ElIcon } from 'element-plus';
import { Delete } from '@element-plus/icons-vue';

export default {
  components: {
    ElIcon,
    Delete
  },
  data() {
    return {
      form: {
        company_name: '',
        credit_number: '',
        legal_representative: '',
        security_code: '',
        stock_abbreviation: ''
      },
      companyResults: [],
      dialogVisible: false,
      companyDetails: {},   
      deleteDialogVisible: false, 
      deleteTarget: null,  
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
    async viewDetails(row) {
      try {
        const response = await axios.post('http://10.176.22.62:8001/qynodedtil/', {
          credit_number: row.credit_number,
        });

        if (response.data) {
          this.companyDetails = response.data;
          this.dialogVisible = true;  
        } else {
          this.$message.error('未能找到该公司详情');
        }
      } catch (error) {
        console.error('请求失败:', error);
        this.$message.error('查询公司详情失败，请稍后重试');
      }
    },
    closeDialog() {
      this.dialogVisible = false;
    },
    showDeleteDialog(credit_number) {
      this.deleteTarget = credit_number;
      this.deleteDialogVisible = true; 
    },
    closeDeleteDialog() {
      this.deleteDialogVisible = false;
      this.deleteTarget = null; 
    },
    async confirmDelete() {
  try {
    // const accessToken = localStorage.getItem('access_token'); 
    // if (!accessToken) {
    //   ElMessage.error('未找到认证信息，请重新登录');
    //   return;
    // }
    const response = await axios.post(
      'http://10.176.22.62:8001/deletenode/',
      { credit_number: this.deleteTarget },
      {
        // headers: {
        //   Authorization: `Bearer ${accessToken}` 
        // }
      }
    );

    if (response.data.status === 'success') {
      this.companyResults = this.companyResults.filter(
        (item) => item.credit_number !== this.deleteTarget
      );
      ElMessage.success('删除成功');  
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    console.error('删除失败:', error);
    ElMessage.error('删除失败，请稍后重试');
  }
  this.closeDeleteDialog();
}
  }
};
</script>

<style scoped>
.container {
  padding: 20px;
}
</style>