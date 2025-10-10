// SmartTavern Composable: useThemeHost (v1)
// 作用：为组件提供主题宿主（ThemeManager/ThemeStore）的响应式封装与便捷 API。
// 安全：默认不执行脚本；仅应用 tokens 与 CSS。脚本开关需要后续显式开启并加沙箱。
// 依赖：src/features/themes/manager.js

import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import ThemeManager from '@/features/themes/manager'

let __inited = false
let __initPromise = null

const currentTheme = ref(null)
const state = reactive({
  version: null,
  ready: false,
})

let __off = null

async function ensureInit() {
  if (__inited) return
  if (!__initPromise) {
    __initPromise = ThemeManager.init({ exposeToWindow: false }).then(() => {
      state.version = ThemeManager.getVersion?.() || 'v1'
      state.ready = true
      currentTheme.value = ThemeManager.getCurrentTheme?.() || null
      // 订阅主题变化
      __off = ThemeManager.on('change', () => {
        currentTheme.value = ThemeManager.getCurrentTheme?.() || null
      })
      __inited = true
    })
  }
  await __initPromise
}

/**
 * 导入并应用主题包（JSON 文本）
 */
async function importFromText(text, { persist = true } = {}) {
  await ensureInit()
  return ThemeManager.importFromText(text, { persist })
}

/**
 * 从文件导入并应用主题包（.json/.sttheme.json）
 */
async function importFromFile(file, { persist = true } = {}) {
  await ensureInit()
  return ThemeManager.importFromFile(file, { persist })
}

/**
 * 直接应用主题包对象
 */
async function applyThemePack(pack, { persist = true } = {}) {
  await ensureInit()
  return ThemeManager.applyThemePack(pack, { persist })
}

/**
 * 重置主题（移除 CSS，清空持久化）
 */
async function resetTheme({ persist = true } = {}) {
  await ensureInit()
  return ThemeManager.resetTheme({ persist })
}

/**
 * 动态设置单个 token（会写入当前 pack 的 tokens 并持久化，若 persist!==false）
 */
async function setToken(name, value, { persist = true } = {}) {
  await ensureInit()
  // ThemeStore.setToken 在 manager/store 内部可用（此处通过 manager 暴露 store 时可直接 setToken）
  try {
    ThemeManager?.store?.setToken?.(name, value, { persist })
  } catch (_) {
    // 回退：尝试直接应用到 root（不会写回包）
    document.documentElement.style.setProperty(name, String(value))
  }
}

/**
 * 主题扩展接口：注册/注销/广播（不执行脚本，仅用于美化扩展监听外观快照）
 */
async function registerExtension(ext) {
  await ensureInit()
  // 返回一个注销函数，若宿主未实现则返回空函数
  return ThemeManager?.registerExtension?.(ext) ?? (() => {})
}
function unregisterExtension(id) {
  try { ThemeManager?.unregisterExtension?.(id) } catch (_) {}
}
function getExtensions() {
  try { return ThemeManager?.getExtensions?.() ?? [] } catch (_) { return [] }
}
async function applyAppearanceSnapshot(snapshot) {
  await ensureInit()
  try { ThemeManager?.applyAppearanceSnapshot?.(snapshot) } catch (_) {}
}

/**
 * 组合式函数：返回响应式状态与 API
 */
export function useThemeHost() {
  onMounted(async () => {
    await ensureInit()
  })
  onBeforeUnmount(() => {
    // 不主动取消全局订阅（保持单例），组件级无需处理
  })

  return {
    // state
    ready: state,
    version: state,
    currentTheme,

    // actions
    importFromText,
    importFromFile,
    applyThemePack,
    resetTheme,
    setToken,
    registerExtension,
    unregisterExtension,
    getExtensions,
    applyAppearanceSnapshot,
    registerExtension,
    unregisterExtension,
    getExtensions,
    applyAppearanceSnapshot,
  }
}

export default useThemeHost