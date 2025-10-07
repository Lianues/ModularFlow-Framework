<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
const props = defineProps({
  anchorLeft: { type: Number, default: 348 }, // 左侧锚定像素（默认=12+320+16）
  width: { type: Number, default: 520 },      // 面板宽度
  zIndex: { type: Number, default: 59 },      // 与 Sidebar 同层（> 背景模糊 58）
  // 统一重命名：外观（原“主题/应用设置”合并）
  title: { type: String, default: '外观 Appearance' },
})
const emit = defineEmits(['close'])

const tabs = [
  { key: 'home', label: '主页设定' },
  { key: 'threaded', label: '楼层对话设定' },
  { key: 'backgrounds', label: '背景图片设定' },
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

// --- Threaded chat live tuning ---
const contentFontSize = ref(18) // 正文文字大小
const nameFontSize = ref(16) // 角色名称文字大小
const badgeFontSize = ref(11) // 角色徽章文字大小
const floorFontSize = ref(16) // 楼层号文字大小
const avatarSize = ref(56) // 角色头像大小
const chatWidth = ref(80) // 百分比值，默认80%
const inputHeight = ref(100) // 输入框高度，默认100px
const tuning = ref(false)
const activeTuningSlider = ref(null)

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

/* 背景图片覆盖（使用 CSS 变量，持久化到 localStorage） */
const BG_KEYS = {
  start: '--st-bg-start',
  threaded: '--st-bg-threaded',
  sandbox: '--st-bg-sandbox',
}
const LS_KEYS = {
  start: 'st.bg.start',
  threaded: 'st.bg.threaded',
  sandbox: 'st.bg.sandbox',
}

function applyBg(type, url) {
  if (!BG_KEYS[type]) return
  // 将 url 字符串封装为 CSS url(...)
  const css = `url("${url}")`
  document.documentElement.style.setProperty(BG_KEYS[type], css)
  try { localStorage.setItem(LS_KEYS[type], url) } catch (_) {}
}

function resetBg(type) {
  if (!BG_KEYS[type]) return
  document.documentElement.style.removeProperty(BG_KEYS[type])
  try { localStorage.removeItem(LS_KEYS[type]) } catch (_) {}
}

function onFileChange(type, e) {
  const file = e.target?.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    const dataUrl = reader.result
    if (typeof dataUrl === 'string') {
      applyBg(type, dataUrl)
    }
  }
  reader.readAsDataURL(file)
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

// 外观与布局（原应用设置项已迁移至此）
// 正文文字
function onContentFontSizeInput(e) {
  contentFontSize.value = Number(e.target.value)
  setRootVar('--st-content-font-size', contentFontSize.value)
}
function onContentFontSizeNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 12 && val <= 32) {
    contentFontSize.value = val
    setRootVar('--st-content-font-size', contentFontSize.value)
  }
}

// 角色名称
function onNameFontSizeInput(e) {
  nameFontSize.value = Number(e.target.value)
  setRootVar('--st-name-font-size', nameFontSize.value)
}
function onNameFontSizeNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 10 && val <= 24) {
    nameFontSize.value = val
    setRootVar('--st-name-font-size', nameFontSize.value)
  }
}

// 角色徽章
function onBadgeFontSizeInput(e) {
  badgeFontSize.value = Number(e.target.value)
  setRootVar('--st-badge-font-size', badgeFontSize.value)
}
function onBadgeFontSizeNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 8 && val <= 16) {
    badgeFontSize.value = val
    setRootVar('--st-badge-font-size', badgeFontSize.value)
  }
}

// 楼层号
function onFloorFontSizeInput(e) {
  floorFontSize.value = Number(e.target.value)
  setRootVar('--st-floor-font-size', floorFontSize.value)
}
function onFloorFontSizeNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 10 && val <= 24) {
    floorFontSize.value = val
    setRootVar('--st-floor-font-size', floorFontSize.value)
  }
}

// 头像大小
function onAvatarSizeInput(e) {
  avatarSize.value = Number(e.target.value)
  setRootVar('--st-avatar-size', avatarSize.value)
}
function onAvatarSizeNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 32 && val <= 80) {
    avatarSize.value = val
    setRootVar('--st-avatar-size', avatarSize.value)
  }
}

// 宽度
function onWidthInput(e) {
  chatWidth.value = Number(e.target.value)
  setRootVar('--st-chat-width', chatWidth.value)
}
function onWidthNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 30 && val <= 100) {
    chatWidth.value = val
    setRootVar('--st-chat-width', chatWidth.value)
  }
}

