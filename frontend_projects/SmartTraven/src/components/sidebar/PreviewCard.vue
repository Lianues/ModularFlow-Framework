<script setup>
const props = defineProps({
  icon: { type: String, default: '✨' },
  title: { type: String, required: true },
  desc: { type: String, default: '' },
  part: { type: String, default: '' },
})
const emit = defineEmits(['click'])
</script>

<template>
  <button
    type="button"
    class="st-preview-card"
    :data-part="props.part || undefined"
    :title="props.title"
    @click="emit('click')"
  >
    <div class="st-preview-head">
      <span class="st-icon">{{ props.icon }}</span>
      <div class="st-preview-title">{{ props.title }}</div>
    </div>
    <div v-if="props.desc" class="st-preview-desc">
      {{ props.desc }}
    </div>
    <div class="st-preview-badge">即将可配置</div>
  </button>
</template>

<style scoped>
/* 预览卡：与全局 Design Tokens 兼容，遵循 4/8 间距体系 */
.st-preview-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: center;
  text-align: left;
  width: 100%;
  padding: 12px;
  border-radius: var(--st-radius-md);
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface-2));
  cursor: pointer;
  transition: transform .12s ease, background .12s ease, box-shadow .12s ease;
}
.st-preview-card:hover {
  transform: translateY(-1px);
  background: rgb(var(--st-surface));
  box-shadow: var(--st-shadow-sm);
}

.st-preview-head { display: contents; }
.st-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px; height: 30px;
  border-radius: 10px;
  background: rgba(var(--st-primary), 0.14);
}
.st-preview-title {
  font-size: 14px;
  font-weight: 600;
  color: rgb(var(--st-color-text));
}
.st-preview-desc {
  grid-column: 1 / -1;
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.7);
  margin-top: 2px;
}
.st-preview-badge {
  display: inline-block;
  margin-top: 6px;
  padding: 2px 6px;
  font-size: 11px;
  color: rgb(var(--st-color-text));
  background: rgba(var(--st-primary),0.12);
  border: 1px solid rgba(var(--st-primary),0.32);
  border-radius: 9999px;
}
</style>