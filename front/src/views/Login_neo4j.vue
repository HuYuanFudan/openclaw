<template>
  <div class="login_container">
    <h1 class="welcome_message">Welcome</h1>
    <div class="login_box">
      <div class="avatar_box">
        <img src="../assets/logo.png" alt="">
      </div>
      <el-form ref="loginFormRef" :model="loginForm" :rules="loginFormRules" label-width="0px" class="login_form">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password">
            <template #prefix>
              <el-icon><Key /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item class="btns">
          <el-button type="primary" @click="handleLogin" style="margin-left: 40%">登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>
<script>
import axios from 'axios';
import {ElForm, ElButton} from 'element-plus';
import { User, Key} from '@element-plus/icons-vue';
export default {
  components:{
    ElForm,
    ElButton,
    User,
    Key
  },
  data() {
    return {
      loginForm: {  
        username: '',
        password: ''
      },
      loginFormRules: {  
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' }
        ]
      }
    };
  },
  mounted() {
    console.log('Component mounted successfully');
  },
  methods: {
    async handleLogin() {
  if (this.$refs.loginFormRef) {
    this.$refs.loginFormRef.validate(async (valid) => {
      if (valid) {
        try {
          const response = await axios.post('http://10.176.22.62:8001/login/', {
            username: this.loginForm.username,
            password: this.loginForm.password
          });
          const accessToken = response.data.access;
          const refreshToken = response.data.refresh;
          localStorage.setItem('access_token', accessToken);
          localStorage.setItem('refresh_token', refreshToken);
          console.log('登录成功');
          this.$router.push('/home');  
        } catch (error) {
          console.log('用户名或密码错误');
          this.$message.error('用户名或密码错误');
        }
      } else {
        console.log('表单验证失败');
      }
    });
  } else {
    console.log('表单引用不存在');
  }
}
  }
};
</script>

<style scoped>
.welcome_message {
  text-align: center;
  font-size: 20px;
  font-weight: lighter;
  margin-bottom: 20px;
  position: absolute;
  top: 150px; 
  left: 50%;
  transform: translateX(-50%);
  color: #333;
}
  .login_container {
    background-color: rgba(21, 35, 242, 0.25);
    height: 100%;
  }

  .button-container {
    text-align: center;
  }

  .login_box {
    width: 450px;
    height: 300px;
    background-color: #f2f2f2;
    border-radius: 3px;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);

    .avatar_box {
      height: 130px;
      width: 130px;
      border: 1px solid #eee;
      border-radius: 50%;
      padding: 10px;
      box-shadow: 0 0 10px #ddd;
      position: absolute;
      left: 50%;
      transform: translate(-50%, -50%);
      background-color: #fff;

      img {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background-color: #eee;
      }
    }

    .login_form {
      position: absolute;
      bottom: 0;
      width: 100%;
      padding: 0 20px;
      box-sizing: border-box;
    }
  }
</style>
