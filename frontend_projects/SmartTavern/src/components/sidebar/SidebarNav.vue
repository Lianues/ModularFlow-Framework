<script setup>
import { onMounted, onUpdated } from 'vue'
import PreviewCard from './PreviewCard.vue'
const emit = defineEmits(['openAppearance','openAppSettings','openPresets','openWorldbook','openCharacters','openPersona','openRegex','update:view','update:theme'])

const props = defineProps({
  view: { type: String, default: 'start' },   // 'start' | 'threaded' | 'sandbox'
  theme: { type: String, default: 'system' }  // 'system' | 'light' | 'dark'
})

const items = [
  { key: 'presets', icon: 'puzzle', title: '预设 Presets', desc: '管理提示词预设与切换' },
  { key: 'worldbook', icon: 'book-open', title: '世界书 Worldbook', desc: '设定世界观/术语库' },
  { key: 'characters', icon: 'users', title: '角色卡 Characters', desc: '管理角色信息卡' },
  { key: 'persona', icon: 'user-cog', title: '用户信息 Persona', desc: '配置用户画像与偏好' },
  { key: 'regex', icon: 'scan-text', title: '正则 Regex Rules', desc: '清洗/后处理规则' },
  { key: 'themes', icon: 'palette', title: '外观 Appearance', desc: '主题与外观设定' },
  { key: 'app', icon: 'settings', title: '应用设置 App Settings', desc: '全局应用行为与高级选项' },
]

function onClick(key) {
  if (key === 'themes') emit('openAppearance')
  else if (key === 'app') emit('openAppSettings')
  else if (key === 'presets') emit('openPresets')
  else if (key === 'worldbook') emit('openWorldbook')
  else if (key === 'characters') emit('openCharacters')
  else if (key === 'persona') emit('openPersona')
  else if (key === 'regex') emit('openRegex')
}

function gotoHome() { emit('update:view', 'start') }
function toggleMode() { emit('update:view', props.view === 'threaded' ? 'sandbox' : 'threaded') }
function toggleTheme() {
  const order = ['system','light','dark']
  const i = Math.max(0, order.indexOf(props.theme))
  emit('update:theme', order[(i+1)%order.length])
}

onMounted(() => window.lucide?.createIcons?.())
onUpdated(() => window.lucide?.createIcons?.())
</script>

<template>
  <div data-scope="sidebar-nav" class="st-sidebar-nav">
    <!-- 顶部控制栏：仅在非主页视图时显示 -->
    <div v-if="props.view !== 'start'" class="st-side-controls">
      <button class="ctrl-btn" type="button" @click="gotoHome">
        <i data-lucide="home" class="icon-16" aria-hidden="true"></i>
      </button>
      <button class="ctrl-btn" type="button" @click="toggleMode">
        <i :data-lucide="props.view === 'threaded' ? 'app-window' : 'message-square'" class="icon-16" aria-hidden="true"></i>
        <span class="ctrl-label">{{ props.view === 'threaded' ? '楼层' : '前端' }}</span>
      </button>
      <button class="ctrl-btn" type="button" @click="toggleTheme" :aria-label="`Theme: ${props.theme}`">
        <i :data-lucide="props.theme === 'dark' ? 'moon' : (props.theme === 'light' ? 'sun' : 'circle-dot')" class="icon-16" aria-hidden="true"></i>
        <span class="ctrl-label">{{ props.theme === 'dark' ? '深色' : (props.theme === 'light' ? '浅色' : '系统') }}</span>
      </button>
    </div>

    <div class="st-sidebar-title">配置预览</div>

    <div class="st-preview-grid">
      <PreviewCard
        v-for="it in items"
        :key="it.key"
        :part="`preview-${it.key}`"
        :icon="it.icon"
        :desc="it.desc"
        @click="onClick(it.key)"
      />
    </div>

    <div class="st-sidebar-hint">
      在聊天页面右侧展示的配置入口（预览占位）
    </div>
  </div>
</template>

<style scoped>
/* 侧边栏（使用全局 Design Tokens 变量） */
.st-sidebar-nav { display: flex; flex-direction: column; gap: 12px; }
.st-sidebar-title { font-weight: 700; color: rgb(var(--st-color-text)); }
.st-sidebar-hint { font-size: 12px; color: rgba(var(--st-color-text), 0.6); }

/* 顶部控制栏 */
.st-side-controls {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0 4px 2px;
}
.ctrl-btn {
  appearance: none;
  background: rgba(var(--st-surface), 0.35);
  backdrop-filter: blur(10px) saturate(140%);
  -webkit-backdrop-filter: blur(10px) saturate(140%);
  border: 1px solid rgba(var(--st-border), 0.9);
  color: rgba(var(--st-color-text), 0.9);
  min-height: 30px;
  padding: 6px 10px;
  border-radius: var(--st-radius-md);
  display: inline-flex; align-items: center; justify-content: center;
  gap: 6px;
  cursor: pointer;
  transition: transform .18s cubic-bezier(.22,.61,.36,1), box-shadow .18s ease, border-color .18s ease;
}
.ctrl-btn:hover { transform: translateY(-1px); box-shadow: var(--st-shadow-sm); border-color: rgba(var(--st-primary), .5); }
.ctrl-label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .2px;
  color: inherit;
  user-select: none;
}

.icon-16 { width: 16px; height: 16px; stroke: currentColor; }

/* 网格 */
.st-preview-grid { display: grid; grid-template-columns: 1fr; gap: 10px; }

/* 预览卡样式已迁移到 PreviewCard.vue，Sidebar 仅保留容器与布局样式 */
</style>