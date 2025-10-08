<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  anchorLeft: { type: Number, default: 348 },
  width: { type: Number, default: 520 },
  zIndex: { type: Number, default: 59 },
  top: { type: Number, default: 64 },
  bottom: { type: Number, default: 12 },
  title: { type: String, default: '正则 Regex Rules' },
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
const usingKey = ref('regex-2')
const regexRules = ref([
  { key:'regex-1', icon:'🧹', name:'占位正则 A', desc:'示例清洗规则，用于文本后处理与格式规范化。' },
  { key:'regex-2', icon:'🔧', name:'占位正则 B', desc:'示例清洗规则，当前被标记为使用中。' },
  { key:'regex-3', icon:'⚙️', name:'占位正则 C', desc:'示例清洗规则，描述可较长以测试多行布局效果与折行。示例清洗规则，描述可较长以测试多行布局效果与折行。' },
  { key:'regex-4', icon:'🛠️', name:'占位正则 D', desc:'文本后处理规则' },
  { key:'regex-5', icon:'📝', name:'占位正则 E', desc:'文本后处理规则' },
])

function close(){ emit('close') }
function onUse(k){ usingKey.value = k; emit('use', k) }
function onView(k){ emit('view', k) }
function onDelete(k){ emit('delete', k) }
</script>

<template>
  <div
    data-scope="regex-view"
    class="rg-panel glass"
    :style="panelStyle"
  >
      <header class="rg-header">
        <div class="rg-title">
          <span class="rg-icon">🧹</span>
          {{ props.title }}
        </div>
        <button class="rg-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <CustomScrollbar class="rg-body">
        <div class="rg-list">
          <div
            v-for="it in regexRules"
            :key="it.key"
            class="rg-card"
          >
            <div class="rg-main">
              <div class="rg-avatar">{{ it.icon }}</div>
              <div class="rg-texts">
                <div class="rg-name">{{ it.name }}</div>
                <div class="rg-desc">{{ it.desc }}</div>
              </div>
            </div>
            <div class="rg-actions">
              <button
                class="rg-btn"
                :class="{ active: usingKey === it.key }"
                type="button"
                @click="onUse(it.key)"
                :aria-pressed="usingKey === it.key"
              >{{ usingKey === it.key ? '使用中' : '使用' }}</button>

              <button class="rg-btn" type="button" @click="onView(it.key)">查看</button>

              <button class="rg-btn rg-danger" type="button" @click="onDelete(it.key)">删除</button>
            </div>
          </div>
        </div>
      </CustomScrollbar>
    </div>
</template>

<style scoped>
.rg-panel {
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
.rg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.rg-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.rg-icon { font-size: 18px; }
.rg-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 8px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.rg-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Body */
.rg-body {
  padding: 12px;
  overflow: hidden;
}
.rg-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

/* Card */
.rg-card {
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
.rg-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Left main */
.rg-main {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
}
.rg-avatar {
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
.rg-texts { min-width: 0; }
.rg-name {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rg-desc {
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
.rg-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  justify-content: center;
}
.rg-btn {
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
.rg-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}
.rg-btn.active {
  border-color: rgba(var(--st-primary), 0.5);
  background: rgba(var(--st-primary), 0.08);
}
.rg-btn.rg-danger {
  border-color: rgba(220, 38, 38, 0.5);
  color: rgb(var(--st-color-text));
  background: rgba(220, 38, 38, 0.06);
}
.rg-btn.rg-danger:hover {
  border-color: rgba(220, 38, 38, 0.7);
  background: rgba(220, 38, 38, 0.1);
}

@media (max-width: 640px) {
  .rg-card { grid-template-columns: 1fr; }
  .rg-actions { flex-direction: row; }
}
</style>