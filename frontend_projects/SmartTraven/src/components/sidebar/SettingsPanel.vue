<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
const props = defineProps({
  anchorLeft: { type: Number, default: 348 }, // 左侧锚定像素（默认=12+320+16）
  width: { type: Number, default: 520 },      // 面板宽度
  zIndex: { type: Number, default: 59 },      // 与 Sidebar 同层（> 背景模糊 58）
  title: { type: String, default: '应用设置' },
})
const emit = defineEmits(['close'])

const tabs = [
  { key: 'home', label: '主页设定' },
  { key: 'threaded', label: '楼层对话设定' },
  { key: 'sandbox', label: '全屏沙盒设定' },
]
const active = ref('home')

const panelStyle = computed(() => ({
  position: 'fixed',
  left: props.anchorLeft + 'px',
  top: '64px',
  bottom: '12px',
  width: props.width + 'px',
  zIndex: String(props.zIndex),
}))
function close() { emit('close') }

// --- Threaded chat live tuning (font-size & width) ---
const fontSize = ref(18)
const chatWidth = ref(80) // 百分比值，默认80%
const tuning = ref(false)
const activeTuningSlider = ref(null) // 'fontSize' | 'chatWidth' | null

function readCssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name)?.trim()
  if (!v) return fallback
  const n = parseInt(v, 10)
  return Number.isFinite(n) ? n : fallback
}
function setRootVar(name, value) {
  // 对于宽度使用百分比，其他使用px
  const suffix = name === '--st-chat-width' ? '%' : 'px'
  document.documentElement.style.setProperty(name, typeof value === 'number' ? value + suffix : String(value))
}
function onTuningStart(sliderName) {
  tuning.value = true
  activeTuningSlider.value = sliderName
  document.body.classList.add('st-live-tuning')
  document.body.setAttribute('data-active-slider', sliderName)
  // 结束事件绑定（一次性）
  window.addEventListener('pointerup', onTuningEndOnce, { once: true })
  window.addEventListener('touchend', onTuningEndOnce, { once: true })
}
function onTuningEndOnce() {
  tuning.value = false
  activeTuningSlider.value = null
  document.body.classList.remove('st-live-tuning')
  document.body.removeAttribute('data-active-slider')
}
function onFontSizeInput(e) {
  fontSize.value = Number(e.target.value)
  setRootVar('--st-chat-font-size', fontSize.value)
}
function onWidthInput(e) {
  chatWidth.value = Number(e.target.value)
  setRootVar('--st-chat-width', chatWidth.value)
}
function onFontSizeNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 12 && val <= 32) {
    fontSize.value = val
    setRootVar('--st-chat-font-size', fontSize.value)
  }
}
function onWidthNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 30 && val <= 100) {
    chatWidth.value = val
    setRootVar('--st-chat-width', chatWidth.value)
  }
}
onMounted(() => {
  fontSize.value = readCssVar('--st-chat-font-size', 18)
  // 读取宽度百分比值（去掉%符号）
  const widthVar = getComputedStyle(document.documentElement).getPropertyValue('--st-chat-width')?.trim()
  chatWidth.value = widthVar ? parseInt(widthVar, 10) : 80
  // 应用当前值到根变量（确保首次打开即与 UI 同步）
  setRootVar('--st-chat-font-size', fontSize.value)
  setRootVar('--st-chat-width', chatWidth.value)
})
onBeforeUnmount(() => {
  document.body.classList.remove('st-live-tuning')
})
</script>

