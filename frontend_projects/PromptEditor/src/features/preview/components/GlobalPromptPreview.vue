<script setup lang="ts">
import { computed, onMounted, nextTick, ref } from 'vue'
import { usePreviewStore, type PreviewMode } from '@/features/preview/store'
import { usePreviewRuntime } from '../runtime'

const preview = usePreviewStore()
const runtime = usePreviewRuntime()

const options: { value: PreviewMode; label: string }[] = [
  { value: 'raw', label: '原始提示词' },
  { value: 'message', label: '对话页面提示词' },
  { value: 'preflight', label: '发给AI前提示词' },
]

const current = computed<PreviewMode>({
  get: () => preview.mode,
  set: (v) => preview.setMode(v),
})

onMounted(() => {
  // 确保首次渲染使用持久化选项
  preview.load()
  // 渲染 Lucide 图标
  nextTick(() => (window as any).lucide?.createIcons?.())
})

// 自动结果展示（来自运行时自动生成，仅显示当前模式）
const subTab = ref<'messages' | 'variables'>('messages')

const autoMessages = computed(() => {
  if (preview.mode === 'raw') {
    return runtime.results.raw?.messages ?? []
  } else if (preview.mode === 'message') {
    return runtime.results.dialog?.message ?? []
  } else if (preview.mode === 'preflight') {
    return runtime.results.preflight?.message ?? []
  }
  return []
})
const autoVariables = computed(() => {
  if (preview.mode === 'message') return runtime.results.dialog?.variables ?? null
  if (preview.mode === 'preflight') return runtime.results.preflight?.variables ?? null
  return null
})
const autoHasVariables = computed(() => {
  const v = autoVariables.value
  return !!(v && typeof v === 'object' && Object.keys(v).length)
})
const autoLoading = computed(() => runtime.generating)
const autoError = computed(() => runtime.lastError)

// 操作：复制当前模式的自动 messages
function copyAuto() {
  try {
    const txt = JSON.stringify(autoMessages.value ?? [], null, 2)
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(txt)
    } else {
      const ta = document.createElement('textarea')
      ta.value = txt
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      ta.remove()
    }
  } catch {}
}

// 显示工具
function sourceType(m: any): string {
  try {
    return String(m?.source?.type ?? '—')
  } catch {
    return '—'
  }
}
function pretty(obj: any): string {
  try {
    return JSON.stringify(obj ?? {}, null, 2)
  } catch {
    return ''
  }
}
</script>

<template>
  <section class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
    <div class="flex items-center space-x-2 mb-4">
      <i data-lucide="eye" class="w-5 h-5 text-black"></i>
      <h3 class="text-lg font-bold text-black">全局提示词预览</h3>
    </div>

    <label class="block text-sm text-black mb-2">预览类型</label>
    <div class="relative">
      <select
        v-model="current"
        class="w-full h-12 px-3 pr-9 bg-white text-black border border-gray-900 rounded-4 focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2 appearance-none"
      >
        <option v-for="opt in options" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <i
        data-lucide="chevron-down"
        class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-black"
      ></i>
    </div>

    <p class="text-xs text-black/60 mt-3">
      默认“原始提示词”。该选择会被持久化保存。
    </p>

    <!-- 自动生成结果（仅显示当前选择的模式） -->
    <div class="mt-6 p-4 bg-white border border-gray-200 rounded-4">
      <div class="flex items-center gap-2 mb-3">
        <i data-lucide="sparkles" class="w-5 h-5 text-black"></i>
        <span class="text-sm font-medium text-black">自动生成结果</span>
        <span class="ml-auto text-xs text-black/60" v-if="autoMessages?.length">总条数：{{ autoMessages.length }}</span>
      </div>

      <!-- 子页签：messages / variables（若有） -->
      <div class="flex items-center gap-2 mb-3">
        <button
          class="px-3 h-10 rounded-4 border border-gray-900 text-black bg-white hover:bg-gray-100 transition"
          :class="subTab==='messages' ? 'bg-gray-100' : ''"
          @click="subTab='messages'"
        >
          消息
        </button>
        <button
          v-if="autoHasVariables"
          class="px-3 h-10 rounded-4 border border-gray-900 text-black bg-white hover:bg-gray-100 transition"
          :class="subTab==='variables' ? 'bg-gray-100' : ''"
          @click="subTab='variables'"
        >
          变量
        </button>

        <div class="ml-auto flex items-center gap-2">
          <button
            class="px-3 h-10 rounded-4 border border-gray-900 text-black bg-white hover:bg-gray-100 transition"
            :disabled="autoLoading || !autoMessages?.length"
            @click="copyAuto"
          >
            复制 JSON
          </button>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="autoError" class="p-3 border border-gray-900 rounded-4 text-sm text-black bg-white mb-3">
        {{ autoError }}
      </div>

      <!-- 子页签：消息 -->
      <div v-if="subTab==='messages'">
        <div
          v-if="autoMessages && autoMessages.length"
          class="space-y-2 max-h-72 overflow-auto"
        >
          <div
            v-for="(m, i) in autoMessages"
            :key="i"
            class="border border-gray-200 rounded-4 p-3 hover:bg-gray-50 transition-colors"
          >
            <div class="flex items-center gap-2 mb-1">
              <span class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ m.role }}</span>
              <span class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ sourceType(m) }}</span>
              <span class="text-2xs text-black/50">#{{ i + 1 }}</span>
            </div>
            <div class="text-sm text-black/80 leading-6 whitespace-pre-wrap break-words">
              {{ m.content }}
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-black/60">暂无消息。</div>
      </div>

      <!-- 子页签：变量 -->
      <div v-else-if="subTab==='variables' && autoHasVariables">
        <div class="grid grid-cols-1 gap-3">
          <div class="border border-gray-200 rounded-4 p-3">
            <div class="text-xs font-medium text-black mb-2">initial</div>
            <pre class="text-xs text-black/80 overflow-auto whitespace-pre-wrap">{{ pretty(autoVariables?.initial) }}</pre>
          </div>
          <div class="border border-gray-200 rounded-4 p-3">
            <div class="text-xs font-medium text-black mb-2">final</div>
            <pre class="text-xs text-black/80 overflow-auto whitespace-pre-wrap">{{ pretty(autoVariables?.final) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 遵循 ui美化规范：仅黑白与灰阶、圆角4px、触控区域≥48px、微交互轻阴影 */
</style>