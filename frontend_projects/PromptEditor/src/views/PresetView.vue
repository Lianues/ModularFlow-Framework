<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'

// 预设设置的简化模型（本地占位状态）
const temperature = ref<number>(1.0)
const maxTokens = ref<number>(300)
const stream = ref<boolean>(true)
const topP = ref<number>(1.0)
const frequencyPenalty = ref<number>(0)
const presencePenalty = ref<number>(0)

/* 面板收起/展开（默认全部展开）；状态持久化到 LocalStorage */
const PANEL_STATE_KEY = 'prompt_editor_ui_panels'
const apiOpen = ref(true)
const promptsOpen = ref(true)
const regexOpen = ref(true)
const relativeOpen = ref(true)
const inChatOpen = ref(true)

/**
 * LLM API 参数在下方“API 配置”面板中编辑；
 * 不再使用后端 BaseURL/API Prefix 作为此面板内容
 */
// LLM API 配置启用与参数开关（仅前端显示，不联通后端）
const apiEnabled = ref(true)
const enableTemperature = ref(true)
const enableTopP = ref(true)
const enableTopK = ref(true)
const enableMaxContext = ref(true)
const enableMaxTokens = ref(true)
const enableStream = ref(true)
const enableFrequencyPenalty = ref(true)
const enablePresencePenalty = ref(true)

// 额外参数（源码默认已有的保持不变，补充 top_k 与 max_context）
const topK = ref<number>(0)
const maxContext = ref<number>(4095)

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

watch([apiOpen, promptsOpen, regexOpen, relativeOpen, inChatOpen], ([a, p, r, ro, io]) => {
  try {
    localStorage.setItem(
      PANEL_STATE_KEY,
      JSON.stringify({ apiOpen: a, promptsOpen: p, regexOpen: r, relativeOpen: ro, inChatOpen: io })
    )
  } catch {}
})

/* 初始化 Lucide 图标（组件挂载后） */
onMounted(() => {
  loadPanelStates()
  ;(window as any).lucide?.createIcons?.()
})

/* 使用 Store 管理预设数据 */
import { usePresetStore } from '../features/presets/store'
import type { PromptItem, PromptItemRelative, PromptItemInChat } from '@/features/presets/types'
import { SPECIAL_RELATIVE_TEMPLATES } from '@/features/presets/types'
import PresetPromptCard from '@/features/presets/components/PresetPromptCard.vue'

const store = usePresetStore()


/* 新增条目（Relative / In-Chat） */
const specialSelect = ref<string>('')
const newRelId = ref<string>('')
const newRelName = ref<string>('')
const relError = ref<string | null>(null)

const availableSpecials = computed(() =>
  SPECIAL_RELATIVE_TEMPLATES.filter(t => !store.relativePrompts.some(p => p.identifier === t.identifier))
)
const reservedIdSet = new Set(SPECIAL_RELATIVE_TEMPLATES.map(t => t.identifier))
const reservedNameSet = new Set(SPECIAL_RELATIVE_TEMPLATES.map(t => t.name))

function addSelectedSpecial() {
  relError.value = null
  const sel = specialSelect.value
  if (!sel) return
  const tpl = SPECIAL_RELATIVE_TEMPLATES.find(t => t.identifier === sel)
  if (!tpl) return
  if (store.relativePrompts.some(p => p.identifier === tpl.identifier)) {
    relError.value = '该一次性组件已存在'
    return
  }
  // 深拷贝，保持占位条目的 content 语义（不写入 content 字段）
  const item: PromptItemRelative = {
    identifier: tpl.identifier,
    name: tpl.name,
    enabled: tpl.enabled,
    role: tpl.role,
    position: tpl.position,
  }
  store.addPrompt(item as PromptItem)
  specialSelect.value = ''
  ;(window as any).lucide?.createIcons?.()
}

function addCustomRelative() {
  relError.value = null
  const id = newRelId.value.trim()
  const name = newRelName.value.trim()
  if (!id) {
    relError.value = '请填写 id'
    return
  }
  if (!name) {
    relError.value = '请填写名称'
    return
  }
  if (reservedIdSet.has(id) || reservedNameSet.has(name)) {
    relError.value = 'id 或 名称 与保留组件重复'
    return
  }
  if (store.relativePrompts.some(p => p.identifier === id)) {
    relError.value = 'id 已存在'
    return
  }
  if (store.relativePrompts.some(p => p.name === name)) {
    relError.value = '名称已存在'
    return
  }
  const item: PromptItemRelative = {
    identifier: id,
    name,
    enabled: null,
    role: 'system',
    position: 'relative',
  }
  store.addPrompt(item as PromptItem)
  newRelId.value = ''
  newRelName.value = ''
  ;(window as any).lucide?.createIcons?.()
}


