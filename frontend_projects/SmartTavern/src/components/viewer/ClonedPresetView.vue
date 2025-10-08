<script setup>
import { ref, reactive, computed, onMounted, nextTick, watchEffect } from 'vue'

/**
 * 目标
 * - 将 PromptEditor 的主预设编辑面板（PresetView）布局与样式迁移到 SmartTavern 内部使用
 * - 不依赖 Pinia/外部 Store，改为本地 JSON 演示数据驱动
 * - 保持 UI 样式一致（类名、结构尽量一致），支持基本的新增/编辑/拖拽排序占位逻辑
 * - 后续可以替换为真实数据流
 */

/* ---------------------- 本地演示 JSON（可被外部 JSON 覆盖） ---------------------- */
const demoData = reactive({
  fileName: 'PresetDemo.json',
  setting: {
    temperature: 1.0,
    frequency_penalty: 0,
    presence_penalty: 0,
    top_p: 1.0,
    top_k: 0,
    max_context: 4095,
    max_tokens: 300,
    stream: true,
  },
  prompts: [
    // relative（一次性组件示例：不含 content）
    { identifier: 'charBefore', name: 'char Before', enabled: null, role: 'system', position: 'relative' },
    // relative（自定义条目：含 content）
    { identifier: 'rb-1', name: '系统介绍', enabled: true, role: 'system', position: 'relative', content: '这是系统层面的介绍段落。' },

    // in-chat 条目（必须含 content）
    { identifier: 'ic-1', name: '对话提示 A', enabled: true, role: 'system', position: 'in-chat', depth: 0, order: 0, content: '请保持礼貌且简洁。' },
    { identifier: 'ic-2', name: '对话提示 B', enabled: false, role: 'system', position: 'in-chat', depth: 0, order: 1, content: '尽量避免重复回答。' },
  ],
  regex_rules: [
    { id: 'remove_xml', name: '移除 XML 标签', enabled: true, find_regex: '<[^>]+>', replace_regex: '', targets: [], placement: 'after_macro', views: [] },
    { id: 'trim_ws', name: '移除尾随空白', enabled: true, find_regex: '\\s+$', replace_regex: '', targets: [], placement: 'after_macro', views: [] },
  ],
})

/* 可选：尝试加载外部演示 JSON（vite 支持 JSON import）。若找不到则保持内置数据。 */
async function tryLoadExternalJson() {
  try {
    const mod = await import('@/data/preset_demo.json')
    const ext = (mod && (mod.default || mod)) || null
    if (ext && typeof ext === 'object') {
      // 浅拷贝覆盖（演示用）
      if (typeof ext.fileName === 'string') demoData.fileName = ext.fileName
      if (ext.setting && typeof ext.setting === 'object') Object.assign(demoData.setting, ext.setting || {})
      if (Array.isArray(ext.prompts)) {
        demoData.prompts.splice(0, demoData.prompts.length, ...ext.prompts.map(x => ({ ...(x || {}) })))
      }
      if (Array.isArray(ext.regex_rules)) {
        demoData.regex_rules.splice(0, demoData.regex_rules.length, ...ext.regex_rules.map(x => ({ ...(x || {}) })))
      }
    }
  } catch {
    // ignore (未创建文件时不报错)
  }
}

/* ---------------------- 面板开合状态（本地存储） ---------------------- */
const PANEL_STATE_KEY = 'preset_viewer_ui_panels'
const apiOpen = ref(true)
const promptsOpen = ref(true)
const regexOpen = ref(true)
const relativeOpen = ref(true)
const inChatOpen = ref(true)

function loadPanelStates() {
  try {
    const raw = localStorage.getItem(PANEL_STATE_KEY)
    if (raw) {
      const obj = JSON.parse(raw)
      if (typeof obj.apiOpen === 'boolean') apiOpen.value = obj.apiOpen
      if (typeof obj.promptsOpen === 'boolean') promptsOpen.value = obj.promptsOpen
      if (typeof obj.regexOpen === 'boolean') regexOpen.value = obj.regexOpen
      if (typeof obj.relativeOpen === 'boolean') relativeOpen.value = obj.relativeOpen
      if (typeof obj.inChatOpen === 'boolean') inChatOpen.value = obj.inChatOpen
    }
  } catch {}
}
function savePanelStates() {
  try {
    localStorage.setItem(
      PANEL_STATE_KEY,
      JSON.stringify({
        apiOpen: apiOpen.value,
        promptsOpen: promptsOpen.value,
        regexOpen: regexOpen.value,
        relativeOpen: relativeOpen.value,
        inChatOpen: inChatOpen.value,
      })
    )
  } catch {}
}

/* ---------------------- API 参数开关与编辑值（仅前端显示，不联通后端） ---------------------- */
const apiEnabled = ref(true)
const enableTemperature = ref(true)
const enableTopP = ref(true)
const enableTopK = ref(true)
const enableMaxContext = ref(true)
const enableMaxTokens = ref(true)
const enableStream = ref(true)
const enableFrequencyPenalty = ref(true)
const enablePresencePenalty = ref(true)

const temperature = ref(1.0)
const maxTokens = ref(300)
const stream = ref(true)
const topP = ref(1.0)
const frequencyPenalty = ref(0)
const presencePenalty = ref(0)
const topK = ref(0)
const maxContext = ref(4095)