<template>
  <transition name="st-settings">
    <div
      data-scope="settings-view"
      class="st-settings glass"
      :style="panelStyle"
    >
      <header class="st-settings-header">
        <div class="st-settings-title">
          <span class="st-settings-icon">⚙️</span>
          {{ props.title }}
        </div>
        <button class="st-settings-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <nav class="st-settings-tabs">
        <button
          v-for="t in tabs"
          :key="t.key"
          type="button"
          class="st-tab"
          :class="{ active: active === t.key }"
          @click="active = t.key"
        >
          {{ t.label }}
        </button>
      </nav>

      <section class="st-settings-body">
        <div v-if="active === 'home'" class="st-tab-panel">
          <h3>主页设定</h3>
          <p class="muted">此为占位页面，用于配置应用主页相关选项。</p>
        </div>

        <div v-else-if="active === 'threaded'" class="st-tab-panel">
          <h3>楼层对话设定</h3>

          <div class="st-control" data-slider="fontSize">
            <label class="st-control-label">
              <span class="label-text">文字大小</span>
              <div class="value-group">
                <input
                  type="number"
                  class="st-number-input"
                  :value="fontSize"
                  min="12"
                  max="32"
                  @input="onFontSizeNumberInput"
                />
                <span class="unit">px</span>
              </div>
            </label>
            <input
              type="range"
              min="12"
              max="32"
              step="1"
              :value="fontSize"
              @pointerdown="onTuningStart('fontSize')"
              @input="onFontSizeInput"
            />
          </div>

          <div class="st-control" data-slider="chatWidth">
            <label class="st-control-label">
              <span class="label-text">对话页面宽度</span>
              <div class="value-group">
                <input
                  type="number"
                  class="st-number-input"
                  :value="chatWidth"
                  min="30"
                  max="100"
                  @input="onWidthNumberInput"
                />
                <span class="unit">%</span>
              </div>
            </label>
            <input
              type="range"
              min="30"
              max="100"
              step="1"
              :value="chatWidth"
              @pointerdown="onTuningStart('chatWidth')"
              @input="onWidthInput"
            />
          </div>

          <p class="muted">拖拽滑条时，页面会自动变透明，仅保留本面板不透明，便于实时查看调整效果。</p>
        </div>

        <div v-else class="st-tab-panel">
          <h3>全屏沙盒设定</h3>
          <p class="muted">此为占位页面，用于配置“全屏沙盒”的安全与渲染选项。</p>
        </div>
      </section>
    </div>
  </transition>
</template>

<style scoped>
.st-settings {
  display: grid;
  grid-template-rows: auto auto 1fr;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(var(--st-surface), 0.92);
  backdrop-filter: blur(8px) saturate(130%);
  -webkit-backdrop-filter: blur(8px) saturate(130%);
  box-shadow: var(--st-shadow-md);
  overflow: hidden;
}

/* Header */
.st-settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.st-settings-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.st-settings-icon { font-size: 18px; }
.st-settings-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 8px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.st-settings-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Tabs */
.st-settings-tabs {
  display: flex;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
  background: rgba(var(--st-surface), 0.65);
}
.st-tab {
  padding: 8px 10px;
  border-radius: 9999px;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  transition: background .12s ease, border-color .12s ease, transform .12s ease;
}
.st-tab:hover { transform: translateY(-1px); }
.st-tab.active {
  background: rgba(var(--st-primary), 0.14);
  border-color: rgba(var(--st-primary), 0.4);
}

/* Body */
.st-settings-body {
  padding: 12px;
  overflow: auto;
}
.st-tab-panel h3 { margin: 0 0 6px; font-weight: 700; }
.st-tab-panel .muted { color: rgba(var(--st-color-text), 0.75); margin: 0; }

/* Controls */
.st-control {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  margin: 10px 0 14px;
}
.st-control-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: rgba(var(--st-color-text), 0.9);
  width: 100%;
}
.label-text {
  flex: 0 0 auto;
}
.value-group {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}
.st-number-input {
  width: 50px;
  padding: 2px 4px;
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: 4px;
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  text-align: right;
  font-size: 12px;
}
.unit {
  opacity: .7;
  font-size: 12px;
}
.st-control input[type="range"] { width: 100%; }

/* 进出场动画（与 Sidebar 保持同层） */
.st-settings-enter-from { opacity: 0; transform: translateX(-10px) scale(0.98); filter: blur(4px); }
.st-settings-leave-to   { opacity: 0; transform: translateX(-12px) scale(0.98); filter: blur(4px); }
.st-settings-enter-active,
.st-settings-leave-active { transition: opacity .18s ease, transform .22s cubic-bezier(.22,.61,.36,1), filter .22s ease; }
</style>