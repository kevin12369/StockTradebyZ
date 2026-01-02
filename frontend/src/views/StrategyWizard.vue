<template>
  <div class="strategy-wizard-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">
          <el-icon class="title-icon"><Guide /></el-icon>
          策略选股向导
        </h1>
        <p class="page-subtitle">4步完成智能选股 · 策略配置 · 执行分析</p>
      </div>
    </div>

    <!-- 向导卡片 -->
    <div class="wizard-card">
      <!-- 步骤导航 -->
      <div class="wizard-header">
        <el-steps :active="currentStep" finish-status="success" align-center class="wizard-steps">
          <el-step title="选择策略" description="选择要执行的策略组合" />
          <el-step title="设置参数" description="配置策略执行参数" />
          <el-step title="执行选股" description="执行策略并查看进度" />
          <el-step title="查看结果" description="查看选股结果和详情" />
        </el-steps>
      </div>

      <!-- 步骤内容 -->
      <div class="wizard-content">
        <!-- 步骤1：选择策略 -->
        <div v-show="currentStep === 0" class="step-content">
          <div class="step-header">
            <h3 class="step-title">
              <el-icon><MagicStick /></el-icon>
              选择要执行的策略
            </h3>
            <p class="step-description">请至少选择一个策略，可选择多个策略进行组合分析</p>
          </div>

          <div v-loading="loadingStrategies" class="strategy-cards">
            <div
              v-for="strategy in strategies"
              :key="strategy.id"
              :class="['strategy-card', { selected: isStrategySelected(strategy.id) }]"
              @click="toggleStrategy(strategy.id)"
            >
              <div class="card-icon">
                <el-icon><MagicStick /></el-icon>
              </div>
              <div class="card-content">
                <div class="card-header">
                  <div class="card-title">
                    <el-checkbox :model-value="isStrategySelected(strategy.id)" @change="toggleStrategy(strategy.id)">
                      {{ strategy.alias }}
                    </el-checkbox>
                    <el-tag v-if="!strategy.is_active" type="info" size="small">已禁用</el-tag>
                  </div>
                </div>
                <div class="card-body">
                  <p class="description">{{ strategy.description || '暂无描述' }}</p>
                  <div class="meta-info">
                    <el-tag size="small" type="info">{{ strategy.class_name }}</el-tag>
                  </div>
                </div>
              </div>
              <div class="card-check">
                <el-icon v-if="isStrategySelected(strategy.id)"><CircleCheckFilled /></el-icon>
              </div>
            </div>
          </div>

          <div class="step-actions">
            <el-button type="primary" :disabled="selectedStrategies.length === 0" @click="nextStep" size="large">
              下一步
              <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 步骤2：设置参数 -->
        <div v-show="currentStep === 1" class="step-content">
          <div class="step-header">
            <h3 class="step-title">
              <el-icon><Setting /></el-icon>
              配置执行参数
            </h3>
            <p class="step-description">设置选股日期和各策略的参数</p>
          </div>

          <div class="params-form">
            <!-- 全局参数 -->
            <div class="form-section">
              <h4 class="section-title">
                <el-icon><Grid /></el-icon>
                全局参数
              </h4>
              <el-form :model="params" label-width="120px">
                <el-form-item label="选股日期">
                  <el-date-picker
                    v-model="params.trade_date"
                    type="date"
                    placeholder="选择日期（默认为最新交易日）"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    clearable
                    style="width: 100%"
                  />
                  <div class="form-tip">留空则使用最新交易日</div>
                </el-form-item>

                <el-form-item label="选股模式">
                  <el-radio-group v-model="params.mode">
                    <el-radio value="union">并集模式（所有策略的并集）</el-radio>
                    <el-radio value="intersection">交集模式（所有策略的交集）</el-radio>
                    <el-radio value="separate">分别执行（各策略独立）</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-form>
            </div>

            <!-- 各策略参数 -->
            <div class="form-section">
              <h4 class="section-title">
                <el-icon><List /></el-icon>
                策略参数
              </h4>
              <div
                v-for="strategyId in selectedStrategies"
                :key="strategyId"
                class="strategy-params"
              >
                <div class="strategy-params-header">
                  <div class="strategy-info">
                    <div class="strategy-icon">
                      <el-icon><MagicStick /></el-icon>
                    </div>
                    <h5>{{ getStrategyById(strategyId)?.alias }}</h5>
                  </div>
                  <el-button text type="primary" @click="editStrategyParams(strategyId)">
                    <el-icon><Edit /></el-icon>
                    编辑参数
                  </el-button>
                </div>
                <div class="strategy-params-preview">
                  <pre>{{ formatStrategyParams(strategyId) }}</pre>
                </div>
              </div>
            </div>
          </div>

          <div class="step-actions">
            <el-button @click="prevStep" size="large">上一步</el-button>
            <el-button type="primary" @click="nextStep" size="large">
              下一步
              <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 步骤3：执行选股 -->
        <div v-show="currentStep === 2" class="step-content">
          <div class="step-header">
            <h3 class="step-title">
              <el-icon><VideoPlay /></el-icon>
              执行选股
            </h3>
            <p class="step-description">确认配置后点击执行按钮</p>
          </div>

          <div class="execution-summary">
            <div class="summary-card">
              <h4 class="summary-title">执行配置</h4>
              <el-descriptions :column="2" border class="summary-desc">
                <el-descriptions-item label="选股日期">
                  {{ params.trade_date || '最新交易日' }}
                </el-descriptions-item>
                <el-descriptions-item label="选股模式">
                  <el-tag :type="getModeColor(params.mode)">{{ getModeName(params.mode) }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="策略数量" :span="2">
                  <el-tag type="primary">{{ selectedStrategies.length }} 个</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="selected-strategies-list">
              <h4>已选策略</h4>
              <div class="strategy-tags">
                <el-tag
                  v-for="strategyId in selectedStrategies"
                  :key="strategyId"
                  type="success"
                  class="strategy-tag"
                  size="large"
                >
                  <el-icon><MagicStick /></el-icon>
                  {{ getStrategyById(strategyId)?.alias }}
                </el-tag>
              </div>
            </div>

            <!-- 执行进度 -->
            <div v-if="executing" class="execution-progress">
              <h4>执行进度</h4>
              <el-progress :percentage="executionProgress" :status="executionStatus" :stroke-width="20" />
              <p class="progress-text">{{ executionMessage }}</p>
            </div>

            <!-- 执行结果 -->
            <div v-if="executionResults.length > 0" class="execution-results">
              <h4>执行结果</h4>
              <div class="results-grid">
                <div
                  v-for="result in executionResults"
                  :key="result.strategy_id"
                  class="result-item"
                  :class="{ success: result.success, error: !result.success }"
                >
                  <div class="result-icon">
                    <el-icon>
                      <CircleCheckFilled v-if="result.success" />
                      <CircleCloseFilled v-else />
                    </el-icon>
                  </div>
                  <div class="result-content">
                    <div class="result-name">{{ result.strategy_alias }}</div>
                    <div class="result-stats">
                      <span>扫描: <strong>{{ result.total_stocks }}</strong> 只</span>
                      <span>选中: <strong>{{ result.selected_count }}</strong> 只</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="step-actions">
            <el-button @click="prevStep" :disabled="executing" size="large">上一步</el-button>
            <el-button
              type="primary"
              :disabled="executionResults.length > 0 || executing"
              :loading="executing"
              @click="handleExecuteStrategies"
              size="large"
            >
              <el-icon class="el-icon--left" v-if="!executing"><VideoPlay /></el-icon>
              {{ executing ? '执行中...' : '开始执行' }}
            </el-button>
            <el-button
              v-if="executionResults.length > 0"
              type="success"
              @click="nextStep"
              size="large"
            >
              查看结果
              <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 步骤4：查看结果 -->
        <div v-show="currentStep === 3" class="step-content">
          <div class="step-header">
            <h3 class="step-title">
              <el-icon><SuccessFilled /></el-icon>
              选股结果
            </h3>
            <p class="step-description">查看和管理选股结果</p>
          </div>

          <!-- 结果统计 -->
          <div class="results-stats">
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ totalSelectedCount }}</div>
                <div class="stat-label">总选中数</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);">
                <el-icon><Grid /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ unionCount }}</div>
                <div class="stat-label">并集数量</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ intersectionCount }}</div>
                <div class="stat-label">交集数量</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);">
                <el-icon><Calendar /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ resultsDate || '-' }}</div>
                <div class="stat-label">选股日期</div>
              </div>
            </div>
          </div>

          <!-- 结果工具栏 -->
          <div class="results-toolbar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索股票代码或名称..."
              clearable
              class="search-input"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>

            <el-select
              v-model="filterStrategy"
              placeholder="筛选策略"
              clearable
              class="filter-select"
            >
              <el-option
                v-for="strategyId in selectedStrategies"
                :key="strategyId"
                :label="getStrategyById(strategyId)?.alias"
                :value="strategyId"
              />
            </el-select>

            <div class="toolbar-actions">
              <el-button :icon="Refresh" @click="loadResults">
                刷新
              </el-button>
              <el-button type="primary" :icon="Download" @click="exportResults">
                导出
              </el-button>
            </div>
          </div>

          <!-- 结果列表 -->
          <el-table
            :data="filteredResults"
            stripe
            v-loading="loadingResults"
            class="results-table"
            @row-click="showStockDetail"
          >
            <el-table-column type="index" label="#" width="60" align="center" />

            <el-table-column label="股票代码" width="150" align="center">
              <template #default="{ row }">
                <span class="stock-code">{{ row.ts_code }}</span>
              </template>
            </el-table-column>

            <el-table-column label="股票名称" width="140" align="center">
              <template #default="{ row }">
                <span class="stock-name">{{ (row.reason as any)?.name || '-' }}</span>
              </template>
            </el-table-column>

            <el-table-column label="选中策略" min-width="200" align="left">
              <template #default="{ row }">
                <div class="strategy-tags-cell">
                  <el-tag
                    v-for="strategy in row.strategies"
                    :key="strategy.strategy_id"
                    size="small"
                    type="success"
                  >
                    {{ strategy.strategy_alias }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="选股日期" width="120" align="center">
              <template #default="{ row }">
                <span class="date-text">{{ row.trade_date }}</span>
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

          <!-- 分页 -->
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="[20, 50, 100, 200]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
            background
          />

          <div class="step-actions">
            <el-button @click="prevStep" size="large">上一步</el-button>
            <el-button @click="resetWizard" size="large">
              <el-icon><RefreshLeft /></el-icon>
              重新开始
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 股票详情弹窗 -->
    <StockDetailDialog
      v-model="stockDetailVisible"
      :ts-code="currentStockTsCode"
      :trade-date="params.trade_date"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Guide,
  MagicStick,
  Setting,
  VideoPlay,
  SuccessFilled,
  ArrowRight,
  Edit,
  Grid,
  List,
  Connection,
  Calendar,
  Document,
  Search,
  Refresh,
  Download,
  TrendCharts,
  CircleCheckFilled,
  CircleCloseFilled,
  RefreshLeft,
} from '@element-plus/icons-vue'
import { getStrategies, executeStrategies, getSelectionResults } from '@/api/strategy'
import type { Strategy, StrategyExecuteResponse, SelectionResult } from '@/types'
import StockDetailDialog from '@/components/strategy/StockDetailDialog.vue'

