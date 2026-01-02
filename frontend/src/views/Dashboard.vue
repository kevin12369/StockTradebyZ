<template>
  <div class="dashboard-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon class="title-icon"><TrendCharts /></el-icon>
          投研工作台
        </h1>
        <p class="page-subtitle">智能选股 · 数据分析 · 策略回测</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Refresh" @click="refreshAll">
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 市场概览 -->
    <section class="dashboard-section">
      <div class="section-header">
        <h2 class="section-title">
          <el-icon><DataLine /></el-icon>
          市场概览
        </h2>
        <el-tag size="small" type="info">{{ currentTime }}</el-tag>
      </div>
      <div class="market-overview">
        <div
          v-for="index in marketIndices"
          :key="index.code"
          class="index-card"
          :class="{ up: index.change > 0, down: index.change < 0 }"
        >
          <div class="index-header">
            <span class="index-name">{{ index.name }}</span>
            <el-tag :type="index.change > 0 ? 'danger' : index.change < 0 ? 'success' : 'info'" size="small">
              {{ index.code }}
            </el-tag>
          </div>
          <div class="index-value" :class="getChangeClass(index.change)">
            {{ index.value?.toFixed(2) || '--' }}
          </div>
          <div class="index-change" :class="getChangeClass(index.change)">
            <span class="change-icon">
              <el-icon v-if="index.change > 0"><CaretTop /></el-icon>
              <el-icon v-else-if="index.change < 0"><CaretBottom /></el-icon>
              <span v-else>-</span>
            </span>
            <span class="change-value">{{ index.change?.toFixed(2) || '--' }}</span>
            <span class="change-percent">({{ index.changePercent?.toFixed(2) || '--' }}%)</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 涨跌统计 -->
    <section class="dashboard-section">
      <div class="section-header">
        <h2 class="section-title">
          <el-icon><PieChart /></el-icon>
          涨跌统计
        </h2>
      </div>
      <div class="stats-grid">
        <div class="stat-card stat-up">
          <div class="stat-icon">
            <el-icon :size="32"><CaretTop /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ marketStats.upCount || 0 }}</div>
            <div class="stat-label">上涨家数</div>
            <div class="stat-percent">{{ marketStats.upPercent || 0 }}%</div>
          </div>
        </div>
        <div class="stat-card stat-flat">
          <div class="stat-icon">
            <el-icon :size="32"><Minus /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ marketStats.flatCount || 0 }}</div>
            <div class="stat-label">平盘家数</div>
            <div class="stat-percent">{{ marketStats.flatPercent || 0 }}%</div>
          </div>
        </div>
        <div class="stat-card stat-down">
          <div class="stat-icon">
            <el-icon :size="32"><CaretBottom /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ marketStats.downCount || 0 }}</div>
            <div class="stat-label">下跌家数</div>
            <div class="stat-percent">{{ marketStats.downPercent || 0 }}%</div>
          </div>
        </div>
        <div class="stat-card stat-limit">
          <div class="stat-icon">
            <el-icon :size="32"><Trophy /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              <span class="limit-up">{{ marketStats.limitUp || 0 }}</span>
              <span class="separator">/</span>
              <span class="limit-down">{{ marketStats.limitDown || 0 }}</span>
            </div>
            <div class="stat-label">涨停 / 跌停</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 左侧：最新选股结果 -->
      <section class="dashboard-section main-content">
        <div class="section-header">
          <h2 class="section-title">
            <el-icon><MagicStick /></el-icon>
            最新选股结果
          </h2>
          <el-button text type="primary" @click="goToPage('/strategies')">
            查看全部
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </div>

        <!-- 策略筛选 -->
        <div v-if="recentResults.length > 0" class="strategy-tabs">
          <el-radio-group v-model="selectedStrategy" size="small" @change="loadRecentResults">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button v-for="strategy in strategies" :key="strategy.id" :label="strategy.id">
              {{ strategy.name }}
            </el-radio-button>
          </el-radio-group>
        </div>

        <!-- 选股结果列表 -->
        <div v-loading="loadingResults" class="results-list">
          <div v-if="safeRecentResults.length === 0 && !loadingResults" class="empty-state">
            <el-empty description="暂无选股结果">
              <el-button type="primary" @click="goToPage('/strategies/wizard')">
                创建选股策略
              </el-button>
            </el-empty>
          </div>
          <div v-else class="result-cards">
            <div
              v-for="result in safeRecentResults.slice(0, 6)"
              :key="result.id"
              class="result-card"
              @click="viewStockDetail(result.stock_code)"
            >
              <div class="result-header">
                <div class="stock-info">
                  <span class="stock-code">{{ result.stock_code }}</span>
                  <span class="stock-name">{{ result.stock_name || '未知' }}</span>
                </div>
                <div class="result-actions">
                  <el-button size="small" text @click.stop="viewKline(result.stock_code)">
                    <el-icon><TrendCharts /></el-icon>
                    K线
                  </el-button>
                </div>
              </div>
              <div class="result-body">
                <div class="strategy-tag">
                  <el-tag size="small" type="primary">{{ result.strategy_name || '未知策略' }}</el-tag>
                </div>
                <div class="result-meta">
                  <span class="meta-item">
                    <el-icon><Calendar /></el-icon>
                    {{ formatDate(result.created_at) }}
                  </span>
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    {{ formatTime(result.created_at) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧：涨幅榜 + 快捷操作 -->
      <div class="side-content">
        <!-- 日涨幅榜 Top 10 -->
        <section class="dashboard-section">
          <div class="section-header">
            <h2 class="section-title">
              <el-icon><Trophy /></el-icon>
              日涨幅榜 Top 10
            </h2>
            <el-button text type="primary" size="small" @click="goToPage('/top-performers?period=1day')">
              更多
            </el-button>
          </div>
          <div v-loading="loadingTopPerformers" class="top-list">
            <div v-if="safeTopPerformers.length === 0 && !loadingTopPerformers" class="empty-state">
              <el-empty description="暂无数据" :image-size="80" />
            </div>
            <div v-else class="top-items">
              <div
                v-for="(item, index) in safeTopPerformers.slice(0, 10)"
                :key="item.code || item.stock_code"
                class="top-item"
                @click="viewStockDetail(item.code || item.stock_code)"
              >
                <div class="top-rank" :class="`rank-${index + 1}`">
                  {{ index + 1 }}
                </div>
                <div class="top-info">
                  <div class="top-stock">
                    <span class="stock-code">{{ item.code || item.stock_code }}</span>
                    <span class="stock-name">{{ item.name || item.stock_name }}</span>
                  </div>
                </div>
                <div class="top-change" :class="getChangeClass(item.change_percent)">
                  {{ item.change_percent?.toFixed(2) }}%
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 快捷操作 -->
        <section class="dashboard-section">
          <div class="section-header">
            <h2 class="section-title">
              <el-icon><Grid /></el-icon>
              快捷操作
            </h2>
          </div>
          <div class="quick-actions">
            <div class="action-item" @click="goToPage('/stocks')">
              <div class="action-icon blue">
                <el-icon :size="24"><Download /></el-icon>
              </div>
              <div class="action-content">
                <div class="action-title">数据同步</div>
                <div class="action-desc">更新股票数据</div>
              </div>
            </div>
            <div class="action-item" @click="goToPage('/strategies/wizard')">
              <div class="action-icon green">
                <el-icon :size="24"><MagicStick /></el-icon>
              </div>
              <div class="action-content">
                <div class="action-title">新建策略</div>
                <div class="action-desc">创建选股策略</div>
              </div>
            </div>
            <div class="action-item" @click="executeStrategy">
              <div class="action-icon orange">
                <el-icon :size="24"><CaretRight /></el-icon>
              </div>
              <div class="action-content">
                <div class="action-title">执行选股</div>
                <div class="action-desc">运行策略</div>
              </div>
            </div>
            <div class="action-item" @click="goToPage('/config')">
              <div class="action-icon purple">
                <el-icon :size="24"><Setting /></el-icon>
              </div>
              <div class="action-content">
                <div class="action-title">策略配置</div>
                <div class="action-desc">管理参数</div>
              </div>
            </div>
          </div>
        </section>

        <!-- 系统状态 -->
        <section class="dashboard-section">
          <div class="section-header">
            <h2 class="section-title">
              <el-icon><Monitor /></el-icon>
              系统状态
            </h2>
          </div>
          <div class="system-status">
            <div class="status-item">
              <span class="status-label">后端API</span>
              <el-tag :type="systemStatus.api ? 'success' : 'danger'" size="small">
                {{ systemStatus.api ? '正常' : '异常' }}
              </el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">数据库</span>
              <el-tag :type="systemStatus.database ? 'success' : 'danger'" size="small">
                {{ systemStatus.database ? '已连接' : '未连接' }}
              </el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">股票数据</span>
              <el-tag type="info" size="small">
                {{ stockCount }} 只
              </el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">最后同步</span>
              <span class="status-value">{{ lastSyncTime || '未同步' }}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  DataLine,
  PieChart,
  MagicStick,
  Trophy,
  Grid,
  Monitor,
  Refresh,
  ArrowRight,
  Download,
  CaretRight,
  Setting,
  CaretTop,
  CaretBottom,
  Minus,
  Calendar,
  Clock,
} from '@element-plus/icons-vue'
import { request } from '@/api/client'

const router = useRouter()

// ========== 状态数据 ==========
const loadingResults = ref(false)
const loadingTopPerformers = ref(false)
const selectedStrategy = ref('all')

// 市场指数
const marketIndices = ref([
  { code: '000001', name: '上证指数', value: 3245.67, change: 1.23, changePercent: 0.38 },
  { code: '399001', name: '深证成指', value: 11234.56, change: -0.45, changePercent: -0.04 },
  { code: '399006', name: '创业板指', value: 2234.89, change: 2.34, changePercent: 0.11 },
  { code: '000300', name: '沪深300', value: 3876.54, change: 0.89, changePercent: 0.23 },
])

// 市场统计
const marketStats = ref({
  upCount: 2345,
  upPercent: 52.3,
  flatCount: 123,
  flatPercent: 2.7,
  downCount: 2012,
  downPercent: 45.0,
  limitUp: 45,
  limitDown: 12,
})

// 最新选股结果
const recentResults = ref<any[]>([])
const strategies = ref([
  { id: 1, name: 'MA金叉' },
  { id: 2, name: 'BBI多头' },
  { id: 3, name: 'KDJ金叉' },
])

// 涨幅榜
const topPerformers = ref<any[]>([])

// 系统状态
const systemStatus = ref({
  api: true,
  database: true,
})

const stockCount = ref(0)
const lastSyncTime = ref('')

// ========== 计算属性 ==========
const currentTime = computed(() => {
  const now = new Date()
  return now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'long',
  })
})

