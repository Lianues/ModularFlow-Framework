<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  anchorLeft: { type: Number, default: 348 },
  width: { type: Number, default: 520 },
  zIndex: { type: Number, default: 59 },
  top: { type: Number, default: 64 },
  bottom: { type: Number, default: 12 },
  title: { type: String, default: '应用设置 App Settings' },
})

const emit = defineEmits(['close'])

const panelStyle = computed(() => ({
  position: 'fixed',
  left: props.anchorLeft + 'px',
  top: props.top + 'px',
  bottom: props.bottom + 'px',
  width: props.width + 'px',
  zIndex: String(props.zIndex),
}))

function close(){ emit('close') }
onMounted(() => window.lucide?.createIcons?.())
</script>

<template>
  <div
    data-scope="appsettings-view"
    class="as-panel glass"
    :style="panelStyle"
  >
      <header class="as-header">
        <div class="as-title">
          <span class="as-icon"><i data-lucide="settings"></i></span>
          {{ props.title }}
        </div>
        <button class="as-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <CustomScrollbar class="as-body">
        <div class="as-content">
          <h3>应用设置（占位）</h3>
          <p class="muted">此为独立的应用设置页面，用于配置全局应用行为与高级选项。</p>
          
          <div class="as-placeholder-grid">
            <div class="as-placeholder-card">
              <div class="as-placeholder-icon">🔔</div>
              <div class="as-placeholder-title">通知设置</div>
              <div class="as-placeholder-desc">配置应用通知与提醒方式</div>
            </div>
            
            <div class="as-placeholder-card">
              <div class="as-placeholder-icon">🗄️</div>
              <div class="as-placeholder-title">数据存储</div>
              <div class="as-placeholder-desc">管理本地数据与缓存策略</div>
            </div>
            
            <div class="as-placeholder-card">
              <div class="as-placeholder-icon">🔒</div>
              <div class="as-placeholder-title">隐私与安全</div>
              <div class="as-placeholder-desc">配置隐私保护与安全选项</div>
            </div>
            
            <div class="as-placeholder-card">
              <div class="as-placeholder-icon">🌐</div>
              <div class="as-placeholder-title">语言与区域</div>
              <div class="as-placeholder-desc">设置语言、时区与地区偏好</div>
            </div>
            
            <div class="as-placeholder-card">
              <div class="as-placeholder-icon">🔌</div>
              <div class="as-placeholder-title">插件与扩展</div>
              <div class="as-placeholder-desc">管理已安装的插件与扩展</div>
            </div>
            
            <div class="as-placeholder-card">
              <div class="as-placeholder-icon">📊</div>
              <div class="as-placeholder-title">统计与日志</div>
              <div class="as-placeholder-desc">查看使用统计与系统日志</div>
            </div>
          </div>
        </div>
      </CustomScrollbar>
    </div>
</template>

<style scoped>
.as-panel {
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
.as-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.as-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.as-icon i { width: 18px; height: 18px; display: inline-block; }
.as-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), background .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
.as-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Body */
.as-body {
  padding: 12px;
  overflow: hidden;
}
.as-content h3 { margin: 0 0 6px; font-weight: 700; color: rgb(var(--st-color-text)); }
.as-content .muted { color: rgba(var(--st-color-text), 0.75); margin: 0 0 16px; font-size: 13px; }

/* Placeholder grid */
.as-placeholder-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.as-placeholder-card {
  border: 1px solid rgb(var(--st-border));
  border-radius: var(--st-radius-md);
  background: rgb(var(--st-surface));
  padding: 16px;
  text-align: center;
  transition: background .12s ease, border-color .12s ease, transform .12s ease, box-shadow .12s ease;
}

.as-placeholder-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--st-shadow-sm);
}

.as-placeholder-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.as-placeholder-title {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  margin-bottom: 4px;
}

.as-placeholder-desc {
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.7);
  line-height: 1.4;
}

@media (max-width: 640px) {
  .as-placeholder-grid { grid-template-columns: 1fr; }
}
</style>