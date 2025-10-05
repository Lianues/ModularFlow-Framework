<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/**
 * 参考后端 world_book 结构（backend_projects/SmartTraven/data/world_books/参考用main_world.json）
 * 本视图仅做 UI 占位与交互演示，暂不接入后端
 */

type Mode = 'always' | 'conditional' | string
type Position = 'before_char' | 'user' | 'after_char' | 'system' | 'in-chat' | string

interface WorldEntry {
  id?: number
  name: string
  content?: string
  mode?: Mode
  position?: Position
  order?: number
  enabled?: boolean
  keys?: string[]
  depth?: number
}

const entries = ref<WorldEntry[]>([
  {
    id: 1,
    name: '未来都市',
    content: '故事发生在一座名为「新星港」的未来都市。这里科技高度发达，悬浮车穿梭于摩天大楼之间。',
    mode: 'always',
    position: 'before_char',
    order: 5,
    enabled: true
  },
  {
    id: 2,
    name: '艾拉的背景',
    keys: ['艾拉', '工程师'],
    content: '艾拉是新星港最顶尖的机械工程师之一。',
    mode: 'conditional',
    position: 'user',
    depth: 0,
    order: 101,
    enabled: true
  }
])

// 过滤/检索
const search = ref('')
const modeFilter = ref<'all' | Mode>('all')
const posFilter = ref<'all' | Position>('all')
const onlyEnabled = ref(false)

const filtered = computed(() =>
  entries.value
    .filter((e) => (onlyEnabled.value ? e.enabled !== false : true))
    .filter((e) => (modeFilter.value === 'all' ? true : e.mode === modeFilter.value))
    .filter((e) => (posFilter.value === 'all' ? true : e.position === posFilter.value))
    .filter((e) => {
      if (!search.value) return true
      const hay = `${e.name} ${e.content ?? ''} ${(e.keys ?? []).join(' ')}`
      return hay.toLowerCase().includes(search.value.toLowerCase())
    })
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
)

function toggleEnabled(item: WorldEntry) {
  item.enabled = !item.enabled
}

onMounted(() => {
  ;(window as any).lucide?.createIcons?.()
})
</script>

<template>
  <section class="space-y-6">
    <!-- 概览 -->
    <div
      class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate"
    >
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <i data-lucide="book-open" class="w-6 h-6 text-black"></i>
          <h2>世界书</h2>
        </div>
        <div class="text-xs text-black/50">
          参考数据结构：backend_projects/SmartTraven/data/world_books/参考用main_world.json
        </div>
      </div>

      <!-- 工具条 -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-black mb-2">搜索</label>
          <input
            v-model="search"
            type="text"
            placeholder="按名称、内容、keys 搜索..."
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-black mb-2">模式</label>
          <select
            v-model="modeFilter"
            class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
          >
            <option value="all">全部</option>
            <option value="always">always</option>
            <option value="conditional">conditional</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-black mb-2">位置</label>
          <select
            v-model="posFilter"
            class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
          >
            <option value="all">全部</option>
            <option value="before_char">before_char</option>
            <option value="user">user</option>
            <option value="after_char">after_char</option>
          </select>
        </div>
      </div>

      <div class="mt-4 flex items-center justify-between">
        <label class="inline-flex items-center space-x-2 select-none">
          <input
            type="checkbox"
            v-model="onlyEnabled"
            class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
          />
          <span class="text-sm text-black/80">仅显示启用</span>
        </label>

        <div class="flex items-center space-x-2 text-sm text-black/60">
          <span>总数：{{ entries.length }}</span>
          <span class="mx-1">/</span>
          <span>已过滤：{{ filtered.length }}</span>
        </div>
      </div>
    </div>

    <!-- 列表 -->
    <div class="space-y-4">
      <div
        v-for="item in filtered"
        :key="item.id ?? item.name"
        class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center space-x-2">
              <i data-lucide="layers" class="w-4 h-4 text-black"></i>
              <h3 class="text-lg font-bold text-black">{{ item.name }}</h3>
              <span
                class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent"
                >{{ item.mode ?? '—' }}</span
              >
              <span
                class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent"
                >{{ item.position ?? '—' }}</span
              >
              <span v-if="item.order !== undefined" class="text-xs text-black/60">#{{ item.order }}</span>
              <span v-if="item.depth !== undefined" class="text-xs text-black/60">depth: {{ item.depth }}</span>
            </div>
            <div v-if="item.keys?.length" class="mt-2 text-xs text-black/60">
              keys：<span class="font-mono">{{ item.keys.join(', ') }}</span>
            </div>
          </div>

          <div class="flex items-center space-x-2">
            <button
              class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
            >
              编辑
            </button>
            <button
              class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
            >
              复制
            </button>
            <button
              class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
              @click="toggleEnabled(item)"
            >
              {{ item.enabled === false ? '启用' : '禁用' }}
            </button>
          </div>
        </div>

        <div class="mt-3 text-sm text-black/70 leading-6">
          <p class="line-clamp-3">
            {{ item.content || '（暂无内容）' }}
          </p>
        </div>
      </div>
    </div>

    <!-- 新建条目（占位） -->
    <div
      class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate"
    >
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center space-x-2">
          <i data-lucide="plus" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">新增条目</span>
        </div>
        <button
          class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
        >
          提交
        </button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-black mb-2">名称</label>
          <input
            type="text"
            placeholder="例如：新条目"
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-black mb-2">模式</label>
          <select
            class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
          >
            <option value="always">always</option>
            <option value="conditional">conditional</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-black mb-2">位置</label>
          <select
            class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
          >
            <option value="before_char">before_char</option>
            <option value="user">user</option>
            <option value="after_char">after_char</option>
          </select>
        </div>
        <div class="md:col-span-3">
          <label class="block text-sm font-medium text-black mb-2">内容</label>
          <textarea
            rows="3"
            placeholder="在这里输入条目的描述内容..."
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          ></textarea>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 仅少量局部样式，整体使用 Tailwind 工具类 */
</style>