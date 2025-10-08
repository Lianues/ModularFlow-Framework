<script setup>
import { ref, computed } from 'vue'
import ViewerModal from '@/components/common/ViewerModal.vue'
import ClonedPresetView from '@/components/viewer/ClonedPresetView.vue'

const props = defineProps({
  anchorLeft: { type: Number, default: 348 }, // 左侧锚定像素（与外观面板一致：12+320+16）
  width: { type: Number, default: 520 },      // 面板宽度
  zIndex: { type: Number, default: 59 },      // 层级（与 Sidebar 同层）
  top: { type: Number, default: 64 },         // 顶部偏移（避开顶部栏）
  bottom: { type: Number, default: 12 },      // 底部偏移
  title: { type: String, default: '预设 Presets' },
})

const emit = defineEmits(['close','use','view','delete'])

const panelStyle = computed(() => ({
  position: 'fixed',
  left: props.anchorLeft + 'px',
  top: props.top + 'px',
  bottom: props.bottom + 'px',
  width: props.width + 'px',
  zIndex: String(props.zIndex),
}))

// 占位数据
const usingKey = ref('preset-2')
const presets = ref([
  { key:'preset-1', icon:'🧩', name:'占位预设 A', desc:'用于演示的占位预设，描述文案较短。' },
  { key:'preset-2', icon:'🧪', name:'占位预设 B', desc:'用于演示的占位预设，当前被标记为使用中。' },
  { key:'preset-3', icon:'🧭', name:'占位预设 C', desc:'用于演示的占位预设，描述可较长以测试多行布局效果与折行。用于演示的占位预设，描述可较长以测试多行布局效果与折行。' },
  { key:'preset-4', icon:'📦', name:'占位预设 D', desc:'预设说明文字' },
  { key:'preset-5', icon:'🧠', name:'占位预设 E', desc:'预设说明文字' },
  { key:'preset-6', icon:'⚙️', name:'占位预设 F', desc:'预设说明文字' },
])

const showViewer = ref(false)
const viewKey = ref(null)
const currentPreset = computed(() => presets.value.find(p => p.key === viewKey.value) || null)

function close(){ emit('close') }
function onUse(k){ usingKey.value = k; emit('use', k) }
function onView(k){
  viewKey.value = k
  showViewer.value = true
  emit('view', k)
}
function onDelete(k){ emit('delete', k) }
</script>

<template>
  <div
    data-scope="presets-view"
    class="pr-panel glass"
    :style="panelStyle"
  >
      <header class="pr-header">
        <div class="pr-title">
          <span class="pr-icon">🧩</span>
          {{ props.title }}
        </div>
        <button class="pr-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <CustomScrollbar class="pr-body">
        <div class="pr-list">
          <div
            v-for="it in presets"
            :key="it.key"
            class="pr-card"
          >
            <div class="pr-main">
              <div class="pr-avatar">{{ it.icon }}</div>
              <div class="pr-texts">
                <div class="pr-name">{{ it.name }}</div>
                <div class="pr-desc">{{ it.desc }}</div>
              </div>
            </div>
            <div class="pr-actions">
              <button
                class="pr-btn"
                :class="{ active: usingKey === it.key }"
                type="button"
                @click="onUse(it.key)"
                :aria-pressed="usingKey === it.key"
              >{{ usingKey === it.key ? '使用中' : '使用' }}</button>

              <button class="pr-btn" type="button" @click="onView(it.key)">查看</button>

              <button class="pr-btn pr-danger" type="button" @click="onDelete(it.key)">删除</button>
            </div>
          </div>
        </div>
      </CustomScrollbar>
    </div>

  <ViewerModal
    v-model="showViewer"
    :title="currentPreset ? ('预设：' + currentPreset.name) : '预设详情'"
  >
    <ClonedPresetView />
  </ViewerModal>
</template>

<style scoped>
.pr-panel {
  display: grid;
  grid-template-rows: auto 1fr;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(var(--st-surface), 0.92);
  backdrop-filter: blur(8px) saturate(130%);
  -webkit-backdrop-filter: blur(8px) saturate(130%);
  box-shadow: var(--st-shadow-md);
  overflow: hidden;
}

/* Header */
.pr-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.pr-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.pr-icon { font-size: 18px; }
.pr-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 8px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.pr-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Body */
.pr-body {
  padding: 12px;
  overflow: hidden;
}
.pr-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

/* Card */
.pr-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: stretch;
  border: 1px solid rgb(var(--st-border));
  border-radius: var(--st-radius-md);
  background: rgb(var(--st-surface));
  padding: 12px;
  transition: background .12s ease, border-color .12s ease, transform .12s ease, box-shadow .12s ease;
}
.pr-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Left main */
.pr-main {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
}
.pr-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: linear-gradient(135deg, rgba(var(--st-primary),0.12), rgba(var(--st-accent),0.12));
  border: 1px solid rgba(var(--st-border), 0.9);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.25);
}
.pr-texts { min-width: 0; }
.pr-name {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pr-desc {
  margin-top: 4px;
  color: rgba(var(--st-color-text), 0.75);
  font-size: 12px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2; /* 标准属性，用于兼容性 */
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Right actions (vertical) */
.pr-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  justify-content: center;
}
.pr-btn {
  appearance: none;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  padding: 8px 10px;
  border-radius: 10px;
  font-size: 12px;
  cursor: pointer;
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease, border-color .12s ease;
  min-width: 64px;
  text-align: center;
}
.pr-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}
.pr-btn.active {
  border-color: rgba(var(--st-primary), 0.5);
  background: rgba(var(--st-primary), 0.08);
}
.pr-btn.pr-danger {
  border-color: rgba(220, 38, 38, 0.5);
  color: rgb(var(--st-color-text));
  background: rgba(220, 38, 38, 0.06);
}
.pr-btn.pr-danger:hover {
  border-color: rgba(220, 38, 38, 0.7);
  background: rgba(220, 38, 38, 0.1);
}


@media (max-width: 640px) {
  .pr-card { grid-template-columns: 1fr; }
  .pr-actions { flex-direction: row; }
}
</style>