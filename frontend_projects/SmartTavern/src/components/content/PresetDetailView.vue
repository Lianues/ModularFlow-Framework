<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  presetData: { type: Object, default: null }
})

// 演示用的占位数据（与 PromptEditor 格式一致）
const demoPresetData = ref({
  name: '演示预设 - 完整示例',
  api_config: {
    enabled: true,
    temperature: 1.0,
    top_p: 1.0,
    top_k: 0,
    max_context: 4095,
    max_tokens: 300,
    stream: true,
    frequency_penalty: 0,
    presence_penalty: 0
  },
  prompts: [
    {
      identifier: 'main',
      name: '主要提示词',
      enabled: true,
      role: 'system',
      position: 'relative',
      content: '你是一个友好的AI助手，请用简洁明了的方式回答问题。这是一个比较长的内容示例，用来展示多行文本的显示效果。'
    },
    {
      identifier: 'char_personality',
      name: '角色性格设定',
      enabled: true,
      role: 'system',
      position: 'relative',
      content: '保持礼貌、专业的态度。始终以用户的需求为中心，提供准确、有用的信息。'
    },
    {
      identifier: 'char_background',
      name: '角色背景',
      enabled: false,
      role: 'system',
      position: 'relative',
      content: '这是一个未启用的提示词示例，用于展示禁用状态的显示效果。'
    },
    {
      identifier: 'world_info',
      name: '世界观设定',
      enabled: null,
      role: 'system',
      position: 'relative',
      content: '这是一个未设置启用状态的提示词，展示 null 状态。'
    },
    {
      identifier: 'inchat_greeting',
      name: '问候语',
      enabled: true,
      role: 'assistant',
      position: 'in-chat',
      depth: 0,
      order: 0,
      content: '你好！我是AI助手，很高兴为你服务。请问有什么我可以帮助你的吗？'
    },
    {
      identifier: 'inchat_example_1',
      name: '对话示例1',
      enabled: true,
      role: 'user',
      position: 'in-chat',
      depth: 2,
      order: 1,
      content: '这是一个用户对话示例，用于展示 in-chat 提示词。'
    },
    {
      identifier: 'inchat_example_2',
      name: '对话示例2',
      enabled: true,
      role: 'system',
      position: 'in-chat',
      depth: 3,
      order: 2,
      content: '这是另一个 in-chat 示例，展示不同的 depth 和 order 参数。'
    }
  ],
  regex_rules: [
    {
      id: 'remove_xml',
      name: '移除XML标签',
      enabled: true,
      find_regex: '<[^>]+>',
      replace_regex: '',
      targets: ['output'],
      placement: 'after_macro',
      views: []
    },
    {
      id: 'clean_spaces',
      name: '清理多余空格',
      enabled: true,
      find_regex: '\\s+',
      replace_regex: ' ',
      targets: ['output', 'input'],
      placement: 'after_macro',
      views: ['chat']
    },
    {
      id: 'format_quotes',
      name: '格式化引号',
      enabled: false,
      find_regex: '"([^"]+)"',
      replace_regex: '「$1」',
      targets: ['output'],
      placement: 'before_display',
      views: []
    },
    {
      id: 'remove_markdown',
      name: '移除 Markdown 标记',
      enabled: true,
      find_regex: '\\*\\*(.+?)\\*\\*|\\*(.+?)\\*|__(.+?)__|_(.+?)_',
      replace_regex: '$1$2$3$4',
      targets: ['output'],
      placement: 'after_macro',
      views: ['preview']
    }
  ]
})

const activeData = computed(() => props.presetData || demoPresetData.value)

// 预设设置的简化模型（本地占位状态）
const temperature = computed(() => activeData.value.api_config?.temperature ?? 1.0)
const maxTokens = computed(() => activeData.value.api_config?.max_tokens ?? 300)
const stream = computed(() => activeData.value.api_config?.stream ?? true)
const topP = computed(() => activeData.value.api_config?.top_p ?? 1.0)
const frequencyPenalty = computed(() => activeData.value.api_config?.frequency_penalty ?? 0)
const presencePenalty = computed(() => activeData.value.api_config?.presence_penalty ?? 0)
const topK = computed(() => activeData.value.api_config?.top_k ?? 0)
const maxContext = computed(() => activeData.value.api_config?.max_context ?? 4095)

/* 面板收起/展开（默认全部展开） */
const apiOpen = ref(true)
const promptsOpen = ref(true)
const regexOpen = ref(true)
const relativeOpen = ref(true)
const inChatOpen = ref(true)

