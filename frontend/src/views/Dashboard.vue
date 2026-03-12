<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="header">
      <div class="header-left">
        <span class="title">黄金价格与波动率监控系统</span>
        <span class="badge">Au99.99 · SGE现货</span>
        <el-tag
          :type="dbStatus.status === 'ok' ? 'success' : 'danger'"
          size="small"
          style="margin-left: 8px"
        >
          {{ dbStatus.status === 'ok' ? '数据库正常' : '数据库异常' }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-tooltip content="数据条数: 日线、5分钟、1分钟" placement="bottom">
          <span class="count-tip" v-if="dbStatus.data_counts">
            日线 {{ dbStatus.data_counts.daily }} |
            5分钟 {{ dbStatus.data_counts['5min'] }} |
            1分钟 {{ dbStatus.data_counts['1min'] }}
          </span>
        </el-tooltip>
        <el-button
          type="warning"
          :loading="fetching"
          @click="handleFetchHistory"
          size="default"
        >
          <el-icon><Download /></el-icon>
          获取历史数据
        </el-button>
        <el-button @click="handleRefresh" :loading="refreshing" circle>
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- Market Summary -->
    <div class="section">
      <MarketSummary :latestData="latestData" />
    </div>

    <!-- Chart Controls -->
    <div class="chart-controls">
      <div class="controls-left">
        <!-- Interval -->
        <el-radio-group v-model="interval" size="small" @change="onIntervalChange">
          <el-radio-button label="daily">日K</el-radio-button>
          <el-radio-button label="5min">5分钟</el-radio-button>
          <el-radio-button label="1min">1分钟</el-radio-button>
        </el-radio-group>

        <!-- Date range -->
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="—"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          style="width: 240px"
          :shortcuts="shortcuts"
        />
      </div>

      <div class="controls-right">
        <span class="ctrl-label">叠加指标：</span>
        <el-checkbox-group v-model="selectedIndicators" size="small">
          <el-checkbox-button label="ma">均线</el-checkbox-button>
          <el-checkbox-button label="boll">布林带</el-checkbox-button>
          <el-checkbox-button label="macd">MACD</el-checkbox-button>
          <el-checkbox-button label="rsi">RSI</el-checkbox-button>
        </el-checkbox-group>
      </div>
    </div>

    <!-- K-line Chart -->
    <div class="section chart-section">
      <KlineChart
        ref="klineRef"
        :interval="interval"
        :dateRange="dateRange"
        :selectedIndicators="selectedIndicators"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import MarketSummary from '../components/MarketSummary.vue'
import KlineChart    from '../components/KlineChart.vue'
import { getLatest, fetchHistory, getStatus } from '../api/index.js'

// ── State ──────────────────────────────────────────────────────────────────
const latestData         = ref({})
const interval           = ref('daily')
const selectedIndicators = ref(['ma', 'macd'])
const fetching           = ref(false)
const refreshing         = ref(false)
const dbStatus           = ref({})
const klineRef           = ref(null)

const defaultDateRange = () => {
  const end   = new Date()
  const start = new Date()
  start.setFullYear(start.getFullYear() - 1)
  return [start, end]
}
const dateRange = ref(defaultDateRange())

// ── Date picker shortcuts ──────────────────────────────────────────────────
const shortcuts = [
  { text: '近1个月', value: () => { const e = new Date(); const s = new Date(); s.setMonth(s.getMonth() - 1); return [s, e] } },
  { text: '近3个月', value: () => { const e = new Date(); const s = new Date(); s.setMonth(s.getMonth() - 3); return [s, e] } },
  { text: '近6个月', value: () => { const e = new Date(); const s = new Date(); s.setMonth(s.getMonth() - 6); return [s, e] } },
  { text: '近1年',   value: () => { const e = new Date(); const s = new Date(); s.setFullYear(s.getFullYear() - 1); return [s, e] } },
  { text: '近3年',   value: () => { const e = new Date(); const s = new Date(); s.setFullYear(s.getFullYear() - 3); return [s, e] } },
]

// ── Interval change resets date range ─────────────────────────────────────
function onIntervalChange(val) {
  const end   = new Date()
  const start = new Date()
  if (val === '1min')       start.setDate(start.getDate() - 3)
  else if (val === '5min')  start.setDate(start.getDate() - 14)
  else                      start.setFullYear(start.getFullYear() - 1)
  dateRange.value = [start, end]
}

// ── API calls ──────────────────────────────────────────────────────────────
async function loadLatest() {
  try {
    const res = await getLatest()
    latestData.value = res.data
  } catch {
    // silent — will retry
  }
}

async function loadStatus() {
  try {
    const res = await getStatus()
    dbStatus.value = res.data
  } catch {
    dbStatus.value = { status: 'error' }
  }
}

async function handleFetchHistory() {
  fetching.value = true
  try {
    await fetchHistory()
    ElNotification({ title: '提示', message: '历史数据正在后台获取，约需1-2分钟...', type: 'info' })
    setTimeout(async () => {
      await Promise.all([loadLatest(), loadStatus()])
      klineRef.value?.refresh()
      fetching.value = false
    }, 90000)
  } catch (err) {
    ElMessage.error('启动失败: ' + (err.message || err))
    fetching.value = false
  }
}

async function handleRefresh() {
  refreshing.value = true
  await Promise.all([loadLatest(), loadStatus()])
  klineRef.value?.refresh()
  refreshing.value = false
}

// ── Auto refresh ──────────────────────────────────────────────────────────
let timer = null

onMounted(async () => {
  await Promise.all([loadLatest(), loadStatus()])
  timer = setInterval(loadLatest, 60000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.dashboard {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px 20px;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #30363d;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.title {
  font-size: 20px;
  font-weight: 700;
  color: #FFD700;
  white-space: nowrap;
}

.badge {
  font-size: 12px;
  background: rgba(255, 215, 0, 0.12);
  color: #FFD700;
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid rgba(255, 215, 0, 0.3);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.count-tip {
  font-size: 12px;
  color: #8b949e;
}

/* Section */
.section {
  margin-bottom: 16px;
}

/* Chart controls */
.chart-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
}

.controls-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.ctrl-label {
  font-size: 13px;
  color: #8b949e;
  white-space: nowrap;
}

/* Chart section */
.chart-section {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  overflow: hidden;
}

/* Element Plus overrides for dark theme */
:deep(.el-radio-button__inner) {
  background: #21262d !important;
  border-color: #30363d !important;
  color: #8b949e !important;
}
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(255, 215, 0, 0.15) !important;
  border-color: #FFD700 !important;
  color: #FFD700 !important;
  box-shadow: none !important;
}
:deep(.el-checkbox-button__inner) {
  background: #21262d !important;
  border-color: #30363d !important;
  color: #8b949e !important;
}
:deep(.el-checkbox-button.is-checked .el-checkbox-button__inner) {
  background: rgba(255, 215, 0, 0.15) !important;
  border-color: #FFD700 !important;
  color: #FFD700 !important;
  box-shadow: none !important;
}
:deep(.el-input__wrapper) {
  background: #21262d !important;
  border: 1px solid #30363d !important;
  box-shadow: none !important;
}
:deep(.el-input__inner), :deep(.el-range-input) {
  color: #c9d1d9 !important;
  background: transparent !important;
}
:deep(.el-range-separator) {
  color: #8b949e !important;
}
:deep(.el-button--warning) {
  background: rgba(255, 215, 0, 0.15) !important;
  border-color: #FFD700 !important;
  color: #FFD700 !important;
}
:deep(.el-button--warning:hover) {
  background: rgba(255, 215, 0, 0.25) !important;
}
:deep(.el-button.is-circle) {
  background: #21262d !important;
  border-color: #30363d !important;
  color: #8b949e !important;
}
</style>
