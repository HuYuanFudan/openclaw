<template>
  <div class="meta-knowledge-container">
    <el-table :data="metaKnowledgeList" style="width: 100%">
      <el-table-column label="描述" prop="description" width="1000" align="center">
      </el-table-column>
      <el-table-column label="操作" width="150" align="center">
        <template #default="scope">
          <el-icon @click="handleIconClick(scope.row.id)">
            <View />
          </el-icon>
          <el-icon @click="openDeleteDialog(scope.row.id)">
            <Delete />
          </el-icon>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="dialogVisible" title="元知识详情" @close="clearMetaKnowledge">
    <div v-if="metaKnowledge">
      <p><strong>描述：</strong>{{ metaKnowledge.description }}</p>
      <p><strong>公式：</strong>
        <span v-if="metaKnowledge.formulas && metaKnowledge.formulas.length > 0">
          {{ metaKnowledge.formulas.map(f => f.formula_string).join(', ') }}
        </span>
        <span v-else>无</span>
      </p>
      <p><strong>变量：</strong></p>
      <ul v-if="metaKnowledge.formulas && metaKnowledge.formulas.length > 0">
        <li v-for="formula in metaKnowledge.formulas" :key="formula.id">
          <strong>公式 {{ formula.id }}:</strong>
          <span v-if="formula.variables && formula.variables.length > 0">
            {{ formula.variables.map(v => `${v.variable_name}(${v.variable_type})`).join(', ') }}
          </span>
          <span v-else>无变量</span>
        </li>
      </ul>
    </div>
    <div v-else>
      <p>加载中...</p>
    </div>
    <span class="dialog-footer">
      <el-button @click="dialogVisible = false">关闭</el-button>
    </span>
  </el-dialog>
    <el-dialog v-model="deleteDialogVisible" title="确认删除">
      <template #default>
        <span>确定要删除这条元知识吗？</span>
      </template>
      <template #footer>
        <el-button @click="closeDeleteDialog">取消</el-button>
        <el-button type="primary" @click="confirmDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script>
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { View, Delete } from '@element-plus/icons-vue';

export default {
  data() {
    return {
      metaKnowledgeList: [], 
      deleteDialogVisible: false, 
      deleteId: null, 
      dialogVisible: false, 
      id: null, 
      metaKnowledge: null, 
    };
  },
  components: {
    View,
    Delete
  },
  created() {
    this.fetchMetaKnowledge(); 
  },
  methods: {
    async fetchMetaKnowledge() {
      try {
        const response = await axios.get('http://10.176.22.62:8001/meta/allmetaknowledge/');
        this.metaKnowledgeList = response.data;
      } catch (error) {
        ElMessage.error('获取元知识失败');
      }
    },
    openDeleteDialog(id) {
      this.deleteId = id;
      this.deleteDialogVisible = true;
    },
    closeDeleteDialog() {
      this.deleteDialogVisible = false;
    },
    async confirmDelete() {
      try {
        const response = await axios.delete(`http://10.176.22.62:8001/meta/allmetaknowledge/${this.deleteId}/`);
        if (response.status === 204) {
          this.closeDeleteDialog();
          this.metaKnowledgeList = this.metaKnowledgeList.filter(item => item.id !== this.deleteId);
          ElMessage.success('元知识已删除');
        } else {
          ElMessage.error('删除失败，请重试！');
        }
      } catch (error) {
        console.error('网络错误:', error);
        ElMessage.error('网络错误，请检查网络连接！');
      }
    },
    async handleIconClick(id) {
      this.id = id;
      this.dialogVisible = true;
      this.metaKnowledge = null; 
      try {
        const response = await axios.get(`http://10.176.22.62:8001/meta/allmetaknowledge/${this.id}/`);
        this.metaKnowledge = response.data;
      } catch (error) {
        console.error('获取元知识信息失败：', error);
        ElMessage.error('获取元知识信息失败');
      }
    },
    clearMetaKnowledge() {
      this.metaKnowledge = null;
    },
  }
};
</script>
<style scoped>
.meta-knowledge-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20px;
}
.el-icon {
  cursor: pointer;
  margin: 0 5px;
}
</style>
