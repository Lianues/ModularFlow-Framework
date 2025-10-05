import { defineStore } from 'pinia'
import type {
  PresetData,
  PresetFile,
  PromptItem,
  PromptItemInChat,
  PromptItemRelative,
} from './types'
import { isPresetData } from './types'

/**
 * LocalStorage schema and key
 */
const STORAGE_KEY = 'prompt_editor_files'

type RootStorage = {
  files: PresetFile[]
  activeName: string | null
}

/**
 * Local storage helpers
 */
function loadFromLocal(): RootStorage {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { files: [], activeName: null }
    const obj = JSON.parse(raw)
    const files = Array.isArray(obj?.files) ? obj.files : []
    const activeName = typeof obj?.activeName === 'string' ? obj.activeName : (files[0]?.name ?? null)
    return { files, activeName }
  } catch {
    return { files: [], activeName: null }
  }
}

function saveToLocal(data: RootStorage) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // ignore
  }
}

/**
 * Read a File as text
 */
function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('read error'))
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.readAsText(file)
  })
}

/**
 * Preset Store
 * - Manage preset files in browser (import/export)
 * - Manage active preset data and prompt items CRUD
 */
export const usePresetStore = defineStore('preset', {
  state: () => ({
    files: [] as PresetFile[],
    activeName: null as string | null,
    loaded: false,
  }),

  getters: {
    activeIndex(state): number {
      if (!state.activeName) return -1
      return state.files.findIndex(f => f.name === state.activeName)
    },
    activeFile(state): PresetFile | null {
      const idx = (this as any).activeIndex as number
      return idx >= 0 ? (state.files[idx] ?? null) : null
    },
    activeData(): PresetData | null {
      return (this as any).activeFile?.data ?? null
    },
    prompts(): PromptItem[] {
      return ((this as any).activeData?.prompts ?? []) as PromptItem[]
    },
    relativePrompts(): PromptItemRelative[] {
      const list = (((this as any).prompts ?? []) as PromptItem[])
      return list.filter((p: PromptItem) => p.position === 'relative') as PromptItemRelative[]
    },
    inChatPrompts(): PromptItemInChat[] {
      const list = (((this as any).prompts ?? []) as PromptItem[])
      return list.filter((p: PromptItem) => p.position === 'in-chat') as PromptItemInChat[]
    },
  },

  actions: {
    load() {
      if (this.loaded) return
      const { files, activeName } = loadFromLocal()
      // basic shape guard (do not strictly validate every file for performance)
      this.files = Array.isArray(files) ? files.filter(f => f && f.name && f.data) : []
      this.activeName = typeof activeName === 'string' ? activeName : (this.files[0]?.name ?? null)
      this.loaded = true
    },

    persist() {
      saveToLocal({ files: this.files, activeName: this.activeName })
    },

    setActive(name: string) {
      if (this.files.some(f => f.name === name)) {
        this.activeName = name
        this.persist()
      }
    },

    toggleEnable(name: string) {
      const f = this.files.find(x => x.name === name)
      if (f) {
        f.enabled = !f.enabled
        this.persist()
      }
    },

    deleteFile(name: string) {
      const idx = this.files.findIndex(x => x.name === name)
      if (idx >= 0) {
        this.files.splice(idx, 1)
        if (this.activeName === name) {
          this.activeName = this.files[0]?.name ?? null
        }
        this.persist()
      }
    },

    clearAll() {
      this.files = []
      this.activeName = null
      this.persist()
    },

    upsertFile(entry: PresetFile) {
      const idx = this.files.findIndex(f => f.name === entry.name)
      if (idx >= 0) this.files.splice(idx, 1, entry)
      else this.files.unshift(entry)
      this.activeName = entry.name
      this.persist()
    },

    async importFromFile(file: File): Promise<void> {
      const text = await readFileAsText(file)
      let json: any
      try {
        json = JSON.parse(text)
      } catch {
        throw new Error('JSON 解析失败')
      }
      if (!isPresetData(json)) {
        // 兼容：若直接是 { setting, regex_rules, prompts } 结构，也允许导入
        if (!(json && typeof json === 'object' && json.setting && json.prompts && json.regex_rules)) {
          throw new Error('JSON 结构不符合 PresetData')
        }
      }
      const entry: PresetFile = {
        name: file.name,
        enabled: true,
        data: json as PresetData,
      }
      this.upsertFile(entry)
    },

    exportActive(): { filename: string; json: string } | null {
      const file = this.activeFile
      if (!file) return null
      const filename = file.name.endsWith('.json') ? file.name : `${file.name}.json`
      const json = JSON.stringify(file.data, null, 2)
      return { filename, json }
    },

    /**
     * Prompt CRUD
     */
    replacePrompt(next: PromptItem) {
      const data = this.activeData
      if (!data) return
      const idx = data.prompts.findIndex(p => p.identifier === next.identifier)
      if (idx >= 0) {
        // replace reference to keep reactivity
        data.prompts.splice(idx, 1, next as any)
        this.persist()
      }
    },

    addPrompt(item: PromptItem) {
      const data = this.activeData
      if (!data) return
      data.prompts.push(item as any)
      this.persist()
    },

    removePrompt(identifier: string) {
      const data = this.activeData
      if (!data) return
      const idx = data.prompts.findIndex(p => p.identifier === identifier)
      if (idx >= 0) {
        data.prompts.splice(idx, 1)
        this.persist()
      }
    },

    /**
     * Reorder items within a given position while preserving positions of other item types.
     * orderedIds defines the new order (identifiers) for the given position.
     */
    reorderWithinPosition(position: 'relative' | 'in-chat', orderedIds: string[]) {
      const data = this.activeData
      if (!data || !Array.isArray(data.prompts)) return

      // Current items and identifier set for the target position
      const items = data.prompts.filter(p => p && p.position === position)
      const idSet = new Set(items.map(i => i.identifier))

      // Normalize provided ids to existing items only and append any missing ids in original order
      const normalized = orderedIds.filter((id): id is string => !!id && idSet.has(id))
      const missing = items.map(i => i.identifier).filter(id => !normalized.includes(id))
      const finalIds = normalized.concat(missing)

      // Map for quick lookup
      const map = new Map<string, PromptItem>(items.map(i => [i.identifier, i as PromptItem]))

      // Write back into original slots to preserve other-position order
      let writeIdx = 0
      for (let i = 0; i < data.prompts.length; i++) {
        const cur = data.prompts[i]
        if (cur && cur.position === position) {
          if (writeIdx >= finalIds.length) continue
          const id = finalIds[writeIdx++]
          if (!id) continue
          const next = map.get(id)
          if (next) data.prompts.splice(i, 1, next as any)
        }
      }

      // If reordering in-chat items, normalize their "order" field to reflect new sequence
      if (position === 'in-chat') {
        let k = 0
        for (let i = 0; i < data.prompts.length; i++) {
          const p = data.prompts[i]
          if (p && p.position === 'in-chat') {
            ;(p as any).order = k++
          }
        }
      }

      this.persist()
    },
  },
})