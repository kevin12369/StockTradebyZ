<template>
  <div class="stock-kline-container">
    <el-page-header @back="goBack" :title="stockName">
      <template #content>
        <div class="page-header-content">
          <span>{{ tsCode }}</span>
          <el-tag type="info" size="small" style="margin-left: 10px">K线图表</el-tag>
        </div>
      </template>
    </el-page-header>

    <el-card style="margin-top: 20px">
      <!-- 控制面板 -->
      <div class="chart-controls">
        <!-- 周期选择 -->
        <div class="control-group">
          <span class="control-label">K线周期:</span>
          <el-radio-group v-model="period" @change="handlePeriodChange" size="small">
            <el-radio-button value="daily">日K</el-radio-button>
            <el-radio-button value="weekly">周K</el-radio-button>
            <el-radio-button value="monthly">月K</el-radio-button>
            <el-radio-button value="quarterly">季K</el-radio-button>
            <el-radio-button value="yearly">年K</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 时间范围选择 -->
        <div class="control-group">
          <span class="control-label">时间范围:</span>
          <el-radio-group v-model="dateRange" @change="handleDateRangeChange" size="small">
            <el-radio-button value="3M">近3月</el-radio-button>
            <el-radio-button value="6M">近6月</el-radio-button>
            <el-radio-button value="1Y">近1年</el-radio-button>
            <el-radio-button value="3Y">近3年</el-radio-button>
            <el-radio-button value="ALL">全部</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 刷新按钮 -->
        <el-button type="primary" @click="handleRefresh" :loading="loading" size="small">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <!-- K线图表 -->
      <div ref="chartRef" class="kline-chart" v-loading="loading"></div>

      <!-- 数据统计 -->
      <el-descriptions v-if="klineData.length > 0" :column="4" border style="margin-top: 20px">
        <el-descriptions-item label="K线周期">{{ periodName }}</el-descriptions-item>
        <el-descriptions-item label="数据量">{{ klineData.length }} 条</el-descriptions-item>
        <el-descriptions-item label="起始日期">{{ formatDate(klineData[0]?.trade_date) }}</el-descriptions-item>
        <el-descriptions-item label="结束日期">{{ formatDate(klineData[klineData.length - 1]?.trade_date) }}</el-descriptions-item>
        <el-descriptions-item label="最新收盘">
          <span :class="getPriceChangeClass(klineData.length - 1)">
            {{ klineData[klineData.length - 1]?.close.toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="期间最高">
          <span class="text-danger">{{ maxPrice?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="期间最低">
          <span class="text-success">{{ minPrice?.toFixed(2) }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getStockKline } from '@/api/stock'
import type { KlineData } from '@/types'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

const route = useRoute()
const router = useRouter()

// 路由参数
const tsCode = computed(() => route.params.tsCode as string)
const stockName = computed(() => (route.query.name as string) || tsCode.value)

// 图表相关
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 数据状态
const loading = ref(false)
const klineData = ref<KlineData[]>([])
const period = ref<'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'>('daily')
const dateRange = ref('1Y')

// 周期名称映射
const periodNameMap = {
  'daily': '日线',
  'weekly': '周线',
  'monthly': '月线',
  'quarterly': '季线',
  'yearly': '年线',
}

const periodName = computed(() => periodNameMap[period.value])

// 日期范围映射（天数）
const dateRangeMap: Record<string, number> = {
  '3M': 90,
  '6M': 180,
  '1Y': 365,
  '3Y': 1095,
  'ALL': 9999,
}

// 计算统计数据
const maxPrice = computed(() => {
  if (klineData.value.length === 0) return 0
  return Math.max(...klineData.value.map(d => d.high))
})

const minPrice = computed(() => {
  if (klineData.value.length === 0) return 0
  return Math.min(...klineData.value.map(d => d.low))
})

// 返回上一页
const goBack = () => {
  router.back()
}

// 加载K线数据
const loadKlineData = async () => {
  loading.value = true
  try {
    const endDate = new Date().toISOString().split('T')[0]
    const days = dateRangeMap[dateRange.value]
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

    const data = await getStockKline(tsCode.value, {
      period: period.value,
      start_date: startDate,
      end_date: endDate,
      limit: 500,
    })

    // 转换价格字段为数字（后端返回的是字符串）
    klineData.value = data.map((d) => ({
      ...d,
      open: Number(d.open),
      close: Number(d.close),
      high: Number(d.high),
      low: Number(d.low),
      amount: Number(d.amount),
    }))

    if (data.length === 0) {
      ElMessage.warning('该股票暂无K线数据')
    } else {
      renderChart()
    }
  } catch (error) {
    console.error('加载K线数据失败:', error)
    // 检查是否是"股票不存在"错误
    const errorMsg = error instanceof Error ? error.message : String(error)
    if (errorMsg.includes('股票不存在')) {
      ElMessage.error({
        message: '股票数据不存在，请先在"系统设置"中执行"全量数据同步"',
        duration: 5000,
        showClose: true,
      })
    } else {
      ElMessage.error('加载K线数据失败: ' + errorMsg)
    }
  } finally {
    loading.value = false
  }
}

// ============ 技术指标计算函数 ============

/**
 * 计算简单移动平均线 (SMA)
 */
const calculateSMA = (data: number[], period: number): number[] => {
  const result: number[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN)
    } else {
      const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(sum / period)
    }
  }
  return result
}

/**
 * 计算BBI (多空指标)
 */
const calculateBBI = (ma3: number[], ma6: number[], ma12: number[], ma24: number[]): number[] => {
  const result: number[] = []
  for (let i = 0; i < ma3.length; i++) {
    const values = [ma3[i], ma6[i], ma12[i], ma24[i]].filter(v => !isNaN(v))
    if (values.length === 4) {
      result.push(values.reduce((a, b) => a + b, 0) / 4)
    } else {
      result.push(NaN)
    }
  }
  return result
}

/**
 * 计算RSI (相对强弱指标)
 */
const calculateRSI = (data: number[], period: number): number[] => {
  const result: number[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period) {
      result.push(NaN)
      continue
    }
    let gains = 0
    let losses = 0
    for (let j = i - period + 1; j <= i; j++) {
      const change = data[j] - data[j - 1]
      if (change > 0) {
        gains += change
      } else {
        losses -= change
      }
    }
    const avgGain = gains / period
    const avgLoss = losses / period
    if (avgLoss === 0) {
      result.push(100)
    } else {
      const rs = avgGain / avgLoss
      result.push(100 - (100 / (1 + rs)))
    }
  }
  return result
}

/**
 * 计算KDJ指标
 */
const calculateKDJ = (high: number[], low: number[], close: number[], period: number = 9) => {
  const k: number[] = []
  const d: number[] = []
  const j: number[] = []
  for (let i = 0; i < close.length; i++) {
    if (i < period - 1) {
      k.push(NaN); d.push(NaN); j.push(NaN)
      continue
    }
    const highSlice = high.slice(i - period + 1, i + 1)
    const lowSlice = low.slice(i - period + 1, i + 1)
    const highestHigh = Math.max(...highSlice)
    const lowestLow = Math.min(...lowSlice)
    const rsv = ((close[i] - lowestLow) / (highestHigh - lowestLow)) * 100
    if (i === period - 1) {
      k.push(rsv); d.push(rsv)
    } else {
      const newK = (2 * k[i - 1] + rsv) / 3
      const newD = (2 * d[i - 1] + newK) / 3
      k.push(newK); d.push(newD)
    }
    j.push(3 * k[i] - 2 * d[i])
  }
  return { k, d, j }
}

/**
 * 计算EMA (指数移动平均)
 */
const calculateEMA = (data: number[], period: number): number[] => {
  const result: number[] = []
  const multiplier = 2 / (period + 1)
  result[0] = data[0]
  for (let i = 1; i < data.length; i++) {
    result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
  }
  return result
}

/**
 * 计算MACD指标
 */
const calculateMACD = (close: number[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) => {
  const emaFast = calculateEMA(close, fastPeriod)
  const emaSlow = calculateEMA(close, slowPeriod)
  const dif: number[] = []
  for (let i = 0; i < close.length; i++) {
    dif.push(emaFast[i] - emaSlow[i])
  }
  const dea = calculateEMA(dif, signalPeriod)
  const macd: number[] = []
  for (let i = 0; i < close.length; i++) {
    macd.push(2 * (dif[i] - dea[i]))
  }
  return { dif, dea, macd }
}

// 渲染图表
const renderChart = () => {
  if (!chartRef.value || klineData.value.length === 0) return

  // 初始化图表
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  // 准备数据
  const dates = klineData.value.map((d) => d.trade_date)
  const close = klineData.value.map(d => d.close)
  const high = klineData.value.map(d => d.high)
  const low = klineData.value.map(d => d.low)
  const open = klineData.value.map(d => d.open)
  const values = klineData.value.map((d) => [d.open, d.close, d.low, d.high])
  const volume = klineData.value.map((d) => d.volume || 0)

  // 计算所有技术指标
  const ma5 = calculateSMA(close, 5)
  const ma10 = calculateSMA(close, 10)
  const ma20 = calculateSMA(close, 20)
  const ma30 = calculateSMA(close, 30)
  const ma60 = calculateSMA(close, 60)

  const ma3 = calculateSMA(close, 3)
  const ma6 = calculateSMA(close, 6)
  const ma12 = calculateSMA(close, 12)
  const ma24 = calculateSMA(close, 24)
  const bbi = calculateBBI(ma3, ma6, ma12, ma24)

  const kdj = calculateKDJ(high, low, close)
  const rsi6 = calculateRSI(close, 6)
  const rsi12 = calculateRSI(close, 12)

  const option: EChartsOption = {
    animation: false,
    title: {
      text: `${tsCode.value} 技术分析`,
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20', 'MA30', 'MA60', 'BBI', '成交量', 'K', 'D', 'J', 'RSI6', 'RSI12'],
      top: 35,
      textStyle: { fontSize: 11 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: function (params: any) {
        if (!params || params.length === 0) return ''
        let result = `日期: ${params[0].axisValue}<br/>`
        params.forEach((param: any) => {
          if (param.seriesName === 'K线') {
            const data = param.data
            result += `开: ${data[1]} 收: ${data[2]}<br/>低: ${data[3]} 高: ${data[4]}<br/>`
          } else if (param.seriesName && param.value !== undefined && !isNaN(param.value)) {
            result += `${param.seriesName}: ${param.value.toFixed(2)}<br/>`
          }
        })
        return result
      }
    },
    grid: [
      { left: '8%', right: '6%', top: '14%', height: '35%' },     // K线图
      { left: '8%', right: '6%', top: '52%', height: '11%' },     // 成交量
      { left: '8%', right: '6%', top: '66%', height: '11%' },     // KDJ
      { left: '8%', right: '6%', top: '80%', height: '11%' }      // RSI
    ],
    // 每个子图的标题
    graphic: [
      {
        type: 'text',
        left: '8%',
        top: '12.5%',
        style: { text: 'K线图 + MA均线', fontSize: 12, fontWeight: 'bold', fill: '#333' }
      },
      {
        type: 'text',
        left: '8%',
        top: '50%',
        style: { text: '成交量', fontSize: 11, fontWeight: 'bold', fill: '#666' }
      },
      {
        type: 'text',
        left: '8%',
        top: '64%',
        style: { text: 'KDJ (K/D/J)', fontSize: 11, fontWeight: 'bold', fill: '#666' }
      },
      {
        type: 'text',
        left: '8%',
        top: '78%',
        style: { text: 'RSI (RSI6/RSI12)', fontSize: 11, fontWeight: 'bold', fill: '#666' }
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      { gridIndex: 1, type: 'category', data: dates, axisLabel: { show: false } },
      { gridIndex: 2, type: 'category', data: dates, axisLabel: { show: false } },
      { gridIndex: 3, type: 'category', data: dates, axisLabel: { show: true } }
    ],
    yAxis: [
      { scale: true, splitArea: { show: true } },                    // K线Y轴
      { scale: true, gridIndex: 1, axisLabel: { show: false }, splitLine: { show: false } }, // 成交量Y轴
      { scale: true, gridIndex: 2, axisLabel: { show: false }, splitLine: { show: false }, min: -20, max: 120 }, // KDJ Y轴（允许J值超出0-100）
      { scale: true, gridIndex: 3, min: 0, max: 100, splitLine: { show: false } }           // RSI Y轴（固定0-100）
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1, 2, 3],
        start: 0,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1, 2, 3],
        type: 'slider',
        top: '93%',
        start: 0,
        end: 100,
        height: '5%'
      }
    ],
    series: [
      // ========== K线图 ==========
      {
        name: 'K线',
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a'
        }
      },
      { name: 'MA5', type: 'line', data: ma5, smooth: true, lineStyle: { color: '#FF5733', opacity: 0.8, width: 1.5 }, symbol: 'none' },
      { name: 'MA10', type: 'line', data: ma10, smooth: true, lineStyle: { color: '#33C3FF', opacity: 0.8, width: 1.5 }, symbol: 'none' },
      { name: 'MA20', type: 'line', data: ma20, smooth: true, lineStyle: { color: '#FFC300', opacity: 0.8, width: 1.5 }, symbol: 'none' },
      { name: 'MA30', type: 'line', data: ma30, smooth: true, lineStyle: { color: '#4CAF50', opacity: 0.8, width: 1.5 }, symbol: 'none' },
      { name: 'MA60', type: 'line', data: ma60, smooth: true, lineStyle: { color: '#C70039', opacity: 0.8, width: 1.5 }, symbol: 'none' },
      { name: 'BBI', type: 'line', data: bbi, smooth: true, lineStyle: { color: '#9C27B0', opacity: 0.8, width: 1.5, type: 'dashed' }, symbol: 'none' },

      // ========== 成交量 ==========
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volume,
        itemStyle: {
          color: (params: any) => {
            const index = params.dataIndex
            if (index === 0) return '#26a69a'
            return (values[index][1] as number) >= (values[index - 1][1] as number) ? '#ef5350' : '#26a69a'
          }
        }
      },

      // ========== KDJ指标 ==========
      {
        name: 'K',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: kdj.k,
        lineStyle: { color: '#FF6B6B', width: 1 },
        symbol: 'none'
      },
      {
        name: 'D',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: kdj.d,
        lineStyle: { color: '#4ECDC4', width: 1 },
        symbol: 'none'
      },
      {
        name: 'J',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: kdj.j,
        lineStyle: { color: '#FFC300', width: 1 },
        symbol: 'none'
      },

      // ========== KDJ参考线（0和100）==========
      {
        name: 'KDJ-100',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: Array(dates.length).fill(100),
        lineStyle: { color: '#ff0000', width: 1, type: 'dashed', opacity: 0.3 },
        symbol: 'none',
        showInLegend: false
      },
      {
        name: 'KDJ-0',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: Array(dates.length).fill(0),
        lineStyle: { color: '#00ff00', width: 1, type: 'dashed', opacity: 0.3 },
        symbol: 'none',
        showInLegend: false
      },

      // ========== RSI指标 ==========
      {
        name: 'RSI6',
        type: 'line',
        xAxisIndex: 3,
        yAxisIndex: 3,
        data: rsi6,
        lineStyle: { color: '#9C27B0', width: 1.5 },
        symbol: 'none'
      },
      {
        name: 'RSI12',
        type: 'line',
        xAxisIndex: 3,
        yAxisIndex: 3,
        data: rsi12,
        lineStyle: { color: '#FF9800', width: 1.5 },
        symbol: 'none'
      },

      // ========== RSI超买超卖区域参考线 ==========
      {
        name: '超买区',
        type: 'line',
        xAxisIndex: 3,
        yAxisIndex: 3,
        data: Array(dates.length).fill(80),
        lineStyle: { color: '#ff0000', width: 1, type: 'dashed', opacity: 0.5 },
        symbol: 'none',
        showInLegend: false
      },
      {
        name: '超卖区',
        type: 'line',
        xAxisIndex: 3,
        yAxisIndex: 3,
        data: Array(dates.length).fill(20),
        lineStyle: { color: '#00ff00', width: 1, type: 'dashed', opacity: 0.5 },
        symbol: 'none',
        showInLegend: false
      }
    ]
  }

  chartInstance.setOption(option)
}

