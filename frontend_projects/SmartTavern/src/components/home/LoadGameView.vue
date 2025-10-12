<script setup>
import { ref, onMounted, nextTick } from 'vue'
import DataCatalog from '@/services/dataCatalog.js'
import ChatBranches from '@/services/chatBranches.js'

/**
 * LoadGameView
 * 需求：
 *  1) 通过 data_catalog 列出对话文件（conversations）
 *  2) 并发调用 chat_branches/get_latest_message 获取每个文件的最后一条消息
 *  3) 汇总后一次性更新面板显示
 */

const loading = ref(false)
const error = ref('')
const items = ref([]) // [{ file, name, description, latest: {node_id, role, content, depth} | null, error?: string }]

function baseName(file) {
  const s = String(file || '')
  const i = s.lastIndexOf('/')
  return i >= 0 ? s.slice(i + 1) : s
}

function roleLabel(role) {
  if (role === 'user') return '用户'
  if (role === 'assistant') return '助手'
  if (role === 'system') return '系统'
  return '未知'
}

function truncate(text, max = 160) {
  const t = String(text || '')
  if (t.length <= max) return t
  return t.slice(0, max - 1) + '…'
}

async function loadData() {
  loading.value = true
  error.value = ''
  items.value = []
  try {
    const list = await DataCatalog.listConversations() // 后端定义见：[python.function(list_conversations)](api/modules/SmartTavern/data_catalog/data_catalog.py:326)
    const rawItems = Array.isArray(list?.items) ? list.items : []
    // 预构造展示数据
    const combined = rawItems.map(it => ({
      file: it.file,
      name: it.name || baseName(it.file),
      description: it.description || '',
      latest: null,
      error: ''
    }))

    // 一次性获取每个文件的最新消息（并发）
    // 若单个失败，不影响整体
    // 刷新时跳过缓存，确保获取最新数据
    const promises = combined.map(async (row, idx) => {
      try {
        const latest = await ChatBranches.getLatestMessageByFile(row.file, { useCache: false }) // 后端定义见：[python.function(get_latest_message)](api/modules/SmartTavern/chat_branches/chat_branches.py:130)
        combined[idx].latest = latest
      } catch (e) {
        combined[idx].error = e?.message || '获取最新消息失败'
      }
    })
    await Promise.allSettled(promises)

    // 一次性更新面板
    items.value = combined

    // 刷新外部图标组件
    nextTick(() => {
      try { window?.lucide?.createIcons?.() } catch (_) {}
      if (typeof window.initFlowbite === 'function') {
        try { window.initFlowbite() } catch (_) {}
      }
    })
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <section data-scope="load-game-view" class="lgv">
    <header class="lgv-header">
      <div class="lgv-title">
        <i class="lgv-icon">💾</i>
        对话存档
      </div>
      <div class="lgv-actions">
        <button class="btn ghost" :disabled="loading" @click="loadData" title="刷新">
          <i data-lucide="refresh-cw" class="icon-16" aria-hidden="true"></i>
          刷新
        </button>
      </div>
    </header>

    <!-- 高级骨架屏加载（微光动画），一行一个卡片 -->
    <div v-if="loading" class="lgv-list">
      <div v-for="n in 2" :key="'sk'+n" class="lgv-card lgv-item lgv-skel">
        <div class="lgv-row">
          <div class="lgv-media">
            <div class="sk-media" aria-hidden="true"></div>
          </div>
          <div class="lgv-main">
            <div class="sk-row w-44"></div>
            <div class="sk-row w-72"></div>
            <div class="sk-row w-56"></div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="error" class="lgv-error">
      <div class="err-icon">⚠️</div>
      <div class="err-text">{{ error }}</div>
    </div>

    <transition-group v-else name="lgv" tag="div" class="lgv-list">
      <div
        v-for="it in items"
        :key="it.file"
        class="lgv-card lgv-item"
      >
        <div class="lgv-row">
          <div class="lgv-media">
            <div class="media-ph" aria-label="封面占位"></div>
          </div>
          <div class="lgv-main">
            <div class="lgv-card-title">
              <span class="lgv-file">{{ it.name }}</span>
              <small class="lgv-file-path">{{ it.file }}</small>
              <div class="lgv-desc" v-if="it.description">
                {{ it.description }}
              </div>
            </div>

            <div v-if="it.error" class="lgv-latest error">
              <div class="err-badge">获取最新消息失败</div>
              <div class="err-detail">{{ it.error }}</div>
            </div>
            <div v-else-if="it.latest" class="lgv-latest">
              <div class="latest-meta">
                <span class="dim">楼层 #{{ it.latest.depth }}</span>
                <span class="badge">{{ roleLabel(it.latest.role) }}</span>
              </div>
              <div class="latest-content">
                {{ truncate(it.latest.content, 220) }}
              </div>
            </div>
            <div v-else class="lgv-latest muted">无最新消息</div>
          </div>
          <div class="lgv-card-actions">
            <button class="btn primary" :disabled="!!it.error" title="确认">
              确认
            </button>
            <button class="btn danger" title="删除">
              删除
            </button>
          </div>
        </div>
      </div>

      <div v-if="items.length === 0" key="empty" class="lgv-empty">
        <div class="empty-icon">📂</div>
        <div class="empty-text">未找到对话存档</div>
      </div>
    </transition-group>
  </section>
</template>

<style scoped>
.icon-16 { width: 16px; height: 16px; stroke: currentColor; }

/* 容器 */
.lgv {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 头部 */
.lgv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0 4px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.lgv-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 18px;
  color: rgb(var(--st-color-text));
}
.lgv-icon { font-size: 22px; }
.lgv-actions { display: inline-flex; gap: 8px; }

/* 按钮 */
.btn {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  border-radius: var(--st-radius-md);
  padding: 12px 16px; /* 增大内边距提升高度 */
  min-height: 48px; /* 最小高度满足触摸区域 */
  width: 100%; /* 确保按钮撑满容器宽度 */
  cursor: pointer;
  display: inline-flex;
  gap: 8px;
  align-items: center;
  justify-content: center; /* 内容水平居中 */
  text-align: center; /* 文字居中 */
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease, border-color .12s ease;
}
.btn:hover { transform: translateY(-1px); box-shadow: var(--st-shadow-sm); }
.btn.primary {
  /* Outline style per UI spec: no solid colored background */
  background: transparent;
  color: rgb(var(--st-primary));
  border-color: rgba(var(--st-primary), 0.55);
}
.btn.primary:hover {
  background: rgba(var(--st-primary), 0.08);
  border-color: rgba(var(--st-primary), 0.7);
}
.btn.ghost { background: rgba(var(--st-surface-2), 0.6); }
.btn.danger {
  /* Outline danger style (no solid fill) */
  background: transparent;
  color: rgb(220, 38, 38);
  border-color: rgba(220, 38, 38, 0.6);
}
.btn.danger:hover {
  background: rgba(220, 38, 38, 0.08);
  border-color: rgba(220, 38, 38, 0.8);
}

/* 加载与错误 */
.lgv-loading, .lgv-error {
  display: grid;
  place-items: center;
  gap: 10px;
  padding: 40px 20px;
}
.spinner {
  width: 22px; height: 22px; border-radius: 50%;
  border: 3px solid currentColor; border-top-color: transparent;
  animation: st-spin 0.9s linear infinite;
  opacity: 0.9;
}
.lgv-loading .text { color: rgba(var(--st-color-text), 0.85); }
.lgv-error .err-icon { font-size: 22px; }
.lgv-error .err-text { color: rgb(220, 38, 38); font-weight: 600; }

/* 列表与卡片 */
.lgv-list {
  display: grid;
  grid-template-columns: 1fr; /* 一行一个卡片 */
  gap: 16px;
  max-width: none; /* 占满页面宽度 */
  width: 100%;
  margin: 0;
  padding: 16px 24px; /* 页面左右内边距 */
  box-sizing: border-box;
}

/* 高级卡片（玻璃+渐变描边+微光） */
.lgv-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  border: 1px solid rgba(var(--st-border), 0.75);
  border-radius: var(--st-radius-lg);
  background: rgb(var(--st-surface) / 0.78) !important;
  backdrop-filter: blur(10px) saturate(130%);
  -webkit-backdrop-filter: blur(10px) saturate(130%);
  padding: 16px;
  transition:
    transform .22s cubic-bezier(.22,.61,.36,1),
    box-shadow .22s cubic-bezier(.22,.61,.36,1),
    border-color .22s cubic-bezier(.22,.61,.36,1),
    background .22s cubic-bezier(.22,.61,.36,1);
  will-change: transform, box-shadow, background, border-color;
}

/* 渐变描边（伪元素） */
.lgv-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  padding: 1px; /* 伪边框宽度 */
  background: linear-gradient(135deg, rgba(var(--st-primary), .34), rgba(var(--st-accent), .34)) border-box;
  -webkit-mask:
    linear-gradient(#000 0 0) padding-box,
    linear-gradient(#000 0 0);
  /* Add standard mask for compatibility */
  mask:
    linear-gradient(#000 0 0) padding-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
          mask-composite: exclude;
}

/* 关闭光泽扫过动画（按需求移除 ::after 效果） */

.lgv-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 44px rgba(0,0,0,0.14);
  border-color: rgba(var(--st-primary), 0.45);
}

/* 卡片内部三列布局：左 media、中 content、右 actions */
.lgv-row {
  display: grid;
  grid-template-columns: 420px 1fr auto;
  gap: 16px;
  align-items: center; /* 垂直居中所有列，按钮列自然居中于图片高度 */
}
.lgv-media { width: 100%; }
.media-ph {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: var(--st-radius-md);
  background:
    linear-gradient(135deg, rgba(var(--st-primary), 0.16), rgba(var(--st-accent), 0.16)),
    repeating-linear-gradient(45deg, rgba(var(--st-color-text),0.06) 0, rgba(var(--st-color-text),0.06) 8px, transparent 8px, transparent 16px);
  border: 1px solid rgba(var(--st-border), 0.7);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.15);
}
.lgv-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-self: start; /* 内容区从顶部开始，不再stretch */
}
@media (max-width: 980px) {
  .lgv-row {
    grid-template-columns: 1fr;
    align-items: start; /* 移动端恢复顶对齐 */
  }
  .lgv-card-actions {
    flex-direction: row; /* 移动端按钮改为水平排列 */
    justify-content: flex-end;
    align-self: auto;
  }
}

