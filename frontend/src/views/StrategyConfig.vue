<template>
  <div class="strategy-config-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">
          <el-icon class="title-icon"><Setting /></el-icon>
          策略配置中心
        </h1>
        <p class="page-subtitle">管理选股策略、配置参数、控制启用状态</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="goToWizard">
          新建策略
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);">
          <el-icon><Collection /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ strategies.length }}</div>
          <div class="stat-label">全部策略</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ activeCount }}</div>
          <div class="stat-label">已启用</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ inactiveCount }}</div>
          <div class="stat-label">已禁用</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ strategyTypes }}</div>
          <div class="stat-label">策略类型</div>
        </div>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-section card">
      <div class="filter-toolbar">
        <div class="filter-group">
          <label class="filter-label">
            <el-icon><Filter /></el-icon>
            状态筛选
          </label>
          <el-select v-model="statusFilter" placeholder="全部状态" clearable @change="handleFilterChange">
            <el-option label="全部状态" value="" />
            <el-option label="已启用" :value="true" />
            <el-option label="已禁用" :value="false" />
          </el-select>
        </div>

        <div class="filter-group filter-search">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索策略名称或描述..."
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="filter-actions">
          <el-button :icon="Refresh" @click="loadStrategies">
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 策略列表 -->
    <div class="strategies-section card">
      <el-table
        :data="filteredStrategies"
        v-loading="loading"
        stripe
        class="strategies-table"
        @row-click="handleEdit"
      >
        <el-table-column type="index" label="#" width="60" align="center" />

        <el-table-column label="策略信息" min-width="280" align="left">
          <template #default="{ row }">
            <div class="strategy-info">
              <div class="strategy-icon">
                <el-icon><MagicStick /></el-icon>
              </div>
              <div class="strategy-details">
                <div class="strategy-name">{{ row.alias }}</div>
                <div class="strategy-desc">{{ row.description || '暂无描述' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="策略类" width="220" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info" class="code-tag">
              <el-icon><DocumentCopy /></el-icon>
              {{ row.class_name }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @click.stop
              @change="handleToggleActive(row)"
              active-text="启用"
              inactive-text="禁用"
            />
          </template>
        </el-table-column>

        <el-table-column label="参数配置" min-width="200" align="left">
          <template #default="{ row }">
            <div class="config-preview">
              <el-tooltip :content="formatConfigPreview(row.config_json)" placement="top">
                <span class="config-text">{{ formatConfigPreview(row.config_json) }}</span>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" @click.stop="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-divider direction="vertical" />
            <el-button text type="success" @click.stop="goToWizard(row)">
              <el-icon><Guide /></el-icon>
              向导
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div v-if="!loading && filteredStrategies.length === 0" class="empty-state">
        <el-empty :image-size="140">
          <template #description>
            <p class="empty-description">暂无策略配置</p>
            <p class="empty-hint">开始创建您的第一个选股策略</p>
          </template>
          <el-button type="primary" :icon="Plus" @click="goToWizard">
            创建策略
          </el-button>
        </el-empty>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`编辑策略 - ${currentStrategy?.alias}`"
      width="700px"
      class="edit-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="formData" label-width="100px" label-position="left">
        <el-form-item label="策略名称">
          <el-input
            v-model="formData.alias"
            placeholder="输入策略别名"
            clearable
          >
            <template #prefix>
              <el-icon><Edit /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="策略描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="描述策略的用途和特点"
          />
        </el-form-item>

        <el-form-item label="策略类">
          <el-input :value="currentStrategy?.class_name" disabled>
            <template #prefix>
              <el-icon><DocumentCopy /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="参数配置">
          <div class="config-editor">
            <el-input
              v-model="formData.config_json"
              type="textarea"
              :rows="12"
              placeholder='JSON 格式，例如：{"j_threshold": 15, "k_threshold": 80}'
              class="json-editor"
            />
            <div class="config-hint">
              <el-icon><InfoFilled /></el-icon>
              <span>请输入有效的 JSON 格式配置</span>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="JSON预览">
          <div class="json-preview">
            <pre v-if="jsonPreview" class="json-content">{{ jsonPreview }}</pre>
            <div v-else class="json-error">
              <el-icon><WarningFilled /></el-icon>
              <span>无效的 JSON 格式</span>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" :icon="Close">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="saving" :icon="Check">
            保存配置
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Setting,
  Plus,
  Filter,
  Search,
  Refresh,
  Collection,
  CircleCheck,
  CircleClose,
  DataAnalysis,
  MagicStick,
  DocumentCopy,
  Edit,
  Guide,
  InfoFilled,
  WarningFilled,
  Close,
  Check,
} from '@element-plus/icons-vue'
import { getStrategies, updateStrategy } from '@/api/strategy'
import type { Strategy } from '@/types'

const router = useRouter()

// ========== 状态 ==========
const loading = ref(false)
const saving = ref(false)
const strategies = ref<Strategy[]>([])

// 筛选条件
const statusFilter = ref<boolean | ''>('')
const searchKeyword = ref('')

// 对话框
const dialogVisible = ref(false)
const currentStrategy = ref<Strategy | null>(null)
const formData = ref({
  alias: '',
  description: '',
  config_json: '{}',
})

// ========== 计算属性 ==========
// 过滤后的策略
const filteredStrategies = computed(() => {
  let result = strategies.value

  // 状态筛选
  if (statusFilter.value !== '') {
    result = result.filter(s => s.is_active === statusFilter.value)
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(s =>
      s.alias.toLowerCase().includes(keyword) ||
      (s.description && s.description.toLowerCase().includes(keyword)) ||
      s.class_name.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 统计数据
const activeCount = computed(() => strategies.value.filter(s => s.is_active).length)
const inactiveCount = computed(() => strategies.value.filter(s => !s.is_active).length)
const strategyTypes = computed(() => {
  const types = new Set(strategies.value.map(s => s.class_name))
  return types.size
})

// JSON 预览
const jsonPreview = computed(() => {
  try {
    const parsed = JSON.parse(formData.value.config_json || '{}')
    return JSON.stringify(parsed, null, 2)
  } catch {
    return null
  }
})

// ========== 方法 ==========
const goToWizard = (strategy?: Strategy) => {
  if (strategy) {
    router.push(`/strategies/wizard?strategyId=${strategy.id}`)
  } else {
    router.push('/strategies/wizard')
  }
}

const handleFilterChange = () => {
  // 筛选逻辑由 computed 自动处理
}

const handleSearch = () => {
  // 搜索逻辑由 computed 自动处理
}

const formatConfigPreview = (configJson: string) => {
  try {
    const config = JSON.parse(configJson || '{}')
    const keys = Object.keys(config)
    if (keys.length === 0) return '无参数'
    return keys.slice(0, 3).map(k => `${k}: ${config[k]}`).join(', ') + (keys.length > 3 ? '...' : '')
  } catch {
    return '无效配置'
  }
}

const handleToggleActive = async (strategy: Strategy) => {
  try {
    await updateStrategy(strategy.id, {
      is_active: strategy.is_active,
    })
    ElMessage.success(`${strategy.alias} 已${strategy.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('操作失败')
    strategy.is_active = !strategy.is_active // 恢复状态
  }
}

const handleEdit = (strategy: Strategy) => {
  currentStrategy.value = strategy
  formData.value = {
    alias: strategy.alias,
    description: strategy.description || '',
    config_json: strategy.config_json || '{}',
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!currentStrategy.value) return

  // 验证 JSON 格式
  try {
    JSON.parse(formData.value.config_json || '{}')
  } catch {
    ElMessage.error('参数配置不是有效的 JSON 格式')
    return
  }

  saving.value = true
  try {
    await updateStrategy(currentStrategy.value.id, {
      alias: formData.value.alias,
      description: formData.value.description,
      config_json: formData.value.config_json,
    })
    ElMessage.success('策略配置保存成功')
    dialogVisible.value = false
    loadStrategies()
  } catch (error) {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

const loadStrategies = async () => {
  loading.value = true
  try {
    const data = await getStrategies()
    strategies.value = data
  } catch (error) {
    console.error('加载策略列表失败:', error)
    ElMessage.error('加载策略列表失败')
  } finally {
    loading.value = false
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  loadStrategies()
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.strategy-config-page {
  padding: $spacing-4;

  // 页面标题
  .page-header {
    @include flex-between;
    margin-bottom: $spacing-6;
    padding: $spacing-6;
    background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
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

  // 统计卡片
  .stats-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: $spacing-4;
    margin-bottom: $spacing-5;

    .stat-card {
      display: flex;
      align-items: center;
      gap: $spacing-4;
      padding: $spacing-5;
      background: $card-bg;
      border-radius: $border-radius-md;
      box-shadow: $shadow-2;
      transition: all $transition-base $easing-cubic;

      &:hover {
        transform: translateY(-2px);
        box-shadow: $shadow-3;
      }

      .stat-icon {
        width: 56px;
        height: 56px;
        @include flex-center;
        border-radius: $border-radius-md;
        color: #fff;
        font-size: 24px;
      }

      .stat-content {
        .stat-value {
          font-size: $font-size-xxl;
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

      :deep(.el-select) {
        width: 160px;
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

  // 策略列表
  .strategies-section {
    margin-bottom: $spacing-5;

    .strategies-table {
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

      .strategy-info {
        display: flex;
        align-items: center;
        gap: $spacing-3;

        .strategy-icon {
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
          border-radius: $border-radius-md;
          @include flex-center;
          color: #fff;
          font-size: 20px;
          flex-shrink: 0;
        }

        .strategy-details {
          flex: 1;
          min-width: 0;

          .strategy-name {
            font-size: $font-size-md;
            font-weight: $font-weight-semibold;
            color: $text-primary;
            margin-bottom: $spacing-1;
          }

          .strategy-desc {
            font-size: $font-size-sm;
            color: $text-tertiary;
            @include text-ellipsis;
          }
        }
      }

      .code-tag {
        font-family: $font-family-code;
        font-size: $font-size-xs;

        .el-icon {
          margin-right: $spacing-1;
        }
      }

      .config-preview {
        .config-text {
          font-family: $font-family-code;
          font-size: $font-size-xs;
          color: $text-secondary;
          @include text-ellipsis;
          display: inline-block;
          max-width: 100%;
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
}

// 编辑对话框
.edit-dialog {
  :deep(.el-dialog__body) {
    padding: $spacing-5;
  }

  .config-editor {
    width: 100%;

    .json-editor {
      :deep(.el-textarea__inner) {
        font-family: $font-family-code;
        font-size: $font-size-sm;
        line-height: 1.6;
      }
    }

    .config-hint {
      display: flex;
      align-items: center;
      gap: $spacing-2;
      margin-top: $spacing-2;
      padding: $spacing-2 $spacing-3;
      background: $primary-light;
      border-radius: $border-radius-sm;
      font-size: $font-size-xs;
      color: $primary-color;
    }
  }

  .json-preview {
    padding: $spacing-4;
    background: $bg-base;
    border-radius: $border-radius-md;
    border: 1px solid $border-light;
    max-height: 200px;
    overflow: auto;

    .json-content {
      font-family: $font-family-code;
      font-size: $font-size-xs;
      color: $text-secondary;
      margin: 0;
      white-space: pre-wrap;
      word-break: break-all;
    }

    .json-error {
      display: flex;
      align-items: center;
      gap: $spacing-2;
      color: $danger-color;

      .el-icon {
        font-size: 16px;
      }

      span {
        font-size: $font-size-sm;
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: $spacing-3;
  }
}

// 响应式
@include respond-below('md') {
  .strategy-config-page {
    padding: $spacing-3;

    .page-header {
      flex-direction: column;
      gap: $spacing-4;
      text-align: center;

      .header-actions {
        margin-left: 0;

        :deep(.el-button) {
          width: 100%;
        }
      }
    }

    .stats-section {
      grid-template-columns: 1fr;
    }

    .filter-toolbar {
      flex-direction: column;
      align-items: stretch;

      .filter-group {
        :deep(.el-select) {
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
  }
}
</style>
