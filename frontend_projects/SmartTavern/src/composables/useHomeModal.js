import { ref, nextTick } from 'vue'

/**
 * useHomeModal：主页功能模态（load / gallery / options）的集中编排
 * - 状态：homeModalOpen / homeModalTitle / homeModalType
 * - 行为：openHomeModal(type) / closeHomeModal()
 * - UI：打开后刷新 lucide 图标与 Flowbite 组件，确保动态节点可用
 *
 * 用法：
 *   import { useHomeModal } from '@/composables/useHomeModal'
 *   const { homeModalOpen, homeModalTitle, homeModalType, openHomeModal, closeHomeModal } = useHomeModal()
 */
export function useHomeModal() {
  const homeModalOpen = ref(false)
  const homeModalTitle = ref('')
  const homeModalType = ref('') // 'load' | 'gallery' | 'options'

  function openHomeModal(type) {
    homeModalType.value = type
    homeModalTitle.value =
      type === 'load' ? '读取存档'
      : type === 'gallery' ? '画廊'
      : type === 'options' ? '选项'
      : ' '
    homeModalOpen.value = true

    nextTick(() => {
      try { window?.lucide?.createIcons?.() } catch (_) {}
      if (typeof window.initFlowbite === 'function') {
        try { window.initFlowbite() } catch (_) {}
      }
    })
  }

  function closeHomeModal() {
    homeModalOpen.value = false
    homeModalType.value = ''
    homeModalTitle.value = ''
  }

  return {
    homeModalOpen,
    homeModalTitle,
    homeModalType,
    openHomeModal,
    closeHomeModal,
  }
}

export default useHomeModal