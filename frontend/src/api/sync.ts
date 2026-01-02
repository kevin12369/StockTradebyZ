/**
 * 双模式同步 API
 */

import { request } from './client'

// ========== 类型定义 ==========

/**
 * 同步模式
 */
export type SyncMode = 'daily' | 'init'

/**
 * 快速同步请求
 */
export interface QuickSyncRequest {
  mode: SyncMode
  limit?: number
}

/**
 * 快速同步响应
 */
export interface QuickSyncResponse {
  task_id: string
  mode: SyncMode
  mode_description: string
  status: string
  message: string
}

/**
 * 时间估算响应
 */
export interface TimeEstimateResponse {
  total_seconds: number
  hours: number
  minutes: number
  seconds: number
  formatted: string
  stock_count: number
  mode: SyncMode
}

/**
 * GitHub 备份信息
 */
export interface GitHubBackup {
  tag_name: string
  name: string
  created_at: string
  html_url: string
  assets: Array<{
    name: string
    size: number
    download_url: string
  }>
}

// ========== API 方法 ==========

/**
 * 快速同步（推荐）
 */
export function quickSync(params: QuickSyncRequest) {
  return request.post<QuickSyncResponse>('/sync/quick', null, { params })
}

/**
 * 日常快速同步
 */
export function dailySync(limit?: number) {
  return request.post<{ message: string }>('/sync/daily', null, { params: { limit } })
}

/**
 * 初始化全量同步
 */
export function initSync(limit?: number) {
  return request.post<{ message: string }>('/sync/init', null, { params: { limit } })
}

/**
 * 估算同步时间
 */
export function estimateSyncTime(stockCount: number, mode: SyncMode) {
  return request.get<TimeEstimateResponse>('/sync/estimate', {
    params: { stock_count: stockCount, mode }
  })
}

/**
 * 手动备份到 GitHub
 */
export function manualBackup() {
  return request.post<{ message: string }>('/sync/backup')
}

/**
 * 列出 GitHub 备份
 */
export function listBackups(limit = 10) {
  return request.get<GitHubBackup[]>('/sync/backups', { params: { limit } })
}

// ========== 高性能同步 API ==========

/**
 * ⚡ 高性能日常同步
 *
 * @param concurrent 并发数（默认20，范围1-50）
 * @param limit 限制同步数量
 */
export function fastDailySync(concurrent = 20, limit?: number) {
  return request.post<{ task_id: string; estimated_time: string }>('/sync/fast/daily', null, {
    params: { concurrent, limit }
  })
}

/**
 * ⚡ 高性能初始化同步
 *
 * @param concurrent 并发数（默认5，范围1-20）
 * @param limit 限制同步数量
 */
export function fastInitSync(concurrent = 5, limit?: number) {
  return request.post<{ task_id: string; estimated_time: string }>('/sync/fast/init', null, {
    params: { concurrent, limit }
  })
}

/**
 * ⚡ 估算高性能同步时间
 *
 * @param stockCount 股票数量
 * @param mode 同步模式
 * @param concurrent 并发数
 */
export function estimateFastSync(stockCount: number, mode: SyncMode, concurrent = 20) {
  return request.get<{
    estimated_time_seconds: number
    estimated_time_formatted: string
    throughput_per_hour: number
    concurrent_requests: number
  }>('/sync/fast/estimate', {
    params: { stock_count: stockCount, mode, concurrent }
  })
}

/**
 * ⚡ 性能对比
 */
export function comparePerformance(stockCount = 5000) {
  return request.get<{
    original: {
      concurrent: number
      total_seconds: number
      total_formatted: string
      throughput_per_hour: number
    }
    fast: {
      concurrent: number
      total_seconds: number
      total_formatted: string
      throughput_per_hour: number
    }
    improvement: {
      speedup: string
      throughput_improvement: string
      time_saved: string
    }
  }>('/sync/fast/compare', {
    params: { stock_count: stockCount }
  })
}