/* sheen 效果已移除 */

/* 进场/离场与重排（与 <transition-group name="lgv"> 对应） */
.lgv-enter-from {
  opacity: 0;
  transform: translateY(10px) scale(0.985);
  filter: blur(10px) saturate(0.94);
}
.lgv-enter-to {
  opacity: 1;
  transform: translateY(0) scale(1);
  filter: blur(0);
}
.lgv-enter-active {
  transition:
    opacity .34s cubic-bezier(.22,.61,.36,1),
    transform .42s cubic-bezier(.22,.61,.36,1),
    filter .42s ease;
  will-change: opacity, transform, filter;
}
.lgv-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.985);
  filter: blur(6px);
}
.lgv-leave-active {
  transition:
    opacity .22s ease,
    transform .26s ease,
    filter .26s ease;
}
.lgv-move {
  transition: transform .32s cubic-bezier(.22,.61,.36,1);
  will-change: transform;
}

/* 轻微阶梯延时：末尾靠后的卡片稍晚出现，营造自然瀑布感 */
.lgv-item.lgv-enter-active:nth-last-child(1) { transition-delay: 24ms; }
.lgv-item.lgv-enter-active:nth-last-child(2) { transition-delay: 48ms; }
.lgv-item.lgv-enter-active:nth-last-child(3) { transition-delay: 72ms; }