// LLM API 配置启用与参数开关（仅前端显示，不联通后端）
const apiEnabled = computed(() => activeData.value.api_config?.enabled ?? true)
const enableTemperature = ref(true)
const enableTopP = ref(true)
const enableTopK = ref(true)
const enableMaxContext = ref(true)
const enableMaxTokens = ref(true)
const enableStream = ref(true)
const enableFrequencyPenalty = ref(true)
const enablePresencePenalty = ref(true)

// 提示词列表
const relativePrompts = computed(() => 
  (activeData.value.prompts || []).filter(p => p.position === 'relative')
)
const inChatPrompts = computed(() => 
  (activeData.value.prompts || []).filter(p => p.position === 'in-chat')
)

/* 初始化 Lucide 图标（组件挂载后） */
onMounted(() => {
  window.lucide?.createIcons?.()
})

watch([() => activeData.value.prompts, () => activeData.value.regex_rules], async () => {
  await nextTick()
  window.lucide?.createIcons?.()
}, { flush: 'post' })

// 渲染提示词卡片的方法
function enabledLabel(v) {
  return v === true ? '已启用' : v === false ? '未启用' : '未设置'
}
</script>

<template>
  <!-- 仅 Preset 视图的内容（不包含三栏布局与顶部栏） -->
  <section class="space-y-6">
    <!-- 页面标题 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <i data-lucide="settings-2" class="w-5 h-5 text-black"></i>
          <h2 class="text-lg font-bold">{{ activeData.name || '预设详情' }}</h2>
        </div>
        <div class="px-3 py-1 rounded-4 bg-gray-100 border border-gray-300 text-black text-sm">
          只读模式
        </div>
      </div>
      <p class="mt-2 text-xs text-black/60">本页为查看模式，展示预设的完整内容</p>
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
          <span class="text-sm text-black/80">{{ apiEnabled ? '已启用' : '未启用' }}</span>
        </div>

        <!-- 参数编辑（仅 UI 显示，不联通后端） -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- temperature -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Temperature</label>
              <span class="text-xs text-black/60">{{ enableTemperature ? '启用' : '禁用' }}</span>
            </div>
            <div class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-sm">
              {{ temperature.toFixed(2) }}
            </div>
          </div>

          <!-- top_p -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Top P</label>
              <span class="text-xs text-black/60">{{ enableTopP ? '启用' : '禁用' }}</span>
            </div>
            <div class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-sm">
              {{ topP.toFixed(2) }}
            </div>
          </div>

          <!-- top_k -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Top K</label>
              <span class="text-xs text-black/60">{{ enableTopK ? '启用' : '禁用' }}</span>
            </div>
            <div class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-sm">
              {{ topK }}
            </div>
          </div>

          <!-- max_context -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Max Context</label>
              <span class="text-xs text-black/60">{{ enableMaxContext ? '启用' : '禁用' }}</span>
            </div>
            <div class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-sm">
              {{ maxContext }}
            </div>
          </div>

          <!-- max_tokens -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Max Tokens</label>
              <span class="text-xs text-black/60">{{ enableMaxTokens ? '启用' : '禁用' }}</span>
            </div>
            <div class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-sm">
              {{ maxTokens }}
            </div>
          </div>

          <!-- stream -->
          <div class="flex items-end">
            <div class="w-full">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-medium text-black">流式输出（stream）</label>
                <span class="text-xs text-black/60">{{ enableStream ? '启用' : '禁用' }}</span>
              </div>
              <div class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-sm">
                {{ stream ? '开启' : '关闭' }}
              </div>
            </div>
          </div>

          <!-- frequency_penalty -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Frequency Penalty</label>
              <span class="text-xs text-black/60">{{ enableFrequencyPenalty ? '启用' : '禁用' }}</span>
            </div>
            <div class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-sm">
              {{ frequencyPenalty }}
            </div>
          </div>

          <!-- presence_penalty -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-black">Presence Penalty</label>
              <span class="text-xs text-black/60">{{ enablePresencePenalty ? '启用' : '禁用' }}</span>
            </div>
            <div class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-sm">
              {{ presencePenalty }}
            </div>
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

                <!-- 已有 Relative 列表 -->
                <div v-show="relativeOpen" class="space-y-2">
                  <div
                    v-for="it in relativePrompts"
                    :key="it.identifier"
                    class="border border-gray-200 rounded-4 p-3 bg-white transition-all duration-200 ease-soft hover:shadow-elevate"
                  >
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                      <div class="text-sm flex items-center gap-2">
                        <span class="font-medium">{{ it.name }}</span>
                      </div>

                      <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ it.role }}</span>
                        <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ enabledLabel(it.enabled) }}</span>
                      </div>
                    </div>

                    <!-- Identifier -->
                    <div class="text-xs text-black/60 mt-2">
                      <span class="font-mono">id:</span>
                      <span class="ml-1 font-mono">{{ it.identifier }}</span>
                    </div>

                    <!-- View mode content -->
                    <div v-if="it.content" class="text-xs text-black/70 mt-2 leading-6 break-words">
                      {{ it.content }}
                    </div>
                  </div>
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
                <div v-show="inChatOpen" class="space-y-2">
                  <div
                    v-for="it in inChatPrompts"
                    :key="it.identifier"
                    class="border border-gray-200 rounded-4 p-3 bg-white transition-all duration-200 ease-soft hover:shadow-elevate"
                  >
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                      <div class="text-sm flex items-center gap-2">
                        <span class="font-medium">{{ it.name }}</span>
                        <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">depth: {{ it.depth }}</span>
                        <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">order: {{ it.order }}</span>
                      </div>

                      <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ it.role }}</span>
                        <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ enabledLabel(it.enabled) }}</span>
                      </div>
                    </div>

                    <!-- Identifier -->
                    <div class="text-xs text-black/60 mt-2">
                      <span class="font-mono">id:</span>
                      <span class="ml-1 font-mono">{{ it.identifier }}</span>
                    </div>

                    <!-- View mode content -->
                    <div v-if="it.content" class="text-xs text-black/70 mt-2 leading-6 break-words">
                      {{ it.content }}
                    </div>
                  </div>
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
        <!-- 规则列表 -->
        <div class="space-y-2">
          <div
            v-for="r in (activeData.regex_rules || [])"
            :key="r.id"
            class="border border-gray-200 rounded-4 p-3 bg-white transition-all duration-200 ease-soft hover:shadow-elevate"
          >
            <!-- Header -->
            <div class="flex items-center justify-between mb-2">
              <div class="text-sm font-medium">{{ r.name }}</div>
              <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ r.enabled ? '已启用' : '未启用' }}</span>
                <span class="px-2 py-0.5 text-xs rounded-4 border border-gray-800 text-black">{{ r.placement }}</span>
              </div>
            </div>

            <!-- ID -->
            <div class="text-xs text-black/60 mb-2">
              <span class="font-mono">id:</span>
              <span class="ml-1 font-mono">{{ r.id }}</span>
            </div>

            <!-- Rules -->
            <div class="space-y-2">
              <div class="grid grid-cols-[80px_1fr] gap-2 items-start">
                <div class="text-xs font-medium text-black/60">查找正则:</div>
                <div class="text-xs font-mono text-black/80 bg-gray-50 px-2 py-1 rounded-4 break-all min-h-[28px] flex items-center">
                  {{ r.find_regex || '(空)' }}
                </div>
              </div>
              <div class="grid grid-cols-[80px_1fr] gap-2 items-start">
                <div class="text-xs font-medium text-black/60">替换正则:</div>
                <div class="text-xs font-mono text-black/80 bg-gray-50 px-2 py-1 rounded-4 break-all min-h-[28px] flex items-center">
                  {{ r.replace_regex === '' ? '(空)' : r.replace_regex }}
                </div>
              </div>
              <div v-if="r.targets && r.targets.length > 0" class="grid grid-cols-[80px_1fr] gap-2 items-start">
                <div class="text-xs font-medium text-black/60">目标:</div>
                <div class="text-xs text-black/80 bg-gray-50 px-2 py-1 rounded-4 min-h-[28px] flex items-center">
                  {{ r.targets.join(', ') }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="(activeData.regex_rules || []).length === 0" class="text-xs text-black/50 px-1 py-1">
          暂无规则
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 遵循 PromptEditor 的黑白主题，使用 Tailwind 工具类 */
.rounded-4 {
  border-radius: 10px;
}

.card-shadow {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.hover\:shadow-elevate:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.ease-soft {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

/* 深色主题适配 */
[data-theme="dark"] .bg-white {
  background-color: rgb(23, 27, 36) !important;
}

[data-theme="dark"] .bg-gray-50 {
  background-color: rgb(28, 34, 45) !important;
}

[data-theme="dark"] .bg-gray-100 {
  background-color: rgb(33, 39, 52) !important;
}

[data-theme="dark"] .text-black {
  color: rgb(232, 236, 244) !important;
}

[data-theme="dark"] .text-black\/60 {
  color: rgba(232, 236, 244, 0.6) !important;
}

[data-theme="dark"] .text-black\/70 {
  color: rgba(232, 236, 244, 0.7) !important;
}

[data-theme="dark"] .text-black\/80 {
  color: rgba(232, 236, 244, 0.8) !important;
}

[data-theme="dark"] .border-gray-200 {
  border-color: rgb(45, 54, 70) !important;
}

[data-theme="dark"] .border-gray-300 {
  border-color: rgb(55, 64, 80) !important;
}

[data-theme="dark"] .border-gray-800 {
  border-color: rgb(200, 205, 215) !important;
}
</style>