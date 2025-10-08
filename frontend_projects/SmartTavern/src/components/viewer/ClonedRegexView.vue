<script setup>
import { ref, reactive, computed, onMounted, nextTick, watchEffect } from 'vue'

/**
 * 正则规则主面板（克隆自 PromptEditor 的 RegexView 样式/交互）
 * - 使用本地 demo JSON 驱动（不依赖 Pinia/后端）
 * - 可选加载：@/data/regex_demo.json（不存在时忽略）
 * - 支持：文件名重命名、导入/导出（占位）、新增规则、拖拽排序、卡片内联编辑
 */

const demoData = reactive({
  fileName: 'RegexDemo.json',
  rules: [
    {
      id: 'remove_xml',
      name: '移除 XML 标签',
      enabled: true,
      find_regex: '<[^>]+>',
      replace_regex: '',
      targets: ['preset', 'world_book', 'history.user', 'history.assistant'],
      placement: 'after_macro',
      views: ['user_view', 'assistant_view'],
      description: '清洗掉文本内的 XML/HTML 标签'
    },
    {
      id: 'trim_trailing_ws',
      name: '移除尾随空白',
      enabled: true,
      find_regex: '\\s+$',
      replace_regex: '',
      targets: ['preset', 'char', 'persona'],
      placement: 'after_macro',
      views: [],
      min_depth: 0,
      max_depth: 5,
      description: '删除每行末尾多余空白'
    }
  ]
})

async function tryLoadExternalJson() {
  try {
    const mod = await import('@/data/regex_demo.json')
    const ext = (mod && (mod.default || mod)) || null
    if (ext && typeof ext === 'object') {
      if (typeof ext.fileName === 'string') demoData.fileName = ext.fileName
      if (Array.isArray(ext.rules)) {
        demoData.rules.splice(0, demoData.rules.length, ...ext.rules.map(x => ({ ...(x || {}) })))
      }
    }
  } catch {
    // ignore
  }
}

/* 顶部：文件名重命名（演示） */
const fileTitle = ref('')
const renameError = ref(null)
function renameRegexFile() {
  renameError.value = null
  const nn = (fileTitle.value || '').trim()
  if (!nn) { renameError.value = '文件名不能为空'; return }
  demoData.fileName = nn
}

/* 右上角新增规则 */
const newId = ref('')
const newName = ref('')
const error = ref(null)

async function addRule() {
  error.value = null
  const id = (newId.value || '').trim()
  const name = (newName.value || '').trim()
  if (!id) { error.value = '请填写 id'; return }
  if (!name) { error.value = '请填写 名称'; return }
  if (demoData.rules.some(r => r.id === id)) { error.value = 'id 已存在'; return }
  const rule = {
    id, name, enabled: true,
    find_regex: '', replace_regex: '',
    targets: [], placement: 'after_macro', views: []
  }
  demoData.rules.unshift(rule)
  newId.value = ''
  newName.value = ''
  await nextTick()
  window?.lucide?.createIcons?.()
}

