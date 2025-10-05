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
import GlobalPromptPreview from './features/preview/components/GlobalPromptPreview.vue'

import { usePresetStore } from './features/presets/store'
import { useCharacterStore } from '@/features/characters/store'
import { usePersonaStore } from '@/features/persona/store'
import { useHistoryStore } from '@/features/history/store'
import { useFileManagerStore } from '@/features/files/fileManager'

type TabKey = 'presets' | 'files' | 'worldbook' | 'characters' | 'regex' | 'user' | 'history'
const currentTab = ref<TabKey>('presets')

const presetStore = usePresetStore()
const characterStore = useCharacterStore()
const personaStore = usePersonaStore()
const historyStore = useHistoryStore()
const fileManager = useFileManagerStore()

onMounted(() => {
  presetStore.load()
  characterStore.load()
  personaStore.load()
  historyStore.load()
  fileManager.load()
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

    // 捕获当前页签快照，避免异步过程中切换导致误判
    const mainTab = currentTab.value

    // 如果是在“文件库”页签，则完全依赖文件库内部的类型（不做任何类型推断）
    const currentType = (fileManager as any)?.getCurrentType || 'presets'
    const targetTab = mainTab === 'files' ? currentType : mainTab

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

    // 重要：不进行文件类型检查。严格按 targetTab 分流导入与入库。

    // 角色卡（SmartTraven 角色卡结构）
    if (targetTab === 'characters') {
      try {
        characterStore.setCharacter(json, file.name)
      } catch {}
      try { fileManager.upsertFile('characters', file.name, json) } catch {}
      return
    }

    // 用户信息（Persona）
    if (targetTab === 'user') {
      try { personaStore.setPersona(json, file.name) } catch {}
      try { fileManager.upsertFile('user', file.name, json) } catch {}
      return
    }

    // 正则（数组或 { regex_rules: [] }）
    if (targetTab === 'regex') {
      const rules: any[] = Array.isArray(json)
        ? json
        : (Array.isArray(json?.regex_rules) ? json.regex_rules : [])
      try {
        if (!presetStore.activeData) {
          presetStore.upsertFile({
            name: 'RegexPanel',
            enabled: true,
            data: { setting: {}, prompts: [], regex_rules: [] } as any,
          } as any)
        }
        presetStore.setRegexRules(rules as any)
      } catch {}
      try { fileManager.upsertFile('regex', file.name, json) } catch {}
      return
    }

    // 对话历史：入库 + 镜像到历史面板
    if (targetTab === 'history') {
      try { historyStore.setDoc(json, file.name) } catch {}
      try { fileManager.upsertFile('history', file.name, json) } catch {}
      return
    }

    // 世界书（仅当在世界书页签下）
    if (targetTab === 'worldbook') {
      let flat: any[] = []
      if (Array.isArray(json?.entries)) {
        flat = flattenObjects(json.entries)
      } else if (Array.isArray(json?.world_book?.entries)) {
        flat = flattenObjects(json.world_book.entries)
      } else if (Array.isArray(json)) {
        flat = flattenObjects(json)
      } else {
        try { fileManager.upsertFile('worldbook', file.name, json) } catch {}
        return
      }
      try { presetStore.setWorldBooks(flat as any) } catch {}
      try { fileManager.upsertFile('worldbook', file.name, json) } catch {}
      return
    }

    // 预设（仅当在预设页签或文件库当前类型为 presets 时）
    if (targetTab === 'presets') {
      try {
        await presetStore.importFromFile(file)
        try { fileManager.upsertFile('presets', file.name, json) } catch {}
      } catch {
        alert('导入失败：预设数据结构不符合预期')
      }
      return
    }

    // 未识别页签保护（理论不应到达）
    alert('导入失败：当前页签未配置导入行为')
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
  } else if (currentTab.value === 'history') {
    const res = historyStore.exportActive()
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

    <!-- 右侧预览插槽：全局提示词预览组件 -->
    <template #right>
      <GlobalPromptPreview />
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