// 安全选股结果 - 确保永远是数组，防止.slice()报错
const safeRecentResults = computed(() => {
  return Array.isArray(recentResults.value) ? recentResults.value : []
})

// 安全涨幅榜 - 确保永远是数组
const safeTopPerformers = computed(() => {
  return Array.isArray(topPerformers.value) ? topPerformers.value : []
})

// ========== 方法 ==========
const getChangeClass = (change: number | undefined) => {
  if (!change) return 'flat'
  return change > 0 ? 'up' : change < 0 ? 'down' : 'flat'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '--'
  return dateStr.split(' ')[0]
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return '--'
  return dateStr.split(' ')[1]?.slice(0, 5) || '--'
}

const refreshAll = () => {
  ElMessage.success('数据刷新成功')
  loadMarketData()
  loadRecentResults()
  loadTopPerformers()
}

const goToPage = (path: string) => {
  router.push(path)
}

const viewStockDetail = (stockCode: string) => {
  router.push(`/stocks/${stockCode}`)
}

const viewKline = (stockCode: string) => {
  router.push(`/kline/${stockCode}`)
}

const executeStrategy = () => {
  ElMessage.info('请先在"策略配置"中选择或创建策略')
  router.push('/strategies')
}

// ========== 数据加载 ==========
const loadMarketData = async () => {
  try {
    // 从后端API加载真实的市场数据
    const data = await request.get('/stocks/realtime/market-overview')

    // 更新市场指数
    if (data.indices && Array.isArray(data.indices)) {
      marketIndices.value = data.indices
    }

    // 更新涨跌统计
    if (data.stats) {
      marketStats.value = data.stats
    }
  } catch (error: any) {
    console.error('加载市场数据失败:', error)
    // 失败时保持原有的默认值
    if (error.response?.status !== 404) {
      ElMessage.error('加载市场数据失败')
    }
  }
}

