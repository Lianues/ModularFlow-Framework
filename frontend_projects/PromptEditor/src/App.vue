<script setup lang="ts">
import { ref } from 'vue'

type TabKey = 'presets' | 'worldbook' | 'characters' | 'regex' | 'user' | 'history'
const currentTab = ref<TabKey>('presets')

// 预设设置的简化模型（占位）
const temperature = ref<number>(1.0)
const maxTokens = ref<number>(300)
const stream = ref<boolean>(true)
const topP = ref<number>(1.0)
const frequencyPenalty = ref<number>(0)
const presencePenalty = ref<number>(0)
</script>

<template>
  <!-- 顶部标题栏 -->
  <header class="fixed top-0 left-0 right-0 h-16 bg-gradient-to-b from-white to-gray-50 border-b border-gray-200 z-40">
    <div class="px-4 h-full">
      <div class="flex items-center justify-between h-full">
        <div class="flex items-center space-x-3">
          <i data-lucide="edit-3" class="w-8 h-8 text-black"></i>
          <div>
            <h1 class="tracking-tight">提示词编辑器</h1>
            <p class="text-black/60 text-sm mt-1">PromptEditor · Vue + Vite + TS</p>
          </div>
        </div>
        <div class="hidden md:flex items-center space-x-2">
          <button class="px-4 py-2 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:text-black transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2">
            保存
          </button>
          <button class="px-4 py-2 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:text-black transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2">
            重置
          </button>
        </div>
      </div>
    </div>
  </header>

  <!-- 三栏布局 -->
  <div class="fixed top-16 left-0 right-0 bottom-0">
    <div class="grid grid-cols-[240px_minmax(0,1fr)_384px] h-full w-full">
      <!-- 左侧导航（桌面） -->
      <aside class="block w-60 flex-shrink-0 h-full overflow-y-auto bg-white border-r border-gray-200">
          <nav class="p-2">
            <ul class="space-y-1">
              <li>
                <button
                  class="relative group w-full flex items-center justify-between px-3 py-2 rounded-4 bg-transparent text-black hover:bg-gray-100 transition-all duration-200 ease-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  :class="currentTab === 'presets' ? 'bg-gray-100 border-l-2 border-black' : ''"
                  @click="currentTab = 'presets'"
                >
                  <div class="flex items-center space-x-2">
                    <i data-lucide="list" class="w-4 h-4 text-black transition-transform duration-200 ease-soft group-hover:translate-x-0.5"></i>
                    <span class="text-sm">预设</span>
                  </div>
                  <span class="text-xs text-black/50">Presets</span>
                </button>
              </li>
              <li>
                <button
                  class="relative group w-full flex items-center justify-between px-3 py-2 rounded-4 bg-transparent text-black hover:bg-gray-100 transition-all duration-200 ease-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  :class="currentTab === 'worldbook' ? 'bg-gray-100 border-l-2 border-black' : ''"
                  @click="currentTab = 'worldbook'"
                >
                  <div class="flex items-center space-x-2">
                    <i data-lucide="book-open" class="w-4 h-4 text-black transition-transform duration-200 ease-soft group-hover:translate-x-0.5"></i>
                    <span class="text-sm">世界书</span>
                  </div>
                  <span class="text-xs text-black/50">World Book</span>
                </button>
              </li>
              <li>
                <button
                  class="relative group w-full flex items-center justify-between px-3 py-2 rounded-4 bg-transparent text-black hover:bg-gray-100 transition-all duration-200 ease-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  :class="currentTab === 'characters' ? 'bg-gray-100 border-l-2 border-black' : ''"
                  @click="currentTab = 'characters'"
                >
                  <div class="flex items-center space-x-2">
                    <i data-lucide="user" class="w-4 h-4 text-black transition-transform duration-200 ease-soft group-hover:translate-x-0.5"></i>
                    <span class="text-sm">角色卡</span>
                  </div>
                  <span class="text-xs text-black/50">Characters</span>
                </button>
              </li>
              <li>
                <button
                  class="relative group w-full flex items-center justify-between px-3 py-2 rounded-4 bg-transparent text-black hover:bg-gray-100 transition-all duration-200 ease-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  :class="currentTab === 'regex' ? 'bg-gray-100 border-l-2 border-black' : ''"
                  @click="currentTab = 'regex'"
                >
                  <div class="flex items-center space-x-2">
                    <i data-lucide="code" class="w-4 h-4 text-black transition-transform duration-200 ease-soft group-hover:translate-x-0.5"></i>
                    <span class="text-sm">正则</span>
                  </div>
                  <span class="text-xs text-black/50">Regex</span>
                </button>
              </li>
              <li>
                <button
                  class="relative group w-full flex items-center justify之间? fix --> justify-between px-3 py-2 rounded-4 bg-transparent text-black hover:bg-gray-100 transition-all duration-200 ease-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  :class="currentTab === 'user' ? 'bg-gray-100 border-l-2 border-black' : ''"
                  @click="currentTab = 'user'"
                >
                  <div class="flex items-center space-x-2">
                    <i data-lucide="id-card" class="w-4 h-4 text-black transition-transform duration-200 ease-soft group-hover:translate-x-0.5"></i>
                    <span class="text-sm">用户信息</span>
                  </div>
                  <span class="text-xs text-black/50">User</span>
                </button>
              </li>
              <li>
                <button
                  class="relative group w-full flex items-center justify-between px-3 py-2 rounded-4 bg-transparent text-black hover:bg-gray-100 transition-all duration-200 ease-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  :class="currentTab === 'history' ? 'bg-gray-100 border-l-2 border-black' : ''"
                  @click="currentTab = 'history'"
                >
                  <div class="flex items-center space-x-2">
                    <i data-lucide="history" class="w-4 h-4 text-black transition-transform duration-200 ease-soft group-hover:translate-x-0.5"></i>
                    <span class="text-sm">对话历史</span>
                  </div>
                  <span class="text-xs text-black/50">History</span>
                </button>
              </li>
            </ul>
          </nav>
      </aside>

      <!-- 中间主视图 -->
      <main class="flex-1 min-w-0 h-full overflow-y-auto px-6 py-4">
        <!-- 预设视图（首期实现） -->
        <section v-if="currentTab === 'presets'" class="space-y-6">
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
                  <input type="range" min="0" max="2" step="0.1" v-model="temperature"
                         class="w-full accent-black" />
                  <div class="text-xs text-black/60 mt-1">当前：{{ temperature.toFixed(1) }}</div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-black mb-2">Top P</label>
                  <input type="range" min="0" max="1" step="0.05" v-model="topP"
                         class="w-full accent-black" />
                  <div class="text-xs text-black/60 mt-1">当前：{{ topP.toFixed(2) }}</div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-black mb-2">Max Tokens</label>
                    <input type="number" min="1" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                           v-model.number="maxTokens" />
                  </div>
                  <div class="flex items-end">
                    <label class="inline-flex items-center space-x-2">
                      <input type="checkbox" v-model="stream" class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2" />
                      <span class="text-sm text-black/80">流式输出</span>
                    </label>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-black mb-2">Frequency Penalty</label>
                    <input type="number" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                           v-model.number="frequencyPenalty" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-black mb-2">Presence Penalty</label>
                    <input type="number" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                           v-model.number="presencePenalty" />
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
                    <button class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:text-black transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2">
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
                        <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:text-black transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2">
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
                        <button class="px-2 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:text-black transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2">
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

        <!-- 其他视图占位 -->
        <section v-else class="bg-white rounded-4 card-shadow border border-gray-200 p-8">
          <div class="text-center">
            <i data-lucide="circle-dashed" class="w-10 h-10 text-black/40 mx-auto mb-4"></i>
            <p class="text-black/60">该视图即将上线：{{ currentTab }}</p>
          </div>
        </section>
      </main>

      <!-- 右侧全局预览（占位） -->
      <aside class="block w-96 flex-shrink-0 h-full overflow-y-auto bg-white border-l border-gray-200">
        <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
          <div class="flex items-center space-x-2 mb-3">
            <i data-lucide="eye" class="w-5 h-5 text-black"></i>
            <h3 class="text-lg font-bold text-black">全局提示词预览</h3>
          </div>
          <div class="text-sm text-black/60">
            暂不实现实时构建。后续将基于全局状态拼装完整提示词。
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
/* 保持最小覆盖，其他通过 Tailwind 类控制 */
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
