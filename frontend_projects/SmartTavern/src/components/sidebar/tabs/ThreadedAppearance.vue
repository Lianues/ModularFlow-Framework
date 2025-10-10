<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

/**
 * 楼层对话外观配置（拆分自 AppearancePanel）
 * - 直接写入/读取 CSS 变量
 * - 使用本地持久化（仅本页签）：st.appearance.threaded.v1
 * - 与父容器视觉语言统一（复用 .st-control 等样式）
 */

/* helpers */
function readCssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name)?.trim()
  if (!v) return fallback
  const n = parseInt(v, 10)
  return Number.isFinite(n) ? n : fallback
}
function readCssVarFloat(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name)?.trim()
  if (!v) return fallback
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : fallback
}
function setRootVar(name, value) {
  const suffix = name === '--st-chat-width' ? '%' : 'px'
  document.documentElement.style.setProperty(name, typeof value === 'number' ? value + suffix : String(value))
}
function setRootVarUnitless(name, value) {
  document.documentElement.style.setProperty(name, String(value))
}

/* state */
const contentFontSize = ref(18)
const nameFontSize = ref(16)
const badgeFontSize = ref(11)
const floorFontSize = ref(16)
const avatarSize = ref(56)
const chatWidth = ref(80)
const inputHeight = ref(100)

const contentLineHeight = ref(1.75)
const messageGap = ref(12)
const cardRadius = ref(NaN) // NaN 表示未覆盖（沿用默认）
const stripeWidth = ref(8)

/* 背景与容器透明度（%） */
const threadedBgOpacityPct = ref(12)
const threadedMsgBgOpacityPct = ref(82)
const threadedListBgOpacityPct = ref(62)
const threadedInputBgOpacityPct = ref(80)

/* 楼层内 HTML 舞台（iframe） */
const thAspectX = ref(16)
const thAspectY = ref(9)
const thMaxWidthPct = ref(100)
const thPadding = ref(8)
const thRadius = ref(12)

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

/* handlers: 字号/尺寸 */
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

/* handlers: 常用外观 */
function onContentLineHeightNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 1.2 && val <= 2.0) {
    contentLineHeight.value = val
    setRootVarUnitless('--st-content-line-height', String(val))
  }
}
function onContentLineHeightRangeInput(e) {
  contentLineHeight.value = Number(e.target.value)
  setRootVarUnitless('--st-content-line-height', String(contentLineHeight.value))
}
function onMessageGapNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 6 && val <= 24) {
    messageGap.value = val
    setRootVar('--st-message-gap', messageGap.value)
  }
}
function onMessageGapRangeInput(e) {
  messageGap.value = Number(e.target.value)
  setRootVar('--st-message-gap', messageGap.value)
}
function onCardRadiusNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 0 && val <= 24) {
    cardRadius.value = val
    setRootVar('--st-card-radius', cardRadius.value)
  }
}
function onCardRadiusRangeInput(e) {
  cardRadius.value = Number(e.target.value)
  setRootVar('--st-card-radius', cardRadius.value)
}
function onStripeWidthNumberInput(e) {
  const val = Number(e.target.value)
  if (val >= 0 && val <= 12) {
    stripeWidth.value = val
    setRootVar('--st-stripe-width', stripeWidth.value)
  }
}
function onStripeWidthRangeInput(e) {
  stripeWidth.value = Number(e.target.value)
  setRootVar('--st-stripe-width', stripeWidth.value)
}

/* handlers: 透明度（%→小数写 CSS） */
function onThreadedBgOpacityNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 100) {
    threadedBgOpacityPct.value = v
    setRootVarUnitless('--st-threaded-bg-opacity', String(v / 100))
  }
}
function onThreadedBgOpacityRangeInput(e) {
  threadedBgOpacityPct.value = Number(e.target.value)
  setRootVarUnitless('--st-threaded-bg-opacity', String(threadedBgOpacityPct.value / 100))
}
function onThreadedMsgBgOpacityNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 100) {
    threadedMsgBgOpacityPct.value = v
    setRootVarUnitless('--st-threaded-msg-bg-opacity', String(v / 100))
  }
}
function onThreadedMsgBgOpacityRangeInput(e) {
  threadedMsgBgOpacityPct.value = Number(e.target.value)
  setRootVarUnitless('--st-threaded-msg-bg-opacity', String(threadedMsgBgOpacityPct.value / 100))
}
function onThreadedListBgOpacityNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 100) {
    threadedListBgOpacityPct.value = v
    setRootVarUnitless('--st-threaded-list-bg-opacity', String(v / 100))
  }
}
function onThreadedListBgOpacityRangeInput(e) {
  threadedListBgOpacityPct.value = Number(e.target.value)
  setRootVarUnitless('--st-threaded-list-bg-opacity', String(threadedListBgOpacityPct.value / 100))
}
function onThreadedInputBgOpacityNumberInput(e) {
  const v = Number(e.target.value)
  if (v >= 0 && v <= 100) {
    threadedInputBgOpacityPct.value = v
    setRootVarUnitless('--st-threaded-input-bg-opacity', String(v / 100))
  }
}
function onThreadedInputBgOpacityRangeInput(e) {
  threadedInputBgOpacityPct.value = Number(e.target.value)
  setRootVarUnitless('--st-threaded-input-bg-opacity', String(threadedInputBgOpacityPct.value / 100))
}