const loadRecentResults = async () => {
  try {
    loadingResults.value = true
    const data = await request.get('/strategies/results', {
      limit: 10,
      strategy_id: selectedStrategy.value === 'all' ? undefined : selectedStrategy.value,
    })
    recentResults.value = Array.isArray(data) ? data : []
  } catch (error: any) {
    console.error('加载选股结果失败:', error)
    recentResults.value = [] // 确保在错误时设置为空数组
    if (error.response?.status !== 404) {
      // 404表示没有数据，不算错误
      ElMessage.error('加载选股结果失败')
    }
  } finally {
    loadingResults.value = false
  }
}

const loadTopPerformers = async () => {
  try {
    loadingTopPerformers.value = true
    // 使用新的实时涨跌幅API（东方财富数据源）
    const data = await request.get('/stocks/realtime/top-gainers', {
      limit: 10,
    })
    // request.get 自动解析 response.data.data
    topPerformers.value = Array.isArray(data?.items) ? data.items : []
  } catch (error: any) {
    console.error('加载涨幅榜失败:', error)
    topPerformers.value = [] // 确保在错误时设置为空数组
    if (error.response?.status !== 404) {
      ElMessage.error('加载涨幅榜失败')
    }
  } finally {
    loadingTopPerformers.value = false
  }
}

