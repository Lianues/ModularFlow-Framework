<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import SidebarNav from '@/components/sidebar/SidebarNav.vue'
import ThemeSwitch from '@/components/common/ThemeSwitch.vue'
import ModeSwitch from '@/components/common/ModeSwitch.vue'
import ThreadedChatPreview from '@/components/chat/ThreadedChatPreview.vue'
import { watch } from 'vue'
import SidebarDrawer from '@/components/sidebar/SidebarDrawer.vue'
import AppearancePanel from '@/components/sidebar/AppearancePanel.vue'
import AppSettingsPanel from '@/components/sidebar/AppSettingsPanel.vue'
import PresetsPanel from '@/components/sidebar/PresetsPanel.vue'
import WorldbookPanel from '@/components/sidebar/WorldbookPanel.vue'
import CharactersPanel from '@/components/sidebar/CharactersPanel.vue'
import PersonaPanel from '@/components/sidebar/PersonaPanel.vue'
import RegexPanel from '@/components/sidebar/RegexPanel.vue'
import ContentViewModal from '@/components/common/ContentViewModal.vue'
import PresetDetailView from '@/components/content/PresetDetailView.vue'

/**
 * 单一路径（/）下的多视图切换
 * - start：开始页（不显示侧边栏）
 * - threaded：对话楼层预览（显示侧边栏）
 * - sandbox：全局沙盒占位（显示侧边栏）
 * 解耦策略：
 * - 将侧边栏的显示与否与视图状态解耦，仅关心布尔：showSidebar
 * - 侧边栏每个项拆分在 SidebarNav 子组件中，避免臃肿
 * - 模式切换抽象为 ModeSwitch 组件（后续可独立成文件）
 */
const view = ref('start')
const showSidebar = computed(() => view.value !== 'start')
const drawerOpen = ref(false)
const appearanceOpen = ref(false)
const appSettingsOpen = ref(false)
const presetsOpen = ref(false)
const worldbookOpen = ref(false)
const charactersOpen = ref(false)
const personaOpen = ref(false)
const regexOpen = ref(false)

// 内容查看模态框
const viewModalOpen = ref(false)
const viewModalTitle = ref('')
const viewModalType = ref('') // 'preset', 'regex', 'worldbook', etc.
const viewModalData = ref(null)

function openViewModal(type, title, data) {
  viewModalType.value = type
  viewModalTitle.value = title
  viewModalData.value = data
  viewModalOpen.value = true
}

function closeViewModal() {
  viewModalOpen.value = false
  viewModalType.value = ''
  viewModalTitle.value = ''
  viewModalData.value = null
}

// 当侧边栏抽屉关闭时，同步关闭右侧“应用设置”面板，保持同层同生命周期
watch(drawerOpen, (v) => {
  if (!v) {
    appearanceOpen.value = false
    appSettingsOpen.value = false
    presetsOpen.value = false
    worldbookOpen.value = false
    charactersOpen.value = false
    personaOpen.value = false
    regexOpen.value = false
  }
})

// 楼层对话演示消息（占位）
const messages = reactive([
  { id: 1, role: 'system', content: '欢迎来到 SmartTavern。' },
  { id: 2, role: 'user', content: '你好，介绍一下你自己？' },
  { id: 3, role: 'assistant', content: '我是一个对话助手，帮助你完成任务。' },
  { id: 4, role: 'user', content: '你能做什么？' },
  { id: 5, role: 'assistant', content: '我可以回答问题、提供建议、帮助你完成各种任务。无论是写作、编程还是日常对话，我都能提供帮助。' },
  { id: 6, role: 'user', content: '那很好！' },
  { id: 7, role: 'assistant', content: '谢谢！有什么我可以帮助你的吗？' },
  { id: 8, role: 'user', content: '我想了解一下这个应用的特点。' },
  { id: 9, role: 'assistant', content: '这个应用具有以下特点：\n\n1. 解耦架构设计\n2. 可自定义主题\n3. 支持多种显示模式\n4. 响应式设计\n5. 美观的UI界面' },
  { id: 10, role: 'user', content: '听起来不错！' },
])

/**
 * ThemeSwitch：UI 表层的明/暗主题切换（后续可挂接到 settings store）
 * - 通过 data-theme 属性切换 CSS Variables
 */
