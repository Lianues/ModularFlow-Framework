<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-semibold">文件管理</h2>
      <button
        class="px-3 py-2 border border-black text-black rounded hover:bg-gray-100 active:bg-gray-200 transition"
        @click="store.clearAll()"
      >
        清空所有
      </button>
    </div>

    <div v-if="store.files.length > 0" class="space-y-4">
      <div
        v-for="f in store.files"
        :key="f.name"
        class="border border-gray-200 rounded p-3 bg-white shadow-sm"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="font-medium">{{ f.name }}</span>
            <span class="text-xs text-gray-500">启用: {{ f.enabled ? '是' : '否' }}</span>
            <span
              v-if="store.activeName === f.name"
              class="text-xs text-black border border-black rounded px-2 py-0.5"
            >
              当前
            </span>
          </div>

          <div class="flex items-center gap-2">
            <label class="inline-flex items-center gap-2 select-none">
              <input
                type="checkbox"
                class="w-5 h-5 accent-black"
                :checked="f.enabled"
                @change="store.toggleEnable(f.name)"
              />
              <span class="text-sm">启用</span>
            </label>

            <button
              class="px-3 py-1.5 border border-black text-black rounded hover:bg-gray-100 active:bg-gray-200"
              @click="store.setActive(f.name)"
            >
              设为当前
            </button>

            <button
              class="px-3 py-1.5 border border-black text-black rounded hover:bg-gray-100 active:bg-gray-200"
              @click="store.deleteFile(f.name)"
            >
              删除
            </button>
          </div>
        </div>

        <div class="mt-3 text-sm text-gray-600">
          <span>类型: 预设</span>
          <span class="ml-3">prompts: {{ f.data?.prompts?.length ?? 0 }}</span>
        </div>
      </div>
    </div>

    <div
      v-else
      class="border border-dashed border-gray-300 rounded p-6 text-center text-sm text-gray-600 bg-gray-50"
    >
      尚未导入任何文件。请使用右上角“导入”按钮选择 JSON 文件。
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { usePresetStore } from '../features/presets/store'

const store = usePresetStore()
onMounted(() => {
  store.load()
})
</script>

<style scoped>
/* 保持黑白主题与 4/8/16 间距系统 */
</style>