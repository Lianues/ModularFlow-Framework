import { defineStore } from 'pinia'

type MsgRole = 'system' | 'user' | 'assistant'
export interface OpenAIMessage {
  role: MsgRole
  content: string
}

export interface HistoryFile {
  name: string
  enabled: boolean
  data: any
}

const STORAGE_KEY = 'prompt_editor_history_files'

function clone<T>(x: T): T {
  return x == null ? (x as any) : JSON.parse(JSON.stringify(x))
}

function loadLocal(): { files: HistoryFile[]; activeName: string | null } {
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

function saveLocal(payload: { files: HistoryFile[]; activeName: string | null }) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  } catch {}
}

/**
 * 从对话历史 JSON 推导 OpenAI messages 数组
 * 兼容几种常见形态：
 * - chat-branches V2：{ schema:{name:'chat-branches'}, nodes, children, active_path }
 * - { messages:[{role, content}]} 或 { openai_messages: [...] }
 * - fallback：[]
 */
export function deriveMessagesFromHistory(doc: any): OpenAIMessage[] {
  try {
    if (!doc || typeof doc !== 'object') return []

    // 1) 显式 messages/openai_messages
    if (Array.isArray(doc.messages)) {
      return (doc.messages as any[])
        .map((m) => ({
          role: (m?.role ?? 'user') as MsgRole,
          content: String(m?.content ?? ''),
        }))
        .filter((m) => m.content != null)
    }
    if (Array.isArray(doc.openai_messages)) {
      return (doc.openai_messages as any[])
        .map((m) => ({
          role: (m?.role ?? 'user') as MsgRole,
          content: String(m?.content ?? ''),
        }))
        .filter((m) => m.content != null)
    }

    // 2) chat-branches v2
    const isBranches =
      doc?.schema?.name === 'chat-branches' &&
      doc?.nodes &&
      doc?.children &&
      (doc?.active_path || doc?.root)

    if (isBranches) {
      const nodes = doc.nodes || {}
      const activePath: string[] = Array.isArray(doc.active_path) ? doc.active_path.slice() : []
      const root: string = doc.root || (activePath.length ? activePath[0] : null)

      const path: string[] = activePath.length
        ? activePath
        : root
        ? [root]
        : []

      const out: OpenAIMessage[] = []
      for (const nid of path) {
        const node = nodes[nid]
        if (!node) continue
        const role = node.role as MsgRole
        if (role === 'system' || role === 'user' || role === 'assistant') {
          out.push({ role, content: String(node.content ?? '') })
        }
      }
      return out
    }

    // fallback
    return []
  } catch {
    return []
  }
}

export const useHistoryStore = defineStore('history', {
  state: () => ({
    files: [] as HistoryFile[],
    activeName: null as string | null,
    loaded: false,
  }),

  getters: {
    activeIndex(state): number {
      if (!state.activeName) return -1
      return state.files.findIndex((f) => f.name === state.activeName)
    },
    activeFile(state): HistoryFile | null {
      const idx = (this as any).activeIndex as number
      return idx >= 0 ? state.files[idx] ?? null : null
    },
    activeData(): any | null {
      return (this as any).activeFile?.data ?? null
    },
    messages(): OpenAIMessage[] {
      const data = (this as any).activeData
      return deriveMessagesFromHistory(data)
    },
  },

  actions: {
    load() {
      if (this.loaded) return
      const { files, activeName } = loadLocal()
      // 仅做轻度形状校验
      this.files = Array.isArray(files) ? files.filter((f) => f && f.name) : []
      this.activeName = typeof activeName === 'string' ? activeName : (this.files[0]?.name ?? null)
      this.loaded = true
    },

    persist() {
      saveLocal({ files: this.files, activeName: this.activeName })
    },

    setActive(name: string) {
      if (this.files.some((f) => f.name === name)) {
        this.activeName = name
        this.persist()
      }
    },

    toggleEnable(name: string) {
      const f = this.files.find((x) => x.name === name)
      if (f) {
        f.enabled = !f.enabled
        this.persist()
      }
    },

    deleteFile(name: string) {
      const idx = this.files.findIndex((x) => x.name === name)
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

    upsertFile(entry: HistoryFile) {
      const idx = this.files.findIndex((f) => f.name === entry.name)
      const rec: HistoryFile = {
        name: entry.name,
        enabled: entry.enabled ?? true,
        data: clone(entry.data),
      }
      if (idx >= 0) this.files.splice(idx, 1, rec)
      else this.files.unshift(rec)
      this.activeName = rec.name
      this.persist()
    },

    async importFromFile(file: File): Promise<void> {
      const text = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onerror = () => reject(new Error('read error'))
        reader.onload = () => resolve(String(reader.result ?? ''))
        reader.readAsText(file)
      })
      let json: any
      try {
        const clean = text.replace(/\uFEFF/g, '')
        json = JSON.parse(clean)
      } catch {
        throw new Error('JSON 解析失败')
      }
      const entry: HistoryFile = { name: file.name, enabled: true, data: json }
      this.upsertFile(entry)
    },

    setDoc(json: any, fileName?: string) {
      const name = fileName ?? this.activeName ?? 'History.json'
      const idx = this.files.findIndex((f) => f.name === name)
      const rec: HistoryFile = {
        name,
        enabled: true,
        data: clone(json),
      }
      if (idx >= 0) this.files.splice(idx, 1, rec)
      else this.files.unshift(rec)
      this.activeName = name
      this.persist()
    },

    exportActive(): { filename: string; json: string } | null {
      const file = this.activeFile
      if (!file) return null
      const filename = file.name.endsWith('.json') ? file.name : `${file.name}.json`
      const json = JSON.stringify(file.data ?? {}, null, 2)
      return { filename, json }
    },
  },
})