const theme = ref('system')
function applyTheme(t) {
  const root = document.documentElement
  if (t === 'dark') {
    root.setAttribute('data-theme', 'dark')
  } else if (t === 'light') {
    root.setAttribute('data-theme', 'light')
  } else {
    root.removeAttribute('data-theme')
  }
}
onMounted(() => applyTheme(theme.value))
function onThemeUpdate(t) {
  theme.value = t
  applyTheme(t)
}

/**
 * ModeSwitch：在聊天页面内部切换（对话楼层 / 全局沙盒占位）
 */
// ModeSwitch moved to src/components/common/ModeSwitch.vue
</script>

<template>
  <div data-scope="app-shell" class="st-app-shell">
    <!-- 背景层（渐变 + 噪点） -->
    <div class="st-bg">
      <div class="st-gradient" />
      <div class="st-noise" />
    </div>

    <!-- 顶部栏（玻璃拟态） -->
    <header class="st-header glass">
      <div class="st-left">
        <button class="st-brand" @click="view = 'start'">
          <span class="st-logo">∞</span>
          SmartTavern
        </button>
        <ModeSwitch
          v-if="showSidebar"
          v-model:modelValue="view"
          class="st-mode-switch"
        />
      </div>
      <div class="st-actions-top">
        <ThemeSwitch :theme="theme" @update:theme="onThemeUpdate" />
      </div>
    </header>

    <!-- 主体 -->
    <div class="st-body">
      <!-- 侧边栏（仅聊天视图显示） -->
      <SidebarDrawer v-if="showSidebar" v-model="drawerOpen">
        <SidebarNav
          @openAppearance="(appearanceOpen = !appearanceOpen, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false)"
          @openAppSettings="(appSettingsOpen = !appSettingsOpen, appearanceOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false)"
          @openPresets="(presetsOpen = !presetsOpen, appearanceOpen = false, appSettingsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false)"
          @openWorldbook="(worldbookOpen = !worldbookOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false)"
          @openCharacters="(charactersOpen = !charactersOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, personaOpen = false, regexOpen = false)"
          @openPersona="(personaOpen = !personaOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, regexOpen = false)"
          @openRegex="(regexOpen = !regexOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false)"
        />
      </SidebarDrawer>

      <!-- 外观面板：与侧边栏同层，位于高斯模糊之上 -->
      <transition name="st-subpage">
        <AppearancePanel
          v-if="showSidebar && appearanceOpen"
          @close="appearanceOpen = false"
        />
      </transition>

      <!-- 应用设置面板：独立于外观面板 -->
      <transition name="st-subpage">
        <AppSettingsPanel
          v-if="showSidebar && appSettingsOpen"
          @close="appSettingsOpen = false"
        />
      </transition>

      <!-- 预设面板：模仿外观面板的弹出与定位（同层/同位置/同过渡） -->
      <transition name="st-subpage">
        <PresetsPanel
          v-if="showSidebar && presetsOpen"
          @close="presetsOpen = false"
          @view="(key) => openViewModal('preset', '预设详情 - ' + key, null)"
        />
      </transition>

      <!-- 世界书面板：同层/同位置/同过渡 -->
      <transition name="st-subpage">
        <WorldbookPanel
          v-if="showSidebar && worldbookOpen"
          @close="worldbookOpen = false"
        />
      </transition>

      <!-- 角色卡面板：同层/同位置/同过渡 -->
      <transition name="st-subpage">
        <CharactersPanel
          v-if="showSidebar && charactersOpen"
          @close="charactersOpen = false"
        />
      </transition>

      <!-- 用户信息面板：同层/同位置/同过渡 -->
      <transition name="st-subpage">
        <PersonaPanel
          v-if="showSidebar && personaOpen"
          @close="personaOpen = false"
        />
      </transition>

      <!-- 正则面板：同层/同位置/同过渡 -->
      <transition name="st-subpage">
        <RegexPanel
          v-if="showSidebar && regexOpen"
          @close="regexOpen = false"
          @view="(key) => openViewModal('regex', '正则规则详情 - ' + key, null)"
        />
      </transition>

      <!-- 主内容 -->
      <main data-scope="main" class="st-main">
        <!-- 开始视图（无侧边栏） -->
        <section v-if="view === 'start'" data-scope="start-view" class="st-start">
          <div class="st-hero glass">
            <h1 class="st-title">欢迎使用 SmartTavern</h1>
            <p class="st-desc">一个可对话、可美化、可扩展的前端应用。</p>
            <div class="st-cta">
              <button class="st-btn st-primary" @click="view = 'threaded'">开始聊天（对话楼层）</button>
              <button class="st-btn" @click="view = 'sandbox'">全局沙盒（占位）</button>
            </div>
          </div>

          <div class="st-features">
            <div class="st-feature card">
              <div class="st-feature-icon">🎯</div>
              <div class="st-feature-title">解耦架构</div>
              <div class="st-feature-desc">表现/逻辑/样式分离，主题与布局可热插拔。</div>
            </div>
            <div class="st-feature card">
              <div class="st-feature-icon">🎨</div>
              <div class="st-feature-title">主题 2.0</div>
              <div class="st-feature-desc">单文件主题包 + 受控 JS 扩展，安全且强大。</div>
            </div>
            <div class="st-feature card">
              <div class="st-feature-icon">⚡</div>
              <div class="st-feature-title">静态发布</div>
              <div class="st-feature-desc">编译产物可直接部署，运行时加载主题与配置。</div>
            </div>
          </div>
        </section>

        <!-- 楼层对话独立视图 -->
        <section v-else-if="view === 'threaded'" data-scope="chat-threaded" class="st-threaded">
          <ThreadedChatPreview :messages="messages" />
        </section>

        <!-- 全局沙盒独立视图 -->
        <section v-else data-scope="chat-sandbox" class="st-sandbox">
          <div class="st-sandbox-stage">
            <div class="st-sandbox-content">
              <div class="st-sandbox-header">
                <h2 class="st-sandbox-title">🎬 沙盒舞台预览</h2>
                <p class="st-sandbox-desc">可在侧栏"外观 → 全屏沙盒设定"中调节舞台尺寸、比例与样式</p>
              </div>
              <div class="st-sandbox-body">
                <div class="st-sandbox-demo-box">
                  <div class="st-demo-icon">🎯</div>
                  <div class="st-demo-text">拖拽"舞台最大宽度"滑条<br/>可看到此区域横向缩放</div>
                </div>
                <div class="st-sandbox-demo-box">
                  <div class="st-demo-icon">📐</div>
                  <div class="st-demo-text">调节"画面宽高比"<br/>可改变舞台的长宽比例</div>
                </div>
                <div class="st-sandbox-demo-box">
                  <div class="st-demo-icon">📏</div>
                  <div class="st-demo-text">调节"舞台内边距"<br/>可改变内容与边界的距离</div>
                </div>
                <div class="st-sandbox-demo-box">
                  <div class="st-demo-icon">✨</div>
                  <div class="st-demo-text">调节"舞台圆角"<br/>可看到四角的圆润程度</div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>

    <!-- 内容查看模态框 -->
    <ContentViewModal
      v-model:show="viewModalOpen"
      :title="viewModalTitle"
      @close="closeViewModal"
    >
      <PresetDetailView
        v-if="viewModalType === 'preset'"
      />
      <div v-else-if="viewModalType === 'regex'" class="modal-placeholder">
        <div class="placeholder-icon">🧹</div>
        <div class="placeholder-text">正则规则详细视图</div>
        <div class="placeholder-desc">此视图待后续开发</div>
      </div>
      <div v-else class="modal-placeholder">
        <div class="placeholder-icon">📋</div>
        <div class="placeholder-text">内容查看</div>
        <div class="placeholder-desc">视图类型：{{ viewModalType }}</div>
      </div>
    </ContentViewModal>
  </div>
