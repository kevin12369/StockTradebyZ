<template>
  <el-dialog
    :model-value="modelValue"
    :title="`股票详情 - ${stockInfo?.name || tsCode} (${tsCode})`"
    width="1200px"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div v-loading="loading" class="stock-detail-content">
      <!-- 基本信息 -->
      <el-descriptions v-if="stockInfo" title="基本信息" :column="3" border class="info-section">
        <el-descriptions-item label="股票代码">{{ stockInfo.ts_code }}</el-descriptions-item>
        <el-descriptions-item label="股票名称">{{ stockInfo.name }}</el-descriptions-item>
        <el-descriptions-item label="市场">{{ stockInfo.market_name || stockInfo.market }}</el-descriptions-item>
        <el-descriptions-item label="板块">{{ stockInfo.board }}</el-descriptions-item>
        <el-descriptions-item label="行业">{{ stockInfo.industry || '-' }}</el-descriptions-item>
        <el-descriptions-item label="上市日期">{{ stockInfo.list_date || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 选股理由 -->
      <div v-if="selectionReasons.length > 0" class="reasons-section">
        <h3 class="section-title">选股理由</h3>
        <el-timeline>
          <el-timeline-item
            v-for="(reason, index) in selectionReasons"
            :key="index"
            :timestamp="reason.strategy_alias"
            placement="top"
          >
            <div class="reason-content">
              <el-tag type="success" size="small">{{ reason.strategy_alias }}</el-tag>
              <div class="reason-details">
                <p v-for="(value, key) in reason.details" :key="key">
                  <strong>{{ formatKey(key) }}:</strong> {{ formatValue(value) }}
                </p>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>

      <!-- K线图 -->
      <div class="kline-section">
        <h3 class="section-title">K线图表（含均线）</h3>
        <div ref="klineChartRef" class="kline-chart"></div>
      </div>

      <!-- 技术指标 -->
      <div v-if="technicalIndicators" class="indicators-section">
        <h3 class="section-title">基础数据</h3>
        <el-row :gutter="16" class="indicator-row">
          <el-col :span="6">
            <el-statistic title="最新价" :value="technicalIndicators.close" :precision="2" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="涨跌幅" :value="technicalIndicators.change_pct" :precision="2" suffix="%" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="成交量" :value="technicalIndicators.volume" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="成交额" :value="technicalIndicators.amount" />
          </el-col>
        </el-row>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
      <el-button type="primary" @click="handleViewKline">查看完整K线图</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getStockList, getStockKline } from '@/api/stock'

interface Props {
  modelValue: boolean
  tsCode: string
  tradeDate?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const router = useRouter()

// 状态
const loading = ref(false)
const stockInfo = ref<any>(null)
const selectionReasons = ref<any[]>([])
const technicalIndicators = ref<any>(null)
const klineChartRef = ref<HTMLElement>()
let klineChart: echarts.ECharts | null = null

// 格式化键名
const formatKey = (key: string) => {
  const keyMap: Record<string, string> = {
    score: '匹配度',
    change_pct: '涨跌幅',
    amount: '成交额',
    close: '收盘价',
    reason: '理由',
    volume: '成交量'
  }
  return keyMap[key] || key
}

// 格式化值
const formatValue = (value: any) => {
  if (typeof value === 'number') {
    if (value > 10000) {
      return (value / 10000).toFixed(2) + '万'
    }
    return value.toFixed(2)
  }
  return value
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
      k.push(NaN)
      d.push(NaN)
      j.push(NaN)
      continue
    }

    const highSlice = high.slice(i - period + 1, i + 1)
    const lowSlice = low.slice(i - period + 1, i + 1)

    const highestHigh = Math.max(...highSlice)
    const lowestLow = Math.min(...lowSlice)

    const rsv = ((close[i] - lowestLow) / (highestHigh - lowestLow)) * 100

    if (i === period - 1) {
      k.push(rsv)
      d.push(rsv)
    } else {
      const newK = (2 * k[i - 1] + rsv) / 3
      const newD = (2 * d[i - 1] + newK) / 3
      k.push(newK)
      d.push(newD)
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

// ============ 数据加载函数 ============

// 加载股票信息
const loadStockInfo = async () => {
  if (!props.tsCode) return

  loading.value = true
  try {
    const result = await getStockList({ search: props.tsCode, page: 1, page_size: 1 })
    if (result.items.length > 0) {
      stockInfo.value = result.items[0]
    }
  } catch (error) {
    console.error('加载股票信息失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载K线数据并计算技术指标
const loadKlineData = async () => {
  if (!props.tsCode) return

  try {
    // 获取最近120个交易日数据（足够计算MA120）
    const klineData = await getStockKline(props.tsCode, {
      period: 'daily',
      limit: 120
    })

    if (klineData.length > 0) {
      // 关键修复：将Decimal字段转换为数字类型
      // 后端返回的Decimal会被序列化为字符串，需要手动转换
      const processedKlineData = klineData.map(k => ({
        ...k,
        open: parseFloat(k.open as string),
        close: parseFloat(k.close as string),
        high: parseFloat(k.high as string),
        low: parseFloat(k.low as string),
        volume: Number(k.volume),
        amount: parseFloat(k.amount as string)
      }))

      // 计算所有技术指标
      const indicators = calculateAllIndicators(processedKlineData)
      technicalIndicators.value = indicators

      // 渲染带均线的K线图
      renderKlineChartWithMA(processedKlineData, indicators)
    } else {
      console.warn('⚠️ K线数据为空')
    }
  } catch (error) {
    console.error('❌ 加载K线数据失败:', error)
  }
}

// 计算所有技术指标
const calculateAllIndicators = (klineData: any[]) => {
  const close = klineData.map(k => k.close)
  const high = klineData.map(k => k.high)
  const low = klineData.map(k => k.low)
  const volume = klineData.map(k => k.volume || 0)

  // 计算MA均线
  const ma5 = calculateSMA(close, 5)
  const ma10 = calculateSMA(close, 10)
  const ma20 = calculateSMA(close, 20)
  const ma60 = calculateSMA(close, 60)
  const ma120 = calculateSMA(close, 120)

  // 计算BBI
  const ma3 = calculateSMA(close, 3)
  const ma6 = calculateSMA(close, 6)
  const ma12 = calculateSMA(close, 12)
  const ma24 = calculateSMA(close, 24)
  const bbi = calculateBBI(ma3, ma6, ma12, ma24)

  // 计算KDJ
  const kdj = calculateKDJ(high, low, close)

  // 计算RSI
  const rsi6 = calculateRSI(close, 6)
  const rsi12 = calculateRSI(close, 12)

  // 计算MACD
  const macdData = calculateMACD(close)

  // 计算涨跌幅
  const changePct = klineData.length >= 2
    ? ((close[close.length - 1] - close[close.length - 2]) / close[close.length - 2]) * 100
    : 0

  // 返回最新的指标值
  const lastIndex = close.length - 1
  return {
    close: close[lastIndex],
    change_pct: changePct,
    volume: volume[lastIndex],
    amount: klineData[lastIndex].amount || 0,
    ma5: ma5[lastIndex],
    ma10: ma10[lastIndex],
    ma20: ma20[lastIndex],
    ma60: ma60[lastIndex],
    ma120: ma120[lastIndex],
    bbi: bbi[lastIndex],
    kdj_k: kdj.k[lastIndex],
    kdj_d: kdj.d[lastIndex],
    kdj_j: kdj.j[lastIndex],
    rsi6: rsi6[lastIndex],
    rsi12: rsi12[lastIndex]
  }
}

// 渲染完整技术分析图表（K线+KDJ+RSI）
const renderKlineChartWithMA = (klineData: any[], indicators: any) => {
  if (!klineChartRef.value) return

  // 初始化图表
  if (!klineChart) {
    klineChart = echarts.init(klineChartRef.value)
  }

  // 准备数据
  const dates = klineData.map(k => k.trade_date)
  const close = klineData.map(k => k.close)
  const high = klineData.map(k => k.high)
  const low = klineData.map(k => k.low)
  const open = klineData.map(k => k.open)
  const values = klineData.map(k => [k.open, k.close, k.low, k.high])
  const volume = klineData.map(k => k.volume || 0)

  // 计算MA均线
  const ma5 = calculateSMA(close, 5)
  const ma10 = calculateSMA(close, 10)
  const ma20 = calculateSMA(close, 20)
  const ma60 = calculateSMA(close, 60)

  // 计算BBI
  const ma3 = calculateSMA(close, 3)
  const ma6 = calculateSMA(close, 6)
  const ma12 = calculateSMA(close, 12)
  const ma24 = calculateSMA(close, 24)
  const bbi = calculateBBI(ma3, ma6, ma12, ma24)

  // 计算KDJ
  const kdj = calculateKDJ(high, low, close)

  // 计算RSI
  const rsi6 = calculateRSI(close, 6)
  const rsi12 = calculateRSI(close, 12)

  const option = {
    title: {
      text: `${props.tsCode} 技术分析`,
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
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
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20', 'MA60', 'BBI', '成交量', 'K', 'D', 'J', 'RSI6', 'RSI12'],
      top: 35,
      textStyle: { fontSize: 11 }
    },
    grid: [
      { left: '8%', right: '6%', top: '14%', height: '35%' },     // K线图
      { left: '8%', right: '6%', top: '52%', height: '11%' },     // 成交量
      { left: '8%', right: '6%', top: '66%', height: '11%' },     // KDJ
      { left: '8%', right: '6%', top: '80%', height: '11%' }      // RSI
    ],
    // 使用graphic在每个子图上方添加标题
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
        start: 50,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1, 2, 3],
        type: 'slider',
        top: '93%',
        start: 50,
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

  klineChart.setOption(option)
}

// 获取日期字符串
const getDateString = (offsetDays: number) => {
  const date = new Date()
  date.setDate(date.getDate() + offsetDays)
  return date.toISOString().split('T')[0]
}

// 查看完整K线图
const handleViewKline = () => {
  emit('update:modelValue', false)
  router.push({ name: 'StockKline', params: { tsCode: props.tsCode } })
}

// 监听弹窗显示
watch(() => props.modelValue, async (visible) => {
  if (visible && props.tsCode) {
    await loadStockInfo()
    await loadKlineData()
  }
})

// 监听窗口大小变化
window.addEventListener('resize', () => {
  klineChart?.resize()
})
</script>

<style scoped lang="scss">
.stock-detail-content {
  .info-section {
    margin-bottom: 24px;
  }

  .reasons-section {
    margin-bottom: 24px;
    padding: 16px;
    background: #f0f9ff;
    border-radius: 8px;

    .section-title {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
    }

    .reason-content {
      .reason-details {
        margin-top: 8px;

        p {
          margin: 4px 0;
          font-size: 14px;
          color: #606266;
        }
      }
    }
  }

  .kline-section {
    margin-bottom: 24px;

    .section-title {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
    }

    .kline-chart {
      width: 100%;
      height: 700px;  // 增加高度以容纳5个子图
    }
  }

  .indicators-section {
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;

    .section-title {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
    }

    .indicator-row {
      margin-bottom: 16px;
    }
  }
}
</style>
