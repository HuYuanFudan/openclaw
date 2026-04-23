<template>
  <el-container>
    <el-header>
      <h2>上传 Excel 文件</h2>
    </el-header>
    <el-main>
      <el-form>
        <el-form-item>
          <el-row>
            <el-col :span="18">
              <el-upload
                ref="upload"
                class="upload-demo"
                drag
                action="/your/api/endpoint"
                :on-change="onFileChange"
                :before-upload="beforeUpload"
                :show-file-list="false"
                :auto-upload="false"
              >
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
                <div class="el-upload__tip">只能上传 .xlsx 或 .xls 文件</div>
              </el-upload>
            </el-col>
            <el-col :span="6" style="padding-left: 20px;">
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item>
          <el-input v-model="relationship_name" placeholder="请输入关系名称" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="uploadFile" :disabled="!selectedFile">确认添加</el-button>
        </el-form-item>
      </el-form>
      <el-descriptions column=1>
        <el-descriptions-item label="输入格式：">
          1. 只有一个表，第一行包含公司属性，每一行代表一个公司，每一列表示一种属性。
        </el-descriptions-item>
        <el-descriptions-item>
          2. 请确保公司属性名称严格对应节点设计中的定义，否则查找或添加关系时可能出现错误。
        </el-descriptions-item>
      </el-descriptions>
      <el-image :src="require('../assets/relationship_excel_law1.png')" />
    </el-main>
    <el-dialog
      title="任务进度"
      v-model="dialogVisible"
      width="50%"
      @close="stopPolling">
      <el-progress :percentage="progress" type="circle" />
      <span class="dialog-footer">
        <el-button @click="stopPolling" >关闭</el-button>
      </span>
    </el-dialog>
  </el-container>
</template>

<script>
import { ElUpload, ElButton, ElForm, ElFormItem, ElProgress, ElDialog, ElDescriptions, ElImage, ElRow, ElCol, ElInput } from 'element-plus';
import axios from 'axios';

export default {
  components: {
    ElUpload,
    ElButton,
    ElForm,
    ElFormItem,
    ElProgress,
    ElDialog,
    ElDescriptions,
    ElImage,
    ElRow,
    ElCol,
    ElInput
  },
  data() {
    return {
      selectedFile: null,
      relationship_name: null,
      progress: 0,
      intervalId: null,
      dialogVisible: false, 
    };
  },
  methods: {
    onFileChange(file) {
      this.selectedFile = file.raw; 
      this.$message.success('文件添加成功！');
    },
    beforeUpload(file) {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                      file.type === 'application/vnd.ms-excel';
      if (!isExcel) {
        this.$message.error('只能上传 Excel 文件！');
      }
      return isExcel; 
    },
    async uploadFile() {
  const formData = new FormData();
  this.dialogVisible = true;  
  formData.append('relationship_name', this.relationship_name);
  formData.append('file', this.selectedFile);
  const accessToken = localStorage.getItem('access_token');
  if (!accessToken) {
    this.$message.error('未登录或认证信息失效，请重新登录');
    return;
  }

  try {
    const uploadResponse = await axios.post('http://localhost:8001/addrelationshipexcel/', formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${accessToken}`  
      }
    });
    if (uploadResponse.data.status === 'success') {
      this.$message.success('文件上传成功，开始处理...');
      this.dialogVisible = true;  
      this.startPolling();  
    } else {
      this.$message.error(uploadResponse.data.message);
    }
  } catch (error) {
    console.error('上传失败:', error);
    this.$message.error('文件上传失败！');
  }
},
    startPolling() {
      let lastProgress = null; 
      let sameCount = 0;    

      this.intervalId = setInterval(() => {
        axios
          .get('http://localhost:8001/getprogress/')
          .then((response) => {
            this.progress = response.data.progress;
            if (this.progress === lastProgress) {
              sameCount++;
            } else {
              sameCount = 0; 
            }
            if (sameCount >= 50) {
              clearInterval(this.intervalId);
              this.$message.success('进度连续50次相同，任务停止');
            }
            if (this.progress >= 100) {
              clearInterval(this.intervalId);
              this.$message.success('任务完成');
              this.dialogVisible = false;  
            }
            lastProgress = this.progress;
          })
          .catch((error) => {
            console.error('获取进度失败', error);
            clearInterval(this.intervalId);
          });
      }, 2000); 
    },
    stopPolling() {
      clearInterval(this.intervalId);
      this.dialogVisible = false; 
    }
  },
};
</script>
<style scoped>
.upload-demo {
  margin-bottom: 16px;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>