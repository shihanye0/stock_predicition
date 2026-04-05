import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '情绪仪表盘' }
  },
  {
    path: '/stocks',
    name: 'Stocks',
    component: () => import('@/views/Stocks.vue'),
    meta: { title: '股票列表' }
  },
  {
    path: '/stock/:code',
    name: 'StockDetail',
    component: () => import('@/views/StockDetail.vue'),
    meta: { title: '股票详情' }
  },
  {
    path: '/trend',
    name: 'Trend',
    component: () => import('@/views/Trend.vue'),
    meta: { title: '趋势分析' }
  },
  {
    path: '/validation',
    name: 'Validation',
    component: () => import('@/views/Validation.vue'),
    meta: { title: '市场验证' }
  },
  {
    path: '/sentiment',
    name: 'Sentiment',
    component: () => import('@/views/Sentiment.vue'),
    meta: { title: '情感分析' }
  },
  {
    path: '/experiment',
    name: 'Experiment',
    component: () => import('@/views/Experiment.vue'),
    meta: { title: '实验对比' }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/Alerts.vue'),
    meta: { title: '情绪预警' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 股票情绪预测系统` : '股票情绪预测系统'

  // 只检查JWT token，不再允许游客模式
  const token = localStorage.getItem('token')
  const isLoggedIn = !!token

  // 公开页面直接放行
  if (to.meta.public) {
    // 已登录用户访问登录页，跳转到首页
    if (to.name === 'Login' && isLoggedIn) {
      next({ name: 'Dashboard' })
      return
    }
    next()
    return
  }

  // 需要登录的页面
  if (!isLoggedIn) {
    next({ name: 'Login' })
    return
  }

  next()
})

export default router
