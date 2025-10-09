<script setup>
import { ref, computed, onMounted, nextTick } from "vue"
onMounted(() => window.lucide?.createIcons?.())

const search = ref("")

const saves = ref([
  { id: "slot-1", name: "沙盒调试会话", desc: "用于测试楼层渲染与分支", character: "许莲笙", latest: "好的，我来尝试说明一下……", updatedAt: "2025-01-01 12:00", cover: null },
  { id: "slot-2", name: "分支对话演示", desc: "演示多分支与回退", character: "心与露", latest: "我们刚刚说到，旅程的开端在清晨。", updatedAt: "2025-02-10 09:26", cover: null },
  { id: "slot-3", name: "世界书检验", desc: "校验关键词触发", character: "系统助手", latest: "触发关键字：神经接口。", updatedAt: "2025-03-08 19:40", cover: null },
])

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return saves.value
  return saves.value.filter(s =>
    [s.name, s.character, s.latest].some(x => String(x || "").toLowerCase().includes(q))
  )
})

function loadSave(id) {
  console.log("load save:", id)
}

function deleteSave(id) {
  if (!confirm("确认删除该存档？此操作不可撤销。")) return
  const i = saves.value.findIndex(s => s.id === id)
  if (i >= 0) saves.value.splice(i, 1)
  nextTick(() => window.lucide?.createIcons?.())
}
</script>

<template>
  <section class="saves-section">
    <div class="hm-title">
      <i data-lucide="history" class="icon-20" aria-hidden="true"></i>
      <h2>读取存档</h2>
    </div>
    <p class="hm-desc">支持通过关键字筛选，单击加载进入会话；可删除无用存档。</p>

    <div class="toolbar">
      <div class="searchbox">
        <i data-lucide="search" class="icon-16 search-icon" aria-hidden="true"></i>
        <input
          v-model="search"
          type="text"
          class="search-input"
          placeholder="搜索名称 / 角色卡 / 最新消息"
        />
      </div>
      <div class="result-chip">
        结果：{{ filtered.length }} 个
      </div>
    </div>

    <div class="saves-list">
      <div
        v-for="s in filtered"
        :key="s.id"
        class="save-item"
      >
        <div class="save-cover" :title="s.name">
          <div class="cover-box">
            <div class="cover-fallback">🖼️</div>
          </div>
        </div>

        <div class="save-main">
          <div class="save-title">
            <span class="save-name">{{ s.name }}</span>
            <span class="save-time">{{ s.updatedAt }}</span>
          </div>
          <div class="save-meta">
            <span class="chip">角色卡：{{ s.character }}</span>
          </div>
          <div class="save-latest" :title="s.latest">
            <span class="latest-label">最新消息：</span>
            <span class="latest-text">{{ s.latest }}</span>
          </div>
        </div>

        <div class="save-actions">
          <button class="btn btn-danger" type="button" @click="deleteSave(s.id)">
            <i data-lucide="trash-2" class="icon-16" aria-hidden="true"></i>
            <span>删除</span>
          </button>
          <button class="btn btn-primary" type="button" @click="loadSave(s.id)">
            <i data-lucide="play" class="icon-16" aria-hidden="true"></i>
            <span>加载</span>
          </button>
        </div>
      </div>

      <div v-if="filtered.length === 0" class="saves-empty">
        未找到匹配的存档
      </div>
    </div>
  </section>
</template>

<style scoped>
.hm-title { display: flex; align-items: center; gap: 10px; }
.hm-title .icon-20 { width: 20px; height: 20px; stroke: currentColor; color: rgb(var(--st-color-text)); }
.hm-title h2 { margin: 0; font-size: 18px; font-weight: 700; color: rgb(var(--st-color-text)); }
.hm-desc { margin: 0 0 8px; font-size: 12px; color: rgba(var(--st-color-text), 0.7); }

