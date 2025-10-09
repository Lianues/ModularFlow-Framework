<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
const props = defineProps({
  anchorLeft: { type: Number, default: 308 }, // 左侧锚定像素（默认=12+280+16）
  width: { type: Number, default: 560 },      // 面板宽度
  zIndex: { type: Number, default: 59 },      // 与 Sidebar 同层（> 背景模糊 58）
  // 统一重命名：外观（原"主题/应用设置"合并）
  title: { type: String, default: '外观 Appearance' },
})
const emit = defineEmits(['close'])

const tabs = [
  { key: 'home', label: '主页', icon: 'home' },
  { key: 'threaded', label: '楼层对话', icon: 'message-square' },
  { key: 'sandbox', label: '全屏沙盒', icon: 'monitor' },
  { key: 'backgrounds', label: '背景图片', icon: 'image' },
  { key: 'theme', label: '主题', icon: 'palette' },
]
const active = ref('threaded')

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

/* --- Sandbox layout controls --- */
const sandboxMaxWidth = ref(1100)      // 舞台最大宽度(px)
const sandboxMaxWidthLimit = ref(1920) // 舞台最大宽度上限(px)
const sandboxPadding = ref(16)         // 舞台内边距(px)
const sandboxRadius = ref(18)          // 舞台圆角(px)
const sandboxAspectX = ref(16)         // 宽高比：分子
const sandboxAspectY = ref(9)          // 宽高比：分母

/* --- Threaded 内嵌 HTML 舞台（iframe）控制 --- */
const thAspectX = ref(16)              // 宽高比：分子
const thAspectY = ref(9)               // 宽高比：分母
const thMaxWidthPct = ref(100)         // 舞台最大宽度（%），不超过消息宽度
const thPadding = ref(8)               // 舞台内边距(px)
const thRadius = ref(12)               // 舞台圆角(px)

/* 预设比例选项 */
const aspectPresets = [
  { label: '16:9', v: [16, 9] },
  { label: '4:3', v: [4, 3] },
  { label: '21:9', v: [21, 9] },
  { label: '1:1', v: [1, 1] },
]

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
// 单位为“无”的变量（如透明度等）
function setRootVarUnitless(name, value) {
  document.documentElement.style.setProperty(name, String(value))
}
// 读取浮点数（允许含 px/% 等，自动 parseFloat）
function readCssVarFloat(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name)?.trim()
  if (!v) return fallback
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : fallback
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

/* --- Sandbox handlers --- */
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
    // 如果当前宽度超过新上限，调整为新上限
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

