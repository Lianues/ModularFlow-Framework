<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import ThemeManager from '@/features/themes/manager'

const themeInfo = ref(null)
let off = null

onMounted(() => {
  try {
    themeInfo.value = ThemeManager.getCurrentTheme?.() || null
    off = ThemeManager.on?.('change', () => {
      themeInfo.value = ThemeManager.getCurrentTheme?.() || null
    })
  } catch (_) {}
})

onBeforeUnmount(() => {
  try { off?.() } catch (_) {}
  off = null
})

async function onThemeFileSelected(e) {
  const file = e?.target?.files?.[0]
  if (!file) return
  try {
    await ThemeManager.importFromFile(file, { persist: true })
  } catch (err) {
    console.warn('[ThemeManagerTab] Theme import failed:', err)
  } finally {
    try { e.target.value = '' } catch (_) {}
  }
}

async function onThemeReset() {
  try {
    await ThemeManager.resetTheme({ persist: true })
  } catch (err) {
    console.warn('[ThemeManagerTab] Theme reset failed:', err)
  }
}
</script>

<template>
  <div class="st-tab-panel" data-scope="settings-theme">
    <h3>主题管理</h3>
    <p class="muted">导入外部主题包（.json/.sttheme.json），或重置为内置风格。</p>

    <div class="st-control" data-slider="themeImport">
      <label class="st-control-label">
        <span class="label-text">导入主题包</span>
        <div class="value-group">
          <span class="unit">JSON</span>
        </div>
      </label>
      <label class="bg-upload">
        <input type="file" accept=".json,application/json" @change="onThemeFileSelected" />
        选择 .json / .sttheme.json
      </label>
      <div class="st-control-hint">
        <span class="muted" style="font-size:12px;">主题包包含 tokens 与可选 CSS；应用后会持久化于浏览器。</span>
      </div>
    </div>

    <div class="st-control" data-slider="themeStatus">
      <label class="st-control-label">
        <span class="label-text">当前主题</span>
        <div class="value-group">
          <span class="unit" v-if="themeInfo">已应用</span>
          <span class="unit" v-else>未应用</span>
        </div>
      </label>
      <div class="theme-info" v-if="themeInfo">
        <div>名称：{{ themeInfo.name || '未命名' }}</div>
        <div>ID：{{ themeInfo.id || '-' }}</div>
        <div>版本：{{ themeInfo.version || '-' }}</div>
      </div>
      <div class="theme-actions" style="margin-top:8px; display:flex; gap:8px;">
        <button class="st-settings-close" type="button" @click="onThemeReset">重置为默认主题</button>
      </div>
    </div>
  </div>
</template>