<template>
  <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
    <el-row :gutter="10">
      <el-col :span="12" v-for="(item, index) in attributes" :key="index" class="form-col">
        <el-form-item :label="item.label" :prop="item.key" :rules="item.rules">
          <el-input v-model="form[item.key]" />
        </el-form-item>
      </el-col>
    </el-row>
  </el-form>
  <div class="button-container">
    <el-button type="primary" @click="submitForm">提交</el-button>
  </div>
</template>

<script>
// eslint-disable-next-line
import axios from 'axios';
export default {
  data() {
    return {
      form: {
        company_name: '',
        credit_number: '',
        province: '',
        company_type: '',
        city: '',
        district_info: '',
        main_business: '',
        a_stock_code: '',
        organization_form: '',
        security_name: '',
        stock_abbreviation: '',
        security_code: '',
        board_secretary_code: '',
        business_scope: '',
        registered_address: '',
        legal_representative: '',
        former_company_name: '',
        company_phone: '',
        company_profile: '',
        english_name: '',
        b_stock_code: '',
        actual_controller: '',
      },
      // company_data: {
      //   "公司中文名称": '',
      //   "统一社会信用代码": '',
      //   "省份": '',
      //   "公司类型": '',
      //   "市": '',
      //   "区县信息": '',
      //   "主营业务": '',
      //   "A股证券代码": '',
      //   "组织形式":'',
      //   "证券名称": '',
      //   "股票简称": '',
      //   "证券代码": '',
      //   "董事会秘书代码": '',
      //   "经营范围": '',
      //   "注册地址": '',
      //   "法定代表人": '',
      //   "公司曾用名": '',
      //   "公司电话": '',
      //   "公司简介": '',
      //   "英文名称": '',
      //   "B股证券代码": '',
      //   "实际控制人": ''
      // },
      attributes: [
        { label: '公司中文名称', key: 'company_name', rules: [{ required: true, message: '公司中文名称是必填项', trigger: 'blur' }] },
        { label: '统一社会信用代码', key: 'credit_number', rules: [{ required: true, message: '统一社会信用代码是必填项', trigger: 'blur' }] },
        { label: '省份', key: 'province' },
        { label: '公司类型', key: 'company_type' },
        { label: '市', key: 'city' },
        { label: '区县信息', key: 'district_info' },
        { label: '主营业务', key: 'main_business' },
        { label: 'A股证券代码', key: 'a_stock_code' },
        { label: '组织形式', key: 'organization_form' },
        { label: '证券名称', key: 'security_name' },
        { label: '股票简称', key: 'stock_abbreviation' },
        { label: '证券代码', key: 'security_code' },
        { label: '董事会秘书代码', key: 'board_secretary_code' },
        { label: '经营范围', key: 'business_scope' },
        { label: '注册地址', key: 'registered_address' },
        { label: '法定代表人', key: 'legal_representative' },
        { label: '公司曾用名', key: 'former_company_name' },
        { label: '公司电话', key: 'company_phone' },
        { label: '公司简介', key: 'company_profile' },
        { label: '英文名称', key: 'english_name' },
        { label: 'B股证券代码', key: 'b_stock_code' },
        { label: '实际控制人', key: 'actual_controller' },
      ],
    };
  },
  methods: {
    async submitForm() {
  this.$refs.formRef.validate(async (valid) => { 
    if (valid) {
      const requestData = { ...this.form };
      // const accessToken = localStorage.getItem('access_token');
      try {
        const response = await axios.post('http://10.176.22.62:8001/addnode/', requestData, {
          // headers: {
          //   Authorization: `Bearer ${accessToken}`
          // }
        });
        
        if (response.data.status === 'success') {
          alert("添加成功");
        } else if (response.data.status === 'error') {
          alert(response.data.message);
        }
      } catch (error) {
        console.error(error);
        alert('请求失败，请重试！');
      }
    } else {
      alert('请填写必填项！');
      return false;
    }
  });
}
  },
};
</script>

<style scoped>
.form-col {
  margin-bottom: 16px;
}
</style>
