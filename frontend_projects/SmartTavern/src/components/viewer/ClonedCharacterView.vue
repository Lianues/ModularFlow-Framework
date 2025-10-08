<script setup>
import { ref, reactive, computed, onMounted, nextTick, watchEffect } from 'vue'

/**
 * 角色卡主面板（克隆自 PromptEditor 的 CharactersView 样式/交互）
 * - 使用本地 demo JSON 驱动（不依赖 Pinia/后端）
 * - 可选加载：@/data/character_demo.json（不存在时忽略）
 * - 支持：文件名重命名、基础信息(name/description)、初始消息、内嵌世界书/正则的新增与拖拽排序
 */

const demoData = reactive({
  fileName: 'CharacterDemo.json',
  name: '示例角色 · 风格化对话者',
  description: '该角色擅长风格化的简短回答，偏好使用简练表述并保持礼貌。',
  messages: [
    '你好，我会尽量用简短、清晰的方式回答你。',
    '若需要详细说明，我会先给出梗概，再展开。'
  ],
  world_entries: [
    {
      id: 'wb-briefing',
      name: '世界观 · 基本设定',
      enabled: true,
      content: '该世界具备中低魔环境，科技水平接近蒸汽与前电气时代交界。',
      mode: 'always',
      position: 'system',
      order: 10,
      depth: 0,
      keys: []
    },
    {
      id: 'wb-terms',
      name: '术语 · 术者/灵源',
      enabled: true,
      content: '术者：能调用灵源之人；灵源：广义超自然能流。',
      mode: 'conditional',
      position: 'before_char',
      order: 20,
      depth: 0,
      keys: ['术者', '灵源']
    }
  ],
  regex_rules: [
    {
      id: 'trim_trailing_ws',
      name: '移除尾随空白',
      enabled: true,
      find_regex: '\\s+$',
      replace_regex: '',
      targets: [],
      placement: 'after_macro',
      views: []
    },
    {
      id: 'collapse_blank_lines',
      name: '折叠多余空行',
      enabled: true,
      find_regex: '\\n{3,}',
      replace_regex: '\\n\\n',
      targets: [],
      placement: 'after_macro',
      views: []
    }
  ]
})

async function tryLoadExternalJson() {
  try {
    const mod = await import('@/data/character_demo.json')
    const ext = (mod && (mod.default || mod)) || null
    if (ext && typeof ext === 'object') {
      if (typeof ext.fileName === 'string') demoData.fileName = ext.fileName
      if (typeof ext.name === 'string') demoData.name = ext.name
      if (typeof ext.description === 'string') demoData.description = ext.description
      if (Array.isArray(ext.messages)) {
        demoData.messages.splice(0, demoData.messages.length, ...ext.messages.map(x => String(x ?? '')))
      }
      if (Array.isArray(ext.world_entries)) {
        demoData.world_entries.splice(0, demoData.world_entries.length, ...ext.world_entries.map(x => ({ ...(x || {}) })))
      }
      if (Array.isArray(ext.regex_rules)) {
        demoData.regex_rules.splice(0, demoData.regex_rules.length, ...ext.regex_rules.map(x => ({ ...(x || {}) })))
      }
    }
  } catch {
    // ignore missing file
  }
}

/* 顶部：文件名重命名（演示） */
const fileTitle = ref('')
const renameError = ref(null)
function renameCharacterFile() {
  renameError.value = null
  const nn = (fileTitle.value || '').trim()
  if (!nn) { renameError.value = '文件名不能为空'; return }
  demoData.fileName = nn
}

/* 基本信息（name/description） */
const nameDraft = ref('')
const descDraft = ref('')
function saveMeta() {
  demoData.name = nameDraft.value
  demoData.description = descDraft.value
}

/* 初始消息 edits（本地数组） */
const messages = computed(() => demoData.messages)
const messageEdits = ref([])
const editingMsgIndex = ref(null)
function syncMsgDrafts() {
  messageEdits.value = (messages.value || []).map(x => String(x ?? ''))
}
function onEditMsg(i) { editingMsgIndex.value = i }
function onCancelMsg(i) {
  if (!messages.value) return
  messageEdits.value[i] = String(messages.value[i] ?? '')
  editingMsgIndex.value = null
}
function onSaveMsg(i) {
  if (i < 0 || i >= messageEdits.value.length) return
  demoData.messages.splice(i, 1, String(messageEdits.value[i] ?? ''))
  editingMsgIndex.value = null
}
function removeMessage(i) {
  if (i < 0 || i >= demoData.messages.length) return
  demoData.messages.splice(i, 1)
  syncMsgDrafts()
}
function addMessage() {
  demoData.messages.push('')
  syncMsgDrafts()
  editingMsgIndex.value = (messages.value?.length ?? 1) - 1
  nextTick(() => (window?.lucide?.createIcons?.()))
}

