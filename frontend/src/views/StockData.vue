<template>
  <div class="stock-data-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">
          <el-icon class="title-icon"><Document /></el-icon>
          数据管理中心
        </h1>
        <p class="page-subtitle">股票数据查询、同步与管理</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Download" @click="handleFullSync">
          全量同步
        </el-button>
      </div>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section card">
      <div class="search-box">
        <el-input
          v-model="queryParams.search"
          placeholder="搜索股票代码或名称..."
          size="large"
          clearable
          @keyup.enter="handleSearch"
          @input="onSearchInput"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
      </div>

      <!-- 高级筛选 -->
      <el-collapse v-model="advancedFilterVisible" class="advanced-filter">
        <el-collapse-item name="filter">
          <template #title>
            <div class="filter-header">
              <el-icon><Filter /></el-icon>
              <span>高级筛选</span>
            </div>
          </template>
          <div class="filter-content">
            <div class="filter-group">
              <label class="filter-label">板块筛选</label>
              <el-select
                v-model="queryParams.boards"
                placeholder="全部板块"
                clearable
                multiple
                collapse-tags
                collapse-tags-tooltip
              >
                <el-option label="沪主板" value="沪主板" />
                <el-option label="深主板" value="深主板" />
                <el-option label="科创板" value="科创板" />
                <el-option label="创业板" value="创业板" />
                <el-option label="北交所" value="北交所" />
              </el-select>
            </div>

            <div class="filter-group">
              <label class="filter-label">数据状态</label>
              <el-select v-model="queryParams.has_data" placeholder="全部" clearable>
                <el-option label="有K线数据" :value="true" />
                <el-option label="无K线数据" :value="false" />
              </el-select>
            </div>

            <div class="filter-actions">
              <el-button type="primary" :icon="Search" @click="handleSearch">
                搜索
              </el-button>
              <el-button :icon="RefreshLeft" @click="handleReset">
                重置
              </el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- Tab内容区 -->
    <div class="content-section card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="data-tabs">
        <!-- 搜索结果Tab -->
        <el-tab-pane name="search">
          <template #label>
            <span class="tab-label">
              <el-icon><List /></el-icon>
              搜索结果
              <el-badge v-if="searchResults.length > 0" :value="searchResults.length" type="primary" />
            </span>
          </template>

          <!-- 未搜索状态 -->
          <div v-if="!hasSearched" class="empty-state">
            <el-empty :image-size="140">
              <template #image>
                <div class="empty-icon">
                  <el-icon><Search /></el-icon>
                </div>
              </template>
              <template #description>
                <p class="empty-title">输入股票代码或名称开始搜索</p>
                <p class="empty-desc">支持模糊搜索，例如：输入"茅台"或"600519"</p>
              </template>
            </el-empty>
          </div>

          <!-- 无结果状态 -->
          <div v-else-if="searchResults.length === 0" class="empty-state">
            <el-empty :image-size="120">
              <template #description>
                <p class="empty-title">未找到匹配的股票</p>
                <p class="empty-desc">尝试调整搜索关键词或筛选条件</p>
              </template>
            </el-empty>
          </div>

          <!-- 搜索结果 -->
          <div v-else class="results-container">
            <!-- 结果统计 -->
            <div class="results-stats">
              <div class="stat-item">
                <span class="stat-icon">
                  <el-icon><Document /></el-icon>
                </span>
                <div class="stat-content">
                  <div class="stat-value">{{ searchResults.length }}</div>
                  <div class="stat-label">找到股票</div>
                </div>
              </div>
              <div class="stat-item" v-if="searchResults.length > 0">
                <span class="stat-icon">
                  <el-icon><Check /></el-icon>
                </span>
                <div class="stat-content">
                  <div class="stat-value">{{ searchResults.filter(s => s.has_data).length }}</div>
                  <div class="stat-label">已同步</div>
                </div>
              </div>
            </div>

            <!-- 表格 -->
            <el-table :data="paginatedResults" v-loading="loading" stripe class="results-table" @row-click="handleViewKline">
              <el-table-column prop="ts_code" label="股票代码" width="150" align="center">
                <template #default="{ row }">
                  <span class="stock-code">{{ row.ts_code }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="symbol" label="代码" width="100" align="center">
                <template #default="{ row }">
                  <span class="symbol-text">{{ row.symbol || '-' }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="name" label="股票名称" width="140" align="center">
                <template #default="{ row }">
                  <span class="stock-name">{{ row.name }}</span>
                </template>
              </el-table-column>

              <el-table-column label="市场" width="100" align="center">
                <template #default="{ row }">
                  <el-tag size="small" type="info">
                    {{ row.market_name || row.market || '-' }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column label="板块" width="110" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.board" size="small" :type="getBoardTagType(row.board)">
                    {{ row.board }}
                  </el-tag>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>

              <el-table-column label="数据状态" width="140" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.has_data" type="success" size="small">
                    <el-icon><CircleCheck /></el-icon>
                    已同步 ({{ row.kline_count }}条)
                  </el-tag>
                  <el-tag v-else type="info" size="small">
                    <el-icon><Clock /></el-icon>
                    未同步
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column label="最新日期" width="120" align="center">
                <template #default="{ row }">
                  <span class="date-text">{{ formatDate(row.latest_date) }}</span>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="180" fixed="right" align="center">
                <template #default="{ row }">
                  <el-button text type="primary" @click.stop="handleViewKline(row)">
                    <el-icon><TrendCharts /></el-icon>
                    K线
                  </el-button>
                  <el-divider direction="vertical" />
                  <el-button
                    text
                    type="success"
                    @click.stop="handleSyncKline(row)"
                    :disabled="row.has_data"
                    :loading="syncing && syncingStock?.ts_code === row.ts_code"
                  >
                    <el-icon><Refresh /></el-icon>
                    同步
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-wrapper" v-if="searchResults.length > 0">
              <el-pagination
                v-model:current-page="pagination.page"
                v-model:page-size="pagination.page_size"
                :total="searchResults.length"
                :page-sizes="[20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
                background
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 今日Top50 -->
        <el-tab-pane name="today">
          <template #label>
            <span class="tab-label">
              <el-icon><TrendCharts /></el-icon>
              今日涨幅榜
            </span>
          </template>
          <Top50Table :data="todayTop50" :loading="todayLoading" period="今日" />
        </el-tab-pane>

        <!-- 近7日Top50 -->
        <el-tab-pane name="week">
          <template #label>
            <span class="tab-label">
              <el-icon><TrendCharts /></el-icon>
              近7日涨幅榜
            </span>
          </template>
          <Top50Table :data="weekTop50" :loading="weekLoading" period="近7日" />
        </el-tab-pane>

        <!-- 近1月Top50 -->
        <el-tab-pane name="month">
          <template #label>
            <span class="tab-label">
              <el-icon><TrendCharts /></el-icon>
              近1月涨幅榜
            </span>
          </template>
          <Top50Table :data="monthTop50" :loading="monthLoading" period="近1月" />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 同步弹窗 -->
    <el-dialog
      v-model="syncing"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      width="400px"
      class="sync-dialog"
    >
      <div class="sync-loading">
        <el-icon class="is-loading" :size="48"><Loading /></el-icon>
        <p class="sync-text">正在同步 {{ syncingStock?.name }} 的K线数据...</p>
        <p class="sync-hint">请勿关闭窗口</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  Search,
  Download,
  List,
  TrendCharts,
  Loading,
  Filter,
  RefreshLeft,
  CircleCheck,
  Clock,
  Check,
} from '@element-plus/icons-vue'
import {
  getStockList,
  syncStockKline,
  getTopPerformers,
  getKlineStatus,
  type TopPerformer,
  type StockKlineStatus,
} from '@/api/stock'
import type { Stock } from '@/types'
import Top50Table from '@/components/Top50Table.vue'

const router = useRouter()

// 状态
const activeTab = ref('search')
const advancedFilterVisible = ref<string[]>([])
const loading = ref(false)
const syncing = ref(false)
const syncingStock = ref<(Stock & { has_data: boolean }) | null>(null)
const hasSearched = ref(false)

// 查询参数
const queryParams = ref({
  search: '',
  boards: [] as string[],
  has_data: undefined as boolean | undefined,
})

// 分页
const pagination = ref({
  page: 1,
  page_size: 20,
})

// 数据
const searchResults = ref<Array<Stock & { has_data: boolean; kline_count: number; latest_date: string | null }>>([])

// Top50数据
const todayTop50 = ref<TopPerformer[]>([])
const weekTop50 = ref<TopPerformer[]>([])
const monthTop50 = ref<TopPerformer[]>([])
const todayLoading = ref(false)
const weekLoading = ref(false)
const monthLoading = ref(false)

// 分页后的结果
const paginatedResults = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.page_size
  const end = start + pagination.value.page_size
  return searchResults.value.slice(start, end)
})