</template>

<!-- 全局：设计令牌 + 主题（不加 scoped，供全局使用） -->
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  /* 基础语义令牌（RGB 形式，便于调优） */
  --st-color-bg: 246 248 253;
  --st-color-text: 18 24 38;
  --st-surface: 255 255 255;
  --st-surface-2: 248 249 255;
  --st-primary: 88 80 236;
  --st-primary-contrast: 255 255 255;
  --st-border: 225 228 236;
  --st-accent: 14 165 233;

  --st-radius-sm: 10px;
  --st-radius-md: 14px;
  --st-radius-lg: 18px;

  --st-shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
  --st-shadow-md: 0 8px 30px rgba(0,0,0,0.06);
  --st-shadow-lg: 0 12px 45px rgba(0,0,0,0.1);

  /* 背景图 Hook（可被主题覆盖） */
  --st-surface-bg-image: none;
  --st-surface-bg-size: cover;
  --st-surface-bg-position: center center;
  --st-surface-bg-repeat: no-repeat;

  /* 页面背景图（可被外观面板覆盖） */
  --st-bg-start: url('/images/HomePage.png');
  --st-bg-threaded: url('/images/ThreadedChat.png');
  --st-bg-sandbox: url('/images/SandboxChat.png');

  --st-font-body: 'Inter', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji';
  --st-font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;

  /* Chat tuning defaults */
  --st-content-font-size: 18px; /* 正文文字大小 */
  --st-name-font-size: 16px; /* 角色名称文字大小 */
  --st-badge-font-size: 11px; /* 角色徽章文字大小 */
  --st-floor-font-size: 16px; /* 楼层号文字大小 */
  --st-avatar-size: 56px; /* 角色头像大小 */
  --st-chat-width: 80%; /* 百分比宽度 */
  --st-input-height: 100px; /* 输入框高度 */

  /* Sandbox layout controls */
  --st-sandbox-max-width: 1100px;  /* 舞台最大宽度 */
  --st-sandbox-aspect: 16 / 9;     /* 舞台宽高比（CSS aspect-ratio） */
  --st-sandbox-padding: 16px;      /* 舞台内边距 */
  --st-sandbox-radius: 18px;       /* 舞台圆角 */
}

