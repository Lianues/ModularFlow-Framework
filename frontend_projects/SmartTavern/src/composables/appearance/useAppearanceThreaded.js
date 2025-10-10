// SmartTavern Composable: useAppearanceThreaded (v1)
// 目标：抽离“楼层对话外观”页签中的 CSS 变量读写、快照构建与本地持久化、快照广播。
// 使用方式：
//   import useAppearanceThreaded from '@/composables/appearance/useAppearanceThreaded'
//   const {
//     state, // 所有涉及的 ref
//     initFromCSS, applyState, buildSnapshot,
//     saveSnapshotLS, loadSnapshotLS,
//     startAutoSave, stopAutoSave,
//     setRootVar, setRootVarUnitless, readCssVar, readCssVarFloat
//   } = useAppearanceThreaded()
//
// 说明：
// - 本模块不直接绑定 UI 控件，仅提供状态与方法，便于在组件中复用与测试。
// - 快照广播到 ThemeManager.applyAppearanceSnapshot（若存在）以供美化扩展监听。
// - 安全：不执行任何外部脚本，仅令牌与 CSS 变量层面的更新。

import { ref } from 'vue'
import ThemeManager from '@/features/themes/manager'

// LocalStorage key (threaded tab-scoped)
const STORE_KEY = 'st.appearance.threaded.v1'

// CSS helpers
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