// 获取价格变化样式类
const getPriceChangeClass = (index: number) => {
  if (index === 0 || klineData.value.length === 0) return ''
  const current = klineData.value[index].close
  const previous = klineData.value[index - 1].close
  if (current > previous) return 'text-danger'    // 红色上涨
  if (current < previous) return 'text-success'   // 绿色下跌
  return ''
}

// 刷新数据
const handleRefresh = () => {
  loadKlineData()
}

// 周期变化
const handlePeriodChange = () => {
  loadKlineData()
}

// 日期范围变化
const handleDateRangeChange = () => {
  loadKlineData()
}

// 格式化日期
const formatDate = (dateStr: string | Date) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toISOString().substring(0, 10)
}

// 窗口大小变化时重新渲染图表
const handleResize = () => {
  chartInstance?.resize()
}

// 初始化
onMounted(() => {
  loadKlineData()
  window.addEventListener('resize', handleResize)
})

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped lang="scss">
.stock-kline-container {
  padding: 20px;

  .page-header-content {
    display: flex;
    align-items: center;
  }

  .chart-controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 20px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;

    .control-group {
      display: flex;
      align-items: center;
      gap: 10px;

      .control-label {
        font-size: 14px;
        color: #606266;
        font-weight: 500;
      }
    }
  }

  .kline-chart {
    width: 100%;
    height: 700px;  // 增加高度以容纳5个子图
  }

  // 价格颜色
  .text-danger {
    color: #ef5350;  // 红色表示上涨（A股习惯）
    font-weight: bold;
  }

  .text-success {
    color: #26a69a;  // 绿色表示下跌（A股习惯）
    font-weight: bold;
  }
}
</style>
