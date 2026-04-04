<template>
  <div class="trend-page">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="股票">
          <el-input v-model="stockCode" placeholder="输入股票代码" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="粒度">
          <el-select v-model="granularity">
            <el-option label="小时" value="hour" />
            <el-option label="日" value="day" />
            <el-option label="周" value="week" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchTrend">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="chart-card">
      <template #header>
        <span>情绪趋势分析</span>
      </template>
      <v-chart :option="chartOption" autoresize style="height: 450px" />
    </el-card>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>情绪指标统计</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="平均看涨指数">
              {{ stats.avgBull.toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="平均看跌指数">
              {{ stats.avgBear.toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="最高看涨指数">
              {{ stats.maxBull.toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="最高看跌指数">
              {{ stats.maxBear.toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="平均情绪温度">
              {{ stats.avgTemp.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="数据点数">
              {{ trendData.length }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>情绪变化分析</span>
          </template>
          <div class="analysis-content">
            <p v-if="trendData.length > 1">
              <strong>趋势判断：</strong>
              <el-tag :type="trendDirection === 'up' ? 'success' : trendDirection === 'down' ? 'danger' : 'info'">
                {{ trendDirectionText }}
              </el-tag>
            </p>
            <p>
              <strong>波动率：</strong>
              {{ volatility.toFixed(4) }}
              <el-tag :type="volatility > 0.3 ? 'danger' : 'success'" size="small">
                {{ volatility > 0.3 ? '高波动' : '低波动' }}
              </el-tag>
            </p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { emotionApi } from '@/api'
import dayjs from 'dayjs'

const stockCode = ref('')
const dateRange = ref([
  dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD')
])
const granularity = ref('day')
const trendData = ref([])

const stats = computed(() => {
  if (trendData.value.length === 0) {
    return { avgBull: 0, avgBear: 0, maxBull: 0, maxBear: 0, avgTemp: 0 }
  }
  const bulls = trendData.value.map(d => d.bull_index || 0)
  const bears = trendData.value.map(d => d.bear_index || 0)
  const temps = trendData.value.map(d => d.temperature || 0)
  
  return {
    avgBull: bulls.reduce((a, b) => a + b, 0) / bulls.length,
    avgBear: bears.reduce((a, b) => a + b, 0) / bears.length,
    maxBull: Math.max(...bulls),
    maxBear: Math.max(...bears),
    avgTemp: temps.reduce((a, b) => a + b, 0) / temps.length
  }
})

const volatility = computed(() => {
  if (trendData.value.length < 2) return 0
  const intensities = trendData.value.map(d => d.intensity || 0)
  const mean = intensities.reduce((a, b) => a + b, 0) / intensities.length
  const variance = intensities.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / intensities.length
  return Math.sqrt(variance)
})

const trendDirection = computed(() => {
  if (trendData.value.length < 2) return 'neutral'
  const recent = trendData.value.slice(-3)
  const older = trendData.value.slice(0, 3)
  const recentAvg = recent.reduce((a, b) => a + (b.intensity || 0), 0) / recent.length
  const olderAvg = older.reduce((a, b) => a + (b.intensity || 0), 0) / older.length
  if (recentAvg > olderAvg + 0.1) return 'up'
  if (recentAvg < olderAvg - 0.1) return 'down'
  return 'neutral'
})

const trendDirectionText = computed(() => {
  if (trendDirection.value === 'up') return '情绪上升'
  if (trendDirection.value === 'down') return '情绪下降'
  return '情绪平稳'
})

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['看涨指数', '看跌指数', '情绪温度'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: trendData.value.map(item => item.date)
  },
  yAxis: { type: 'value', max: 100 },
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
    },
    {
      name: '情绪温度',
      type: 'line',
      smooth: true,
      itemStyle: { color: '#409EFF' },
      data: trendData.value.map(item => item.temperature)
    }
  ]
}))

const fetchTrend = async () => {
  try {
    const [startDate, endDate] = dateRange.value
    const res = await emotionApi.getTrend({
      stock_code: stockCode.value || undefined,
      start_date: startDate,
      end_date: endDate,
      granularity: granularity.value
    })
    trendData.value = res.data?.trend || []
  } catch (error) {
    console.error('Fetch trend error:', error)
  }
}
</script>

<style scoped>
.trend-page {
  min-height: 100%;
}

.filter-card {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.analysis-content {
  line-height: 2;
}
</style>
