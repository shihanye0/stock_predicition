<template>
  <div class="alerts-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total"><el-icon><Bell /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total || 0 }}</div>
              <div class="stat-label">预警总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon unread"><el-icon><Message /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.unread || 0 }}</div>
              <div class="stat-label">未读预警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon high"><el-icon><WarningFilled /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_severity?.high || 0 }}</div>
              <div class="stat-label">高危预警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon medium"><el-icon><InfoFilled /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_severity?.medium || 0 }}</div>
              <div class="stat-label">中等预警</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作栏 -->
    <el-card class="action-card">
      <div class="action-bar">
        <div class="action-left">
          <el-select v-model="filters.severity" placeholder="严重程度" clearable @change="fetchAlerts" style="width: 120px">
            <el-option label="高危" value="high" />
            <el-option label="中等" value="medium" />
            <el-option label="低危" value="low" />
          </el-select>
          <el-select v-model="filters.alert_type" placeholder="预警类型" clearable @change="fetchAlerts" style="width: 160px">
            <el-option label="情绪强度突变" value="intensity_spike" />
            <el-option label="看涨极端" value="bull_extreme" />
            <el-option label="看跌极端" value="bear_extreme" />
            <el-option label="评论量暴增" value="volume_surge" />
            <el-option label="温度异常" value="temperature_anomaly" />
            <el-option label="趋势反转" value="sentiment_reversal" />
            <el-option label="舆情爆发" value="burst_activity" />
            <el-option label="行业联动" value="sector_linkage" />
            <el-option label="波动率异常" value="volatility_anomaly" />
            <el-option label="极值突破" value="new_high_low" />
          </el-select>
          <el-select v-model="filters.is_read" placeholder="已读状态" clearable @change="fetchAlerts" style="width: 120px">
            <el-option label="未读" :value="0" />
            <el-option label="已读" :value="1" />
          </el-select>
        </div>
        <div class="action-right">
          <el-button @click="markAllRead" :disabled="!stats.unread">全部标记已读</el-button>
          <el-button type="primary" @click="triggerScan" :loading="scanLoading">
            触发预警扫描
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 预警列表 -->
    <el-card>
      <el-table :data="alerts" v-loading="loading" @row-click="handleRowClick" row-class-name="alert-row">
        <el-table-column width="8">
          <template #default="{ row }">
            <div v-if="!row.is_read" class="unread-dot"></div>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small" effect="dark">
              {{ getSeverityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="stock_name" label="股票" width="120">
          <template #default="{ row }">
            <span class="stock-link" @click.stop="$router.push(`/stock/${row.stock_code}`)">
              {{ row.stock_name }} ({{ row.stock_code }})
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="预警标题" show-overflow-tooltip />
        <el-table-column prop="alert_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getAlertTypeName(row.alert_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="metric_value" label="指标值" width="80">
          <template #default="{ row }">
            {{ row.metric_value != null ? row.metric_value.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="triggered_at" label="触发时间" width="160">
          <template #default="{ row }">{{ row.triggered_at?.substring(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button v-if="!row.is_read" type="primary" link size="small" @click.stop="markRead(row)">
              已读
            </el-button>
            <span v-else class="read-label">已读</span>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          :total="pagination.total"
          :page-size="pagination.pageSize"
          layout="total, prev, pager, next"
          @current-change="fetchAlerts"
        />
      </div>
    </el-card>

    <!-- 预警详情对话框 -->
    <el-dialog v-model="detailVisible" title="预警详情" width="500px">
      <div v-if="selectedAlert" class="alert-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="股票">{{ selectedAlert.stock_name }} ({{ selectedAlert.stock_code }})</el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :type="getSeverityType(selectedAlert.severity)" effect="dark">{{ getSeverityLabel(selectedAlert.severity) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="类型">{{ getAlertTypeName(selectedAlert.alert_type) }}</el-descriptions-item>
          <el-descriptions-item label="标题">{{ selectedAlert.title }}</el-descriptions-item>
          <el-descriptions-item label="详情">{{ selectedAlert.message }}</el-descriptions-item>
          <el-descriptions-item label="指标值">{{ selectedAlert.metric_value?.toFixed(4) }}</el-descriptions-item>
          <el-descriptions-item label="阈值">{{ selectedAlert.threshold?.toFixed(4) }}</el-descriptions-item>
          <el-descriptions-item label="触发时间">{{ selectedAlert.triggered_at }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { alertApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const scanLoading = ref(false)
const alerts = ref([])
const stats = ref({})
const detailVisible = ref(false)
const selectedAlert = ref(null)

const filters = reactive({
  severity: '',
  alert_type: '',
  is_read: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getSeverityType = (s) => {
  if (s === 'high') return 'danger'
  if (s === 'medium') return 'warning'
  return 'info'
}

const getSeverityLabel = (s) => {
  if (s === 'high') return '高危'
  if (s === 'medium') return '中等'
  return '低危'
}

const getAlertTypeName = (type) => {
  const map = {
    'intensity_spike': '情绪突变',
    'bull_extreme': '看涨极端',
    'bear_extreme': '看跌极端',
    'volume_surge': '评论暴增',
    'temperature_anomaly': '温度异常',
    'sentiment_reversal': '趋势反转',
    'burst_activity': '舆情爆发',
    'sector_linkage': '行业联动',
    'volatility_anomaly': '波动率异常',
    'new_high_low': '极值突破'
  }
  return map[type] || type
}

const fetchAlerts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...filters
    }
    // 清除空值
    Object.keys(params).forEach(k => { if (params[k] === '' || params[k] === null) delete params[k] })
    
    const res = await alertApi.getAlerts(params)
    alerts.value = res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('Fetch alerts error:', error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await alertApi.getStats()
    stats.value = res.data || {}
  } catch (error) {
    console.error('Fetch stats error:', error)
  }
}

const markRead = async (alert) => {
  try {
    await alertApi.markRead(alert.id)
    alert.is_read = 1
    stats.value.unread = Math.max(0, (stats.value.unread || 0) - 1)
  } catch (error) {
    ElMessage.error('标记失败')
  }
}

const markAllRead = async () => {
  try {
    await alertApi.markAllRead()
    ElMessage.success('全部标记已读')
    fetchAlerts()
    fetchStats()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const triggerScan = async () => {
  scanLoading.value = true
  try {
    const res = await alertApi.scan()
    const count = res.data?.alerts_generated || 0
    ElMessage.success(`扫描完成，生成 ${count} 条预警`)
    fetchAlerts()
    fetchStats()
  } catch (error) {
    ElMessage.error('扫描失败')
  } finally {
    scanLoading.value = false
  }
}

const handleRowClick = (row) => {
  selectedAlert.value = row
  detailVisible.value = true
  if (!row.is_read) markRead(row)
}

onMounted(() => {
  fetchAlerts()
  fetchStats()
})
</script>

<style scoped>
.alerts-page { min-height: 100%; }

.stat-row { margin-bottom: 20px; }

.stat-card { border-radius: 8px; }

.stat-content { display: flex; align-items: center; gap: 16px; }

.stat-icon {
  width: 52px; height: 52px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; font-size: 24px;
}
.stat-icon.total { background: var(--accent-soft); color: var(--accent); }
.stat-icon.unread { background: var(--neutral-soft); color: var(--neutral); }
.stat-icon.high { background: var(--bear-soft); color: var(--bear); }
.stat-icon.medium { background: var(--info-soft); color: var(--info); }

.stat-value { font-size: 26px; font-weight: bold; color: var(--text-primary); font-family: var(--font-display); }
.stat-label { font-size: 13px; color: var(--text-muted); margin-top: 2px; }

.action-card { margin-bottom: 20px; }
.action-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.action-left { display: flex; gap: 10px; flex-wrap: wrap; }

.unread-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--bear); margin-top: 4px;
  box-shadow: 0 0 6px var(--bear-glow);
}

.stock-link { color: var(--accent); cursor: pointer; }
.stock-link:hover { text-decoration: underline; }

.read-label { color: var(--text-muted); font-size: 12px; }

.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }

.alert-detail { padding: 10px 0; }
</style>
