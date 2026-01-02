/**
 * TypeScript 类型定义
 */

// 通用响应格式
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页响应格式
export interface PageResponse<T = any> {
  total: number
  page: number
  page_size: number
  items: T[]
}

// 股票相关类型
export interface Stock {
  id: number
  ts_code: string
  symbol: string
  name: string
  market?: string
  market_name?: string  // 市场中文名称
  board?: string  // 板块（主板/创业板/科创板等）
  industry?: string
  list_date?: string
  is_active: boolean
}

export interface KlineData {
  id: number
  ts_code: string
  trade_date: string
  open?: number
  close?: number
  high?: number
  low?: number
  volume?: number
  amount?: number
}

// 策略相关类型
export interface Strategy {
  id: number
  class_name: string
  alias: string
  description?: string
  is_active: boolean
  config_json: string
  sort_order: number
}

export interface SelectionResult {
  id: number
  strategy_id: number
  ts_code: string
  trade_date: string
  score?: number
  reason: Record<string, any>
}

// 策略执行请求
export interface StrategyExecuteRequest {
  strategy_ids: number[]
  trade_date?: string
}

// 策略执行响应
export interface StrategyExecuteResponse {
  success: boolean
  message: string
  strategy_id?: number
  strategy_alias?: string
  trade_date?: string
  total_stocks?: number
  selected_count?: number
  saved_count?: number
  results: Array<{
    ts_code: string
    symbol: string
    name: string
  }>
}
