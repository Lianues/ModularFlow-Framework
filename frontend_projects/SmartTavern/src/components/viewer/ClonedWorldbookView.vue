<script setup>
import { ref, reactive, computed, onMounted, nextTick, watchEffect } from 'vue'

/**
 * 世界书主面板（克隆自 PromptEditor 的 WorldbookView + WorldBookCard）
 * - 完全本地 demo JSON 驱动，不依赖 Pinia Store
 * - UI 与交互尽量保持一致（新增/编辑/删除/拖拽排序/重命名）
 * - 可选加载外部 demo：@/data/worldbook_demo.json（不存在时忽略）
 */

/* ---------------------- 本地演示 JSON（可被外部 JSON 覆盖） ---------------------- */
const demoData = reactive({
  fileName: 'WorldBookDemo.json',
  entries: [
    {
      id: 'wb-1',
      name: '世界观·基本设定',
      enabled: true,
      content: '这里描述世界的基本架构、时代背景、科技树与超自然规则。',
      mode: 'always',
      position: 'system',
      order: 10,
      depth: 0,
      keys: []
    },
    {
      id: 'wb-2',
      name: '世界术语·术者与灵源',
      enabled: true,
      content: '术者：可调用灵源的个体。灵源：世界潜在的能量载体。',
      mode: 'conditional',
      position: 'before_char',
      order: 20,
      depth: 0,
      keys: ['术者', '灵源']
    },
    {
      id: 'wb-3',
      name: '地理·北境诸国',
      enabled: false,
      content: '北境气候严寒，诸国依附矿脉而兴衰，贸易多以毛皮与矿货为主。',
      mode: 'always',
      position: 'system',
      order: 30,
      depth: 0,
      keys: []
    }
  ]
})

/* 可选：尝试加载外部演示 JSON（vite 支持 JSON import）。若找不到则保持内置数据。 */
async function tryLoadExternalJson() {
  try {
    const mod = await import('@/data/worldbook_demo.json')
    const ext = (mod && (mod.default || mod)) || null
    if (ext && typeof ext === 'object') {
      if (typeof ext.fileName === 'string') demoData.fileName = ext.fileName
      if (Array.isArray(ext.entries)) {
        demoData.entries.splice(0, demoData.entries.length, ...ext.entries.map(x => ({ ...(x || {}) })))
      }
    }
  } catch {
    // ignore
  }
}

/* ---------------------- 面板开合状态（本地存储） ---------------------- */
const PANEL_STATE_KEY = 'worldbook_viewer_ui_panels'
const mainOpen = ref(true)

function loadPanelStates() {
  try {
    const raw = localStorage.getItem(PANEL_STATE_KEY)
    if (raw) {
      const obj = JSON.parse(raw)
      if (typeof obj.mainOpen === 'boolean') mainOpen.value = obj.mainOpen
    }
  } catch {}
}
function savePanelStates() {
  try {
    localStorage.setItem(PANEL_STATE_KEY, JSON.stringify({ mainOpen: mainOpen.value }))
  } catch {}
}

/* ---------------------- 文件名重命名（演示） ---------------------- */
const fileTitle = ref('')
const renameError = ref(null)
function renameWorldbookFile() {
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
  fileTitle.value = demoData.fileName || ''
  await tryLoadExternalJson()
  await nextTick()
  window?.lucide?.createIcons?.()
})
watchEffect(savePanelStates)

/* ---------------------- 新增条目（右上角 id + 名称 + 添加） ---------------------- */
const newId = ref('')
const newName = ref('')

async function addEntry() {
  const id = newId.value.trim()
  const name = newName.value.trim()
  if (!id) { alert('请填写 id'); return }
  if (!name) { alert('请填写 名称'); return }
  if (demoData.entries.some(e => e.id === id)) {
    alert('id 已存在'); return
  }
  const entry = {
    id, name,
    enabled: true,
    content: '',
    mode: 'always',
    position: 'before_char', // framing 默认在角色前
    order: 100,
    depth: 0,
    keys: []
  }
  demoData.entries.unshift(entry)
  newId.value = ''
  newName.value = ''
  await nextTick()
  window?.lucide?.createIcons?.()
}