/* ---------------------- 文件名重命名（演示） ---------------------- */
const fileTitle = ref('')
const renameError = ref(null)
function renamePresetFile() {
  renameError.value = null
  const nn = (fileTitle.value || '').trim()
  if (!nn) {
    renameError.value = '文件名不能为空'
    return
  }
  demoData.fileName = nn
}

/* ---------------------- 初始化 ---------------------- */
onMounted(async () => {
  loadPanelStates()
  // 将 setting 映射到 UI
  try {
    const s = demoData.setting
    temperature.value = Number(s.temperature ?? 1)
    topP.value = Number(s.top_p ?? 1)
    topK.value = Number(s.top_k ?? 0)
    maxContext.value = Number(s.max_context ?? 4095)
    maxTokens.value = Number(s.max_tokens ?? 300)
    stream.value = !!s.stream
    frequencyPenalty.value = Number(s.frequency_penalty ?? 0)
    presencePenalty.value = Number(s.presence_penalty ?? 0)
  } catch {}
  fileTitle.value = demoData.fileName || ''
  await tryLoadExternalJson()
  await nextTick()
  window?.lucide?.createIcons?.()
})

/* 自动保存开合状态 */
watchEffect(() => {
  savePanelStates()
})

/* ---------------------- 提示词条目逻辑（本地数组） ---------------------- */
const relativePrompts = computed(() => demoData.prompts.filter(p => p.position === 'relative'))
const inChatPrompts = computed(() => demoData.prompts.filter(p => p.position === 'in-chat'))

// 一次性 Relative 组件清单（与 PromptEditor 保持一致 ID/名称）
const SPECIAL_RELATIVE_TEMPLATES = [
  { identifier: 'charBefore', name: 'char Before', enabled: null, role: 'system', position: 'relative' },
  { identifier: 'personaDescription', name: 'Persona Description', enabled: false, role: 'system', position: 'relative' },
  { identifier: 'charDescription', name: 'Char Description', enabled: true, role: 'system', position: 'relative' },
  { identifier: 'charAfter', name: 'char After', enabled: true, role: 'system', position: 'relative' },
  { identifier: 'chatHistory', name: 'Chat History', enabled: true, role: 'system', position: 'relative' },
]

// 可选特别模板下拉框
const specialSelect = ref('')
const availableSpecials = computed(() =>
  SPECIAL_RELATIVE_TEMPLATES.filter(t => !relativePrompts.value.some(p => p.identifier === t.identifier))
)
const reservedIdSet = computed(() => new Set(SPECIAL_RELATIVE_TEMPLATES.map(t => t.identifier)))
const reservedNameSet = computed(() => new Set(SPECIAL_RELATIVE_TEMPLATES.map(t => t.name)))

// 自定义 Relative 新增
const newRelId = ref('')
const newRelName = ref('')
const relError = ref(null)

async function addSelectedSpecial() {
  relError.value = null
  const sel = specialSelect.value
  if (!sel) return
  const tpl = SPECIAL_RELATIVE_TEMPLATES.find(t => t.identifier === sel)
  if (!tpl) return
  if (relativePrompts.value.some(p => p.identifier === tpl.identifier)) {
    relError.value = '该一次性组件已存在'
    return
  }
  demoData.prompts.unshift({ ...tpl })
  specialSelect.value = ''
  await nextTick()
  window?.lucide?.createIcons?.()
}

async function addCustomRelative() {
  relError.value = null
  const id = newRelId.value.trim()
  const name = newRelName.value.trim()
  if (!id) { relError.value = '请填写 id'; return }
  if (!name) { relError.value = '请填写 名称'; return }
  if (reservedIdSet.value.has(id) || reservedNameSet.value.has(name)) {
    relError.value = 'id 或 名称 与保留组件重复'
    return
  }
  if (relativePrompts.value.some(p => p.identifier === id)) {
    relError.value = 'id 已存在'
    return
  }
  if (relativePrompts.value.some(p => p.name === name)) {
    relError.value = '名称已存在'
    return
  }
  demoData.prompts.unshift({
    identifier: id,
    name,
    enabled: null,
    role: 'system',
    position: 'relative',
    content: '',
  })
  newRelId.value = ''
  newRelName.value = ''
  await nextTick()
  window?.lucide?.createIcons?.()
}

// In-Chat 新增
const newChatId = ref('')
const newChatName = ref('')
const chatError = ref(null)

async function addCustomInChat() {
  chatError.value = null
  const id = newChatId.value.trim()
  const name = newChatName.value.trim()
  if (!id) { chatError.value = '请填写 id'; return }
  if (!name) { chatError.value = '请填写 名称'; return }
  if (demoData.prompts.some(p => p.identifier === id)) { chatError.value = 'id 已存在'; return }
  if (inChatPrompts.value.some(p => p.name === name)) { chatError.value = '名称已存在'; return }

  demoData.prompts.unshift({
    identifier: id,
    name,
    enabled: true,
    role: 'system',
    position: 'in-chat',
    depth: 0,
    order: 0,
    content: '',
  })
  // 规范化顺序字段
  let k = 0
  for (const p of demoData.prompts) {
    if (p.position === 'in-chat') p.order = k++
  }
  newChatId.value = ''
  newChatName.value = ''
  await nextTick()
  window?.lucide?.createIcons?.()
}

