import { ref } from 'vue'

/**
 * usePanels：右侧各功能面板开关状态的集中管理（互斥切换）
 * - 目标：用统一的 togglePanel/closeAll 替代 App.vue 中重复的内联赋值表达式
 * - 用法：
 *   import { usePanels } from '@/composables/usePanels'
 *   const {
 *     // state
 *     appearanceOpen, appSettingsOpen, presetsOpen, worldbookOpen,
 *     charactersOpen, personaOpen, regexOpen, aiConfigOpen,
 *     // actions
 *     togglePanel, closeAllPanels,
 *   } = usePanels()
 *   // 在模板事件中使用：@openAppearance="togglePanel('appearance')" 等
 */
export function usePanels() {
  // 所有右侧抽屉型面板的开关状态
  const appearanceOpen   = ref(false)
  const appSettingsOpen  = ref(false)
  const presetsOpen      = ref(false)
  const worldbookOpen    = ref(false)
  const charactersOpen   = ref(false)
  const personaOpen      = ref(false)
  const regexOpen        = ref(false)
  const aiConfigOpen     = ref(false)

  // 内部帮助：关闭全部
  function closeAllPanels() {
    appearanceOpen.value  = false
    appSettingsOpen.value = false
    presetsOpen.value     = false
    worldbookOpen.value   = false
    charactersOpen.value  = false
    personaOpen.value     = false
    regexOpen.value       = false
    aiConfigOpen.value    = false
  }

  // 互斥切换：点哪个就只保留哪个打开（再次触发同一面板则关闭）
  function togglePanel(name) {
    const current = {
      appearance: appearanceOpen,
      appSettings: appSettingsOpen,
      presets: presetsOpen,
      worldbook: worldbookOpen,
      characters: charactersOpen,
      persona: personaOpen,
      regex: regexOpen,
      aiConfig: aiConfigOpen,
    }[name]

    if (!current) {
      // 未知面板名：直接关闭所有以保证一致性
      closeAllPanels()
      return
    }

    const willOpen = !current.value
    closeAllPanels()
    current.value = willOpen
  }

  return {
    // state
    appearanceOpen,
    appSettingsOpen,
    presetsOpen,
    worldbookOpen,
    charactersOpen,
    personaOpen,
    regexOpen,
    aiConfigOpen,

    // actions
    togglePanel,
    closeAllPanels,
  }
}

export default usePanels