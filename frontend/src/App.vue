<template>
  <el-config-provider :locale="zhCn" :size="'default'">
    <!-- 公开页面（登录页）：纯净全屏，无侧边栏和顶栏 -->
    <router-view v-if="isPublicRoute" />

    <!-- 认证页面：带侧边栏和顶栏的主布局 -->
    <el-container v-else class="app-container">
      <!-- 侧边栏 -->
      <el-aside width="240px" class="app-aside">
        <div class="logo">
          <div class="logo-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="logo-text">
            <span class="logo-title">SentiStock</span>
            <span class="logo-sub">情绪预测终端</span>
          </div>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="app-menu"
          router
        >
          <el-menu-item index="/">
            <el-icon><Odometer /></el-icon>
            <span>情绪仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/stocks">
            <el-icon><List /></el-icon>
            <span>股票列表</span>
          </el-menu-item>
          <el-menu-item index="/trend">
            <el-icon><DataLine /></el-icon>
            <span>趋势分析</span>
          </el-menu-item>
          <el-menu-item index="/validation">
            <el-icon><DocumentChecked /></el-icon>
            <span>市场验证</span>
          </el-menu-item>
          <el-menu-item index="/sentiment">
            <el-icon><ChatLineRound /></el-icon>
            <span>情感分析</span>
          </el-menu-item>
          <el-menu-item index="/experiment">
            <el-icon><Cpu /></el-icon>
            <span>实验对比</span>
          </el-menu-item>
          <el-menu-item index="/alerts">
            <el-icon><Bell /></el-icon>
            <span>情绪预警</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>

        <!-- 侧边栏底部用户区 -->
        <div class="sidebar-footer" v-if="userStore.isLoggedIn">
          <div class="user-avatar">{{ (userStore.username || 'U').charAt(0).toUpperCase() }}</div>
          <div class="user-info">
            <span class="user-name">{{ userStore.username }}</span>
            <span class="user-role">在线</span>
          </div>
          <el-button class="logout-btn" link @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
          </el-button>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <el-header class="app-header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="currentRoute">{{ currentRoute }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <div class="status-indicator">
              <span class="status-dot"></span>
              <span class="status-text">系统运行中</span>
            </div>
          </div>
        </el-header>

        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="page-fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isPublicRoute = computed(() => !!route.meta.public)

const activeMenu = computed(() => route.path)

const routeNameMap = {
  '/': '情绪仪表盘',
  '/stocks': '股票列表',
  '/trend': '趋势分析',
  '/validation': '市场验证',
  '/sentiment': '情感分析',
  '/experiment': '实验对比',
  '/alerts': '情绪预警',
  '/settings': '系统设置'
}

const currentRoute = computed(() => {
  const path = route.path
  if (path === '/') return ''
  return routeNameMap[path] || path
})

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style>
/* ========== 主布局 ========== */
.app-container {
  height: 100%;
}

.app-aside {
  background-color: var(--bg-deep) !important;
  border-right: 1px solid var(--border-base);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ========== Logo ========== */
.logo {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  border-bottom: 1px solid var(--border-base);
  flex-shrink: 0;
}

.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--accent), #0080ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.logo-sub {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

/* ========== 侧边栏菜单 ========== */
.app-menu {
  background-color: transparent !important;
  border-right: none !important;
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
}

.app-menu .el-menu-item {
  height: 44px;
  line-height: 44px;
  margin-bottom: 2px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary) !important;
  transition: all var(--transition-base);
  font-size: 14px;
}

.app-menu .el-menu-item:hover {
  background-color: var(--accent-soft) !important;
  color: var(--text-primary) !important;
}

.app-menu .el-menu-item.is-active {
  background: linear-gradient(90deg, var(--accent-soft), transparent) !important;
  color: var(--accent) !important;
  position: relative;
}

.app-menu .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 8px var(--accent-glow);
}

.app-menu .el-menu-item .el-icon {
  font-size: 18px;
  margin-right: 8px;
}

/* ========== 侧边栏底部用户区 ========== */
.sidebar-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-base);
  background-color: rgba(0, 0, 0, 0.15);
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #0080ff);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.user-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11px;
  color: var(--bull);
}

.logout-btn {
  color: var(--text-muted) !important;
  font-size: 18px !important;
  padding: 4px !important;
}
.logout-btn:hover {
  color: var(--bear) !important;
}

/* ========== 顶部栏 ========== */
.app-header {
  background-color: var(--bg-deep) !important;
  border-bottom: 1px solid var(--border-base) !important;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px !important;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--bull);
  box-shadow: 0 0 8px var(--bull-glow);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-display);
  letter-spacing: 0.5px;
}

/* ========== 主内容区 ========== */
.app-main {
  background-color: var(--bg-base) !important;
  padding: 24px !important;
  overflow-y: auto;
}

/* ========== 页面切换动画 ========== */
.page-fade-enter-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-fade-leave-active {
  transition: opacity 0.15s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-fade-leave-to {
  opacity: 0;
}
</style>