/* 面板开合状态（本地存储） */
const PANEL_STATE_KEY = 'character_viewer_ui_panels'
const baseOpen = ref(true)
const msgOpen = ref(true)
const wbOpen = ref(true)
const rxOpen = ref(true)
function loadPanelStates() {
  try {
    const raw = localStorage.getItem(PANEL_STATE_KEY)
    if (!raw) return
    const o = JSON.parse(raw)
    if (typeof o.baseOpen === 'boolean') baseOpen.value = o.baseOpen
    if (typeof o.msgOpen === 'boolean') msgOpen.value = o.msgOpen
    if (typeof o.wbOpen === 'boolean') wbOpen.value = o.wbOpen
    if (typeof o.rxOpen === 'boolean') rxOpen.value = o.rxOpen
  } catch {}
}
function savePanelStates() {
  try {
    localStorage.setItem(PANEL_STATE_KEY, JSON.stringify({
      baseOpen: baseOpen.value,
      msgOpen: msgOpen.value,
      wbOpen: wbOpen.value,
      rxOpen: rxOpen.value
    }))
  } catch {}
}

/* 世界书小节：新增 + 排序 */
const newWbId = ref('')
const newWbName = ref('')
function addWorldEntry() {
  const id = (newWbId.value || '').trim()
  const name = (newWbName.value || '').trim()
  if (!id) { alert('请填写世界书 ID'); return }
  if (!name) { alert('请填写 世界书名称'); return }
  if (demoData.world_entries.some(e => String(e?.id) === id)) { alert('ID 已存在'); return }
  const entry = {
    id, name,
    enabled: true,
    content: '',
    mode: 'always',
    position: 'before_char',
    order: 100,
    depth: 0,
    keys: []
  }
  demoData.world_entries.unshift(entry)
  newWbId.value = ''
  newWbName.value = ''
  nextTick(() => (window?.lucide?.createIcons?.()))
}

/* 世界书拖拽排序（黑线预览） */
const draggingWb = ref(null)
const dragOverWbId = ref(null)
const dragOverWbBefore = ref(true)
function onDragStartWb(id, ev) {
  draggingWb.value = id
  try {
    ev.dataTransfer?.setData('text/plain', id)
    ev.dataTransfer.effectAllowed = 'move'
    const canvas = document.createElement('canvas'); canvas.width = 1; canvas.height = 1
    ev.dataTransfer?.setDragImage(canvas, 0, 0)
  } catch {}
}
function onDragOverWb(overId, ev) {
  if (!draggingWb.value) return
  ev.preventDefault()
  try {
    const el = ev.currentTarget
    if (el) {
      const rect = el.getBoundingClientRect()
      const mid = rect.top + rect.height / 2
      dragOverWbBefore.value = ev.clientY < mid
    }
  } catch {}
  dragOverWbId.value = overId
}
function onDropWb(overId, ev) {
  if (!draggingWb.value) return
  ev.preventDefault()
  const dId = draggingWb.value
  const items = [...demoData.world_entries]
  let ids = items.map(i => String(i.id))
  const fromIdx = ids.indexOf(String(dId))
  if (fromIdx < 0) return
  ids.splice(fromIdx, 1)
  if (overId && overId !== dId) {
    const toIdx = ids.indexOf(String(overId))
    let insertIdx = toIdx < 0 ? ids.length : toIdx + (dragOverWbBefore.value ? 0 : 1)
    if (insertIdx < 0) insertIdx = 0
    if (insertIdx > ids.length) insertIdx = ids.length
    ids.splice(insertIdx, 0, String(dId))
  } else {
    ids.push(String(dId))
  }
  const map = new Map(items.map(i => [String(i.id), i]))
  const next = []
  for (const id of ids) {
    const x = map.get(String(id))
    if (x) next.push(x)
  }
  demoData.world_entries.splice(0, demoData.world_entries.length, ...next)
  draggingWb.value = null
  dragOverWbId.value = null
  window?.lucide?.createIcons?.()
}
function onDropEndWb(ev) { onDropWb(null, ev) }
function onDragEndWb() { draggingWb.value = null; dragOverWbId.value = null }

