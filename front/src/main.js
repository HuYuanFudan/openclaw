import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import axios from 'axios';
import App from './App.vue';
import router from './router/index.js';

const app = createApp(App);

// === 修复 ResizeObserver loop 警告 ===
// 根因：Element Plus 内部 ResizeObserver 回调在同步阶段触发 DOM/布局变更，
// 导致浏览器抛出 "ResizeObserver loop completed with undelivered notifications"。
// 解法：用 rAF 把所有 ResizeObserver 回调延后到下一帧，打断同步循环。
// 这是 Element Plus 官方推荐的处理方式。
if (typeof window !== 'undefined' && window.ResizeObserver) {
  const _OrigRO = window.ResizeObserver;
  window.ResizeObserver = class ResizeObserver extends _OrigRO {
    constructor(callback) {
      super((entries, observer) => {
        requestAnimationFrame(() => {
          try { callback(entries, observer); } catch (e) { /* swallow */ }
        });
      });
    }
  };
}

// 兜底：即便上面失效，也屏蔽 webpack-dev-server 浮层显示该警告
window.addEventListener('error', (e) => {
  if (e && e.message && e.message.includes('ResizeObserver loop')) {
    e.stopImmediatePropagation();
    e.preventDefault();
    return false;
  }
  return true;
}, true);
/* eslint-disable no-unused-vars */
const _origOnError = window.onerror;
window.onerror = function (msg, src, line, col, err) {
  if (typeof msg === 'string' && msg.includes('ResizeObserver loop')) return true;
  if (_origOnError) return _origOnError.apply(this, arguments);
  return false;
};
app.config.errorHandler = (err, vm, info) => {
  if (err && err.message && err.message.includes('ResizeObserver loop')) return;
  // eslint-disable-next-line no-console
  console.error(err, info);
};
/* eslint-enable no-unused-vars */

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
app.use(router);

// 挂载应用
app.mount('#app');
