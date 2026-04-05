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
        </el-form-item>
      </el-form>
    </el-card>
    
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
import { stockApi } from '@/api'

const router = useRouter()

// 数据
const stockList = ref([])
const loading = ref(false)

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
  try {
    const res = await stockApi.getStocks({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      market: filters.market || undefined
    })
    stockList.value = res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('Fetch stocks error:', error)
  } finally {
    loading.value = false
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
.table-card { border-radius: var(--radius-md); }

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table__row) {
  cursor: pointer;
}
:deep(.el-table__row:hover) {
  background-color: var(--accent-soft) !important;
}
</style>