/* sheen 动画已移除 */
/* 骨架屏（高端微光） */
.lgv-skel .sk-media {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: var(--st-radius-md);
  border: 1px solid rgba(var(--st-border), 0.7);
  background:
    linear-gradient(90deg,
      rgba(var(--st-surface-2), 0.6) 0%,
      rgba(var(--st-surface-2), 0.85) 20%,
      rgba(var(--st-surface-2), 0.6) 40%);
  background-size: 200% 100%;
  animation: lgv-shimmer 1.4s ease-in-out infinite;
  margin-bottom: 12px;
}
.lgv-skel .sk-row {
  height: 16px;
  border-radius: 8px;
  background:
    linear-gradient(90deg,
      rgba(var(--st-surface-2), 0.6) 0%,
      rgba(var(--st-surface-2), 0.85) 20%,
      rgba(var(--st-surface-2), 0.6) 40%);
  background-size: 200% 100%;
  animation: lgv-shimmer 1.4s ease-in-out infinite;
  margin: 8px 0;
}
.lgv-skel .sk-row.w-44 { width: 176px; }
.lgv-skel .sk-row.w-56 { width: 224px; }
.lgv-skel .sk-row.w-72 { width: 288px; }
@media (max-width: 480px) {
  .lgv-skel .sk-row.w-44 { width: 52vw; }
  .lgv-skel .sk-row.w-56 { width: 62vw; }
  .lgv-skel .sk-row.w-72 { width: 78vw; }
}
@keyframes lgv-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 可访问性焦点与按压反馈 */
.btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(var(--st-primary), 0.18);
  border-color: rgba(var(--st-primary), 0.6);
}
.btn:active {
  transform: translateY(0);
}

