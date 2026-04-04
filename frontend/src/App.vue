<template>
  <el-config-provider :locale="zhCn">
    <el-container class="app-container">
      <!-- 侧边栏 -->
      <el-aside width="220px" class="app-aside">
        <div class="logo">
          <el-icon><TrendCharts /></el-icon>
          <span>股票情绪预测</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="app-menu"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
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
            <el-tag type="success" effect="plain">系统运行中</el-tag>
          </div>
        </el-header>
        
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const route = useRoute()

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
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.app-container {
  height: 100%;
}

.app-aside {
  background-color: #304156;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #3d4a5e;
}

.logo .el-icon {
  font-size: 24px;
  color: #409EFF;
}

.app-menu {
  border-right: none;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.app-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
