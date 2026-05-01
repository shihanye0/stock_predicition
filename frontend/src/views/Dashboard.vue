<template>
  <div class="dashboard">
    <!-- 预警通知栏 -->
    <div v-if="recentAlerts.length" class="alert-banner">
      <el-alert
        v-for="alert in recentAlerts.slice(0, 3)"
        :key="alert.id"
        :title="alert.title"
        :type="alert.severity === 'high' ? 'error' : 'warning'"
        :description="alert.message"
        show-icon
        closable
        class="alert-item"
        @close="dismissAlert(alert)"
      />
      <div v-if="alertStats.unread > 3" class="alert-more">
        <el-button type="primary" link @click="$router.push('/alerts')">
          还有 {{ alertStats.unread - 3 }} 条未读预警，查看全部 →
        </el-button>
      </div>
    </div>

    <!-- 数据初始化操作栏 -->
    <div class="action-bar">
      <el-space>
        <el-button
          type="primary"
          :loading="loadingDemo"
          @click="initDemoData"
        >
          <el-icon v-if="!loadingDemo"><TrendCharts /></el-icon>
          生成演示数据
        </el-button>
        <el-button
          :loading="loadingCrawl"
          :disabled="crawlerStatus.is_running"
          @click="startCrawl"
        >
          <el-icon v-if="!loadingCrawl && !crawlerStatus.is_running"><Upload /></el-icon>
          爬取真实数据
        </el-button>
        <el-button
          v-if="crawlerStatus.is_running || loadingCrawl"
          type="danger"
          :loading="loadingStop"
          @click="stopCrawl"
        >
          <el-icon v-if="!loadingStop"><CircleClose /></el-icon>
          停止爬虫
        </el-button>
      </el-space>
      <span v-if="dataStatus.comments > 0" class="data-hint">
        {{ dataStatus.stocks || 0 }}只股票 | {{ dataStatus.comments }}条评论
      </span>
    </div>

    <!-- 顶部统计卡片 -->
    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <div class="stat-card stat-bull">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.avg_bull_index || 0 }}<span class="unit">%</span></div>
            <div class="stat-label">看涨指数</div>
          </div>
          <div class="stat-decoration"></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-bear">
          <div class="stat-icon">
            <el-icon><Bottom /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.avg_bear_index || 0 }}<span class="unit">%</span></div>
            <div class="stat-label">看跌指数</div>
          </div>
          <div class="stat-decoration"></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-sentiment">
          <div class="stat-icon">
            <el-icon><Histogram /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ sentimentLabel }}</div>
            <div class="stat-label">市场情绪</div>
          </div>
          <div class="stat-decoration"></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-total">
          <div class="stat-icon">
            <el-icon><ChatLineRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(totalComments) }}</div>
            <div class="stat-label">评论总数</div>
          </div>
          <div class="stat-decoration"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>情绪趋势</span>
              <div class="trend-controls">
                <el-radio-group v-model="trendDays" size="small" @change="fetchTrend">
                  <el-radio-button :value="7">近7天</el-radio-button>
                  <el-radio-button :value="14">近14天</el-radio-button>
                  <el-radio-button :value="30">近30天</el-radio-button>
                </el-radio-group>
                <el-tooltip content="减少数据点以优化显示" placement="top">
                  <el-select v-model="trendDensity" size="small" style="width: 80px; margin-left: 8px;" @change="handleDensityChange">
                    <el-option label="全部" :value="0" />
                    <el-option label="100条" :value="100" />
                    <el-option label="50条" :value="50" />
                    <el-option label="20条" :value="20" />
                  </el-select>
                </el-tooltip>
              </div>
            </div>
          </template>
          <div v-if="trendData.length > 0">
            <v-chart :option="trendChartOption" autoresize style="height: 350px" />
          </div>
          <el-empty v-else description="暂无趋势数据" :image-size="120" style="height: 350px; display: flex; align-items: center; justify-content: center;" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>情绪分布</span>
          </template>
          <div v-if="overview.avg_bull_index">
            <v-chart :option="pieChartOption" autoresize style="height: 350px" />
          </div>
          <el-empty v-else description="暂无分布数据" :image-size="120" style="height: 350px; display: flex; align-items: center; justify-content: center;" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 热门股票排行 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>热门股票情绪排行</span>
          <el-button type="primary" link @click="$router.push('/stocks')">查看更多</el-button>
        </div>
      </template>
      <el-table :data="hotStocks" style="width: 100%">
        <el-table-column prop="stock_code" label="代码" width="100">
          <template #default="{ row }">
            <span class="code-text">{{ row.stock_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="stock_name" label="名称" width="120" />
        <el-table-column prop="bull_index" label="看涨指数" width="180">
          <template #default="{ row }">
            <el-progress
              :percentage="row.bull_index"
              :color="'#00e676'"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="bear_index" label="看跌指数" width="180">
          <template #default="{ row }">
            <el-progress
              :percentage="row.bear_index"
              :color="'#ff5252'"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="comment_count" label="评论数" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link @click="goToStock(row.stock_code)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { emotionApi, alertApi, adminApi, crawlerApi } from '@/api'
import { darkChartTheme, darkAxisStyle, chartColors, buildLineSeries, buildPieOption } from '@/utils/chart-theme'

const router = useRouter()

const overview = ref({})
const trendData = ref([])
const hotStocks = ref([])
const trendDays = ref(7)
const trendDensity = ref(0) // 0 means all data
const recentAlerts = ref([])
const alertStats = ref({})
const dataStatus = ref({ comments: 0 })
const loadingDemo = ref(false)
const loadingCrawl = ref(false)
const crawlerStatus = ref({ status: 'stopped' })
const loadingStop = ref(false)
let pollInterval = null

const sentimentLabel = computed(() => {
  const sentiment = overview.value.market_sentiment
  if (sentiment === 'bullish') return '看涨'
  if (sentiment === 'bearish') return '看跌'
  return '中性'
})

const totalComments = computed(() => {
  return dataStatus.value.comments || 0
})

// 趋势图表配置
const trendChartOption = computed(() => {
  const trendLen = trendData.value.length
  // 根据数据点数量动态调整X轴标签
  const showAllLabels = trendLen <= 10
  const axisLabelConfig = showAllLabels ? {} : { interval: 0, rotate: 45 }

  return {
    ...darkChartTheme,
    legend: { ...darkChartTheme.legend, data: ['看涨指数', '看跌指数'] },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trendData.value.map(item => item.date),
      axisLabel: {
        color: '#8b95a5',
        ...axisLabelConfig
      },
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)' } },
      axisTick: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)' } },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.04)' } }
    },
    yAxis: { type: 'value', max: 100, ...darkAxisStyle },
    series: [
      buildLineSeries('看涨指数', chartColors.bull, trendData.value.map(item => item.bull_index), { area: true }),
      buildLineSeries('看跌指数', chartColors.bear, trendData.value.map(item => item.bear_index), { area: true })
    ]
  }
})

