<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

/**
 * 全屏沙盒外观配置（拆分自 AppearancePanel）
 * - 控制 CSS 变量：--st-sandbox-aspect / --st-sandbox-max-width / --st-sandbox-padding / --st-sandbox-radius
 *                --st-sandbox-bg-opacity / --st-sandbox-stage-bg-opacity
 * - 本页签独立持久化（localStorage）：st.appearance.sandbox.v1
 */

/* helpers */
function readCssVarFloat(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name)?.trim()
  if (!v) return fallback
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : fallback
}
function setRootVar(name, value) {
  document.documentElement.style.setProperty(name, typeof value === 'number' ? `${value}px` : String(value))
}
function setRootVarUnitless(name, value) {
  document.documentElement.style.setProperty(name, String(value))
}

/* state */
const sandboxAspectX = ref(16)
const sandboxAspectY = ref(9)
const sandboxMaxWidth = ref(1100)
const sandboxMaxWidthLimit = ref(1920)
const sandboxPadding = ref(16)
const sandboxRadius = ref(18)
const sandboxBgOpacityPct = ref(12)     // 0~100
const sandboxStageBgOpacityPct = ref(82) // 0~100

const aspectPresets = [
  { label: '16:9', v: [16, 9] },
  { label: '4:3', v: [4, 3] },
  { label: '21:9', v: [21, 9] },
  { label: '1:1', v: [1, 1] },
]

/* live tuning indicator */
const tuning = ref(false)
const activeTuningSlider = ref(null)
function onTuningStart(sliderName) {
  tuning.value = true
  activeTuningSlider.value = sliderName
  document.body.classList.add('st-live-tuning')
  document.body.setAttribute('data-active-slider', sliderName)
  window.addEventListener('pointerup', onTuningEndOnce, { once: true })
  window.addEventListener('touchend', onTuningEndOnce, { once: true })
}
function onTuningEndOnce() {
  tuning.value = false
  activeTuningSlider.value = null
  document.body.classList.remove('st-live-tuning')
  document.body.removeAttribute('data-active-slider')
}

/* handlers: 画面宽高比 */
function onSandboxAspectPreset(e) {
  const raw = e.target.value
  if (!raw) return
  const [ax, ay] = raw.split(',').map(Number)
  if (ax > 0 && ay > 0) {
    sandboxAspectX.value = ax
    sandboxAspectY.value = ay
    setRootVar('--st-sandbox-aspect', `${ax} / ${ay}`)
  }
}
function onSandboxAspectNumInputX(e) {
  const v = Number(e.target.value)
  if (v > 0) {
    sandboxAspectX.value = v
    setRootVar('--st-sandbox-aspect', `${sandboxAspectX.value} / ${sandboxAspectY.value}`)
  }
}
function onSandboxAspectNumInputY(e) {
  const v = Number(e.target.value)
  if (v > 0) {
    sandboxAspectY.value = v
    setRootVar('--st-sandbox-aspect', `${sandboxAspectX.value} / ${sandboxAspectY.value}`)
  }
}

/* handlers: 尺寸与圆角/内边距 */
function onSandboxMaxWidthNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 640 && v <= sandboxMaxWidthLimit.value) {
    sandboxMaxWidth.value = v
    setRootVar('--st-sandbox-max-width', sandboxMaxWidth.value)
  }
}
function onSandboxMaxWidthRangeInput(e) {
  sandboxMaxWidth.value = Number(e.target.value)
  setRootVar('--st-sandbox-max-width', sandboxMaxWidth.value)
}
function onSandboxMaxWidthLimitInput(e) {
  const v = Number(e.target.value)
  if (v >= 640 && v <= 3840) {
    sandboxMaxWidthLimit.value = v
    if (sandboxMaxWidth.value > v) {
      sandboxMaxWidth.value = v
      setRootVar('--st-sandbox-max-width', sandboxMaxWidth.value)
    }
  }
}
function onSandboxPaddingNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 48) {
    sandboxPadding.value = v
    setRootVar('--st-sandbox-padding', sandboxPadding.value)
  }
}
function onSandboxPaddingRangeInput(e) {
  sandboxPadding.value = Number(e.target.value)
  setRootVar('--st-sandbox-padding', sandboxPadding.value)
}
function onSandboxRadiusNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 32) {
    sandboxRadius.value = v
    setRootVar('--st-sandbox-radius', sandboxRadius.value)
  }
}
function onSandboxRadiusRangeInput(e) {
  sandboxRadius.value = Number(e.target.value)
  setRootVar('--st-sandbox-radius', sandboxRadius.value)
}

