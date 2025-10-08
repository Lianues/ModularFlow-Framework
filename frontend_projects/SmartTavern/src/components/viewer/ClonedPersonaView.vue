<script setup>
import { ref, reactive, onMounted, nextTick, watchEffect } from 'vue'

/**
 * 用户信息主面板（克隆自 PromptEditor 的 UserView 样式/交互）
 * - 使用本地 demo JSON 驱动（不依赖 Pinia/后端）
 * - 可选加载：@/data/persona_demo.json（不存在时忽略）
 * - 支持：文件名重命名、基础信息(name/description) 编辑与重置
 */

/* ---------------------- Demo 数据（可被外部 JSON 覆盖） ---------------------- */
const demoData = reactive({
  fileName: 'PersonaDemo.json',
  name: '示例用户 · 简洁偏好',
  description: '该用户偏好简洁明了的回答，期望先给出要点再展开说明；对技术问题接受代码示例与分步讲解。'
})

async function tryLoadExternalJson() {
  try {
    const mod = await import('@/data/persona_demo.json')
    const ext = (mod && (mod.default || mod)) || null
    if (ext && typeof ext === 'object') {
      if (typeof ext.fileName === 'string') demoData.fileName = ext.fileName
      if (typeof ext.name === 'string') demoData.name = ext.name
      if (typeof ext.description === 'string') demoData.description = ext.description
    }
  } catch {
    // ignore: 演示文件不存在时静默
  }
}

/* ---------------------- 顶部：文件名重命名（演示） ---------------------- */
const fileTitle = ref('')
const renameError = ref(null)
function renamePersonaFile() {
  renameError.value = null
  const nn = (fileTitle.value || '').trim()
  if (!nn) { renameError.value = '文件名不能为空'; return }
  demoData.fileName = nn
}

/* ---------------------- 基本信息编辑（name/description） ---------------------- */
const nameDraft = ref('')
const descDraft = ref('')
function saveName() { demoData.name = nameDraft.value }
function saveDesc() { demoData.description = descDraft.value }
function resetAll() {
  nameDraft.value = demoData.name
  descDraft.value = demoData.description
  nextTick(() => (window?.lucide?.createIcons?.()))
}

/* ---------------------- 面板开合状态（演示） ---------------------- */
const PANEL_STATE_KEY = 'persona_viewer_ui_panels'
const baseOpen = ref(true)
function loadPanelStates() {
  try {
    const raw = localStorage.getItem(PANEL_STATE_KEY)
    if (!raw) return
    const o = JSON.parse(raw)
    if (typeof o.baseOpen === 'boolean') baseOpen.value = o.baseOpen
  } catch {}
}
function savePanelStates() {
  try {
    localStorage.setItem(PANEL_STATE_KEY, JSON.stringify({ baseOpen: baseOpen.value }))
  } catch {}
}

/* ---------------------- 初始化 ---------------------- */
onMounted(async () => {
  loadPanelStates()
  await tryLoadExternalJson()
  fileTitle.value = demoData.fileName || 'PersonaDemo.json'
  nameDraft.value = demoData.name || ''
  descDraft.value = demoData.description || ''
  await nextTick()
  window?.lucide?.createIcons?.()
})
watchEffect(savePanelStates)
</script>

<template>
  <section class="space-y-6">
    <!-- 概览 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between mb-2 gap-3">
        <div class="flex items-center gap-2">
          <i data-lucide="id-card" class="w-5 h-5 text-black"></i>
          <h2>用户信息</h2>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="fileTitle"
            placeholder="文件名.json"
            class="w-56 px-3 py-2 border border-gray-300 rounded-4 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800"
            @keyup.enter="renamePersonaFile"
            @blur="renamePersonaFile"
          />
          <button
            class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black text-sm hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
            @click="renamePersonaFile"
          >重命名</button>
        </div>
      </div>
      <p class="text-xs text-black/60">结构参考：backend_projects/SmartTavern/data/persona/用户2.json</p>
      <p v-if="renameError" class="text-xs text-red-600 mt-1">* {{ renameError }}</p>
    </div>

    <!-- 基本信息（仅 name / description） -->
    <div class="bg-white rounded-4 border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <i data-lucide="user" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">基本信息</span>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:shadow-elevate hover:-translate-y-0.5 transition-all duration-200 ease-soft text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
            @click="resetAll"
          >
            重置
          </button>
        </div>
      </div>

      <button
        type="button"
        class="w-full flex items-center justify-between mb-3 rounded-4"
        @click="baseOpen = !baseOpen"
      >
        <div class="flex items-center gap-2">
          <i data-lucide="chevron-right" class="w-4 h-4 text-black transition-transform duration-200 ease-soft"
             :class="baseOpen ? 'rotate-90' : ''"></i>
          <span class="text-sm font-medium text-black">展开/收起</span>
        </div>
      </button>

      <div v-show="baseOpen" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-black mb-2">名称</label>
          <input
            v-model="nameDraft"
            @blur="saveName"
            type="text"
            placeholder="输入名称"
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
        </div>

        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-black mb-2">描述</label>
          <textarea
            v-model="descDraft"
            @blur="saveDesc"
            rows="4"
            placeholder="输入描述..."
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          ></textarea>
        </div>
      </div>
    </div>

    <!-- 说明 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="text-xs text-black/60">
        说明：本面板仅维护单个用户信息 JSON（name / description）。导入与导出可在上层集成入口进行。
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 轻量样式，视觉保持与其他面板一致 */
</style>