/* --- Threaded HTML 舞台 handlers --- */
function onThreadedAspectPreset(e) {
  const raw = e.target.value
  if (!raw) return
  const [ax, ay] = raw.split(',').map(Number)
  if (ax > 0 && ay > 0) {
    thAspectX.value = ax
    thAspectY.value = ay
    setRootVarUnitless('--st-threaded-stage-aspect', `${ax} / ${ay}`)
  }
}
function onThreadedAspectNumInputX(e) {
  const v = Number(e.target.value)
  if (v > 0) {
    thAspectX.value = v
    setRootVarUnitless('--st-threaded-stage-aspect', `${thAspectX.value} / ${thAspectY.value}`)
  }
}
function onThreadedAspectNumInputY(e) {
  const v = Number(e.target.value)
  if (v > 0) {
    thAspectY.value = v
    setRootVarUnitless('--st-threaded-stage-aspect', `${thAspectX.value} / ${thAspectY.value}`)
  }
}
function onThreadedMaxWidthNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 30 && v <= 100) {
    thMaxWidthPct.value = v
    setRootVarUnitless('--st-threaded-stage-maxw', thMaxWidthPct.value)
  }
}
function onThreadedMaxWidthRangeInput(e) {
  thMaxWidthPct.value = Number(e.target.value)
  setRootVarUnitless('--st-threaded-stage-maxw', thMaxWidthPct.value)
}
function onThreadedPaddingNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 48) {
    thPadding.value = v
    setRootVar('--st-threaded-stage-padding', thPadding.value)
  }
}
function onThreadedPaddingRangeInput(e) {
  thPadding.value = Number(e.target.value)
  setRootVar('--st-threaded-stage-padding', thPadding.value)
}
function onThreadedRadiusNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 32) {
    thRadius.value = v
    setRootVar('--st-threaded-stage-radius', thRadius.value)
  }
}
function onThreadedRadiusRangeInput(e) {
  thRadius.value = Number(e.target.value)
  setRootVar('--st-threaded-stage-radius', thRadius.value)
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

  // 初始化沙盒布局变量（从 CSS 变量读取）
  const rs = getComputedStyle(document.documentElement)

  // 全屏沙盒 比例
  const aspRaw = rs.getPropertyValue('--st-sandbox-aspect')?.trim()
  if (aspRaw && aspRaw.includes('/')) {
    const parts = aspRaw.split('/')
    const ax = parseFloat(parts[0])
    const ay = parseFloat(parts[1])
    if (Number.isFinite(ax) && Number.isFinite(ay) && ax > 0 && ay > 0) {
      sandboxAspectX.value = Math.round(ax)
      sandboxAspectY.value = Math.round(ay)
    }
  }
  // 全屏沙盒 其他参数
  sandboxMaxWidth.value = readCssVarFloat('--st-sandbox-max-width', 1100)
  sandboxPadding.value = readCssVarFloat('--st-sandbox-padding', 16)
  sandboxRadius.value = readCssVarFloat('--st-sandbox-radius', 18)

  // 楼层对话内嵌 HTML 舞台（iframe）变量
  const thAspRaw = rs.getPropertyValue('--st-threaded-stage-aspect')?.trim()
  if (thAspRaw && thAspRaw.includes('/')) {
    const parts = thAspRaw.split('/')
    const ax = parseFloat(parts[0])
    const ay = parseFloat(parts[1])
    if (Number.isFinite(ax) && Number.isFinite(ay) && ax > 0 && ay > 0) {
      thAspectX.value = Math.round(ax)
      thAspectY.value = Math.round(ay)
    }
  }
  thMaxWidthPct.value = readCssVarFloat('--st-threaded-stage-maxw', 100)
  thPadding.value = readCssVarFloat('--st-threaded-stage-padding', 8)
  thRadius.value = readCssVarFloat('--st-threaded-stage-radius', 12)

  // 回写一次，确保打开面板即与 UI 同步
  setRootVarUnitless('--st-threaded-stage-aspect', `${thAspectX.value} / ${thAspectY.value}`)
  setRootVarUnitless('--st-threaded-stage-maxw', thMaxWidthPct.value)
  setRootVar('--st-threaded-stage-padding', thPadding.value)
  setRootVar('--st-threaded-stage-radius', thRadius.value)
})
onBeforeUnmount(() => {
  document.body.classList.remove('st-live-tuning')
})
onMounted(() => window.lucide?.createIcons?.())
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
          <span class="st-settings-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                 data-lucide="palette" class="lucide lucide-palette">
              <path d="M12 22a1 1 0 0 1 0-20 10 9 0 0 1 10 9 5 5 0 0 1-5 5h-2.25a1.75 1.75 0 0 0-1.4 2.8l.3.4a1.75 1.75 0 0 1-1.4 2.8z"></path>
              <circle cx="13.5" cy="6.5" r=".5" fill="currentColor"></circle>
              <circle cx="17.5" cy="10.5" r=".5" fill="currentColor"></circle>
              <circle cx="6.5" cy="12.5" r=".5" fill="currentColor"></circle>
              <circle cx="8.5" cy="7.5" r=".5" fill="currentColor"></circle>
            </svg>
          </span>
          {{ props.title }}
        </div>
        <button class="st-settings-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <nav class="st-settings-tabs" role="tablist" aria-label="外观页签">
        <button
          v-for="t in tabs"
          :key="t.key"
          type="button"
          class="st-tab"
          :class="{ active: active === t.key }"
          role="tab"
          :aria-selected="active === t.key"
          :tabindex="active === t.key ? 0 : -1"
          @click="active = t.key"
        >
          <i v-if="t.icon" :data-lucide="t.icon"></i>
          <span class="st-tab-label">{{ t.label }}</span>
        </button>
        <!-- 提示：原“应用设置”内容已合并到本外观面板 -->
      </nav>

      <CustomScrollbar class="st-settings-body">
        <div v-if="active === 'home'" class="st-tab-panel">
          <h3>主页</h3>
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

          <!-- 楼层对话：HTML 舞台（iframe）设置 -->
          <h4 class="muted" style="margin:8px 0 0;">HTML 舞台（楼层内 iframe）</h4>

          <!-- 画面宽高比 -->
          <div class="st-control" data-slider="threadedStageAspect">
            <label class="st-control-label">
              <span class="label-text">画面宽高比</span>
              <div class="value-group">
                <select class="st-number-input" @change="onThreadedAspectPreset">
                  <option disabled selected value="">预设</option>
                  <option v-for="p in aspectPresets" :key="p.label" :value="p.v.join(',')">{{ p.label }}</option>
                </select>
                <span class="unit">或 自定义</span>
              </div>
            </label>
            <div style="display:flex; gap:8px; align-items:center;">
              <input type="number" class="st-number-input" :value="thAspectX" min="1" max="100" @input="onThreadedAspectNumInputX" />
              <span>:</span>
              <input type="number" class="st-number-input" :value="thAspectY" min="1" max="100" @input="onThreadedAspectNumInputY" />
            </div>
          </div>

          <!-- 舞台最大宽度（%） -->
          <div class="st-control" data-slider="threadedStageMaxWidthPct">
            <label class="st-control-label">
              <span class="label-text">舞台最大宽度</span>
              <div class="value-group">
                <input type="number" class="st-number-input" :value="thMaxWidthPct" min="30" max="100" @input="onThreadedMaxWidthNumberInput" />
                <span class="unit">%</span>
              </div>
            </label>
            <input type="range" min="30" max="100" step="1" :value="thMaxWidthPct" @pointerdown="onTuningStart('threadedStageMaxWidthPct')" @input="onThreadedMaxWidthRangeInput" />
            <div class="st-control-hint">
              <span class="muted" style="font-size:12px;">以消息内容宽度为上限，设置相对百分比宽度</span>
            </div>
          </div>

          <!-- 内边距 -->
          <div class="st-control" data-slider="threadedStagePadding">
            <label class="st-control-label">
              <span class="label-text">舞台内边距</span>
              <div class="value-group">
                <input type="number" class="st-number-input" :value="thPadding" min="0" max="48" @input="onThreadedPaddingNumberInput" />
                <span class="unit">px</span>
              </div>
            </label>
            <input type="range" min="0" max="48" step="1" :value="thPadding" @pointerdown="onTuningStart('threadedStagePadding')" @input="onThreadedPaddingRangeInput" />
          </div>

          <!-- 圆角 -->
          <div class="st-control" data-slider="threadedStageRadius">
            <label class="st-control-label">
              <span class="label-text">舞台圆角</span>
              <div class="value-group">
                <input type="number" class="st-number-input" :value="thRadius" min="0" max="32" @input="onThreadedRadiusNumberInput" />
                <span class="unit">px</span>
              </div>
            </label>
            <input type="range" min="0" max="32" step="1" :value="thRadius" @pointerdown="onTuningStart('threadedStageRadius')" @input="onThreadedRadiusRangeInput" />
          </div>

          <p class="muted">拖拽滑条时，页面会自动变透明，仅保留本面板不透明，便于实时查看调整效果。</p>
        </div>

        <div v-else-if="active === 'sandbox'" class="st-tab-panel">
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

          <p class="muted">提示：上述设定实时作用于页面上的"全局沙盒"舞台，并以 CSS 变量方式保存，便于主题或脚本统一接管。</p>
        </div>

        <div v-else-if="active === 'backgrounds'" class="st-tab-panel">
          <h3>背景图片</h3>
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

        <div v-else-if="active === 'theme'" class="st-tab-panel">
          <h3>主题管理</h3>
          <p class="muted">此为主题配置页面（占位），后续可用于主题切换、自定义主题包导入与预览。</p>

          <div class="theme-placeholder">
            <div class="theme-placeholder-icon">🎨</div>
            <div class="theme-placeholder-title">主题系统</div>
            <div class="theme-placeholder-desc">主题包导入、切换与预览功能即将推出</div>
          </div>
        </div>

        <div v-else class="st-tab-panel">
          <h3>未知页签</h3>
          <p class="muted">占位内容</p>
        </div>
      </CustomScrollbar>
    </div>
  </transition>