/* 暗色主题 */
[data-theme="dark"] {
  --st-color-bg: 14 17 22;
  --st-color-text: 232 236 244;
  --st-surface: 23 27 36;
  --st-surface-2: 28 34 45;
  --st-primary: 129 140 248;
  --st-primary-contrast: 19 23 32;
  --st-border: 45 54 70;
  --st-accent: 94 234 212;
}

/* 页面背景 */
body[data-app="smarttavern"] {
  margin: 0;
  font-family: var(--st-font-body);
  color: rgb(var(--st-color-text));
  background-color: rgb(var(--st-color-bg));
  background-image: var(--st-surface-bg-image);
  background-size: var(--st-surface-bg-size);
  background-position: var(--st-surface-bg-position);
  background-repeat: var(--st-surface-bg-repeat);
}

* { box-sizing: border-box; }

/* Live tuning: elegantly minimize left sidebar (animated) */
/* Prepare transitions on drawer/backdrop for smooth state changes */
.sd-drawer,
.sd-backdrop {
  transition: opacity .28s cubic-bezier(.4, .14, .3, 1),
              transform .32s cubic-bezier(.22,.61,.36,1),
              filter .32s ease,
              box-shadow .28s ease,
              backdrop-filter .32s ease;
  will-change: opacity, transform, filter;
}

/* During live tuning, fade/blur/slide the drawer out instead of hard hiding */
body.st-live-tuning .sd-backdrop {
  opacity: 0;
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
  pointer-events: none;
}

body.st-live-tuning .sd-drawer {
  opacity: 0;
  transform: translateX(-18px) scale(0.985);
  filter: blur(8px) saturate(60%);
  box-shadow: none;
  pointer-events: none;
}

/* Hide all text elements but keep layout space to prevent position shift */
body.st-live-tuning [data-scope="settings-view"] .st-settings-header,
body.st-live-tuning [data-scope="settings-view"] .st-settings-tabs,
body.st-live-tuning [data-scope="settings-view"] .muted,
body.st-live-tuning [data-scope="settings-view"] h3 {
  visibility: hidden !important;
}


/* Make panel completely transparent - override glass class */
body.st-live-tuning [data-scope="settings-view"].glass,
body.st-live-tuning [data-scope="settings-view"] .glass,
body.st-live-tuning [data-scope="settings-view"] .st-settings {
  background: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: 0 !important;
  box-shadow: none !important;
}

body.st-live-tuning [data-scope="settings-view"] .st-settings-body {
  background: transparent !important;
}