const router = useRouter()

// 当前步骤
const currentStep = ref(0)

// 数据状态
const loadingStrategies = ref(false)
const strategies = ref<Strategy[]>([])
const selectedStrategies = ref<number[]>([])

// 参数配置
const params = ref({
  trade_date: '',
  mode: 'separate' as 'union' | 'intersection' | 'separate',
  strategyParams: {} as Record<number, any>
})

// 执行状态
const executing = ref(false)
const executionProgress = ref(0)
const executionStatus = ref<'success' | 'exception' | ''>('')
const executionMessage = ref('')
const executionResults = ref<StrategyExecuteResponse[]>([])

// 结果状态
const loadingResults = ref(false)
const searchKeyword = ref('')
const filterStrategy = ref<number | undefined>(undefined)
const allResults = ref<SelectionResult[]>([])
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

// 详情弹窗
const stockDetailVisible = ref(false)
const currentStockTsCode = ref('')

// 计算属性
const filteredResults = computed(() => {
  let results = allResults.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    results = results.filter(r =>
      r.ts_code.toLowerCase().includes(keyword) ||
      (r.reason as any).name?.toLowerCase().includes(keyword)
    )
  }

  if (filterStrategy.value !== null) {
    results = results.filter(r =>
      (r as any).strategies?.some((s: any) => s.strategy_id === filterStrategy.value)
    )
  }

  return results
})