</template>

<style>
/* Global range slider styles for AppearancePanel (non-scoped for pseudo-element support) */
/* Scope limited to [data-scope="settings-view"] */

/* Base range input reset */
[data-scope="settings-view"] .st-control input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  width: 100%;
}

/* LIGHT THEME: Premium black rail with gradient depth */
[data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-runnable-track {
  height: 8px !important;
  border-radius: 9999px !important;
  background: linear-gradient(180deg, rgba(0,0,0,0.68), rgba(0,0,0,0.82)) !important;
  border: 1px solid rgba(0,0,0,0.92) !important;
  box-shadow:
    inset 0 1px 2px rgba(0,0,0,0.25),
    0 1px 0 rgba(255,255,255,0.15) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]::-moz-range-track {
  height: 8px !important;
  border-radius: 9999px !important;
  background: linear-gradient(180deg, rgba(0,0,0,0.68), rgba(0,0,0,0.82)) !important;
  border: 1px solid rgba(0,0,0,0.92) !important;
  box-shadow:
    inset 0 1px 2px rgba(0,0,0,0.25),
    0 1px 0 rgba(255,255,255,0.15) !important;
}

/* LIGHT THEME: Premium white thumb with refined shadow */
[data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 9999px;
  background: linear-gradient(180deg, #ffffff, #f8f9fa) !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.9),
    0 2px 4px rgba(0,0,0,0.20),
    0 4px 8px rgba(0,0,0,0.10) !important;
  margin-top: -6px;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1),
              box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
[data-scope="settings-view"] .st-control input[type="range"]::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 9999px;
  background: linear-gradient(180deg, #ffffff, #f8f9fa) !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.9),
    0 2px 4px rgba(0,0,0,0.20),
    0 4px 8px rgba(0,0,0,0.10) !important;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1),
              box-shadow .2s cubic-bezier(.22,.61,.36,1);
}

/* DARK THEME: Premium white rail with gradient depth */
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-runnable-track {
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.85)) !important;
  border: 1px solid rgba(255,255,255,0.95) !important;
  box-shadow:
    inset 0 1px 2px rgba(255,255,255,0.20),
    0 1px 0 rgba(0,0,0,0.15) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-moz-range-track {
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.85)) !important;
  border: 1px solid rgba(255,255,255,0.95) !important;
  box-shadow:
    inset 0 1px 2px rgba(255,255,255,0.20),
    0 1px 0 rgba(0,0,0,0.15) !important;
}

