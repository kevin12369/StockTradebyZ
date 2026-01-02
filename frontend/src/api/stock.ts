/**
 * 股票数据 API
 */

import { request } from './client'
import type { ApiResponse, PageResponse, Stock, KlineData } from '@/types'

/**
 * 股票K线状态
 */
export interface StockKlineStatus {
  ts_code: string
  symbol: string
  name: string
  market: string
  kline_count: number
  latest_date: string | null
  has_data: boolean
}

/**
 * 批量同步结果
 */
export interface BatchSyncResult {
  success: boolean
  message: string
  total: number
  skipped?: number  // 跳过的股票数量（数据已经是最新的）
  succeeded_count: number
  failed_count: number
  succeeded: Array<{
    ts_code: string
    name: string
    count: number
    sync_mode: string
  }>
  failed: Array<{
    ts_code: string
    name: string
    error: string
  }>
}

/**
 * 获取股票列表
 * @param params 查询参数，markets为市场筛选数组（支持多选）
 */
export function getStockList(params: {
  page?: number
  page_size?: number
  search?: string
  market?: string  // 保留单选以兼容后端
  markets?: string[]  // 新增多选（前端筛选用）
}): Promise<PageResponse<Stock>> {
  return request.get('/stocks', { params })
}

/**
 * 获取股票详情
 */
export function getStockDetail(tsCode: string): Promise<Stock> {
  return request.get(`/stocks/${tsCode}`)
}

/**
 * 获取K线数据
 * @param tsCode 股票代码
 * @param params 查询参数，period支持 daily(日线)/weekly(周线)/monthly(月线)/quarterly(季线)/yearly(年线)
 */
export function getStockKline(
  tsCode: string,
  params?: {
    period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
    start_date?: string
    end_date?: string
    limit?: number
  }
): Promise<KlineData[]> {
  return request.get(`/stocks/${tsCode}/kline`, { params })
}

/**
 * 同步股票列表
 */
export function syncStockList(): Promise<{
  success: boolean
  message: string
  count: number
  added: number
  updated: number
  deactivated: number
}> {
  return request.post('/stocks/sync')
}

/**
 * 同步单只股票K线数据（增量更新）
 */
export function syncStockKline(
  tsCode: string,
  params?: {
    force_full_sync?: boolean
  }
): Promise<{
  success: boolean
  message: string
  ts_code: string
  count: number
  added: number
  updated: number
  sync_mode: string
}> {
  return request.post(`/stocks/${tsCode}/kline/sync`, null, { params })
}

/**
 * 批量同步K线数据（异步任务版本）
 * 返回任务ID，需要通过轮询任务状态获取进度和结果
 */
export function batchSyncKline(params: {
  limit?: number
  force_full_sync?: boolean
}): Promise<{
  task_id: string
  status: string
  message: string
}> {
  return request.post('/stocks/kline/batch-sync', params)
}

/**
 * 获取K线数据状态
 */
export function getKlineStatus(params?: {
  limit?: number
}): Promise<StockKlineStatus[]> {
  return request.get('/stocks/kline/status', { params })
}

/**
 * 涨幅榜数据
 */
export interface TopPerformer {
  ts_code: string
  symbol: string
  name: string
  market: string
  market_name: string
  board: string
  start_date: string
  end_date: string
  start_price: number
  end_price: number
  change_pct: number
}

/**
 * 获取涨幅榜Top50
 * @param period 时间周期：1day(今日)、1week(近7日)、1month(近1月)
 * @param limit 返回数量
 */
export function getTopPerformers(params: {
  period?: '1day' | '1week' | '1month'
  limit?: number
}): Promise<TopPerformer[]> {
  return request.get('/stocks/top-performers', { params })
}

// ========== 智能分批同步接口 ==========

/**
 * 同步进度统计
 */
export interface BatchSyncProgress {
  total_stocks: number
  need_update: number
  up_to_date: number
  need_update_list: Array<{
    ts_code: string
    name: string
    latest_date: string | null
  }>
  up_to_date_list: Array<{
    ts_code: string
    name: string
    latest_date: string | null
  }>
}

/**
 * 批次信息
 */
export interface BatchInfo {
  batch_id: string
  batch_index: number
  total_batches: number
  stock_count: number
  status: string
  created_at: string
}

/**
 * 创建批次响应
 */
export interface CreateBatchesResponse {
  batch_id_prefix: string
  total_batches: number
  total_stocks: number
  batches: BatchInfo[]
}

/**
 * 批次执行结果
 */
export interface BatchExecutionResult {
  batch_id: string
  batch_index: number
  total_batches: number
  success: boolean
  message: string
  total: number
  skipped: number
  succeeded_count: number
  failed_count: number
  succeeded: Array<{
    ts_code: string
    name: string
    count: number
    sync_mode: string
  }>
  failed: Array<{
    ts_code: string
    name: string
    error: string
  }>
}

/**
 * 批次执行进度
 */
export interface BatchExecutionProgress {
  batch_id: string
  batch_index: number
  total_batches: number
  total_count: number
  current_index: number
  current_stock: {
    ts_code: string
    name: string
  } | null
  progress: number
  status: 'running' | 'completed' | 'completed_with_errors' | 'failed'
  succeeded_count: number
  failed_count: number
  skipped_count: number
  start_time: string
  end_time?: string
  message: string
}

/**
 * 获取智能分批同步进度
 */
export function getBatchSyncProgress(): Promise<BatchSyncProgress> {
  return request.get('/stocks/kline/batch/progress')
}

/**
 * 创建智能分批同步计划
 * @param params 配置参数
 */
export function createSyncBatches(params: {
  force_full_sync?: boolean
  batch_size?: number
}): Promise<CreateBatchesResponse> {
  return request.post('/stocks/kline/batch/create-batches', null, { params })
}

/**
 * 执行单个批次
 * @param params 执行参数
 */
export function executeSingleBatch(params: {
  batch_index: number
  batch_id_prefix: string
  force_full_sync?: boolean
  batch_size?: number
}): Promise<BatchExecutionResult> {
  return request.post('/stocks/kline/batch/execute-single', null, { params })
}

/**
 * 获取批次执行进度
 * @param batch_id 批次ID
 */
export function getBatchExecutionProgress(batch_id: string): Promise<BatchExecutionProgress> {
  return request.get('/stocks/kline/batch/execution-progress', { params: { batch_id } })
}
