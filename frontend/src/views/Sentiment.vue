<template>
  <div class="sentiment-page">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>文本情感分析</span>
          </template>
          <el-form @submit.prevent="analyzeText">
            <el-form-item>
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="6"
                placeholder="请输入要分析的金融文本..."
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="analyzeText" :loading="analyzing">
                分析情感
              </el-button>
              <el-button @click="clearInput">清空</el-button>
            </el-form-item>
          </el-form>
          
          <el-divider v-if="result.label" />
          
          <div v-if="result.label" class="result-section">
            <h4>分析结果</h4>
            <div class="result-content">
              <div class="result-label">
                <el-tag 
                  :type="getSentimentType(result.label)" 
                  size="large"
                  effect="dark"
                >
                  {{ getSentimentLabel(result.label) }}
                </el-tag>
                <span class="confidence">置信度: {{ (result.confidence * 100).toFixed(1) }}%</span>
              </div>
              <div class="score-bars">
                <div class="score-item">
                  <span>积极</span>
                  <el-progress 
                    :percentage="(result.scores?.positive || 0) * 100" 
                    :stroke-width="15"
                    color="#67C23A"
                  />
                </div>
                <div class="score-item">
                  <span>中性</span>
                  <el-progress 
                    :percentage="(result.scores?.neutral || 0) * 100" 
                    :stroke-width="15"
                    color="#E6A23C"
                  />
                </div>
                <div class="score-item">
                  <span>消极</span>
                  <el-progress 
                    :percentage="(result.scores?.negative || 0) * 100" 
                    :stroke-width="15"
                    color="#F56C6C"
                  />
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>批量分析</span>
          </template>
          <el-form>
            <el-form-item>
              <el-input
                v-model="batchText"
                type="textarea"
                :rows="6"
                placeholder="每行一条文本..."
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="batchAnalyze" :loading="batchAnalyzing">
                批量分析
              </el-button>
            </el-form-item>
          </el-form>
          
          <el-divider v-if="batchResults.length > 0" />
          
          <div v-if="batchResults.length > 0">
            <h4>批量分析结果</h4>
            <el-table :data="batchResults" max-height="300">
              <el-table-column prop="text" label="文本" show-overflow-tooltip />
              <el-table-column prop="label" label="情感" width="80">
                <template #default="{ row }">
                  <el-tag :type="getSentimentType(row.label)" size="small">
                    {{ getSentimentLabel(row.label) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="confidence" label="置信度" width="100">
                <template #default="{ row }">
                  {{ (row.confidence * 100).toFixed(1) }}%
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
        
        <el-card style="margin-top: 20px">
          <template #header>
            <span>模型信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="模型名称">
              {{ modelStats.model_name || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="模型状态">
              <el-tag :type="modelStats.model_loaded ? 'success' : 'danger'">
                {{ modelStats.model_loaded ? '已加载' : '未加载' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="已分析数量">
              {{ modelStats.total_analyzed || 0 }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { sentimentApi } from '@/api'
import { ElMessage } from 'element-plus'

const inputText = ref('')
const batchText = ref('')
const analyzing = ref(false)
const batchAnalyzing = ref(false)
const result = ref({})
const batchResults = ref([])
const modelStats = ref({})

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

const analyzeText = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入文本')
    return
  }
  
  analyzing.value = true
  try {
    const res = await sentimentApi.analyze(inputText.value)
    result.value = res.data || {}
  } catch (error) {
    console.error('Analyze error:', error)
  } finally {
    analyzing.value = false
  }
}

const batchAnalyze = async () => {
  const texts = batchText.value.split('\n').filter(t => t.trim())
  if (texts.length === 0) {
    ElMessage.warning('请输入文本')
    return
  }
  
  batchAnalyzing.value = true
  try {
    const res = await sentimentApi.batchAnalyze(texts)
    batchResults.value = res.data || []
  } catch (error) {
    console.error('Batch analyze error:', error)
  } finally {
    batchAnalyzing.value = false
  }
}

const clearInput = () => {
  inputText.value = ''
  result.value = {}
}

const fetchStats = async () => {
  try {
    const res = await sentimentApi.getStats()
    modelStats.value = res.data || {}
  } catch (error) {
    console.error('Fetch stats error:', error)
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.sentiment-page {
  min-height: 100%;
}

.result-section {
  margin-top: 20px;
}

.result-content {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.result-label {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.confidence {
  color: #909399;
  font-size: 14px;
}

.score-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-item span {
  width: 40px;
  font-size: 14px;
  color: #606266;
}

.score-item .el-progress {
  flex: 1;
}
</style>
