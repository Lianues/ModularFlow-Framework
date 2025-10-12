import { ref, nextTick } from 'vue'
import DataCatalog from '@/services/dataCatalog'

/**
 * useViewModal：内容查看模态编排（Preset/WorldBook/Character/Persona/Regex）
 * - 状态：open/title/type/data/loading/error/file
 * - 行为：openViewModal(type, title, fileOrData) / closeViewModal()
 * - 特性：支持传入对象直接渲染，或传入文件名自动拉取并缓存
 * - UI：打开/载入完成后刷新 lucide 图标与 Flowbite 组件
 *
 * 用法（父组件/App）：
 *   import { useViewModal } from '@/composables/useViewModal'
 *   const {
 *     viewModalOpen, viewModalTitle, viewModalType, viewModalData,
 *     viewModalLoading, viewModalError, viewModalFile,
 *     openViewModal, closeViewModal, currentPresetData
 *   } = useViewModal()
 */
export function useViewModal() {
  // state
  const viewModalOpen    = ref(false)
  const viewModalTitle   = ref('')
  const viewModalType    = ref('') // 'preset' | 'worldbook' | 'character' | 'persona' | 'regex'
  const viewModalData    = ref(null)
  const viewModalLoading = ref(false)
  const viewModalError   = ref('')
  const viewModalFile    = ref('')

  // 供外部 AI 配置面板使用的“当前预设内容”
  const currentPresetData = ref(null)

  async function openViewModal(type, title, fileOrData) {
    viewModalType.value  = type
    viewModalTitle.value = title || ''
    viewModalError.value = ''
    viewModalLoading.value = true
    viewModalData.value  = null
    viewModalFile.value  = typeof fileOrData === 'string' ? fileOrData : ''

    viewModalOpen.value = true

    try {
      if (fileOrData && typeof fileOrData === 'object') {
        // 直接渲染对象
        viewModalData.value = fileOrData
      } else if (typeof fileOrData === 'string') {
        // 按类型向后端请求详情
        const fetchers = {
          preset:    (f) => DataCatalog.getPresetDetail(f,    { useCache: false, persist: false }),
          worldbook: (f) => DataCatalog.getWorldBookDetail(f, { useCache: false, persist: false }),
          character: (f) => DataCatalog.getCharacterDetail(f, { useCache: false, persist: false }),
          persona:   (f) => DataCatalog.getPersonaDetail(f,   { useCache: false, persist: false }),
          regex:     (f) => DataCatalog.getRegexRuleDetail(f, { useCache: false, persist: false }),
        }
        const fn = fetchers[type]
        if (!fn) throw new Error(`未知类型: ${type}`)
        const res = await fn(fileOrData)
        // 后端结构：{ file, name, description, content }
        viewModalData.value = res && (res.content ?? res)
        if (res && typeof res.file === 'string') {
          viewModalFile.value = res.file
        }
        if (type === 'preset' && res) {
          currentPresetData.value = res.content ?? res
        }
      } else {
        // 无 fileOrData：保持空占位
      }
    } catch (e) {
      viewModalError.value = e?.message || String(e)
    } finally {
      viewModalLoading.value = false
      // 刷新图标与 Flowbite 交互组件
      nextTick(() => {
        try { window?.lucide?.createIcons?.() } catch (_) {}
        if (typeof window.initFlowbite === 'function') {
          try { window.initFlowbite() } catch (_) {}
        }
      })
    }
  }

  function closeViewModal() {
    viewModalOpen.value = false
    viewModalType.value = ''
    viewModalTitle.value = ''
    viewModalData.value = null
    viewModalLoading.value = false
    viewModalError.value = ''
    viewModalFile.value = ''
  }

  return {
    // state
    viewModalOpen,
    viewModalTitle,
    viewModalType,
    viewModalData,
    viewModalLoading,
    viewModalError,
    viewModalFile,
    currentPresetData,

    // actions
    openViewModal,
    closeViewModal,
  }
}

export default useViewModal