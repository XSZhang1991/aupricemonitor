<template>
  <div class="kline-wrap">
    <div v-if="loading" class="chart-loading">
      <el-icon class="rotating"><Loading /></el-icon> 加载数据中...
    </div>
    <div v-else-if="noData" class="chart-empty">
      暂无数据，请先点击「获取历史数据」按钮
    </div>
    <div ref="chartEl" class="chart-container" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getKline, getIndicators } from '../api/index.js'
import { ElMessage } from 'element-plus'

const props = defineProps({
  interval:           { type: String,  default: 'daily' },
  dateRange:          { type: Array,   default: () => [] },
  selectedIndicators: { type: Array,   default: () => ['ma', 'macd'] },
})

const chartEl   = ref(null)
const loading   = ref(false)
const noData    = ref(false)
let   chart     = null

// ── Date helpers ───────────────────────────────────────────────────────────

const fmtDate = d => {
  if (!d) return ''
  const dt = d instanceof Date ? d : new Date(d)
  return dt.toISOString().slice(0, 10)
}

// ── ECharts init ───────────────────────────────────────────────────────────

function initChart() {
  if (chartEl.value && !chart) {
    chart = echarts.init(chartEl.value, null, { renderer: 'canvas' })
  }
}

function disposeChart() {
  chart?.dispose()
  chart = null
}

// ── Build ECharts option ──────────────────────────────────────────────────

function buildOption(klineData, indData, interval, selectedInd) {
  const times   = klineData.map(d => d.time)
  const ohlc    = klineData.map(d => [d.open, d.close, d.low, d.high])
  const volumes = klineData.map(d => d.volume ?? 0)

  const showMacd  = selectedInd.includes('macd')
  const showRsi   = selectedInd.includes('rsi') && !showMacd
  const showBott  = selectedInd.includes('macd') || showRsi  // bottom panel visible
  const showMa    = selectedInd.includes('ma')
  const showBoll  = selectedInd.includes('boll')

  // Grid layout
  const mainBottom  = showBott ? '40%' : '15%'
  const volTop      = showBott ? '62%'  : '72%'
  const volBottom   = showBott ? '32%'  : '5%'
  const bottTop     = '73%'

  const grids = [
    { left: 60, right: 60, top: 40, bottom: mainBottom },
    { left: 60, right: 60, top: volTop,  bottom: volBottom },
  ]
  if (showBott) grids.push({ left: 60, right: 60, top: bottTop, bottom: '5%' })

  // --- Indicator map by time
  const indMap = {}
  indData.forEach(d => { indMap[d.time] = d })

  // --- Series
  const series = []

  // Candlestick
  series.push({
    name: 'K线',
    type: 'candlestick',
    xAxisIndex: 0, yAxisIndex: 0,
    data: ohlc,
    itemStyle: {
      color: '#ef5350',         // up candle (close > open) — red in Chinese convention
      color0: '#26a69a',        // down candle
      borderColor: '#ef5350',
      borderColor0: '#26a69a',
    },
  })

  // MA lines
  if (showMa) {
    const maConfig = [
      { key: 'ma5',  name: 'MA5',  color: '#FFEB3B' },
      { key: 'ma10', name: 'MA10', color: '#2196F3' },
      { key: 'ma20', name: 'MA20', color: '#FF9800' },
      { key: 'ma60', name: 'MA60', color: '#9C27B0' },
    ]
    maConfig.forEach(({ key, name, color }) => {
      series.push({
        name, type: 'line',
        xAxisIndex: 0, yAxisIndex: 0,
        data: times.map(t => indMap[t]?.[key] ?? null),
        smooth: false,
        symbol: 'none',
        lineStyle: { width: 1, color },
        itemStyle: { color },
      })
    })
  }

  // Bollinger Bands
  if (showBoll) {
    const bollColors = ['rgba(255,255,255,0.5)', 'rgba(255,255,255,0.7)', 'rgba(255,255,255,0.5)']
    ;['boll_upper', 'boll_mid', 'boll_lower'].forEach((key, i) => {
      series.push({
        name: key === 'boll_mid' ? 'BOLL中轨' : key === 'boll_upper' ? 'BOLL上轨' : 'BOLL下轨',
        type: 'line',
        xAxisIndex: 0, yAxisIndex: 0,
        data: times.map(t => indMap[t]?.[key] ?? null),
        symbol: 'none',
        lineStyle: { width: 1, color: bollColors[i], type: i === 1 ? 'solid' : 'dashed' },
        itemStyle: { color: bollColors[i] },
      })
    })
  }

  // Volume bars
  series.push({
    name: '成交量',
    type: 'bar',
    xAxisIndex: 1, yAxisIndex: 1,
    data: volumes.map((v, i) => ({
      value: v,
      itemStyle: {
        color: (ohlc[i][1] >= ohlc[i][0]) ? 'rgba(239,83,80,0.6)' : 'rgba(38,166,154,0.6)',
      },
    })),
  })

  // MACD
  if (showMacd && grids.length > 2) {
    series.push({
      name: 'MACD',
      type: 'bar',
      xAxisIndex: 2, yAxisIndex: 2,
      data: times.map(t => {
        const h = indMap[t]?.macd_hist
        return h == null ? null : {
          value: h,
          itemStyle: { color: h >= 0 ? '#ef5350' : '#26a69a' },
        }
      }),
    })
    ;[
      { key: 'macd_dif', name: 'DIF',  color: '#FFEB3B' },
      { key: 'macd_dea', name: 'DEA',  color: '#FF9800' },
    ].forEach(({ key, name, color }) => {
      series.push({
        name, type: 'line',
        xAxisIndex: 2, yAxisIndex: 2,
        data: times.map(t => indMap[t]?.[key] ?? null),
        symbol: 'none',
        lineStyle: { width: 1, color },
        itemStyle: { color },
      })
    })
  }

  // RSI
  if (showRsi && grids.length > 2) {
    ;[
      { key: 'rsi_6',  name: 'RSI6',  color: '#FFEB3B' },
      { key: 'rsi_12', name: 'RSI12', color: '#2196F3' },
      { key: 'rsi_24', name: 'RSI24', color: '#FF9800' },
    ].forEach(({ key, name, color }) => {
      series.push({
        name, type: 'line',
        xAxisIndex: 2, yAxisIndex: 2,
        data: times.map(t => indMap[t]?.[key] ?? null),
        symbol: 'none',
        lineStyle: { width: 1, color },
        itemStyle: { color },
      })
    })
  }

  // --- xAxis
  const xAxisFmt = interval === 'daily'
    ? val => val.slice(0, 10)
    : val => val.slice(5, 16)

  const axisCount = grids.length
  const xAxes = Array.from({ length: axisCount }, (_, i) => ({
    type: 'category',
    data: times,
    gridIndex: i,
    axisLine:  { lineStyle: { color: '#30363d' } },
    axisLabel: i < axisCount - 1
      ? { show: false }
      : { color: '#8b949e', fontSize: 11, formatter: xAxisFmt },
    splitLine: { show: false },
    axisTick:  { show: false },
  }))

  const yAxes = grids.map((_, i) => ({
    type: 'value',
    gridIndex: i,
    scale: true,
    splitNumber: i === 0 ? 5 : 3,
    axisLabel:  { color: '#8b949e', fontSize: 11 },
    axisLine:   { show: false },
    splitLine:  { lineStyle: { color: '#21262d', type: 'dashed' } },
  }))

  // dataZoom — default: show last 120 points
  const startVal = Math.max(0, times.length - 120)
  const startPct = Math.round(startVal / Math.max(times.length, 1) * 100)

  return {
    backgroundColor: '#0d1117',
    animation: false,
    legend: {
      top: 4, left: 60,
      textStyle: { color: '#8b949e', fontSize: 11 },
      itemWidth: 16, itemHeight: 8,
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }], label: { backgroundColor: '#21262d' } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: '#21262d',
      borderColor: '#30363d',
      textStyle: { color: '#c9d1d9', fontSize: 12 },
      formatter(params) {
        if (!params.length) return ''
        const t = params[0].axisValue
        let html = `<div style="font-weight:600;margin-bottom:4px">${t}</div>`
        params.forEach(p => {
          if (p.seriesType === 'candlestick') {
            const [o, c, l, h] = p.data
            html += `开: ${o}  收: ${c}  高: ${h}  低: ${l}<br>`
          } else if (p.value != null) {
            html += `${p.marker}${p.seriesName}: ${
              typeof p.value === 'object' ? p.value.value ?? '' : p.value
            }<br>`
          }
        })
        return html
      },
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: Array.from({ length: axisCount }, (_, i) => i), start: startPct, end: 100 },
      { type: 'slider', xAxisIndex: Array.from({ length: axisCount }, (_, i) => i), start: startPct, end: 100,
        bottom: showBott ? '3%' : '1%', height: 20,
        fillerColor: 'rgba(255,215,0,0.1)', borderColor: '#30363d',
        textStyle: { color: '#8b949e' } },
    ],
    grid:    grids,
    xAxis:   xAxes,
    yAxis:   yAxes,
    series,
  }
}

