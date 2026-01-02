/**
 * 选股策略 API
 */

import { request } from './client'
import type {
  ApiResponse,
  Strategy,
  SelectionResult,
  StrategyExecuteRequest,
  StrategyExecuteResponse,
  PageResponse,
} from '@/types'

/**
 * 获取策略列表
 */
export function getStrategies(params?: {
  is_active?: boolean
}): Promise<Strategy[]> {
  return request.get('/strategies', { params })
}

/**
 * 获取策略详情
 */
export function getStrategyDetail(strategyId: number): Promise<Strategy> {
  return request.get(`/strategies/${strategyId}`)
}

/**
 * 更新策略配置
 */
export function updateStrategy(
  strategyId: number,
  data: {
    alias?: string
    description?: string
    is_active?: boolean
    config_json?: string
    sort_order?: number
  }
): Promise<Strategy> {
  return request.put(`/strategies/${strategyId}`, data)
}

/**
 * 执行选股策略
 */
export function executeStrategies(data: StrategyExecuteRequest): Promise<StrategyExecuteResponse[]> {
  return request.post('/strategies/run', data)
}

/**
 * 获取选股结果
 */
export function getSelectionResults(params?: {
  strategy_id?: number
  trade_date?: string
  page?: number
  page_size?: number
}): Promise<PageResponse<SelectionResult>> {
  return request.get('/strategies/results', { params })
}

/**
 * 获取选股统计
 */
export function getSelectionStats(params?: {
  trade_date?: string
}): Promise<{
  trade_date: string | null
  strategies: Array<{
    strategy_id: number
    strategy_alias: string
    count: number
  }>
  total: number
}> {
  return request.get('/strategies/results/stats', { params })
}