/* ---------------------- 提示词卡片（内联版本，复用样式） ---------------------- */
function enabledLabel(v) { return v === true ? '已启用' : v === false ? '未启用' : '未设置' }

function startEdit(item, stateMap) {
  const key = item.identifier
  stateMap[key] = {
    editing: true,
    name: item.name,
    enabled: item.enabled === true ? 'true' : item.enabled === false ? 'false' : 'null',
    role: item.role,
    depth: item.position === 'in-chat' ? (item.depth || 0) : 0,
    order: item.position === 'in-chat' ? (item.order || 0) : 0,
    content: 'content' in item ? (item.content || '') : '',
  }
}
function cancelEdit(item, stateMap) {
  const key = item.identifier
  stateMap[key] = { editing: false }
}
function saveEdit(item, stateMap) {
  const key = item.identifier
  const s = stateMap[key]
  if (!s) return
  item.name = s.name
  item.enabled = s.enabled === 'true' ? true : s.enabled === 'false' ? false : null
  item.role = s.role
  if (item.position === 'in-chat') {
    item.depth = Number(s.depth || 0)
    item.order = Number(s.order || 0)
  }
  if ('content' in item) {
    item.content = s.content
  } else {
    // 一次性 relative（无 content 字段）保持不变
  }
  stateMap[key] = { editing: false }
}
function removeItem(identifier) {
  const idx = demoData.prompts.findIndex(p => p.identifier === identifier)
  if (idx >= 0) demoData.prompts.splice(idx, 1)
}
const cardState = reactive({}) // identifier -> { editing, name, enabled, role, depth, order, content }

/* 拖拽排序（Relative / In-Chat，黑线预览） */
const dragging = ref(null) // { position, id }
const dragOverId = ref(null)
const dragOverBefore = ref(true)

function onDragStart(position, id, ev) {
  dragging.value = { position, id }
  try {
    ev.dataTransfer?.setData('text/plain', id)
    ev.dataTransfer.effectAllowed = 'move'
    const canvas = document.createElement('canvas')
    canvas.width = 1; canvas.height = 1
    ev.dataTransfer?.setDragImage(canvas, 0, 0)
  } catch {}
}
function onDragOver(position, overId, ev) {
  if (!dragging.value || dragging.value.position !== position) return
  ev.preventDefault()
  try {
    const el = ev.currentTarget
    if (el) {
      const rect = el.getBoundingClientRect()
      const mid = rect.top + rect.height / 2
      dragOverBefore.value = ev.clientY < mid
    }
  } catch {}
  dragOverId.value = overId
}
function onDrop(position, overId, ev) {
  if (!dragging.value || dragging.value.position !== position) return
  ev.preventDefault()
  const dId = dragging.value.id

  const list = demoData.prompts.filter(p => p.position === position)
  let ids = list.map(i => i.identifier)
  const fromIdx = ids.indexOf(dId)
  if (fromIdx < 0) return
  ids.splice(fromIdx, 1)
  if (overId && overId !== dId) {
    const toIdx = ids.indexOf(overId)
    let insertIdx = toIdx < 0 ? ids.length : toIdx + (dragOverBefore.value ? 0 : 1)
    if (insertIdx < 0) insertIdx = 0
    if (insertIdx > ids.length) insertIdx = ids.length
    ids.splice(insertIdx, 0, dId)
  } else {
    ids.push(dId)
  }

  // 写回 demoData.prompts 中对应 position 的顺序
  const map = new Map(list.map(i => [i.identifier, i]))
  let writeIdx = 0
  for (let i = 0; i < demoData.prompts.length; i++) {
    const cur = demoData.prompts[i]
    if (cur.position === position) {
      if (writeIdx >= ids.length) continue
      const id = ids[writeIdx++]
      const next = map.get(id)
      if (next) demoData.prompts.splice(i, 1, next)
    }
  }
  if (position === 'in-chat') {
    let k = 0
    for (const p of demoData.prompts) {
      if (p.position === 'in-chat') p.order = k++
    }
  }

  dragging.value = null
  dragOverId.value = null
  window?.lucide?.createIcons?.()
}
function onDropEnd(position, ev) {
  onDrop(position, null, ev)
}
function onDragEnd() {
  dragging.value = null
  dragOverId.value = null
}

/* ---------------------- 正则规则（本地数组） ---------------------- */
const newRegexId = ref('')
const newRegexName = ref('')
const regexError = ref(null)

async function addCustomRegex() {
  regexError.value = null
  const id = newRegexId.value.trim()
  const name = newRegexName.value.trim()
  if (!id) { regexError.value = '请填写 id'; return }
  if (!name) { regexError.value = '请填写 名称'; return }
  if (demoData.regex_rules.some(r => r.id === id)) {
    regexError.value = 'id 已存在'
    return
  }
  demoData.regex_rules.unshift({
    id, name, enabled: true,
    find_regex: '', replace_regex: '',
    targets: [], placement: 'after_macro', views: [],
  })
  newRegexId.value = ''
  newRegexName.value = ''
  await nextTick()
  window?.lucide?.createIcons?.()
}

/* 正则拖拽（可选，简化版：仅末尾放置） */
const draggingRegex = ref(null)
const dragOverRegexId = ref(null)
const dragOverRegexBefore = ref(true)