/* handlers: 楼层内 HTML 舞台 */
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

/* persistence (tab-scoped) */
const STORE_KEY = 'st.appearance.threaded.v1'
let __lastSaved = ''
let __saveTimer = null

function getSnapshot() {
  return {
    contentFontSize: Number(contentFontSize.value),
    nameFontSize: Number(nameFontSize.value),
    badgeFontSize: Number(badgeFontSize.value),
    floorFontSize: Number(floorFontSize.value),
    avatarSize: Number(avatarSize.value),
    chatWidth: Number(chatWidth.value),
    inputHeight: Number(inputHeight.value),
    contentLineHeight: Number(contentLineHeight.value),
    messageGap: Number(messageGap.value),
    cardRadius: Number.isFinite(cardRadius.value) ? Number(cardRadius.value) : null,
    stripeWidth: Number(stripeWidth.value),
    threadedBgOpacityPct: Number(threadedBgOpacityPct.value),
    threadedMsgBgOpacityPct: Number(threadedMsgBgOpacityPct.value),
    threadedListBgOpacityPct: Number(threadedListBgOpacityPct.value),
    threadedInputBgOpacityPct: Number(threadedInputBgOpacityPct.value),
    thAspectX: Number(thAspectX.value),
    thAspectY: Number(thAspectY.value),
    thMaxWidthPct: Number(thMaxWidthPct.value),
    thPadding: Number(thPadding.value),
    thRadius: Number(thRadius.value),
  }
}
function applyState(s) {
  if (!s || typeof s !== 'object') return
  const num = (v, f) => (typeof v === 'number' ? v : f)

  contentFontSize.value = num(s.contentFontSize, 18); setRootVar('--st-content-font-size', contentFontSize.value)
  nameFontSize.value = num(s.nameFontSize, 16); setRootVar('--st-name-font-size', nameFontSize.value)
  badgeFontSize.value = num(s.badgeFontSize, 11); setRootVar('--st-badge-font-size', badgeFontSize.value)
  floorFontSize.value = num(s.floorFontSize, 16); setRootVar('--st-floor-font-size', floorFontSize.value)
  avatarSize.value = num(s.avatarSize, 56); setRootVar('--st-avatar-size', avatarSize.value)
  chatWidth.value = num(s.chatWidth, 80); setRootVar('--st-chat-width', chatWidth.value)
  inputHeight.value = num(s.inputHeight, 100); setRootVar('--st-input-height', inputHeight.value)

  contentLineHeight.value = num(s.contentLineHeight, 1.75); setRootVarUnitless('--st-content-line-height', String(contentLineHeight.value))
  messageGap.value = num(s.messageGap, 12); setRootVar('--st-message-gap', messageGap.value)
  if (s.cardRadius === null) {
    cardRadius.value = NaN
    document.documentElement.style.removeProperty('--st-card-radius')
  } else {
    cardRadius.value = num(s.cardRadius, NaN)
    if (Number.isFinite(cardRadius.value)) setRootVar('--st-card-radius', cardRadius.value)
  }
  stripeWidth.value = num(s.stripeWidth, 8); setRootVar('--st-stripe-width', stripeWidth.value)

  threadedBgOpacityPct.value = num(s.threadedBgOpacityPct, 12); setRootVarUnitless('--st-threaded-bg-opacity', String(threadedBgOpacityPct.value / 100))
  threadedMsgBgOpacityPct.value = num(s.threadedMsgBgOpacityPct, 82); setRootVarUnitless('--st-threaded-msg-bg-opacity', String(threadedMsgBgOpacityPct.value / 100))
  threadedListBgOpacityPct.value = num(s.threadedListBgOpacityPct, 62); setRootVarUnitless('--st-threaded-list-bg-opacity', String(threadedListBgOpacityPct.value / 100))
  threadedInputBgOpacityPct.value = num(s.threadedInputBgOpacityPct, 80); setRootVarUnitless('--st-threaded-input-bg-opacity', String(threadedInputBgOpacityPct.value / 100))

  thAspectX.value = num(s.thAspectX, 16)
  thAspectY.value = num(s.thAspectY, 9)
  setRootVarUnitless('--st-threaded-stage-aspect', `${thAspectX.value} / ${thAspectY.value}`)
  thMaxWidthPct.value = num(s.thMaxWidthPct, 100); setRootVarUnitless('--st-threaded-stage-maxw', thMaxWidthPct.value)
  thPadding.value = num(s.thPadding, 8); setRootVar('--st-threaded-stage-padding', thPadding.value)
  thRadius.value = num(s.thRadius, 12); setRootVar('--st-threaded-stage-radius', thRadius.value)
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
  /* init from CSS vars */
  contentFontSize.value = readCssVar('--st-content-font-size', 18)
  nameFontSize.value = readCssVar('--st-name-font-size', 16)
  badgeFontSize.value = readCssVar('--st-badge-font-size', 11)
  floorFontSize.value = readCssVar('--st-floor-font-size', 16)
  avatarSize.value = readCssVar('--st-avatar-size', 56)
  {
    const widthVar = getComputedStyle(document.documentElement).getPropertyValue('--st-chat-width')?.trim()
    chatWidth.value = widthVar ? parseInt(widthVar, 10) : 80
  }
  inputHeight.value = readCssVar('--st-input-height', 100)

  contentLineHeight.value = readCssVarFloat('--st-content-line-height', 1.75)
  messageGap.value = readCssVarFloat('--st-message-gap', 12)
  {
    const cr = readCssVarFloat('--st-card-radius', NaN)
    cardRadius.value = Number.isFinite(cr) ? cr : NaN
  }
  stripeWidth.value = readCssVarFloat('--st-stripe-width', 8)

  threadedBgOpacityPct.value = Math.round(readCssVarFloat('--st-threaded-bg-opacity', 0.12) * 100)
  threadedMsgBgOpacityPct.value = Math.round(readCssVarFloat('--st-threaded-msg-bg-opacity', 0.82) * 100)
  threadedListBgOpacityPct.value = Math.round(readCssVarFloat('--st-threaded-list-bg-opacity', 0.62) * 100)
  threadedInputBgOpacityPct.value = Math.round(readCssVarFloat('--st-threaded-input-bg-opacity', 0.80) * 100)

  /* threaded stage */
  {
    const asp = getComputedStyle(document.documentElement).getPropertyValue('--st-threaded-stage-aspect')?.trim()
    if (asp && asp.includes('/')) {
      const parts = asp.split('/')
      const ax = parseFloat(parts[0]); const ay = parseFloat(parts[1])
      if (Number.isFinite(ax) && Number.isFinite(ay) && ax > 0 && ay > 0) {
        thAspectX.value = Math.round(ax)
        thAspectY.value = Math.round(ay)
      }
    }
  }
  thMaxWidthPct.value = readCssVarFloat('--st-threaded-stage-maxw', 100)
  thPadding.value = readCssVarFloat('--st-threaded-stage-padding', 8)
  thRadius.value = readCssVarFloat('--st-threaded-stage-radius', 12)

  /* write-back to ensure sync */
  setRootVar('--st-content-font-size', contentFontSize.value)
  setRootVar('--st-name-font-size', nameFontSize.value)
  setRootVar('--st-badge-font-size', badgeFontSize.value)
  setRootVar('--st-floor-font-size', floorFontSize.value)
  setRootVar('--st-avatar-size', avatarSize.value)
  setRootVar('--st-chat-width', chatWidth.value)
  setRootVar('--st-input-height', inputHeight.value)
  setRootVarUnitless('--st-content-line-height', String(contentLineHeight.value))
  setRootVar('--st-message-gap', messageGap.value)
  if (Number.isFinite(cardRadius.value)) setRootVar('--st-card-radius', cardRadius.value)
  setRootVar('--st-stripe-width', stripeWidth.value)
  setRootVarUnitless('--st-threaded-bg-opacity', String(threadedBgOpacityPct.value / 100))
  setRootVarUnitless('--st-threaded-msg-bg-opacity', String(threadedMsgBgOpacityPct.value / 100))
  setRootVarUnitless('--st-threaded-list-bg-opacity', String(threadedListBgOpacityPct.value / 100))
  setRootVarUnitless('--st-threaded-input-bg-opacity', String(threadedInputBgOpacityPct.value / 100))
  setRootVarUnitless('--st-threaded-stage-aspect', `${thAspectX.value} / ${thAspectY.value}`)
  setRootVarUnitless('--st-threaded-stage-maxw', thMaxWidthPct.value)
  setRootVar('--st-threaded-stage-padding', thPadding.value)
  setRootVar('--st-threaded-stage-radius', thRadius.value)

  loadSaved()
  if (__saveTimer) { clearInterval(__saveTimer); __saveTimer = null }
  __saveTimer = setInterval(maybeSave, 1000)
})

