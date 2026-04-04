<template>
  <div class="settings-page">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>爬虫管理</span>
          </template>
          
          <div class="crawler-list">
            <div v-for="crawler in crawlerStatuses" :key="crawler.platform" class="crawler-item">
              <div class="crawler-info">
                <span class="platform-name">{{ getPlatformName(crawler.platform) }}</span>
                <el-tag :type="getStatusType(crawler.status)" size="small">
                  {{ getStatusText(crawler.status) }}
                </el-tag>
              </div>
              <div class="crawler-stats">
                <span>已采集: {{ crawler.total_crawled || 0 }}</span>
                <span v-if="crawler.last_crawl_time">
                  最后采集: {{ formatTime(crawler.last_crawl_time) }}
                </span>
              </div>
              <div class="crawler-actions">
                <el-button 
                  type="primary" 
                  size="small"
                  :disabled="crawler.status === 'running'"
                  @click="startCrawler(crawler.platform)"
                >
                  启动
                </el-button>
                <el-button 
                  type="danger" 
                  size="small"
                  :disabled="crawler.status !== 'running'"
                  @click="stopCrawler(crawler.platform)"
                >
                  停止
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
        
        <el-card style="margin-top: 20px">
          <template #header>
            <span>爬虫统计</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="总评论数">
              {{ crawlerStats.total_comments || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="今日采集">
              {{ crawlerStats.today_crawled || 0 }}
            </el-descriptions-item>
          </el-descriptions>
          <div class="platform-stats" v-if="crawlerStats.platform_stats">
            <h4>各平台数据量</h4>
            <el-progress 
              v-for="(count, platform) in crawlerStats.platform_stats" 
              :key="platform"
              :text-inside="true" 
              :stroke-width="20"
              :percentage="getPlatformPercentage(count)"
            >
              <span>{{ getPlatformName(platform) }}: {{ count }}</span>
            </el-progress>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>启动爬虫任务</span>
          </template>
          <el-form :model="crawlerForm" label-width="100px">
            <el-form-item label="平台">
              <el-select v-model="crawlerForm.platform" placeholder="选择平台">
                <el-option label="东方财富" value="eastmoney" />
                <el-option label="雪球" value="xueqiu" />
                <el-option label="新浪财经" value="sina" />
              </el-select>
            </el-form-item>
            <el-form-item label="股票代码">
              <el-input 
                v-model="crawlerForm.stockCodes" 
                placeholder="多个代码用逗号分隔，留空则采集热门股票"
              />
            </el-form-item>
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="crawlerForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitCrawlerTask">
                提交任务
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card style="margin-top: 20px">
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统名称">
              股票情绪预测系统
            </el-descriptions-item>
            <el-descriptions-item label="版本">
              1.0.0
            </el-descriptions-item>
            <el-descriptions-item label="后端状态">
              <el-tag type="success">运行中</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { crawlerApi } from '@/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const crawlerStatuses = ref([])
const crawlerStats = ref({})
let refreshTimer = null

const crawlerForm = reactive({
  platform: 'eastmoney',
  stockCodes: '',
  dateRange: null
})

const getPlatformName = (platform) => {
  const map = {
    'eastmoney': '东方财富',
    'xueqiu': '雪球',
    'sina': '新浪财经'
  }
  return map[platform] || platform
}

const getStatusType = (status) => {
  if (status === 'running') return 'success'
  if (status === 'error') return 'danger'
  return 'info'
}

const getStatusText = (status) => {
  if (status === 'running') return '运行中'
  if (status === 'error') return '错误'
  return '已停止'
}

const formatTime = (time) => {
  if (!time) return '-'
  return dayjs(time).format('MM-DD HH:mm')
}

const getPlatformPercentage = (count) => {
  const total = crawlerStats.value.total_comments || 1
  return Math.min((count / total) * 100, 100)
}

const fetchStatus = async () => {
  try {
    const res = await crawlerApi.getStatus()
    crawlerStatuses.value = res.data?.crawlers || []
  } catch (error) {
    console.error('Fetch status error:', error)
  }
}

const fetchStats = async () => {
  try {
    const res = await crawlerApi.getStats()
    crawlerStats.value = res.data || {}
  } catch (error) {
    console.error('Fetch stats error:', error)
  }
}

const startCrawler = async (platform) => {
  try {
    await crawlerApi.start({ platform, stock_codes: [] })
    ElMessage.success(`${getPlatformName(platform)} 爬虫已启动`)
    fetchStatus()
  } catch (error) {
    ElMessage.error('启动失败')
  }
}

const stopCrawler = async (platform) => {
  try {
    await crawlerApi.stop(platform)
    ElMessage.success(`${getPlatformName(platform)} 爬虫已停止`)
    fetchStatus()
  } catch (error) {
    ElMessage.error('停止失败')
  }
}

const submitCrawlerTask = async () => {
  if (!crawlerForm.platform) {
    ElMessage.warning('请选择平台')
    return
  }
  
  const stockCodes = crawlerForm.stockCodes 
    ? crawlerForm.stockCodes.split(',').map(s => s.trim()).filter(s => s)
    : []
  
  const [startDate, endDate] = crawlerForm.dateRange || []
  
  try {
    await crawlerApi.start({
      platform: crawlerForm.platform,
      stock_codes: stockCodes,
      start_date: startDate,
      end_date: endDate
    })
    ElMessage.success('爬虫任务已提交')
    fetchStatus()
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

onMounted(() => {
  fetchStatus()
  fetchStats()
  refreshTimer = setInterval(() => {
    fetchStatus()
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.settings-page {
  min-height: 100%;
}

.crawler-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.crawler-item {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.crawler-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.platform-name {
  font-weight: bold;
  font-size: 16px;
}

.crawler-stats {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
  display: flex;
  gap: 16px;
}

.crawler-actions {
  display: flex;
  gap: 8px;
}

.platform-stats {
  margin-top: 20px;
}

.platform-stats h4 {
  margin-bottom: 12px;
  font-size: 14px;
}

.platform-stats .el-progress {
  margin-bottom: 8px;
}
</style>
