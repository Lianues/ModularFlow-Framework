<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/**
 * 参考正则规则结构（backend_projects/SmartTraven/data/regex_rules/remove_xml_tags.json）
 * 本视图仅做 UI 占位与交互演示，暂不接入后端
 */

type Placement = 'before_macro' | 'after_macro' | string
interface Rule {
  id: string
  name: string
  enabled?: boolean
  find_regex: string
  replace_regex: string
  targets?: string[]
  placement?: Placement
  views?: string[]
  min_depth?: number
  max_depth?: number
  description?: string
}

const rules = ref<Rule[]>([
  {
    id: 'remove_xml_tags_rule',
    name: 'Remove XML Tags',
    enabled: true,
    find_regex: '<([a-zA-Z0-9]+)>(.|\\n)*?</\\\\1>',
    replace_regex: '移除xml',
    targets: ['preset', 'world_book', 'history'],
    placement: 'before_macro',
    views: ['user_view', 'assistant_view'],
    description: 'Removes XML tags and their content, affecting only the user_view.'
  },
  {
    id: '53a86be21-aaa329111a-45b5-88c1-4209d4d232f1a11',
    name: '状态栏',
    enabled: true,
    find_regex: '<StatusPlaceHolderImpl/>',
    replace_regex: '这里是状态栏',
    targets: ['history'],
    placement: 'after_macro',
    views: ['user_view'],
    min_depth: 0,
    max_depth: 5,
    description: '仅对Markdown内容生效'
  }
])

const search = ref('')
const placementFilter = ref<'all' | Placement>('all')
const onlyEnabled = ref(false)

const targetFilters = ref<{ [k: string]: boolean }>({
  preset: false,
  world_book: false,
  history: false
})
const viewFilters = ref<{ [k: string]: boolean }>({
  user_view: false,
  assistant_view: false
})

const filtered = computed(() => {
  return rules.value
    .filter(r => (onlyEnabled.value ? r.enabled !== false : true))
    .filter(r => (placementFilter.value === 'all' ? true : r.placement === placementFilter.value))
    .filter(r => {
      const anyTargetSelected = Object.values(targetFilters.value).some(v => v)
      if (!anyTargetSelected) return true
      const set = new Set(r.targets || [])
      return Object.entries(targetFilters.value).every(([k, v]) => (v ? set.has(k) : true))
    })
    .filter(r => {
      const anyViewSelected = Object.values(viewFilters.value).some(v => v)
      if (!anyViewSelected) return true
      const set = new Set(r.views || [])
      return Object.entries(viewFilters.value).every(([k, v]) => (v ? set.has(k) : true))
    })
    .filter(r => {
      if (!search.value) return true
      const hay = `${r.id} ${r.name} ${r.find_regex} ${r.replace_regex} ${(r.targets || []).join(' ')} ${(r.views || []).join(' ')} ${r.description || ''}`
      return hay.toLowerCase().includes(search.value.toLowerCase())
    })
})

function toggleEnabled(r: Rule) {
  r.enabled = !r.enabled
}

onMounted(() => {
  ;(window as any).lucide?.createIcons?.()
})
</script>

<template>
  <section class="space-y-6">
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <i data-lucide="code" class="w-6 h-6 text-black"></i>
          <h2>正则规则</h2>
        </div>
        <div class="text-xs text-black/50">参考：backend_projects/SmartTraven/data/regex_rules/remove_xml_tags.json</div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-6 gap-4">
        <div class="md:col-span-3">
          <label class="block text-sm font-medium text-black mb-2">搜索</label>
          <input
            v-model="search"
            type="text"
            placeholder="按名称、ID、正则、描述搜索..."
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-black mb-2">阶段（placement）</label>
          <select
            v-model="placementFilter"
            class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
          >
            <option value="all">全部</option>
            <option value="before_macro">before_macro</option>
            <option value="after_macro">after_macro</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-black mb-2">Targets</label>
          <div class="flex items-center gap-3">
            <label class="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="targetFilters.preset" class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2" />
              <span>preset</span>
            </label>
            <label class="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="targetFilters.world_book" class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2" />
              <span>world_book</span>
            </label>
            <label class="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="targetFilters.history" class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2" />
              <span>history</span>
            </label>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-black mb-2">Views</label>
          <div class="flex items-center gap-3">
            <label class="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="viewFilters.user_view" class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2" />
              <span>user_view</span>
            </label>
            <label class="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="viewFilters.assistant_view" class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2" />
              <span>assistant_view</span>
            </label>
          </div>
        </div>

        <div class="md:col-span-1 flex items-end">
          <label class="inline-flex items-center space-x-2 select-none">
            <input type="checkbox" v-model="onlyEnabled" class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2" />
            <span class="text-sm text-black/80">仅启用</span>
          </label>
        </div>
      </div>
    </div>

    <div class="space-y-4">
      <div
        v-for="r in filtered"
        :key="r.id"
        class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <div class="flex items-center gap-2">
                <i data-lucide="sparkles" class="w-4 h-4 text-black"></i>
                <h3 class="text-lg font-bold text-black">{{ r.name }}</h3>
              </div>
              <span class="text-xs text-black/60">ID: {{ r.id }}</span>
              <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ r.placement ?? '—' }}</span>
              <span v-if="r.min_depth !== undefined" class="text-xs text-black/60">min: {{ r.min_depth }}</span>
              <span v-if="r.max_depth !== undefined" class="text-xs text-black/60">max: {{ r.max_depth }}</span>
            </div>

            <div class="mt-2 flex flex-wrap items-center gap-2">
              <span v-for="t in r.targets || []" :key="t" class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ t }}</span>
              <span v-for="v in r.views || []" :key="v" class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ v }}</span>
            </div>

            <p v-if="r.description" class="mt-2 text-xs text-black/60">{{ r.description }}</p>
          </div>

          <div class="flex items-center gap-2">
            <button
              class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
            >
              编辑
            </button>
            <button
              class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
            >
              测试
            </button>
            <button
              class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
              @click="toggleEnabled(r)"
            >
              {{ r.enabled === false ? '启用' : '禁用' }}
            </button>
          </div>
        </div>

        <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="border border-gray-200 rounded-4 p-3">
            <div class="text-xs font-medium text-black mb-2">find_regex</div>
            <div class="text-xs text-black/70 font-mono break-all whitespace-pre-wrap">{{ r.find_regex }}</div>
          </div>
          <div class="border border-gray-200 rounded-4 p-3">
            <div class="text-xs font-medium text-black mb-2">replace_regex</div>
            <div class="text-xs text-black/70 font-mono break-all whitespace-pre-wrap">{{ r.replace_regex }}</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 仅少量局部样式，整体使用 Tailwind 工具类 */
</style>