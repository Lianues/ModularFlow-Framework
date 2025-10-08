<script setup>
import { ref, computed } from 'vue'
import ViewerModal from '@/components/common/ViewerModal.vue'
import ClonedPersonaView from '@/components/viewer/ClonedPersonaView.vue'

const props = defineProps({
  anchorLeft: { type: Number, default: 348 },
  width: { type: Number, default: 520 },
  zIndex: { type: Number, default: 59 },
  top: { type: Number, default: 64 },
  bottom: { type: Number, default: 12 },
  title: { type: String, default: '用户信息 Persona' },
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
const usingKey = ref('persona-1')
const personas = ref([
  { key:'persona-1', icon:'🧠', name:'占位用户 A', desc:'示例用户画像，包含用户偏好与对话风格设定。' },
  { key:'persona-2', icon:'👤', name:'占位用户 B', desc:'示例用户画像，当前被标记为使用中。' },
  { key:'persona-3', icon:'🎯', name:'占位用户 C', desc:'示例用户画像，描述可较长以测试多行布局效果与折行。示例用户画像，描述可较长以测试多行布局效果与折行。' },
  { key:'persona-4', icon:'💼', name:'占位用户 D', desc:'用户偏好与画像' },
])

const showViewer = ref(false)
const viewKey = ref(null)
const currentPersona = computed(() => personas.value.find(p => p.key === viewKey.value) || null)

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
    data-scope="persona-view"
    class="ps-panel glass"
    :style="panelStyle"
  >
      <header class="ps-header">
        <div class="ps-title">
          <span class="ps-icon">🧠</span>
          {{ props.title }}
        </div>
        <button class="ps-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <CustomScrollbar class="ps-body">
        <div class="ps-list">
          <div
            v-for="it in personas"
            :key="it.key"
            class="ps-card"
          >
            <div class="ps-main">
              <div class="ps-avatar">{{ it.icon }}</div>
              <div class="ps-texts">
                <div class="ps-name">{{ it.name }}</div>
                <div class="ps-desc">{{ it.desc }}</div>
              </div>
            </div>
            <div class="ps-actions">
              <button
                class="ps-btn"
                :class="{ active: usingKey === it.key }"
                type="button"
                @click="onUse(it.key)"
                :aria-pressed="usingKey === it.key"
              >{{ usingKey === it.key ? '使用中' : '使用' }}</button>

              <button class="ps-btn" type="button" @click="onView(it.key)">查看</button>

              <button class="ps-btn ps-danger" type="button" @click="onDelete(it.key)">删除</button>
            </div>
          </div>
        </div>
      </CustomScrollbar>
    </div>
  <ViewerModal
    v-model="showViewer"
    :title="currentPersona ? ('用户：' + currentPersona.name) : '用户信息'"
  >
    <ClonedPersonaView />
  </ViewerModal>
</template>

<style scoped>
.ps-panel {
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
.ps-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.ps-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.ps-icon { font-size: 18px; }
.ps-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 8px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.ps-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Body */
.ps-body {
  padding: 12px;
  overflow: hidden;
}
.ps-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

/* Card */
.ps-card {
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
.ps-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Left main */
.ps-main {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
}
.ps-avatar {
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
.ps-texts { min-width: 0; }
.ps-name {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ps-desc {
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
.ps-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  justify-content: center;
}
.ps-btn {
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
.ps-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}
.ps-btn.active {
  border-color: rgba(var(--st-primary), 0.5);
  background: rgba(var(--st-primary), 0.08);
}
.ps-btn.ps-danger {
  border-color: rgba(220, 38, 38, 0.5);
  color: rgb(var(--st-color-text));
  background: rgba(220, 38, 38, 0.06);
}
.ps-btn.ps-danger:hover {
  border-color: rgba(220, 38, 38, 0.7);
  background: rgba(220, 38, 38, 0.1);
}

@media (max-width: 640px) {
  .ps-card { grid-template-columns: 1fr; }
  .ps-actions { flex-direction: row; }
}
</style>