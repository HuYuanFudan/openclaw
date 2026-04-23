<template>
  <div class="container">
    <el-row type="flex" justify="center" align="middle">
      <el-col :span="12">
        <el-form>
          <el-form-item label="公司名称" label-width="80px">
            <el-input
              v-model="inputText"
              placeholder="请输入公司名称"
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
          @click="sendData"
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
      <el-table-column prop="name" label="公司中文名称" width="250px"></el-table-column>
      <el-table-column prop="social_credit_code" label="社会信用代码" width="250px"></el-table-column>
    </el-table>
    <el-button
      v-if="companyResults.length > 0"
      type="success"
      size="medium"
      style="margin-top: 20px; display: block; margin-left: auto; margin-right: auto;"
      @click="downloadExcel"
    >
      下载 Excel 文件
    </el-button>
    <div v-else style="margin-top: 20px; text-align: center; color: #888;">
      暂无匹配结果
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      inputText: '', 
      companyResults: [], 
      isButtonEnabled: false, 
    };
  },
  watch: {
    inputText(value) {
      this.isButtonEnabled = value.trim().length > 0;
    },
  },
  methods: {
    async sendData() {
      try {
        const response = await axios.post('http://10.176.22.62:8001/fuzzymatch/', {
          companyName: this.inputText,
        });
        this.companyResults = response.data.companies;
      } catch (error) {
        console.error('Error:', error);
      }
    },
    async downloadExcel() {
  try {
    const response = await axios.post('http://10.176.22.62:8001/fmatexcel/', {
      companyName: this.inputText,
    }, {
      responseType: 'arraybuffer',  
    });
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'companies.xlsx';  
    link.click();  

  } catch (error) {
    console.error('Error:', error);
  }
},
  },
};
</script>
<style scoped>
.container {
  padding: 30px;
  background-color: #f9f9f9;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  margin: 0 auto;
}
.el-button {
  width: 100%;
}
.el-table {
  background-color: #ffffff;
  border-radius: 5px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}
.el-table th {
  background-color: #f5f5f5;
  color: #333;
}
.el-table .cell {
  text-align: center;
}
</style>
