<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  anchorLeft: { type: Number, default: 308 },
  width: { type: Number, default: 560 },
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

function close(){ emit('close') }
function onUse(k){ usingKey.value = k; emit('use', k) }
function onView(k){ emit('view', k) }
function onDelete(k){ emit('delete', k) }
/** 图标渲染：lucide 名称优先，否则回退 emoji */
const isLucide = (v) => typeof v === 'string' && /^[a-z\-]+$/.test(v)
onMounted(() => window.lucide?.createIcons?.())
</script>

<template>
  <div
    data-scope="characters-view"
    class="ch-panel glass"
    :style="panelStyle"
  >
      <header class="ch-header">
        <div class="ch-title">
          <span class="ch-icon"><i data-lucide="users"></i></span>
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
              <div class="ch-avatar">
                <i v-if="isLucide(it.icon)" :data-lucide="it.icon"></i>
                <span v-else>{{ it.icon }}</span>
              </div>
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
.ch-icon i { width: 18px; height: 18px; display: inline-block; }
.ch-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), background .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
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
  gap: 12px;
}

/* Card */
.ch-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: stretch;
  border: 1px solid rgb(var(--st-border));
  border-radius: var(--st-radius-md);
  background: rgb(var(--st-surface));
  padding: 12px;
  transition: background .2s cubic-bezier(.22,.61,.36,1), border-color .2s cubic-bezier(.22,.61,.36,1), transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
.ch-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Left main */
.ch-main {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: center;
}
.ch-avatar {
  width: 40px;
  height: 40px;
  border-radius: 4px;
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
  gap: 8px;
  justify-content: center;
}
.ch-btn {
  appearance: none;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1), background .2s cubic-bezier(.22,.61,.36,1), border-color .2s cubic-bezier(.22,.61,.36,1);
  min-width: 64px;
  text-align: center;
}
.ch-btn:focus-visible,
.ch-close:focus-visible {
  outline: 2px solid rgba(var(--st-primary), 0.6);
  outline-offset: 2px;
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