/* handlers: 不透明度（%→小数写 CSS） */
function onSandboxBgOpacityNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 100) {
    sandboxBgOpacityPct.value = v
    setRootVarUnitless('--st-sandbox-bg-opacity', String(v / 100))
  }
}
function onSandboxBgOpacityRangeInput(e) {
  sandboxBgOpacityPct.value = Number(e.target.value)
  setRootVarUnitless('--st-sandbox-bg-opacity', String(sandboxBgOpacityPct.value / 100))
}
function onSandboxStageBgOpacityNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 100) {
    sandboxStageBgOpacityPct.value = v
    setRootVarUnitless('--st-sandbox-stage-bg-opacity', String(v / 100))
  }
}
function onSandboxStageBgOpacityRangeInput(e) {
  sandboxStageBgOpacityPct.value = Number(e.target.value)
  setRootVarUnitless('--st-sandbox-stage-bg-opacity', String(sandboxStageBgOpacityPct.value / 100))
}

/* persistence (tab-scoped) */
const STORE_KEY = 'st.appearance.sandbox.v1'
let __lastSaved = ''
let __saveTimer = null

function getSnapshot() {
  return {
    sandboxAspectX: Number(sandboxAspectX.value),
    sandboxAspectY: Number(sandboxAspectY.value),
    sandboxMaxWidth: Number(sandboxMaxWidth.value),
    sandboxMaxWidthLimit: Number(sandboxMaxWidthLimit.value),
    sandboxPadding: Number(sandboxPadding.value),
    sandboxRadius: Number(sandboxRadius.value),
    sandboxBgOpacityPct: Number(sandboxBgOpacityPct.value),
    sandboxStageBgOpacityPct: Number(sandboxStageBgOpacityPct.value),
  }
}
function applyState(s) {
  if (!s || typeof s !== 'object') return
  const num = (v, f) => (typeof v === 'number' ? v : f)

  sandboxAspectX.value = num(s.sandboxAspectX, 16)
  sandboxAspectY.value = num(s.sandboxAspectY, 9)
  setRootVar('--st-sandbox-aspect', `${sandboxAspectX.value} / ${sandboxAspectY.value}`)

  sandboxMaxWidth.value = num(s.sandboxMaxWidth, 1100)
  setRootVar('--st-sandbox-max-width', sandboxMaxWidth.value)

  sandboxMaxWidthLimit.value = num(s.sandboxMaxWidthLimit, 1920)

  sandboxPadding.value = num(s.sandboxPadding, 16)
  setRootVar('--st-sandbox-padding', sandboxPadding.value)

  sandboxRadius.value = num(s.sandboxRadius, 18)
  setRootVar('--st-sandbox-radius', sandboxRadius.value)

  sandboxBgOpacityPct.value = num(s.sandboxBgOpacityPct, 12)
  setRootVarUnitless('--st-sandbox-bg-opacity', String(sandboxBgOpacityPct.value / 100))

  sandboxStageBgOpacityPct.value = num(s.sandboxStageBgOpacityPct, 82)
  setRootVarUnitless('--st-sandbox-stage-bg-opacity', String(sandboxStageBgOpacityPct.value / 100))
}
function loadSaved() {
  try {
    const raw = localStorage.getItem(STORE_KEY)
    if (!raw) return
    const saved = JSON.parse(raw)
    applyState(saved)
    __lastSaved = raw
  } catch (_) {}
}
function maybeSave() {
  try {
    const snap = getSnapshot()
    const str = JSON.stringify(snap)
    if (str !== __lastSaved) {
      localStorage.setItem(STORE_KEY, str)
      __lastSaved = str
    }
  } catch (_) {}
}