// LS helpers
function saveSnapshotLS(snapshot) {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(snapshot))
    return true
  } catch (_) {
    return false
  }
}
function loadSnapshotLS() {
  try {
    const raw = localStorage.getItem(STORE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (_) {
    return null
  }
}

// State factory
function createState() {
  // 字号/尺寸
  const contentFontSize = ref(18)
  const nameFontSize = ref(16)
  const badgeFontSize = ref(11)
  const floorFontSize = ref(16)
  const avatarSize = ref(56)
  const chatWidth = ref(80)
  const inputHeight = ref(100)

  // 常用外观
  const contentLineHeight = ref(1.75)
  const messageGap = ref(12)
  const cardRadius = ref(NaN) // NaN 表示未覆盖（沿用默认）
  const stripeWidth = ref(8)

  // 透明度（%）
  const threadedBgOpacityPct = ref(12)
  const threadedMsgBgOpacityPct = ref(82)
  const threadedListBgOpacityPct = ref(62)
  const threadedInputBgOpacityPct = ref(80)

  // 楼层内 HTML 舞台
  const thAspectX = ref(16)
  const thAspectY = ref(9)
  const thMaxWidthPct = ref(100)
  const thPadding = ref(8)
  const thRadius = ref(12)

  return {
    contentFontSize, nameFontSize, badgeFontSize, floorFontSize, avatarSize,
    chatWidth, inputHeight,
    contentLineHeight, messageGap, cardRadius, stripeWidth,
    threadedBgOpacityPct, threadedMsgBgOpacityPct, threadedListBgOpacityPct, threadedInputBgOpacityPct,
    thAspectX, thAspectY, thMaxWidthPct, thPadding, thRadius,
  }
}

// Build snapshot from state refs
function buildSnapshot(state) {
  return {
    contentFontSize: Number(state.contentFontSize.value),
    nameFontSize: Number(state.nameFontSize.value),
    badgeFontSize: Number(state.badgeFontSize.value),
    floorFontSize: Number(state.floorFontSize.value),
    avatarSize: Number(state.avatarSize.value),
    chatWidth: Number(state.chatWidth.value),
    inputHeight: Number(state.inputHeight.value),

    contentLineHeight: Number(state.contentLineHeight.value),
    messageGap: Number(state.messageGap.value),
    cardRadius: Number.isFinite(state.cardRadius.value) ? Number(state.cardRadius.value) : null,
    stripeWidth: Number(state.stripeWidth.value),

    threadedBgOpacityPct: Number(state.threadedBgOpacityPct.value),
    threadedMsgBgOpacityPct: Number(state.threadedMsgBgOpacityPct.value),
    threadedListBgOpacityPct: Number(state.threadedListBgOpacityPct.value),
    threadedInputBgOpacityPct: Number(state.threadedInputBgOpacityPct.value),

    thAspectX: Number(state.thAspectX.value),
    thAspectY: Number(state.thAspectY.value),
    thMaxWidthPct: Number(state.thMaxWidthPct.value),
    thPadding: Number(state.thPadding.value),
    thRadius: Number(state.thRadius.value),
  }
}

// Apply state from snapshot into refs + write CSS variables
function applyState(state, s) {
  if (!s || typeof s !== 'object') return
  const num = (v, f) => (typeof v === 'number' ? v : f)

  state.contentFontSize.value = num(s.contentFontSize, 18); setRootVar('--st-content-font-size', state.contentFontSize.value)
  state.nameFontSize.value = num(s.nameFontSize, 16); setRootVar('--st-name-font-size', state.nameFontSize.value)
  state.badgeFontSize.value = num(s.badgeFontSize, 11); setRootVar('--st-badge-font-size', state.badgeFontSize.value)
  state.floorFontSize.value = num(s.floorFontSize, 16); setRootVar('--st-floor-font-size', state.floorFontSize.value)
  state.avatarSize.value = num(s.avatarSize, 56); setRootVar('--st-avatar-size', state.avatarSize.value)
  state.chatWidth.value = num(s.chatWidth, 80); setRootVar('--st-chat-width', state.chatWidth.value)
  state.inputHeight.value = num(s.inputHeight, 100); setRootVar('--st-input-height', state.inputHeight.value)

  state.contentLineHeight.value = num(s.contentLineHeight, 1.75); setRootVarUnitless('--st-content-line-height', String(state.contentLineHeight.value))
  state.messageGap.value = num(s.messageGap, 12); setRootVar('--st-message-gap', state.messageGap.value)

  if (s.cardRadius === null) {
    state.cardRadius.value = NaN
    document.documentElement.style.removeProperty('--st-card-radius')
  } else {
    state.cardRadius.value = num(s.cardRadius, NaN)
    if (Number.isFinite(state.cardRadius.value)) setRootVar('--st-card-radius', state.cardRadius.value)
  }
  state.stripeWidth.value = num(s.stripeWidth, 8); setRootVar('--st-stripe-width', state.stripeWidth.value)

  state.threadedBgOpacityPct.value = num(s.threadedBgOpacityPct, 12); setRootVarUnitless('--st-threaded-bg-opacity', String(state.threadedBgOpacityPct.value / 100))
  state.threadedMsgBgOpacityPct.value = num(s.threadedMsgBgOpacityPct, 82); setRootVarUnitless('--st-threaded-msg-bg-opacity', String(state.threadedMsgBgOpacityPct.value / 100))
  state.threadedListBgOpacityPct.value = num(s.threadedListBgOpacityPct, 62); setRootVarUnitless('--st-threaded-list-bg-opacity', String(state.threadedListBgOpacityPct.value / 100))
  state.threadedInputBgOpacityPct.value = num(s.threadedInputBgOpacityPct, 80); setRootVarUnitless('--st-threaded-input-bg-opacity', String(state.threadedInputBgOpacityPct.value / 100))

  state.thAspectX.value = num(s.thAspectX, 16)
  state.thAspectY.value = num(s.thAspectY, 9)
  setRootVarUnitless('--st-threaded-stage-aspect', `${state.thAspectX.value} / ${state.thAspectY.value}`)
  state.thMaxWidthPct.value = num(s.thMaxWidthPct, 100); setRootVarUnitless('--st-threaded-stage-maxw', state.thMaxWidthPct.value)
  state.thPadding.value = num(s.thPadding, 8); setRootVar('--st-threaded-stage-padding', state.thPadding.value)
  state.thRadius.value = num(s.thRadius, 12); setRootVar('--st-threaded-stage-radius', state.thRadius.value)
}

// Initialize refs from current CSS variables and write-back to sync UI
function initFromCSS(state) {
  state.contentFontSize.value = readCssVar('--st-content-font-size', 18)
  state.nameFontSize.value = readCssVar('--st-name-font-size', 16)
  state.badgeFontSize.value = readCssVar('--st-badge-font-size', 11)
  state.floorFontSize.value = readCssVar('--st-floor-font-size', 16)
  state.avatarSize.value = readCssVar('--st-avatar-size', 56)
  {
    const widthVar = getComputedStyle(document.documentElement).getPropertyValue('--st-chat-width')?.trim()
    state.chatWidth.value = widthVar ? parseInt(widthVar, 10) : 80
  }
  state.inputHeight.value = readCssVar('--st-input-height', 100)

  state.contentLineHeight.value = readCssVarFloat('--st-content-line-height', 1.75)
  state.messageGap.value = readCssVarFloat('--st-message-gap', 12)
  {
    const cr = readCssVarFloat('--st-card-radius', NaN)
    state.cardRadius.value = Number.isFinite(cr) ? cr : NaN
  }
  state.stripeWidth.value = readCssVarFloat('--st-stripe-width', 8)

  state.threadedBgOpacityPct.value = Math.round(readCssVarFloat('--st-threaded-bg-opacity', 0.12) * 100)
  state.threadedMsgBgOpacityPct.value = Math.round(readCssVarFloat('--st-threaded-msg-bg-opacity', 0.82) * 100)
  state.threadedListBgOpacityPct.value = Math.round(readCssVarFloat('--st-threaded-list-bg-opacity', 0.62) * 100)
  state.threadedInputBgOpacityPct.value = Math.round(readCssVarFloat('--st-threaded-input-bg-opacity', 0.80) * 100)

  // threaded stage
  {
    const asp = getComputedStyle(document.documentElement).getPropertyValue('--st-threaded-stage-aspect')?.trim()
    if (asp && asp.includes('/')) {
      const parts = asp.split('/')
      const ax = parseFloat(parts[0]); const ay = parseFloat(parts[1])
      if (Number.isFinite(ax) && Number.isFinite(ay) && ax > 0 && ay > 0) {
        state.thAspectX.value = Math.round(ax)
        state.thAspectY.value = Math.round(ay)
      }
    }
  }
  state.thMaxWidthPct.value = readCssVarFloat('--st-threaded-stage-maxw', 100)
  state.thPadding.value = readCssVarFloat('--st-threaded-stage-padding', 8)
  state.thRadius.value = readCssVarFloat('--st-threaded-stage-radius', 12)

  // write-back to ensure sync
  setRootVar('--st-content-font-size', state.contentFontSize.value)
  setRootVar('--st-name-font-size', state.nameFontSize.value)
  setRootVar('--st-badge-font-size', state.badgeFontSize.value)
  setRootVar('--st-floor-font-size', state.floorFontSize.value)
  setRootVar('--st-avatar-size', state.avatarSize.value)
  setRootVar('--st-chat-width', state.chatWidth.value)
  setRootVar('--st-input-height', state.inputHeight.value)
  setRootVarUnitless('--st-content-line-height', String(state.contentLineHeight.value))
  setRootVar('--st-message-gap', state.messageGap.value)
  if (Number.isFinite(state.cardRadius.value)) setRootVar('--st-card-radius', state.cardRadius.value)
  setRootVar('--st-stripe-width', state.stripeWidth.value)
  setRootVarUnitless('--st-threaded-bg-opacity', String(state.threadedBgOpacityPct.value / 100))
  setRootVarUnitless('--st-threaded-msg-bg-opacity', String(state.threadedMsgBgOpacityPct.value / 100))
  setRootVarUnitless('--st-threaded-list-bg-opacity', String(state.threadedListBgOpacityPct.value / 100))
  setRootVarUnitless('--st-threaded-input-bg-opacity', String(state.threadedInputBgOpacityPct.value / 100))
  setRootVarUnitless('--st-threaded-stage-aspect', `${state.thAspectX.value} / ${state.thAspectY.value}`)
  setRootVarUnitless('--st-threaded-stage-maxw', state.thMaxWidthPct.value)
  setRootVar('--st-threaded-stage-padding', state.thPadding.value)
  setRootVar('--st-threaded-stage-radius', state.thRadius.value)
}

// Auto save timer
function startAutoSave(state, { intervalMs = 1000 } = {}) {
  let last = ''
  function tick() {
    try {
      const snap = buildSnapshot(state)
      const str = JSON.stringify(snap)
      if (str !== last) {
        saveSnapshotLS(snap)
        last = str
      }
      // Broadcast snapshot for theme extensions (optional)
      try { ThemeManager?.applyAppearanceSnapshot?.(snap) } catch (_) {}
    } catch (_) {}
  }
  const timer = setInterval(tick, intervalMs)
  return () => {
    clearInterval(timer)
  }
}
function stopAutoSave(stopFn) {
  try { typeof stopFn === 'function' && stopFn() } catch (_) {}
}

// Composable entry
export default function useAppearanceThreaded() {
  const state = createState()
  return {
    state,
    // lifecycle helpers
    initFromCSS: () => initFromCSS(state),
    applyState: (snap) => applyState(state, snap),
    buildSnapshot: () => buildSnapshot(state),
    saveSnapshotLS: (snap) => saveSnapshotLS(snap),
    loadSnapshotLS,
    startAutoSave: (opts) => startAutoSave(state, opts),
    stopAutoSave,
    // low-level helpers
    setRootVar,
    setRootVarUnitless,
    readCssVar,
    readCssVarFloat,
  }
}