function onRegexDragStart(id, ev) {
  draggingRegex.value = id
  try {
    ev.dataTransfer?.setData('text/plain', id)
    ev.dataTransfer.effectAllowed = 'move'
    const canvas = document.createElement('canvas')
    canvas.width = 1; canvas.height = 1
    ev.dataTransfer?.setDragImage(canvas, 0, 0)
  } catch {}
}
function onRegexDragOver(overId, ev) {
  if (!draggingRegex.value) return
  ev.preventDefault()
  try {
    const el = ev.currentTarget
    if (el) {
      const rect = el.getBoundingClientRect()
      const mid = rect.top + rect.height / 2
      dragOverRegexBefore.value = ev.clientY < mid
    }
  } catch {}
  dragOverRegexId.value = overId
}
function onRegexDrop(overId, ev) {
  if (!draggingRegex.value) return
  ev.preventDefault()
  const dId = draggingRegex.value
  const items = [...demoData.regex_rules]
  const ids = items.map(i => i.id)
  const fromIdx = ids.indexOf(dId)
  if (fromIdx < 0) return
  ids.splice(fromIdx, 1)
  if (overId && overId !== dId) {
    const toIdx = ids.indexOf(overId)
    let insertIdx = toIdx < 0 ? ids.length : toIdx + (dragOverRegexBefore.value ? 0 : 1)
    if (insertIdx < 0) insertIdx = 0
    if (insertIdx > ids.length) insertIdx = ids.length
    ids.splice(insertIdx, 0, dId)
  } else {
    ids.push(dId)
  }
  const map = new Map(items.map(i => [i.id, i]))
  const next = []
  for (const id of ids) {
    const x = map.get(id)
    if (x) next.push(x)
  }
  demoData.regex_rules.splice(0, demoData.regex_rules.length, ...next)
  draggingRegex.value = null
  dragOverRegexId.value = null
  window?.lucide?.createIcons?.()
}
function onRegexDropEnd(ev) { onRegexDrop(null, ev) }
function onRegexDragEnd() { draggingRegex.value = null; dragOverRegexId.value = null }
</script>