// 饼图配置
const pieChartOption = computed(() => {
  return buildPieOption([
    { value: overview.value.avg_bull_index || 50, name: '看涨', itemStyle: { color: chartColors.bull } },
    { value: 100 - (overview.value.avg_bull_index || 50) - (overview.value.avg_bear_index || 30), name: '中性', itemStyle: { color: chartColors.neutral } },
    { value: overview.value.avg_bear_index || 30, name: '看跌', itemStyle: { color: chartColors.bear } }
  ])
})

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  return num.toString()
}

const fetchOverview = async () => {
  try {
    const res = await emotionApi.getOverview()
    overview.value = res.data || {}
    hotStocks.value = res.data?.hot_stocks || []
  } catch (error) {
    // 静默处理
  }
}

const fetchTrend = async () => {
  try {
    const endDate = new Date().toISOString().split('T')[0]
    const startDate = new Date(Date.now() - trendDays.value * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    const res = await emotionApi.getTrend({
      start_date: startDate,
      end_date: endDate,
      granularity: 'day',
      limit: trendDensity.value || undefined
    })
    let trend = res.data?.trend || []
    // Frontend sampling if backend doesn't support limit
    if (trendDensity.value > 0 && trend.length > trendDensity.value) {
      const step = Math.ceil(trend.length / trendDensity.value)
      trend = trend.filter((_, i) => i % step === 0)
    }
    trendData.value = trend
  } catch (error) {
    // 静默处理
  }
}

const handleDensityChange = () => {
  fetchTrend()
}

const goToStock = (code) => {
  router.push(`/stock/${code}`)
}

const fetchAlerts = async () => {
  try {
    const [alertsRes, statsRes] = await Promise.all([
      alertApi.getAlerts({ is_read: 0, page_size: 5 }),
      alertApi.getStats({ days: 7 })
    ])
    recentAlerts.value = alertsRes.data || []
    alertStats.value = statsRes.data || {}
  } catch (error) {
    // 静默处理
  }
}

const dismissAlert = async (alert) => {
  try {
    await alertApi.markRead(alert.id)
    recentAlerts.value = recentAlerts.value.filter(a => a.id !== alert.id)
  } catch (e) { /* ignore */ }
}

const fetchDataStatus = async () => {
  try {
    const res = await adminApi.getDataStatus()
    dataStatus.value = res.data || {}
  } catch (error) {
    // 静默处理
  }
}

const initDemoData = async () => {
  loadingDemo.value = true
  try {
    const res = await adminApi.initDemo()
    if (res.data) {
      const stocksAdded = res.data.stocks_added || 0
      const stocksTotal = res.data.stocks_total || 0
      const comments = res.data.comments || 0
      let msg = `数据生成成功！`
      if (stocksAdded > 0) {
        msg += `新增 ${stocksAdded} 只股票，`
      }
      msg += `股票总数 ${stocksTotal}，评论 ${comments} 条`
      ElMessage.success(msg)
      // 刷新数据
      await fetchDataStatus()
      await fetchOverview()
      await fetchTrend()
    }
  } catch (error) {
    ElMessage.error('生成演示数据失败')
  } finally {
    loadingDemo.value = false
  }
}

// 爬虫轮询间隔 3秒
const POLL_INTERVAL_MS = 3000

// 计算7天前的日期
const getDateNDaysAgo = (days) => {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return date.toISOString().split('T')[0]
}

const startCrawl = async () => {
  loadingCrawl.value = true
  try {
    const res = await adminApi.startCrawl({
      platform: 'eastmoney',
      stock_codes: [],
      start_date: getDateNDaysAgo(7),
      end_date: getDateNDaysAgo(0)
    })
    if (res.message) {
      ElMessage.success(res.message)
    } else {
      ElMessage.info('爬虫任务已启动')
    }
    startPolling()
  } catch (error) {
    ElMessage.error('启动爬虫失败')
  } finally {
    loadingCrawl.value = false
  }
}

const fetchCrawlerStatus = async () => {
  try {
    const { data } = await crawlerApi.getStatus('eastmoney') || {}
    const isRunning = data?.is_running || data?.status === 'running'

    crawlerStatus.value = {
      status: data?.status || 'stopped',
      is_running: isRunning
    }

    if (!isRunning) {
      stopPolling()
      await Promise.all([fetchDataStatus(), fetchOverview()])
    }
  } catch {
    // ignore
  }
}

const startPolling = () => {
  fetchCrawlerStatus()
  pollInterval = setInterval(fetchCrawlerStatus, POLL_INTERVAL_MS)
}

const stopPolling = () => {
  clearInterval(pollInterval)
  pollInterval = null
}

const stopCrawl = async () => {
  loadingStop.value = true
  try {
    await crawlerApi.stop('eastmoney')
    ElMessage.success('爬虫已停止')
    stopPolling()
    await Promise.all([fetchCrawlerStatus(), fetchDataStatus()])
  } catch (error) {
    ElMessage.error('停止爬虫失败')
  } finally {
    loadingStop.value = false
  }
}

onMounted(() => {
  fetchDataStatus()
  fetchOverview()
  fetchTrend()
  fetchAlerts()
  fetchCrawlerStatus()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.dashboard {
  min-height: 100%;
}

/* ========== 操作栏 ========== */
.action-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-base);
  border-radius: var(--radius-md);
}

.data-hint {
  color: var(--text-muted);
  font-size: 13px;
}

/* ========== 统计卡片 ========== */
.stat-cards {
  margin-bottom: 16px;
}

.stat-card {
  padding: 20px;
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  border: 1px solid var(--border-base);
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition: all var(--transition-base);
}

.stat-card:hover {
  border-color: var(--border-accent);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-bull .stat-icon { background: var(--bull-soft); color: var(--bull); }
.stat-bear .stat-icon { background: var(--bear-soft); color: var(--bear); }
.stat-sentiment .stat-icon { background: var(--accent-soft); color: var(--accent); }
.stat-total .stat-icon { background: var(--info-soft); color: var(--info); }

.stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-value .unit {
  font-size: 16px;
  color: var(--text-secondary);
  margin-left: 2px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 装饰光晕 */
.stat-decoration {
  position: absolute;
  right: -20px;
  top: -20px;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  opacity: 0.06;
}
.stat-bull .stat-decoration { background: var(--bull); }
.stat-bear .stat-decoration { background: var(--bear); }
.stat-sentiment .stat-decoration { background: var(--accent); }
.stat-total .stat-decoration { background: var(--info); }

/* ========== 图表区 ========== */
.chart-row {
  margin-bottom: 16px;
}

.chart-card {
  border-radius: var(--radius-md);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trend-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ========== 表格增强 ========== */
.code-text {
  font-family: var(--font-display);
  color: var(--accent);
  font-size: 13px;
}

/* ========== 预警横幅 ========== */
.alert-banner {
  margin-bottom: 16px;
}

.alert-item {
  margin-bottom: 8px;
}

.alert-more {
  text-align: center;
  margin-top: 4px;
}
</style>