onBeforeUnmount(() => { if (__saveTimer) { clearInterval(__saveTimer); __saveTimer = null } })
</script>

<template>
  <div class="st-tab-panel" data-scope="settings-threaded">
    <h3>楼层对话外观</h3>

    <!-- 字号/尺寸 -->
    <div class="st-control" data-slider="contentFontSize">
      <label class="st-control-label">
        <span class="label-text">正文文字大小</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="contentFontSize" min="12" max="32" @input="onContentFontSizeNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="12" max="32" step="1" :value="contentFontSize" @pointerdown="onTuningStart('contentFontSize')" @input="onContentFontSizeInput" />
    </div>

    <div class="st-control" data-slider="nameFontSize">
      <label class="st-control-label">
        <span class="label-text">角色名称文字大小</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="nameFontSize" min="10" max="24" @input="onNameFontSizeNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="10" max="24" step="1" :value="nameFontSize" @pointerdown="onTuningStart('nameFontSize')" @input="onNameFontSizeInput" />
    </div>

    <div class="st-control" data-slider="badgeFontSize">
      <label class="st-control-label">
        <span class="label-text">角色徽章文字大小</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="badgeFontSize" min="8" max="16" @input="onBadgeFontSizeNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="8" max="16" step="1" :value="badgeFontSize" @pointerdown="onTuningStart('badgeFontSize')" @input="onBadgeFontSizeInput" />
    </div>

    <div class="st-control" data-slider="floorFontSize">
      <label class="st-control-label">
        <span class="label-text">楼层号文字大小</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="floorFontSize" min="10" max="24" @input="onFloorFontSizeNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="10" max="24" step="1" :value="floorFontSize" @pointerdown="onTuningStart('floorFontSize')" @input="onFloorFontSizeInput" />
    </div>

    <div class="st-control" data-slider="avatarSize">
      <label class="st-control-label">
        <span class="label-text">角色头像大小</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="avatarSize" min="32" max="80" @input="onAvatarSizeNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="32" max="80" step="2" :value="avatarSize" @pointerdown="onTuningStart('avatarSize')" @input="onAvatarSizeInput" />
    </div>

    <div class="st-control" data-slider="chatWidth">
      <label class="st-control-label">
        <span class="label-text">对话页面宽度</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="chatWidth" min="30" max="100" @input="onWidthNumberInput" />
          <span class="unit">%</span>
        </div>
      </label>
      <input type="range" min="30" max="100" step="1" :value="chatWidth" @pointerdown="onTuningStart('chatWidth')" @input="onWidthInput" />
    </div>

    <div class="st-control" data-slider="inputHeight">
      <label class="st-control-label">
        <span class="label-text">底部输入框高度</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="inputHeight" min="60" max="300" @input="onInputHeightNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="60" max="300" step="10" :value="inputHeight" @pointerdown="onTuningStart('inputHeight')" @input="onInputHeightInput" />
    </div>

    <!-- 常用外观 -->
    <div class="st-control" data-slider="contentLineHeight">
      <label class="st-control-label">
        <span class="label-text">正文行距</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="contentLineHeight" min="1.2" max="2.0" step="0.05" @input="onContentLineHeightNumberInput" />
          <span class="unit">×</span>
        </div>
      </label>
      <input type="range" min="1.2" max="2.0" step="0.05" :value="contentLineHeight" @pointerdown="onTuningStart('contentLineHeight')" @input="onContentLineHeightRangeInput" />
    </div>

    <div class="st-control" data-slider="messageGap">
      <label class="st-control-label">
        <span class="label-text">消息间距</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="messageGap" min="6" max="24" step="1" @input="onMessageGapNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="6" max="24" step="1" :value="messageGap" @pointerdown="onTuningStart('messageGap')" @input="onMessageGapRangeInput" />
    </div>

    <div class="st-control" data-slider="cardRadius">
      <label class="st-control-label">
        <span class="label-text">消息卡圆角</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="Number.isFinite(cardRadius) ? cardRadius : ''" min="0" max="24" step="1" @input="onCardRadiusNumberInput" placeholder="默认" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="0" max="24" step="1" :value="Number.isFinite(cardRadius) ? cardRadius : 12" @pointerdown="onTuningStart('cardRadius')" @input="onCardRadiusRangeInput" />
    </div>

    <div class="st-control" data-slider="stripeWidth">
      <label class="st-control-label">
        <span class="label-text">色条宽度</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="stripeWidth" min="0" max="12" step="1" @input="onStripeWidthNumberInput" />
          <span class="unit">px</span>
        </div>
      </label>
      <input type="range" min="0" max="12" step="1" :value="stripeWidth" @pointerdown="onTuningStart('stripeWidth')" @input="onStripeWidthRangeInput" />
    </div>

    <!-- 透明度 -->
    <div class="st-control" data-slider="threadedBgOpacity">
      <label class="st-control-label">
        <span class="label-text">背景图片遮罩不透明度</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="threadedBgOpacityPct" min="0" max="100" @input="onThreadedBgOpacityNumberInput" />
          <span class="unit">%</span>
        </div>
      </label>
      <input type="range" min="0" max="100" step="1" :value="threadedBgOpacityPct" @pointerdown="onTuningStart('threadedBgOpacity')" @input="onThreadedBgOpacityRangeInput" />
    </div>

    <div class="st-control" data-slider="threadedMsgBgOpacity">
      <label class="st-control-label">
        <span class="label-text">楼层消息背景不透明度</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="threadedMsgBgOpacityPct" min="0" max="100" @input="onThreadedMsgBgOpacityNumberInput" />
          <span class="unit">%</span>
        </div>
      </label>
      <input type="range" min="0" max="100" step="1" :value="threadedMsgBgOpacityPct" @pointerdown="onTuningStart('threadedMsgBgOpacity')" @input="onThreadedMsgBgOpacityRangeInput" />
    </div>

    <div class="st-control" data-slider="threadedListBgOpacity">
      <label class="st-control-label">
        <span class="label-text">对话区容器背景不透明度</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="threadedListBgOpacityPct" min="0" max="100" @input="onThreadedListBgOpacityNumberInput" />
          <span class="unit">%</span>
        </div>
      </label>
      <input type="range" min="0" max="100" step="1" :value="threadedListBgOpacityPct" @pointerdown="onTuningStart('threadedListBgOpacity')" @input="onThreadedListBgOpacityRangeInput" />
    </div>

    <div class="st-control" data-slider="threadedInputBgOpacity">
      <label class="st-control-label">
        <span class="label-text">底部输入框背景不透明度</span>
        <div class="value-group">
          <input type="number" class="st-number-input" :value="threadedInputBgOpacityPct" min="0" max="100" @input="onThreadedInputBgOpacityNumberInput" />
          <span class="unit">%</span>
        </div>
      </label>
      <input type="range" min="0" max="100" step="1" :value="threadedInputBgOpacityPct" @pointerdown="onTuningStart('threadedInputBgOpacity')" @input="onThreadedInputBgOpacityRangeInput" />
    </div>

    <!-- 楼层对话：HTML 舞台（iframe） -->
    <h4 class="muted" style="margin:8px 0 0;">HTML 舞台（楼层内 iframe）</h4>

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
</template>

