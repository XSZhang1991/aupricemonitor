<template>
  <div class="app-root">
    <Dashboard />
  </div>
</template>

<script setup>
import Dashboard from './views/Dashboard.vue'
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: #0d1117;
  color: #c9d1d9;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
  min-height: 100vh;
}

.app-root {
  min-height: 100vh;
  background: #0d1117;
}

/* Element Plus dark overrides */
.el-card {
  background: #161b22 !important;
  border: 1px solid #30363d !important;
  color: #c9d1d9 !important;
}

.el-card__header {
  border-bottom: 1px solid #30363d !important;
  color: #c9d1d9 !important;
}
</style>
