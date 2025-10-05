<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppShell from './layouts/AppShell.vue'
import Sidebar from './components/Sidebar.vue'
import PresetView from './views/PresetView.vue'
import WorldbookView from './views/WorldbookView.vue'
import CharactersView from './views/CharactersView.vue'
import RegexView from './views/RegexView.vue'
import UserView from './views/UserView.vue'
import HistoryView from './views/HistoryView.vue'
import FileManagerView from './views/FileManagerView.vue'

import { usePresetStore } from './features/presets/store'
import { useCharacterStore } from '@/features/characters/store'
import { usePersonaStore } from '@/features/persona/store'

type TabKey = 'presets' | 'files' | 'worldbook' | 'characters' | 'regex' | 'user' | 'history'
const currentTab = ref<TabKey>('presets')

const presetStore = usePresetStore()
const characterStore = useCharacterStore()
const personaStore = usePersonaStore()

onMounted(() => {
  presetStore.load()
  characterStore.load()
  personaStore.load()
})

/* 顶部右侧：导入（选择 JSON），导出（下载当前）
   - 预设页：仍按 PresetData 导入/导出
   - 世界书页：仅支持 {entries:[...]} 或 {world_book:{entries:[...]}} 导入/导出 */
function handleImport() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json,application/json'
  input.onchange = async () => {
    const file = input.files?.[0]
    if (!file) return

    // 读取文本并清理 BOM/不可见字符
    let text = ''
    try {
      text = await file.text()
    } catch {
      alert('导入失败：无法读取文件')
      return
    }
    if (text && text.charCodeAt(0) === 0xFEFF) text = text.slice(1)
    text = text.replace(/\uFEFF/g, '').trim()

    let json: any
    try {
      json = JSON.parse(text)
    } catch {
      alert('导入失败：JSON 解析错误')
      return
    }

    // 工具：扁平化数组/嵌套数组为对象列表
    const flattenObjects = (input: any): any[] => {
      const out: any[] = []
      const walk = (x: any) => {
        if (Array.isArray(x)) {
          for (const it of x) walk(it)
        } else if (x && typeof x === 'object') {
          out.push(x)
        }
      }
      walk(input)
      return out
    }

    // 启发式判断世界书 JSON（仅支持 {entries:[...]} 或 {world_book:{entries:[...]}}）
    const isWorldBooksJson = (val: any): boolean => {
      let objs: any[] = []
      if (Array.isArray(val?.entries)) {
        objs = flattenObjects(val.entries)
      } else if (Array.isArray(val?.world_book?.entries)) {
        objs = flattenObjects(val.world_book.entries)
      }
      if (!objs.length) return false
      let score = 0
      for (const o of objs.slice(0, Math.min(5, objs.length))) {
        if (o && typeof o === 'object') {
          if (typeof o.position === 'string') score++
          if ('mode' in o) score++
          if ('content' in o) score++
          if ('name' in o) score++
        }
      }
      return score >= 3
    }

    // 角色卡页签：优先按角色卡导入（防止被世界书检测抢占）
    if (currentTab.value === 'characters') {
      try {
        characterStore.setCharacter(json, file.name)
      } catch {
        alert('导入失败：角色卡数据结构不符合预期')
      }
      return
    }

    // 用户信息页签：按用户信息（Persona）导入
    if (currentTab.value === 'user') {
      try {
        personaStore.setPersona(json, file.name)
      } catch {
        alert('导入失败：用户信息数据结构不符合预期')
      }
      return
    }

    // 世界书页或检测为世界书数据时，按世界书导入（仅新格式）
    if (currentTab.value === 'worldbook' || isWorldBooksJson(json)) {
      let flat: any[] = []
      if (Array.isArray(json?.entries)) {
        flat = flattenObjects(json.entries)
      } else if (Array.isArray(json?.world_book?.entries)) {
        flat = flattenObjects(json.world_book.entries)
      } else {
        alert('导入失败：世界书数据结构仅支持 {entries:[...]} 或 {world_book:{entries:[...]}}')
        return
      }
      try {
        presetStore.setWorldBooks(flat as any)
      } catch {
        alert('导入失败：世界书数据结构不符合预期')
      }
      return
    }

    // 否则按预设数据导入（完整 PresetData）
    try {
      await presetStore.importFromFile(file)
    } catch {
      alert('导入失败：预设数据结构不符合预期')
    }
  }
  input.click()
}

