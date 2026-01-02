/**
 * 任务管理 API
 *
 * 提供任务提交、状态查询、取消等接口
 */

import { request } from './client'

// ========== 类型定义 ==========

/**
 * 任务状态枚举
 */
export type TaskStatus = 'pending' | 'running' | 'paused' | 'success' | 'failed' | 'cancelled'

/**
 * 任务信息
 */
export interface TaskInfo {
  task_id: string
  task_type: string
  status: TaskStatus
  progress: number
  message: string
  result?: Record<string, any>
  error?: string
  created_at: string
  started_at?: string
  completed_at?: string
  details?: Record<string, any>  // 新增：详细信息
}

/**
 * 任务提交请求
 */
export interface TaskSubmitRequest {
  task_type: 'sync_stock_list' | 'sync_kline' | 'batch_sync_kline'
  params?: Record<string, any>
}

/**
 * 任务提交响应
 */
export interface TaskSubmitResponse {
  task_id: string
  status: string
  message: string
}

/**
 * 任务列表响应
 */
export interface TaskListResponse {
  tasks: TaskInfo[]
  total: number
}

// ========== API 方法 ==========

/**
 * 提交任务
 */
export function submitTask(data: TaskSubmitRequest) {
  return request.post<TaskSubmitResponse>('/tasks/submit', data)
}

/**
 * 获取任务状态
 */
export function getTaskStatus(taskId: string) {
  return request.get<TaskInfo>(`/tasks/${taskId}`)
}

/**
 * 获取任务列表
 */
export function listTasks(params?: {
  status?: TaskStatus
  limit?: number
}) {
  return request.get<TaskListResponse>('/tasks', { params })
}

/**
 * 取消任务
 */
export function cancelTask(taskId: string) {
  return request.post<{ message: string }>(`/tasks/${taskId}/cancel`)
}

/**
 * 暂停任务
 */
export function pauseTask(taskId: string) {
  return request.post<{ message: string }>(`/tasks/${taskId}/pause`)
}

/**
 * 恢复任务
 */
export function resumeTask(taskId: string) {
  return request.post<{ message: string }>(`/tasks/${taskId}/resume`)
}

/**
 * 删除任务记录
 */
export function deleteTask(taskId: string) {
  return request.delete<{ message: string }>(`/tasks/${taskId}`)
}
