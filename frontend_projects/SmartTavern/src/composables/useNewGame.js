import { ref, nextTick } from 'vue'

/**
 * useNewGame：管理“新建对话”模态的状态与行为
 * - 提供：newGameOpen / openNewGame / cancelNewGame / onNewChatConfirm
 * - 依赖：setView 回调（用于将视图切换到 threaded/sandbox），refreshIcons（刷新图标与 Flowbite）
 *
 * 用法（在 App.vue 中）：
 *   import { useNewGame } from '@/composables/useNewGame'
 *   const { newGameOpen, openNewGame, cancelNewGame, onNewChatConfirm } =
 *     useNewGame({ setView: (v) => (view.value = v), refreshIcons })
 */
export function useNewGame({ setView, refreshIcons }) {
  const newGameOpen = ref(false)

  function openNewGame() {
    newGameOpen.value = true
    // 打开后刷新图标与交互组件
    nextTick(() => {
      try { window?.lucide?.createIcons?.() } catch (_) {}
      if (typeof window.initFlowbite === 'function') {
        try { window.initFlowbite() } catch (_) {}
      }
    })
  }

  function cancelNewGame() {
    newGameOpen.value = false
    nextTick(() => {
      try { window?.lucide?.createIcons?.() } catch (_) {}
      if (typeof window.initFlowbite === 'function') {
        try { window.initFlowbite() } catch (_) {}
      }
    })
  }

  function onNewChatConfirm(payload) {
    // TODO：与后端通信创建会话（携带所选项）
    // payload: { name, type, preset, character, persona, regex?, worldbook? }
    const t = payload?.type
    if (t === 'threaded' || t === 'sandbox') {
      try {
        typeof setView === 'function' && setView(t)
      } catch (_) {}
    }
    newGameOpen.value = false
    // 关闭后刷新图标
    if (typeof refreshIcons === 'function') {
      refreshIcons()
    } else {
      nextTick(() => { try { window?.lucide?.createIcons?.() } catch (_) {} })
    }
  }

  return {
    newGameOpen,
    openNewGame,
    cancelNewGame,
    onNewChatConfirm,
  }
}

export default useNewGame