onMounted(() => {
  // init from CSS vars
  const rs = getComputedStyle(document.documentElement)

  // aspect
  const aspRaw = rs.getPropertyValue('--st-sandbox-aspect')?.trim()
  if (aspRaw && aspRaw.includes('/')) {
    const parts = aspRaw.split('/')
    const ax = parseFloat(parts[0]); const ay = parseFloat(parts[1])
    if (Number.isFinite(ax) && Number.isFinite(ay) && ax > 0 && ay > 0) {
      sandboxAspectX.value = Math.round(ax)
      sandboxAspectY.value = Math.round(ay)
    }
  }

  sandboxMaxWidth.value = readCssVarFloat('--st-sandbox-max-width', 1100)
  sandboxPadding.value = readCssVarFloat('--st-sandbox-padding', 16)
  sandboxRadius.value = readCssVarFloat('--st-sandbox-radius', 18)

  // opacities (css stores 0~1)
  sandboxBgOpacityPct.value = Math.round(readCssVarFloat('--st-sandbox-bg-opacity', 0.12) * 100)
  sandboxStageBgOpacityPct.value = Math.round(readCssVarFloat('--st-sandbox-stage-bg-opacity', 0.82) * 100)

  // write-back to ensure sync
  setRootVar('--st-sandbox-max-width', sandboxMaxWidth.value)
  setRootVar('--st-sandbox-padding', sandboxPadding.value)
  setRootVar('--st-sandbox-radius', sandboxRadius.value)
  setRootVarUnitless('--st-sandbox-aspect', `${sandboxAspectX.value} / ${sandboxAspectY.value}`)
  setRootVarUnitless('--st-sandbox-bg-opacity', String(sandboxBgOpacityPct.value / 100))
  setRootVarUnitless('--st-sandbox-stage-bg-opacity', String(sandboxStageBgOpacityPct.value / 100))

  loadSaved()
  if (__saveTimer) { clearInterval(__saveTimer); __saveTimer = null }
  __saveTimer = setInterval(maybeSave, 1000)
})

onBeforeUnmount(() => { if (__saveTimer) { clearInterval(__saveTimer); __saveTimer = null } })
</script>

<template>
  <div class="st-tab-panel" data-scope="settings-sandbox">
    <h3>全屏沙盒外观</h3>
    <p class="muted">配置沙盒舞台的尺寸与长宽比，便于后续嵌入画面/预览对齐。</p>

    <!-- 画面宽高比 -->
    <div class="st-control" data-slider="sandboxAspect">
      <label class="st-control-label">
        <span class="label-text">画面宽高比</span>
        <div class="value-group">
          <select class="st-number-input" @change="onSandboxAspectPreset">
            <option disabled selected value="">预设</option>
            <option v-for="p in aspectPresets" :key="p.label" :value="p.v.join(',')">{{ p.label }}</option>
          </select>
          <span class="unit">或 自定义</span>
        </div>
      </label>
      <div style="display:flex; gap:8px; align-items:center;">
        <input type="number" class="st-number-input" :value="sandboxAspectX" min="1" max="100" @input="onSandboxAspectNumInputX" />
        <span>:</span>
        <input type="number" class="st-number-input" :value="sandboxAspectY" min="1" max="100" @input="onSandboxAspectNumInputY" />
      </div>
    </div>

    <!-- 舞台最大宽度 -->
    <div class="st-control" data-slider="sandboxMaxWidth">
      <label class="st-control-label">
        <span class="label-text">舞台最大宽度</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="sandboxMaxWidth" min="640" :max="sandboxMaxWidthLimit" @input="onSandboxMaxWidthNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="640" :max="sandboxMaxWidthLimit" step="10" :value="sandboxMaxWidth" @pointerdown="onTuningStart('sandboxMaxWidth')" @input="onSandboxMaxWidthRangeInput" />
      <div class="st-control-hint">
        <label class="st-control-label">
          <span class="label-text" style="font-size: 11px; opacity: 0.8;">滑条最大值</span>
          <div class="value-group">
            <input type="number" class="st-number-input" :value="sandboxMaxWidthLimit" min="640" max="3840" @input="onSandboxMaxWidthLimitInput" style="width: 60px;" />
            <span class="unit">px</span>
          </div>
        </label>
      </div>
    </div>

    <!-- 内边距 -->
    <div class="st-control" data-slider="sandboxPadding">
      <label class="st-control-label">
        <span class="label-text">舞台内边距</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="sandboxPadding" min="0" max="48" @input="onSandboxPaddingNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="0" max="48" step="1" :value="sandboxPadding" @pointerdown="onTuningStart('sandboxPadding')" @input="onSandboxPaddingRangeInput" />
    </div>

    <!-- 圆角 -->
    <div class="st-control" data-slider="sandboxRadius">
      <label class="st-control-label">
        <span class="label-text">舞台圆角</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="sandboxRadius" min="0" max="32" @input="onSandboxRadiusNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="0" max="32" step="1" :value="sandboxRadius" @pointerdown="onTuningStart('sandboxRadius')" @input="onSandboxRadiusRangeInput" />
    </div>

    <!-- 背景图片遮罩不透明度 -->
    <div class="st-control" data-slider="sandboxBgOpacity">
      <label class="st-control-label">
        <span class="label-text">背景图片遮罩不透明度</span>
        <div class="value-group">
          <input
            type="number"
            class="st-number-input"
            :value="sandboxBgOpacityPct"
            min="0"
            max="100"
            @input="onSandboxBgOpacityNumberInput"
          />
          <span class="unit">%</span>
        </div>
      </label>
      <input
        type="range"
        min="0"
        max="100"
        step="1"
        :value="sandboxBgOpacityPct"
        @pointerdown="onTuningStart('sandboxBgOpacity')"
        @input="onSandboxBgOpacityRangeInput"
      />
    </div>

    <!-- 舞台背景不透明度 -->
    <div class="st-control" data-slider="sandboxStageBgOpacity">
      <label class="st-control-label">
        <span class="label-text">舞台背景不透明度</span>
        <div class="value-group">
          <input
            type="number"
            class="st-number-input"
            :value="sandboxStageBgOpacityPct"
            min="0"
            max="100"
            @input="onSandboxStageBgOpacityNumberInput"
          />
          <span class="unit">%</span>
        </div>
      </label>
      <input
        type="range"
        min="0"
        max="100"
        step="1"
        :value="sandboxStageBgOpacityPct"
        @pointerdown="onTuningStart('sandboxStageBgOpacity')"
        @input="onSandboxStageBgOpacityRangeInput"
      />
    </div>

    <p class="muted">提示：上述设定实时作用于页面上的"全局沙盒"舞台，并以 CSS 变量方式保存，便于主题或脚本统一接管。</p>
  </div>