const loadSystemStatus = async () => {
  try {
    // TODO: 等后端API实现后再启用
    // const [statusRes, stocksRes] = await Promise.all([
    //   axios.get('/api/v1/system/status').catch(() => null),
    //   axios.get('/api/v1/stocks/stats').catch(() => null),
    // ])

    // if (statusRes) {
    //   systemStatus.value = statusRes.data
    // }
    // if (stocksRes) {
    //   stockCount.value = stocksRes.data?.total || 0
    //   lastSyncTime.value = stocksRes.data?.last_sync || ''
    // }

    // 暂时使用模拟数据
    systemStatus.value = {
      api: true,
      database: true,
    }
    stockCount.value = 0
    lastSyncTime.value = ''
  } catch (error: any) {
    console.error('加载系统状态失败:', error)
    // 404表示后端API未实现，不算错误
    if (error.response?.status !== 404) {
      ElMessage.error('加载系统状态失败')
    }
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  loadMarketData()
  loadRecentResults()
  loadTopPerformers()
  loadSystemStatus()
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.dashboard-page {
  min-height: 100%;
  padding: $spacing-4;

  .page-header {
    @include flex-between;
    margin-bottom: $spacing-6;
    padding: $spacing-6;
    background: linear-gradient(135deg, #1890ff 0%, #52c41a 100%);
    border-radius: $border-radius-lg;
    color: #fff;
    box-shadow: $shadow-3;

    .header-content {
      .page-title {
        display: flex;
        align-items: center;
        gap: $spacing-3;
        margin: 0 0 $spacing-1 0;
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
        font-weight: $font-weight-normal;
      }
    }

    .header-actions {
      :deep(.el-button) {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.3);
        color: #fff;

        &:hover {
          background: rgba(255, 255, 255, 0.3);
          border-color: rgba(255, 255, 255, 0.5);
        }
      }
    }
  }

  .dashboard-section {
    background: $card-bg;
    border-radius: $border-radius-md;
    padding: $spacing-5;
    margin-bottom: $spacing-5;
    box-shadow: $card-shadow;

    .section-header {
      @include flex-between;
      margin-bottom: $spacing-5;
      padding-bottom: $spacing-4;
      border-bottom: 1px solid $border-light;

      .section-title {
        display: flex;
        align-items: center;
        gap: $spacing-2;
        margin: 0;
        font-size: $font-size-xl;
        font-weight: $font-weight-semibold;
        color: $text-primary;

        .el-icon {
          font-size: $font-size-xxl;
          color: $primary-color;
        }
      }
    }
  }

  // 市场概览
  .market-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: $spacing-4;

    .index-card {
      padding: $spacing-4;
      border-radius: $border-radius-md;
      background: $bg-base;
      border: 2px solid transparent;
      transition: all $transition-base $easing-cubic;
      cursor: pointer;

      &:hover {
        transform: translateY(-2px);
        box-shadow: $shadow-3;
      }

      &.up {
        border-color: $up-bg;
        background: $up-bg;
      }

      &.down {
        border-color: $down-bg;
        background: $down-bg;
      }

      .index-header {
        @include flex-between;
        margin-bottom: $spacing-3;

        .index-name {
          font-size: $font-size-md;
          font-weight: $font-weight-semibold;
          color: $text-secondary;
        }
      }

      .index-value {
        font-size: $font-size-xxl;
        font-weight: $font-weight-bold;
        margin-bottom: $spacing-2;

        &.up {
          color: $up-color;
        }

        &.down {
          color: $down-color;
        }
      }

      .index-change {
        display: flex;
        align-items: center;
        gap: $spacing-1;
        font-size: $font-size-sm;
        font-weight: $font-weight-medium;

        &.up {
          color: $up-color;
        }

        &.down {
          color: $down-color;
        }

        .change-icon {
          font-size: $font-size-lg;
        }
      }
    }
  }

  // 涨跌统计
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: $spacing-4;

    .stat-card {
      display: flex;
      align-items: center;
      gap: $spacing-4;
      padding: $spacing-4;
      border-radius: $border-radius-md;
      background: $bg-base;

      .stat-icon {
        width: 56px;
        height: 56px;
        border-radius: $border-radius-md;
        @include flex-center;
        font-size: 24px;
      }

      .stat-content {
        flex: 1;

        .stat-value {
          font-size: $font-size-xxl;
          font-weight: $font-weight-bold;
          line-height: 1;
          margin-bottom: $spacing-2;
        }

        .stat-label {
          font-size: $font-size-sm;
          color: $text-tertiary;
          margin-bottom: $spacing-1;
        }

        .stat-percent {
          font-size: $font-size-xs;
          color: $text-tertiary;
        }
      }

      &.stat-up {
        background: $up-bg;

        .stat-icon {
          background: rgba($up-color, 0.1);
          color: $up-color;
        }

        .stat-value {
          color: $up-color;
        }
      }

      &.stat-down {
        background: $down-bg;

        .stat-icon {
          background: rgba($down-color, 0.1);
          color: $down-color;
        }

        .stat-value {
          color: $down-color;
        }
      }

      &.stat-flat {
        background: #fafafa;

        .stat-icon {
          background: rgba($flat-color, 0.1);
          color: $flat-color;
        }

        .stat-value {
          color: $flat-color;
        }
      }

      &.stat-limit {
        background: linear-gradient(135deg, $up-bg 50%, $down-bg 50%);

        .stat-icon {
          background: #fff;
          color: $primary-color;
        }

        .stat-value {
          font-size: $font-size-xl;

          .limit-up {
            color: $up-color;
          }

          .limit-down {
            color: $down-color;
          }

          .separator {
            margin: 0 $spacing-2;
            color: $text-tertiary;
          }
        }
      }
    }
  }

  // 主要内容区域
  .dashboard-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: $spacing-5;

    @include respond-below('xl') {
      grid-template-columns: 1fr;
    }
  }

  // 最新选股结果
  .strategy-tabs {
    margin-bottom: $spacing-4;
  }

  .results-list {
    min-height: 200px;

    .result-cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: $spacing-4;

      .result-card {
        padding: $spacing-4;
        border: 1px solid $border-light;
        border-radius: $border-radius-md;
        background: $bg-base;
        cursor: pointer;
        transition: all $transition-base $easing-cubic;

        &:hover {
          border-color: $primary-color;
          box-shadow: $shadow-3;
          transform: translateY(-2px);
        }

        .result-header {
          @include flex-between;
          margin-bottom: $spacing-3;
          padding-bottom: $spacing-3;
          border-bottom: 1px solid $border-lighter;

          .stock-info {
            .stock-code {
              font-size: $font-size-lg;
              font-weight: $font-weight-bold;
              color: $text-primary;
              margin-right: $spacing-2;
            }

            .stock-name {
              font-size: $font-size-sm;
              color: $text-secondary;
            }
          }
        }

        .result-body {
          .strategy-tag {
            margin-bottom: $spacing-3;
          }

          .result-meta {
            display: flex;
            gap: $spacing-4;
            font-size: $font-size-xs;
            color: $text-tertiary;

            .meta-item {
              display: flex;
              align-items: center;
              gap: 4px;
            }
          }
        }
      }
    }
  }

  // 涨幅榜
  .top-list {
    min-height: 200px;

    .top-items {
      .top-item {
        display: flex;
        align-items: center;
        gap: $spacing-3;
        padding: $spacing-3;
        border-radius: $border-radius-base;
        cursor: pointer;
        transition: background-color $transition-fast;

        &:hover {
          background: $bg-base;
        }

        .top-rank {
          min-width: 28px;
          height: 28px;
          @include flex-center;
          font-weight: $font-weight-bold;
          font-size: $font-size-sm;
          background: $bg-base;
          border-radius: $border-radius-sm;

          &.rank-1 {
            background: $up-color;
            color: #fff;
            font-size: $font-size-md;
          }

          &.rank-2 {
            background: #fa8c16;
            color: #fff;
          }

          &.rank-3 {
            background: $primary-color;
            color: #fff;
          }
        }

        .top-info {
          flex: 1;

          .top-stock {
            .stock-code {
              font-weight: $font-weight-semibold;
              margin-right: $spacing-2;
            }

            .stock-name {
              font-size: $font-size-sm;
              color: $text-tertiary;
            }
          }
        }

        .top-change {
          font-family: $font-family-code;
          font-weight: $font-weight-semibold;
          padding: 2px 8px;
          border-radius: $border-radius-sm;

          &.up {
            color: $up-color;
            background: $up-bg;
          }

          &.down {
            color: $down-color;
            background: $down-bg;
          }
        }
      }
    }
  }

  // 快捷操作
  .quick-actions {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-3;

    .action-item {
      display: flex;
      align-items: center;
      gap: $spacing-3;
      padding: $spacing-3;
      border: 1px solid $border-light;
      border-radius: $border-radius-md;
      cursor: pointer;
      transition: all $transition-base $easing-cubic;

      &:hover {
        border-color: $primary-color;
        background: $primary-light;
        transform: translateY(-2px);
        box-shadow: $shadow-2;
      }

      .action-icon {
        width: 48px;
        height: 48px;
        border-radius: $border-radius-md;
        @include flex-center;

        &.blue {
          background: rgba($primary-color, 0.1);
          color: $primary-color;
        }

        &.green {
          background: rgba($success-color, 0.1);
          color: $success-color;
        }

        &.orange {
          background: rgba($warning-color, 0.1);
          color: $warning-color;
        }

        &.purple {
          background: rgba($danger-color, 0.1);
          color: $danger-color;
        }
      }

      .action-content {
        .action-title {
          font-size: $font-size-md;
          font-weight: $font-weight-semibold;
          color: $text-primary;
          margin-bottom: 2px;
        }

        .action-desc {
          font-size: $font-size-xs;
          color: $text-tertiary;
        }
      }
    }
  }

  // 系统状态
  .system-status {
    display: flex;
    flex-direction: column;
    gap: $spacing-3;

    .status-item {
      @include flex-between;
      padding: $spacing-3;
      background: $bg-base;
      border-radius: $border-radius-base;

      .status-label {
        font-size: $font-size-sm;
        color: $text-secondary;
      }

      .status-value {
        font-size: $font-size-sm;
        color: $text-primary;
      }
    }
  }
}
</style>