const totalSelectedCount = computed(() => allResults.value.length)

const unionCount = computed(() => {
  const uniqueCodes = new Set(allResults.value.map(r => r.ts_code))
  return uniqueCodes.size
})

const intersectionCount = computed(() => {
  if (selectedStrategies.value.length === 0) return 0
  const codeMap = new Map<string, number>()
  allResults.value.forEach(r => {
    codeMap.set(r.ts_code, (codeMap.get(r.ts_code) || 0) + 1)
  })
  return Array.from(codeMap.values()).filter(count => count === selectedStrategies.value.length).length
})

const resultsDate = computed(() => {
  return allResults.value.length > 0 ? allResults.value[0].trade_date : ''
})

// 策略相关方法
const isStrategySelected = (id: number) => selectedStrategies.value.includes(id)

const toggleStrategy = (id: number) => {
  const index = selectedStrategies.value.indexOf(id)
  if (index > -1) {
    selectedStrategies.value.splice(index, 1)
  } else {
    selectedStrategies.value.push(id)
  }
}

const getStrategyById = (id: number) => strategies.value.find(s => s.id === id)

const loadStrategies = async () => {
  loadingStrategies.value = true
  try {
    const data = await getStrategies({ is_active: true })
    strategies.value = data
  } catch (error) {
    ElMessage.error('加载策略列表失败')
  } finally {
    loadingStrategies.value = false
  }
}

