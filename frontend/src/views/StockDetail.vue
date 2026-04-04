<template>
  <div class="stock-detail">
    <!-- 股票信息卡片 -->
    <el-card class="info-card">
      <div class="stock-info">
        <div class="info-main">
          <h2>{{ stockInfo.stock_name || '--' }}</h2>
          <span class="stock-code">{{ stockInfo.stock_code || '--' }}</span>
          <el-tag :type="stockInfo.market === 'SH' ? 'danger' : 'primary'" class="market-tag">
            {{ stockInfo.market }}
          </el-tag>
        </div>
        <div class="info-stats">
          <div class="stat-item">
            <span class="label">看涨指数</span>
            <span class="value bull">{{ emotionSummary.avg_bull_index || 0 }}%</span>
          </div>
          <div class="stat-item">
            <span class="label">看跌指数</span>
            <span class="value bear">{{ emotionSummary.avg_bear_index || 0 }}%</span>
          </div>
          <div class="stat-item">
            <span class="label">情绪强度</span>
            <span class="value">{{ (emotionSummary.avg_intensity * 100).toFixed(2) || 0 }}%</span>
          </div>
          <div class="stat-item">
            <span class="label">评论总数</span>
            <span class="value">{{ emotionSummary.total_comments || 0 }}</span>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>情绪趋势</span>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                @change="handleDateChange"
              />
            </div>
          </template>
          <v-chart :option="trendChartOption" autoresize style="height: 350px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>情感分布</span>
          </template>
          <v-chart :option="pieChartOption" autoresize style="height: 350px" />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 方面分析 + 情绪画像 -->
    <el-row :gutter="20" class="profile-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>方面级情感分析</span>
              <el-button type="primary" link @click="fetchAspects" :loading="aspectsLoading">刷新</el-button>
            </div>
          </template>
          <v-chart v-if="aspectRadarOption" :option="aspectRadarOption" autoresize style="height: 300px" />
          <el-empty v-else description="暂无方面分析数据" />
          <div v-if="aspectsList.length" class="aspect-tags">
            <div v-for="asp in aspectsList" :key="asp.aspect" class="aspect-item">
              <span class="aspect-name">{{ asp.aspect }}</span>
              <el-progress :percentage="((asp.positive_ratio || 0) * 100).toFixed(0) * 1" :color="'#67C23A'" :stroke-width="8" style="width: 100px; display: inline-flex; margin: 0 8px;" />
              <span class="aspect-count">{{ asp.total }}条</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>情绪画像</span>
              <el-button type="primary" link @click="fetchProfile" :loading="profileLoading">刷新</el-button>
            </div>
          </template>
          <v-chart v-if="profileRadarOption" :option="profileRadarOption" autoresize style="height: 280px" />
          <el-empty v-else description="暂无情绪画像数据" />
          <div v-if="profileData.tags && profileData.tags.length" class="profile-tags">
            <el-tag v-for="tag in profileData.tags" :key="tag" effect="plain" class="profile-tag"
              :type="getTagType(tag)">{{ tag }}</el-tag>
          </div>
          <div v-if="profileData.statistics" class="profile-stats">
            <span>日均评论: {{ profileData.statistics?.daily_avg_comments || 0 }}</span>
            <span>情绪温度: {{ profileData.statistics?.avg_temperature || 0 }}%</span>
            <span>价格关联: {{ ((profileData.price_correlation || 0) * 100).toFixed(1) }}%</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 评论列表 -->
    <el-card class="comment-card">
      <template #header>
        <div class="card-header">
          <span>最新评论</span>
          <el-select v-model="commentFilters.platform" placeholder="全部平台" clearable @change="fetchComments">
            <el-option label="东方财富" value="eastmoney" />
            <el-option label="雪球" value="xueqiu" />
            <el-option label="新浪财经" value="sina" />
          </el-select>
        </div>
      </template>
      
      <el-table :data="comments" v-loading="commentsLoading">
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="platform" label="平台" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getPlatformName(row.platform) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sentiment_label" label="情感" width="80">
          <template #default="{ row }">
            <el-tag 
              :type="getSentimentType(row.sentiment_label)" 
              size="small"
            >
              {{ getSentimentLabel(row.sentiment_label) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="100" />
        <el-table-column prop="publish_time" label="时间" width="160" />
      </el-table>
      
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="commentPagination.page"
          :total="commentPagination.total"
          :page-size="commentPagination.pageSize"
          layout="prev, pager, next"
          @current-change="fetchComments"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import VChart from 'vue-echarts'
import { stockApi } from '@/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const route = useRoute()
const stockCode = computed(() => route.params.code)

// 数据
const stockInfo = ref({})
const emotionData = ref({})
const emotionTrend = ref([])
const comments = ref([])
const commentsLoading = ref(false)

const emotionSummary = computed(() => emotionData.value.summary || {})

// 方面分析数据
const aspectsData = ref({})
const aspectsList = computed(() => aspectsData.value.aspects || [])
const aspectsLoading = ref(false)

// 情绪画像数据
const profileData = ref({})
const profileLoading = ref(false)

const dateRange = ref([
  dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD')
])

const commentFilters = reactive({
  platform: ''
})

const commentPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 方面雷达图
const aspectRadarOption = computed(() => {
  const aspects = aspectsList.value
  if (!aspects.length) return null
  return {
    radar: {
      indicator: aspects.map(a => ({ name: a.aspect, max: Math.max(...aspects.map(x => x.total), 10) }))
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: aspects.map(a => a.positive || 0),
          name: '积极',
          areaStyle: { color: 'rgba(103, 194, 58, 0.3)' },
          lineStyle: { color: '#67C23A' }
        },
        {
          value: aspects.map(a => a.negative || 0),
          name: '消极',
          areaStyle: { color: 'rgba(245, 108, 108, 0.3)' },
          lineStyle: { color: '#F56C6C' }
        }
      ]
    }],
    legend: { data: ['积极', '消极'], bottom: 0 }
  }
})