// In-Chat 新增（右对齐 id + 名称 + 添加）
const newChatId = ref<string>('')
const newChatName = ref<string>('')
const chatError = ref<string | null>(null)

function addCustomInChat() {
  chatError.value = null
  const id = newChatId.value.trim()
  const name = newChatName.value.trim()
  if (!id) {
    chatError.value = '请填写 id'
    return
  }
  if (!name) {
    chatError.value = '请填写名称'
    return
  }
  // 唯一性校验：identifier 需全局唯一；名称在 In-Chat 内唯一
  if (store.prompts.some(p => p.identifier === id)) {
    chatError.value = 'id 已存在'
    return
  }
  if (store.inChatPrompts.some(p => p.name === name)) {
    chatError.value = '名称已存在'
    return
  }
  const item: PromptItemInChat = {
    identifier: id,
    name,
    enabled: true,
    role: 'system',
    position: 'in-chat',
    depth: 0,
    order: 0,
    content: ''
  }
  store.addPrompt(item as PromptItem)
  newChatId.value = ''
  newChatName.value = ''
  ;(window as any).lucide?.createIcons?.()
}

// 拖拽排序（Relative / In-Chat）
type PosType = 'relative' | 'in-chat'
const dragging = ref<{ position: PosType; id: string } | null>(null)
const dragOverId = ref<string | null>(null)

function onDragStart(position: PosType, id: string, ev: DragEvent) {
  dragging.value = { position, id }
  try {
    ev.dataTransfer?.setData('text/plain', id)
    ev.dataTransfer!.effectAllowed = 'move'
  } catch {}
}

function onDragOver(position: PosType, overId: string | null, ev: DragEvent) {
  if (dragging.value?.position !== position) return
  ev.preventDefault()
  dragOverId.value = overId
}

function onDrop(position: PosType, overId: string | null, ev: DragEvent) {
  if (dragging.value?.position !== position) return
  ev.preventDefault()
  const dId = dragging.value.id
  const list = position === 'relative' ? [...store.relativePrompts] : [...store.inChatPrompts]
  let ids = list.map(i => i.identifier)
  const fromIdx = ids.indexOf(dId)
  if (fromIdx < 0) return
  // remove original
  ids.splice(fromIdx, 1)
  if (overId && overId !== dId) {
    const toIdx = ids.indexOf(overId)
    const insertIdx = toIdx < 0 ? ids.length : toIdx
    ids.splice(insertIdx, 0, dId)
  } else {
    // drop at end
    ids.push(dId)
  }
  store.reorderWithinPosition(position, ids)
  // cleanup
  dragging.value = null
  dragOverId.value = null
  ;(window as any).lucide?.createIcons?.()
}

function onDropEnd(position: PosType, ev: DragEvent) {
  onDrop(position, null, ev)
}

function onDragEnd() {
  dragging.value = null
  dragOverId.value = null
}
</script>

