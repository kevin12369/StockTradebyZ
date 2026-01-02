<template>
  <div class="sync-progress-panel">
    <!-- 当前同步任务 -->
    <div v-if="currentTask" class="current-task-card">
      <div class="task-header">
        <div class="task-title">
          <el-icon class="is-loading" v-if="isRunning"><Loading /></el-icon>
          <el-icon v-else-if="isPaused"><VideoPause /></el-icon>
          <el-icon v-else-if="isSuccess"><CircleCheck /></el-icon>
          <el-icon v-else-if="isFailed"><CircleClose /></el-icon>
          <span class="title-text">{{ getTaskTitle(currentTask) }}</span>
        </div>
        <div class="task-status">
          <el-tag :type="getStatusType(currentTask.status)" size="small">
            {{ getStatusText(currentTask.status) }}
          </el-tag>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <el-progress
          :percentage="Math.round(currentTask.progress)"
          :status="getProgressStatus(currentTask.status)"
          :stroke-width="12"
        >
          <template #default="{ percentage }">
            <span class="progress-text">{{ percentage }}%</span>
          </template>
        </el-progress>
      </div>

      <!-- 进度消息 -->
      <div class="progress-message">
        {{ currentTask.message }}
      </div>

      <!-- 详细信息 -->
      <div v-if="currentTask.details && Object.keys(currentTask.details).length > 0" class="task-details">
        <div v-for="(value, key) in currentTask.details" :key="key" class="detail-item">
          <span class="detail-label">{{ getDetailLabel(key) }}:</span>
          <span class="detail-value">{{ formatDetailValue(key, value) }}</span>
        </div>
      </div>

      <!-- 控制按钮 -->
      <div class="task-actions">
        <template v-if="isRunning">
          <el-button
            type="warning"
            size="small"
            @click="handlePause"
            :icon="VideoPause"
          >
            暂停
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click="handleCancel"
            :icon="Close"
          >
            取消
          </el-button>
        </template>
        <template v-else-if="isPaused">
          <el-button
            type="success"
            size="small"
            @click="handleResume"
            :icon="VideoPlay"
          >
            继续
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click="handleCancel"
            :icon="Close"
          >
            取消
          </el-button>
        </template>
        <template v-else-if="isSuccess || isFailed">
          <el-button
            size="small"
            @click="handleDelete"
            :icon="Delete"
          >
            删除记录
          </el-button>
        </template>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty :image-size="80" description="暂无运行中的任务" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Loading,
  VideoPause,
  VideoPlay,
  CircleCheck,
  CircleClose,
  Close,
  Delete,
} from '@element-plus/icons-vue'
import { getTaskStatus, type TaskInfo } from '@/api/task'
import { cancelTask, pauseTask, resumeTask, deleteTask } from '@/api/task'

// 状态
const currentTask = ref<TaskInfo | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

// 计算属性
const isRunning = computed(() => currentTask.value?.status === 'running')
const isPaused = computed(() => currentTask.value?.status === 'paused')
const isSuccess = computed(() => currentTask.value?.status === 'success')
const isFailed = computed(() => currentTask.value?.status === 'failed')

// 获取任务标题
const getTaskTitle = (task: TaskInfo) => {
  const titles: Record<string, string> = {
    'quick_sync_daily': '日常快速同步',
    'quick_sync_init': '初始化全量同步',
    'daily_sync': '日常数据同步',
    'init_sync': '初始化数据同步',
    'batch_sync_kline': '批量K线同步',
    'fast_daily_sync': '高性能日常同步',
    'fast_init_sync': '高性能初始化同步',
  }
  return titles[task.task_type] || task.task_type
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    'pending': 'info',
    'running': 'primary',
    'paused': 'warning',
    'success': 'success',
    'failed': 'danger',
    'cancelled': 'info',
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'pending': '等待中',
    'running': '执行中',
    'paused': '已暂停',
    'success': '已完成',
    'failed': '失败',
    'cancelled': '已取消',
  }
  return texts[status] || status
}

// 获取进度条状态
const getProgressStatus = (status: string) => {
  const statusMap: Record<string, any> = {
    'success': 'success',
    'failed': 'exception',
  }
  return statusMap[status] || undefined
}

// 获取详情标签
const getDetailLabel = (key: string) => {
  const labels: Record<string, string> = {
    'current_index': '当前进度',
    'total_count': '总数',
    'succeeded_count': '成功',
    'failed_count': '失败',
    'current_stock': '当前股票',
  }
  return labels[key] || key
}