/* Hide all sliders and their labels by default */
body.st-live-tuning [data-scope="settings-view"] .st-control {
  visibility: hidden !important;
}

/* Show only the active slider (including its label, value, and range input) */
body.st-live-tuning[data-active-slider="contentFontSize"] [data-scope="settings-view"] .st-control[data-slider="contentFontSize"],
body.st-live-tuning[data-active-slider="nameFontSize"] [data-scope="settings-view"] .st-control[data-slider="nameFontSize"],
body.st-live-tuning[data-active-slider="badgeFontSize"] [data-scope="settings-view"] .st-control[data-slider="badgeFontSize"],
body.st-live-tuning[data-active-slider="floorFontSize"] [data-scope="settings-view"] .st-control[data-slider="floorFontSize"],
body.st-live-tuning[data-active-slider="avatarSize"] [data-scope="settings-view"] .st-control[data-slider="avatarSize"],
body.st-live-tuning[data-active-slider="chatWidth"] [data-scope="settings-view"] .st-control[data-slider="chatWidth"],
body.st-live-tuning[data-active-slider="inputHeight"] [data-scope="settings-view"] .st-control[data-slider="inputHeight"],
body.st-live-tuning[data-active-slider="sandboxMaxWidth"] [data-scope="settings-view"] .st-control[data-slider="sandboxMaxWidth"],
body.st-live-tuning[data-active-slider="sandboxPadding"] [data-scope="settings-view"] .st-control[data-slider="sandboxPadding"],
body.st-live-tuning[data-active-slider="sandboxRadius"] [data-scope="settings-view"] .st-control[data-slider="sandboxRadius"] {
  visibility: visible !important;
}
</style>

<!-- 局部样式（scoped） -->
<style scoped>
/* 背景层 */
.st-bg {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
}
.st-gradient {
  position: absolute; inset: -10%;
  background:
    radial-gradient(800px 500px at 20% 10%, rgba(129,140,248,0.22), transparent 60%),
    radial-gradient(800px 500px at 80% 10%, rgba(56,189,248,0.18), transparent 60%),
    radial-gradient(800px 500px at 50% 90%, rgba(52,211,153,0.18), transparent 60%);
  filter: blur(40px);
}
.st-noise {
  position: absolute; inset: 0; background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" opacity="0.045"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(%23n)"/></svg>');
  background-size: cover;
}

/* 玻璃拟态与卡片 */
.glass {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: saturate(140%) blur(10px);
  -webkit-backdrop-filter: saturate(140%) blur(10px);
  border: 1px solid rgba(var(--st-border), 0.7);
  box-shadow: var(--st-shadow-sm);
}
[data-theme="dark"] .glass {
  background: rgba(26, 31, 43, 0.55);
}

.card {
  background: rgb(var(--st-surface));
  border: 1px solid rgb(var(--st-border));
  border-radius: var(--st-radius-lg);
  box-shadow: var(--st-shadow-md);
}

/* 布局 */
.st-app-shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.st-header {
  position: sticky; top: 0; z-index: 5;
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px;
}
.st-logo { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 8px;
  background: linear-gradient(135deg, rgba(var(--st-primary),1), rgba(var(--st-accent),1)); color: #fff; margin-right: 10px; font-weight: 700; }
.st-brand {
  display: inline-flex; align-items: center;
  gap: 12px; font-weight: 700; font-size: 16px;
  background: transparent; border: none; color: rgb(var(--st-color-text)); cursor: pointer;
}
.st-actions-top { display: flex; align-items: center; gap: 8px; }
.st-left { display: inline-flex; align-items: center; gap: 12px; }

.st-body {
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}
.st-sidebar {
  width: 320px; padding: 14px; border-radius: var(--st-radius-lg);
  align-self: stretch; overflow: auto;
}
.st-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 开始视图（Hero） */
.st-start {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 16px;
  align-items: start;
  overflow-y: auto;
  height: 100%;
  position: relative;
}
.st-start::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: var(--st-bg-start);
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  opacity: 0.15;
  z-index: -1;
  pointer-events: none;
}
@media (max-width: 980px) { .st-start { grid-template-columns: 1fr; } }

