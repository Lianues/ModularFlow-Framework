<script setup lang="ts">
import { ref } from 'vue'
import AppShell from './layouts/AppShell.vue'
import Sidebar from './components/Sidebar.vue'
import PresetView from './views/PresetView.vue'

type TabKey = 'presets' | 'worldbook' | 'characters' | 'regex' | 'user' | 'history'
const currentTab = ref<TabKey>('presets')
</script>

<template>
  <AppShell>
    <!-- 左侧栏插槽：侧边导航 -->
    <template #left>
      <Sidebar v-model="currentTab" />
    </template>

    <!-- 中间主视图区 -->
    <template #main>
      <section v-if="currentTab === 'presets'" class="h-full">
        <PresetView />
      </section>

      <!-- 其他视图占位（后续替换成对应视图组件） -->
      <section
        v-else
        class="bg-white rounded-4 card-shadow border border-gray-200 p-8 transition-all duration-200 ease-soft hover:shadow-elevate"
      >
        <div class="text-center">
          <i data-lucide="circle-dashed" class="w-10 h-10 text-black/40 mx-auto mb-4"></i>
          <p class="text-black/60">该视图即将上线：{{ currentTab }}</p>
        </div>
      </section>
    </template>

    <!-- 右侧预览插槽（占位，后续接入全局提示词拼装状态） -->
    <template #right>
      <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
        <div class="flex items-center space-x-2 mb-3">
          <i data-lucide="eye" class="w-5 h-5 text-black"></i>
          <h3 class="text-lg font-bold text-black">全局提示词预览</h3>
        </div>
        <div class="text-sm text-black/60">
          暂不实现实时构建。后续将基于全局状态拼装完整提示词。
        </div>
      </div>
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