<style>
/* 复制自 AppearancePanel 的 range slider 非 scoped 样式（限定 data-scope），以保持一致外观 */
[data-scope="settings-view"] .st-control input[type="range"],
[data-scope="settings-threaded"] .st-control input[type="range"] {
  -webkit-appearance: none; appearance: none; background: transparent; width: 100%;
}
[data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-runnable-track,
[data-scope="settings-threaded"] .st-control input[type="range"]::-webkit-slider-runnable-track {
  height: 8px !important; border-radius: 9999px !important;
  background: linear-gradient(180deg, rgba(0,0,0,0.68), rgba(0,0,0,0.82)) !important;
  border: 1px solid rgba(0,0,0,0.92) !important;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.25), 0 1px 0 rgba(255,255,255,0.15) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]::-moz-range-track,
[data-scope="settings-threaded"] .st-control input[type="range"]::-moz-range-track {
  height: 8px !important; border-radius: 9999px !important;
  background: linear-gradient(180deg, rgba(0,0,0,0.68), rgba(0,0,0,0.82)) !important;
  border: 1px solid rgba(0,0,0,0.92) !important;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.25), 0 1px 0 rgba(255,255,255,0.15) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-thumb,
[data-scope="settings-threaded"] .st-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none; width: 18px; height: 18px; border-radius: 9999px;
  background: linear-gradient(180deg, #ffffff, #f8f9fa) !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.9), 0 2px 4px rgba(0,0,0,0.20), 0 4px 8px rgba(0,0,0,0.10) !important;
  margin-top: -6px; cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
[data-scope="settings-view"] .st-control input[type="range"]::-moz-range-thumb,
[data-scope="settings-threaded"] .st-control input[type="range"]::-moz-range-thumb {
  width: 18px; height: 18px; border-radius: 9999px;
  background: linear-gradient(180deg, #ffffff, #f8f9fa) !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.9), 0 2px 4px rgba(0,0,0,0.20), 0 4px 8px rgba(0,0,0,0.10) !important;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-runnable-track,
[data-theme="dark"] [data-scope="settings-threaded"] .st-control input[type="range"]::-webkit-slider-runnable-track {
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.85)) !important;
  border: 1px solid rgba(255,255,255,0.95) !important;
  box-shadow: inset 0 1px 2px rgba(255,255,255,0.20), 0 1px 0 rgba(0,0,0,0.15) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-moz-range-track,
[data-theme="dark"] [data-scope="settings-threaded"] .st-control input[type="range"]::-moz-range-track {
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.85)) !important;
  border: 1px solid rgba(255,255,255,0.95) !important;
  box-shadow: inset 0 1px 2px rgba(255,255,255,0.20), 0 1px 0 rgba(0,0,0,0.15) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-webkit-slider-thumb,
[data-theme="dark"] [data-scope="settings-threaded"] .st-control input[type="range"]::-webkit-slider-thumb {
  background: linear-gradient(180deg, #1a1a1a, #0a0a0a) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.85), 0 2px 4px rgba(255,255,255,0.15), 0 4px 8px rgba(0,0,0,0.40) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]::-moz-range-thumb,
[data-theme="dark"] [data-scope="settings-threaded"] .st-control input[type="range"]::-moz-range-thumb {
  background: linear-gradient(180deg, #1a1a1a, #0a0a0a) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.85), 0 2px 4px rgba(255,255,255,0.15), 0 4px 8px rgba(0,0,0,0.40) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-scope="settings-threaded"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-scope="settings-view"] .st-control input[type="range"]:hover::-moz-range-thumb,
[data-scope="settings-threaded"] .st-control input[type="range"]:hover::-moz-range-thumb {
  transform: scale(1.12);
  box-shadow: 0 0 0 1px rgba(255,255,255,0.95), 0 4px 8px rgba(0,0,0,0.25), 0 6px 12px rgba(0,0,0,0.15), 0 0 0 4px rgba(var(--st-primary),0.15) !important;
}
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-theme="dark"] [data-scope="settings-threaded"] .st-control input[type="range"]:hover::-webkit-slider-thumb,
[data-theme="dark"] [data-scope="settings-view"] .st-control input[type="range"]:hover::-moz-range-thumb,
[data-theme="dark"] [data-scope="settings-threaded"] .st-control input[type="range"]:hover::-moz-range-thumb {
  transform: scale(1.12);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.90), 0 4px 8px rgba(255,255,255,0.20), 0 6px 12px rgba(0,0,0,0.50), 0 0 0 4px rgba(var(--st-accent),0.20) !important;
}
[data-scope="settings-view"] .st-control input[type="range"]:active::-webkit-slider-thumb,
[data-scope="settings-threaded"] .st-control input[type="range"]:active::-webkit-slider-thumb,
[data-scope="settings-view"] .st-control input[type="range"]:active::-moz-range-thumb,
[data-scope="settings-threaded"] .st-control input[type="range"]:active::-moz-range-thumb {
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