<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/**
 * 参考角色卡结构（backend_projects/SmartTraven/data/characters/*）
 * - 心与露.json：包含 message[], world_book.entries[], regex_rules[], extensions.world 等
 * - 许莲笙.json：包含 message[], world_book.entries[], regex_rules[], extensions.world 等
 * 本视图仅做 UI 占位与交互演示，暂不接入后端
 */

interface CharacterItem {
  name: string
  description?: string
  world?: string
  messageCount?: number
  worldEntryCount?: number
  regexRuleCount?: number
}

const items = ref<CharacterItem[]>([
  {
    name: '心与露',
    description: '温馨治愈的日常轻喜剧，夹杂少女恋心的成长与酸涩（示例预览）',
    world: '心与露',
    messageCount: 4,
    worldEntryCount: 14,
    regexRuleCount: 3
  },
  {
    name: '许莲笙',
    description:
      '缟尔玛女子学院的萝莉老师 × 不良少女的故事。外表柔软、内心坚韧的老师与叛逆天才少女的互动（示例预览）',
    world: '不良少女和萝莉老师-改',
    messageCount: 2,
    worldEntryCount: 6,
    regexRuleCount: 5
  }
])

// 过滤
const search = ref('')
const worldFilter = ref<'all' | string>('all')

const worlds = computed(() => {
  const set = new Set<string>()
  items.value.forEach(i => i.world && set.add(i.world))
  return Array.from(set)
})

const filtered = computed(() =>
  items.value.filter((i) => {
    if (worldFilter.value !== 'all' && i.world !== worldFilter.value) return false
    if (!search.value) return true
    const hay = `${i.name} ${i.description ?? ''} ${i.world ?? ''}`
    return hay.toLowerCase().includes(search.value.toLowerCase())
  })
)

onMounted(() => {
  ;(window as any).lucide?.createIcons?.()
})
</script>

<template>
  <section class="space-y-6">
    <!-- 顶部卡片 -->
    <div
      class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate"
    >
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <i data-lucide="user" class="w-6 h-6 text-black"></i>
          <h2>角色卡</h2>
        </div>
        <div class="text-xs text-black/50">
          参考数据结构：backend_projects/SmartTraven/data/characters/*.json
        </div>
      </div>

      <!-- 工具条 -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div class="md:col-span-3">
          <label class="block text-sm font-medium text-black mb-2">搜索</label>
          <input
            v-model="search"
            type="text"
            placeholder="按名称、描述、世界筛选..."
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
        </div>
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-black mb-2">世界</label>
          <select
            v-model="worldFilter"
            class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-white focus:outline-none focus:ring-2 focus:ring-gray-800"
          >
            <option value="all">全部</option>
            <option v-for="w in worlds" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 列表 -->
    <div class="space-y-4">
      <div
        v-for="c in filtered"
        :key="c.name"
        class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <div class="flex items-center space-x-2">
                <i data-lucide="id-card" class="w-4 h-4 text-black"></i>
                <h3 class="text-lg font-bold text-black">{{ c.name }}</h3>
              </div>
              <span
                v-if="c.world"
                class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent"
              >
                {{ c.world }}
              </span>

              <div class="ml-1 flex items-center gap-2 text-xs text-black/60">
                <span class="inline-flex items-center gap-1">
                  <i data-lucide="message-square" class="w-3.5 h-3.5"></i>{{ c.messageCount ?? 0 }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <i data-lucide="book-open" class="w-3.5 h-3.5"></i>{{ c.worldEntryCount ?? 0 }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <i data-lucide="regex" class="w-3.5 h-3.5"></i>{{ c.regexRuleCount ?? 0 }}
                </span>
              </div>
            </div>

            <p class="mt-2 text-sm text-black/70 leading-6 line-clamp-2">
              {{ c.description || '（暂无描述）' }}
            </p>
          </div>

          <div class="flex items-center space-x-2">
            <button
              class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
            >
              打开
            </button>
            <button
              class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
            >
              编辑
            </button>
          </div>
        </div>

        <!-- 结构预览（示例） -->
        <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="border border-gray-200 rounded-4 p-3">
            <div class="text-xs font-medium text-black mb-2">概览</div>
            <ul class="text-xs text-black/60 space-y-1">
              <li class="flex items-center gap-1">
                <i data-lucide="message-square" class="w-3.5 h-3.5"></i>消息条数：{{ c.messageCount ?? 0 }}
              </li>
              <li class="flex items-center gap-1">
                <i data-lucide="book" class="w-3.5 h-3.5"></i>世界书条目：{{ c.worldEntryCount ?? 0 }}
              </li>
              <li class="flex items-center gap-1">
                <i data-lucide="code" class="w-3.5 h-3.5"></i>正则规则：{{ c.regexRuleCount ?? 0 }}
              </li>
            </ul>
          </div>

          <div class="border border-gray-200 rounded-4 p-3">
            <div class="text-xs font-medium text-black mb-2">提示词片段（示例）</div>
            <div class="text-xs text-black/60" v-pre>
              Write {{char}}'s next reply in a fictional chat between {{char}} and {{user}}.
            </div>
          </div>

          <div class="border border-gray-200 rounded-4 p-3">
            <div class="text-xs font-medium text-black mb-2">标签</div>
            <div class="flex flex-wrap gap-2">
              <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">character</span>
              <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">prompt</span>
              <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">world</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建角色（占位） -->
    <div
      class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate"
    >
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center space-x-2">
          <i data-lucide="plus" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">新增角色</span>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
          >
            提交
          </button>
          <button
            class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
          >
            重置
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-black mb-2">名称</label>
          <input
            type="text"
            placeholder="如：新角色"
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-black mb-2">世界</label>
          <input
            type="text"
            placeholder="如：世界名称"
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
        </div>
        <div class="md:col-span-3">
          <label class="block text-sm font-medium text-black mb-2">描述</label>
          <textarea
            rows="3"
            placeholder="在这里输入角色的描述..."
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          ></textarea>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 局部样式尽量轻量化，主体交由 Tailwind 工具类 */
</style>