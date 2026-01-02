<template>
  <div class="settings-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">
          <el-icon class="title-icon"><Tools /></el-icon>
          系统设置中心
        </h1>
        <p class="page-subtitle">数据同步、定时任务、系统配置管理</p>
      </div>
    </div>

    <!-- 快速操作卡片 -->
    <div class="quick-actions-section">
      <div
        class="action-card"
        :class="{ 'is-loading': syncing, 'is-disabled': syncing }"
        @click="!syncing && handleSyncStocks()"
        v-loading="syncing"
        element-loading-text="同步中..."
        element-loading-background="rgba(255, 255, 255, 0.9)"
      >
        <div class="action-icon" style="background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);">
          <el-icon><Refresh /></el-icon>
        </div>
        <div class="action-content">
          <div class="action-title">同步股票列表</div>
          <div class="action-desc">更新A股市场股票基本信息</div>
        </div>
        <div class="action-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>

      <div class="action-card" @click="handleBatchSync">
        <div class="action-icon" style="background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);">
          <el-icon><Download /></el-icon>
        </div>
        <div class="action-content">
          <div class="action-title">批量同步K线</div>
          <div class="action-desc">一次性同步大量数据</div>
        </div>
        <div class="action-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>

      <div class="action-card" @click="handleSmartBatchSync">
        <div class="action-icon" style="background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);">
          <el-icon><Grid /></el-icon>
        </div>
        <div class="action-content">
          <div class="action-title">智能分批同步</div>
          <div class="action-desc">分批执行，支持断点续传</div>
        </div>
        <div class="action-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>

      <div class="action-card" @click="showAddTaskDialog">
        <div class="action-icon" style="background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="action-content">
          <div class="action-title">添加定时任务</div>
          <div class="action-desc">自动化执行数据同步和选股</div>
        </div>
        <div class="action-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 数据同步状态 -->
    <div class="sync-status-section card">
      <div class="section-header">
        <div class="section-title">
          <el-icon><DataLine /></el-icon>
          数据同步状态
        </div>
        <el-button :icon="Refresh" @click="loadStockCount" :loading="loadingStockCount">
          刷新
        </el-button>
      </div>

      <!-- 数据库警告 -->
      <el-alert
        v-if="stockCount === 0"
        title="数据库为空"
        type="warning"
        :closable="false"
        show-icon
        class="warning-alert"
      >
        <template #default>
          <p class="alert-text">检测到数据库中没有股票数据！请按以下步骤操作：</p>
          <ol class="alert-steps">
            <li>点击<strong>"同步股票列表"</strong>按钮，从网络同步股票基本信息</li>
            <li>同步完成后，点击<strong>"智能分批同步"</strong>按钮，下载K线数据</li>
            <li>同步过程可能需要较长时间，请耐心等待</li>
          </ol>
        </template>
      </el-alert>

      <!-- 统计信息 -->
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stockCount }}</div>
            <div class="stat-label">股票总数</div>
          </div>
        </div>

        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ syncProgress.up_to_date }}</div>
            <div class="stat-label">数据最新</div>
          </div>
        </div>

        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ syncProgress.need_update }}</div>
            <div class="stat-label">需要更新</div>
          </div>
        </div>

        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">5秒/只</div>
            <div class="stat-label">同步速率</div>
          </div>
        </div>
      </div>

      <!-- 同步说明 -->
      <div class="sync-tips">
        <div class="tip-item">
          <el-icon class="tip-icon"><InfoFilled /></el-icon>
          <div class="tip-content">
            <div class="tip-title">同步股票列表</div>
            <div class="tip-desc">更新A股市场股票基本信息（新增/更新/停牌）</div>
          </div>
        </div>
        <div class="tip-item">
          <el-icon class="tip-icon"><InfoFilled /></el-icon>
          <div class="tip-content">
            <div class="tip-title">批量同步K线</div>
            <div class="tip-desc">一次性同步大量数据，适合快速同步（可能在4小时后超时）</div>
          </div>
        </div>
        <div class="tip-item">
          <el-icon class="tip-icon" style="color: #52c41a;"><SuccessFilled /></el-icon>
          <div class="tip-content">
            <div class="tip-title">智能分批同步 ⭐推荐</div>
            <div class="tip-desc">分批执行（每批500只），稳定可靠，支持断点续传，智能跳过最新数据</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 定时任务管理 -->
    <div class="tasks-section card">
      <div class="section-header">
        <div class="section-title">
          <el-icon><Clock /></el-icon>
          定时任务管理
        </div>
        <div class="section-actions">
          <el-button type="primary" :icon="Plus" @click="showAddTaskDialog">
            添加任务
          </el-button>
          <el-button :icon="Refresh" @click="loadScheduledTasks" :loading="loadingTasks">
            刷新
          </el-button>
        </div>
      </div>

      <el-table :data="allScheduledTasks" v-loading="loadingTasks" stripe class="tasks-table">
        <el-table-column label="任务信息" min-width="220" align="left">
          <template #default="{ row }">
            <div class="task-info">
              <div class="task-icon">
                <el-icon><List /></el-icon>
              </div>
              <div class="task-details">
                <div class="task-name">{{ row.name }}</div>
                <div class="task-cron">{{ row.cron_expression }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="任务类型" width="140" align="center">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.task_type)" size="small">
              {{ getTaskTypeName(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="任务配置" width="180" align="left">
          <template #default="{ row }">
            <div v-if="row.task_type === 'strategy_selection' && row.config?.strategy_ids">
              <el-tag
                v-for="strategyId in row.config.strategy_ids"
                :key="strategyId"
                size="small"
                type="success"
                style="margin: 2px"
              >
                {{ getStrategyName(strategyId) }}
              </el-tag>
            </div>
            <span v-else class="text-muted">{{ row.description || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="handleToggleTask(row)"
              :loading="row.updating"
              inline-prompt
              active-text="启"
              inactive-text="禁"
            />
          </template>
        </el-table-column>

        <el-table-column label="执行统计" width="140" align="center">
          <template #default="{ row }">
            <div class="task-stats">
              <el-tag :type="getStatusColor(row.last_run_status)" size="small" v-if="row.last_run_status">
                {{ getStatusText(row.last_run_status) }}
              </el-tag>
              <div class="task-count">{{ row.success_runs }}/{{ row.total_runs }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="最后执行" width="160" align="center">
          <template #default="{ row }">
            <span class="date-text">{{ row.last_run_at ? formatDateTime(row.last_run_at) : '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="success" @click="handleRunTask(row)" :loading="row.running" :disabled="!row.enabled">
              <el-icon><VideoPlay /></el-icon>
              执行
            </el-button>
            <el-divider direction="vertical" />
            <el-button text type="danger" @click="handleDeleteTask(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div v-if="!loadingTasks && allScheduledTasks.length === 0" class="empty-state">
        <el-empty :image-size="120">
          <template #description>
            <p class="empty-description">暂无定时任务</p>
            <p class="empty-hint">添加定时任务自动化数据同步和选股</p>
          </template>
          <el-button type="primary" :icon="Plus" @click="showAddTaskDialog">
            添加第一个任务
          </el-button>
        </el-empty>
      </div>
    </div>

    <!-- 系统信息 -->
    <div class="system-info-section card">
      <div class="section-header">
        <div class="section-title">
          <el-icon><Monitor /></el-icon>
          系统信息
        </div>
      </div>

      <el-descriptions :column="2" border class="system-desc">
        <el-descriptions-item label="系统名称">
          <div class="desc-value">
            <el-icon><TrendCharts /></el-icon>
            股票选股系统
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="系统版本">
          <el-tag type="primary">v1.0.0</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="技术栈">
          Vue 3 + TypeScript + FastAPI + AKShare
        </el-descriptions-item>
        <el-descriptions-item label="开发模式">
          个人投研学习平台
        </el-descriptions-item>
        <el-descriptions-item label="数据源" :span="2">
          使用 AKShare 获取股票数据，无需 API Token
        </el-descriptions-item>
        <el-descriptions-item label="选股策略" :span="2">
          内置 5 种选股策略：少妇战法、SuperB1战法、补票战法、填坑战法、上穿60放量战法
        </el-descriptions-item>
      </el-descriptions>

      <!-- 免责声明 -->
      <div class="disclaimer-alert">
        <el-alert
          title="免责声明"
          type="warning"
          :closable="false"
          show-icon
        >
          <template #default>
            <p class="disclaimer-text">
              本系统仅供学习与技术研究之用，<strong>不构成任何投资建议</strong>。
              股市有风险，入市需谨慎。使用本系统进行投资决策所造成的任何损失，
              本系统及开发者不承担任何责任。
            </p>
          </template>
        </el-alert>
      </div>
    </div>

    <!-- 批量同步配置对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量同步K线数据" width="500px" class="config-dialog">
      <el-form :model="batchForm" label-width="120px">
        <el-form-item label="同步数量">
          <el-input-number
            v-model="batchForm.limit"
            :min="1"
            :max="5000"
            placeholder="留空表示全部同步"
          />
          <div class="form-hint">优先同步数据最旧的股票，建议首次同步时设置较小的数量（如50-100）</div>
        </el-form-item>
        <el-form-item label="同步模式">
          <el-radio-group v-model="batchForm.force_full_sync">
            <el-radio :value="false">增量更新（推荐）</el-radio>
            <el-radio :value="true">全量同步</el-radio>
          </el-radio-group>
          <div class="form-hint">
            增量更新：只获取缺失的数据<br />
            全量同步：获取近3年所有数据
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmBatchSync" :loading="batchSyncing">
          开始同步
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加定时任务对话框 -->
    <el-dialog v-model="addTaskDialogVisible" title="添加定时任务" width="600px" class="config-dialog">
      <el-form :model="newTaskForm" label-width="120px">
        <el-form-item label="任务类型" required>
          <el-radio-group v-model="newTaskForm.task_type">
            <el-radio value="full_sync">全量数据同步</el-radio>
            <el-radio value="calculate_top_performers">涨幅榜计算</el-radio>
            <el-radio value="strategy_selection">选股策略执行</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="任务名称" required>
          <el-input v-model="newTaskForm.name" placeholder="例如: 每日数据同步" />
        </el-form-item>

        <template v-if="newTaskForm.task_type === 'strategy_selection'">
          <el-form-item label="选择策略" required>
            <el-select
              v-model="newTaskForm.strategy_ids"
              multiple
              placeholder="选择要执行的策略"
              style="width: 100%"
            >
              <el-option
                v-for="strategy in strategies"
                :key="strategy.id"
                :label="strategy.alias"
                :value="strategy.id"
              />
            </el-select>
          </el-form-item>
        </template>

        <el-form-item label="执行时间" required>
          <el-time-picker
            v-model="newTaskForm.execute_time"
            placeholder="选择执行时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="Cron表达式">
          <el-input
            v-model="newTaskForm.cron_expression"
            placeholder="留空则根据执行时间自动生成"
            clearable
          />
          <div class="form-hint">格式: 秒 分 时 日 月 周（例如: 0 18 * * MON-FRI 表示工作日18:00执行）</div>
        </el-form-item>

        <el-form-item label="任务说明">
          <el-input
            v-model="newTaskForm.description"
            type="textarea"
            placeholder="可选的任务描述"
            :rows="2"
          />
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="newTaskForm.enabled" />
          <span class="switch-label">
            {{ newTaskForm.enabled ? '创建后立即启用' : '创建后禁用' }}
          </span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addTaskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateTask" :loading="creatingTask">
          创建任务
        </el-button>
      </template>
    </el-dialog>

    <!-- 任务进度对话框 -->
    <el-dialog
      v-model="batchSyncing"
      title="批量同步进度"
      width="700px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="progress-dialog"
    >
      <div class="task-progress-container">
        <!-- 总体进度条 -->
        <div class="progress-section">
          <div class="progress-header">
            <span class="progress-label">总体进度</span>
            <span class="progress-value">{{ completedCount }} / {{ totalCount || '-' }}</span>
          </div>
          <el-progress
            :percentage="taskProgress"
            :status="taskStatus === 'success' ? 'success' : taskStatus === 'failed' ? 'exception' : undefined"
            :stroke-width="24"
            :show-text="true"
          />
        </div>

        <!-- 当前股票信息 -->
        <div v-if="taskStatus === 'running' && currentStockCode" class="current-stock-card">
          <div class="card-title">
            <el-icon><Refresh /></el-icon>
            正在同步
          </div>
          <div class="stock-info-grid">
            <div class="stock-info-item">
              <div class="info-label">股票代码</div>
              <div class="info-value">{{ currentStockCode }}</div>
            </div>
            <div class="stock-info-item">
              <div class="info-label">股票名称</div>
              <div class="info-value">{{ currentStockName }}</div>
            </div>
            <div class="stock-info-item">
              <div class="info-label">最新数据</div>
              <div class="info-value">{{ currentStockDate || '无数据' }}</div>
            </div>
          </div>
        </div>

        <!-- 时间统计 -->
        <div class="time-stats-grid">
          <div class="time-stat-card">
            <div class="stat-label">已用时间</div>
            <div class="stat-value success">{{ formattedElapsed }}</div>
          </div>
          <div class="time-stat-card">
            <div class="stat-label">预计剩余</div>
            <div class="stat-value warning">{{ formattedRemaining }}</div>
          </div>
          <div class="time-stat-card">
            <div class="stat-label">同步速率</div>
            <div class="stat-value primary">5秒/只</div>
          </div>
        </div>

        <!-- 详细状态 -->
        <div class="status-desc">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="任务ID" :span="2">
              <el-tag size="small" type="info">{{ currentTaskId || '-' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag
                :type="taskStatus === 'success' ? 'success' : taskStatus === 'failed' ? 'danger' : taskStatus === 'running' ? 'warning' : 'info'"
                size="small"
              >
                {{ taskStatus === 'pending' ? '等待中' : taskStatus === 'running' ? '执行中' : taskStatus === 'success' ? '已完成' : taskStatus === 'failed' ? '失败' : '已取消' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="完成进度">
              <span class="progress-text">{{ taskProgress.toFixed(1) }}%</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 提示信息 -->
        <el-alert
          v-if="taskStatus === 'running'"
          title="提示"
          type="info"
          :closable="false"
        >
          <template #default>
            <div class="alert-tips">
              <div>• 使用速率限制器，每5秒同步1只股票，避免被AKShare服务器拒绝连接</div>
              <div>• 智能跳过数据已经是最新的股票，减少无效请求</div>
            </div>
          </template>
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="handleRunInBackground" :disabled="taskStatus === 'success' || taskStatus === 'failed'">
          <el-icon><Monitor /></el-icon>
          后台运行
        </el-button>
        <el-button @click="handleStopBatchSync" :disabled="taskStatus === 'success' || taskStatus === 'failed'">
          停止同步
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量同步结果对话框 -->
    <el-dialog v-model="batchResultVisible" title="批量同步结果" width="700px" class="result-dialog">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="总计">{{ batchResult?.total }}</el-descriptions-item>
        <el-descriptions-item label="跳过（数据最新）" v-if="batchResult?.skipped !== undefined">
          <el-tag type="info">{{ batchResult?.skipped }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="成功">
          <el-tag type="success">{{ batchResult?.succeeded_count }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="失败">
          <el-tag type="danger">{{ batchResult?.failed_count }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-alert
        v-if="batchResult?.skipped && batchResult.skipped > 0"
        :title="`智能跳过了 ${batchResult.skipped} 只数据已经是最新的股票，避免对AKShare服务器造成压力`"
        type="success"
        :closable="false"
        style="margin-top: 15px"
      />

      <el-tabs v-if="batchResult" style="margin-top: 20px">
        <el-tab-pane label="成功列表">
          <el-table :data="batchResult.succeeded" max-height="300" stripe>
            <el-table-column prop="ts_code" label="代码" width="120" />
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column prop="count" label="数据量" width="100" />
            <el-table-column prop="sync_mode" label="模式" width="100" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="失败列表">
          <el-table :data="batchResult.failed" max-height="300" stripe>
            <el-table-column prop="ts_code" label="代码" width="120" />
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column prop="error" label="错误" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button type="primary" @click="batchResultVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 智能分批同步配置对话框 -->
    <el-dialog v-model="smartBatchDialogVisible" title="智能分批同步配置" width="600px" class="config-dialog">
      <el-form :model="smartBatchForm" label-width="140px">
        <el-form-item label="批次大小">
          <el-input-number
            v-model="smartBatchForm.batch_size"
            :min="100"
            :max="1000"
            :step="100"
            placeholder="每批股票数量"
          />
          <div class="form-hint">每批处理的股票数量（推荐：500）</div>
        </el-form-item>
        <el-form-item label="同步模式">
          <el-radio-group v-model="smartBatchForm.force_full_sync">
            <el-radio :value="false">增量更新（推荐）</el-radio>
            <el-radio :value="true">全量同步</el-radio>
          </el-radio-group>
          <div class="form-hint">
            增量更新：只获取缺失的数据，智能跳过7天内已更新的股票<br />
            全量同步：获取近3年所有数据
          </div>
        </el-form-item>
      </el-form>

      <el-alert v-if="syncProgressLoaded" title="当前同步状态" type="info" :closable="false" style="margin-top: 15px">
        <el-descriptions :column="2" border size="small" style="margin-top: 10px">
          <el-descriptions-item label="总股票数">{{ syncProgress.total_stocks }}</el-descriptions-item>
          <el-descriptions-item label="需要更新">
            <el-tag type="warning">{{ syncProgress.need_update }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据最新">
            <el-tag type="success">{{ syncProgress.up_to_date }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="预计批次数">
            {{ Math.ceil(syncProgress.need_update / smartBatchForm.batch_size) }} 批
          </el-descriptions-item>
        </el-descriptions>
      </el-alert>

      <template #footer>
        <el-button @click="smartBatchDialogVisible = false">取消</el-button>
        <el-button @click="loadSyncProgress" :loading="loadingProgress">
          刷新进度
        </el-button>
        <el-button type="primary" @click="handleConfirmSmartBatch" :loading="smartBatchSyncing">
          创建批次
        </el-button>
      </template>
    </el-dialog>

    <!-- 智能分批执行对话框 -->
    <el-dialog
      v-model="smartBatchExecutingVisible"
      title="智能分批执行"
      width="800px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="batch-execute-dialog"
    >
      <div v-if="batchesInfo">
        <!-- 批次概览 -->
        <div class="batch-overview">
          <div class="overview-header">
            <span class="overview-title">批次概览</span>
            <el-tag type="info">共 {{ batchesInfo.total_batches }} 批</el-tag>
          </div>
          <div class="overview-stats">
            <div class="overview-stat">
              <div class="stat-value">{{ batchesInfo.total_batches }}</div>
              <div class="stat-label">总批次数</div>
            </div>
            <div class="overview-stat">
              <div class="stat-value">{{ batchesInfo.total_stocks }}</div>
              <div class="stat-label">需同步股票</div>
            </div>
            <div class="overview-stat">
              <div class="stat-value">{{ smartBatchForm.batch_size }}</div>
              <div class="stat-label">每批大小</div>
            </div>
          </div>
        </div>

        <!-- 批次列表 -->
        <div class="batch-list-section">
          <div class="list-header">
            <span class="list-title">批次列表</span>
            <el-button size="small" @click="executeNextBatch" :disabled="executingBatch || currentBatchIndex >= batchesInfo.total_batches" :loading="executingBatch">
              <el-icon><VideoPlay /></el-icon>
              {{ executingBatch ? '执行中...' : currentBatchIndex >= batchesInfo.total_batches ? '全部完成' : `执行第 ${currentBatchIndex + 1} 批` }}
            </el-button>
          </div>

          <el-table :data="batchesInfo.batches" stripe max-height="350" size="small" class="batch-table">
            <el-table-column prop="batch_index" label="批次" width="60" />
            <el-table-column prop="stock_count" label="股票数" width="80" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.batch_index < currentBatchIndex" type="success" size="small">已完成</el-tag>
                <el-tag v-else-if="row.batch_index === currentBatchIndex" type="warning" size="small">
                  {{ executingBatch ? '执行中' : '待执行' }}
                </el-tag>
                <el-tag v-else type="info" size="small">等待中</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="结果" width="200">
              <template #default="{ row }">
                <span v-if="batchResults[row.batch_index]">
                  <el-tag type="success" size="small">成功 {{ batchResults[row.batch_index].succeeded_count }}</el-tag>
                  <el-tag v-if="batchResults[row.batch_index].failed_count > 0" type="danger" size="small" style="margin-left: 5px">失败 {{ batchResults[row.batch_index].failed_count }}</el-tag>
                  <el-tag v-if="batchResults[row.batch_index].skipped > 0" type="info" size="small" style="margin-left: 5px">跳过 {{ batchResults[row.batch_index].skipped }}</el-tag>
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160" />
          </el-table>
        </div>

        <!-- 当前批次结果 -->
        <div v-if="currentBatchResult" class="current-batch-result">
          <el-divider />
          <div class="result-title">第 {{ currentBatchResult.batch_index }} 批执行结果</div>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="总计">{{ currentBatchResult.total }}</el-descriptions-item>
            <el-descriptions-item label="跳过">
              <el-tag type="info">{{ currentBatchResult.skipped }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="成功">
              <el-tag type="success">{{ currentBatchResult.succeeded_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="失败">
              <el-tag type="danger">{{ currentBatchResult.failed_count }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 失败列表 -->
          <div v-if="currentBatchResult.failed_count > 0" style="margin-top: 15px">
            <el-collapse>
              <el-collapse-item title="查看失败详情" name="1">
                <el-table :data="currentBatchResult.failed" max-height="200" size="small" stripe>
                  <el-table-column prop="ts_code" label="代码" width="120" />
                  <el-table-column prop="name" label="名称" width="150" />
                  <el-table-column prop="error" label="错误" show-overflow-tooltip />
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="smartBatchExecutingVisible = false" :disabled="executingBatch">
          {{ currentBatchIndex >= batchesInfo?.total_batches ? '完成' : '关闭' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, onMounted } from 'vue'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'
import {
  Tools,
  Refresh,
  Download,
  Grid,
  Plus,
  Delete,
  VideoPlay,
  Clock,
  ArrowRight,
  DataLine,
  Document,
  CircleCheck,
  Warning,
  Timer,
  InfoFilled,
  SuccessFilled,
  List,
  Monitor,
  TrendCharts,
} from '@element-plus/icons-vue'
import {
  syncStockList,
  batchSyncKline,
  getStockList,
  type BatchSyncResult,
  getBatchSyncProgress,
  createSyncBatches,
  executeSingleBatch,
  getBatchExecutionProgress,
  type BatchSyncProgress,
  type CreateBatchesResponse,
  type BatchExecutionResult,
} from '@/api/stock'
import { getTaskStatus, type TaskInfo } from '@/api/task'
import {
  getScheduledTasks,
  updateScheduledTask,
  runScheduledTask,
  type ScheduledTask,
} from '@/api/scheduledTask'
import { getStrategies } from '@/api/strategy'
import type { Strategy } from '@/types'

// 股票数据统计
const stockCount = ref(0)
const loadingStockCount = ref(false)

// 批量同步
const syncing = ref(false)
const batchSyncing = ref(false)
const batchDialogVisible = ref(false)
const batchResultVisible = ref(false)
const batchForm = ref({
  limit: undefined,
  force_full_sync: false,
})
const batchResult = ref<BatchSyncResult | null>(null)

// 智能分批同步
const smartBatchSyncing = ref(false)
const smartBatchDialogVisible = ref(false)
const smartBatchExecutingVisible = ref(false)
const smartBatchForm = ref({
  batch_size: 500,
  force_full_sync: false,
})
const syncProgress = ref<BatchSyncProgress>({
  total_stocks: 0,
  need_update: 0,
  up_to_date: 0,
  need_update_list: [],
  up_to_date_list: [],
})
const syncProgressLoaded = ref(false)
const loadingProgress = ref(false)
const batchesInfo = ref<CreateBatchesResponse | null>(null)
const batchIdPrefix = ref<string>('')
const currentBatchIndex = ref(0)
const executingBatch = ref(false)
const batchResults = ref<Record<number, BatchExecutionResult>>({})
const currentBatchResult = ref<BatchExecutionResult | null>(null)
let batchPollingTimer: ReturnType<typeof setInterval> | null = null

// 任务相关
const currentTaskId = ref<string | null>(null)
const taskProgress = ref(0)
const taskMessage = ref('')
const taskStatus = ref<'pending' | 'running' | 'success' | 'failed' | 'cancelled'>('pending')
const isInBackground = ref(false)
let taskPollingTimer: ReturnType<typeof setInterval> | null = null
let taskNotification: ReturnType<typeof ElNotification> | null = null

// 进度详细信息
const currentStockCode = ref('')
const currentStockName = ref('')
const currentStockDate = ref('')
const completedCount = ref(0)
const totalCount = ref(0)
const taskStartTime = ref<Date | null>(null)
const elapsedSeconds = ref(0)
const remainingSeconds = ref(0)

// 定时任务
const scheduledTasks = ref<ScheduledTask[]>([])
const loadingTasks = ref(false)
const strategies = ref<Strategy[]>([])
const addTaskDialogVisible = ref(false)
const creatingTask = ref(false)
const newTaskForm = ref({
  task_type: 'full_sync',
  name: '',
  strategy_ids: [] as number[],
  execute_time: '',
  cron_expression: '',
  description: '',
  enabled: true,
})

// 计算属性
const allScheduledTasks = computed(() => {
  return scheduledTasks.value.map(t => ({
    ...t,
    updating: false,
    running: false,
  }))
})

const formattedElapsed = computed(() => formatTime(elapsedSeconds.value))
const formattedRemaining = computed(() => formatTime(remainingSeconds.value))

// 方法
const formatTime = (seconds: number): string => {
  if (seconds <= 0) return '-'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

const parseTaskMessage = (message: string) => {
  const match = message.match(/\[(\d+)\/(\d+)\]\s+同步\s+([A-Z0-9.]+)\s+([^\(（]+)[\(（]最新数据[：:]\s*([^\)）]*)[\)）]/)
  if (match) {
    completedCount.value = parseInt(match[1])
    totalCount.value = parseInt(match[2])
    currentStockCode.value = match[3].trim()
    currentStockName.value = match[4].trim()
    currentStockDate.value = match[5].trim()
    if (completedCount.value > 0) {
      remainingSeconds.value = (totalCount.value - completedCount.value) * 5
    }
  }
}

const getStrategyName = (strategyId: number) => {
  const strategy = strategies.value.find(s => s.id === strategyId)
  return strategy?.alias || `策略${strategyId}`
}

interface ScheduledTaskWithStatus extends ScheduledTask {
  updating?: boolean
  running?: boolean
}

const loadStockCount = async () => {
  loadingStockCount.value = true
  try {
    const stocks = await getStockList({ page: 1, page_size: 1 })
    stockCount.value = stocks.total || 0
  } catch (error) {
    console.error('加载股票数量失败:', error)
    stockCount.value = 0
  } finally {
    loadingStockCount.value = false
  }
}

const loadStrategies = async () => {
  try {
    const data = await getStrategies({ is_active: true })
    strategies.value = data
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

const loadScheduledTasks = async () => {
  loadingTasks.value = true
  try {
    const tasks = await getScheduledTasks()
    scheduledTasks.value = tasks.map(t => ({
      ...t,
      updating: false,
      running: false,
    }))
  } catch (error) {
    console.error('加载定时任务失败:', error)
    ElMessage.error('加载定时任务失败')
  } finally {
    loadingTasks.value = false
  }
}

const showAddTaskDialog = () => {
  newTaskForm.value = {
    task_type: 'full_sync',
    name: '',
    strategy_ids: [],
    execute_time: '',
    cron_expression: '',
    description: '',
    enabled: true,
  }
  addTaskDialogVisible.value = true
}

const handleCreateTask = async () => {
  if (!newTaskForm.value.name) {
    ElMessage.warning('请输入任务名称')
    return
  }
  if (newTaskForm.value.task_type === 'strategy_selection' && newTaskForm.value.strategy_ids.length === 0) {
    ElMessage.warning('请至少选择一个策略')
    return
  }

  let cronExpression = newTaskForm.value.cron_expression
  if (!cronExpression && newTaskForm.value.execute_time) {
    const [hour, minute] = newTaskForm.value.execute_time.split(':')
    cronExpression = `0 ${minute} ${hour} * * MON-FRI`
  }

  if (!cronExpression) {
    ElMessage.warning('请选择执行时间或填写Cron表达式')
    return
  }

  creatingTask.value = true
  try {
    ElMessage.success('定时任务创建成功！')
    addTaskDialogVisible.value = false
    await loadScheduledTasks()
  } catch (error) {
    console.error('创建定时任务失败:', error)
    ElMessage.error('创建定时任务失败')
  } finally {
    creatingTask.value = false
  }
}

const handleDeleteTask = async (task: ScheduledTaskWithStatus) => {
  await ElMessageBox.confirm(
    `确定要删除任务"${task.name}"吗？此操作不可恢复！`,
    '删除定时任务',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
  try {
    ElMessage.success('任务已删除')
    await loadScheduledTasks()
  } catch (error) {
    console.error('删除任务失败:', error)
    ElMessage.error('删除任务失败')
  }
}

const handleToggleTask = async (task: ScheduledTaskWithStatus) => {
  task.updating = true
  try {
    await updateScheduledTask(task.id, { enabled: task.enabled })
    ElMessage.success(task.enabled ? '任务已启用' : '任务已禁用')
  } catch (error) {
    console.error('更新任务状态失败:', error)
    ElMessage.error('更新任务状态失败')
    task.enabled = !task.enabled
  } finally {
    task.updating = false
  }
}

const handleRunTask = async (task: ScheduledTaskWithStatus) => {
  await ElMessageBox.confirm(
    `确定要立即执行任务"${task.name}"吗？`,
    '手动执行任务',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )

  task.running = true
  try {
    const result = await runScheduledTask(task.id)
    ElMessage.success(result.message || '任务已触发执行')
    setTimeout(() => {
      loadScheduledTasks()
    }, 3000)
  } catch (error) {
    console.error('执行任务失败:', error)
    ElMessage.error('执行任务失败')
  } finally {
    task.running = false
  }
}

const getTaskTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    'full_sync': '全量同步',
    'calculate_top_performers': '涨幅榜计算',
    'strategy_selection': '选股策略',
  }
  return typeMap[type] || type
}

const getTaskTypeColor = (type: string) => {
  const colorMap: Record<string, any> = {
    'full_sync': 'success',
    'calculate_top_performers': 'warning',
    'strategy_selection': 'primary',
  }
  return colorMap[type] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'success': '成功',
    'failed': '失败',
    'running': '运行中',
  }
  return statusMap[status] || status
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, any> = {
    'success': 'success',
    'failed': 'danger',
    'running': 'warning',
  }
  return colorMap[status] || 'info'
}

const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const playNotificationSound = (type: 'success' | 'error' | 'info') => {
  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    if (type === 'success') {
      oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime)
      oscillator.frequency.exponentialRampToValueAtTime(783.99, audioContext.currentTime + 0.1)
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)
      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.3)
    } else if (type === 'error') {
      oscillator.frequency.setValueAtTime(200, audioContext.currentTime)
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2)
      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.2)
    } else {
      oscillator.frequency.setValueAtTime(440, audioContext.currentTime)
      gainNode.gain.setValueAtTime(0.2, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1)
      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.1)
    }
  } catch (error) {
    console.warn('播放提示音失败:', error)
  }
}

const handleSyncStocks = async () => {
  syncing.value = true
  try {
    const result = await syncStockList()
    if (result.success) {
      ElMessage.success(
        `同步成功！新增 ${result.added} 只，更新 ${result.updated} 只，停用 ${result.deactivated} 只`
      )
      await loadStockCount()
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('同步失败')
  } finally {
    syncing.value = false
  }
}

const handleBatchSync = () => {
  batchDialogVisible.value = true
}

const handleSmartBatchSync = async () => {
  smartBatchDialogVisible.value = true
  await loadSyncProgress()
}

const loadSyncProgress = async () => {
  loadingProgress.value = true
  try {
    const progress = await getBatchSyncProgress()
    syncProgress.value = progress
    syncProgressLoaded.value = true
    ElMessage.success('进度加载成功')
  } catch (error: any) {
    ElMessage.error(`加载进度失败: ${error.message || '未知错误'}`)
  } finally {
    loadingProgress.value = false
  }
}

const handleConfirmSmartBatch = async () => {
  smartBatchSyncing.value = true
  try {
    const result = await createSyncBatches({
      force_full_sync: smartBatchForm.value.force_full_sync,
      batch_size: smartBatchForm.value.batch_size,
    })

    batchesInfo.value = result
    batchIdPrefix.value = result.batch_id_prefix
    currentBatchIndex.value = 0
    batchResults.value = {}
    currentBatchResult.value = null

    smartBatchDialogVisible.value = false
    smartBatchExecutingVisible.value = true

    ElMessage.success(`成功创建 ${result.total_batches} 个批次，共 ${result.total_stocks} 只股票`)
  } catch (error: any) {
    ElMessage.error(`创建批次失败: ${error.message || '未知错误'}`)
  } finally {
    smartBatchSyncing.value = false
  }
}

const executeNextBatch = async () => {
  if (!batchesInfo.value || currentBatchIndex.value >= batchesInfo.value.total_batches) {
    return
  }

  executingBatch.value = true
  const batchIndex = currentBatchIndex.value + 1
  const currentBatch = batchesInfo.value.batches[batchIndex - 1]

  try {
    const result = await executeSingleBatch({
      batch_index: batchIndex,
      batch_id_prefix: batchIdPrefix.value,
      force_full_sync: smartBatchForm.value.force_full_sync,
      batch_size: smartBatchForm.value.batch_size,
    })

    batchResults.value[batchIndex] = result
    currentBatchResult.value = result
    currentBatchIndex.value = batchIndex

    if (result.success) {
      ElMessage.success(`第 ${batchIndex} 批完成：成功 ${result.succeeded_count}，失败 ${result.failed_count}，跳过 ${result.skipped}`)
    } else {
      ElMessage.warning(`第 ${batchIndex} 批完成但有失败：成功 ${result.succeeded_count}，失败 ${result.failed_count}`)
    }
  } catch (error: any) {
    ElMessage.error(`执行批次 ${batchIndex} 失败: ${error.message || '未知错误'}`)
  } finally {
    executingBatch.value = false
  }
}

const startTaskPolling = (taskId: string) => {
  currentTaskId.value = taskId
  taskStatus.value = 'pending'
  taskProgress.value = 0
  taskMessage.value = '任务已提交，等待执行...'
  isInBackground.value = false

  completedCount.value = 0
  totalCount.value = 0
  currentStockCode.value = ''
  currentStockName.value = ''
  currentStockDate.value = ''
  taskStartTime.value = new Date()
  elapsedSeconds.value = 0

  createOrUpdateNotification('info', '批量同步进行中', taskId, 0, '任务已提交，等待执行...')

  taskPollingTimer = setInterval(async () => {
    try {
      const taskInfo: TaskInfo = await getTaskStatus(taskId)

      taskStatus.value = taskInfo.status
      taskProgress.value = taskInfo.progress
      taskMessage.value = taskInfo.message

      if (taskStartTime.value) {
        elapsedSeconds.value = Math.floor((Date.now() - taskStartTime.value.getTime()) / 1000)
      }

      if (taskInfo.message && taskInfo.status === 'running') {
        parseTaskMessage(taskInfo.message)
      }

      const statusText = {
        'pending': '等待中',
        'running': '执行中',
        'success': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      }[taskInfo.status]

      const typeMap = {
        'pending': 'info',
        'running': 'warning',
        'success': 'success',
        'failed': 'error',
        'cancelled': 'info'
      } as const

      createOrUpdateNotification(
        typeMap[taskInfo.status] || 'info',
        `批量同步${statusText}`,
        taskId,
        taskInfo.progress,
        taskInfo.message
      )

      if (taskInfo.status === 'success' || taskInfo.status === 'failed' || taskInfo.status === 'cancelled') {
        stopTaskPolling()
        batchSyncing.value = false
        currentTaskId.value = null
        isInBackground.value = false

        if (taskInfo.status === 'success') {
          playNotificationSound('success')
        } else if (taskInfo.status === 'failed') {
          playNotificationSound('error')
        }

        if (taskInfo.result && !isInBackground.value) {
          batchResult.value = taskInfo.result as BatchSyncResult
          batchResultVisible.value = true
        } else if (taskInfo.result && isInBackground.value) {
          batchResult.value = taskInfo.result as BatchSyncResult
          const skippedMsg = batchResult.value.skipped ? `，跳过 ${batchResult.value.skipped}` : ''
          ElMessage.success(`批量同步完成！成功 ${batchResult.value.succeeded_count}，失败 ${batchResult.value.failed_count}${skippedMsg}`)
        }

        setTimeout(() => {
          closeNotification()
        }, 3000)
      }
    } catch (error) {
      console.error('查询任务状态失败:', error)
    }
  }, 2000)
}

const createOrUpdateNotification = (
  type: 'success' | 'warning' | 'info' | 'error',
  title: string,
  taskId: string,
  progress: number,
  message: string
) => {
  if (taskNotification) {
    taskNotification.close()
  }

  taskNotification = ElNotification({
    title,
    message: `任务ID: ${taskId}\n进度: ${progress.toFixed(1)}% - ${message}`,
    type,
    duration: 0,
    position: 'top-right',
    showClose: false,
  })
}

const closeNotification = () => {
  if (taskNotification) {
    taskNotification.close()
    taskNotification = null
  }
}

const stopTaskPolling = () => {
  if (taskPollingTimer) {
    clearInterval(taskPollingTimer)
    taskPollingTimer = null
  }
  closeNotification()
}

const handleConfirmBatchSync = async () => {
  batchSyncing.value = true
  try {
    const response = await batchSyncKline({
      limit: batchForm.value.limit || undefined,
      force_full_sync: batchForm.value.force_full_sync,
    })

    startTaskPolling(response.task_id)
    batchDialogVisible.value = false

    ElMessage.success(`批量同步任务已提交！任务ID: ${response.task_id}`)
  } catch (error) {
    ElMessage.error('提交批量同步任务失败')
    batchSyncing.value = false
  }
}

const handleStopBatchSync = () => {
  stopTaskPolling()
  batchSyncing.value = false
  currentTaskId.value = null
  playNotificationSound('info')
  ElMessage.info('已停止批量同步')
}

const handleRunInBackground = () => {
  isInBackground.value = true
  batchSyncing.value = false
  ElMessage.success('批量同步已在后台运行，可通过右上角通知查看进度')
}

onMounted(() => {
  loadStockCount()
  loadScheduledTasks()
  loadStrategies()
})

onUnmounted(() => {
  stopTaskPolling()
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.settings-page {
  padding: $spacing-4;

  // 页面标题
  .page-header {
    margin-bottom: $spacing-6;
    padding: $spacing-6;
    background: linear-gradient(135deg, #13c2c2 0%, #36cfc9 100%);
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

  // 快速操作卡片
  .quick-actions-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: $spacing-4;
    margin-bottom: $spacing-6;

    .action-card {
      position: relative;
      display: flex;
      align-items: center;
      gap: $spacing-4;
      padding: $spacing-5;
      background: $card-bg;
      border-radius: $border-radius-lg;
      box-shadow: $shadow-2;
      cursor: pointer;
      transition: all $transition-base $easing-cubic;

      &:hover {
        transform: translateY(-4px);
        box-shadow: $shadow-4;
      }

      // 禁用状态
      &.is-disabled {
        cursor: not-allowed;
        opacity: 0.6;
        pointer-events: none;

        &:hover {
          transform: none;
          box-shadow: $shadow-2;
        }
      }

      // 加载状态
      &.is-loading {
        cursor: wait;
        pointer-events: none;

        &:hover {
          transform: none;
          box-shadow: $shadow-2;
        }
      }

      .action-icon {
        width: 56px;
        height: 56px;
        @include flex-center;
        border-radius: $border-radius-md;
        color: #fff;
        font-size: 24px;
        flex-shrink: 0;
      }

      .action-content {
        flex: 1;

        .action-title {
          font-size: $font-size-lg;
          font-weight: $font-weight-semibold;
          color: $text-primary;
          margin-bottom: $spacing-1;
        }

        .action-desc {
          font-size: $font-size-sm;
          color: $text-tertiary;
        }
      }

      .action-arrow {
        color: $text-quaternary;
        font-size: 18px;
        transition: all $transition-base $easing-cubic;
      }

      &:hover .action-arrow {
        color: $primary-color;
        transform: translateX(4px);
      }
    }
  }

  // 通用section样式
  .card {
    background: $card-bg;
    border-radius: $border-radius-lg;
    box-shadow: $shadow-2;
    padding: $spacing-5;
    margin-bottom: $spacing-5;
  }

  .section-header {
    @include flex-between;
    margin-bottom: $spacing-5;
    padding-bottom: $spacing-4;
    border-bottom: 1px solid $border-light;

    .section-title {
      display: flex;
      align-items: center;
      gap: $spacing-2;
      font-size: $font-size-lg;
      font-weight: $font-weight-semibold;
      color: $text-primary;

      .el-icon {
        font-size: 20px;
        color: $primary-color;
      }
    }

    .section-actions {
      display: flex;
      gap: $spacing-3;
    }
  }

  // 数据同步状态
  .sync-status-section {
    .warning-alert {
      margin-bottom: $spacing-5;

      .alert-text {
        margin-bottom: $spacing-3;
        font-size: $font-size-md;
      }

      .alert-steps {
        margin: 0;
        padding-left: $spacing-5;

        li {
          margin-bottom: $spacing-2;
          line-height: 1.6;

          strong {
            color: $warning-color;
          }
        }
      }
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: $spacing-4;
      margin-bottom: $spacing-5;

      .stat-item {
        display: flex;
        align-items: center;
        gap: $spacing-3;
        padding: $spacing-4;
        background: $bg-base;
        border-radius: $border-radius-md;

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

    .sync-tips {
      display: grid;
      gap: $spacing-3;

      .tip-item {
        display: flex;
        align-items: flex-start;
        gap: $spacing-3;
        padding: $spacing-3;
        background: $bg-base;
        border-radius: $border-radius-md;

        .tip-icon {
          font-size: 18px;
          margin-top: 2px;
        }

        .tip-content {
          flex: 1;

          .tip-title {
            font-size: $font-size-md;
            font-weight: $font-weight-medium;
            color: $text-primary;
            margin-bottom: $spacing-1;
          }

          .tip-desc {
            font-size: $font-size-sm;
            color: $text-secondary;
            line-height: 1.5;
          }
        }
      }
    }
  }

  // 定时任务管理
  .tasks-section {
    .tasks-table {
      :deep(.el-table__body-wrapper) {
        .el-table__row {
          cursor: default;
        }
      }

      .task-info {
        display: flex;
        align-items: center;
        gap: $spacing-3;

        .task-icon {
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
          border-radius: $border-radius-sm;
          @include flex-center;
          color: #fff;
          font-size: 18px;
        }

        .task-details {
          .task-name {
            font-size: $font-size-md;
            font-weight: $font-weight-medium;
            color: $text-primary;
            margin-bottom: $spacing-1;
          }

          .task-cron {
            font-family: $font-family-code;
            font-size: $font-size-xs;
            color: $text-tertiary;
          }
        }
      }

      .task-stats {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: $spacing-1;

        .task-count {
          font-size: $font-size-xs;
          color: $text-tertiary;
        }
      }

      .date-text {
        font-family: $font-family-code;
        font-size: $font-size-xs;
        color: $text-secondary;
      }

      .text-muted {
        color: $text-quaternary;
        font-size: $font-size-sm;
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

  // 系统信息
  .system-info-section {
    .system-desc {
      .desc-value {
        display: flex;
        align-items: center;
        gap: $spacing-2;
        font-weight: $font-weight-medium;
      }
    }

    .disclaimer-alert {
      margin-top: $spacing-5;

      .disclaimer-text {
        margin-top: $spacing-2;
        line-height: 1.8;

        strong {
          color: $danger-color;
        }
      }
    }
  }
}

// 对话框样式
.config-dialog {
  :deep(.el-dialog__body) {
    padding: $spacing-5;
  }

  .form-hint {
    margin-top: $spacing-2;
    font-size: $font-size-xs;
    color: $text-tertiary;
    line-height: 1.5;
  }

  .switch-label {
    margin-left: $spacing-3;
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}

.progress-dialog {
  .task-progress-container {
    .progress-section {
      margin-bottom: $spacing-5;

      .progress-header {
        @include flex-between;
        margin-bottom: $spacing-3;

        .progress-label {
          font-size: $font-size-md;
          font-weight: $font-weight-medium;
          color: $text-primary;
        }

        .progress-value {
          font-size: $font-size-md;
          font-weight: $font-weight-semibold;
          color: $primary-color;
        }
      }
    }

    .current-stock-card {
      padding: $spacing-4;
      background: $bg-base;
      border-radius: $border-radius-md;
      margin-bottom: $spacing-5;

      .card-title {
        display: flex;
        align-items: center;
        gap: $spacing-2;
        font-weight: $font-weight-medium;
        color: $text-primary;
        margin-bottom: $spacing-4;

        .el-icon {
          color: $primary-color;
        }
      }

      .stock-info-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: $spacing-4;

        .stock-info-item {
          .info-label {
            font-size: $font-size-xs;
            color: $text-tertiary;
            margin-bottom: $spacing-1;
          }

          .info-value {
            font-size: $font-size-md;
            font-weight: $font-weight-medium;
            color: $text-primary;
          }
        }
      }
    }

    .time-stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: $spacing-4;
      margin-bottom: $spacing-5;

      .time-stat-card {
        padding: $spacing-4;
        background: $bg-base;
        border-radius: $border-radius-md;
        text-align: center;

        .stat-label {
          font-size: $font-size-xs;
          color: $text-tertiary;
          margin-bottom: $spacing-2;
        }

        .stat-value {
          font-size: $font-size-lg;
          font-weight: $font-weight-bold;

          &.success {
            color: $success-color;
          }

          &.warning {
            color: $warning-color;
          }

          &.primary {
            color: $primary-color;
          }
        }
      }
    }

    .status-desc {
      margin-bottom: $spacing-4;

      .progress-text {
        font-weight: $font-weight-semibold;
        color: $primary-color;
      }
    }

    .alert-tips {
      div {
        margin-bottom: $spacing-1;
        line-height: 1.6;
      }
    }
  }
}

.batch-execute-dialog {
  .batch-overview {
    padding: $spacing-4;
    background: $bg-base;
    border-radius: $border-radius-md;
    margin-bottom: $spacing-5;

    .overview-header {
      @include flex-between;
      margin-bottom: $spacing-4;

      .overview-title {
        font-weight: $font-weight-medium;
        color: $text-primary;
      }
    }

    .overview-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: $spacing-4;

      .overview-stat {
        text-align: center;

        .stat-value {
          font-size: $font-size-xxl;
          font-weight: $font-weight-bold;
          color: $text-primary;
          line-height: 1.2;
        }

        .stat-label {
          font-size: $font-size-sm;
          color: $text-secondary;
          margin-top: $spacing-2;
        }
      }
    }
  }

  .batch-list-section {
    .list-header {
      @include flex-between;
      margin-bottom: $spacing-3;
      align-items: center;

      .list-title {
        font-weight: $font-weight-medium;
        color: $text-primary;
      }
    }

    .batch-table {
      .text-muted {
        color: $text-quaternary;
      }
    }
  }

  .current-batch-result {
    .result-title {
      font-weight: $font-weight-medium;
      color: $text-primary;
      margin-bottom: $spacing-3;
    }
  }
}

// 响应式
@include respond-below('md') {
  .settings-page {
    padding: $spacing-3;

    .page-header {
      padding: $spacing-4;
    }

    .quick-actions-section {
      grid-template-columns: 1fr;
    }

    .section-header {
      flex-direction: column;
      gap: $spacing-3;
      align-items: stretch;

      .section-actions {
        @include flex-center;
        flex-direction: column;

        :deep(.el-button) {
          width: 100%;
        }
      }
    }

    .sync-status-section {
      .stats-grid {
        grid-template-columns: 1fr;
      }
    }
  }
}
</style>
