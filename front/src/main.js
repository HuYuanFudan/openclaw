import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import axios from 'axios';
import App from './App.vue';
import router from './router/index.js';

const app = createApp(App);

// 先配置 axios 和 Vue Router，再挂载应用
const token = localStorage.getItem('jwt_token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

axios.defaults.withCredentials = true;
axios.defaults.baseURL = process.env.NODE_ENV === "development" ? "" : "http://10.176.22.62:8000";

// 全局挂载 axios
app.config.globalProperties.$http = axios;

// 使用 Element Plus 和 Vue Router
app.use(ElementPlus);
app.use(router);  // 路由应该在此处

// 挂载应用
app.mount('#app');
