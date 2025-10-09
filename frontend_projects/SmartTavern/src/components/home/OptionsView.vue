<script setup>
import { ref, onMounted } from "vue"
onMounted(() => window.lucide?.createIcons?.())

// 占位状态（控件禁用，仅作演示）
const lang = ref("zh-CN")
const volume = ref(60)
const theme = ref("system")
</script>

<template>
  <section class="home-modal-section">
    <div class="hm-title">
      <i data-lucide="settings" class="icon-20" aria-hidden="true"></i>
      <h2>选项</h2>
    </div>
    <p class="hm-desc">占位界面：未来这里提供音量、语言、显示与键位等设置。</p>

    <div class="opt-panel">
      <div class="opt-row">
        <label class="opt-label">语言</label>
        <select class="opt-input" v-model="lang" disabled>
          <option value="zh-CN">简体中文</option>
          <option value="en-US">English</option>
          <option value="ja-JP">日本語</option>
        </select>
      </div>

      <div class="opt-row">
        <label class="opt-label">主题</label>
        <select class="opt-input" v-model="theme" disabled>
          <option value="system">系统</option>
          <option value="light">浅色</option>
          <option value="dark">深色</option>
        </select>
      </div>

      <div class="opt-row">
        <label class="opt-label">音量</label>
        <input type="range" min="0" max="100" v-model="volume" class="opt-range" disabled />
        <span class="opt-val">{{ volume }}%</span>
      </div>

      <div class="opt-hint">当前为占位界面，控件不可用。</div>
    </div>
  </section>
</template>

<style scoped>
.home-modal-section { display: grid; gap: 12px; }
.hm-title { display: flex; align-items: center; gap: 10px; }
.hm-title .icon-20 { width: 20px; height: 20px; stroke: currentColor; color: rgb(var(--st-color-text)); }
.hm-title h2 { margin: 0; font-size: 18px; font-weight: 700; color: rgb(var(--st-color-text)); }
.hm-desc { margin: 0 0 8px; font-size: 12px; color: rgba(var(--st-color-text), 0.7); }

.opt-panel {
  display: grid; gap: 12px;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  border-radius: var(--st-radius-lg);
  padding: 12px;
}
.opt-row {
  display: grid;
  grid-template-columns: 120px 1fr auto;
  gap: 10px; align-items: center;
}
@media (max-width: 640px) {
  .opt-row { grid-template-columns: 1fr; align-items: start; }
}

.opt-label { font-size: 13px; color: rgba(var(--st-color-text), .85); font-weight: 600; }
.opt-input {
  width: 100%; padding: 8px 10px; border-radius: 8px;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface-2));
  color: rgb(var(--st-color-text));
  opacity: .7;
}
.opt-range { width: 100%; }
.opt-val { font-size: 12px; color: rgba(var(--st-color-text), .7); }

.opt-hint { font-size: 12px; color: rgba(var(--st-color-text), .6); }
</style>
