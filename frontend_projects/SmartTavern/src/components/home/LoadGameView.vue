<script setup>
import { onMounted } from "vue"
onMounted(() => window.lucide?.createIcons?.())
</script>

<template>
  <section class="home-modal-section">
    <div class="hm-title">
      <i data-lucide="history" class="icon-20" aria-hidden="true"></i>
      <h2>读取存档</h2>
    </div>
    <p class="hm-desc">占位界面：未来这里展示最近记录与存档槽，支持筛选与删除。</p>

    <div class="hm-grid">
      <div class="hm-card" v-for="i in 6" :key="i">
        <div class="hm-thumb" />
        <div class="hm-meta">
          <div class="hm-name">存档槽 {{ i }}</div>
          <div class="hm-sub">2025-01-01 12:00</div>
        </div>
        <button class="hm-btn" type="button" disabled>加载</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.home-modal-section { display: grid; gap: 12px; }
.hm-title { display: flex; align-items: center; gap: 10px; }
.hm-title .icon-20 { width: 20px; height: 20px; stroke: currentColor; color: rgb(var(--st-color-text)); }
.hm-title h2 { margin: 0; font-size: 18px; font-weight: 700; color: rgb(var(--st-color-text)); }
.hm-desc { margin: 0 0 8px; font-size: 12px; color: rgba(var(--st-color-text), 0.7); }

.hm-grid { display: grid; grid-template-columns: repeat(2, minmax(260px, 1fr)); gap: 12px; }
@media (max-width: 720px) { .hm-grid { grid-template-columns: 1fr; } }

.hm-card {
  display: grid;
  grid-template-columns: 96px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: var(--st-radius-md);
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  transition: transform .18s cubic-bezier(.22,.61,.36,1), box-shadow .18s, border-color .18s;
}
.hm-card:hover { transform: translateY(-1px); box-shadow: var(--st-shadow-sm); border-color: rgba(var(--st-primary), .45); }

.hm-thumb {
  width: 96px; height: 60px; border-radius: 8px;
  background: linear-gradient(135deg, rgba(var(--st-primary), .12), rgba(var(--st-accent), .12));
  border: 1px solid rgba(var(--st-border), .9);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.2);
}

.hm-meta { min-width: 0; }
.hm-name { font-weight: 700; color: rgb(var(--st-color-text)); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hm-sub { margin-top: 2px; font-size: 12px; color: rgba(var(--st-color-text), .65); }

.hm-btn {
  appearance: none;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  color: rgba(var(--st-color-text), .9);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: not-allowed;
  opacity: .7;
}
</style>
