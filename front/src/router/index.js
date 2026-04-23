import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import AddNode from '../views/AddNode.vue';
import Login from '../views/Login_neo4j.vue';
import QueryNode from '@/views/QueryNode.vue';
import DeleteNode from '@/views/DeleteNode.vue';
import QueryRelationship from '@/views/QueryRelationship.vue';
import AllGraph from '@/views/AllGraph.vue';
import Allmetaknowledge from '@/views/AllMetaknowledge.vue';
import Addmetaknowdede from '@/views/AddMetaKnowledge.vue';
import Formula from '@/views/formula.vue'
import CrossDocEntityExtract from '@/views/CrossDocEntityExtract.vue'
import EvidenceEnhancedDecision from '@/views/EvidenceEnhancedDecision.vue'
const routes = [
  {
    path: '/home',
    name: 'home',
    component: HomeView,
    meta:{
      requireAuth: true
    }
  },
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/addnode',
    name: 'addnode',
    component: AddNode,
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
  },
  {
    path: '/querynode',
    name: 'querynode',
    component: QueryNode
  },
  {
    path: '/deletenode',
    name: 'deletenode',
    component: DeleteNode
  },
  {
    path: '/queryrelationship',
    name: 'queryrelationship',
    component: QueryRelationship
  },
  {
    path: '/allgraph',
    name: 'allgraph',
    component: AllGraph
  },
  {
    path: '/allmetaknowledge',
    name: 'allmetaknowledge',
    component: Allmetaknowledge
  },
  {
    path: '/addmetaknowledge',
    name: 'addmetaknowledge',
    component: Addmetaknowdede
  },
  {
    path: '/formula',
    name: 'formula',
    component: Formula
  },
  {
    path: '/cross-doc-extract',
    name: 'cross-doc-extract',
    component: CrossDocEntityExtract
  },
  {
    path: '/evidence-decision',
    name: 'evidence-decision',
    component: EvidenceEnhancedDecision
  }
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token');
  const isLoginRoute = to.path === '/login';

  if (to.matched.some(record => record.meta.requireAuth)) {
    // 需要认证的路由
    if (!token) {
      next('/login');
    } else {
      next();
    }
  } else if (token && isLoginRoute) {
    // 已登录但访问登录页，重定向到首页
    next('/home');
  } else {
    // 其他情况放行
    next();
  }
});

export default router