.lgv-card-actions {
  display: flex;
  flex-direction: column; /* 垂直排列按钮 */
  gap: 12px; /* 增大按钮间距 */
  align-items: stretch; /* 按钮等宽 */
  justify-content: center; /* 垂直居中 */
  flex-shrink: 0;
  min-width: 120px; /* 按钮最小宽度 */
}
.lgv-card-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
.lgv-file {
  font-weight: 700;
  font-size: 18px; /* 增大标题字体 */
  color: rgb(var(--st-color-text));
}
.lgv-file-path {
  color: rgba(var(--st-color-text), 0.6);
  font-family: var(--st-font-mono);
  font-size: 13px; /* 略微增大路径字体 */
}

/* 描述 */
.lgv-desc {
  color: rgba(var(--st-color-text), 0.9);
  font-size: 15px; /* 增大描述字体 */
  line-height: 1.6;
}

/* 最新消息 */
.lgv-latest {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-top: 1px solid rgba(var(--st-border), 0.35);
  padding-top: 8px;
}
.lgv-latest .latest-meta {
  display: inline-flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 9999px;
  font-size: 12px;
  color: rgb(var(--st-color-text));
  background: rgba(var(--st-primary), 0.12);
  border: 1px solid rgba(var(--st-primary), 0.32);
}
.dim { color: rgba(var(--st-color-text), 0.85); font-size: 12px; font-weight: 600; }
.muted { color: rgba(var(--st-color-text), 0.65); font-size: 13px; }
.lgv-latest .latest-content {
  color: rgba(var(--st-color-text), 0.95);
  font-size: 15px; /* 增大最新消息字体 */
  line-height: 1.7;
  font-style: italic;
}
.lgv-latest.error {
  border-color: rgba(220, 38, 38, 0.45);
}
.err-badge {
  display: inline-flex; align-items: center; justify-content: center;
  height: 22px; padding: 0 8px; border-radius: 9999px;
  font-size: 12px; color: rgb(220,38,38);
  background: rgba(220,38,38,0.08); border: 1px solid rgba(220,38,38,0.45);
}
.err-detail { color: rgb(220,38,38); font-size: 12px; }

/* 空状态 */
.lgv-empty {
  grid-column: 1 / -1;
  display: grid;
  place-items: center;
  gap: 8px;
  padding: 60px 20px;
}
.empty-icon { font-size: 48px; opacity: 0.6; }
.empty-text { font-weight: 700; color: rgba(var(--st-color-text), 0.9); }

@keyframes st-spin { to { transform: rotate(360deg); } }
</style>
