import { ref } from 'vue'
import ThemeManager from '@/features/themes/manager'

/**
 * useThemeMode：统一管理主题模式（system/dark/light）
 * - 暴露：theme / applyTheme / onThemeUpdate / initTheme
 * - 行为：跟随系统时监听 prefers-color-scheme 变化；与 ThemeManager 同步；持久化本地存储
 *
 * 用法：
 *   import { useThemeMode } from '@/composables/useThemeMode'
 *   const { theme, initTheme, onThemeUpdate, applyTheme } = useThemeMode()
 *   onMounted(() => initTheme()) // 优先于 UI 渲染，避免白屏闪烁
 */

let __themeMql = null
let __onSchemeChange = null

export function useThemeMode() {
  const theme = ref('system')

  function detectInitialTheme() {
    try {
      const attrTheme = document?.documentElement?.getAttribute?.('data-theme')
      const savedTheme = localStorage.getItem('st.theme')
      return (attrTheme === 'dark' || attrTheme === 'light') ? attrTheme
           : (savedTheme === 'dark' || savedTheme === 'light' || savedTheme === 'system') ? savedTheme
           : 'system'
    } catch (_) {
      return 'system'
    }
  }

  function applyTheme(t) {
    const root = document.documentElement
    // detach previous system watcher if any
    if (__themeMql && t !== 'system' && __onSchemeChange) {
      try { __themeMql.removeEventListener('change', __onSchemeChange) } catch (_) {}
      __themeMql = null
    }
    if (t === 'dark' || t === 'light') {
      root.setAttribute('data-theme', t)
      return
    }
    // system: follow OS prefers-color-scheme (and react to changes)
    const mql = window.matchMedia?.('(prefers-color-scheme: dark)')
    const setByMql = (mq) => {
      try {
        root.setAttribute('data-theme', mq?.matches ? 'dark' : 'light')
      } catch (_) {}
    }
    setByMql(mql)
    if (mql) {
      __onSchemeChange = (e) => setByMql(e)
      try { mql.addEventListener('change', __onSchemeChange) } catch (_) {}
      __themeMql = mql
    }
  }

  function onThemeUpdate(t) {
    theme.value = t
    applyTheme(t)
    try { ThemeManager.setColorMode?.(t) } catch (_) {}
    try { localStorage.setItem('st.theme', t) } catch (_) {}
  }

  function initTheme() {
    const init = detectInitialTheme()
    if (init !== 'system') {
      theme.value = init
    }
    applyTheme(theme.value)
    try { ThemeManager.setColorMode?.(theme.value) } catch (_) {}
  }

  return {
    theme,
    applyTheme,
    onThemeUpdate,
    initTheme,
  }
}

export default useThemeMode