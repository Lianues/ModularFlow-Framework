import { defineStore } from 'pinia'
import type {
  PresetData,
  PresetFile,
  PromptItem,
  PromptItemInChat,
  PromptItemRelative,
  RegexRule,
} from './types'
import { isPresetData, SPECIAL_RELATIVE_TEMPLATES } from './types'

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
 * Helpers: normalize content field presence
 * Rule: For all items except SPECIAL_RELATIVE_TEMPLATES, ensure content: '' exists.
 */
function isSpecialRelative(id: string): boolean {
  try {
    return SPECIAL_RELATIVE_TEMPLATES.some(t => t.identifier === id)
  } catch {
    return false
  }
}

function normalizePromptItem(item: PromptItem): PromptItem {
  const x: any = item as any
  if (x && x.position === 'relative') {
    if (!isSpecialRelative(x.identifier)) {
      if (!('content' in x) || x.content == null) x.content = ''
    }
  } else if (x && x.position === 'in-chat') {
    if (!('content' in x) || x.content == null) x.content = ''
  }
  return item
}

function normalizeRegexRule(r: any): void {
  if (!r || typeof r !== 'object') return
  if (typeof r.id !== 'string') r.id = String(r.id ?? '')
  if (typeof r.name !== 'string') r.name = String(r.name ?? r.id ?? '')
  r.enabled = r.enabled === true ? true : r.enabled === false ? false : true
  if (typeof r.find_regex !== 'string') r.find_regex = String(r.find_regex ?? '')
  if (typeof r.replace_regex !== 'string') r.replace_regex = String(r.replace_regex ?? '')
  if (!Array.isArray(r.targets)) r.targets = []
  if (typeof r.placement !== 'string') r.placement = 'after_macro'
  if (!Array.isArray(r.views)) r.views = []
  if (r.min_depth != null) r.min_depth = Number(r.min_depth)
  if (r.max_depth != null) r.max_depth = Number(r.max_depth)
  if (r.description != null && typeof r.description !== 'string') r.description = String(r.description)
}

function normalizePresetData(data: PresetData): boolean {
  if (!data) return false
  let changed = false

  // prompts
  if (Array.isArray((data as any).prompts)) {
    for (const p of (data as any).prompts as any[]) {
      const had = Object.prototype.hasOwnProperty.call(p, 'content')
      const before = p.content
      normalizePromptItem(p as any)
      if (!had || before !== p.content) changed = true
    }
  } else {
    ;(data as any).prompts = []
    changed = true
  }

  // regex_rules
  if (!Array.isArray((data as any).regex_rules)) {
    ;(data as any).regex_rules = []
    changed = true
  } else {
    for (const r of (data as any).regex_rules as any[]) {
      const before = JSON.stringify(r)
      normalizeRegexRule(r)
      if (JSON.stringify(r) !== before) changed = true
    }
  }

  return changed
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
    regexRules(): RegexRule[] {
      return (((this as any).activeData?.regex_rules ?? []) as any[]) as RegexRule[]
    },
  },

  actions: {
    load() {
      if (this.loaded) return
      const { files, activeName } = loadFromLocal()
      // basic shape guard (do not strictly validate every file for performance)
      this.files = Array.isArray(files) ? files.filter(f => f && f.name && f.data) : []
      // normalize content fields for non-special items
      let changed = false
      for (const f of this.files) {
        try {
          if (f?.data) {
            if (normalizePresetData(f.data)) changed = true
          }
        } catch {}
      }
      this.activeName = typeof activeName === 'string' ? activeName : (this.files[0]?.name ?? null)
      this.loaded = true
      if (changed) this.persist()
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
      try { normalizePresetData(entry.data) } catch {}
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
      // 规范化导入数据：除一次性 Relative 外，其余条目必须含 content 字段（空则为 ""）
      try { normalizePresetData(json as PresetData) } catch {}
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
      const fixed = normalizePromptItem(next)
      const idx = data.prompts.findIndex(p => p.identifier === fixed.identifier)
      if (idx >= 0) {
        // replace reference to keep reactivity
        data.prompts.splice(idx, 1, fixed as any)
        this.persist()
      }
    },

    addPrompt(item: PromptItem) {
      const data = this.activeData
      if (!data) return
      const normalized = normalizePromptItem(item)
      // 新增放到队首
      data.prompts.unshift(normalized as any)
      // 若为 in-chat，规范化顺序字段，使其按当前出现顺序从 0 开始递增
      if ((normalized as any).position === 'in-chat') {
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
     * Regex Rules CRUD
     */
    addRegexRule(rule: RegexRule) {
      const data = this.activeData
      if (!data) return
      if (!Array.isArray(data.regex_rules)) data.regex_rules = []
      const i = data.regex_rules.findIndex(r => r && r.id === rule.id)
      if (i >= 0) {
        data.regex_rules.splice(i, 1, rule as any)
      } else {
        data.regex_rules.unshift(rule as any)
      }
      this.persist()
    },

    replaceRegexRule(updated: RegexRule) {
      const data = this.activeData
      if (!data || !Array.isArray(data.regex_rules)) return
      const idx = data.regex_rules.findIndex(r => r && r.id === updated.id)
      if (idx >= 0) {
        data.regex_rules.splice(idx, 1, updated as any)
        this.persist()
      }
    },

    removeRegexRule(id: string) {
      const data = this.activeData
      if (!data || !Array.isArray(data.regex_rules)) return
      const idx = data.regex_rules.findIndex(r => r && r.id === id)
      if (idx >= 0) {
        data.regex_rules.splice(idx, 1)
        this.persist()
      }
    },

    /**
     * Replace entire regex_rules list (used by Regex panel import)
     */
    setRegexRules(rules: RegexRule[]) {
      const data = this.activeData
      if (!data) return
      const list: any[] = Array.isArray(rules) ? rules.map(r => ({ ...(r as any) })) : []
      for (const r of list) {
        try { normalizeRegexRule(r) } catch {}
      }
      data.regex_rules = list as any
      this.persist()
    },

    /**
     * Reorder regex_rules by provided id order (ids not present keep original order at tail)
     */
    reorderRegexRules(orderedIds: string[]) {
      const data = this.activeData
      if (!data || !Array.isArray(data.regex_rules)) return
      const items = data.regex_rules
      const idSet = new Set(items.map(i => i.id))
      const normalized = (orderedIds || []).filter((id): id is string => !!id && idSet.has(id))
      const missing = items.map(i => i.id).filter(id => !normalized.includes(id))
      const finalIds = normalized.concat(missing)
      const map = new Map<string, RegexRule>(items.map(i => [i.id, i as RegexRule]))
      const next: RegexRule[] = []
      for (const id of finalIds) {
        const x = map.get(id)
        if (x) next.push(x)
      }
      data.regex_rules.splice(0, data.regex_rules.length, ...(next as any))
      this.persist()
    },

    /**
     * Export regex_rules array only (array schema like backend .../regex_rules/*.json)
     */
    exportRegexRules(): { filename: string; json: string } | null {
      const data = this.activeData
      if (!data) return null
      const filename = 'regex_rules.json'
      const json = JSON.stringify(data.regex_rules ?? [], null, 2)
      return { filename, json }
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