// 格式化详情值
const formatDetailValue = (key: string, value: any) => {
  if (key === 'current_stock' && typeof value === 'object') {
    return `${value.ts_code} - ${value.name}`
  }
  return value
}

// 暂停任务
const handlePause = async () => {
  if (!currentTask.value) return

  try {
    await pauseTask(currentTask.value.task_id)
    ElMessage.success('任务已暂停')
  } catch (error: any) {
    ElMessage.error(error.message || '暂停失败')
  }
}

// 恢复任务
const handleResume = async () => {
  if (!currentTask.value) return

  try {
    await resumeTask(currentTask.value.task_id)
    ElMessage.success('任务已恢复')
  } catch (error: any) {
    ElMessage.error(error.message || '恢复失败')
  }
}

// 取消任务
const handleCancel = async () => {
  if (!currentTask.value) return

  try {
    await ElMessageBox.confirm('确定要取消此任务吗？', '确认取消', {
      type: 'warning',
    })
    await cancelTask(currentTask.value.task_id)
    ElMessage.success('任务已取消')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '取消失败')
    }
  }
}

// 删除记录
const handleDelete = async () => {
  if (!currentTask.value) return

  try {
    await ElMessageBox.confirm('确定要删除此任务记录吗？', '确认删除', {
      type: 'warning',
    })
    await deleteTask(currentTask.value.task_id)
    currentTask.value = null
    ElMessage.success('任务记录已删除')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 轮询任务状态
const pollTaskStatus = async () => {
  // 获取所有正在运行的任务
  try {
    const response = await fetch('/api/v1/tasks?limit=10&status=running')
    const data = await response.json()

    if (data.code === 200 && data.data.tasks.length > 0) {
      const task = data.data.tasks[0]
      if (JSON.stringify(task) !== JSON.stringify(currentTask.value)) {
        currentTask.value = task
      }
    } else {
      // 检查是否有最近完成的任务
      const allResponse = await fetch('/api/v1/tasks?limit=5')
      const allData = await allResponse.json()

      if (allData.code === 200 && allData.data.tasks.length > 0) {
        const latestTask = allData.data.tasks[0]
        if (latestTask.status === 'success' || latestTask.status === 'failed') {
          currentTask.value = latestTask
        } else {
          currentTask.value = null
        }
      } else {
        currentTask.value = null
      }
    }
  } catch (error) {
    console.error('轮询任务状态失败:', error)
  }
}

// 初始化
onMounted(() => {
  // 立即获取一次状态
  pollTaskStatus()

  // 每3秒轮询一次
  pollTimer = setInterval(pollTaskStatus, 3000)
})

// 清理
onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.sync-progress-panel {
  .current-task-card {
    padding: $spacing-4;
    background: $bg-base;
    border-radius: $border-radius-md;
    border: 1px solid $border-light;

    .task-header {
      @include flex-between;
      align-items: center;
      margin-bottom: $spacing-4;

      .task-title {
        display: flex;
        align-items: center;
        gap: $spacing-2;

        .title-text {
          font-size: $font-size-md;
          font-weight: $font-weight-medium;
          color: $text-primary;
        }
      }
    }

    .progress-section {
      margin-bottom: $spacing-4;

      .progress-text {
        font-size: $font-size-sm;
        font-weight: $font-weight-medium;
      }
    }

    .progress-message {
      margin-bottom: $spacing-4;
      padding: $spacing-3;
      background: $primary-light;
      border-radius: $border-radius-sm;
      font-size: $font-size-sm;
      color: $text-secondary;
      line-height: 1.5;
    }

    .task-details {
      margin-bottom: $spacing-4;
      padding: $spacing-3;
      background: $bg-page;
      border-radius: $border-radius-sm;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: $spacing-3;

      .detail-item {
        display: flex;
        justify-content: space-between;
        font-size: $font-size-sm;

        .detail-label {
          color: $text-tertiary;
        }

        .detail-value {
          color: $text-primary;
          font-weight: $font-weight-medium;
        }
      }
    }

    .task-actions {
      display: flex;
      gap: $spacing-3;
      justify-content: flex-end;
    }
  }

  .empty-state {
    padding: $spacing-6 0;
    text-align: center;
  }
}
</style>