/* 正则小节：新增 + 排序 */
const newRuleId = ref('')
const newRuleName = ref('')
const ruleError = ref(null)
function addRegexRule() {
  ruleError.value = null
  const id = (newRuleId.value || '').trim()
  const name = (newRuleName.value || '').trim()
  if (!id) { ruleError.value = '请填写 规则 id'; return }
  if (!name) { ruleError.value = '请填写 规则名称'; return }
  const rules = demoData.regex_rules || []
  if (rules.some(r => String(r?.id) === id)) { ruleError.value = '该 id 已存在'; return }
  const rule = {
    id, name, enabled: true,
    find_regex: '', replace_regex: '',
    targets: [], placement: 'after_macro', views: []
  }
  demoData.regex_rules.unshift(rule)
  newRuleId.value = ''
  newRuleName.value = ''
  nextTick(() => (window?.lucide?.createIcons?.()))
}

/* 正则拖拽排序 */
const draggingRx = ref(null)
const dragOverRxId = ref(null)
const dragOverRxBefore = ref(true)
function onDragStartRx(id, ev) {
  draggingRx.value = id
  try {
    ev.dataTransfer?.setData('text/plain', id)
    ev.dataTransfer.effectAllowed = 'move'
    const canvas = document.createElement('canvas'); canvas.width = 1; canvas.height = 1
    ev.dataTransfer?.setDragImage(canvas, 0, 0)
  } catch {}
}
function onDragOverRx(overId, ev) {
  if (!draggingRx.value) return
  ev.preventDefault()
  try {
    const el = ev.currentTarget
    if (el) {
      const rect = el.getBoundingClientRect()
      const mid = rect.top + rect.height / 2
      dragOverRxBefore.value = ev.clientY < mid
    }
  } catch {}
  dragOverRxId.value = overId
}
function onDropRx(overId, ev) {
  if (!draggingRx.value) return
  ev.preventDefault()
  const dId = draggingRx.value
  const items = [...(demoData.regex_rules || [])]
  let ids = items.map(i => String(i.id))
  const fromIdx = ids.indexOf(String(dId))
  if (fromIdx < 0) return
  ids.splice(fromIdx, 1)
  if (overId && overId !== dId) {
    const toIdx = ids.indexOf(String(overId))
    let insertIdx = toIdx < 0 ? ids.length : toIdx + (dragOverRxBefore.value ? 0 : 1)
    if (insertIdx < 0) insertIdx = 0
    if (insertIdx > ids.length) insertIdx = ids.length
    ids.splice(insertIdx, 0, String(dId))
  } else {
    ids.push(String(dId))
  }
  const map = new Map(items.map(i => [String(i.id), i]))
  const next = []
  for (const id of ids) {
    const x = map.get(String(id))
    if (x) next.push(x)
  }
  demoData.regex_rules.splice(0, demoData.regex_rules.length, ...next)
  draggingRx.value = null
  dragOverRxId.value = null
  window?.lucide?.createIcons?.()
}
function onDropEndRx(ev) { onDropRx(null, ev) }
function onDragEndRx() { draggingRx.value = null; dragOverRxId.value = null }

/* 初始化 */
onMounted(async () => {
  loadPanelStates()
  fileTitle.value = demoData.fileName || 'CharacterDemo.json'
  nameDraft.value = demoData.name || ''
  descDraft.value = demoData.description || ''
  syncMsgDrafts()
  await tryLoadExternalJson()
  syncMsgDrafts()
  await nextTick()
  window?.lucide?.createIcons?.()
})
watchEffect(savePanelStates)
</script>