/* ---------------------- 拖拽排序（黑线插入预览） ---------------------- */
const dragging = ref(null)        // string | null (id)
const dragOverId = ref(null)      // string | null
const dragOverBefore = ref(true)  // boolean

function onDragStart(id, ev) {
  dragging.value = id
  try {
    ev.dataTransfer?.setData('text/plain', id)
    ev.dataTransfer.effectAllowed = 'move'
    const canvas = document.createElement('canvas'); canvas.width = 1; canvas.height = 1
    ev.dataTransfer?.setDragImage(canvas, 0, 0)
  } catch {}
}
function onDragOver(overId, ev) {
  if (!dragging.value) return
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
function onDrop(overId, ev) {
  if (!dragging.value) return
  ev.preventDefault()
  const dId = dragging.value
  const items = [...demoData.entries]
  let ids = items.map(i => i.id)
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
  // 将重排结果写回
  const map = new Map(items.map(i => [i.id, i]))
  const next = []
  for (const id of ids) {
    const x = map.get(id)
    if (x) next.push(x)
  }
  demoData.entries.splice(0, demoData.entries.length, ...next)
  dragging.value = null
  dragOverId.value = null
  window?.lucide?.createIcons?.()
}
function onDropEnd(ev) { onDrop(null, ev) }
function onDragEnd() { dragging.value = null; dragOverId.value = null }

/* ---------------------- 卡片编辑（内联），按 id 维护草稿 ---------------------- */
const cardState = reactive({}) // id -> { editing, id, name, enabled, content, mode, position, order, depth, keysText, error }

function toggleEdit(entry) {
  const key = entry.id
  const st = cardState[key]
  if (st && st.editing) {
    cardState[key].editing = false
    return
  }
  cardState[key] = {
    editing: true,
    id: entry.id,
    name: entry.name,
    enabled: !!entry.enabled,
    content: entry.content ?? '',
    mode: entry.mode ?? 'always',
    position: entry.position ?? 'system',
    order: entry.order ?? 100,
    depth: entry.depth ?? 0,
    keysText: (entry.keys ?? []).join(';'),
    error: null
  }
  nextTick(() => window?.lucide?.createIcons?.())
}

function onSave(entry) {
  const st = cardState[entry.id]
  if (!st) return
  st.error = null
  const newId = String(st.id ?? '').trim()
  if (!newId) { st.error = '请填写 ID'; return }
  // 若 id 改动且与他人重复，报错
  if (newId !== entry.id && demoData.entries.some(w => w.id === newId)) {
    st.error = 'ID 已存在'; return
  }
  const keysArr =
    st.mode === 'conditional'
      ? String(st.keysText || '')
          .split(/;/)
          .map(x => x.trim())
          .filter(Boolean)
      : []

  const updated = {
    id: newId,
    name: String(st.name || '').trim() || newId,
    enabled: !!st.enabled,
    content: String(st.content ?? ''),
    mode: st.mode,
    position: st.position,
    order: Number(st.order ?? 100),
    depth: Number(st.depth ?? 0),
    keys: keysArr
  }

  // 在相同位置替换，若改了 id 则相当于“重命名”
  const idx = demoData.entries.findIndex(w => w.id === entry.id)
  if (idx >= 0) {
    demoData.entries.splice(idx, 1, updated)
  }
  // 若 id 改了，迁移编辑状态至新 key
  if (newId !== entry.id) {
    delete cardState[entry.id]
    cardState[newId] = { editing: false }
  } else {
    cardState[entry.id] = { editing: false }
  }
  nextTick(() => window?.lucide?.createIcons?.())
}

function onCancel(entry) {
  const key = entry.id
  if (cardState[key]) cardState[key].editing = false
}

function onDelete(entry) {
  const idx = demoData.entries.findIndex(w => w.id === entry.id)
  if (idx >= 0) demoData.entries.splice(idx, 1)
}
</script>

<template>
  <section class="space-y-6">
    <!-- 标题 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <i data-lucide="book-open" class="w-5 h-5 text-black"></i>
          <h2>世界书（独立面板）</h2>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="fileTitle"
            placeholder="文件名.json"
            class="w-56 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
            @keyup.enter="renameWorldbookFile"
            @blur="renameWorldbookFile"
          />
          <button
            class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-sm hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
            @click="renameWorldbookFile"
          >重命名</button>
        </div>
      </div>
      <p class="mt-2 text-xs text-black/60">使用右上角 导入/导出 · 参考：backend_projects/SmartTavern/data/world_books/参考用main_world.json</p>
      <p v-if="renameError" class="text-xs text-red-600 mt-1">* {{ renameError }}</p>
    </div>

    <!-- 工具栏：仅新增（导入/导出请使用右上角按钮） -->
    <div class="bg-white rounded-4 border border-gray-200 p-4 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between gap-3">
        <div class="text-sm text-black/70">
          条目数量：{{ demoData.entries.length }}
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="newId"
            placeholder="id"
            class="w-32 px-3 py-2 border border-gray-300 rounded-4 text-xs focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
          <input
            v-model="newName"
            placeholder="名称"
            class="w-40 px-3 py-2 border border-gray-300 rounded-4 text-xs focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
          <button
            class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
            @click="addEntry"
          >
            添加
          </button>
        </div>
      </div>
      <p class="text-xs text-black/50 mt-2">导入/导出请使用右上角按钮</p>
    </div>

    <!-- 条目区域 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <button
        type="button"
        class="w-full flex items-center justify-between mb-3 rounded-4"
        @click="mainOpen = !mainOpen"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="settings-2" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">世界书编辑</span>
        </div>
        <i
          data-lucide="chevron-down"
          class="w-4 h-4 text-black transition-transform duration-200 ease-soft"
          :class="mainOpen ? 'rotate-180' : ''"
        />
      </button>

      <!-- 列表（可拖拽排序，左侧握把 + 黑线插入预览） -->
      <div v-show="mainOpen" class="space-y-2">
        <div
          v-for="w in demoData.entries"
          :key="w.id"
          class="flex items-stretch gap-2 group draglist-item"
          :class="{
            'dragging-item': dragging && dragging === w.id,
            'drag-over-top': dragging && dragOverId === w.id && dragOverBefore,
            'drag-over-bottom': dragging && dragOverId === w.id && !dragOverBefore
          }"
          @dragover.prevent="onDragOver(w.id, $event)"
          @drop.prevent="onDrop(w.id, $event)"
        >
          <div
            class="w-6 flex items-center justify-center select-none cursor-grab active:cursor-grabbing"
            draggable="true"
            @dragstart="onDragStart(w.id, $event)"
            @dragend="onDragEnd"
            title="拖拽排序"
          >
            <i data-lucide="grip-vertical" class="icon-grip w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
          </div>

          <div class="flex-1">
            <!-- 卡片（内联编辑版本，复用 PromptEditor 的视觉） -->
            <div class="bg-white rounded-4 border border-gray-200 p-4 transition-all duration-200 ease-soft hover:shadow-elevate">
              <div class="flex items-start justify-between">
                <div class="min-w-0">
                  <div class="flex items-center flex-wrap gap-2">
                    <h3 class="text-lg font-bold text-black truncate">{{ w.name }}</h3>
                    <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">id: {{ w.id }}</span>
                    <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ w.mode || 'always' }}</span>
                    <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ w.position || 'system' }}</span>
                    <span class="text-xs text-black/60">{{ w.enabled ? '已启用' : '未启用' }}</span>
                    <span v-if="w.order !== undefined" class="text-xs text-black/50">#{{ w.order }}</span>
                    <span v-if="w.depth !== undefined" class="text-xs text-black/50">depth: {{ w.depth }}</span>
                  </div>
                </div>

                <div class="flex items-center gap-2 shrink-0">
                  <button
                    class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                    @click="onDelete(w)">删除</button>

                  <button
                    v-if="!(cardState[w.id]?.editing)"
                    class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                    @click="toggleEdit(w)">编辑</button>

                  <template v-else>
                    <button
                      class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 text-sm"
                      @click="onSave(w)">保存</button>
                    <button
                      class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 text-sm"
                      @click="onCancel(w)">取消</button>
                  </template>
                </div>
              </div>

              <!-- 查看模式 -->
              <div v-if="!(cardState[w.id]?.editing)" class="mt-3 space-y-2">
                <div class="text-sm text-black/70 leading-6">{{ w.content || '（暂无内容）' }}</div>
                <div v-if="w.mode === 'conditional' && (w.keys?.length || 0) > 0" class="text-xs text-black/60">
                  keys：<span class="font-mono">{{ (w.keys || []).join(', ') }}</span>
                </div>
              </div>

              <!-- 编辑模式 -->
              <div v-else class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-black mb-2">ID</label>
                  <input v-model="cardState[w.id].id" placeholder="例如：1 或 my-id" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-black mb-2">名称</label>
                  <input v-model="cardState[w.id].name" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800" />
                </div>
                <div class="flex items-center gap-3">
                  <label class="inline-flex items-center space-x-2 select-none">
                    <input type="checkbox" v-model="cardState[w.id].enabled" class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2" />
                    <span class="text-sm text-black/80">已启用</span>
                  </label>
                </div>

                <div>
                  <label class="block text-sm font-medium text-black mb-2">模式</label>
                  <select v-model="cardState[w.id].mode" class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800">
                    <option value="always">always</option>
                    <option value="conditional">conditional</option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-black mb-2">位置（position）</label>
                  <select v-model="cardState[w.id].position" class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800">
                    <optgroup label="framing（角色前后）">
                      <option value="before_char">before_char</option>
                      <option value="after_char">after_char</option>
                    </optgroup>
                    <optgroup label="in-chat（插入对话）">
                      <option value="user">user</option>
                      <option value="assistant">assistant</option>
                      <option value="system">system</option>
                    </optgroup>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-black mb-2">order（排序权重）</label>
                  <input type="number" v-model.number="cardState[w.id].order" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-black mb-2">depth（注入深度）</label>
                  <input type="number" v-model.number="cardState[w.id].depth" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800" />
                </div>

                <div v-if="cardState[w.id].mode === 'conditional'" class="md:col-span-2">
                  <label class="block text-sm font-medium text-black mb-2">keys（关键词，使用英文分号 ; 分隔）</label>
                  <input v-model="cardState[w.id].keysText" placeholder="示例：艾拉;工程师" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800" />
                </div>

                <div class="md:col-span-2">
                  <label class="block text-sm font-medium text-black mb-2">内容</label>
                  <textarea rows="4" v-model="cardState[w.id].content" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"></textarea>
                </div>

                <p v-if="cardState[w.id].error" class="md:col-span-2 text-xs text-red-600">* {{ cardState[w.id].error }}</p>
              </div>
            </div>
          </div>
        </div>

        <div
          class="h-3 draglist-end"
          :class="{ 'drag-over-end': dragging && dragOverId === null }"
          @dragover.prevent="onDragOver(null, $event)"
          @drop.prevent="onDropEnd($event)"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
/* lucide 加载失败时的握把占位符 */
.icon-grip::before {
  content: '⋮⋮';
  display: inline-block;
  line-height: 1;
  font-weight: 700;
  color: #111;
}

/* 拖拽动效与黑线插入预览（与预设/正则页面一致） */
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