</template>

<style>
/* 复制自 AppearancePanel 的 range slider 非 scoped 样式（限定 data-scope），以保持一致外观 */
[data-scope="settings-view"] .st-control input[type="range"],
[data-scope="settings-sandbox"] .st-control input[type="range"] {
  -webkit-appearance: none; appearance: none; background: transparent; width: 100%;
}
[data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-runnable-track,
[data-scope="settings-sandbox"] .st-control input[type="range"]::-webkit-slider-runnable-track {
  height: 8px !important; border-radius: 9999px !important;
  background: linear-gradient(180deg, rgba(0,0,0,0.68), rgba(0,0,0,0.82)) !important;
  border: 1px solid rgba(0,0,0,0.92) !important;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.25), 0 1px 0 rgba(255,255,255,0.15) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]::-moz-range-track,
[data-scope="settings-sandbox"] .st-control input[type="range"]::-moz-range-track {
  height: 8px !important; border-radius: 9999px !important;
  background: linear-gradient(180deg, rgba(0,0,0,0.68), rgba(0,0,0,0.82)) !important;
  border: 1px solid rgba(0,0,0,0.92) !important;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.25), 0 1px 0 rgba(255,255,255,0.15) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-thumb,
[data-scope="settings-sandbox"] .st-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none; width: 18px; height: 18px; border-radius: 9999px;
  background: linear-gradient(180deg, #ffffff, #f8f9fa) !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.9), 0 2px 4px rgba(0,0,0,0.20), 0 4px 8px rgba(0,0,0,0.10) !important;
  margin-top: -6px; cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
[data-scope="settings-view"] .st-control input[type="range"]::-moz-range-thumb,
[data-scope="settings-sandbox"] .st-control input[type="range"]::-moz-range-thumb {
  width: 18px; height: 18px; border-radius: 9999px;
  background: linear-gradient(180deg, #ffffff, #f8f9fa) !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.9), 0 2px 4px rgba(0,0,0,0.20), 0 4px 8px rgba(0,0,0,0.10) !important;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-runnable-track,
[data-theme="dark"] [data-scope="settings-sandbox"] .st-control input[type="range"]::-webkit-slider-runnable-track {
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.85)) !important;
  border: 1px solid rgba(255,255,255,0.95) !important;
  box-shadow: inset 0 1px 2px rgba(255,255,255,0.20), 0 1px 0 rgba(0,0,0,0.15) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-moz-range-track,
[data-theme="dark"] [data-scope="settings-sandbox"] .st-control input[type="range"]::-moz-range-track {
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.85)) !important;
  border: 1px solid rgba(255,255,255,0.95) !important;
  box-shadow: inset 0 1px 2px rgba(255,255,255,0.20), 0 1px 0 rgba(0,0,0,0.15) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-thumb,
[data-theme="dark"] [data-scope="settings-sandbox"] .st-control input[type="range"]::-webkit-slider-thumb {
  background: linear-gradient(180deg, #1a1a1a, #0a0a0a) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.85), 0 2px 4px rgba(255,255,255,0.15), 0 4px 8px rgba(0,0,0,0.40) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-moz-range-thumb,
[data-theme="dark"] [data-scope="settings-sandbox"] .st-control input[type="range"]::-moz-range-thumb {
  background: linear-gradient(180deg, #1a1a1a, #0a0a0a) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.85), 0 2px 4px rgba(255,255,255,0.15), 0 4px 8px rgba(0,0,0,0.40) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-scope="settings-sandbox"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-scope="settings-view"] .st-control input[type="range"]:hover::-moz-range-thumb,
[data-scope="settings-sandbox"] .st-control input[type="range"]:hover::-moz-range-thumb {
  transform: scale(1.12);
  box-shadow: 0 0 0 1px rgba(255,255,255,0.95), 0 4px 8px rgba(0,0,0,0.25), 0 6px 12px rgba(0,0,0,0.15), 0 0 0 4px rgba(var(--st-primary),0.15) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-theme="dark"] [data-scope="settings-sandbox"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]:hover::-moz-range-thumb,
[data-theme="dark"] [data-scope="settings-sandbox"] .st-control input[type="range"]:hover::-moz-range-thumb {
  transform: scale(1.12);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.90), 0 4px 8px rgba(255,255,255,0.20), 0 6px 12px rgba(0,0,0,0.50), 0 0 0 4px rgba(var(--st-accent),0.20) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]:active::-webkit-slider-thumb,
[data-scope="settings-sandbox"] .st-control input[type="range"]:active::-webkit-slider-thumb,
[data-scope="settings-view"] .st-control input[type="range"]:active::-moz-range-thumb,
[data-scope="settings-sandbox"] .st-control input[type="range"]:active::-moz-range-thumb {
  transform: scale(1.05);
}
</style>

<style scoped>
/* 复用 AppearancePanel 的视觉语言（样式类同名，方便一致性） */
.st-tab-panel h3 { margin: 0 0 6px; font-weight: 700; }
.st-tab-panel .muted { color: rgba(var(--st-color-text), 0.75); margin: 0; }

.st-control {
  display: grid; grid-template-columns: 1fr; gap: 8px; margin: 12px 0 16px;
  background: rgba(var(--st-surface-2), 0.5);
  border: 1px solid rgba(var(--st-border), 0.6);
  border-radius: 6px; padding: 10px;
}
.st-control-label {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 13px; color: rgba(var(--st-color-text), 0.9); width: 100%;
}
.label-text { flex: 0 0 auto; }
.value-group { display: flex; align-items: center; gap: 4px; margin-left: auto; }
.st-number-input {
  width: 50px; padding: 2px 4px;
  border: 1px solid rgba(var(--st-border), 0.9); border-radius: 4px;
  background: rgb(var(--st-surface)); color: rgb(var(--st-color-text));
  text-align: right; font-size: 12px;
}
select.st-number-input {
  width: 120px; text-align: center; text-align-last: center; -moz-text-align-last: center;
}
.st-number-input:focus-visible { outline: 2px solid rgba(var(--st-primary), 0.6); outline-offset: 2px; }
.unit { opacity: .7; font-size: 12px; }

.st-control-hint {
  margin-top: 4px; padding: 6px 8px;
  background: rgba(var(--st-surface-2), 0.5);
  border-radius: 4px; border: 1px solid rgba(var(--st-border), 0.4);
}
</style>