.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; margin: 8px 0 12px;
}
.searchbox {
  position: relative; flex: 1;
}
.search-icon {
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  color: rgba(var(--st-color-text), .6);
}
.search-input {
  width: 100%;
  padding: 10px 12px 10px 34px;
  border-radius: 10px;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface-2));
  color: rgb(var(--st-color-text));
  outline: none;
}
.search-input:focus {
  border-color: rgba(var(--st-primary), .55);
  box-shadow: 0 0 0 3px rgba(var(--st-primary), .12);
}
.result-chip {
  white-space: nowrap;
  font-size: 12px;
  color: rgba(var(--st-color-text), .7);
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  border-radius: 999px;
  padding: 6px 10px;
}

.saves-list { display: grid; gap: 12px; }

/* 单行卡片布局 */
.save-item {
  display: grid;
  grid-template-columns: var(--cover-w, 280px) 1fr auto;
  align-items: center;
  gap: 16px;
  padding: 14px;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  transition: transform .18s cubic-bezier(.22,.61,.36,1), box-shadow .18s, border-color .18s;
}
.save-item:hover { transform: translateY(-1px); box-shadow: var(--st-shadow-sm); border-color: rgba(var(--st-primary), .45); }

/* 左侧 16:9 头像/封面区域 */
.save-cover { line-height: 0; font-size: 0; }
.cover-box {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 10px;
  border: 1px solid rgba(var(--st-border), .9);
  background:
    linear-gradient(135deg, rgba(var(--st-primary), .12), rgba(var(--st-accent), .12)),
    repeating-conic-gradient(from 45deg, rgba(0,0,0,.05) 0 10deg, transparent 10deg 20deg);
  display: flex; align-items: center; justify-content: center;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.2);
  overflow: hidden;
}
.cover-fallback { font-size: 28px; opacity: .7; }

/* 中部信息区 */
.save-main { min-width: 0; display: grid; gap: 6px; }
.save-title { display: flex; align-items: baseline; gap: 10px; }
.save-name { font-weight: 800; color: rgb(var(--st-color-text)); font-size: 18px; }
.save-time { font-size: 12px; color: rgba(var(--st-color-text), .55); }

/* 角色卡：完全左对齐、无边框/背景、加粗文本 */
.save-meta { display: block; margin: 0; padding: 0; }
.chip {
  display: inline;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  font-weight: 700;
  font-size: 13px;
  color: rgb(var(--st-color-text));
}

/* 最新消息：与左侧紧贴、基线对齐、单行省略号、斜体 */
.save-latest { display: flex; align-items: baseline; gap: 6px; min-width: 0; margin: 0; padding: 0; }
.latest-label { font-size: 12px; color: rgba(var(--st-color-text), .6); border: 0; background: transparent; padding: 0; margin: 0; }
.latest-text { font-size: 12px; color: rgba(var(--st-color-text), .85); font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* 右侧行为区 */
.save-actions { display: grid; gap: 8px; }
.btn {
  appearance: none;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  border-radius: 8px; padding: 8px 12px; font-size: 12px; cursor: pointer;
  border: 1px solid rgb(var(--st-border)); background: rgb(var(--st-surface)); color: rgb(var(--st-color-text));
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease, background .15s ease;
  min-width: 86px;
}
.btn:hover { transform: translateY(-1px); box-shadow: var(--st-shadow-sm); border-color: rgba(var(--st-primary), .45); }
.btn-primary { border-color: rgba(var(--st-primary), .55); background: rgba(var(--st-primary), .08); }
.btn-primary:hover { background: rgba(var(--st-primary), .12); }
.btn-danger { border-color: rgba(220, 38, 38, .55); background: rgba(220, 38, 38, .06); }
.btn-danger:hover { background: rgba(220, 38, 38, .1); }

.saves-empty {
  text-align: center; padding: 24px 8px;
  font-size: 12px; color: rgba(var(--st-color-text), .6);
  border: 1px dashed rgba(var(--st-border), .9);
  border-radius: 10px; background: rgba(var(--st-surface), .6);
}

/* 深色主题细化 */
[data-theme="dark"] .search-input { background: rgb(var(--st-surface)); }
</style>
