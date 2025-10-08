<script setup>
import PreviewCard from './PreviewCard.vue'
const emit = defineEmits(['openAppearance','openAppSettings','openPresets','openWorldbook','openCharacters','openPersona','openRegex'])
const items = [
  { key: 'presets', icon: '🧩', title: '预设 Presets', desc: '管理提示词预设与切换' },
  { key: 'worldbook', icon: '📚', title: '世界书 Worldbook', desc: '设定世界观/术语库' },
  { key: 'characters', icon: '🧑‍🚀', title: '角色卡 Characters', desc: '管理角色信息卡' },
  { key: 'persona', icon: '🧠', title: '用户信息 Persona', desc: '配置用户画像与偏好' },
  { key: 'regex', icon: '🧹', title: '正则 Regex Rules', desc: '清洗/后处理规则' },
  { key: 'themes', icon: '🎨', title: '外观 Appearance', desc: '主题与外观设定' },
  { key: 'app', icon: '⚙️', title: '应用设置 App Settings', desc: '全局应用行为与高级选项' },
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
</script>

<template>
  <div data-scope="sidebar-nav" class="st-sidebar-nav">
    <div class="st-sidebar-title">配置预览</div>

    <div class="st-preview-grid">
      <PreviewCard
        v-for="it in items"
        :key="it.key"
        :part="`preview-${it.key}`"
        :icon="it.icon"
        :title="it.title"
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

/* 网格 */
.st-preview-grid { display: grid; grid-template-columns: 1fr; gap: 10px; }

/* 预览卡样式已迁移到 PreviewCard.vue，Sidebar 仅保留容器与布局样式 */
</style>