function handleExport() {
  if (currentTab.value === 'worldbook') {
    const res = presetStore.exportWorldBooks()
    if (!res) return
    const blob = new Blob([res.json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = res.filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } else if (currentTab.value === 'characters') {
    const res = characterStore.exportCharacter()
    if (!res) return
    const blob = new Blob([res.json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = res.filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } else if (currentTab.value === 'user') {
    const res = personaStore.exportPersona()
    if (!res) return
    const blob = new Blob([res.json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = res.filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } else {
    const res = presetStore.exportActive()
    if (!res) return
    const blob = new Blob([res.json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = res.filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }
}
</script>

<template>
  <AppShell @import-files="handleImport" @export-file="handleExport">
    <!-- 左侧栏插槽：侧边导航 -->
    <template #left>
      <Sidebar v-model="currentTab" />
    </template>

    <!-- 中间主视图区 -->
    <template #main>
      <section v-if="currentTab === 'presets'" class="h-full">
        <PresetView />
      </section>

      <section v-else-if="currentTab === 'files'" class="h-full">
        <FileManagerView />
      </section>

      <section v-else-if="currentTab === 'worldbook'" class="h-full">
        <WorldbookView />
      </section>

      <section v-else-if="currentTab === 'characters'" class="h-full">
        <CharactersView />
      </section>

      <section v-else-if="currentTab === 'regex'" class="h-full">
        <RegexView />
      </section>

      <section v-else-if="currentTab === 'user'" class="h-full">
        <UserView />
      </section>

      <section v-else-if="currentTab === 'history'" class="h-full">
        <HistoryView />
      </section>

      <section v-else class="bg-white rounded-4 card-shadow border border-gray-200 p-8 transition-all duration-200 ease-soft hover:shadow-elevate">
        <div class="text-center">
          <i data-lucide="circle-dashed" class="w-10 h-10 text-black/40 mx-auto mb-4"></i>
          <p class="text-black/60">未知视图：{{ currentTab }}</p>
        </div>
      </section>
    </template>

    <!-- 右侧预览插槽（占位，后续接入全局提示词拼装状态） -->
    <template #right>
      <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
        <div class="flex items-center space-x-2 mb-3">
          <i data-lucide="eye" class="w-5 h-5 text-black"></i>
          <h3 class="text-lg font-bold text-black">全局提示词预览</h3>
        </div>
        <div class="text-sm text-black/60">
          暂不实现实时构建。后续将基于全局状态拼装完整提示词。
        </div>
      </div>
    </template>
  </AppShell>
</template>

<style scoped>
/* 局部样式保持最轻，仅少量覆盖；其余交由 Tailwind 工具类 */
</style>

<style>
/* Range 输入美化（全局，黑白风格） */
input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  width: 100%;
}
input[type="range"]::-webkit-slider-runnable-track {
  height: 4px;
  background-color: #E5E7EB;
  border-radius: 9999px;
}
input[type="range"]::-moz-range-track {
  height: 4px;
  background-color: #E5E7EB;
  border-radius: 9999px;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  background: #111;
  border: 2px solid #111;
  border-radius: 50%;
  margin-top: -5px; /* 居中对齐轨道 */
  transition: transform 180ms cubic-bezier(0.2,0,0,1), box-shadow 180ms cubic-bezier(0.2,0,0,1);
}
input[type="range"]::-webkit-slider-thumb:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}
input[type="range"]::-moz-range-thumb {
  width: 14px;
  height: 14px;
  background: #111;
  border: 2px solid #111;
  border-radius: 50%;
  transition: transform 180ms cubic-bezier(0.2,0,0,1), box-shadow 180ms cubic-bezier(0.2,0,0,1);
}
input[type="range"]::-moz-range-thumb:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}
</style>
