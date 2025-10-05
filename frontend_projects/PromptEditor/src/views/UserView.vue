<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/**
 * 参考后端 Persona 结构（backend_projects/SmartTraven/data/persona/*.json）
 * 示例文件：backend_projects/SmartTraven/data/persona/用户2.json
 * 本视图仅做 UI 占位与交互演示，暂不接入后端
 */

interface Persona {
  id: string
  name: string
  description?: string
  tags?: string[]
}

const personas = ref<Persona[]>([
  { id: 'user2', name: '用户2', description: '新建的用户角色', tags: ['默认'] },
  { id: 'default', name: '默认用户', description: '用于演示的默认用户（占位数据）', tags: ['演示'] }
])

// 选择与检索
const search = ref('')
const filtered = computed(() => {
  if (!search.value) return personas.value
  const q = search.value.toLowerCase()
  return personas.value.filter(p =>
    `${p.name} ${p.description ?? ''} ${(p.tags ?? []).join(' ')}`.toLowerCase().includes(q)
  )
})

const currentIndex = ref(0)
const current = computed(() => filtered.value[currentIndex.value] ?? filtered.value[0])

// 表单
const formName = ref('')
const formDesc = ref('')

const jsonPreview = computed(() => {
  const obj = {
    name: formName.value || current.value?.name || '',
    description: formDesc.value || current.value?.description || ''
  }
  return JSON.stringify(obj, null, 2)
})

function loadFromCurrent() {
  if (!current.value) return
  formName.value = current.value.name
  formDesc.value = current.value.description ?? ''
}

function selectRow(idx: number) {
  currentIndex.value = idx
  loadFromCurrent()
  ;(window as any).lucide?.createIcons?.()
}

function saveForm() {
  if (!current.value) return
  current.value.name = formName.value.trim() || current.value.name
  current.value.description = formDesc.value
}

function resetForm() {
  loadFromCurrent()
}

onMounted(() => {
  loadFromCurrent()
  ;(window as any).lucide?.createIcons?.()
})
</script>

<template>
  <section class="space-y-6">
    <!-- 概览 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <i data-lucide="id-card" class="w-6 h-6 text-black"></i>
          <h2>用户信息</h2>
        </div>
        <div class="text-xs text-black/50">
          参考结构：backend_projects/SmartTraven/data/persona/*.json
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 左：用户列表与搜索 -->
        <div class="md:col-span-1">
          <label class="block text-sm font-medium text-black mb-2">搜索</label>
          <input
            v-model="search"
            type="text"
            placeholder="按名称、描述、标签过滤..."
            class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
          />
          <div class="text-xs text-black/60 mt-2">共 {{ filtered.length }} 条</div>

          <div class="mt-4 space-y-2">
            <button
              v-for="(p,idx) in filtered"
              :key="p.id"
              class="w-full text-left px-3 py-2 rounded-4 border border-gray-200 bg-white hover:bg-gray-100 transition-all duration-200 ease-soft hover:-translate-y-0.5 hover:shadow-elevate focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
              :class="idx === currentIndex ? 'bg-gray-100 border-gray-300' : ''"
              @click="selectRow(idx)"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <i data-lucide="user" class="w-4 h-4 text-black"></i>
                  <span class="text-sm text-black">{{ p.name }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <span
                    v-for="t in p.tags || []"
                    :key="t"
                    class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent"
                  >{{ t }}</span>
                </div>
              </div>
              <p class="mt-1 text-xs text-black/60 line-clamp-2">{{ p.description || '（无描述）' }}</p>
            </button>
          </div>
        </div>

        <!-- 中：表单编辑 -->
        <div class="md:col-span-2">
          <div class="bg-white rounded-4 border border-gray-200 p-5">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-2">
                <i data-lucide="edit-3" class="w-4 h-4 text-black"></i>
                <span class="text-sm font-medium text-black">基本信息</span>
              </div>
              <div class="flex items-center gap-2">
                <button
                  class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:shadow-elevate hover:-translate-y-0.5 transition-all duration-200 ease-soft text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  @click="saveForm"
                >
                  更新
                </button>
                <button
                  class="px-3 py-1 rounded-4 bg-transparent border border-gray-900 text-black hover:bg-gray-100 active:bg-gray-200 hover:shadow-elevate hover:-translate-y-0.5 transition-all duration-200 ease-soft text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
                  @click="resetForm"
                >
                  重置
                </button>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-black mb-2">名称</label>
                <input
                  v-model="formName"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                  placeholder="输入名称"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-black mb-2">ID（只读）</label>
                <input
                  :value="current?.id || ''"
                  type="text"
                  readonly
                  class="w-full px-3 py-2 border border-gray-300 rounded-4 bg-gray-50 text-black/70"
                />
              </div>

              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-black mb-2">描述</label>
                <textarea
                  v-model="formDesc"
                  rows="4"
                  class="w-full px-3 py-2 border border-gray-300 rounded-4 focus:outline-none focus:ring-2 focus:ring-gray-800"
                  placeholder="输入描述..."
                ></textarea>
              </div>
            </div>
          </div>

          <!-- 预览 -->
          <div class="mt-4 bg-white rounded-4 border border-gray-200 p-5">
            <div class="flex items-center gap-2 mb-2">
              <i data-lucide="eye" class="w-4 h-4 text-black"></i>
              <span class="text-sm font-medium text-black">JSON 预览（示例）</span>
            </div>
            <pre class="text-xs text-black/70 whitespace-pre-wrap font-mono">
{{ jsonPreview }}
            </pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 占位：更多属性（未来扩展：头像、联系方式、自定义变量等） -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center gap-2 mb-2">
        <i data-lucide="boxes" class="w-4 h-4 text-black"></i>
        <span class="text-sm font-medium text-black">更多属性（占位）</span>
      </div>
      <div class="text-xs text-black/60">
        未来将扩展更多用户字段（如自定义变量、头像、联系方式等），并与后端联通。
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 局部样式尽量轻，统一通过 Tailwind 工具类控制 */
</style>