/* DARK THEME: Premium black thumb with refined shadow */
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-thumb {
  background: linear-gradient(180deg, #1a1a1a, #0a0a0a) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  box-shadow:
    0 0 0 1px rgba(0,0,0,0.85),
    0 2px 4px rgba(255,255,255,0.15),
    0 4px 8px rgba(0,0,0,0.40) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-moz-range-thumb {
  background: linear-gradient(180deg, #1a1a1a, #0a0a0a) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  box-shadow:
    0 0 0 1px rgba(0,0,0,0.85),
    0 2px 4px rgba(255,255,255,0.15),
    0 4px 8px rgba(0,0,0,0.40) !important;
}

/* Hover state: Light theme - elevate with enhanced glow */
[data-scope="settings-view"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-scope="settings-view"] .st-control input[type="range"]:hover::-moz-range-thumb {
  transform: scale(1.12);
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.95),
    0 4px 8px rgba(0,0,0,0.25),
    0 6px 12px rgba(0,0,0,0.15),
    0 0 0 4px rgba(var(--st-primary),0.15) !important;
}

/* Hover state: Dark theme - elevate with enhanced glow */
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]:hover::-moz-range-thumb {
  transform: scale(1.12);
  box-shadow:
    0 0 0 1px rgba(0,0,0,0.90),
    0 4px 8px rgba(255,255,255,0.20),
    0 6px 12px rgba(0,0,0,0.50),
    0 0 0 4px rgba(var(--st-accent),0.20) !important;
}

/* Active/dragging state */
[data-scope="settings-view"] .st-control input[type="range"]:active::-webkit-slider-thumb,
[data-scope="settings-view"] .st-control input[type="range"]:active::-moz-range-thumb {
  transform: scale(1.05);
}
</style>

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
.st-settings-icon i,
.st-settings-icon svg { width: 24px; height: 24px; display: inline-block; }
.st-settings-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), background .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
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
  border-top-left-radius: var(--st-radius-lg);
  border-top-right-radius: var(--st-radius-lg);
  box-shadow: inset 0 -1px 0 rgba(0,0,0,0.02);
}
.st-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 9999px;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  transition: background .2s cubic-bezier(.22,.61,.36,1),
              border-color .2s cubic-bezier(.22,.61,.36,1),
              transform .2s cubic-bezier(.22,.61,.36,1),
              box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
