/**
 * 定时任务管理 API
 */
import { request } from './client'

// ========== 数据类型 ==========

/** 定时任务配置 */
export interface ScheduledTask {
  id: number
  name: string
  task_type: string
  description?: string
  config?: { strategy_ids?: number[] }  // 任务配置，如选股策略ID列表
  enabled: boolean
  cron_expression?: string
  scheduled_time?: string
  last_run_at?: string
  last_run_status?: 'success' | 'failed' | 'running'
  last_run_message?: string
  total_runs: number
  success_runs: number
  failed_runs: number
  created_at: string
  updated_at: string
}

/** 创建任务请求 */
export interface CreateTaskRequest {
  name: string
  task_type: string
  description?: string
  config?: { strategy_ids?: number[] }  // 任务配置
  enabled?: boolean
  cron_expression?: string
  scheduled_time?: string
}

/** 更新任务请求 */
export interface UpdateTaskRequest {
  name?: string
  task_type?: string
  description?: string
  config?: { strategy_ids?: number[] }  // 任务配置
  enabled?: boolean
  cron_expression?: string
  scheduled_time?: string
}

// ========== API 方法 ==========

/**
 * 获取所有定时任务
 */
export async function getScheduledTasks(): Promise<ScheduledTask[]> {
  return request.get<ScheduledTask[]>('/scheduled-tasks')
}

/**
 * 获取任务详情
 */
export async function getScheduledTask(taskId: number): Promise<ScheduledTask> {
  return request.get<ScheduledTask>(`/scheduled-tasks/${taskId}`)
}

/**
 * 创建定时任务
 */
export async function createScheduledTask(data: CreateTaskRequest): Promise<ScheduledTask> {
  return request.post<ScheduledTask>('/scheduled-tasks', data)
}

/**
 * 更新定时任务
 */
export async function updateScheduledTask(
  taskId: number,
  data: UpdateTaskRequest
): Promise<ScheduledTask> {
  return request.put<ScheduledTask>(`/scheduled-tasks/${taskId}`, data)
}

/**
 * 删除定时任务
 */
export async function deleteScheduledTask(taskId: number): Promise<void> {
  return request.delete<void>(`/scheduled-tasks/${taskId}`)
}

/**
 * 手动执行任务
 */
export async function runScheduledTask(taskId: number): Promise<{ message: string }> {
  return request.post<{ message: string }>(`/scheduled-tasks/${taskId}/run`)
}

/**
 * 初始化默认任务
 */
export async function initDefaultTasks(): Promise<{ count: number; tasks: ScheduledTask[] }> {
  return request.post<{ count: number; tasks: ScheduledTask[] }>('/scheduled-tasks/init')
}