<template>
  <!-- 仅 Preset 视图内容（不包含三栏布局与顶部栏） -->
  <section class="space-y-6">
    <!-- 页面标题 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <i data-lucide="settings-2" class="w-5 h-5 text-black"></i>
          <h2>预设编辑器</h2>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="fileTitle"
            placeholder="文件名.json"
            class="w-56 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
            @keyup.enter="renamePresetFile"
            @blur="renamePresetFile"
          />
          <button
            class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-sm hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
            @click="renamePresetFile"
          >重命名</button>
        </div>
      </div>
      <p class="mt-2 text-xs text-black/60">本页为 UI 演示，保存与联通待后续</p>
      <p v-if="renameError" class="text-xs text-red-600 mt-1">* {{ renameError }}</p>
    </div>

    <!-- API 配置 -->
    <div class="bg-white rounded-4 border border-gray-200 transition-all duration-200 ease-soft hover:shadow-elevate">
      <button
        type="button"
        class="w-full flex items-center justify-between px-5 py-3 rounded-4"
        @click="apiOpen = !apiOpen"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="server-cog" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">API 配置</span>
        </div>
        <i
          data-lucide="chevron-down"
          class="w-4 h-4 text-black transition-transform duration-200 ease-soft"
          :class="apiOpen ? 'rotate-180' : ''"
        />
      </button>

      <div v-show="apiOpen" class="border-t border-gray-200 p-5">
        <!-- 全局启用开关 -->
        <div class="mb-4 flex items-center justify-between">
          <div class="text-sm font-medium text-black">启用 API 配置</div>
          <label class="inline-flex items-center gap-2 select-none">
            <input
              type="checkbox"
              v-model="apiEnabled"
              class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
            />
            <span class="text-sm text-black/80">{{ apiEnabled ? '已启用' : '未启用' }}</span>
          </label>
        </div>

        <!-- 参数编辑 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- temperature -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Temperature</label>
              <label class="inline-flex items-center gap-2 select-none">
                <input type="checkbox" v-model="enableTemperature" class="w-4 h-4 border border-gray-400 rounded-4 accent-black" />
                <span class="text-xs text-black/60">启用</span>
              </label>
            </div>
            <input
              type="number" min="0" max="2" step="0.01"
              v-model.number="temperature"
              :disabled="!apiEnabled || !enableTemperature"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
              placeholder="0.00"
            />
            <div class="text-xs text-black/60 mt-1">当前：{{ Number(temperature ?? 0).toFixed(2) }}</div>
          </div>

          <!-- top_p -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Top P</label>
              <label class="inline-flex items-center gap-2 select-none">
                <input type="checkbox" v-model="enableTopP" class="w-4 h-4 border border-gray-400 rounded-4 accent-black" />
                <span class="text-xs text-black/60">启用</span>
              </label>
            </div>
            <input
              type="number" min="0" max="1" step="0.01"
              v-model.number="topP"
              :disabled="!apiEnabled || !enableTopP"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
              placeholder="0.00"
            />
            <div class="text-xs text-black/60 mt-1">当前：{{ Number(topP ?? 0).toFixed(2) }}</div>
          </div>

          <!-- top_k -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Top K</label>
              <label class="inline-flex items-center gap-2 select-none">
                <input type="checkbox" v-model="enableTopK" class="w-4 h-4 border border-gray-400 rounded-4 accent-black" />
                <span class="text-xs text-black/60">启用</span>
              </label>
            </div>
            <input
              type="number" min="0"
              v-model.number="topK"
              :disabled="!apiEnabled || !enableTopK"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
            />
          </div>

          <!-- max_context -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Max Context</label>
              <label class="inline-flex items-center gap-2 select-none">
                <input type="checkbox" v-model="enableMaxContext" class="w-4 h-4 border border-gray-400 rounded-4 accent-black" />
                <span class="text-xs text-black/60">启用</span>
              </label>
            </div>
            <input
              type="number" min="1"
              v-model.number="maxContext"
              :disabled="!apiEnabled || !enableMaxContext"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
            />
          </div>

          <!-- max_tokens -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Max Tokens</label>
              <label class="inline-flex items-center gap-2 select-none">
                <input type="checkbox" v-model="enableMaxTokens" class="w-4 h-4 border border-gray-400 rounded-4 accent-black" />
                <span class="text-xs text-black/60">启用</span>
              </label>
            </div>
            <input
              type="number" min="1"
              v-model.number="maxTokens"
              :disabled="!apiEnabled || !enableMaxTokens"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
            />
          </div>

          <!-- stream -->
          <div class="flex items-end">
            <div class="w-full">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-medium text-black">流式输出（stream）</label>
                <label class="inline-flex items-center gap-2 select-none">
                  <input type="checkbox" v-model="enableStream" class="w-4 h-4 border border-gray-400 rounded-4 accent-black" />
                  <span class="text-xs text-black/60">启用</span>
                </label>
              </div>
              <label class="inline-flex items-center space-x-2">
                <input
                  type="checkbox"
                  v-model="stream"
                  :disabled="!apiEnabled || !enableStream"
                  class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                />
                <span class="text-sm text-black/80">开启</span>
              </label>
            </div>
          </div>

          <!-- frequency_penalty -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Frequency Penalty</label>
              <label class="inline-flex items-center gap-2 select-none">
                <input type="checkbox" v-model="enableFrequencyPenalty" class="w-4 h-4 border border-gray-400 rounded-4 accent-black" />
                <span class="text-xs text-black/60">启用</span>
              </label>
            </div>
            <input
              type="number" min="0"
              v-model.number="frequencyPenalty"
              :disabled="!apiEnabled || !enableFrequencyPenalty"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
            />
          </div>

          <!-- presence_penalty -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Presence Penalty</label>
              <label class="inline-flex items-center gap-2 select-none">
                <input type="checkbox" v-model="enablePresencePenalty" class="w-4 h-4 border border-gray-400 rounded-4 accent-black" />
                <span class="text-xs text-black/60">启用</span>
              </label>
            </div>
            <input
              type="number" min="0"
              v-model.number="presencePenalty"
              :disabled="!apiEnabled || !enablePresencePenalty"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 提示词编辑 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <button
        type="button"
        class="w-full flex items-center justify-between mb-4 rounded-4"
        @click="promptsOpen = !promptsOpen"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="edit-3" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">提示词编辑</span>
        </div>
        <i
          data-lucide="chevron-down"
          class="w-4 h-4 text-black transition-transform duration-200 ease-soft"
          :class="promptsOpen ? 'rotate-180' : ''"
        />
      </button>

      <div v-show="promptsOpen" class="grid grid-cols-1 gap-6">
        <div class="space-y-4">
          <div class="border border-gray-200 rounded-4 p-4 transition-all duration-200 ease-soft hover:shadow-elevate">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-2">
                <i data-lucide="list" class="w-4 h-4 text-black"></i>
                <span class="text-sm font-medium text-black">提示词条目</span>
              </div>
            </div>

            <div class="space-y-6">
              <!-- Relative -->
              <div>
                <button
                  type="button"
                  class="w-full flex items-center justify-between mb-2 rounded-4"
                  @click="relativeOpen = !relativeOpen"
                >
                  <div class="flex items-center gap-2">
                    <i data-lucide="layers" class="w-4 h-4 text-black"></i>
                    <span class="text-sm font-medium text-black">Relative 条目</span>
                  </div>
                  <i
                    data-lucide="chevron-down"
                    class="w-4 h-4 text-black transition-transform duration-200 ease-soft"
                    :class="relativeOpen ? 'rotate-180' : ''"
                  />
                </button>

                <div v-show="relativeOpen" class="space-y-2 mb-2">
                  <div class="grid grid-cols-1 lg:grid-cols-2 gap-2">
                    <!-- 一次性组件 -->
                    <div class="flex items-center gap-2">
                      <select
                        v-model="specialSelect"
                        class="min-w-[220px] px-3 py-2 border border-gray-300 rounded-4 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
                      >
                        <option value="" disabled>选择一次性组件</option>
                        <option
                          v-for="sp in availableSpecials"
                          :key="sp.identifier"
                          :value="sp.identifier"
                        >
                          {{ sp.name }} (id: {{ sp.identifier }})
                        </option>
                      </select>
                      <button
                        class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs disabled:opacity-50"
                        :disabled="!specialSelect"
                        @click="addSelectedSpecial"
                      >
                        添加特殊
                      </button>
                    </div>

                    <!-- 自定义 Relative -->
                    <div class="flex items-center gap-2 justify-end">
                      <input
                        v-model="newRelId"
                        placeholder="id"
                        class="w-32 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
                      />
                      <input
                        v-model="newRelName"
                        placeholder="名称"
                        class="w-40 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
                      />
                      <button
                        class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                        @click="addCustomRelative"
                      >
                        添加
                      </button>
                    </div>
                  </div>
                  <p v-if="relError" class="text-xs text-red-600">* {{ relError }}</p>
                </div>

                <!-- Relative 列表 -->
                <div v-show="relativeOpen" class="space-y-2">
                  <div
                    v-for="it in relativePrompts"
                    :key="it.identifier"
                    class="flex items-stretch gap-2 group draglist-item"
                    :class="{
                      'dragging-item': dragging && dragging.id === it.identifier && dragging.position === 'relative',
                      'drag-over-top': dragging && dragOverId === it.identifier && dragging.position === 'relative' && dragOverBefore,
                      'drag-over-bottom': dragging && dragOverId === it.identifier && dragging.position === 'relative' && !dragOverBefore
                    }"
                    @dragover.prevent="onDragOver('relative', it.identifier, $event)"
                    @drop.prevent="onDrop('relative', it.identifier, $event)"
                  >
                    <div
                      class="w-6 flex items-center justify-center select-none cursor-grab active:cursor-grabbing"
                      draggable="true"
                      @dragstart="onDragStart('relative', it.identifier, $event)"
                      @dragend="onDragEnd"
                      title="拖拽排序"
                    >
                      <i data-lucide="grip-vertical" class="icon-grip w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
                    </div>

                    <div class="flex-1">
                      <!-- 卡片（内联编辑） -->
                      <div class="border border-gray-200 rounded-4 p-3 bg-white transition-all duration-200 ease-soft hover:shadow-elevate">
                        <div class="flex items-center justify-between">
                          <div class="text-sm flex items-center gap-2">
                            <span class="font-medium">{{ it.name }}</span>
                          </div>
                          <div class="flex items-center gap-2">
                            <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ it.role }}</span>
                            <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ enabledLabel(it.enabled) }}</span>

                            <button
                              v-if="!(cardState[it.identifier]?.editing)"
                              class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                              @click="startEdit(it, cardState)"
                            >编辑</button>
                            <button
                              v-if="!(cardState[it.identifier]?.editing)"
                              class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                              @click="removeItem(it.identifier)"
                            >删除</button>

                            <template v-if="cardState[it.identifier]?.editing">
                              <button
                                class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                                @click="saveEdit(it, cardState)"
                              >保存</button>
                              <button
                                class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                                @click="cancelEdit(it, cardState)"
                              >取消</button>
                            </template>
                          </div>
                        </div>

                        <div class="text-xs text-black/60 mt-2">
                          <span class="font-mono">id:</span>
                          <span class="ml-1 font-mono">{{ it.identifier }}</span>
                        </div>

                        <!-- 查看模式：仅当存在 content 字段时显示 -->
                        <div v-if="!cardState[it.identifier]?.editing">
                          <div v-if="'content' in it" class="text-xs text-black/70 mt-2 leading-6 break-words">
                            {{ it.content }}
                          </div>
                        </div>

                        <!-- 编辑模式 -->
                        <div v-else class="mt-3 space-y-3">
                          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div>
                              <label class="block text-xs text-black/60 mb-1">名称</label>
                              <input
                                type="text"
                                v-model="cardState[it.identifier].name"
                                class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                              />
                            </div>
                            <div>
                              <label class="block text-xs text-black/60 mb-1">启用状态</label>
                              <select
                                v-model="cardState[it.identifier].enabled"
                                class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
                              >
                                <option value="true">已启用</option>
                                <option value="false">未启用</option>
                                <option value="null">未设置</option>
                              </select>
                            </div>
                            <div>
                              <label class="block text-xs text-black/60 mb-1">角色（role）</label>
                              <select
                                v-model="cardState[it.identifier].role"
                                class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
                              >
                                <option value="system">system</option>
                                <option value="user">user</option>
                                <option value="assistant">assistant</option>
                              </select>
                            </div>
                          </div>

                          <div v-if="'content' in it">
                            <label class="block text-xs text-black/60 mb-1">内容（content）</label>
                            <textarea
                              v-model="cardState[it.identifier].content"
                              rows="4"
                              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 列表末尾插入线 -->
                  <div
                    class="h-3 draglist-end"
                    :class="{ 'drag-over-end': dragging && dragOverId === null && dragging.position === 'relative' }"
                    @dragover.prevent="onDragOver('relative', null, $event)"
                    @drop.prevent="onDropEnd('relative', $event)"
                  />
                </div>
              </div>

              <!-- In-Chat -->
              <div>
                <button
                  type="button"
                  class="w-full flex items-center justify-between mb-2 rounded-4"
                  @click="inChatOpen = !inChatOpen"
                >
                  <div class="flex items-center gap-2">
                    <i data-lucide="message-square" class="w-4 h-4 text-black"></i>
                    <span class="text-sm font-medium text-black">In-Chat 条目</span>
                  </div>
                  <i
                    data-lucide="chevron-down"
                    class="w-4 h-4 text-black transition-transform duration-200 ease-soft"
                    :class="inChatOpen ? 'rotate-180' : ''"
                  />
                </button>

                <div v-show="inChatOpen" class="mb-2 flex justify-end">
                  <div class="flex items-center gap-2">
                    <input
                      v-model="newChatId"
                      placeholder="id"
                      class="w-32 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
                    />
                    <input
                      v-model="newChatName"
                      placeholder="名称"
                      class="w-40 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
                    />
                    <button
                      class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                      @click="addCustomInChat"
                    >
                      添加
                    </button>
                  </div>
                </div>
                <p v-show="inChatOpen && chatError" class="text-xs text-red-600">* {{ chatError }}</p>

                <div v-show="inChatOpen" class="space-y-2">
                  <div
                    v-for="it in inChatPrompts"
                    :key="it.identifier"
                    class="flex items-stretch gap-2 group draglist-item"
                    :class="{
                      'dragging-item': dragging && dragging.id === it.identifier && dragging.position === 'in-chat',
                      'drag-over-top': dragging && dragOverId === it.identifier && dragging.position === 'in-chat' && dragOverBefore,
                      'drag-over-bottom': dragging && dragOverId === it.identifier && dragging.position === 'in-chat' && !dragOverBefore
                    }"
                    @dragover.prevent="onDragOver('in-chat', it.identifier, $event)"
                    @drop.prevent="onDrop('in-chat', it.identifier, $event)"
                  >
                    <div
                      class="w-6 flex items-center justify-center select-none cursor-grab active:cursor-grabbing"
                      draggable="true"
                      @dragstart="onDragStart('in-chat', it.identifier, $event)"
                      @dragend="onDragEnd"
                      title="拖拽排序"
                    >
                      <i data-lucide="grip-vertical" class="icon-grip w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
                    </div>

                    <div class="flex-1">
                      <!-- 卡片（内联编辑） -->
                      <div class="border border-gray-200 rounded-4 p-3 bg-white transition-all duration-200 ease-soft hover:shadow-elevate">
                        <div class="flex items-center justify-between">
                          <div class="text-sm flex items-center gap-2">
                            <span class="font-medium">{{ it.name }}</span>
                            <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">depth: {{ Number(it.depth || 0) }}</span>
                            <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">order: {{ Number(it.order || 0) }}</span>
                          </div>
                          <div class="flex items-center gap-2">
                            <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ it.role }}</span>
                            <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ enabledLabel(it.enabled) }}</span>

                            <button
                              v-if="!(cardState[it.identifier]?.editing)"
                              class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                              @click="startEdit(it, cardState)"
                            >编辑</button>
                            <button
                              v-if="!(cardState[it.identifier]?.editing)"
                              class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                              @click="removeItem(it.identifier)"
                            >删除</button>

                            <template v-if="cardState[it.identifier]?.editing">
                              <button
                                class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                                @click="saveEdit(it, cardState)"
                              >保存</button>
                              <button
                                class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                                @click="cancelEdit(it, cardState)"
                              >取消</button>
                            </template>
                          </div>
                        </div>

                        <div class="text-xs text-black/60 mt-2">
                          <span class="font-mono">id:</span>
                          <span class="ml-1 font-mono">{{ it.identifier }}</span>
                        </div>

                        <div v-if="!cardState[it.identifier]?.editing">
                          <div class="text-xs text-black/70 mt-2 leading-6 break-words">
                            {{ it.content }}
                          </div>
                        </div>

                        <div v-else class="mt-3 space-y-3">
                          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div>
                              <label class="block text-xs text-black/60 mb-1">名称</label>
                              <input
                                type="text"
                                v-model="cardState[it.identifier].name"
                                class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                              />
                            </div>
                            <div>
                              <label class="block text-xs text-black/60 mb-1">启用状态</label>
                              <select
                                v-model="cardState[it.identifier].enabled"
                                class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
                              >
                                <option value="true">已启用</option>
                                <option value="false">未启用</option>
                                <option value="null">未设置</option>
                              </select>
                            </div>
                            <div>
                              <label class="block text-xs text-black/60 mb-1">角色（role）</label>
                              <select
                                v-model="cardState[it.identifier].role"
                                class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
                              >
                                <option value="system">system</option>
                                <option value="user">user</option>
                                <option value="assistant">assistant</option>
                              </select>
                            </div>
                            <div>
                              <label class="block text-xs text-black/60 mb-1">深度（depth）</label>
                              <input
                                type="number"
                                v-model.number="cardState[it.identifier].depth"
                                class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                              />
                            </div>
                            <div>
                              <label class="block text-xs text-black/60 mb-1">顺序（order）</label>
                              <input
                                type="number"
                                v-model.number="cardState[it.identifier].order"
                                class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                              />
                            </div>
                          </div>

                          <div>
                            <label class="block text-xs text-black/60 mb-1">内容（content）</label>
                            <textarea
                              v-model="cardState[it.identifier].content"
                              rows="4"
                              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 列表末尾插入线 -->
                  <div
                    class="h-3 draglist-end"
                    :class="{ 'drag-over-end': dragging && dragOverId === null && dragging.position === 'in-chat' }"
                    @dragover.prevent="onDragOver('in-chat', null, $event)"
                    @drop.prevent="onDropEnd('in-chat', $event)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div> <!-- grid end -->
    </div>

    <!-- 正则编辑 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <button
        type="button"
        class="w-full flex items-center justify-between mb-3 rounded-4"
        @click="regexOpen = !regexOpen"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="code" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">正则编辑</span>
        </div>
        <i
          data-lucide="chevron-down"
          class="w-4 h-4 text-black transition-transform duration-200 ease-soft"
          :class="regexOpen ? 'rotate-180' : ''"
        />
      </button>

      <div v-show="regexOpen" class="space-y-2">
        <!-- 新增 Regex：右侧 id + 名称 + 添加 -->
        <div class="mb-2 flex justify-end">
          <div class="flex items-center gap-2">
            <input
              v-model="newRegexId"
              placeholder="id"
              class="w-32 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
            />
            <input
              v-model="newRegexName"
              placeholder="名称"
              class="w-40 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
            />
            <button
              class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
              @click="addCustomRegex"
            >
              添加
            </button>
          </div>
        </div>
        <p v-if="regexError" class="text-xs text-red-600">* {{ regexError }}</p>

        <!-- 规则列表（可拖拽排序，黑线插入预览） -->
        <div class="space-y-2">
          <div
            v-for="r in demoData.regex_rules"
            :key="r.id"
            class="flex items-stretch gap-2 group draglist-item"
            :class="{
              'dragging-item': draggingRegex && draggingRegex === r.id,
              'drag-over-top': draggingRegex && dragOverRegexId === r.id && dragOverRegexBefore,
              'drag-over-bottom': draggingRegex && dragOverRegexId === r.id && !dragOverRegexBefore
            }"
            @dragover.prevent="onRegexDragOver(r.id, $event)"
            @drop.prevent="onRegexDrop(r.id, $event)"
          >
            <div
              class="w-6 flex items-center justify-center select-none cursor-grab active:cursor-grabbing"
              draggable="true"
              @dragstart="onRegexDragStart(r.id, $event)"
              @dragend="onRegexDragEnd"
              title="拖拽排序"
            >
              <i data-lucide="grip-vertical" class="icon-grip w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
            </div>
            <div class="flex-1">
              <!-- 简版 Regex 卡片 -->
              <div class="border border-gray-200 rounded-4 p-3 bg-white transition-all duration-200 ease-soft hover:shadow-elevate">
                <div class="flex items-center justify-between">
                  <div class="text-sm flex items-center gap-2">
                    <span class="font-medium">{{ r.name }}</span>
                    <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">id: {{ r.id }}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ r.enabled ? '已启用' : '未启用' }}</span>
                  </div>
                </div>
                <div class="text-xs text-black/60 mt-2 break-words">
                  find: <span class="font-mono">{{ r.find_regex || '(未设置)' }}</span>
                </div>
                <div class="text-xs text-black/60 mt-1 break-words">
                  replace: <span class="font-mono">{{ r.replace_regex || '(未设置)' }}</span>
                </div>
              </div>
            </div>
          </div>

          <div
            class="h-3 draglist-end"
            :class="{ 'drag-over-end': draggingRegex && dragOverRegexId === null }"
            @dragover.prevent="onRegexDragOver(null, $event)"
            @drop.prevent="onRegexDropEnd($event)"
          />
        </div>

        <div v-if="demoData.regex_rules.length === 0" class="text-xs text-black/50 px-1 py-1">
          暂无规则，请在右上角输入后点击添加
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 悬浮滑条（透明导轨），暂留复用 */
.overlay-range {
  position: absolute;
  left: 0; right: 0; top: -12px;
  pointer-events: auto;
}
/* WebKit 导轨透明 */
.overlay-range::-webkit-slider-runnable-track { background: transparent !important; height: 0 !important; border: none !important; }
.overlay-range::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 12px; height: 12px; background: #111; border-radius: 50%; border: 2px solid #111;
}
/* Firefox 导轨透明 */
.overlay-range::-moz-range-track { background: transparent !important; height: 0 !important; border: none !important; }
.overlay-range::-moz-range-thumb { width: 12px; height: 12px; background: #111; border-radius: 50%; border: 2px solid #111; }

/* 抓手与占位 */
.cursor-grab { cursor: grab; }
.cursor-grab:active { cursor: grabbing; }
.icon-grip::before {
  content: '⋮⋮';
  display: inline-block;
  line-height: 1;
  font-weight: 700;
  color: #111;
}

/* 列表拖拽预览线与动画 */
.draglist-move { transition: transform 180ms cubic-bezier(.2,.6,.2,1); }
.draglist-enter-active, .draglist-leave-active { transition: all 120ms ease; }
.draglist-enter-from, .draglist-leave-to { opacity: 0; transform: translateY(4px); }

/* 相对定位容器，便于绘制顶/底插入线 */
.draglist-item { position: relative; }
.drag-over-top::before {
  content: ''; position: absolute; left: 8px; right: 8px; top: -6px; height: 2px; background: #111; border-radius: 2px;
}
.drag-over-bottom::after {
  content: ''; position: absolute; left: 8px; right: 8px; bottom: -6px; height: 2px; background: #111; border-radius: 2px;
}
.dragging-item {
  transform: scale(0.98); box-shadow: 0 12px 24px rgba(0,0,0,0.18); opacity: 0.92; z-index: 1;
  transition: transform 150ms ease, box-shadow 150ms ease, opacity 150ms ease;
}
.draglist-end { position: relative; }
.drag-over-end::after {
  content: ''; position: absolute; left: 8px; right: 8px; top: 5px; height: 2px; background: #111; border-radius: 2px;
}
</style>