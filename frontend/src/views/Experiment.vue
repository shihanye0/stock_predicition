<template>
  <div class="experiment">
    <!-- 实时对比面板 -->
    <el-card class="compare-card">
      <template #header>
        <div class="card-header">
          <span>多模型实时对比</span>
          <el-tag type="info">输入文本，3个模型同时分析</el-tag>
        </div>
      </template>
      <div class="compare-input">
        <el-input
          v-model="compareText"
          type="textarea"
          :rows="3"
          placeholder="请输入要分析的金融评论文本，例如：茅台业绩超预期，看涨！"
          maxlength="512"
          show-word-limit
        />
        <el-button type="primary" @click="runCompare" :loading="compareLoading" style="margin-top: 12px">
          开始对比分析
        </el-button>
      </div>
      
      <!-- 对比结果 -->
      <div v-if="compareResult" class="compare-results">
        <el-row :gutter="20">
          <el-col :span="8" v-for="r in compareResult.results" :key="r.model_name">
            <el-card shadow="hover" :class="['model-card', r.label]">
              <div class="model-name">{{ r.model_name }}</div>
              <div class="model-label">
                <el-tag :type="getSentimentType(r.label)" size="large" effect="dark">
                  {{ getSentimentLabel(r.label) }}
                </el-tag>
              </div>
              <div class="model-confidence">置信度: {{ (r.confidence * 100).toFixed(1) }}%</div>
              <div class="model-scores">
                <div class="score-bar">
                  <span class="score-label">积极</span>
                  <el-progress :percentage="(r.scores.positive * 100).toFixed(1) * 1" :color="'#00e676'" :stroke-width="12" />
                </div>
                <div class="score-bar">
                  <span class="score-label">中性</span>
                  <el-progress :percentage="(r.scores.neutral * 100).toFixed(1) * 1" :color="'#ffab40'" :stroke-width="12" />
                </div>
                <div class="score-bar">
                  <span class="score-label">消极</span>
                  <el-progress :percentage="(r.scores.negative * 100).toFixed(1) * 1" :color="'#ff5252'" :stroke-width="12" />
                </div>
              </div>
              <div class="model-time">耗时: {{ r.elapsed_ms.toFixed(1) }}ms</div>
            </el-card>
          </el-col>
        </el-row>
        <div class="consensus">
          <el-tag type="success" v-if="compareResult.agreement_rate >= 1">
            三模型一致: {{ getSentimentLabel(compareResult.consensus) }}
          </el-tag>
          <el-tag type="warning" v-else>
            一致率: {{ (compareResult.agreement_rate * 100).toFixed(0) }}% | 多数判定: {{ getSentimentLabel(compareResult.consensus) }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 基准测试 -->
    <el-row :gutter="20" class="benchmark-row">
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>基准测试</span>
          </template>
          <el-form label-width="80px">
            <el-form-item label="样本量">
              <el-input-number v-model="benchmarkForm.sample_size" :min="10" :max="500" :step="50" />
            </el-form-item>
            <el-form-item label="股票代码">
              <el-input v-model="benchmarkForm.stock_code" placeholder="留空则使用全部" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="runBenchmark" :loading="benchmarkLoading">
                运行基准测试
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>性能指标对比</span>
              <el-button type="primary" link @click="fetchMetrics">刷新</el-button>
            </div>
          </template>
          <v-chart v-if="metricsChartOption" :option="metricsChartOption" autoresize style="height: 350px" />
          <el-empty v-else description="暂无实验数据，请先运行基准测试" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 混淆矩阵 & 详细指标 -->
    <el-row :gutter="20" class="detail-row">
      <el-col :span="12">
        <el-card>
          <template #header><span>混淆矩阵热力图</span></template>
          <v-chart v-if="confusionChartOption" :option="confusionChartOption" autoresize style="height: 350px" />
          <el-empty v-else description="运行基准测试后显示" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>历史实验记录</span></template>
          <el-table :data="historyResults" max-height="320">
            <el-table-column prop="model_name" label="模型" width="100" />
            <el-table-column prop="accuracy" label="准确率" width="80">
              <template #default="{ row }">{{ row.accuracy ? (row.accuracy * 100).toFixed(1) + '%' : '-' }}</template>
            </el-table-column>
            <el-table-column prop="f1_score" label="F1" width="80">
              <template #default="{ row }">{{ row.f1_score ? (row.f1_score * 100).toFixed(1) + '%' : '-' }}</template>
            </el-table-column>
            <el-table-column prop="sample_count" label="样本数" width="80" />
            <el-table-column prop="run_time" label="耗时(s)" width="80">
              <template #default="{ row }">{{ row.run_time ? row.run_time.toFixed(2) : '-' }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="140">
              <template #default="{ row }">{{ row.created_at?.substring(0, 16) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { experimentApi } from '@/api'
import { ElMessage } from 'element-plus'
import { darkChartTheme, darkAxisStyle, chartColors } from '@/utils/chart-theme'

// 对比分析
const compareText = ref('')
const compareResult = ref(null)
const compareLoading = ref(false)

// 基准测试
const benchmarkForm = ref({ sample_size: 100, stock_code: '' })
const benchmarkLoading = ref(false)
const benchmarkData = ref(null)

// 历史数据
const metricsData = ref(null)
const historyResults = ref([])

// 辅助方法
const getSentimentType = (label) => {
  if (label === 'positive') return 'success'
  if (label === 'negative') return 'danger'
  return 'warning'
}

const getSentimentLabel = (label) => {
  if (label === 'positive') return '积极'
  if (label === 'negative') return '消极'
  if (label === 'neutral') return '中性'
  return label
}

// 对比分析
const runCompare = async () => {
  if (!compareText.value.trim()) {
    ElMessage.warning('请输入待分析文本')
    return
  }
  compareLoading.value = true
  try {
    const res = await experimentApi.compare(compareText.value)
    compareResult.value = res.data
  } catch (error) {
    ElMessage.error('对比分析失败')
  } finally {
    compareLoading.value = false
  }
}

// 基准测试
const runBenchmark = async () => {
  benchmarkLoading.value = true
  try {
    const data = { ...benchmarkForm.value }
    if (!data.stock_code) delete data.stock_code
    const res = await experimentApi.benchmark(data)
    benchmarkData.value = res.data
    ElMessage.success(`基准测试完成，共${res.data?.sample_count || 0}个样本`)
    fetchMetrics()
    fetchHistory()
  } catch (error) {
    ElMessage.error('基准测试失败: ' + (error.response?.data?.message || error.message))
  } finally {
    benchmarkLoading.value = false
  }
}

// 获取指标
const fetchMetrics = async () => {
  try {
    const res = await experimentApi.getMetrics()
    metricsData.value = res.data
  } catch (error) {
    console.error('Fetch metrics error:', error)
  }
}

// 获取历史
const fetchHistory = async () => {
  try {
    const res = await experimentApi.getResults({ page_size: 50 })
    historyResults.value = res.data || []
  } catch (error) {
    console.error('Fetch history error:', error)
  }
}

// 性能指标柱状图
const metricsChartOption = computed(() => {
  const comparison = metricsData.value?.comparison
  if (!comparison || !comparison.length) return null
  
  const modelNames = comparison.map(c => c.model_name)
  const metrics = ['accuracy', 'f1_score', 'precision_score', 'recall_score']
  const metricLabels = ['准确率', 'F1分数', '精确率', '召回率']
  const colors = [chartColors.accent, chartColors.bull, chartColors.neutral, chartColors.bear]

  return {
    ...darkChartTheme,
    legend: { ...darkChartTheme.legend, data: metricLabels },
    xAxis: { type: 'category', data: modelNames, ...darkAxisStyle },
    yAxis: { type: 'value', max: 1, ...darkAxisStyle, axisLabel: { color: '#8b95a5', formatter: (v) => (v * 100).toFixed(0) + '%' } },
    series: metrics.map((m, i) => ({
      name: metricLabels[i],
      type: 'bar',
      data: comparison.map(c => c[m] || 0),
      itemStyle: { color: colors[i] },
      barMaxWidth: 40
    }))
  }
})

// 混淆矩阵热力图
const confusionChartOption = computed(() => {
  const comparison = metricsData.value?.comparison
  if (!comparison || !comparison.length) return null
  
  // 取第一个有混淆矩阵的模型
  const target = comparison.find(c => c.confusion_matrix)
  if (!target || !target.confusion_matrix) return null
  
  const labels = Object.keys(target.confusion_matrix)
  const labelsCN = labels.map(l => getSentimentLabel(l))
  const data = []
  
  labels.forEach((trueLabel, yi) => {
    labels.forEach((predLabel, xi) => {
      data.push([xi, yi, target.confusion_matrix[trueLabel]?.[predLabel] || 0])
    })
  })
  
  const maxVal = Math.max(...data.map(d => d[2]), 1)
  
  return {
    ...darkChartTheme,
    title: { text: `${target.model_name} 混淆矩阵`, left: 'center', textStyle: { fontSize: 14, color: '#e8ecf1' } },
    tooltip: { ...darkChartTheme.tooltip, formatter: (p) => `真实: ${labelsCN[p.value[1]]}<br>预测: ${labelsCN[p.value[0]]}<br>数量: ${p.value[2]}` },
    xAxis: { type: 'category', data: labelsCN, name: '预测标签', ...darkAxisStyle, nameTextStyle: { color: '#8b95a5' }, splitArea: { show: true, areaStyle: { color: ['rgba(0,0,0,0)', 'rgba(255,255,255,0.02)'] } } },
    yAxis: { type: 'category', data: labelsCN, name: '真实标签', ...darkAxisStyle, nameTextStyle: { color: '#8b95a5' }, splitArea: { show: true, areaStyle: { color: ['rgba(0,0,0,0)', 'rgba(255,255,255,0.02)'] } } },
    visualMap: { min: 0, max: maxVal, calculable: true, orient: 'horizontal', left: 'center', bottom: '0%', textStyle: { color: '#8b95a5' }, inRange: { color: ['#1a2332', '#00d4ff', '#00e676'] } },
    series: [{
      type: 'heatmap',
      data: data,
      label: { show: true, fontSize: 16, fontWeight: 'bold', color: '#e8ecf1' },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 212, 255, 0.5)' } }
    }]
  }
})

onMounted(() => {
  fetchMetrics()
  fetchHistory()
})
</script>

<style scoped>
.experiment {
  min-height: 100%;
}

.compare-card {
  margin-bottom: 20px;
}

.compare-results {
  margin-top: 20px;
}

.model-card {
  text-align: center;
  padding: 12px;
}

.model-card.positive { border-top: 3px solid var(--bull); }
.model-card.negative { border-top: 3px solid var(--bear); }
.model-card.neutral { border-top: 3px solid var(--neutral); }

.model-name {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.model-label {
  margin-bottom: 12px;
}

.model-confidence {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.model-scores {
  text-align: left;
}

.score-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.score-label {
  width: 30px;
  font-size: 12px;
  color: var(--text-muted);
}

.score-bar .el-progress {
  flex: 1;
}

.model-time {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

.consensus {
  text-align: center;
  margin-top: 16px;
}

.benchmark-row, .detail-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
