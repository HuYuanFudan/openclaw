<template>
  <div class="container">
    <div class="input-group">
      <label for="description">元知识描述</label>
      <el-input
        id="description"
        v-model="description"
        placeholder="请输入元知识描述"
        required
      ></el-input>
    </div>
    
    <div class="formula-editor">
      <label>输入公式</label>
      <div v-for="(formula, index) in formulas" :key="index" class="formula-item">
        <math-field
          :id="'formula-' + index"
          :value="formula"
          @input="formulas[index] = $event.target.value"
        ></math-field>
        <el-icon class="delete-icon" v-if="formulas.length > 1" @click="removeFormula(index)">
          <Delete />
        </el-icon>
      </div>
    </div>

    <div class="variable-editor">
      <label>输入变量</label>
      <div v-for="(variable, index) in variables" :key="index" class="variable-item">
        <el-input v-model="variables[index]" :placeholder="'输入格式：第n个公式_变量名_代表的含义,例如 1_x_公司负债率'"></el-input>
        <el-icon class="delete-icon" @click="removeVariable(index)">
          <Delete />
        </el-icon>
      </div>
    </div>

    <div class="button-group">
      <el-button type="primary" @click="addVariable">添加变量</el-button>
      <el-button type="primary" @click="addFormula">添加公式</el-button>
      <el-button type="success" @click="addMetaKnowledge">提交</el-button>
    </div>
    
    <p v-if="message" class="message">{{ message }}</p>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { MathfieldElement } from 'mathlive';
import axios from 'axios';
import { Delete } from '@element-plus/icons-vue';

export default {
  components:{
    Delete
  },
  setup() {
    const description = ref('');
    const message = ref('');
    const formulas = ref(['']); // 公式变成数组形式
    const variables = ref(['']); // 变量变成数组形式

    onMounted(() => {
      if (!customElements.get('math-field')) {
        customElements.define('math-field', MathfieldElement);
      }
    });

    const addFormula = () => {
      formulas.value.push(''); // 添加新的空公式
    };

    const removeFormula = (index) => {
      if (formulas.value.length > 1) {
        formulas.value.splice(index, 1);
      }
    };

    const addVariable = () => {
      variables.value.push(''); // 添加新的空变量
    };

    const removeVariable = (index) => {
      variables.value.splice(index, 1);
    };

    const addMetaKnowledge = async () => {
      try {
        const response = await axios.post('http://10.176.22.62:8001/meta/allmetaknowledge/', {
          description: description.value,
          formulas: formulas.value,
          variables: variables.value, // 以列表形式传递变量
        });
        if (response.status === 201) {
          message.value = '元知识添加成功！';
          description.value = '';
          formulas.value = [''];
          variables.value = [];
        } else {
          message.value = '元知识添加失败，请重试！';
        }
      } catch (error) {
        console.error('网络错误:', error);
        message.value = '网络错误，请检查网络连接！';
      }
    };

    return {
      description,
      message,
      formulas,
      variables,
      addFormula,
      removeFormula,
      addVariable,
      removeVariable,
      addMetaKnowledge,
    };
  },
};
</script>

<style scoped>
.container {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
}

.formula-editor,
.variable-editor {
  margin-bottom: 20px;
}

.formula-item,
.variable-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

math-field {
  flex: 1;
  min-height: 50px;
  padding: 10px;
  font-size: 1.2em;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: border-color 0.3s, box-shadow 0.3s;
}

math-field:focus {
  border-color: #409eff; 
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.6); 
}

.delete-icon {
  margin-left: 10px;
  color: #f56c6c;
  cursor: pointer;
  font-size: 20px;
  transition: color 0.3s;
}

.delete-icon:hover {
  color: #ff0000;
}

/* 按钮组，确保按钮在同一行 */
.button-group {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
}

.submit-btn {
  text-align: center;
}

.message {
  text-align: center;
  margin-top: 10px;
  color: green;
}
</style>