// 步骤导航
const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const resetWizard = () => {
  currentStep.value = 0
  selectedStrategies.value = []
  params.value = {
    trade_date: '',
    mode: 'separate',
    strategyParams: {}
  }
  executionResults.value = []
  allResults.value = []
  searchKeyword.value = ''
  filterStrategy.value = null
}

// 参数配置
const formatStrategyParams = (strategyId: number) => {
  const strategy = getStrategyById(strategyId)
  if (!strategy) return '暂无参数'

  try {
    const config = JSON.parse(strategy.config_json || '{}')
    return JSON.stringify(config, null, 2)
  } catch {
    return strategy.config_json || '{}'
  }
}

const editStrategyParams = (strategyId: number) => {
  ElMessage.info('参数编辑功能开发中，请前往"策略配置"页面进行编辑')
  router.push({ name: 'StrategyConfig' })
}

const getModeName = (mode: string) => {
  const names = {
    union: '并集模式',
    intersection: '交集模式',
    separate: '分别执行'
  }
  return names[mode] || mode
}

const getModeColor = (mode: string) => {
  const colors = {
    union: 'primary',
    intersection: 'success',
    separate: 'warning'
  }
  return colors[mode] || 'info'
}

// 执行选股
const handleExecuteStrategies = async () => {
  if (selectedStrategies.value.length === 0) {
    ElMessage.warning('请至少选择一个策略')
    return
  }

  executing.value = true
  executionProgress.value = 0
  executionStatus.value = ''
  executionMessage.value = '正在执行选股...'
  executionResults.value = []

  try {
    const results = await executeStrategies({
      strategy_ids: selectedStrategies.value,
      trade_date: params.value.trade_date || undefined
    })

    executionResults.value = results
    executionProgress.value = 100

    const successCount = results.filter(r => r.success).length
    const totalCount = results.reduce((sum, r) => sum + (r.selected_count || 0), 0)

    if (successCount === results.length) {
      executionStatus.value = 'success'
      executionMessage.value = `执行完成！共选中 ${totalCount} 只股票`
      ElMessage.success(executionMessage.value)

      setTimeout(() => {
        nextStep()
      }, 1000)
    } else {
      executionStatus.value = 'exception'
      executionMessage.value = `部分策略执行失败`
      ElMessage.warning(executionMessage.value)
    }
  } catch (error) {
    executionStatus.value = 'exception'
    executionMessage.value = '执行失败，请稍后重试'
    ElMessage.error('执行选股失败')
  } finally {
    executing.value = false
  }
}

