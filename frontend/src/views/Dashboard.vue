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

    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon bull">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.avg_bull_index || 0 }}%</div>
              <div class="stat-label">看涨指数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon bear">
              <el-icon><Bottom /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.avg_bear_index || 0 }}%</div>
              <div class="stat-label">看跌指数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon sentiment" :class="sentimentClass">
              <el-icon><Histogram /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ sentimentLabel }}</div>
              <div class="stat-label">市场情绪</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><ChatLineRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(totalComments) }}</div>
              <div class="stat-label">评论总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>情绪趋势</span>
              <el-radio-group v-model="trendDays" size="small" @change="fetchTrend">
                <el-radio-button :label="7">近7天</el-radio-button>
                <el-radio-button :label="14">近14天</el-radio-button>
                <el-radio-button :label="30">近30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <v-chart :option="trendChartOption" autoresize style="height: 350px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>情绪分布</span>
          </template>
          <v-chart :option="pieChartOption" autoresize style="height: 350px" />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 热门股票排行 -->
    <el-row :gutter="20" class="table-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>热门股票情绪排行</span>
              <el-button type="primary" link @click="$router.push('/stocks')">查看更多</el-button>
            </div>
          </template>
          <el-table :data="hotStocks" style="width: 100%">
            <el-table-column prop="stock_code" label="代码" width="100" />
            <el-table-column prop="stock_name" label="名称" width="120" />
            <el-table-column prop="bull_index" label="看涨指数" width="120">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.bull_index" 
                  :color="'#67C23A'"
                  :stroke-width="10"
                />
              </template>
            </el-table-column>
            <el-table-column prop="bear_index" label="看跌指数" width="120">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.bear_index" 
                  :color="'#F56C6C'"
                  :stroke-width="10"
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
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { emotionApi, alertApi } from '@/api'

const router = useRouter()

// 数据
const overview = ref({})
const trendData = ref([])
const hotStocks = ref([])
const trendDays = ref(7)
const recentAlerts = ref([])
const alertStats = ref({})

// 计算属性
const sentimentClass = computed(() => {
  const sentiment = overview.value.market_sentiment
  if (sentiment === 'bullish') return 'bull'
  if (sentiment === 'bearish') return 'bear'
  return 'neutral'
})

const sentimentLabel = computed(() => {
  const sentiment = overview.value.market_sentiment
  if (sentiment === 'bullish') return '看涨'
  if (sentiment === 'bearish') return '看跌'
  return '中性'
})

const totalComments = computed(() => {
  return trendData.value.reduce((sum, item) => sum + (item.comment_count || 0), 0)
})

// 趋势图表配置
const trendChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['看涨指数', '看跌指数']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: trendData.value.map(item => item.date)
  },
  yAxis: {
    type: 'value',
    max: 100
  },
  series: [
    {
      name: '看涨指数',
      type: 'line',
      smooth: true,
      itemStyle: { color: '#67C23A' },
      areaStyle: { color: 'rgba(103, 194, 58, 0.2)' },
      data: trendData.value.map(item => item.bull_index)
    },
    {
      name: '看跌指数',
      type: 'line',
      smooth: true,
      itemStyle: { color: '#F56C6C' },
      areaStyle: { color: 'rgba(245, 108, 108, 0.2)' },
      data: trendData.value.map(item => item.bear_index)
    }
  ]
}))

// 饼图配置
const pieChartOption = computed(() => {
  const lastData = trendData.value[trendData.value.length - 1] || {}
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      bottom: '5%'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        data: [
          { value: overview.value.avg_bull_index || 50, name: '看涨', itemStyle: { color: '#67C23A' } },
          { value: 100 - (overview.value.avg_bull_index || 50) - (overview.value.avg_bear_index || 30), name: '中性', itemStyle: { color: '#E6A23C' } },
          { value: overview.value.avg_bear_index || 30, name: '看跌', itemStyle: { color: '#F56C6C' } }
        ]
      }
    ]
  }
})

// 方法
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
    trendData.value = res.data?.recent_trend || []
  } catch (error) {
    console.error('Fetch overview error:', error)
  }
}

const fetchTrend = async () => {
  try {
    const endDate = new Date().toISOString().split('T')[0]
    const startDate = new Date(Date.now() - trendDays.value * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    
    const res = await emotionApi.getTrend({
      start_date: startDate,
      end_date: endDate,
      granularity: 'day'
    })
    trendData.value = res.data?.trend || []
  } catch (error) {
    console.error('Fetch trend error:', error)
  }
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
    console.error('Fetch alerts error:', error)
  }
}

const dismissAlert = async (alert) => {
  try {
    await alertApi.markRead(alert.id)
    recentAlerts.value = recentAlerts.value.filter(a => a.id !== alert.id)
  } catch (e) { /* ignore */ }
}

// 生命周期
onMounted(() => {
  fetchOverview()
  fetchAlerts()
})
</script>

<style scoped>
.dashboard {
  min-height: 100%;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-icon.bull {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67C23A;
}

.stat-icon.bear {
  background-color: rgba(245, 108, 108, 0.1);
  color: #F56C6C;
}

.stat-icon.neutral {
  background-color: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
}

.stat-icon.sentiment {
  background-color: rgba(64, 158, 255, 0.1);
  color: #409EFF;
}

.stat-icon.total {
  background-color: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-row, .table-row {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

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
