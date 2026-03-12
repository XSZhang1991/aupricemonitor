<template>
  <div class="market-summary">
    <div v-if="!latestData.price" class="loading-tip">
      <el-icon class="rotating"><Loading /></el-icon>
      数据加载中，请稍候...
    </div>

    <div v-else class="cards-row">
      <!-- Current Price -->
      <div class="metric-card price-card">
        <div class="metric-label">黄金现价（元/克）</div>
        <div class="metric-value gold">{{ fmt(latestData.price) }}</div>
        <div class="metric-sub" :class="changeClass">
          {{ changeSign }}{{ fmt(latestData.change) }}
          （{{ changeSign }}{{ fmt(latestData.change_pct) }}%）
        </div>
        <div class="metric-time">{{ latestData.update_time }}</div>
      </div>

      <!-- High / Low -->
      <div class="metric-card">
        <div class="metric-label">今日最高 / 最低</div>
        <div class="metric-value-sm">
          <span class="up">{{ fmt(latestData.high) }}</span>
          <span class="sep"> / </span>
          <span class="down">{{ fmt(latestData.low) }}</span>
        </div>
        <div class="metric-label mt8">开盘</div>
        <div class="metric-value-sm">{{ fmt(latestData.open) }}</div>
      </div>

      <!-- Volatility -->
      <div class="metric-card">
        <div class="metric-label">日波动率（年化）</div>
        <div class="metric-value-sm">{{ pct(latestData.volatility_daily) }}</div>
        <div class="metric-label mt8">周波动率（年化）</div>
        <div class="metric-value-sm">{{ pct(latestData.volatility_weekly) }}</div>
      </div>

      <!-- 7d / 15d returns -->
      <div class="metric-card">
        <div class="metric-row">
          <span class="rl">近7日涨幅</span>
          <span :class="retClass(latestData.returns?.['7d'])">{{ retFmt(latestData.returns?.['7d']) }}</span>
        </div>
        <div class="metric-row">
          <span class="rl">近15日涨幅</span>
          <span :class="retClass(latestData.returns?.['15d'])">{{ retFmt(latestData.returns?.['15d']) }}</span>
        </div>
        <div class="metric-row">
          <span class="rl">近30日涨幅</span>
          <span :class="retClass(latestData.returns?.['30d'])">{{ retFmt(latestData.returns?.['30d']) }}</span>
        </div>
        <div class="metric-row">
          <span class="rl">近90日涨幅</span>
          <span :class="retClass(latestData.returns?.['90d'])">{{ retFmt(latestData.returns?.['90d']) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  latestData: { type: Object, default: () => ({}) }
})

const fmt = v => v != null ? Number(v).toFixed(2) : '--'
const pct = v => v != null ? (Number(v) * 100).toFixed(3) + '%' : '--'
const retFmt = v => v != null ? (v >= 0 ? '+' : '') + Number(v).toFixed(2) + '%' : '--'
const retClass = v => v == null ? '' : v >= 0 ? 'up' : 'down'

const changeSign = computed(() => {
  const c = props.latestData.change
  return (c != null && c >= 0) ? '+' : ''
})
const changeClass = computed(() => {
  const c = props.latestData.change
  return c == null ? '' : c >= 0 ? 'up' : 'down'
})
</script>

<style scoped>
.market-summary { padding: 0 0 16px; }

.loading-tip {
  display: flex; align-items: center; gap: 8px;
  color: #8b949e; padding: 20px;
  font-size: 14px;
}
.rotating { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.cards-row {
  display: flex; gap: 12px; flex-wrap: wrap;
}

.metric-card {
  flex: 1; min-width: 180px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 16px;
}

.price-card { min-width: 220px; }

.metric-label {
  font-size: 12px; color: #8b949e; margin-bottom: 6px;
}
.mt8 { margin-top: 8px; }

.metric-value {
  font-size: 28px; font-weight: 700; line-height: 1.2;
}
.metric-value.gold { color: #FFD700; }

.metric-value-sm {
  font-size: 18px; font-weight: 600;
}

.metric-sub {
  font-size: 13px; margin-top: 4px;
}

.metric-time {
  font-size: 11px; color: #8b949e; margin-top: 6px;
}

.metric-row {
  display: flex; justify-content: space-between;
  font-size: 13px; padding: 3px 0;
}
.rl { color: #8b949e; }

.sep { color: #8b949e; }

.up   { color: #ef5350; }
.down { color: #26a69a; }
</style>