// 结果相关
const loadResults = async () => {
  loadingResults.value = true
  try {
    const result = await getSelectionResults({
      trade_date: params.value.trade_date || undefined,
      page: 1,
      page_size: 500
    })

    allResults.value = result.items.map(item => ({
      ...item,
      strategies: [{ strategy_id: item.strategy_id, strategy_alias: (item.reason as any).strategy_alias || '' }]
    }))

    pagination.value.total = result.total

    ElMessage.success(`加载了 ${result.items.length} 条选股结果`)
  } catch (error) {
    console.error('加载选股结果失败:', error)
    ElMessage.error('加载选股结果失败')
  } finally {
    loadingResults.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
}

const handlePageSizeChange = (size: number) => {
  pagination.value.page_size = size
  pagination.value.page = 1
}

const exportResults = () => {
  ElMessage.info('导出功能开发中')
}

// 详情相关
const showStockDetail = (row: SelectionResult) => {
  currentStockTsCode.value = row.ts_code
  stockDetailVisible.value = true
}

const viewKline = (tsCode: string) => {
  router.push({ name: 'StockKline', params: { tsCode } })
}

// 生命周期
onMounted(() => {
  loadStrategies()
})

watch(currentStep, async (newStep) => {
  if (newStep === 3) {
    await loadResults()
  }
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.strategy-wizard-page {
  padding: $spacing-4;

  // 页面标题
  .page-header {
    margin-bottom: $spacing-6;
    padding: $spacing-6;
    background: linear-gradient(135deg, #fa8c16 0%, #ffc53d 100%);
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
  }

  // 向导卡片
  .wizard-card {
    background: $card-bg;
    border-radius: $border-radius-lg;
    box-shadow: $shadow-2;
    overflow: hidden;

    .wizard-header {
      padding: $spacing-6;
      background: $bg-base;
      border-bottom: 1px solid $border-light;

      .wizard-steps {
        :deep(.el-step__title) {
          font-weight: $font-weight-semibold;
        }
      }
    }

    .wizard-content {
      padding: $spacing-6;
      min-height: 600px;

      .step-content {
        .step-header {
          margin-bottom: $spacing-6;
          text-align: center;

          .step-title {
            display: inline-flex;
            align-items: center;
            gap: $spacing-2;
            font-size: $font-size-xl;
            font-weight: $font-weight-semibold;
            color: $text-primary;
            margin-bottom: $spacing-2;

            .el-icon {
              font-size: 24px;
              color: $warning-color;
            }
          }

          .step-description {
            color: $text-secondary;
            font-size: $font-size-md;
          }
        }

        // 步骤1：策略选择
        .strategy-cards {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: $spacing-4;
          margin-bottom: $spacing-6;

          .strategy-card {
            position: relative;
            display: flex;
            align-items: center;
            gap: $spacing-4;
            padding: $spacing-4;
            background: $bg-base;
            border: 2px solid $border-light;
            border-radius: $border-radius-md;
            cursor: pointer;
            transition: all $transition-base $easing-cubic;

            &:hover {
              border-color: $warning-color;
              box-shadow: 0 4px 12px rgba(250, 140, 22, 0.2);
              transform: translateY(-2px);
            }

            &.selected {
              border-color: $warning-color;
              background: $warning-bg;
            }

            .card-icon {
              width: 48px;
              height: 48px;
              @include flex-center;
              background: linear-gradient(135deg, #fa8c16 0%, #ffc53d 100%);
              border-radius: $border-radius-md;
              color: #fff;
              font-size: 24px;
              flex-shrink: 0;
            }

            .card-content {
              flex: 1;

              .card-header {
                .card-title {
                  display: flex;
                  align-items: center;
                  gap: $spacing-2;
                  margin-bottom: $spacing-2;

                  :deep(.el-checkbox__label) {
                    font-weight: $font-weight-semibold;
                    color: $text-primary;
                  }
                }
              }

              .card-body {
                .description {
                  font-size: $font-size-sm;
                  color: $text-secondary;
                  margin-bottom: $spacing-2;
                  line-height: 1.5;
                }

                .meta-info {
                  display: flex;
                  gap: $spacing-2;
                }
              }
            }

            .card-check {
              color: $warning-color;
              font-size: 24px;
            }
          }
        }

        // 步骤2：参数配置
        .params-form {
          .form-section {
            margin-bottom: $spacing-6;
            padding: $spacing-5;
            background: $bg-base;
            border-radius: $border-radius-md;

            .section-title {
              display: flex;
              align-items: center;
              gap: $spacing-2;
              font-size: $font-size-lg;
              font-weight: $font-weight-semibold;
              color: $text-primary;
              margin-bottom: $spacing-4;

              .el-icon {
                font-size: 20px;
                color: $warning-color;
              }
            }

            .form-tip {
              margin-top: $spacing-2;
              font-size: $font-size-xs;
              color: $text-tertiary;
            }

            .strategy-params {
              margin-bottom: $spacing-4;
              padding: $spacing-4;
              background: $card-bg;
              border-radius: $border-radius-sm;

              .strategy-params-header {
                @include flex-between;
                margin-bottom: $spacing-3;

                .strategy-info {
                  display: flex;
                  align-items: center;
                  gap: $spacing-2;

                  .strategy-icon {
                    width: 32px;
                    height: 32px;
                    @include flex-center;
                    background: linear-gradient(135deg, #fa8c16 0%, #ffc53d 100%);
                    border-radius: $border-radius-sm;
                    color: #fff;
                    font-size: 16px;
                  }

                  h5 {
                    margin: 0;
                    font-size: $font-size-md;
                    font-weight: $font-weight-semibold;
                    color: $text-primary;
                  }
                }
              }

              .strategy-params-preview {
                pre {
                  margin: 0;
                  padding: $spacing-3;
                  background: $bg-base;
                  border-radius: $border-radius-sm;
                  font-family: $font-family-code;
                  font-size: $font-size-xs;
                  color: $text-secondary;
                  overflow-x: auto;
                  line-height: 1.6;
                }
              }
            }
          }
        }

        // 步骤3：执行选股
        .execution-summary {
          .summary-card {
            margin-bottom: $spacing-5;

            .summary-title {
              font-size: $font-size-lg;
              font-weight: $font-weight-semibold;
              color: $text-primary;
              margin-bottom: $spacing-4;
            }

            .summary-desc {
              :deep(.el-descriptions__label) {
                font-weight: $font-weight-medium;
              }
            }
          }

          .selected-strategies-list {
            margin-bottom: $spacing-5;
            padding: $spacing-4;
            background: $warning-light;
            border-radius: $border-radius-md;

            h4 {
              margin: 0 0 $spacing-3 0;
              font-size: $font-size-md;
              font-weight: $font-weight-semibold;
              color: $text-primary;
            }

            .strategy-tags {
              display: flex;
              flex-wrap: wrap;
              gap: $spacing-2;

              .strategy-tag {
                :deep(.el-icon) {
                  margin-right: $spacing-1;
                }
              }
            }
          }

          .execution-progress {
            margin-bottom: $spacing-5;
            padding: $spacing-5;
            background: $bg-base;
            border-radius: $border-radius-md;

            h4 {
              margin: 0 0 $spacing-4 0;
              font-size: $font-size-md;
              font-weight: $font-weight-semibold;
              color: $text-primary;
            }

            .progress-text {
              margin-top: $spacing-3;
              text-align: center;
              font-size: $font-size-md;
              color: $text-secondary;
            }
          }

          .execution-results {
            margin-bottom: $spacing-5;

            h4 {
              margin: 0 0 $spacing-4 0;
              font-size: $font-size-md;
              font-weight: $font-weight-semibold;
              color: $text-primary;
            }

            .results-grid {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
              gap: $spacing-4;

              .result-item {
                display: flex;
                align-items: center;
                gap: $spacing-3;
                padding: $spacing-4;
                background: $card-bg;
                border-radius: $border-radius-md;
                border-left: 4px solid;

                &.success {
                  border-left-color: $success-color;
                }

                &.error {
                  border-left-color: $danger-color;
                }

                .result-icon {
                  font-size: 32px;

                  &.success {
                    color: $success-color;
                  }

                  &.error {
                    color: $danger-color;
                  }
                }

                .result-content {
                  flex: 1;

                  .result-name {
                    font-size: $font-size-md;
                    font-weight: $font-weight-semibold;
                    color: $text-primary;
                    margin-bottom: $spacing-1;
                  }

                  .result-stats {
                    display: flex;
                    gap: $spacing-3;
                    font-size: $font-size-sm;
                    color: $text-secondary;

                    strong {
                      color: $text-primary;
                    }
                  }
                }
              }
            }
          }
        }

        // 步骤4：查看结果
        .results-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: $spacing-4;
          margin-bottom: $spacing-5;

          .stat-card {
            display: flex;
            align-items: center;
            gap: $spacing-3;
            padding: $spacing-4;
            background: $card-bg;
            border-radius: $border-radius-md;
            box-shadow: $shadow-1;

            .stat-icon {
              width: 48px;
              height: 48px;
              @include flex-center;
              border-radius: $border-radius-md;
              color: #fff;
              font-size: 20px;
            }

            .stat-content {
              .stat-value {
                font-size: $font-size-xl;
                font-weight: $font-weight-bold;
                color: $text-primary;
                line-height: 1.2;
              }

              .stat-label {
                font-size: $font-size-sm;
                color: $text-secondary;
                margin-top: $spacing-1;
              }
            }
          }
        }

        .results-toolbar {
          display: flex;
          align-items: center;
          gap: $spacing-3;
          margin-bottom: $spacing-5;
          flex-wrap: wrap;

          .search-input {
            flex: 1;
            min-width: 200px;
          }

          .filter-select {
            width: 180px;
          }

          .toolbar-actions {
            margin-left: auto;
            display: flex;
            gap: $spacing-2;
          }
        }

        .results-table {
          margin-bottom: $spacing-5;

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

          .stock-name {
            font-weight: $font-weight-medium;
            color: $text-secondary;
          }

          .strategy-tags-cell {
            display: flex;
            flex-wrap: wrap;
            gap: $spacing-2;
          }

          .date-text {
            font-family: $font-family-code;
            font-size: $font-size-sm;
            color: $text-tertiary;
          }
        }
      }

      .step-actions {
        display: flex;
        justify-content: center;
        gap: $spacing-3;
        margin-top: $spacing-6;
        padding-top: $spacing-5;
        border-top: 1px solid $border-light;
      }
    }
  }
}

// 响应式
@include respond-below('md') {
  .strategy-wizard-page {
    padding: $spacing-3;

    .page-header {
      padding: $spacing-4;

      .header-info {
        .page-title {
          font-size: $font-size-xl;
        }
      }
    }

    .wizard-card {
      .wizard-header {
        padding: $spacing-4;

        :deep(.el-steps) {
          :deep(.el-step__main) {
            :deep(.el-step__title) {
              font-size: $font-size-xs !important;
            }
          }
        }
      }

      .wizard-content {
        padding: $spacing-4;

        .step-content {
          .step-header {
            .step-title {
              font-size: $font-size-lg;
            }
          }

          .strategy-cards {
            grid-template-columns: 1fr;
          }

          .results-stats {
            grid-template-columns: 1fr;
          }

          .results-toolbar {
            flex-direction: column;
            align-items: stretch;

            .search-input,
            .filter-select {
              width: 100%;
            }

            .toolbar-actions {
              margin-left: 0;
              @include flex-center;
              flex-direction: column;
            }
          }
        }

        .step-actions {
          flex-direction: column;

          :deep(.el-button) {
            width: 100%;
          }
        }
      }
    }
  }
}
</style>
