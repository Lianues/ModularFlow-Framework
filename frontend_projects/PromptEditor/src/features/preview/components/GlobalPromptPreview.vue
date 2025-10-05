<script setup lang="ts">
import { computed, onMounted, nextTick, ref } from 'vue'
import { usePreviewStore, type PreviewMode } from '@/features/preview/store'
import { runPromptRaw, type PromptRawResult } from '@/features/workflow/promptRaw'
import { runDialogView, runPreflightView } from '@/features/workflow/promptFlows'

const preview = usePreviewStore()

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

// 原始提示词（RAW）工作流状态
const loading = ref(false)
const error = ref('')
const result = ref<PromptRawResult | null>(null)

// 调用后端 RAW 装配工作流，聚合前端上下文并提交
async function generateRaw() {
  loading.value = true
  error.value = ''
  try {
    const res = await runPromptRaw()
    result.value = res
  } catch (e: any) {
    error.value = String(e?.message || e || '执行失败')
  } finally {
    loading.value = false
    nextTick(() => (window as any).lucide?.createIcons?.())
  }
}

function copyRaw() {
  try {
    const txt = JSON.stringify(result.value?.messages ?? [], null, 2)
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

function clearRaw() {
  result.value = null
  error.value = ''
}
// 生成：对话页面提示词（user_view）
async function generateDialog() {
  loading.value = true
  error.value = ''
  try {
    // 1) RAW
    const raw = await runPromptRaw()
    // 2) postprocess user_view（variables 传空对象由服务端处理）
    const dialogRes = await runDialogView(raw.messages)
    // 统一封装成 PromptRawResult 形状用于渲染
    result.value = { messages: dialogRes.message as any }
  } catch (e: any) {
    error.value = String(e?.message || e || '执行失败')
  } finally {
    loading.value = false
    nextTick(() => (window as any).lucide?.createIcons?.())
  }
}

// 生成：发给AI前提示词（assistant_view）
async function generatePreflight() {
  loading.value = true
  error.value = ''
  try {
    // 1) RAW
    const raw = await runPromptRaw()
    // 2) user_view
    const dialogRes = await runDialogView(raw.messages)
    // 3) preflight（在 user_view 基础上再次装配并对 assistant_view 后处理）
    const preflightRes = await runPreflightView(dialogRes)
    result.value = { messages: preflightRes.message as any }
  } catch (e: any) {
    error.value = String(e?.message || e || '执行失败')
  } finally {
    loading.value = false
    nextTick(() => (window as any).lucide?.createIcons?.())
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

    <!-- 原始提示词（RAW） -->
    <div v-if="current === 'raw'" class="mt-6">
      <div class="flex flex-wrap items-center gap-2">
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading"
          @click="generateRaw"
        >
          <span v-if="!loading">生成原始提示词</span>
          <span v-else>处理中…</span>
        </button>
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading || !result"
          @click="copyRaw"
        >
          复制 JSON
        </button>
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading || !result"
          @click="clearRaw"
        >
          清空
        </button>

        <span class="ml-auto text-xs text-black/60" v-if="result">总条数：{{ result?.messages?.length || 0 }}</span>
      </div>

      <div v-if="error" class="mt-3 p-3 border border-gray-900 rounded-4 text-sm text-black bg-white">
        {{ error }}
      </div>

      <div v-if="result && result.messages?.length" class="mt-4 space-y-2 max-h-72 overflow-auto">
        <div
          v-for="(m, i) in result.messages"
          :key="i"
          class="border border-gray-200 rounded-4 p-3 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center gap-2 mb-1">
            <span class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ m.role }}</span>
            <span class="text-2xs text-black/50">#{{ i + 1 }}</span>
          </div>
          <div class="text-sm text-black/80 leading-6 whitespace-pre-wrap break-words">
            {{ m.content }}
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="mt-4 p-4 bg-white border border-gray-200 rounded-4 text-sm text-black/60">
        选择“生成原始提示词”以从当前上下文构建 RAW messages。
      </div>
    </div>

    <!-- 对话页面提示词（user_view） -->
    <div v-else-if="current === 'message'" class="mt-6">
      <div class="flex flex-wrap items-center gap-2">
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading"
          @click="generateDialog"
        >
          <span v-if="!loading">生成对话页面提示词</span>
          <span v-else>处理中…</span>
        </button>
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading || !result"
          @click="copyRaw"
        >
          复制 JSON
        </button>
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading || !result"
          @click="clearRaw"
        >
          清空
        </button>

        <span class="ml-auto text-xs text-black/60" v-if="result">总条数：{{ result?.messages?.length || 0 }}</span>
      </div>

      <div v-if="error" class="mt-3 p-3 border border-gray-900 rounded-4 text-sm text-black bg-white">
        {{ error }}
      </div>

      <div v-if="result && result.messages?.length" class="mt-4 space-y-2 max-h-72 overflow-auto">
        <div
          v-for="(m, i) in result.messages"
          :key="i"
          class="border border-gray-200 rounded-4 p-3 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center gap-2 mb-1">
            <span class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ m.role }}</span>
            <span class="text-2xs text-black/50">#{{ i + 1 }}</span>
          </div>
          <div class="text-sm text-black/80 leading-6 whitespace-pre-wrap break-words">
            {{ m.content }}
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="mt-4 p-4 bg-white border border-gray-200 rounded-4 text-sm text-black/60">
        选择“生成对话页面提示词”以从 RAW messages 进行 user_view 后处理（variables 为空）。
      </div>
    </div>

    <!-- 发给AI前提示词（assistant_view） -->
    <div v-else-if="current === 'preflight'" class="mt-6">
      <div class="flex flex-wrap items-center gap-2">
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading"
          @click="generatePreflight"
        >
          <span v-if="!loading">生成发给AI前提示词</span>
          <span v-else>处理中…</span>
        </button>
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading || !result"
          @click="copyRaw"
        >
          复制 JSON
        </button>
        <button
          class="px-4 h-12 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 ease-soft"
          :disabled="loading || !result"
          @click="clearRaw"
        >
          清空
        </button>

        <span class="ml-auto text-xs text-black/60" v-if="result">总条数：{{ result?.messages?.length || 0 }}</span>
      </div>

      <div v-if="error" class="mt-3 p-3 border border-gray-900 rounded-4 text-sm text-black bg-white">
        {{ error }}
      </div>

      <div v-if="result && result.messages?.length" class="mt-4 space-y-2 max-h-72 overflow-auto">
        <div
          v-for="(m, i) in result.messages"
          :key="i"
          class="border border-gray-200 rounded-4 p-3 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center gap-2 mb-1">
            <span class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ m.role }}</span>
            <span class="text-2xs text-black/50">#{{ i + 1 }}</span>
          </div>
          <div class="text-sm text-black/80 leading-6 whitespace-pre-wrap break-words">
            {{ m.content }}
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="mt-4 p-4 bg-white border border-gray-200 rounded-4 text-sm text-black/60">
        在 user_view 的结果作为 history 重新装配 RAW 后，对 assistant_view 执行后处理（携带 user_view 的 variables）。
      </div>
    </div>

    <!-- 兜底占位 -->
    <div v-else class="mt-6 p-4 bg-white border border-gray-200 rounded-4">
      <p class="text-sm text-black/60">请选择上方的预览类型进行生成。</p>
    </div>
  </section>
</template>

<style scoped>
/* 遵循 ui美化规范：仅黑白与灰阶、圆角4px、触控区域≥48px、微交互轻阴影 */
</style>