.st-tab i { width: 14px; height: 14px; display: inline-block; }
.st-tab-label { font-weight: 600; letter-spacing: 0.2px; }
.st-tab:focus-visible {
  outline: 2px solid rgba(var(--st-primary), 0.6);
  outline-offset: 2px;
}
.st-tab:hover { transform: translateY(-1px); }
.st-tab.active {
  background: rgba(var(--st-primary), 0.14);
  border-color: rgba(var(--st-primary), 0.45);
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
  transform: translateY(-1px);
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
  gap: 8px;
  margin: 12px 0 16px;
  background: rgba(var(--st-surface-2), 0.5);
  border: 1px solid rgba(var(--st-border), 0.6);
  border-radius: 6px;
  padding: 10px;
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
/* 预设下拉宽度与文字居中（同时作用于“楼层对话/全屏沙盒”的比例预设） */
select.st-number-input {
  width: 120px;
  text-align: center;
  text-align-last: center;
  -moz-text-align-last: center;
}
.st-number-input:focus-visible {
  outline: 2px solid rgba(var(--st-primary), 0.6);
  outline-offset: 2px;
}
.unit {
  opacity: .7;
  font-size: 12px;
}

.st-control-hint {
  margin-top: 4px;
  padding: 6px 8px;
  background: rgba(var(--st-surface-2), 0.5);
  border-radius: 4px;
  border: 1px solid rgba(var(--st-border), 0.4);
}

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
  border-radius: var(--st-radius-md);
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
  border-radius: 4px;
  padding: 6px 10px;
  cursor: pointer;
  transition: background .2s cubic-bezier(.22,.61,.36,1),
              border-color .2s cubic-bezier(.22,.61,.36,1),
              transform .2s cubic-bezier(.22,.61,.36,1),
              box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
.bg-upload:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}
.bg-upload:focus-within {
  outline: 2px solid rgba(var(--st-primary), 0.6);
  outline-offset: 2px;
}
.bg-upload input[type="file"] {
  display: none;
}

/* Theme placeholder */
.theme-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  text-align: center;
  border: 1px dashed rgba(var(--st-border), 0.7);
  border-radius: var(--st-radius-md);
  background: rgba(var(--st-surface-2), 0.4);
}
.theme-placeholder-icon {
  font-size: 64px;
  opacity: 0.7;
}
.theme-placeholder-title {
  font-size: 20px;
  font-weight: 600;
  color: rgb(var(--st-color-text));
}
.theme-placeholder-desc {
  font-size: 14px;
  color: rgba(var(--st-color-text), 0.65);
}
</style>