.st-hero {
  padding: 24px; border-radius: var(--st-radius-lg);
  box-shadow: var(--st-shadow-lg);
}
.st-title { margin: 0 0 6px; font-size: 24px; font-weight: 700; }
.st-desc { margin: 0 0 12px; color: rgba(var(--st-color-text), 0.75); }
.st-cta { display: flex; gap: 12px; margin-top: 6px; }
.st-btn {
  appearance: none; border: 1px solid rgb(var(--st-border)); background: rgb(var(--st-surface));
  padding: 10px 14px; border-radius: var(--st-radius-md); cursor: pointer; color: rgb(var(--st-color-text));
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
}
.st-btn:hover { transform: translateY(-1px); box-shadow: var(--st-shadow-md); }
.st-btn.st-primary { background: linear-gradient(135deg, rgba(var(--st-primary),1), rgba(var(--st-accent),1)); color: var(--st-primary-contrast); border-color: transparent; }
.st-btn.st-primary:hover { filter: saturate(1.05); }

.st-features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 980px) { .st-features { grid-template-columns: 1fr; } }
.st-feature { padding: 18px; border-radius: var(--st-radius-lg); }
.st-feature-icon { font-size: 20px; }
.st-feature-title { margin-top: 8px; font-weight: 600; }
.st-feature-desc { margin-top: 4px; color: rgba(var(--st-color-text), 0.7); }

/* Threaded chat container */
.st-threaded {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: var(--st-chat-width, 860px);
  margin: 0 auto;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  position: relative;
}
.st-threaded::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: var(--st-bg-threaded);
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  opacity: 0.12;
  z-index: -1;
  pointer-events: none;
}

/* Sandbox container */
.st-sandbox {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0 auto;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  position: relative;
}
.st-sandbox::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: var(--st-bg-sandbox);
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  opacity: 0.12;
  z-index: -1;
  pointer-events: none;
}

/* Sandbox stage: 控制舞台尺寸与比例 */
.st-sandbox-stage {
  position: relative;
  width: 100%;
  max-width: var(--st-sandbox-max-width);
  margin: 0 auto;
  aspect-ratio: var(--st-sandbox-aspect);
  padding: var(--st-sandbox-padding);
  border-radius: var(--st-sandbox-radius);
  /* 舞台可见边界：淡色边框 + 半透明背景 */
  border: 2px solid rgba(var(--st-primary), 0.25);
  background: rgba(var(--st-surface), 0.4);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  overflow: hidden;
}

/* Sandbox content layout */
.st-sandbox-content {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 1;
}

.st-sandbox-header {
  text-align: center;
  padding: 12px;
}

.st-sandbox-title {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}

.st-sandbox-desc {
  margin: 0;
  font-size: 13px;
  color: rgba(var(--st-color-text), 0.7);
}

.st-sandbox-body {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 0 12px 12px;
}

.st-sandbox-demo-box {
  background: rgba(var(--st-surface), 0.6);
  border: 1px solid rgba(var(--st-border), 0.6);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.st-sandbox-demo-box:hover {
  transform: translateY(-2px);
  box-shadow: var(--st-shadow-sm);
}

.st-demo-icon {
  font-size: 28px;
}

.st-demo-text {
  font-size: 12px;
  line-height: 1.4;
  color: rgba(var(--st-color-text), 0.8);
}

/* ModeSwitch styles moved into src/components/common/ModeSwitch.vue */
/* Threaded chat preview styles moved into src/components/chat/ThreadedChatPreview.vue */

/* 子页面展开/收起动画（AppearancePanel 组件在 App 层的过渡） */
.st-subpage-enter-from { opacity: 0; transform: translateX(-10px) scale(0.98); filter: blur(4px); }
.st-subpage-leave-to   { opacity: 0; transform: translateX(-12px) scale(0.98); filter: blur(4px); }
.st-subpage-enter-active,
.st-subpage-leave-active { transition: opacity .2s ease, transform .24s cubic-bezier(.22,.61,.36,1), filter .24s ease; }

/* 模态框占位符样式 */
.modal-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  text-align: center;
}

.placeholder-icon {
  font-size: 64px;
  opacity: 0.6;
}

.placeholder-text {
  font-size: 20px;
  font-weight: 600;
  color: rgb(var(--st-color-text));
}

.placeholder-desc {
  font-size: 14px;
  color: rgba(var(--st-color-text), 0.65);
}
</style>
