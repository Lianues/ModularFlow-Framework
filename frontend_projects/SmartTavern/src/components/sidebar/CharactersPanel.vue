<script setup>
import { ref, computed } from 'vue'
import ViewerModal from '@/components/common/ViewerModal.vue'
import ClonedCharacterView from '@/components/viewer/ClonedCharacterView.vue'

const props = defineProps({
  anchorLeft: { type: Number, default: 348 },
  width: { type: Number, default: 520 },
  zIndex: { type: Number, default: 59 },
  top: { type: Number, default: 64 },
  bottom: { type: Number, default: 12 },
  title: { type: String, default: '角色卡 Characters' },
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
const usingKey = ref('char-2')
const characters = ref([
  { key:'char-1', icon:'🧑‍🚀', name:'占位角色 A', desc:'示例角色卡，包含角色性格、背景与对话风格。' },
  { key:'char-2', icon:'👤', name:'占位角色 B', desc:'示例角色卡，当前被标记为使用中。' },
  { key:'char-3', icon:'🎭', name:'占位角色 C', desc:'示例角色卡，描述可较长以测试多行布局效果与折行。示例角色卡，描述可较长以测试多行布局效果与折行。' },
  { key:'char-4', icon:'👨‍💼', name:'占位角色 D', desc:'角色设定与对话风格' },
  { key:'char-5', icon:'👩‍🎨', name:'占位角色 E', desc:'角色设定与对话风格' },
  { key:'char-6', icon:'🤖', name:'占位角色 F', desc:'角色设定与对话风格' },
])

// 查看弹窗状态（与预设/世界书一致）
const showViewer = ref(false)
const viewKey = ref(null)
const currentChar = computed(() => characters.value.find(c => c.key === viewKey.value) || null)

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
    data-scope="characters-view"
    class="ch-panel glass"
    :style="panelStyle"
  >
      <header class="ch-header">
        <div class="ch-title">
          <span class="ch-icon">🧑‍🚀</span>
          {{ props.title }}
        </div>
        <button class="ch-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <CustomScrollbar class="ch-body">
        <div class="ch-list">
          <div
            v-for="it in characters"
            :key="it.key"
            class="ch-card"
          >
            <div class="ch-main">
              <div class="ch-avatar">{{ it.icon }}</div>
              <div class="ch-texts">
                <div class="ch-name">{{ it.name }}</div>
                <div class="ch-desc">{{ it.desc }}</div>
              </div>
            </div>
            <div class="ch-actions">
              <button
                class="ch-btn"
                :class="{ active: usingKey === it.key }"
                type="button"
                @click="onUse(it.key)"
                :aria-pressed="usingKey === it.key"
              >{{ usingKey === it.key ? '使用中' : '使用' }}</button>

              <button class="ch-btn" type="button" @click="onView(it.key)">查看</button>

              <button class="ch-btn ch-danger" type="button" @click="onDelete(it.key)">删除</button>
            </div>
          </div>
        </div>
      </CustomScrollbar>
    </div>

  <ViewerModal
    v-model="showViewer"
    :title="currentChar ? ('角色：' + currentChar.name) : '角色详情'"
  >
    <ClonedCharacterView />
  </ViewerModal>
</template>

<style scoped>
.ch-panel {
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
.ch-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.ch-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.ch-icon { font-size: 18px; }
.ch-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 8px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.ch-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Body */
.ch-body {
  padding: 12px;
  overflow: hidden;
}
.ch-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

/* Card */
.ch-card {
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
.ch-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Left main */
.ch-main {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
}
.ch-avatar {
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
.ch-texts { min-width: 0; }
.ch-name {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ch-desc {
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
.ch-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  justify-content: center;
}
.ch-btn {
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
.ch-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}
.ch-btn.active {
  border-color: rgba(var(--st-primary), 0.5);
  background: rgba(var(--st-primary), 0.08);
}
.ch-btn.ch-danger {
  border-color: rgba(220, 38, 38, 0.5);
  color: rgb(var(--st-color-text));
  background: rgba(220, 38, 38, 0.06);
}
.ch-btn.ch-danger:hover {
  border-color: rgba(220, 38, 38, 0.7);
  background: rgba(220, 38, 38, 0.1);
}

@media (max-width: 640px) {
  .ch-card { grid-template-columns: 1fr; }
  .ch-actions { flex-direction: row; }
}
</style>