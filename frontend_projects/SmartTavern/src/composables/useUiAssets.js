import { nextTick } from 'vue'

/**
 * useUiAssets：统一管理 UI 依赖（Lucide 图标 / Flowbite JS）的按需加载与刷新
 *
 * - ensureUIAssets(): 按需加载脚本并完成一次性初始化
 * - refreshIcons(): 在动态节点更新后刷新图标与 Flowbite 组件（建议在 nextTick 中调用）
 *
 * 用法：
 *   import { useUiAssets } from '@/composables/useUiAssets'
 *   const { ensureUIAssets, refreshIcons } = useUiAssets()
 *   onMounted(() => { ensureUIAssets() })
 *   // 任意需要刷新图标/交互组件的地方：
 *   refreshIcons()
 */
export function useUiAssets() {
  async function loadScript(src) {
    return new Promise((resolve, reject) => {
      try {
        if (document.querySelector(`script[src="${src}"]`)) return resolve()
        const s = document.createElement('script')
        s.src = src
        s.async = true
        s.onload = () => resolve()
        s.onerror = (e) => reject(e)
        document.head.appendChild(s)
      } catch (e) {
        // 无法创建 script 节点时直接 resolve，避免阻塞
        resolve()
      }
    })
  }

  async function ensureUIAssets() {
    try {
      // Lucide（图标）
      await loadScript('https://unpkg.com/lucide@latest/dist/umd/lucide.min.js')
    } catch (_) {}

    try {
      // Flowbite（交互组件）
      await loadScript('https://cdn.jsdelivr.net/npm/flowbite@2.0.0/dist/flowbite.min.js')
    } catch (_) {}

    try { window?.lucide?.createIcons?.() } catch (_) {}
    if (typeof window.initFlowbite === 'function') {
      try { window.initFlowbite() } catch (_) {}
    }
  }

  function refreshIcons() {
    nextTick(() => {
      try { window?.lucide?.createIcons?.() } catch (_) {}
      if (typeof window.initFlowbite === 'function') {
        try { window.initFlowbite() } catch (_) {}
      }
    })
  }

  return {
    ensureUIAssets,
    refreshIcons,
  }
}

export default useUiAssets