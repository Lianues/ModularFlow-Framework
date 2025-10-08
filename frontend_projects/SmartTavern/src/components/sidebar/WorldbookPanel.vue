<script setup>
import { ref, computed } from 'vue'
import ViewerModal from '@/components/common/ViewerModal.vue'
import ClonedWorldbookView from '@/components/viewer/ClonedWorldbookView.vue'

const props = defineProps({
  anchorLeft: { type: Number, default: 348 },
  width: { type: Number, default: 520 },
  zIndex: { type: Number, default: 59 },
  top: { type: Number, default: 64 },
  bottom: { type: Number, default: 12 },
  title: { type: String, default: '世界书 Worldbook' },
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
const usingKey = ref('worldbook-1')
const worldbooks = ref([
  { key:'worldbook-1', icon:'📚', name:'占位世界书 A', desc:'示例世界观设定，包含世界观术语与背景知识。' },
  { key:'worldbook-2', icon:'🌍', name:'占位世界书 B', desc:'示例世界观设定，当前被标记为使用中。' },
  { key:'worldbook-3', icon:'📖', name:'占位世界书 C', desc:'示例世界观设定，描述可较长以测试多行布局效果与折行。示例世界观设定，描述可较长以测试多行布局效果与折行。' },
  { key:'worldbook-4', icon:'🗺️', name:'占位世界书 D', desc:'世界观术语库' },
  { key:'worldbook-5', icon:'📜', name:'占位世界书 E', desc:'世界观术语库' },
])

const showViewer = ref(false)
const viewKey = ref(null)
const currentWb = computed(() => worldbooks.value.find(w => w.key === viewKey.value) || null)

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
    data-scope="worldbook-view"
    class="wb-panel glass"
    :style="panelStyle"
  >
      <header class="wb-header">
        <div class="wb-title">
          <span class="wb-icon">📚</span>
          {{ props.title }}
        </div>
        <button class="wb-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <CustomScrollbar class="wb-body">
        <div class="wb-list">
          <div
            v-for="it in worldbooks"
            :key="it.key"
            class="wb-card"
          >
            <div class="wb-main">
              <div class="wb-avatar">{{ it.icon }}</div>
              <div class="wb-texts">
                <div class="wb-name">{{ it.name }}</div>
                <div class="wb-desc">{{ it.desc }}</div>
              </div>
            </div>
            <div class="wb-actions">
              <button
                class="wb-btn"
                :class="{ active: usingKey === it.key }"
                type="button"
                @click="onUse(it.key)"
                :aria-pressed="usingKey === it.key"
              >{{ usingKey === it.key ? '使用中' : '使用' }}</button>

              <button class="wb-btn" type="button" @click="onView(it.key)">查看</button>

              <button class="wb-btn wb-danger" type="button" @click="onDelete(it.key)">删除</button>
            </div>
          </div>
        </div>
      </CustomScrollbar>
    </div>

  <ViewerModal
    v-model="showViewer"
    :title="currentWb ? ('世界书：' + currentWb.name) : '世界书详情'"
  >
    <ClonedWorldbookView />
  </ViewerModal>
</template>

<style scoped>
.wb-panel {
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
.wb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.wb-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.wb-icon { font-size: 18px; }
.wb-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 8px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.wb-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Body */
.wb-body {
  padding: 12px;
  overflow: hidden;
}
.wb-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

/* Card */
.wb-card {
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
.wb-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Left main */
.wb-main {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
}
.wb-avatar {
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
.wb-texts { min-width: 0; }
.wb-name {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.wb-desc {
  margin-top: 4px;
  color: rgba(var(--st-color-text), 0.75);
  font-size: 12px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Right actions (vertical) */
.wb-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  justify-content: center;
}
.wb-btn {
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
.wb-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}
.wb-btn.active {
  border-color: rgba(var(--st-primary), 0.5);
  background: rgba(var(--st-primary), 0.08);
}
.wb-btn.wb-danger {
  border-color: rgba(220, 38, 38, 0.5);
  color: rgb(var(--st-color-text));
  background: rgba(220, 38, 38, 0.06);
}
.wb-btn.wb-danger:hover {
  border-color: rgba(220, 38, 38, 0.7);
  background: rgba(220, 38, 38, 0.1);
}

@media (max-width: 640px) {
  .wb-card { grid-template-columns: 1fr; }
  .wb-actions { flex-direction: row; }
}
</style>