// 输入框高度
function onInputHeightInput(e) {
  inputHeight.value = Number(e.target.value)
  setRootVar('--st-input-height', inputHeight.value)
}
function onInputHeightNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 60 && val <= 300) {
    inputHeight.value = val
    setRootVar('--st-input-height', inputHeight.value)
  }
}
onMounted(() => {
  contentFontSize.value = readCssVar('--st-content-font-size', 18)
  nameFontSize.value = readCssVar('--st-name-font-size', 16)
  badgeFontSize.value = readCssVar('--st-badge-font-size', 11)
  floorFontSize.value = readCssVar('--st-floor-font-size', 16)
  avatarSize.value = readCssVar('--st-avatar-size', 56)
  // 读取宽度百分比值（去掉%符号）
  const widthVar = getComputedStyle(document.documentElement).getPropertyValue('--st-chat-width')?.trim()
  chatWidth.value = widthVar ? parseInt(widthVar, 10) : 80
  inputHeight.value = readCssVar('--st-input-height', 100)
  // 应用当前值到根变量（确保首次打开即与 UI 同步）
  setRootVar('--st-content-font-size', contentFontSize.value)
  setRootVar('--st-name-font-size', nameFontSize.value)
  setRootVar('--st-badge-font-size', badgeFontSize.value)
  setRootVar('--st-floor-font-size', floorFontSize.value)
  setRootVar('--st-avatar-size', avatarSize.value)
  setRootVar('--st-chat-width', chatWidth.value)
  setRootVar('--st-input-height', inputHeight.value)

  // 恢复背景图片自定义（若本地已保存）
  try {
    const s = localStorage.getItem(LS_KEYS.start)
    const t = localStorage.getItem(LS_KEYS.threaded)
    const z = localStorage.getItem(LS_KEYS.sandbox)
    if (s) applyBg('start', s)
    if (t) applyBg('threaded', t)
    if (z) applyBg('sandbox', z)
  } catch (_) {}
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
        <!-- 提示：原“应用设置”内容已合并到本外观面板 -->
      </nav>

      <CustomScrollbar class="st-settings-body">
        <div v-if="active === 'home'" class="st-tab-panel">
          <h3>主页设定</h3>
          <p class="muted">此为占位页面，用于配置应用主页相关选项。</p>
        </div>

        <div v-else-if="active === 'threaded'" class="st-tab-panel">
          <h3>楼层对话外观</h3>

          <div class="st-control" data-slider="contentFontSize">
            <label class="st-control-label">
              <span class="label-text">正文文字大小</span>
              <div class="value-group">
                <input
                  type="number"
                  class="st-number-input"
                  :value="contentFontSize"
                  min="12"
                  max="32"
                  @input="onContentFontSizeNumberInput"
                />
                <span class="unit">px</span>
              </div>
            </label>
            <input
              type="range"
              min="12"
              max="32"
              step="1"
              :value="contentFontSize"
              @pointerdown="onTuningStart('contentFontSize')"
              @input="onContentFontSizeInput"
            />
          </div>

          <div class="st-control" data-slider="nameFontSize">
            <label class="st-control-label">
              <span class="label-text">角色名称文字大小</span>
              <div class="value-group">
                <input
                  type="number"
                  class="st-number-input"
                  :value="nameFontSize"
                  min="10"
                  max="24"
                  @input="onNameFontSizeNumberInput"
                />
                <span class="unit">px</span>
              </div>
            </label>
            <input
              type="range"
              min="10"
              max="24"
              step="1"
              :value="nameFontSize"
              @pointerdown="onTuningStart('nameFontSize')"
              @input="onNameFontSizeInput"
            />
          </div>

          <div class="st-control" data-slider="badgeFontSize">
            <label class="st-control-label">
              <span class="label-text">角色徽章文字大小</span>
              <div class="value-group">
                <input
                  type="number"
                  class="st-number-input"
                  :value="badgeFontSize"
                  min="8"
                  max="16"
                  @input="onBadgeFontSizeNumberInput"
                />
                <span class="unit">px</span>
              </div>
            </label>
            <input
              type="range"
              min="8"
              max="16"
              step="1"
              :value="badgeFontSize"
              @pointerdown="onTuningStart('badgeFontSize')"
              @input="onBadgeFontSizeInput"
            />
          </div>

          <div class="st-control" data-slider="floorFontSize">
            <label class="st-control-label">
              <span class="label-text">楼层号文字大小</span>
              <div class="value-group">
                <input
                  type="number"
                  class="st-number-input"
                  :value="floorFontSize"
                  min="10"
                  max="24"
                  @input="onFloorFontSizeNumberInput"
                />
                <span class="unit">px</span>
              </div>
            </label>
            <input
              type="range"
              min="10"
              max="24"
              step="1"
              :value="floorFontSize"
              @pointerdown="onTuningStart('floorFontSize')"
              @input="onFloorFontSizeInput"
            />
          </div>

          <div class="st-control" data-slider="avatarSize">
            <label class="st-control-label">
              <span class="label-text">角色头像大小</span>
              <div class="value-group">
                <input
                  type="number"
                  class="st-number-input"
                  :value="avatarSize"
                  min="32"
                  max="80"
                  @input="onAvatarSizeNumberInput"
                />
                <span class="unit">px</span>
              </div>
            </label>
            <input
              type="range"
              min="32"
              max="80"
              step="2"
              :value="avatarSize"
              @pointerdown="onTuningStart('avatarSize')"
              @input="onAvatarSizeInput"
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

          <div class="st-control" data-slider="inputHeight">
            <label class="st-control-label">
              <span class="label-text">底部输入框高度</span>
              <div class="value-group">
                <input
                  type="number"
                  class="st-number-input"
                  :value="inputHeight"
                  min="60"
                  max="300"
                  @input="onInputHeightNumberInput"
                />
                <span class="unit">px</span>
              </div>
            </label>
            <input
              type="range"
              min="60"
              max="300"
              step="10"
              :value="inputHeight"
              @pointerdown="onTuningStart('inputHeight')"
              @input="onInputHeightInput"
            />
          </div>

          <p class="muted">拖拽滑条时，页面会自动变透明，仅保留本面板不透明，便于实时查看调整效果。</p>
        </div>

        <div v-else-if="active === 'backgrounds'" class="st-tab-panel">
          <h3>背景图片设定</h3>
          <p class="muted">为开始页面、楼层对话页面、沙盒页面设置背景图。可覆盖默认图片并即时预览。</p>

          <div class="bg-grid">
            <div class="bg-card">
              <div class="bg-title">开始页面</div>
              <div class="bg-preview bg-start" />
              <div class="bg-actions">
                <label class="bg-upload">
                  <input type="file" accept="image/*" @change="onFileChange('start', $event)" />
                  选择图片
                </label>
                <button class="st-settings-close" type="button" @click="resetBg('start')">重置默认</button>
              </div>
            </div>

            <div class="bg-card">
              <div class="bg-title">楼层对话页面</div>
              <div class="bg-preview bg-threaded" />
              <div class="bg-actions">
                <label class="bg-upload">
                  <input type="file" accept="image/*" @change="onFileChange('threaded', $event)" />
                  选择图片
                </label>
                <button class="st-settings-close" type="button" @click="resetBg('threaded')">重置默认</button>
              </div>
            </div>

            <div class="bg-card">
              <div class="bg-title">沙盒页面</div>
              <div class="bg-preview bg-sandbox" />
              <div class="bg-actions">
                <label class="bg-upload">
                  <input type="file" accept="image/*" @change="onFileChange('sandbox', $event)" />
                  选择图片
                </label>
                <button class="st-settings-close" type="button" @click="resetBg('sandbox')">重置默认</button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="st-tab-panel">
          <h3>全屏沙盒外观</h3>
          <p class="muted">此为占位页面，用于配置"全屏沙盒"的安全与渲染选项。</p>
        </div>
      </CustomScrollbar>
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
  overflow: hidden;
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

/* 背景设置预览 */
.bg-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
.bg-card {
  border: 1px solid rgb(var(--st-border));
  border-radius: var(--st-radius-md);
  background: rgb(var(--st-surface));
  padding: 10px;
}
.bg-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: rgb(var(--st-color-text));
}
.bg-preview {
  width: 100%;
  height: 120px;
  border-radius: 10px;
  border: 1px solid rgba(var(--st-border), 0.8);
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  box-shadow: var(--st-shadow-sm);
}
.bg-preview.bg-start { background-image: var(--st-bg-start); }
.bg-preview.bg-threaded { background-image: var(--st-bg-threaded); }
.bg-preview.bg-sandbox { background-image: var(--st-bg-sandbox); }

.bg-actions {
  display: flex; align-items: center; gap: 8px; margin-top: 8px;
}
.bg-upload {
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
}
.bg-upload input[type="file"] {
  display: none;
}
</style>