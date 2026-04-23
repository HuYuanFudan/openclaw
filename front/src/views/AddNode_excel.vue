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
                action=""
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
              <el-button type="primary" @click="uploadFile" :disabled="!selectedFile">上传</el-button>
            </el-col>
          </el-row>
        </el-form-item>
      </el-form>
      <el-descriptions column="1">
        <el-descriptions-item label="输入格式：">
          1. 只有一个表，第一行包含公司属性，每一行代表一个公司，每一列表示一种属性。
        </el-descriptions-item>
        <el-descriptions-item>
          2. 请确保公司属性名称严格对应节点设计中的定义，否则查找或添加关系时可能出现错误。
        </el-descriptions-item>
        <el-descriptions-item>
          3. 公司中文名称和统一社会信用代码必须填写，以方便后续查找。如果不填写，不会报错，但可能影响查找效率。
        </el-descriptions-item>
        <el-descriptions-item>
          4. 表格中会自动去除重复的公司记录以及在数据库中已存在的公司记录。
        </el-descriptions-item>
      </el-descriptions>

      <el-image :src="require('../assets/node_excel_law1.png')" />
    </el-main>
    <el-dialog
      v-model="dialogVisible"
      title="上传进度"
      width="400px"
      :before-close="handleClose"
    >
      <el-progress type="circle" :percentage="progress" />
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">关闭</el-button>
      </span>
    </el-dialog>
  </el-container>
</template>
<script>
import { ElUpload, ElButton, ElForm, ElFormItem, ElProgress, ElDialog } from 'element-plus';
import axios from 'axios';
export default {
  components: {
    ElUpload,
    ElButton,
    ElForm,
    ElFormItem,
    ElProgress,
    ElDialog,
  },
  data() {
    return {
      selectedFile: null, 
      progress: 0, 
      intervalId: null, 
      dialogVisible: false, 
    };
  },
  methods: {
    onFileChange(file) {
      this.selectedFile = file.raw;
      this.$message.success('文件已选择');
    },
    beforeUpload(file) {
      const isExcel =
        file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
        file.type === 'application/vnd.ms-excel';
      if (!isExcel) {
        this.$message.error('只能上传 Excel 文件！');
      }
      return isExcel; 
    },
    uploadFile() {
  const formData = new FormData();
  formData.append('file', this.selectedFile);
  
  this.dialogVisible = true;
  console.log('Dialog should now be visible');
  this.startPolling();  // 开始轮询
  // const accessToken = localStorage.getItem('access_token');
  // if (!accessToken) {
  //   this.$message.error('未登录或认证信息失效，请重新登录');
  //   return;
  // }
  axios.post('http://localhost:8001/addnodeexcel/', formData, {
    // headers: {
    //   Authorization: `Bearer ${accessToken}`  // 添加 Authorization 请求头
    // }
  })
  .then((response) => {
    if (response.data.status === 'success') {
      this.$message.success(response.data.message || '节点添加成功');
      if (response.data.existing_nodes && response.data.existing_nodes.length > 0) {
        console.log('重复节点:', response.data.existing_nodes);
        this.existingNodes = response.data.existing_nodes;
      } else {
        this.existingNodes = [];
      }
    } else {
      this.$message.error(response.data.message || '上传过程中发生错误');
    }
  })
  .catch((error) => {
    this.$message.error('节点添加失败');
    console.error(error);
  });
},
    startPolling() {
      let lastProgress = null;
      let sameCount = 0;
      this.intervalId = setInterval(() => {
        axios.get('http://localhost:8001/getprogress/')
          .then((response) => {
            this.progress = response.data.progress;
            console.log('Current progress:', this.progress); 
            if (this.progress === lastProgress) {
              sameCount++;
            } else {
              sameCount = 0;
            }
            if (sameCount >= 10) {
              clearInterval(this.intervalId);
              this.$message.success('进度连续10次相同，任务停止');
            }
            if (this.progress >= 100) {
              clearInterval(this.intervalId); 
            }
            lastProgress = this.progress;
          })
          .catch((error) => {
            console.error('获取进度失败', error);
            clearInterval(this.intervalId); 
          });
      }, 2000); 
    },
    handleClose() {
      clearInterval(this.intervalId);
    }
  },
};
</script>

<style scoped>
.upload-demo {
  margin-bottom: 16px;
}

.dialog-footer {
  text-align: center;
}
</style>