// 情绪画像雷达图
const profileRadarOption = computed(() => {
  const radar = profileData.value.radar_data
  if (!radar || !radar.indicators) return null
  return {
    radar: { indicator: radar.indicators },
    series: [{
      type: 'radar',
      data: [{
        value: radar.values,
        name: '情绪特征',
        areaStyle: { color: 'rgba(64, 158, 255, 0.3)' },
        lineStyle: { color: '#409EFF' }
      }]
    }]
  }
})

const getTagType = (tag) => {
  if (tag.includes('多头') || tag.includes('升温') || tag.includes('高关注')) return 'success'
  if (tag.includes('空头') || tag.includes('降温') || tag.includes('敏感')) return 'danger'
  return 'info'
}

// 图表配置
const trendChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['看涨指数', '看跌指数', '情绪温度']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: emotionTrend.value.map(item => item.date)
  },
  yAxis: [
    { type: 'value', max: 100 }
  ],
  series: [
    {
      name: '看涨指数',
      type: 'line',
      smooth: true,
      itemStyle: { color: '#67C23A' },
      data: emotionTrend.value.map(item => item.bull_index)
    },
    {
      name: '看跌指数',
      type: 'line',
      smooth: true,
      itemStyle: { color: '#F56C6C' },
      data: emotionTrend.value.map(item => item.bear_index)
    },
    {
      name: '情绪温度',
      type: 'line',
      smooth: true,
      itemStyle: { color: '#409EFF' },
      data: emotionTrend.value.map(item => item.temperature)
    }
  ]
}))

const pieChartOption = computed(() => {
  const summary = emotionSummary.value
  const total = (summary.total_comments || 1)
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
        data: [
          { value: summary.avg_bull_index || 33, name: '看涨', itemStyle: { color: '#67C23A' } },
          { value: 100 - (summary.avg_bull_index || 33) - (summary.avg_bear_index || 33), name: '中性', itemStyle: { color: '#E6A23C' } },
          { value: summary.avg_bear_index || 33, name: '看跌', itemStyle: { color: '#F56C6C' } }
        ]
      }
    ]
  }
})

// 方法
const getPlatformName = (platform) => {
  const map = {
    'eastmoney': '东方财富',
    'xueqiu': '雪球',
    'sina': '新浪财经'
  }
  return map[platform] || platform
}

const getSentimentType = (label) => {
  if (label === 'positive') return 'success'
  if (label === 'negative') return 'danger'
  return 'warning'
}

const getSentimentLabel = (label) => {
  if (label === 'positive') return '积极'
  if (label === 'negative') return '消极'
  return '中性'
}

const fetchAspects = async () => {
  aspectsLoading.value = true
  try {
    const res = await stockApi.getStockAspects(stockCode.value)
    aspectsData.value = res.data || {}
  } catch (error) {
    console.error('Fetch aspects error:', error)
  } finally {
    aspectsLoading.value = false
  }
}

const fetchProfile = async () => {
  profileLoading.value = true
  try {
    const res = await stockApi.getStockProfile(stockCode.value, { days: 30 })
    profileData.value = res.data || {}
  } catch (error) {
    console.error('Fetch profile error:', error)
  } finally {
    profileLoading.value = false
  }
}

const fetchStockInfo = async () => {
  try {
    const res = await stockApi.getStock(stockCode.value)
    stockInfo.value = res.data || {}
  } catch (error) {
    console.error('Fetch stock info error:', error)
  }
}

const fetchEmotion = async () => {
  try {
    const [startDate, endDate] = dateRange.value
    const res = await stockApi.getStockEmotion(stockCode.value, {
      start_date: startDate,
      end_date: endDate,
      granularity: 'day'
    })
    emotionData.value = res.data || {}
    emotionTrend.value = res.data?.trend || []
  } catch (error) {
    console.error('Fetch emotion error:', error)
  }
}

const fetchComments = async () => {
  commentsLoading.value = true
  try {
    const res = await stockApi.getStockComments(stockCode.value, {
      page: commentPagination.page,
      page_size: commentPagination.pageSize,
      platform: commentFilters.platform || undefined
    })
    comments.value = res.data || []
    commentPagination.total = res.total || 0
  } catch (error) {
    console.error('Fetch comments error:', error)
  } finally {
    commentsLoading.value = false
  }
}

const handleDateChange = () => {
  if (dateRange.value) {
    fetchEmotion()
  }
}

// 生命周期
onMounted(() => {
  fetchStockInfo()
  fetchEmotion()
  fetchComments()
  fetchAspects()
  fetchProfile()
})
</script>

<style scoped>
.stock-detail {
  min-height: 100%;
}

.info-card {
  margin-bottom: 20px;
}

.stock-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-main h2 {
  margin: 0;
  font-size: 24px;
}

.stock-code {
  color: #909399;
  font-size: 16px;
}

.info-stats {
  display: flex;
  gap: 40px;
}

.stat-item {
  text-align: center;
}

.stat-item .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-item .value {
  font-size: 20px;
  font-weight: bold;
}

.stat-item .value.bull {
  color: #67C23A;
}

.stat-item .value.bear {
  color: #F56C6C;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card, .comment-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.profile-row {
  margin-bottom: 20px;
}

.aspect-tags {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.aspect-item {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
}

.aspect-name {
  width: 50px;
  font-weight: bold;
  color: #303133;
}

.aspect-count {
  color: #909399;
  font-size: 12px;
}

.profile-tags {
  text-align: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.profile-tag {
  margin: 4px;
}

.profile-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
}
</style>
