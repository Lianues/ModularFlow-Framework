<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 预设设置的简化模型（本地占位状态）
const temperature = ref<number>(1.0)
const maxTokens = ref<number>(300)
const stream = ref<boolean>(true)
const topP = ref<number>(1.0)
const frequencyPenalty = ref<number>(0)
const presencePenalty = ref<number>(0)

// 初始化 Lucide 图标（组件挂载后）
onMounted(() => {
  (window as any).lucide?.createIcons?.()
})
</script>

<template>
  <!-- 仅 Preset 视图的内容（不包含三栏布局与顶部栏） -->
  <section class="space-y-6">
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between mb-4">
        <h2>预设编辑器</h2>
        <div class="text-xs text-black/50">仅做本地编辑演示，保存联通待后续</div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 左：设置表单 -->
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-black mb-2">Temperature</label>
            <input type="range" min="0" max="2" step="0.1" v-model="temperature" class="w-full accent-black" />
            <div class="text-xs text-black/60 mt-1">当前：{{ temperature.toFixed(1) }}</div>
          </div>

          <div>
            <label class="block text-sm font-medium text-black mb-2">Top P</label>
            <input type="range" min="0" max="1" step="0.05" v-model="topP" class="w-full accent-black" />
            <div class="text-xs text-black/60 mt-1">当前：{{ topP.toFixed(2) }}</div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-black mb-2">Max Tokens</label>
              <input
                type="number"
                min="1"
                class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                v-model.number="maxTokens"
              />
            </div>
            <div class="flex items-end">
              <label class="inline-flex items-center space-x-2">
                <input
                  type="checkbox"
                  v-model="stream"
                  class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                />
                <span class="text-sm text-black/80">流式输出</span>
              </label>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-black mb-2">Frequency Penalty</label>
              <input
                type="number"
                min="0"
                class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                v-model.number="frequencyPenalty"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-black mb-2">Presence Penalty</label>
              <input
                type="number"
                min="0"
                class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                v-model.number="presencePenalty"
              />
            </div>
          </div>
        </div>

        <!-- 右：Prompts 简表（占位） -->
        <div class="space-y-4">
          <div class="border border-gray-200 rounded-4 p-4 transition-all duration-200 ease-soft hover:shadow-elevate">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-2">
                <i data-lucide="list" class="w-4 h-4 text-black"></i>
                <span class="text-sm font-medium text-black">提示词条目</span>
              </div>
              <button
                class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:text-black transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
              >
                新增
              </button>
            </div>
            <div class="space-y-2">
              <div class="border border-gray-200 rounded-4 p-3 transition-all duration-200 ease-soft hover:shadow-elevate">
                <div class="flex items-center justify-between">
                  <div class="text-sm">
                    <span class="font-mono">main</span>
                    <span class="text-black/60 ml-2">role: user</span>
                  </div>
                  <button
                    class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:text-black transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  >
                    编辑
                  </button>
                </div>
                <div class="text-xs text-black/60 mt-2 truncate" v-pre>
                  Write {{char}}'s next reply in a fictional chat between {{char}} and {{user}}.
                </div>
              </div>

              <div class="border border-gray-200 rounded-4 p-3 transition-all duration-200 ease-soft hover:shadow-elevate">
                <div class="flex items-center justify-between">
                  <div class="text-sm">
                    <span class="font-mono">charAfter</span>
                    <span class="text-black/60 ml-2">role: system</span>
                  </div>
                  <button
                    class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:text-black transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  >
                    编辑
                  </button>
                </div>
                <div class="text-xs text-black/60 mt-2 truncate">
                  World Info (after) ...
                </div>
              </div>
            </div>
          </div>

          <div class="border border-gray-200 rounded-4 p-4 transition-all duration-200 ease-soft hover:shadow-elevate">
            <div class="flex items-center space-x-2 mb-3">
              <i data-lucide="code" class="w-4 h-4 text-black"></i>
              <span class="text-sm font-medium text-black">正则规则（简表）</span>
            </div>
            <div class="text-xs text-black/60">
              示例：find「示例」→ replace「【预设替换】」，目标：user/assistant
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>