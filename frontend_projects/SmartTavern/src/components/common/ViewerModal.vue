<script setup>
import { onMounted, onBeforeUnmount, computed } from 'vue'

const props = defineProps({
  // 标题
  title: { type: String, default: '查看详情' },
  // 是否显示
  modelValue: { type: Boolean, default: false },
  // 面板宽度（大号窗口）
  width: { type: Number, default: 1200 },
  // 层级
  zIndex: { type: Number, default: 80 },
  // 是否允许点击遮罩关闭
  closeOnBackdrop: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue', 'close'])

function close() {
  emit('update:modelValue', false)
  emit('close')
}

function onKeydown(e) {
  if (e.key === 'Escape') {
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})

const wrapperStyle = computed(() => ({
  position: 'fixed',
  inset: 0,
  zIndex: String(props.zIndex),
}))

const panelStyle = computed(() => ({
  width: props.width + 'px',
}))
</script>

<template>
  <transition name="st-subpage">
    <div v-if="modelValue" :style="wrapperStyle" data-scope="viewer-modal">
      <!-- 背景遮罩 -->
      <div class="vm-backdrop" @click="closeOnBackdrop ? close() : null" />

      <!-- 居中大窗口 -->
      <div class="vm-shell">
        <div class="vm-panel glass" :style="panelStyle">
          <header class="vm-header">
            <div class="vm-title">
              <span class="vm-icon">🔎</span>
              {{ title }}
            </div>
            <button class="vm-close" type="button" title="关闭" @click="close">✕</button>
          </header>

          <div class="vm-body">
            <!-- 占位内容区域：插槽 -->
            <slot>
              <div class="vm-placeholder">
                <div class="vm-placeholder-icon">📄</div>
                <div class="vm-placeholder-title">占位查看内容</div>
                <div class="vm-placeholder-desc">
                  这里将展示 PromptEditor 对应的主页面内容。当前为占位视图，用于联调“查看”打开/关闭流程。
                </div>
              </div>
            </slot>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
/* 遮罩 */
.vm-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.35);
  backdrop-filter: blur(1px);
  -webkit-backdrop-filter: blur(1px);
}

/* 居中容器 */
.vm-shell {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
}

/* 大号窗口面板（玻璃风格与预设面板一致基因） */
.vm-panel {
  display: grid;
  grid-template-rows: auto 1fr;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px) saturate(130%);
  -webkit-backdrop-filter: blur(10px) saturate(130%);
  box-shadow: 0 16px 60px rgba(0,0,0,0.2);
  max-height: min(86vh, 980px);
  overflow: hidden;
}

/* 头部 */
.vm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.vm-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.vm-icon { font-size: 18px; }
.vm-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 8px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.vm-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* 内容区域 */
.vm-body {
  padding: 14px;
  overflow: auto;
}

/* 默认占位内容（若未传插槽时） */
.vm-placeholder {
  display: grid;
  grid-template-columns: 1fr;
  place-items: center;
  text-align: center;
  gap: 10px;
  padding: 40px 10px;
  color: rgba(var(--st-color-text), 0.9);
}
.vm-placeholder-icon { font-size: 40px; }
.vm-placeholder-title { font-weight: 800; font-size: 18px; }
.vm-placeholder-desc { font-size: 13px; color: rgba(var(--st-color-text), 0.75); }

/* 内嵌页面 iframe（用于嵌入 PromptEditor 视图，占位/联调） */
.vm-iframe {
  width: 100%;
  height: min(72vh, 820px);
  border: 0;
  border-radius: 12px;
  background: rgb(var(--st-surface));
  box-shadow: var(--st-shadow-sm) inset;
}

/* 过渡已沿用 st-subpage（与项目现有一致） */
</style>