<template>
  <!-- 仅 Preset 视图的内容（不包含三栏布局与顶部栏） -->
  <section class="space-y-6">
    <!-- 页面标题 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i data-lucide="settings-2" class="w-5 h-5 text-black"></i>
          <h2>预设编辑器</h2>
        </div>
        <div class="text-xs text-black/60">本页为 UI 演示，保存与联通待后续</div>
      </div>
    </div>

    <!-- API 配置（默认收起） -->
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

        <!-- 参数编辑（仅 UI 显示，不联通后端） -->
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
              type="number"
              min="0"
              max="2"
              step="0.01"
              v-model.number="temperature"
              :disabled="!apiEnabled || !enableTemperature"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
              placeholder="0.00"
            />
            <div class="text-xs text-black/60 mt-1">当前：{{ temperature.toFixed(2) }}</div>
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
              type="number"
              min="0"
              max="1"
              step="0.01"
              v-model.number="topP"
              :disabled="!apiEnabled || !enableTopP"
              class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
              placeholder="0.00"
            />
            <div class="text-xs text-black/60 mt-1">当前：{{ topP.toFixed(2) }}</div>
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

    <!-- 提示词编辑（默认展开） -->
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
        <!-- 左侧生成参数已迁移到“API 配置”面板，此处仅保留右侧提示词条目 -->

        <!-- 右：提示词条目 -->
        <div class="space-y-4">
          <div class="border border-gray-200 rounded-4 p-4 transition-all duration-200 ease-soft hover:shadow-elevate">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-2">
                <i data-lucide="list" class="w-4 h-4 text-black"></i>
                <span class="text-sm font-medium text-black">提示词条目</span>
              </div>
            </div>
            <div class="space-y-6">
              <!-- Relative 条目 -->
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

                <!-- 新增 Relative：一次性组件 + 自定义 -->
                <div v-show="relativeOpen" class="space-y-2 mb-2">
                  <div class="grid grid-cols-1 lg:grid-cols-2 gap-2">
                    <!-- 一次性组件选择（仅显示尚未添加过的保留组件） -->
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

                    <!-- 自定义 Relative（允许设定 id 与 名称；禁止与保留组件重名/重 id） -->
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

                <!-- 已有 Relative 列表 -->
                <div v-show="relativeOpen" class="space-y-2">
                  <div
                    v-for="it in store.relativePrompts"
                    :key="it.identifier"
                    class="flex items-stretch gap-2 group"
                    :class="{'dragging-item': dragging && dragging.id === it.identifier && dragging.position === 'relative'}"
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
                      <i data-lucide="grip-vertical" class="w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
                    </div>
                    <div class="flex-1" :class="{'drag-over': dragOverId === it.identifier && dragging && dragging.position === 'relative'}">
                      <PresetPromptCard :item="it" />
                    </div>
                  </div>
                  <div
                    class="h-3"
                    @dragover.prevent="onDragOver('relative', null, $event)"
                    @drop.prevent="onDropEnd('relative', $event)"
                  />
                </div>
              </div>

              <!-- In-Chat 条目 -->
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
                    v-for="it in store.inChatPrompts"
                    :key="it.identifier"
                    class="flex items-stretch gap-2 group"
                    :class="{'dragging-item': dragging && dragging.id === it.identifier && dragging.position === 'in-chat'}"
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
                      <i data-lucide="grip-vertical" class="w-4 h-4 text-black opacity-60 group-hover:opacity-100"></i>
                    </div>
                    <div class="flex-1" :class="{'drag-over': dragOverId === it.identifier && dragging && dragging.position === 'in-chat'}">
                      <PresetPromptCard :item="it" />
                    </div>
                  </div>
                  <div
                    class="h-3"
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

    <!-- 正则编辑（默认展开） -->
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
        <!-- 示例规则条目 -->
        <div class="border border-gray-200 rounded-4 p-3 transition-all duration-200 ease-soft hover:shadow-elevate">
          <div class="flex items-center justify-between">
            <div class="text-sm">
              <span class="font-mono">preset_rule_example</span>
              <span class="text-black/60 ml-2">状态：启用</span>
            </div>
            <div class="flex items-center gap-2">
              <button
                class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
              >
                编辑
              </button>
              <button
                class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
              >
                复制
              </button>
            </div>
          </div>
          <div class="mt-2 text-xs text-black/70 leading-6">
            find: <span class="font-mono">示例</span> →
            replace: <span class="font-mono">【预设替换】</span>，
            targets: <span class="font-mono">user, assistant</span>，
            placement: <span class="font-mono">after_macro</span>
          </div>
        </div>
      </div>

      <div v-show="regexOpen" class="mt-3">
        <button
          class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
        >
          新增规则
        </button>
      </div>
    </div>
  </section>
</template>
<style scoped>
/* 悬浮滑条（透明导轨，不影响布局高度）
   使用方式：给 range 加上 class="overlay-range"
   注意：当前 API 配置面板已将 Temperature/TopP 改为数值输入，不再使用滑条。
   此样式供后续可能新增的滑条控件复用。 */
.overlay-range {
  position: absolute; /* 由容器负责定位（relative），滑条悬浮在容器之上 */
  left: 0;
  right: 0;
  top: -12px; /* 根据需求微调，使不占用布局空间 */
  pointer-events: auto;
}

/* 导轨透明（WebKit/Chromium） */
.overlay-range::-webkit-slider-runnable-track {
  background: transparent !important;
  height: 0 !important; /* 避免占据布局空间 */
  border: none !important;
}
/* 拇指样式（可选，维持可见） */
.overlay-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  background: #111;
  border-radius: 50%;
  border: 2px solid #111;
}

/* 导轨透明（Firefox） */
.overlay-range::-moz-range-track {
  background: transparent !important;
  height: 0 !important;
  border: none !important;
}
.overlay-range::-moz-range-thumb {
  width: 12px;
  height: 12px;
  background: #111;
  border-radius: 50%;
  border: 2px solid #111;
}

/* 抓手光标与 hover 提示对比度 */
.cursor-grab {
  cursor: grab;
}
.cursor-grab:active {
  cursor: grabbing;
}
</style>