/* 导入/导出（占位演示，不真正读文件） */
const fileInput = ref(null)
function triggerImport() {
  alert('导入功能为演示占位，后续接入真实文件读取。')
}
function exportRules() {
  const blob = new Blob([JSON.stringify(demoData.rules, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = demoData.fileName.endsWith('.json') ? demoData.fileName : `${demoData.fileName}.json`
  a.click()
  URL.revokeObjectURL(url)
}

/* 拖拽排序（黑线预览） */
const dragging = ref(null)
const dragOverId = ref(null)
const dragOverBefore = ref(true)

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
  const items = [...demoData.rules]
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
  const map = new Map(items.map(i => [i.id, i]))
  const next = []
  for (const id of ids) {
    const x = map.get(id)
    if (x) next.push(x)
  }
  demoData.rules.splice(0, demoData.rules.length, ...next)
  dragging.value = null
  dragOverId.value = null
  window?.lucide?.createIcons?.()
}
function onDropEnd(ev) { onDrop(null, ev) }
function onDragEnd() { dragging.value = null; dragOverId.value = null }

/* 卡片编辑（内联，按 id 维护草稿） */
const cardState = reactive({}) // id -> { editing, name, enabled, placement, find, replace, selectedTargets, selectedViews, selectedSourceTypes, minDepth, maxDepth, description }

const TARGET_PREFIXES = ['preset','world_book','history','char','persona']
const VIEWS = ['user_view','assistant_view']
const SOURCE_TYPES = [
  'history.user', 'history.assistant', 'history.thinking',
  'preset.relative', 'preset.in-chat',
  'world_book.before_char', 'world_book.after_char', 'world_book.in-chat',
  'char.description', 'persona.description',
]

function enabledLabel(v) { return v ? '已启用' : '未启用' }

function toggleEdit(rule) {
  const key = rule.id
  const st = cardState[key]
  if (st && st.editing) {
    cardState[key].editing = false
    return
  }
  const arrT = (rule.targets || []).map(x => String(x))
  const arrV = (rule.views || []).map(x => String(x))
  const selT = {}
  for (const k of TARGET_PREFIXES) selT[k] = arrT.includes(k)
  const selV = {}
  for (const v of VIEWS) selV[v] = arrV.includes(v)
  const selST = {}
  for (const s of SOURCE_TYPES) selST[s] = arrT.includes(s)

  cardState[key] = {
    editing: true,
    name: rule.name,
    enabled: rule.enabled ? 'true' : 'false',
    placement: rule.placement || 'after_macro',
    find: rule.find_regex || '',
    replace: rule.replace_regex || '',
    selectedTargets: selT,
    selectedViews: selV,
    selectedSourceTypes: selST,
    minDepth: rule.min_depth != null ? String(rule.min_depth) : '',
    maxDepth: rule.max_depth != null ? String(rule.max_depth) : '',
    description: rule.description || ''
  }
  nextTick(() => window?.lucide?.createIcons?.())
}

function toNumOrUndef(text) {
  const t = String(text || '').trim()
  if (t === '') return undefined
  const n = Number(t)
  return Number.isFinite(n) ? n : undefined
}

function onSave(rule) {
  const st = cardState[rule.id]
  if (!st) return
  const targets = [
    ...TARGET_PREFIXES.filter(k => st.selectedTargets[k]),
    ...SOURCE_TYPES.filter(s => st.selectedSourceTypes[s]),
  ]
  const views = VIEWS.filter(v => st.selectedViews[v])
  const updated = {
    id: rule.id,
    name: (st.name || '').trim() || rule.id,
    enabled: st.enabled === 'true',
    find_regex: st.find || '',
    replace_regex: st.replace || '',
    targets,
    placement: st.placement || 'after_macro',
    views,
  }
  const minD = toNumOrUndef(st.minDepth)
  const maxD = toNumOrUndef(st.maxDepth)
  if (minD !== undefined) updated.min_depth = minD
  if (maxD !== undefined) updated.max_depth = maxD
  const desc = (st.description || '').trim()
  if (desc) updated.description = desc

  const idx = demoData.rules.findIndex(r => r.id === rule.id)
  if (idx >= 0) demoData.rules.splice(idx, 1, updated)
  cardState[rule.id] = { editing: false }
  nextTick(() => window?.lucide?.createIcons?.())
}

function onCancel(rule) {
  const key = rule.id
  if (cardState[key]) cardState[key].editing = false
}
function onDelete(rule) {
  const idx = demoData.rules.findIndex(r => r.id === rule.id)
  if (idx >= 0) demoData.rules.splice(idx, 1)
}

/* 面板开合状态（本地存储） */
const PANEL_STATE_KEY = 'regex_viewer_ui_panels'
const mainOpen = ref(true)
function loadPanelStates() {
  try {
    const raw = localStorage.getItem(PANEL_STATE_KEY)
    if (!raw) return
    const o = JSON.parse(raw)
    if (typeof o.mainOpen === 'boolean') mainOpen.value = o.mainOpen
  } catch {}
}
function savePanelStates() {
  try {
    localStorage.setItem(PANEL_STATE_KEY, JSON.stringify({ mainOpen: mainOpen.value }))
  } catch {}
}

/* 初始化 */
onMounted(async () => {
  loadPanelStates()
  fileTitle.value = demoData.fileName || 'RegexDemo.json'
  await tryLoadExternalJson()
  await nextTick()
  window?.lucide?.createIcons?.()
})
watchEffect(savePanelStates)
</script>

<template>
  <section class="space-y-6">
    <!-- 标题 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <i data-lucide="code" class="w-5 h-5 text-black"></i>
          <h2>正则规则（独立面板）</h2>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="fileTitle"
            placeholder="文件名.json"
            class="w-56 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
            @keyup.enter="renameRegexFile"
            @blur="renameRegexFile"
          />
          <button
            class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-sm hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
            @click="renameRegexFile"
          >重命名</button>
        </div>
      </div>
      <p class="mt-2 text-xs text-black/60">导入/导出参考：backend_projects/SmartTavern/data/regex_rules/remove_xml_tags.json</p>
      <p v-if="renameError" class="text-xs text-red-600 mt-1">* {{ renameError }}</p>
    </div>

    <!-- 工具栏：导入/导出 + 新增 -->
    <div class="bg-white rounded-4 border border-gray-200 p-4 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between gap-3">
        <div class="text-sm text-black/70">
          规则数量：{{ demoData.rules.length }}
        </div>
        <div class="flex items-center gap-2">
          <input ref="fileInput" type="file" accept="application/json" class="hidden" />
          <button
            class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
            @click="triggerImport"
          >
            导入
          </button>
          <button
            class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
            @click="exportRules"
          >
            导出
          </button>
          <div class="w-px h-5 bg-gray-300 mx-1"></div>
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
            @click="addRule"
          >
            添加
          </button>
        </div>
      </div>
      <p v-if="error" class="text-xs text-red-600 mt-2">* {{ error }}</p>
    </div>

    <!-- 条目区域容器（白色背景，小标题：正则编辑） -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <button
        type="button"
        class="w-full flex items-center justify-between mb-3 rounded-4"
        @click="mainOpen = !mainOpen"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="sliders" class="w-4 h-4 text-black"></i>
          <h3 class="text-base font-semibold text-black">正则编辑</h3>
        </div>
        <i data-lucide="chevron-down" class="w-4 h-4 text-black transition-transform duration-200 ease-soft" :class="mainOpen ? 'rotate-180' : ''"></i>
      </button>

      <!-- 列表（可拖拽排序，左侧握把 + 黑线插入预览） -->
      <div v-show="mainOpen" class="space-y-2">
        <div
          v-for="r in demoData.rules"
          :key="r.id"
          class="flex items-stretch gap-2 group draglist-item"
          :class="{
            'dragging-item': dragging && dragging === r.id,
            'drag-over-top': dragging && dragOverId === r.id && dragOverBefore,
            'drag-over-bottom': dragging && dragOverId === r.id && !dragOverBefore
          }"
          @dragover.prevent="onDragOver(r.id, $event)"
          @drop.prevent="onDrop(r.id, $event)"
        >
          <div
            class="w-6 flex items-center justify-center select-none cursor-grab active:cursor-grabbing"
            draggable="true"
            @dragstart="onDragStart(r.id, $event)"
            @dragend="onDragEnd"
            title="拖拽排序"
          >
            <i data-lucide="grip-vertical" class="icon-grip w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
          </div>
          <div class="flex-1">
            <!-- 卡片（内联编辑） -->
            <div class="border border-gray-200 rounded-4 p-3 bg-white transition-all duration-200 ease-soft hover:shadow-elevate">
              <div class="flex items-start justify-between">
                <div class="text-sm space-y-2">
                  <!-- 第一行：名称与 ID -->
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="font-medium">{{ r.name }}</span>
                    <span class="text-xs text-black/60 font-mono">id: {{ r.id }}</span>
                  </div>

                  <!-- 第二行：阶段与深度信息 -->
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="text-xs text-black/60">阶段</span>
                    <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ r.placement || '—' }}</span>
                    <span v-if="r.min_depth !== undefined" class="text-xs text-black/60">min: {{ r.min_depth }}</span>
                    <span v-if="r.max_depth !== undefined" class="text-xs text-black/60">max: {{ r.max_depth }}</span>
                  </div>

                  <!-- 第三行：targets -->
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="text-xs text-black/60">targets</span>
                    <span v-for="t in (r.targets || [])" :key="t" class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ t }}</span>
                  </div>

                  <!-- 第四行：views -->
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="text-xs text-black/60">views</span>
                    <span v-for="v in (r.views || [])" :key="v" class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ v }}</span>
                  </div>

                  <!-- 描述 -->
                  <p v-if="r.description" class="text-xs text-black/60">{{ r.description }}</p>
                </div>

                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ enabledLabel(r.enabled) }}</span>
                  <button
                    v-if="!(cardState[r.id]?.editing)"
                    class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                    @click="onDelete(r)"
                  >
                    删除
                  </button>
                  <button
                    v-if="!(cardState[r.id]?.editing)"
                    class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs"
                    @click="toggleEdit(r)"
                  >
                    编辑
                  </button>
                  <div v-else class="flex items-center gap-2">
                    <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs" @click="onSave(r)">保存</button>
                    <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-xs" @click="onCancel(r)">取消</button>
                  </div>
                </div>
              </div>

              <!-- View mode regex bodies -->
              <div v-if="!(cardState[r.id]?.editing)" class="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                <div class="border border-gray-200 rounded-4 p-3">
                  <div class="text-xs font-medium text-black mb-2">find_regex</div>
                  <div class="text-xs text-black/70 font-mono break-all whitespace-pre-wrap">{{ r.find_regex }}</div>
                </div>
                <div class="border border-gray-200 rounded-4 p-3">
                  <div class="text-xs font-medium text-black mb-2">replace_regex</div>
                  <div class="text-xs text-black/70 font-mono break-all whitespace-pre-wrap">{{ r.replace_regex }}</div>
                </div>
              </div>

              <!-- Edit form -->
              <div v-else class="mt-3 space-y-3">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label class="block text-xs text-black/60 mb-1">名称</label>
                    <input
                      type="text"
                      v-model="cardState[r.id].name"
                      class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-black/60 mb-1">启用状态</label>
                    <select
                      v-model="cardState[r.id].enabled"
                      class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
                    >
                      <option value="true">已启用</option>
                      <option value="false">未启用</option>
                    </select>
                  </div>

                  <div>
                    <label class="block text-xs text-black/60 mb-1">阶段（placement）</label>
                    <select
                      v-model="cardState[r.id].placement"
                      class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
                    >
                      <option value="before_macro">before_macro</option>
                      <option value="after_macro">after_macro</option>
                    </select>
                  </div>

                  <div>
                    <label class="block text-xs text-black/60 mb-1">Targets</label>
                    <div class="space-y-2">
                      <!-- 大类前缀 -->
                      <div class="flex flex-wrap items-center gap-3">
                        <span class="text-xs text-black/60">大类</span>
                        <label class="inline-flex items-center gap-2 text-xs" v-for="k in TARGET_PREFIXES" :key="k">
                          <input
                            type="checkbox"
                            v-model="cardState[r.id].selectedTargets[k]"
                            class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                          />
                          <span>{{ k }}</span>
                        </label>
                      </div>
                      <!-- 细粒度来源类型 -->
                      <div class="flex flex-wrap items-center gap-3">
                        <span class="text-xs text-black/60">细项</span>
                        <label class="inline-flex items-center gap-2 text-xs" v-for="s in SOURCE_TYPES" :key="s">
                          <input
                            type="checkbox"
                            v-model="cardState[r.id].selectedSourceTypes[s]"
                            class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                          />
                          <span>{{ s }}</span>
                        </label>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label class="block text-xs text-black/60 mb-1">Views</label>
                    <div class="flex flex-wrap items-center gap-3">
                      <label class="inline-flex items-center gap-2 text-xs" v-for="v in VIEWS" :key="v">
                        <input
                          type="checkbox"
                          v-model="cardState[r.id].selectedViews[v]"
                          class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                        />
                        <span>{{ v }}</span>
                      </label>
                    </div>
                  </div>

                  <div>
                    <label class="block text-xs text-black/60 mb-1">min_depth（可选）</label>
                    <input
                      type="number"
                      v-model="cardState[r.id].minDepth"
                      class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                    />
                  </div>

                  <div>
                    <label class="block text-xs text-black/60 mb-1">max_depth（可选）</label>
                    <input
                      type="number"
                      v-model="cardState[r.id].maxDepth"
                      class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                    />
                  </div>

                  <div class="md:col-span-2">
                    <label class="block text-xs text-black/60 mb-1">描述（可选）</label>
                    <textarea
                      v-model="cardState[r.id].description"
                      rows="3"
                      class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label class="block text-xs text-black/60 mb-1">find_regex</label>
                    <textarea
                      v-model="cardState[r.id].find"
                      rows="3"
                      class="w-full font-mono px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-black/60 mb-1">replace_regex</label>
                    <textarea
                      v-model="cardState[r.id].replace"
                      rows="3"
                      class="w-full font-mono px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                    />
                  </div>
                </div>
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