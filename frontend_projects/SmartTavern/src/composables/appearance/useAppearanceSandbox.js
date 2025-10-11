// SmartTavern Composable: useAppearanceSandbox (v1)
// 目标：抽离“全屏沙盒外观”页签中的 CSS 变量读写、快照构建与本地持久化、快照广播。
// 使用方式：
//   import useAppearanceSandbox from '@/composables/appearance/useAppearanceSandbox'
//   const {
//     state, // 所有涉及的 ref
//     initFromCSS, applyState, buildSnapshot,
//     saveSnapshotLS, loadSnapshotLS,
//     startAutoSave, stopAutoSave,
//     setRootVar, setRootVarUnitless, readCssVarFloat
//   } = useAppearanceSandbox()
//
// 说明：
// - 本模块不直接绑定 UI 控件，仅提供状态与方法，便于在组件中复用与测试。
// - 快照广播到 ThemeManager.applyAppearanceSnapshot（若存在）以供美化扩展监听。
// - 安全：不执行任何外部脚本，仅令牌与 CSS 变量层面的更新。

import { ref } from 'vue'
import ThemeManager from '@/features/themes/manager'

// LocalStorage key (sandbox tab-scoped)
const STORE_KEY = 'st.appearance.sandbox.v1'

// CSS helpers
function readCssVarFloat(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name)?.trim()
  if (!v) return fallback
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : fallback
}
function setRootVar(name, value) {
  // 这些变量都使用 px（例如 --st-sandbox-max-width/--st-sandbox-padding/--st-sandbox-radius）
  document.documentElement.style.setProperty(name, typeof value === 'number' ? `${value}px` : String(value))
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
  // 宽高比
  const sandboxAspectX = ref(16)
  const sandboxAspectY = ref(9)
  // 尺寸与圆角/内边距
  const sandboxMaxWidth = ref(1100)       // px
  const sandboxMaxWidthLimit = ref(1920)  // px，可在 UI 中调整滑条上限
  const sandboxPadding = ref(16)          // px
  const sandboxRadius = ref(18)           // px
  // 透明度（%）
  const sandboxBgOpacityPct = ref(12)      // 0~100
  const sandboxStageBgOpacityPct = ref(82) // 0~100
  // 背景遮罩模糊（px）
  const sandboxBgBlurPx = ref(0)

  return {
    sandboxAspectX, sandboxAspectY,
    sandboxMaxWidth, sandboxMaxWidthLimit,
    sandboxPadding, sandboxRadius,
    sandboxBgOpacityPct, sandboxStageBgOpacityPct,
    // 新增
    sandboxBgBlurPx,
  }
}

// Build snapshot from state refs
function buildSnapshot(state) {
  return {
    sandboxAspectX: Number(state.sandboxAspectX.value),
    sandboxAspectY: Number(state.sandboxAspectY.value),
    sandboxMaxWidth: Number(state.sandboxMaxWidth.value),
    sandboxMaxWidthLimit: Number(state.sandboxMaxWidthLimit.value),
    sandboxPadding: Number(state.sandboxPadding.value),
    sandboxRadius: Number(state.sandboxRadius.value),
    sandboxBgOpacityPct: Number(state.sandboxBgOpacityPct.value),
    sandboxStageBgOpacityPct: Number(state.sandboxStageBgOpacityPct.value),
    // 新增：背景遮罩模糊（px）
    sandboxBgBlurPx: Number(state.sandboxBgBlurPx.value),
  }
}

// Apply state from snapshot into refs + write CSS variables
function applyState(state, s) {
  if (!s || typeof s !== 'object') return
  const num = (v, f) => (typeof v === 'number' ? v : f)

  state.sandboxAspectX.value = num(s.sandboxAspectX, 16)
  state.sandboxAspectY.value = num(s.sandboxAspectY, 9)
  setRootVarUnitless('--st-sandbox-aspect', `${state.sandboxAspectX.value} / ${state.sandboxAspectY.value}`)

  state.sandboxMaxWidth.value = num(s.sandboxMaxWidth, 1100)
  setRootVar('--st-sandbox-max-width', state.sandboxMaxWidth.value)

  state.sandboxMaxWidthLimit.value = num(s.sandboxMaxWidthLimit, 1920)

  state.sandboxPadding.value = num(s.sandboxPadding, 16)
  setRootVar('--st-sandbox-padding', state.sandboxPadding.value)

  state.sandboxRadius.value = num(s.sandboxRadius, 18)
  setRootVar('--st-sandbox-radius', state.sandboxRadius.value)

  state.sandboxBgOpacityPct.value = num(s.sandboxBgOpacityPct, 12)
  setRootVarUnitless('--st-sandbox-bg-opacity', String(state.sandboxBgOpacityPct.value / 100))

  state.sandboxStageBgOpacityPct.value = num(s.sandboxStageBgOpacityPct, 82)
  setRootVarUnitless('--st-sandbox-stage-bg-opacity', String(state.sandboxStageBgOpacityPct.value / 100))

  // 新增：背景遮罩模糊
  state.sandboxBgBlurPx.value = num(s.sandboxBgBlurPx, 0)
  setRootVar('--st-sandbox-bg-blur', state.sandboxBgBlurPx.value)
}

// Initialize refs from current CSS variables and write-back to sync UI
function initFromCSS(state) {
  // aspect
  const aspRaw = getComputedStyle(document.documentElement).getPropertyValue('--st-sandbox-aspect')?.trim()
  if (aspRaw && aspRaw.includes('/')) {
    const parts = aspRaw.split('/')
    const ax = parseFloat(parts[0]); const ay = parseFloat(parts[1])
    if (Number.isFinite(ax) && Number.isFinite(ay) && ax > 0 && ay > 0) {
      state.sandboxAspectX.value = Math.round(ax)
      state.sandboxAspectY.value = Math.round(ay)
    }
  }
  // size/padding/radius
  state.sandboxMaxWidth.value = readCssVarFloat('--st-sandbox-max-width', 1100)
  state.sandboxPadding.value = readCssVarFloat('--st-sandbox-padding', 16)
  state.sandboxRadius.value = readCssVarFloat('--st-sandbox-radius', 18)

  // opacities (css stores 0~1)
  state.sandboxBgOpacityPct.value = Math.round(readCssVarFloat('--st-sandbox-bg-opacity', 0.12) * 100)
  state.sandboxStageBgOpacityPct.value = Math.round(readCssVarFloat('--st-sandbox-stage-bg-opacity', 0.82) * 100)
  // 新增：背景遮罩模糊（px）
  state.sandboxBgBlurPx.value = readCssVarFloat('--st-sandbox-bg-blur', 0)

  // write-back
  setRootVarUnitless('--st-sandbox-aspect', `${state.sandboxAspectX.value} / ${state.sandboxAspectY.value}`)
  setRootVar('--st-sandbox-max-width', state.sandboxMaxWidth.value)
  setRootVar('--st-sandbox-padding', state.sandboxPadding.value)
  setRootVar('--st-sandbox-radius', state.sandboxRadius.value)
  setRootVarUnitless('--st-sandbox-bg-opacity', String(state.sandboxBgOpacityPct.value / 100))
  setRootVarUnitless('--st-sandbox-stage-bg-opacity', String(state.sandboxStageBgOpacityPct.value / 100))
  // 新增：写回遮罩模糊
  setRootVar('--st-sandbox-bg-blur', state.sandboxBgBlurPx.value)
}

// Auto save timer + broadcast
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
export default function useAppearanceSandbox() {
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
    readCssVarFloat,
  }
}