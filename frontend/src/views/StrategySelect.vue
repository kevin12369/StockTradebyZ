<template>
  <div class="strategy-select-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">
          <el-icon class="title-icon"><MagicStick /></el-icon>
          选股结果列表
        </h1>
        <p class="page-subtitle">查看和管理策略选股结果</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Guide" @click="goToWizard">
          执行选股
        </el-button>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-section card">
      <div class="filter-toolbar">
        <div class="filter-group">
          <label class="filter-label">
            <el-icon><Calendar /></el-icon>
            选股日期
          </label>
          <el-date-picker
            v-model="filterDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            clearable
            @change="handleFilterChange"
          />
        </div>

        <div class="filter-group">
          <label class="filter-label">
            <el-icon><Filter /></el-icon>
            策略筛选
          </label>
          <el-select
            v-model="filterStrategy"
            placeholder="全部策略"
            clearable
            @change="handleFilterChange"
          >
            <el-option
              v-for="strategy in strategies"
              :key="strategy.id"
              :label="strategy.alias"
              :value="strategy.id"
            />
          </el-select>
        </div>

        <div class="filter-group filter-search">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索股票代码或名称..."
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="filter-actions">
          <el-button :icon="Refresh" @click="loadResults">
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section" v-if="!loading && filteredResults.length > 0">
      <div class="stat-item">
        <span class="stat-label">筛选结果</span>
        <span class="stat-value">{{ filteredResults.length }}</span>
        <span class="stat-unit">只</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">总计</span>
        <span class="stat-value">{{ pagination.total }}</span>
        <span class="stat-unit">只</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">当前页</span>
        <span class="stat-value">{{ pagination.page }}</span>
        <span class="stat-unit">/ {{ Math.ceil(pagination.total / pagination.page_size) }}</span>
      </div>
    </div>

    <!-- 结果列表 -->
    <div class="results-section card">
      <el-table
        :data="paginatedResults"
        v-loading="loading"
        stripe
        class="results-table"
        @row-click="showStockDetail"
      >
        <el-table-column type="index" label="排名" width="80" align="center">
          <template #default="{ $index }">
            <span class="rank-badge" :class="getRankClass($index)">
              {{ $index + 1 + (pagination.page - 1) * pagination.page_size }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="股票代码" width="140" align="center">
          <template #default="{ row }">
            <span class="stock-code">{{ (row.reason as any)?.symbol || row.ts_code }}</span>
          </template>
        </el-table-column>

        <el-table-column label="股票名称" width="140" align="center">
          <template #default="{ row }">
            <span class="stock-name">{{ (row.reason as any)?.name || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="选股策略" width="160" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="primary">
              {{ (row.reason as any)?.strategy_alias || '-' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="选股日期" width="120" align="center">
          <template #default="{ row }">
            <span class="date-text">{{ row.trade_date }}</span>
          </template>
        </el-table-column>

        <el-table-column label="选股理由" min-width="250" align="left">
          <template #default="{ row }">
            <div class="reason-cell">
              <el-tooltip :content="getReasonText(row)" placement="top">
                <span class="reason-text">{{ getReasonText(row) }}</span>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" @click.stop="showStockDetail(row)">
              <el-icon><Document /></el-icon>
              详情
            </el-button>
            <el-divider direction="vertical" />
            <el-button text type="success" @click.stop="viewKline(row.ts_code)">
              <el-icon><TrendCharts /></el-icon>
              K线
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div v-if="!loading && filteredResults.length === 0" class="empty-state">
        <el-empty :image-size="120">
          <template #description>
            <p class="empty-description">暂无选股结果</p>
            <p class="empty-hint">尝试调整筛选条件或执行新的选股策略</p>
          </template>
          <el-button type="primary" :icon="Guide" @click="goToWizard">
            执行选股
          </el-button>
        </el-empty>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-section" v-if="!loading && filteredResults.length > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        background
      />
    </div>

    <!-- 股票详情弹窗 -->
    <StockDetailDialog
      v-model="stockDetailVisible"
      :ts-code="currentStockTsCode"
      :trade-date="filterDate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  MagicStick,
  Guide,
  Calendar,
  Filter,
  Search,
  Refresh,
  Document,
  TrendCharts,
} from '@element-plus/icons-vue'
import { getStrategies, getSelectionResults } from '@/api/strategy'
import type { Strategy, SelectionResult } from '@/types'
import StockDetailDialog from '@/components/strategy/StockDetailDialog.vue'

const router = useRouter()

// ========== 状态 ==========
const stockDetailVisible = ref(false)
const currentStockTsCode = ref('')
const loading = ref(false)

// 筛选条件
const filterDate = ref('')
const filterStrategy = ref<number | undefined>(undefined)
const searchKeyword = ref('')

// 分页参数
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

// 数据
const strategies = ref<Strategy[]>([])
const allResults = ref<SelectionResult[]>([])

// ========== 计算属性 ==========
// 过滤后的结果（前端搜索）
const filteredResults = computed(() => {
  let results = allResults.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    results = results.filter(r =>
      r.ts_code.toLowerCase().includes(keyword) ||
      (r.reason as any)?.name?.toLowerCase().includes(keyword)
    )
  }

  return results
})

// 分页后的结果
const paginatedResults = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.page_size
  const end = start + pagination.value.page_size
  return filteredResults.value.slice(start, end)
})

// ========== 方法 ==========
const getRankClass = (index: number) => {
  const rank = index + 1
  if (rank === 1) return 'rank-1'
  if (rank === 2) return 'rank-2'
  if (rank === 3) return 'rank-3'
  return ''
}

const getReasonText = (row: SelectionResult) => {
  const reason = row.reason as any
  if (!reason) return '-'

  // 构建理由文本
  const parts: string[] = []
  if (reason.symbol) parts.push(`代码: ${reason.symbol}`)
  if (reason.name) parts.push(`名称: ${reason.name}`)
  if (reason.strategy_alias) parts.push(`策略: ${reason.strategy_alias}`)

  return parts.join(' | ') || '-'
}

const goToWizard = () => {
  router.push('/strategies/wizard')
}

const handleFilterChange = () => {
  pagination.value.page = 1
  loadResults()
}

const handleSearch = () => {
  // 前端过滤，不需要重新加载
  pagination.value.page = 1
}

const showStockDetail = (row: SelectionResult) => {
  currentStockTsCode.value = row.ts_code
  stockDetailVisible.value = true
}

const viewKline = (tsCode: string) => {
  router.push({ name: 'StockKline', params: { tsCode } })
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
}

const handleSizeChange = (size: number) => {
  pagination.value.page_size = size
  pagination.value.page = 1
}

// ========== 数据加载 ==========
const loadStrategies = async () => {
  try {
    const data = await getStrategies({ is_active: true })
    strategies.value = data
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

const loadResults = async () => {
  loading.value = true
  try {
    const result = await getSelectionResults({
      trade_date: filterDate.value || undefined,
      strategy_id: filterStrategy.value,
      page: pagination.value.page,
      page_size: pagination.value.page_size,
    })

    allResults.value = result.items
    pagination.value.total = result.total
  } catch (error) {
    console.error('加载选股结果失败:', error)
    ElMessage.error('加载选股结果失败')
  } finally {
    loading.value = false
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  loadStrategies()
  loadResults()
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.strategy-select-page {
  padding: $spacing-4;

  // 页面标题
  .page-header {
    @include flex-between;
    margin-bottom: $spacing-6;
    padding: $spacing-6;
    background: linear-gradient(135deg, #1890ff 0%, #52c41a 100%);
    border-radius: $border-radius-lg;
    color: #fff;
    box-shadow: $shadow-3;

    .header-info {
      .page-title {
        display: flex;
        align-items: center;
        gap: $spacing-3;
        margin: 0 0 $spacing-2 0;
        font-size: $font-size-xxl;
        font-weight: $font-weight-bold;

        .title-icon {
          font-size: 32px;
        }
      }

      .page-subtitle {
        margin: 0;
        font-size: $font-size-md;
        opacity: 0.9;
      }
    }

    .header-actions {
      :deep(.el-button) {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.3);
        color: #fff;

        &:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      }
    }
  }

  // 筛选工具栏
  .filter-section {
    margin-bottom: $spacing-5;
  }

  .filter-toolbar {
    display: flex;
    align-items: center;
    gap: $spacing-4;
    flex-wrap: wrap;

    .filter-group {
      display: flex;
      flex-direction: column;
      gap: $spacing-2;

      .filter-label {
        display: flex;
        align-items: center;
        gap: $spacing-1;
        font-size: $font-size-sm;
        font-weight: $font-weight-medium;
        color: $text-secondary;
      }

      :deep(.el-select),
      :deep(.el-date-editor) {
        width: 180px;
      }
    }

    .filter-search {
      flex: 1;
      min-width: 200px;

      :deep(.el-input) {
        width: 100%;
      }
    }

    .filter-actions {
      margin-left: auto;
    }
  }

  // 统计信息
  .stats-section {
    display: flex;
    align-items: center;
    gap: $spacing-6;
    padding: $spacing-4;
    margin-bottom: $spacing-5;
    background: linear-gradient(135deg, $primary-light 0%, rgba(82, 196, 26, 0.1) 100%);
    border-radius: $border-radius-md;
    border: 1px solid $border-light;

    .stat-item {
      display: flex;
      align-items: baseline;
      gap: $spacing-2;

      .stat-label {
        font-size: $font-size-sm;
        color: $text-secondary;
      }

      .stat-value {
        font-size: $font-size-xl;
        font-weight: $font-weight-bold;
        color: $primary-color;
      }

      .stat-unit {
        font-size: $font-size-sm;
        color: $text-tertiary;
      }
    }
  }

  // 结果列表
  .results-section {
    margin-bottom: $spacing-5;

    .results-table {
      :deep(.el-table__body-wrapper) {
        .el-table__row {
          cursor: pointer;
          transition: background-color $transition-fast;

          &:hover {
            td {
              background-color: $primary-light !important;
            }
          }
        }
      }

      .rank-badge {
        display: inline-block;
        min-width: 32px;
        height: 32px;
        line-height: 32px;
        text-align: center;
        font-weight: $font-weight-bold;
        font-size: $font-size-base;
        background: $bg-base;
        border-radius: $border-radius-sm;
        color: $text-secondary;

        &.rank-1 {
          background: linear-gradient(135deg, #f5222d 0%, #ff4d4f 100%);
          color: #fff;
          font-size: $font-size-lg;
          box-shadow: $up-shadow;
        }

        &.rank-2 {
          background: linear-gradient(135deg, #fa8c16 0%, #ffa940 100%);
          color: #fff;
          box-shadow: 0 2px 8px rgba(250, 140, 22, 0.3);
        }

        &.rank-3 {
          background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
          color: #fff;
          box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
        }
      }

      .stock-code {
        font-family: $font-family-code;
        font-weight: $font-weight-semibold;
        color: $text-primary;
      }

      .stock-name {
        font-weight: $font-weight-medium;
        color: $text-secondary;
      }

      .date-text {
        font-family: $font-family-code;
        font-size: $font-size-sm;
        color: $text-tertiary;
      }

      .reason-cell {
        .reason-text {
          display: inline-block;
          max-width: 100%;
          font-size: $font-size-sm;
          color: $text-secondary;
          @include text-ellipsis;
        }
      }
    }

    .empty-state {
      padding: $spacing-10 0;

      .empty-description {
        font-size: $font-size-md;
        color: $text-secondary;
        margin-bottom: $spacing-2;
      }

      .empty-hint {
        font-size: $font-size-sm;
        color: $text-tertiary;
        margin-bottom: $spacing-6;
      }
    }
  }

  // 分页
  .pagination-section {
    @include flex-center;
    padding: $spacing-4;
    background: $card-bg;
    border-radius: $border-radius-md;
  }
}

// 响应式
@include respond-below('md') {
  .strategy-select-page {
    padding: $spacing-3;

    .page-header {
      flex-direction: column;
      gap: $spacing-4;
      text-align: center;

      .header-actions {
        margin-left: 0;
      }
    }

    .filter-toolbar {
      flex-direction: column;
      align-items: stretch;

      .filter-group {
        :deep(.el-select),
        :deep(.el-date-editor) {
          width: 100%;
        }
      }

      .filter-search {
        order: -1;
      }

      .filter-actions {
        margin-left: 0;

        :deep(.el-button) {
          width: 100%;
        }
      }
    }

    .stats-section {
      flex-direction: column;
      gap: $spacing-3;
      text-align: center;
    }
  }
}
</style>
