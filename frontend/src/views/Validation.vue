<template>
  <div class="validation-page">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="股票代码">
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
        <el-form-item>
          <el-button type="primary" @click="fetchValidation">分析</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>相关性分析</span>
          </template>
          <el-table :data="correlationData">
            <el-table-column prop="lag" label="领先天数" width="100" />
            <el-table-column prop="correlation" label="相关系数">
              <template #default="{ row }">
                <span :style="{ color: getCorrelationColor(row.correlation) }">
                  {{ row.correlation?.toFixed(4) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="significance" label="显著性">
              <template #default="{ row }">
                <el-tag :type="getSignificanceType(row.significance)">
                  {{ row.significance }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>预测准确率</span>
          </template>
          <div class="accuracy-display">
            <el-progress 
              type="dashboard" 
              :percentage="accuracy * 100" 
              :color="getAccuracyColor"
              :width="180"
            >
              <template #default>
                <span class="accuracy-value">{{ (accuracy * 100).toFixed(1) }}%</span>
              </template>
            </el-progress>
            <div class="accuracy-info">
              <p>正确预测: {{ correctCount }} 次</p>
              <p>总样本数: {{ totalCount }} 次</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="chart-card">
      <template #header>
        <span>情绪与行情对比</span>
      </template>
      <v-chart :option="chartOption" autoresize style="height: 400px" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { validationApi } from '@/api'
import dayjs from 'dayjs'

const stockCode = ref('000001')
const dateRange = ref([
  dayjs().subtract(90, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD')
])

const correlationData = ref([])
const accuracy = ref(0)
const correctCount = ref(0)
const totalCount = ref(0)
const comparisonData = ref([])

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['情绪强度', '涨跌幅'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: comparisonData.value.map(d => d.date)
  },
  yAxis: [
    { type: 'value', name: '情绪强度', position: 'left', min: -1, max: 1 },
    { type: 'value', name: '涨跌幅(%)', position: 'right' }
  ],
  series: [
    {
      name: '情绪强度',
      type: 'line',
      smooth: true,
      yAxisIndex: 0,
      itemStyle: { color: '#409EFF' },
      data: comparisonData.value.map(d => d.emotion_intensity)
    },
    {
      name: '涨跌幅',
      type: 'bar',
      yAxisIndex: 1,
      itemStyle: {
        color: (params) => params.value >= 0 ? '#F56C6C' : '#67C23A'
      },
      data: comparisonData.value.map(d => d.change_pct)
    }
  ]
}))

const getCorrelationColor = (val) => {
  if (!val) return '#909399'
  const abs = Math.abs(val)
  if (abs >= 0.5) return '#67C23A'
  if (abs >= 0.3) return '#E6A23C'
  return '#909399'
}

const getSignificanceType = (sig) => {
  if (sig === 'high') return 'success'
  if (sig === 'medium') return 'warning'
  return 'info'
}

const getAccuracyColor = (percentage) => {
  if (percentage >= 60) return '#67C23A'
  if (percentage >= 50) return '#E6A23C'
  return '#F56C6C'
}

const fetchValidation = async () => {
  if (!stockCode.value) return
  
  try {
    const [startDate, endDate] = dateRange.value
    
    // 获取相关性分析
    const corrRes = await validationApi.getCorrelation({
      stock_code: stockCode.value,
      start_date: startDate,
      end_date: endDate
    })
    
    const correlations = corrRes.data?.correlations || []
    correlationData.value = correlations.slice(0, 5).map(c => ({
      lag: c.lag_days || 0,
      correlation: c.correlation,
      significance: c.significance
    }))
    
    // 获取准确率
    const accRes = await validationApi.getAccuracy({
      stock_code: stockCode.value,
      start_date: startDate,
      end_date: endDate,
      lag_days: 1
    })
    
    accuracy.value = accRes.data?.overall_accuracy || 0
    totalCount.value = accRes.data?.total_samples || 0
    correctCount.value = Math.round(accuracy.value * totalCount.value)
    
    // 获取详细报告
    const reportRes = await validationApi.getReport(stockCode.value, {
      start_date: startDate,
      end_date: endDate
    })
    
    comparisonData.value = reportRes.data?.comparison || []
    
  } catch (error) {
    console.error('Fetch validation error:', error)
  }
}
</script>

<style scoped>
.validation-page {
  min-height: 100%;
}

.filter-card {
  margin-bottom: 20px;
}

.chart-card {
  margin-top: 20px;
}

.accuracy-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  padding: 20px;
}

.accuracy-value {
  font-size: 28px;
  font-weight: bold;
}

.accuracy-info {
  text-align: left;
  line-height: 2;
}
</style>
