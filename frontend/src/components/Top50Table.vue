<template>
  <div class="top-performers-table">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="48"><Loading /></el-icon>
      <p class="loading-text">数据加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!data || data.length === 0" class="empty-state">
      <el-empty :image-size="140">
        <template #description>
          <p class="empty-title">暂无涨幅榜数据</p>
          <p class="empty-desc">请先执行数据同步获取最新行情</p>
        </template>
      </el-empty>
    </div>

    <!-- 数据展示 -->
    <div v-else class="data-content">
      <!-- 筛选工具栏 -->
      <div class="filter-toolbar">
        <div class="filter-group">
          <label class="filter-label">
            <el-icon><Location /></el-icon>
            市场
          </label>
          <el-select v-model="marketFilter" placeholder="全部市场" clearable @change="handleFilterChange">
            <el-option label="深交所" value="SZ" />
            <el-option label="上交所" value="SH" />
            <el-option label="北交所" value="BJ" />
          </el-select>
        </div>

        <div class="filter-group">
          <label class="filter-label">
            <el-icon><Grid /></el-icon>
            板块
          </label>
          <el-select v-model="boardFilter" placeholder="全部板块" clearable @change="handleFilterChange">
            <el-option label="沪主板" value="沪主板" />
            <el-option label="深主板" value="深主板" />
            <el-option label="科创板" value="科创板" />
            <el-option label="创业板" value="创业板" />
            <el-option label="北交所" value="北交所" />
          </el-select>
        </div>

        <div class="filter-stats">
          <span class="stats-text">
            显示 <strong>{{ filteredData.length }}</strong> / <strong>{{ data.length }}</strong> 只股票
          </span>
        </div>
      </div>

      <!-- 统计摘要 -->
      <div class="stats-summary" v-if="filteredData.length > 0">
        <div class="summary-item">
          <span class="summary-label">平均涨幅</span>
          <span class="summary-value" :class="getChangeClass(averageChange)">
            {{ formatPercent(averageChange) }}
          </span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
          <span class="summary-label">最高涨幅</span>
          <span class="summary-value" :class="getChangeClass(maxChange)">
            {{ formatPercent(maxChange) }}
          </span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
          <span class="summary-label">最低涨幅</span>
          <span class="summary-value" :class="getChangeClass(minChange)">
            {{ formatPercent(minChange) }}
          </span>
        </div>
      </div>

      <!-- 表格 -->
      <el-table :data="filteredData" stripe class="performers-table" @row-click="handleViewKline">
        <el-table-column type="index" label="排名" width="90" align="center">
          <template #default="{ $index }">
            <span class="rank-badge" :class="getRankClass($index)">
              {{ $index + 1 }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="股票代码" width="150" align="center">
          <template #default="{ row }">
            <span class="stock-code">{{ row.symbol || row.ts_code }}</span>
          </template>
        </el-table-column>

        <el-table-column label="股票名称" width="140" align="center">
          <template #default="{ row }">
            <span class="stock-name">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="市场" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">
              {{ row.market || '-' }}
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

        <el-table-column label="期初价格" width="120" align="right">
          <template #default="{ row }">
            <span class="price-text">{{ formatPrice(row.start_price) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="期末价格" width="120" align="right">
          <template #default="{ row }">
            <span class="price-text">{{ formatPrice(row.end_price) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="涨跌幅" width="160" align="left">
          <template #default="{ row }">
            <div class="change-cell">
              <div class="change-bar" :class="getChangeClass(row.change_pct)">
                <div
                  class="change-fill"
                  :style="{ width: getChangeBarWidth(row.change_pct) + '%' }"
                ></div>
              </div>
              <span class="change-value" :class="getChangeClass(row.change_pct)">
                {{ formatPercent(row.change_pct) }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="期初日期" width="120" align="center">
          <template #default="{ row }">
            <span class="date-text">{{ formatDate(row.start_date) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="期末日期" width="120" align="center">
          <template #default="{ row }">
            <span class="date-text">{{ formatDate(row.end_date) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" @click.stop="handleViewKline(row)">
              <el-icon><TrendCharts /></el-icon>
              K线
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Loading, Location, Grid, TrendCharts } from '@element-plus/icons-vue'
import type { TopPerformer } from '@/api/stock'

interface Props {
  data: TopPerformer[]
  loading: boolean
  period: string
}

const props = defineProps<Props>()

const router = useRouter()

// 筛选状态
const marketFilter = ref<string>('')
const boardFilter = ref<string>('')

// 过滤后的数据
const filteredData = computed(() => {
  let result = [...props.data]

  if (marketFilter.value) {
    result = result.filter(item => item.market === marketFilter.value)
  }

  if (boardFilter.value) {
    result = result.filter(item => item.board === boardFilter.value)
  }

  return result
})

// 统计数据
const averageChange = computed(() => {
  if (!filteredData.value?.length) return 0
  const sum = filteredData.value.reduce((acc, item) => acc + item.change_pct, 0)
  return sum / filteredData.value.length
})

const maxChange = computed(() => {
  if (!filteredData.value?.length) return 0
  return Math.max(...filteredData.value.map(item => item.change_pct))
})

const minChange = computed(() => {
  if (!filteredData.value?.length) return 0
  return Math.min(...filteredData.value.map(item => item.change_pct))
})

// 方法
const handleFilterChange = () => {
  // 筛选逻辑由computed自动处理
}

const getRankClass = (index: number) => {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

const getBoardTagType = (board: string) => {
  const tagTypeMap: Record<string, string> = {
    '沪主板': 'primary',
    '深主板': 'success',
    '科创板': 'danger',
    '创业板': 'warning',
    '北交所': 'info',
  }
  return tagTypeMap[board] || undefined // ✅ 返回undefined而不是空字符串，ElTag会使用默认样式
}

const getChangeClass = (change: number) => {
  if (change > 0) return 'up'
  if (change < 0) return 'down'
  return 'flat'
}

const getChangeBarWidth = (change: number) => {
  // 计算相对最大涨幅的百分比
  const maxRef = Math.max(Math.abs(maxChange.value), Math.abs(minChange.value))
  if (maxRef === 0) return 0
  return Math.min(Math.abs(change) / maxRef * 100, 100)
}

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatPercent = (percent: number) => {
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return dateStr.substring(5) // 只显示 MM-DD
}

const handleViewKline = (stock: TopPerformer) => {
  router.push({
    name: 'StockKline',
    params: { tsCode: stock.ts_code },
    query: { name: stock.name },
  })
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.top-performers-table {
  // 加载状态
  .loading-state {
    @include flex-center;
    flex-direction: column;
    padding: $spacing-16 0;
    gap: $spacing-4;

    .loading-text {
      margin: 0;
      color: $text-secondary;
      font-size: $font-size-md;
    }
  }

  // 空状态
  .empty-state {
    padding: $spacing-10 0;

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

  // 数据内容
  .data-content {
    // 筛选工具栏
    .filter-toolbar {
      @include flex-between;
      align-items: center;
      padding: $spacing-4;
      margin-bottom: $spacing-4;
      background: $bg-base;
      border-radius: $border-radius-md;
      flex-wrap: wrap;
      gap: $spacing-4;

      .filter-group {
        display: flex;
        align-items: center;
        gap: $spacing-3;

        .filter-label {
          display: flex;
          align-items: center;
          gap: $spacing-1;
          font-size: $font-size-sm;
          font-weight: $font-weight-medium;
          color: $text-secondary;
          white-space: nowrap;
        }

        :deep(.el-select) {
          width: 140px;
        }
      }

      .filter-stats {
        margin-left: auto;

        .stats-text {
          font-size: $font-size-sm;
          color: $text-tertiary;

          strong {
            color: $primary-color;
            font-weight: $font-weight-semibold;
          }
        }
      }
    }

    // 统计摘要
    .stats-summary {
      display: flex;
      align-items: center;
      padding: $spacing-5;
      margin-bottom: $spacing-5;
      background: linear-gradient(135deg, $up-bg 0%, $down-bg 100%);
      border-radius: $border-radius-md;

      .summary-item {
        flex: 1;
        text-align: center;

        .summary-label {
          display: block;
          font-size: $font-size-sm;
          color: $text-secondary;
          margin-bottom: $spacing-2;
        }

        .summary-value {
          font-size: $font-size-xl;
          font-weight: $font-weight-bold;

          &.up {
            color: $up-color;
          }

          &.down {
            color: $down-color;
          }

          &.flat {
            color: $flat-color;
          }
        }
      }

      .summary-divider {
        width: 1px;
        height: 40px;
        background: $border-base;
      }
    }

    // 表格
    .performers-table {
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
        min-width: 36px;
        height: 36px;
        line-height: 36px;
        text-align: center;
        font-weight: $font-weight-bold;
        font-size: $font-size-base;
        background: $bg-base;
        border-radius: $border-radius-sm;
        color: $text-secondary;

        &.rank-1 {
          background: linear-gradient(135deg, $up-color 0%, #ff4d4f 100%);
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
          background: linear-gradient(135deg, $primary-color 0%, #40a9ff 100%);
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

      .price-text {
        font-family: $font-family-code;
        font-size: $font-size-sm;
        color: $text-secondary;
      }

      .date-text {
        font-family: $font-family-code;
        font-size: $font-size-xs;
        color: $text-tertiary;
      }

      .text-muted {
        color: $text-quaternary;
      }

      .change-cell {
        display: flex;
        align-items: center;
        gap: $spacing-2;

        .change-bar {
          position: relative;
          flex: 1;
          height: 8px;
          background: $bg-base;
          border-radius: $border-radius-sm;
          overflow: hidden;

          .change-fill {
            height: 100%;
            border-radius: $border-radius-sm;
            transition: width $transition-slow $easing-cubic;
          }

          &.up .change-fill {
            background: linear-gradient(90deg, $up-color 0%, #ff4d4f 100%);
          }

          &.down .change-fill {
            background: linear-gradient(90deg, $down-color 0%, #73d13d 100%);
          }

          &.flat .change-fill {
            background: $flat-color;
          }
        }

        .change-value {
          font-family: $font-family-code;
          font-weight: $font-weight-semibold;
          font-size: $font-size-sm;
          min-width: 70px;
          text-align: right;

          &.up {
            color: $up-color;
          }

          &.down {
            color: $down-color;
          }

          &.flat {
            color: $flat-color;
          }
        }
      }
    }
  }
}

// 响应式
@include respond-below('md') {
  .top-performers-table {
    .data-content {
      .filter-toolbar {
        flex-direction: column;
        align-items: stretch;

        .filter-group {
          :deep(.el-select) {
            width: 100%;
          }
        }

        .filter-stats {
          margin-left: 0;
          text-align: center;
        }
      }

      .stats-summary {
        flex-direction: column;
        gap: $spacing-4;

        .summary-divider {
          width: 100%;
          height: 1px;
        }
      }
    }
  }
}
</style>