<template>
  <section class="space-y-6">
    <!-- 顶部卡片：角色卡编辑入口 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <i data-lucide="user" class="w-5 h-5 text-black"></i>
          <h2>角色卡（单文件导入/导出）</h2>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="fileTitle"
            placeholder="文件名.json"
            class="w-56 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
            @keyup.enter="renameCharacterFile"
            @blur="renameCharacterFile"
          />
          <button
            class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-sm hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
            @click="renameCharacterFile"
          >重命名</button>
        </div>
      </div>
      <p class="mt-2 text-xs text-black/60">
        使用右上角导入按钮选择单个角色卡 JSON（结构示例位于演示数据）。导出亦可通过上层集成实现。
      </p>
      <p v-if="renameError" class="text-xs text-red-600 mt-1">* {{ renameError }}</p>
    </div>

    <!-- 基本设定 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <button
        type="button"
        class="w-full flex items-center justify-between mb-3 rounded-4"
        @click="baseOpen = !baseOpen"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="id-card" class="w-4 h-4 text-black"></i>
          <h3 class="text-base font-semibold text-black">基本设定</h3>
        </div>
        <i data-lucide="chevron-down" class="w-4 h-4 text-black transition-transform duration-200 ease-soft" :class="baseOpen ? 'rotate-180' : ''"></i>
      </button>

      <div v-show="baseOpen" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-black mb-2">名称</label>
          <input v-model="nameDraft" @blur="saveMeta" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800" />
        </div>
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-black mb-2">描述</label>
          <textarea v-model="descDraft" @blur="saveMeta" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800" />
        </div>
      </div>
    </div>

    <!-- 初始消息（message[]） -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <button
        type="button"
        class="w-full flex items-center justify-between mb-3 rounded-4"
        @click="msgOpen = !msgOpen"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="message-square" class="w-4 h-4 text-black"></i>
          <h3 class="text-base font-semibold text-black">初始消息（message）</h3>
        </div>
        <i data-lucide="chevron-down" class="w-4 h-4 text-black transition-transform duration-200 ease-soft" :class="msgOpen ? 'rotate-180' : ''"></i>
      </button>

      <div v-show="msgOpen" class="flex items-center justify-between mb-3">
        <div class="text-xs text-black/60">共 {{ messages.length }} 条</div>
        <div class="flex items-center gap-2">
          <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100"
                  @click="addMessage">新增</button>
        </div>
      </div>

      <div v-show="msgOpen" class="space-y-3">
        <div v-for="(m, i) in messageEdits" :key="i" class="border border-gray-200 rounded-4 p-3">
          <div class="flex items-center justify-between gap-2 mb-2">
            <div class="text-xs text-black/60">#{{ i + 1 }} · 长度：{{ (m || '').length }}</div>
            <div class="flex items-center gap-2">
              <template v-if="editingMsgIndex === i">
                <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100"
                        @click="onSaveMsg(i)">保存</button>
                <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100"
                        @click="onCancelMsg(i)">取消</button>
              </template>
              <template v-else>
                <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100"
                        @click="onEditMsg(i)">编辑</button>
                <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100"
                        @click="removeMessage(i)">删除</button>
              </template>
            </div>
          </div>
          <template v-if="editingMsgIndex === i">
            <textarea v-model="messageEdits[i]" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800" />
          </template>
          <template v-else>
            <div class="text-sm text-black/70 whitespace-pre-wrap">{{ m }}</div>
          </template>
        </div>
      </div>
    </div>

    <!-- 内嵌 · 世界书 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 mb-3">
          <i data-lucide="book-open" class="w-4 h-4 text-black"></i>
          <h3 class="text-base font-semibold text-black">世界书编辑</h3>
        </div>
        <div class="flex items-center gap-2">
          <input v-model="newWbId" placeholder="id" class="w-32 px-3 py-2 border border-gray-300 rounded-4 text-xs focus:outline-none focus:ring-2 focus:ring-gray-800" />
          <input v-model="newWbName" placeholder="名称" class="w-40 px-3 py-2 border border-gray-300 rounded-4 text-xs focus:outline-none focus:ring-2 focus:ring-gray-800" />
          <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100"
                  @click="addWorldEntry">添加</button>
        </div>
      </div>

      <div class="space-y-2">
        <div
          v-for="w in demoData.world_entries"
          :key="String(w.id)"
          class="flex items-stretch gap-2 group draglist-item"
          :class="{
            'dragging-item': draggingWb && draggingWb === String(w.id),
            'drag-over-top': draggingWb && dragOverWbId === String(w.id) && dragOverWbBefore,
            'drag-over-bottom': draggingWb && dragOverWbId === String(w.id) && !dragOverWbBefore
          }"
          @dragover.prevent="onDragOverWb(String(w.id), $event)"
          @drop.prevent="onDropWb(String(w.id), $event)"
        >
          <div
            class="w-6 flex items-center justify-center select-none cursor-grab active:cursor-grabbing"
            draggable="true"
            @dragstart="onDragStartWb(String(w.id), $event)"
            @dragend="onDragEndWb"
            title="拖拽排序"
          >
            <i data-lucide="grip-vertical" class="icon-grip w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
          </div>
          <div class="flex-1">
            <div class="bg-white rounded-4 border border-gray-200 p-3 transition-all duration-200 ease-soft hover:shadow-elevate">
              <div class="flex items-start justify-between">
                <div class="min-w-0">
                  <div class="flex items-center flex-wrap gap-2">
                    <h3 class="text-sm font-bold text-black truncate">{{ w.name }}</h3>
                    <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">id: {{ w.id }}</span>
                    <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ w.mode || 'always' }}</span>
                    <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ w.position || 'system' }}</span>
                    <span class="text-xs text-black/60">{{ w.enabled ? '已启用' : '未启用' }}</span>
                  </div>
                </div>
              </div>
              <div class="text-xs text-black/70 mt-2 leading-6 break-words">
                {{ w.content || '（暂无内容）' }}
              </div>
              <div v-if="w.mode === 'conditional' && (w.keys || []).length > 0" class="text-xs text-black/60 mt-1">
                keys：<span class="font-mono">{{ (w.keys || []).join(', ') }}</span>
              </div>
            </div>
          </div>
        </div>
        <div
          class="h-3 draglist-end"
          :class="{ 'drag-over-end': draggingWb && dragOverWbId === null }"
          @dragover.prevent="onDragOverWb(null, $event)"
          @drop.prevent="onDropEndWb($event)"
        />
      </div>
    </div>

    <!-- 内嵌 · 正则 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 mb-3">
          <i data-lucide="code" class="w-4 h-4 text-black"></i>
          <h3 class="text-base font-semibold text-black">正则编辑</h3>
        </div>
        <div class="flex items-center gap-2">
          <input v-model="newRuleId" placeholder="规则 id" class="w-32 px-3 py-2 border border-gray-300 rounded-4 text-xs focus:outline-none focus:ring-2 focus:ring-gray-800" />
          <input v-model="newRuleName" placeholder="规则名称" class="w-40 px-3 py-2 border border-gray-300 rounded-4 text-xs focus:outline-none focus:ring-2 focus:ring-gray-800" />
          <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100"
                  @click="addRegexRule">添加</button>
        </div>
      </div>
      <p v-if="ruleError" class="text-xs text-red-600 mb-2">* {{ ruleError }}</p>

      <div class="space-y-2">
        <div
          v-for="r in demoData.regex_rules"
          :key="String(r.id)"
          class="flex items-stretch gap-2 group draglist-item"
          :class="{
            'dragging-item': draggingRx && draggingRx === String(r.id),
            'drag-over-top': draggingRx && dragOverRxId === String(r.id) && dragOverRxBefore,
            'drag-over-bottom': draggingRx && dragOverRxId === String(r.id) && !dragOverRxBefore
          }"
          @dragover.prevent="onDragOverRx(String(r.id), $event)"
          @drop.prevent="onDropRx(String(r.id), $event)"
        >
          <div
            class="w-6 flex items-center justify-center select-none cursor-grab active:cursor-grabbing"
            draggable="true"
            @dragstart="onDragStartRx(String(r.id), $event)"
            @dragend="onDragEndRx"
            title="拖拽排序"
          >
            <i data-lucide="grip-vertical" class="icon-grip w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
          </div>
          <div class="flex-1">
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
          :class="{ 'drag-over-end': draggingRx && dragOverRxId === null }"
          @dragover.prevent="onDragOverRx(null, $event)"
          @drop.prevent="onDropEndRx($event)"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
/* lucide 抓手占位符 */
.icon-grip::before {
  content: '⋮⋮';
  display: inline-block;
  line-height: 1;
  font-weight: 700;
  color: #111;
}

/* 拖拽动效与黑线插入预览（与其他面板一致） */
.draglist-item { position: relative; }
.drag-over-top::before {
  content: '';
  position: absolute;
  left: 8px;
  right: 8px;
  top: -6px;
  height: 2px;
  background: #111;
  border-radius: 2px;
}
.drag-over-bottom::after {
  content: '';
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: -6px;
  height: 2px;
  background: #111;
  border-radius: 2px;
}
.dragging-item {
  transform: scale(0.98);
  box-shadow: 0 12px 24px rgba(0,0,0,0.18);
  opacity: 0.92;
  z-index: 1;
  transition: transform 150ms ease, box-shadow 150ms ease, opacity 150ms ease;
}
.draglist-end { position: relative; }
.drag-over-end::after {
  content: '';
  position: absolute;
  left: 8px;
  right: 8px;
  top: 5px;
  height: 2px;
  background: #111;
  border-radius: 2px;
}
</style>