// ── Load data & render ────────────────────────────────────────────────────

async function loadAndRender() {
  if (!chart) return
  const [startDate, endDate] = [
    fmtDate(props.dateRange[0]) || '',
    fmtDate(props.dateRange[1]) || '',
  ]
  loading.value = true
  noData.value  = false
  try {
    const [kRes, iRes] = await Promise.all([
      getKline(props.interval, startDate, endDate),
      props.interval === 'daily' ? getIndicators(startDate, endDate) : Promise.resolve({ data: { data: [] } }),
    ])
    const klineData = kRes.data.data ?? []
    const indData   = iRes.data.data ?? []

    if (!klineData.length) {
      noData.value = true
      chart.clear()
      return
    }
    const opt = buildOption(klineData, indData, props.interval, props.selectedIndicators)
    chart.setOption(opt, true)
  } catch (err) {
    ElMessage.error('图表数据加载失败: ' + (err.message || err))
  } finally {
    loading.value = false
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────

onMounted(async () => {
  await nextTick()
  initChart()
  await loadAndRender()

  // Responsive resize
  const ro = new ResizeObserver(() => chart?.resize())
  if (chartEl.value) ro.observe(chartEl.value)
  onUnmounted(() => ro.disconnect())
})

onUnmounted(() => disposeChart())

watch(
  () => [props.interval, props.dateRange, props.selectedIndicators],
  () => loadAndRender(),
  { deep: true },
)

// Expose for parent refresh
defineExpose({ refresh: loadAndRender })
</script>

<style scoped>
.kline-wrap {
  position: relative;
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 680px;
}

.chart-loading,
.chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: #8b949e;
  background: #0d1117;
  z-index: 10;
}

.rotating {
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
