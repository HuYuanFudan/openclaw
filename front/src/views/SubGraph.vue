<template>
    <el-form :model="form" label-width="120px">
      <el-form-item label="公司名称">
        <el-input v-model="form.companyName" placeholder="请输入公司名称" />
      </el-form-item>
      <el-form-item label="跳数">
        <el-input v-model="form.step" placeholder="请输入跳数量" />
      </el-form-item>
      <el-form-item label="时间属性名">
        <el-input v-model="form.date_name" placeholder="请输入时间属性名" />
      </el-form-item>
      <el-form-item label="开始时间">
        <el-date-picker
          v-model="form.startDate"
          type="date"
          placeholder="选择开始时间"
        />
      </el-form-item>
      <el-form-item label="结束时间">
        <el-date-picker
          v-model="form.endDate"
          type="date"
          placeholder="选择结束时间"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submitForm">提交</el-button>
      </el-form-item>
    </el-form>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    name: 'Neo4jQueryForm',
    data() {
      return {
        form: {
          companyName: '',
          startDate: '',
          endDate: '',
          step: '',
          date_name: '',
        },
      }
    },
    methods: {
      async submitForm() {
        const requestData = {
          companyName: this.form.companyName,
          startDate: this.form.startDate,
          endDate: this.form.endDate,
          step: this.form.step,
          date_name: this.form.date_name,
        }
        try {
          const response = await axios.post('http://10.176.22.62:8001/generatequery/', requestData, {
            responseType: 'blob' // 将响应数据视为 Blob 文件
          })
          const blob = new Blob([response.data])
          const downloadUrl = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = downloadUrl
          const contentDisposition = response.headers['content-disposition']
          let fileName = 'downloaded_file.json' 
          if (contentDisposition) {
            const matches = contentDisposition.match(/filename="(.+)"/)
            if (matches && matches[1]) fileName = matches[1]
          }
          link.setAttribute('download', fileName)
          document.body.appendChild(link)
          link.click()
          link.remove()
          window.URL.revokeObjectURL(downloadUrl)
          this.$message({
            message: '文件已成功下载！',
            type: 'success',
          })
        } catch (error) {
          this.$message.error('下载失败，请检查输入')
          console.error(error)
        }
      },
    },
  }
  </script>
  <style scoped>
  .el-form {
    max-width: 600px;
    margin: 20px auto;
  }
  </style>
  