// 方法
const handleTabChange = (tabName: string) => {
  if (tabName === 'today' && todayTop50.value.length === 0) {
    loadTopPerformers('today', '1day')
  } else if (tabName === 'week' && weekTop50.value.length === 0) {
    loadTopPerformers('week', '1week')
  } else if (tabName === 'month' && monthTop50.value.length === 0) {
    loadTopPerformers('month', '1month')
  }
}

const loadTopPerformers = async (type: 'today' | 'week' | 'month', period: '1day' | '1week' | '1month') => {
  const loadingMap = { today: todayLoading, week: weekLoading, month: monthLoading }
  const dataMap = { today: todayTop50, week: weekTop50, month: monthTop50 }

  loadingMap[type].value = true
  try {
    const data = await getTopPerformers({ period, limit: 50 })
    dataMap[type].value = data
  } catch (error) {
    console.error(`加载${period}涨幅榜失败:`, error)
  } finally {
    loadingMap[type].value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
const onSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    if (queryParams.value.search.trim()) {
      handleSearch()
    }
  }, 500)
}

const handleSearch = async () => {
  if (!queryParams.value.search.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  hasSearched.value = true
  pagination.value.page = 1

  try {
    // 并发请求：股票列表 + K线状态
    const [stocksResult, klineStatus] = await Promise.all([
      getStockList({
        page: 1,
        page_size: 100,
        search: queryParams.value.search || undefined,
      }),
      getKlineStatus({ limit: 1000 }).catch(() => []), // 如果失败就返回空数组
    ])

    let results = stocksResult.items

    // 板块筛选
    if (queryParams.value.boards && queryParams.value.boards.length > 0) {
      results = results.filter((stock) => {
        return stock.board && queryParams.value.boards!.includes(stock.board)
      })
    }

    // 按板块+代码排序
    results.sort((a, b) => {
      const marketOrder = ['沪主板', '深主板', '科创板', '创业板', '北交所']
      const aBoard = a.board || ''
      const bBoard = b.board || ''
      const aIndex = marketOrder.indexOf(aBoard) !== -1 ? marketOrder.indexOf(aBoard) : 999
      const bIndex = marketOrder.indexOf(bBoard) !== -1 ? marketOrder.indexOf(bBoard) : 999
      if (aIndex !== bIndex) return aIndex - bIndex
      return a.ts_code.localeCompare(b.ts_code)
    })

    // 构建 K线状态映射表
    const statusMap = new Map<string, StockKlineStatus>()
    for (const status of klineStatus) {
      statusMap.set(status.ts_code, status)
    }

    // 合并股票数据和K线状态
    let mergedResults = results.map(stock => {
      const status = statusMap.get(stock.ts_code)
      return {
        ...stock,
        has_data: status?.has_data ?? false,
        kline_count: status?.kline_count ?? 0,
        latest_date: status?.latest_date ?? null,
      }
    })

    // 数据状态筛选（在合并后执行）
    if (queryParams.value.has_data !== undefined) {
      mergedResults = mergedResults.filter(item => item.has_data === queryParams.value.has_data)
    }

    searchResults.value = mergedResults
  } catch (error) {
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  queryParams.value = { search: '', boards: [], has_data: undefined }
  searchResults.value = []
  hasSearched.value = false
  pagination.value.page = 1
}

const handleFullSync = () => {
  ElMessage.info('全量同步功能开发中，请前往系统设置执行')
  router.push('/settings')
}

const handleSyncKline = async (stock: Stock & { has_data: boolean }) => {
  syncing.value = true
  syncingStock.value = stock
  try {
    const result = await syncStockKline(stock.ts_code)
    if (result.success) {
      ElMessage.success(`${stock.name} K线数据同步成功！新增 ${result.added} 条`)
      // 刷新搜索结果
      if (hasSearched.value) {
        handleSearch()
      }
    } else {
      ElMessage.warning(result.message)
    }
  } catch (error) {
    ElMessage.error(`${stock.name} K线数据同步失败`)
  } finally {
    syncing.value = false
    syncingStock.value = null
  }
}

const handleViewKline = (stock: Stock) => {
  router.push({
    name: 'StockKline',
    params: { tsCode: stock.ts_code },
    query: { name: stock.name },
  })
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
}

const handleSizeChange = (size: number) => {
  pagination.value.page_size = size
  pagination.value.page = 1
}

const formatDate = (dateStr: string) => {
  return dateStr?.substring(0, 10) || '-'
}

const getBoardTagType = (board: string) => {
  const tagTypeMap: Record<string, string> = {
    '沪主板': 'primary',
    '深主板': 'success',
    '科创板': 'danger',
    '创业板': 'warning',
    '北交所': 'info',
  }
  return tagTypeMap[board] || ''
}

// 初始化
onMounted(() => {
  loadTopPerformers('today', '1day')
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.stock-data-page {
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

  // 搜索区域
  .search-section {
    margin-bottom: $spacing-5;

    .search-box {
      margin-bottom: $spacing-4;

      :deep(.el-input) {
        .el-input__wrapper {
          padding: $spacing-4 $spacing-5;
          border-radius: $border-radius-lg;
        }

        .el-input__inner {
          font-size: $font-size-md;
        }
      }
    }

    .advanced-filter {
      :deep(.el-collapse) {
        border: none;
      }

      :deep(.el-collapse-item__header) {
        background: $bg-base;
        border-radius: $border-radius-base;
        padding: 0 $spacing-4;
        margin-bottom: $spacing-3;
        font-weight: $font-weight-medium;

        .el-collapse-item__arrow {
          margin-left: $spacing-2;
        }
      }

      .filter-header {
        display: flex;
        align-items: center;
        gap: $spacing-2;
      }

      .filter-content {
        display: flex;
        align-items: center;
        gap: $spacing-4;
        flex-wrap: wrap;
        padding: $spacing-4;
        background: $bg-base;
        border-radius: $border-radius-base;

        .filter-group {
          display: flex;
          flex-direction: column;
          gap: $spacing-2;

          .filter-label {
            font-size: $font-size-sm;
            font-weight: $font-weight-medium;
            color: $text-secondary;
          }
        }

        .filter-actions {
          margin-left: auto;
          display: flex;
          gap: $spacing-3;
        }
      }
    }
  }

  // 内容区域
  .content-section {
    min-height: 500px;

    .data-tabs {
      :deep(.el-tabs__header) {
        margin: 0;
        padding: 0 $spacing-4;
        background: $bg-base;
        border-radius: $border-radius-md $border-radius-md 0 0;
        border-bottom: 1px solid $border-lighter;
      }

      :deep(.el-tabs__nav-wrap::after) {
        display: none;
      }

      :deep(.el-tabs__item) {
        padding: 0 $spacing-5;
        height: 48px;
        line-height: 48px;
        color: $text-secondary;
        font-weight: $font-weight-medium;

        &:hover {
          color: $primary-color;
        }

        &.is-active {
          color: $primary-color;
        }
      }

      :deep(.el-tabs__active-bar) {
        height: 3px;
        background-color: $primary-color;
      }

      .tab-label {
        display: flex;
        align-items: center;
        gap: $spacing-2;

        :deep(.el-badge) {
          margin-left: $spacing-2;
        }
      }
    }

    .empty-state {
      padding: $spacing-10 0;

      .empty-icon {
        width: 120px;
        height: 120px;
        margin: 0 auto $spacing-6;
        @include flex-center;
        background: $bg-base;
        border-radius: 50%;
        color: $text-quaternary;

        .el-icon {
          font-size: 48px;
        }
      }

      .empty-title {
        font-size: $font-size-lg;
        color: $text-secondary;
        margin-bottom: $spacing-2;
      }

      .empty-desc {
        font-size: $font-size-sm;
        color: $text-tertiary;
        margin: 0;
      }
    }

    .results-container {
      .results-stats {
        display: flex;
        align-items: center;
        gap: $spacing-6;
        padding: $spacing-5;
        margin-bottom: $spacing-5;
        background: linear-gradient(135deg, $primary-light 0%, rgba(82, 196, 26, 0.1) 100%);
        border-radius: $border-radius-md;

        .stat-item {
          display: flex;
          align-items: center;
          gap: $spacing-3;

          .stat-icon {
            width: 40px;
            height: 40px;
            @include flex-center;
            background: #fff;
            border-radius: $border-radius-sm;
            color: $primary-color;
            box-shadow: $shadow-1;
          }

          .stat-content {
            .stat-value {
              font-size: $font-size-xl;
              font-weight: $font-weight-bold;
              color: $primary-color;
              line-height: 1;
            }

            .stat-label {
              font-size: $font-size-xs;
              color: $text-tertiary;
            }
          }
        }
      }

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

        .stock-code {
          font-family: $font-family-code;
          font-weight: $font-weight-semibold;
          color: $text-primary;
        }

        .symbol-text {
          font-family: $font-family-code;
          font-size: $font-size-sm;
          color: $text-tertiary;
        }

        .stock-name {
          font-weight: $font-weight-medium;
          color: $text-secondary;
        }

        .text-muted {
          color: $text-quaternary;
        }

        .date-text {
          font-family: $font-family-code;
          font-size: $font-size-sm;
          color: $text-tertiary;
        }
      }

      .pagination-wrapper {
        @include flex-center;
        padding: $spacing-4 0;
      }
    }
  }

  // 同步弹窗
  .sync-dialog {
    .sync-loading {
      @include flex-center;
      flex-direction: column;
      padding: $spacing-8 0;
      gap: $spacing-4;

      .sync-text {
        margin: 0;
        font-size: $font-size-md;
        color: $text-primary;
      }

      .sync-hint {
        margin: 0;
        font-size: $font-size-sm;
        color: $text-tertiary;
      }
    }
  }
}

// 响应式
@include respond-below('md') {
  .stock-data-page {
    padding: $spacing-3;

    .page-header {
      flex-direction: column;
      gap: $spacing-4;
      text-align: center;
    }

    .search-section {
      .advanced-filter {
        .filter-content {
          flex-direction: column;
          align-items: stretch;

          .filter-actions {
            margin-left: 0;
            width: 100%;

            :deep(.el-button) {
              flex: 1;
            }
          }
        }
      }
    }

    .content-section {
      .results-container {
        .results-stats {
          flex-direction: column;
          gap: $spacing-4;
          text-align: center;
        }
      }
    }
  }
}
</style>
