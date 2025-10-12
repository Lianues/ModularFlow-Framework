<script setup>
import { ref, computed, watch } from 'vue'
import DataCatalog from '@/services/dataCatalog'
import ChatBranches from '@/services/chatBranches'

const props = defineProps({
  anchorLeft: { type: Number, default: 308 },
  width: { type: Number, default: 560 },
  zIndex: { type: Number, default: 59 },
  top: { type: Number, default: 64 },
  bottom: { type: Number, default: 12 },
  title: { type: String, default: '正则 Regex Rules' },
  conversationFile: { type: String, default: null },
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

const loading = ref(false)
const error = ref(null)
const usingKeys = ref([]) // 多选：使用数组
const regexRules = ref([])
const settingsLoaded = ref(false)

async function loadData() {
  if (settingsLoaded.value) return
  
  loading.value = true
  error.value = null
  
  try {
    const promises = [DataCatalog.listRegexRules()]
    
    if (props.conversationFile) {
      promises.push(
        ChatBranches.settings({
          action: 'get',
          file: props.conversationFile
        })
      )
    }
    
    const results = await Promise.all(promises)
    const listRes = results[0]
    const settingsRes = results[1]
    
    regexRules.value = DataCatalog.mapToCards(listRes?.items || [], 'regex_rules')
    
    // regex_rules是数组字段（多选）
    if (Array.isArray(settingsRes?.settings?.regex_rules)) {
      usingKeys.value = settingsRes.settings.regex_rules
    }
    
    settingsLoaded.value = true
  } catch (e) {
    error.value = e?.message || String(e)
  } finally {
    loading.value = false
    setTimeout(() => {
      try { window?.lucide?.createIcons?.() } catch (_) {}
    }, 50)
  }
}

watch(() => props.conversationFile, (v) => {
  if (v && !settingsLoaded.value) {
    loadData()
  }
}, { immediate: true })

function close(){ emit('close') }

// 多选逻辑：切换选中状态
async function onUse(k) {
  if (!props.conversationFile) {
    const idx = usingKeys.value.indexOf(k)
    if (idx >= 0) {
      usingKeys.value.splice(idx, 1)
    } else {
      usingKeys.value.push(k)
    }
    emit('use', k)
    return
  }
  
  try {
    const newKeys = [...usingKeys.value]
    const idx = newKeys.indexOf(k)
    if (idx >= 0) {
      newKeys.splice(idx, 1)
    } else {
      newKeys.push(k)
    }
    
    await ChatBranches.settings({
      action: 'update',
      file: props.conversationFile,
      patch: { regex_rules: newKeys }
    })
    usingKeys.value = newKeys
    emit('use', k)
  } catch (e) {
    error.value = e?.message || '更新失败'
  }
}

function onView(k){ emit('view', k) }
function onDelete(k){ emit('delete', k) }
const isLucide = (v) => typeof v === 'string' && /^[a-z\-]+$/.test(v)

// 辅助：检查是否选中
const isUsing = (k) => usingKeys.value.includes(k)
</script>

<template>
  <div
    data-scope="regex-view"
    class="rg-panel glass"
    :style="panelStyle"
  >
      <header class="rg-header">
        <div class="rg-title">
          <span class="rg-icon"><i data-lucide="scan-text"></i></span>
          {{ props.title }}
        </div>
        <button class="rg-close" type="button" title="关闭" @click="close">✕</button>
      </header>

      <CustomScrollbar class="rg-body">
        <div v-if="loading" class="rg-loading">加载中...</div>
        <div v-else-if="error" class="rg-error">加载失败：{{ error }}</div>
        <div v-else class="rg-list">
          <div
            v-for="it in regexRules"
            :key="it.key"
            class="rg-card"
          >
            <div class="rg-main">
              <div class="rg-avatar">
                <i v-if="isLucide(it.icon)" :data-lucide="it.icon"></i>
                <span v-else>{{ it.icon }}</span>
              </div>
              <div class="rg-texts">
                <div class="rg-name">{{ it.name }}</div>
                <div class="rg-desc">{{ it.desc }}</div>
              </div>
            </div>
            <div class="rg-actions">
              <button
                class="rg-btn"
                :class="{ active: isUsing(it.key) }"
                type="button"
                @click="onUse(it.key)"
                :aria-pressed="isUsing(it.key)"
              >{{ isUsing(it.key) ? '使用中' : '使用' }}</button>

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
  background: rgb(var(--st-surface));
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
.rg-icon i { width: 18px; height: 18px; display: inline-block; }
.rg-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), background .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
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
  gap: 12px;
}

/* Card */
.rg-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: stretch;
  border: 1px solid rgb(var(--st-border));
  border-radius: var(--st-radius-md);
  background: rgb(var(--st-surface));
  padding: 12px;
  transition: background .2s cubic-bezier(.22,.61,.36,1), border-color .2s cubic-bezier(.22,.61,.36,1), transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
.rg-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

/* Left main */
.rg-main {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: center;
}
.rg-avatar {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: linear-gradient(135deg, rgba(var(--st-primary),0.12), rgba(var(--st-accent),0.12));
  border: 1px solid rgba(var(--st-border), 0.9);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.25);
}
.rg-avatar i { width: 18px; height: 18px; display: inline-block; }
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
  gap: 8px;
  justify-content: center;
}
.rg-btn {
  appearance: none;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1), background .2s cubic-bezier(.22,.61,.36,1), border-color .2s cubic-bezier(.22,.61,.36,1);
  min-width: 64px;
  text-align: center;
}
.rg-btn:focus-visible,
.rg-close:focus-visible {
  outline: 2px solid rgba(var(--st-primary), 0.6);
  outline-offset: 2px;
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

/* States */
.rg-loading,
.rg-error {
  padding: 12px;
  font-size: 13px;
  color: rgba(var(--st-color-text), 0.8);
}
.rg-error { color: rgb(220, 38, 38); }

@media (max-width: 640px) {
  .rg-card { grid-template-columns: 1fr; }
  .rg-actions { flex-direction: row; }
}
</style>