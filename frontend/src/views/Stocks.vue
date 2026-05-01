<template>
  <div class="stocks-page">
    <!-- 搜索筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="股票搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="输入代码或名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="市场">
          <el-select
            v-model="filters.market"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option label="上海" value="SH" />
            <el-option label="深圳" value="SZ" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="success" @click="initDemoData" :loading="initLoading">
            {{ stockList.length === 0 ? '初始化演示数据' : `补充数据 (当前${pagination.total}只)` }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据状态提示 -->
    <el-alert
      v-if="fetched && stockList.length === 0"
      title="暂无股票数据"
      type="warning"
      :closable="false"
      show-icon
      class="data-alert"
    >
      <template #default>
        数据库中暂无股票数据，请点击上方「初始化演示数据」按钮生成示例数据。
      </template>
    </el-alert>

    <el-alert
      v-if="fetched && stockList.length > 0 && stockList.length < pagination.pageSize"
      title="数据较少"
      type="info"
      :closable="false"
      show-icon
      class="data-alert"
    >
      <template #default>
        当前共有 <strong>{{ pagination.total }}</strong> 条股票数据，已全部展示。
        点击「补充数据」可生成更多示例数据。
      </template>
    </el-alert>

    <!-- 股票列表 -->
    <el-card class="table-card">
      <el-table 
        :data="stockList" 
        v-loading="loading"
        style="width: 100%"
        @row-click="goToDetail"
      >
        <el-table-column prop="stock_code" label="代码" width="100" />
        <el-table-column prop="stock_name" label="名称" width="120" />
        <el-table-column prop="market" label="市场" width="80">
          <template #default="{ row }">
            <el-tag :type="row.market === 'SH' ? 'danger' : 'primary'" size="small">
              {{ row.market }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="goToDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { stockApi, adminApi } from '@/api'

const router = useRouter()

// 数据
const stockList = ref([])
const loading = ref(false)
const initLoading = ref(false)
const fetched = ref(false)

const filters = reactive({
  keyword: '',
  market: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 方法
const fetchStocks = async () => {
  loading.value = true
  fetched.value = false
  try {
    const res = await stockApi.getStocks({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      market: filters.market || undefined
    })
    stockList.value = res.data || []
    pagination.total = res.total || 0
    fetched.value = true
  } catch (error) {
    console.error('Fetch stocks error:', error)
    fetched.value = true
  } finally {
    loading.value = false
  }
}

// 初始化演示数据
const initDemoData = async () => {
  initLoading.value = true
  try {
    const res = await adminApi.initDemo()
    const stocksAdded = res.data?.stocks_added || 0
    const stocksTotal = res.data?.stocks_total || 0
    if (stocksAdded > 0) {
      ElMessage.success(`数据补充成功！新增 ${stocksAdded} 只股票，股票总数 ${stocksTotal}`)
    } else {
      ElMessage.success('演示数据更新成功')
    }
    // 刷新列表
    pagination.page = 1
    fetchStocks()
  } catch (error) {
    console.error('Init demo data error:', error)
    ElMessage.error('初始化失败：' + (error.message || '请检查后端服务'))
  } finally {
    initLoading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchStocks()
}

const resetFilters = () => {
  filters.keyword = ''
  filters.market = null
  pagination.page = 1
  fetchStocks()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchStocks()
}

const handlePageChange = () => {
  fetchStocks()
}

const goToDetail = (row) => {
  router.push(`/stock/${row.stock_code}`)
}

// 生命周期
onMounted(() => {
  fetchStocks()
})
</script>

<style scoped>
.stocks-page { min-height: 100%; }
.filter-card { margin-bottom: 16px; }
.table-card {
  border-radius: var(--radius-md);
  overflow: visible !important;
}

.data-alert {
  margin-bottom: 16px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  position: relative;
  z-index: 100;
  overflow: visible !important;
}

/* 分页组件全量样式修复 */
:deep(.el-pagination) {
  pointer-events: auto !important;
  visibility: visible !important;
  display: flex !important;
  flex-wrap: wrap;
  gap: 4px;
}

/* 上一页/下一页按钮 */
:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  pointer-events: auto !important;
  cursor: pointer !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  min-width: 32px !important;
  height: 32px !important;
  background-color: var(--bg-elevated) !important;
  border-radius: var(--radius-sm) !important;
}

:deep(.el-pagination .btn-prev:disabled),
:deep(.el-pagination .btn-next:disabled) {
  pointer-events: none !important;
  opacity: 0.5 !important;
}

/* 页码按钮 */
:deep(.el-pagination .el-pager) {
  pointer-events: auto !important;
  display: flex !important;
  gap: 4px;
}

:deep(.el-pagination .el-pager li) {
  pointer-events: auto !important;
  cursor: pointer !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  min-width: 32px !important;
  height: 32px !important;
  background-color: var(--bg-elevated) !important;
  border-radius: var(--radius-sm) !important;
  margin: 0 !important;
}

:deep(.el-pagination .el-pager li:hover) {
  color: var(--accent) !important;
}

:deep(.el-pagination .el-pager li.is-active) {
  background-color: var(--accent) !important;
  color: var(--text-inverse) !important;
}

/* jumper 输入框 */
:deep(.el-pagination .el-pagination__jump) {
  pointer-events: auto !important;
}

:deep(.el-pagination .el-input) {
  pointer-events: auto !important;
}

:deep(.el-pagination .el-input__wrapper) {
  pointer-events: auto !important;
  cursor: text !important;
}

/* sizes 选择器 */
:deep(.el-pagination .el-pagination__sizes) {
  pointer-events: auto !important;
}

:deep(.el-pagination .el-select) {
  pointer-events: auto !important;
}

:deep(.el-table__row) {
  cursor: pointer;
}
:deep(.el-table__row:hover) {
  background-color: var(--accent-soft) !important;
}
</style>
