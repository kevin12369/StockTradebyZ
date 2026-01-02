/**
 * 格式化工具函数
 */

import dayjs from 'dayjs'

/**
 * 格式化日期
 */
export function formatDate(date: string | Date, format = 'YYYY-MM-DD'): string {
  return dayjs(date).format(format)
}

/**
 * 格式化数字（千分位）
 */
export function formatNumber(num: number, decimals = 2): string {
  return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * 格式化金额
 */
export function formatAmount(amount: number): string {
  if (amount >= 100000000) {
    return `${(amount / 100000000).toFixed(2)}亿`
  } else if (amount >= 10000) {
    return `${(amount / 10000).toFixed(2)}万`
  }
  return amount.toFixed(2)
}

/**
 * 格式化百分比
 */
export function formatPercent(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 格式化股票代码
 */
export function formatStockCode(tsCode: string): string {
  return tsCode.replace('.', '')
}
