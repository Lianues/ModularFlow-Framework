<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import SidebarNav from '@/components/sidebar/SidebarNav.vue'
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
import AIConfigPanel from '@/components/sidebar/AIConfigPanel.vue'
import ContentViewModal from '@/components/common/ContentViewModal.vue'
import PresetDetailView from '@/components/content/PresetDetailView.vue'
import WorldbookDetailView from '@/components/content/WorldbookDetailView.vue'
import CharacterDetailView from '@/components/content/CharacterDetailView.vue'
import PersonaDetailView from '@/components/content/PersonaDetailView.vue'
import RegexDetailView from '@/components/content/RegexDetailView.vue'
import SandboxStage from '@/components/sandbox/SandboxStage.vue'
import NewChatModal from '@/components/home/NewChatModal.vue'
import HomeMenu from '@/components/home/HomeMenu.vue'
import LoadGameModal from '@/components/home/LoadGameModal.vue'
import GalleryModal from '@/components/home/GalleryModal.vue'
import OptionsModal from '@/components/home/OptionsModal.vue'
import AppShell from '@/layouts/AppShell.vue'
import { useHomeMenuInk } from '@/composables/useHomeMenuInk'
import { useBackgroundFx } from '@/composables/useBackgroundFx'
import { useSidebar } from '@/composables/useSidebar.js'
import ThemeManager from '@/features/themes/manager'
import DataCatalog from '@/services/dataCatalog'

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
const { drawerOpen } = useSidebar()
const appearanceOpen = ref(false)
const appSettingsOpen = ref(false)
const presetsOpen = ref(false)
const worldbookOpen = ref(false)
const charactersOpen = ref(false)
const personaOpen = ref(false)
const regexOpen = ref(false)
const aiConfigOpen = ref(false)

const { updateHomeMenuInk } = useHomeMenuInk(() => view.value === 'start')
const { playHomeBgFX, playThreadedBgFX, playSandboxBgFX } = useBackgroundFx()

 // 内容查看模态框
const viewModalOpen = ref(false)
const viewModalTitle = ref('')
const viewModalType = ref('') // 'preset', 'regex', 'worldbook', etc.
const viewModalData = ref(null)
const viewModalLoading = ref(false)
const viewModalError = ref('')
const viewModalFile = ref('') // 详情对应的文件相对路径

// 当前使用的预设数据（用于AI配置面板的覆盖提示）
const currentPresetData = ref(null)

async function openViewModal(type, title, fileOrData) {
  viewModalType.value = type
  viewModalTitle.value = title
  viewModalError.value = ''
  viewModalLoading.value = true
  viewModalData.value = null
  // 先记录 file（如果传入的是字符串）
  viewModalFile.value = typeof fileOrData === 'string' ? fileOrData : ''
  viewModalOpen.value = true

  try {
    if (fileOrData && typeof fileOrData === 'object') {
      // 直接使用传入的数据（可能没有 file）
      viewModalData.value = fileOrData
    } else if (typeof fileOrData === 'string') {
      // 按类型调用后端详情接口，并写入缓存（由服务内部处理）
      const fetchers = {
        preset:    (f) => DataCatalog.getPresetDetail(f, { useCache: false, persist: false }),
        worldbook: (f) => DataCatalog.getWorldBookDetail(f, { useCache: false, persist: false }),
        character: (f) => DataCatalog.getCharacterDetail(f, { useCache: false, persist: false }),
        persona:   (f) => DataCatalog.getPersonaDetail(f, { useCache: false, persist: false }),
        regex:     (f) => DataCatalog.getRegexRuleDetail(f, { useCache: false, persist: false }),
      }
      const fn = fetchers[type]
      if (!fn) throw new Error(`未知类型: ${type}`)
      const res = await fn(fileOrData)
      // 后端结构为 { file, name, description, content }
      viewModalData.value = res && (res.content ?? res)
      if (res && typeof res.file === 'string') {
        viewModalFile.value = res.file
      }
      // 如果是预设类型，保存为当前预设数据（用于AI配置覆盖检测）
      if (type === 'preset' && res) {
        currentPresetData.value = res.content ?? res
      }
    } else {
      // 无文件参数时保持空（例如纯占位模式）
    }
  } catch (e) {
    viewModalError.value = e?.message || String(e)
  } finally {
    viewModalLoading.value = false
    nextTick(() => { window?.lucide?.createIcons?.() })
  }
}

function closeViewModal() {
  viewModalOpen.value = false
  viewModalType.value = ''
  viewModalTitle.value = ''
  viewModalData.value = null
  viewModalLoading.value = false
  viewModalError.value = ''
  viewModalFile.value = ''
}

// 主页功能模态（Load / Gallery / Options）
const homeModalOpen = ref(false)
const homeModalTitle = ref('')
const homeModalType = ref('') // 'load' | 'gallery' | 'options'

function openHomeModal(type) {
  homeModalType.value = type
  homeModalTitle.value =
    type === 'load' ? '读取存档'
    : type === 'gallery' ? '画廊'
    : type === 'options' ? '选项'
    : ' '
  homeModalOpen.value = true
  nextTick(() => {
    window?.lucide?.createIcons?.()
    if (typeof window.initFlowbite === 'function') {
      try { window.initFlowbite() } catch (_) {}
    }
  })
}

function closeHomeModal() {
  homeModalOpen.value = false
  homeModalType.value = ''
  homeModalTitle.value = ''
}

/* New Game 模态：新建对话（独立组件 NewChatModal 管理表单状态） */
const newGameOpen = ref(false)

function openNewGame() {
  newGameOpen.value = true
  nextTick(() => {
    window?.lucide?.createIcons?.()
    if (typeof window.initFlowbite === 'function') {
      try { window.initFlowbite() } catch (_) {}
    }
  })
}

function onNewChatConfirm(payload) {
  // TODO: 占位符 —— 后续在此与后端通信创建会话（携带所选项）
  // payload: { name, type, preset, character, persona, regex?, worldbook? }
  if (payload?.type === 'threaded' || payload?.type === 'sandbox') {
    view.value = payload.type
  }
  newGameOpen.value = false
  nextTick(() => { window?.lucide?.createIcons?.() })
}

function cancelNewGame() {
  newGameOpen.value = false
  nextTick(() => { window?.lucide?.createIcons?.() })
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
    aiConfigOpen.value = false
  }
})

/* 监听视图切换，start/threaded/sandbox 统一景深+焦点动画 */
watch(view, (v) => {
  document.body.dataset.home = (v === 'start' ? 'plain' : '')
  if (v === 'start') {
    nextTick(() => { updateHomeMenuInk(); playHomeBgFX() })
  } else if (v === 'threaded') {
    nextTick(() => { playThreadedBgFX() })
  } else if (v === 'sandbox') {
    nextTick(() => { playSandboxBgFX() })
  }
  if (v !== 'start') {
    // 离开主页时关闭主页相关模态
    homeModalOpen.value = false
    homeModalType.value = ''
    homeModalTitle.value = ''
  }
})

/* HomeMenu 智能前景色逻辑已抽离至 useHomeMenuInk 组合式 */

/* 背景动画逻辑已抽离至 useBackgroundFx 组合式 */



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
  { id: 11, role: 'assistant', content: '下面是一个内嵌演示网页，前后还有普通正文，便于比对。\n\n正文段落 A。\n\n```html\n<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>内嵌演示</title></head><body><h1 style="font-family:system-ui;margin:16px;">楼层内 Iframe 演示</h1><p style="margin:16px;">这是一段通过 iframe 渲染的 HTML。</p></body></html>\n```\n\n正文段落 B。' },
])

/**
 * ThemeSwitch：UI 表层的明/暗主题切换（后续可挂接到 settings store）
 * - 通过 data-theme 属性切换 CSS Variables
 */
const theme = ref('system')

// 初始化主题优先从 documentElement 或本地存储读取，避免深色主题白屏闪烁
try {
  const attrTheme = document?.documentElement?.getAttribute?.('data-theme')
  const savedTheme = localStorage.getItem('st.theme')
  const init = (attrTheme === 'dark' || attrTheme === 'light') ? attrTheme
             : (savedTheme === 'dark' || savedTheme === 'light' || savedTheme === 'system') ? savedTheme
             : 'system'
  if (init !== 'system') {
    theme.value = init
  }
} catch (_) {}

let __themeMql = null
let __onSchemeChange = null
function applyTheme(t) {
  const root = document.documentElement
  // detach previous system watcher if any
  if (__themeMql && t !== 'system' && __onSchemeChange) {
    try { __themeMql.removeEventListener('change', __onSchemeChange) } catch (_) {}
    __themeMql = null
  }
  if (t === 'dark' || t === 'light') {
    root.setAttribute('data-theme', t)
    return
  }
  // system: follow OS prefers-color-scheme (and react to changes)
  const mql = window.matchMedia?.('(prefers-color-scheme: dark)')
  const setByMql = (mq) => {
    try {
      root.setAttribute('data-theme', mq?.matches ? 'dark' : 'light')
    } catch (_) {}
  }
  setByMql(mql)
  if (mql) {
    __onSchemeChange = (e) => setByMql(e)
    try { mql.addEventListener('change', __onSchemeChange) } catch (_) {}
    __themeMql = mql
  }
}

// 动态注入 UI 库（Lucide 图标、Flowbite JS），并初始化图标
async function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve()
    const s = document.createElement('script')
    s.src = src
    s.async = true
    s.onload = () => resolve()
    s.onerror = (e) => reject(e)
    document.head.appendChild(s)
  })
}
async function ensureUIAssets() {
  try {
    await loadScript('https://unpkg.com/lucide@latest/dist/umd/lucide.min.js')
  } catch (_) {}
  try {
    await loadScript('https://cdn.jsdelivr.net/npm/flowbite@2.0.0/dist/flowbite.min.js')
  } catch (_) {}
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons()
  }
  // 初始化 Flowbite（如 Tooltip 等组件）
  if (typeof window.initFlowbite === 'function') {
    try { window.initFlowbite() } catch (_) {}
  }
}
function refreshIcons() {
  nextTick(() => {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons()
    }
    // 重新扫描并初始化 Flowbite 组件（确保动态节点生效）
    if (typeof window.initFlowbite === 'function') {
      try { window.initFlowbite() } catch (_) {}
    }
  })
}

onMounted(() => {
  applyTheme(theme.value)
  try { ThemeManager.setColorMode?.(theme.value) } catch (_) {}

  ensureUIAssets().finally(() => {
    try {
      if (view.value === 'start') {
        updateHomeMenuInk()
        playHomeBgFX()
      } else if (view.value === 'threaded') {
        playThreadedBgFX()
      } else if (view.value === 'sandbox') {
        playSandboxBgFX()
      }
    } catch (_) {}
  })
  // 主页（start-view）时让 body 完全透明，避免白色半透明底
  document.body.dataset.home = (view.value === 'start' ? 'plain' : '')
})

function onThemeUpdate(t) {
  theme.value = t
  applyTheme(t)
  try { ThemeManager.setColorMode?.(t) } catch (_) {}
  try { localStorage.setItem('st.theme', t) } catch (_) {}
  refreshIcons()
}

// 修复：通过显式方法更新 ref，避免模板内对 ref 直接赋值导致的响应性异常
function onSidebarViewUpdate(v) {
  if (v === 'threaded' || v === 'sandbox' || v === 'start') {
    view.value = v
  } else {
    view.value = 'start'
  }
  // 视图切换后刷新图标/交互组件
  refreshIcons()
}

</script>

<template>
  <AppShell :homePlain="view === 'start'">
    <template #sidebar>
      <SidebarDrawer v-if="showSidebar" v-model="drawerOpen">
        <SidebarNav
          :view="view"
          :theme="theme"
          @update:view="onSidebarViewUpdate"
          @update:theme="onThemeUpdate"
          @openAppearance="(appearanceOpen = !appearanceOpen, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false, aiConfigOpen = false)"
          @openAppSettings="(appSettingsOpen = !appSettingsOpen, appearanceOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false, aiConfigOpen = false)"
          @openPresets="(presetsOpen = !presetsOpen, appearanceOpen = false, appSettingsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false, aiConfigOpen = false)"
          @openWorldbook="(worldbookOpen = !worldbookOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false, aiConfigOpen = false)"
          @openCharacters="(charactersOpen = !charactersOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, personaOpen = false, regexOpen = false, aiConfigOpen = false)"
          @openPersona="(personaOpen = !personaOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, regexOpen = false, aiConfigOpen = false)"
          @openRegex="(regexOpen = !regexOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false, aiConfigOpen = false)"
          @openAIConfig="(aiConfigOpen = !aiConfigOpen, appearanceOpen = false, appSettingsOpen = false, presetsOpen = false, worldbookOpen = false, charactersOpen = false, personaOpen = false, regexOpen = false)"
        />
      </SidebarDrawer>
    </template>

    <template #overlays>
      
      <transition name="st-subpage">
        <AppearancePanel
          v-if="showSidebar && appearanceOpen"
          @close="appearanceOpen = false"
        />
      </transition>

      
      <transition name="st-subpage">
        <AppSettingsPanel
          v-if="showSidebar && appSettingsOpen"
          :theme="theme"
          @update:theme="onThemeUpdate"
          @close="appSettingsOpen = false"
        />
      </transition>

      
      <transition name="st-subpage">
        <PresetsPanel
          v-if="showSidebar && presetsOpen"
          @close="presetsOpen = false"
          @view="(key) => openViewModal('preset', '预设详情 - ' + key, key)"
        />
      </transition>

      
      <transition name="st-subpage">
        <WorldbookPanel
          v-if="showSidebar && worldbookOpen"
          @close="worldbookOpen = false"
          @view="(key) => openViewModal('worldbook', '世界书详情 - ' + key, key)"
        />
      </transition>

      
      <transition name="st-subpage">
        <CharactersPanel
          v-if="showSidebar && charactersOpen"
          @close="charactersOpen = false"
          @view="(key) => openViewModal('character', '角色卡详情 - ' + key, key)"
        />
      </transition>

      
      <transition name="st-subpage">
        <PersonaPanel
          v-if="showSidebar && personaOpen"
          @close="personaOpen = false"
          @view="(key) => openViewModal('persona', '用户信息详情 - ' + key, key)"
        />
      </transition>

      
      <transition name="st-subpage">
        <RegexPanel
          v-if="showSidebar && regexOpen"
          @close="regexOpen = false"
          @view="(key) => openViewModal('regex', '正则规则详情 - ' + key, key)"
        />
      </transition>

      
      <transition name="st-subpage">
        <AIConfigPanel
          v-if="showSidebar && aiConfigOpen"
          :currentPreset="currentPresetData"
          @close="aiConfigOpen = false"
        />
      </transition>
    </template>

    
    
    <section v-if="view === 'start'" data-scope="start-view" class="st-start">
      
      <HomeMenu
        @new-game="openNewGame"
        @open-load="openHomeModal('load')"
        @open-gallery="openHomeModal('gallery')"
        @open-options="openHomeModal('options')"
      />
    </section>

    
    <section v-else-if="view === 'threaded'" data-scope="chat-threaded" class="st-threaded">
      <ThreadedChatPreview :messages="messages" />
    </section>

    
    <section v-else data-scope="chat-sandbox" class="st-sandbox">
      <SandboxStage />
    </section>

    
    <ContentViewModal
      v-model:show="viewModalOpen"
      :title="viewModalTitle"
      @close="closeViewModal"
    >
      <div v-if="viewModalLoading" class="modal-loading">读取中...</div>
      <div v-else-if="viewModalError" class="modal-error">读取失败：{{ viewModalError }}</div>
      <PresetDetailView
        v-else-if="viewModalType === 'preset'"
        :presetData="viewModalData"
        :file="viewModalFile"
      />
      <WorldbookDetailView
        v-else-if="viewModalType === 'worldbook'"
        :worldbookData="viewModalData"
        :file="viewModalFile"
      />
      <CharacterDetailView
        v-else-if="viewModalType === 'character'"
        :characterData="viewModalData"
        :file="viewModalFile"
      />
      <PersonaDetailView
        v-else-if="viewModalType === 'persona'"
        :personaData="viewModalData"
        :file="viewModalFile"
      />
      <RegexDetailView
        v-else-if="viewModalType === 'regex'"
        :regexData="viewModalData"
        :file="viewModalFile"
      />
      <div v-else class="modal-placeholder">
        <div class="placeholder-icon">📋</div>
        <div class="placeholder-text">内容查看</div>
        <div class="placeholder-desc">视图类型：{{ viewModalType }}</div>
      </div>
    </ContentViewModal>

    
    <NewChatModal
      v-model:show="newGameOpen"
      title="新建对话"
      @confirm="onNewChatConfirm"
      @close="cancelNewGame"
    />

    
    <LoadGameModal
      :show="homeModalOpen && homeModalType === 'load'"
      :title="homeModalTitle || '读取存档'"
      @update:show="(v) => { if (!v) closeHomeModal() }"
      @close="closeHomeModal"
    />
    <GalleryModal
      :show="homeModalOpen && homeModalType === 'gallery'"
      :title="homeModalTitle || '画廊'"
      @update:show="(v) => { if (!v) closeHomeModal() }"
      @close="closeHomeModal"
    />
    <OptionsModal
      :show="homeModalOpen && homeModalType === 'options'"
      :title="homeModalTitle || '选项'"
      :theme="theme"
      @update:theme="onThemeUpdate"
      @update:show="(v) => { if (!v) closeHomeModal() }"
      @close="closeHomeModal"
    />
  </AppShell>
</template>


<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=Cormorant+Garamond:wght@400;600;700&display=swap');

/* Tokens moved to src/styles/tokens.css
   - Loaded via main.js import: import './styles/tokens.css'
   - Runtime overrides by ThemeStore and AppearancePanel remain effective */

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
/* start-view 完全透明：去除 body 白色底色 */
body[data-app="smarttavern"][data-home="plain"] {
  background-color: transparent !important;
}

* { box-sizing: border-box; }


/* Home 背景景深 + 焦点位移动画（进入/返回主页时触发） */
:root {
  --fx-shift-x: 0px;
  --fx-shift-y: 0px;
}

@keyframes stDepthIntro {
  /* 两段式：0-75% 焦点位移+模糊减弱；75-100% 仅清晰过渡 */
  0% {
    transform: scale(1.08) translate3d(var(--fx-shift-x), var(--fx-shift-y), 0);
    filter: blur(20px) saturate(118%) brightness(0.96);
    opacity: 0;
  }
  75% {
    transform: scale(1) translate3d(0, 0, 0);
    filter: blur(2px) saturate(103%) brightness(1);
    opacity: 1;
  }
  100% {
    transform: scale(1) translate3d(0, 0, 0);
    filter: blur(0px) saturate(100%) brightness(1);
    opacity: 1;
  }
}


/* 使用 body.st-bg-anim 切换动画态，避免常驻性能消耗 */
body.st-bg-anim [data-scope="start-view"]::before {
  will-change: transform, filter, opacity;
  /* 放慢到 4s，总时长匹配 JS 清理 4.1s */
  animation: stDepthIntro 4s cubic-bezier(.22,.61,.36,1) forwards;
}
/* Threaded/Sandbox 背景：两段式“0-75% 位移+模糊、75-100% 仅清晰”动画（背景只做景深，不改不透明度） */
/* 改为依据用户配置的“目标模糊度”作为动画终点，避免动画结束后跳变导致闪烁 */
@keyframes stDepthIntroBgVarThreaded {
  0% {
    transform: scale(1.08) translate3d(var(--fx-shift-x), var(--fx-shift-y), 0);
    filter: blur(var(--st-bg-intro-blur-start, 20px)) saturate(118%) brightness(0.96);
  }
  75% {
    transform: scale(1) translate3d(0,0,0);
    /* 中段仍保持较小模糊，趋近自然对焦 */
    filter: blur(2px) saturate(103%) brightness(1);
  }
  100% {
    transform: scale(1) translate3d(0,0,0);
    /* 终点严格对齐用户设置的模糊度变量 */
    filter: blur(var(--st-threaded-bg-blur, 0px)) saturate(100%) brightness(1);
  }
}
@keyframes stDepthIntroBgVarSandbox {
  0% {
    transform: scale(1.08) translate3d(var(--fx-shift-x), var(--fx-shift-y), 0);
    filter: blur(var(--st-bg-intro-blur-start, 20px)) saturate(118%) brightness(0.96);
  }
  75% {
    transform: scale(1) translate3d(0,0,0);
    filter: blur(2px) saturate(103%) brightness(1);
  }
  100% {
    transform: scale(1) translate3d(0,0,0);
    filter: blur(var(--st-sandbox-bg-blur, 0px)) saturate(100%) brightness(1);
  }
}

/* 叠加遮罩按变量过渡到目标不透明度，避免加载完成时跳变 */
@keyframes stDepthOverlayToVar {
  0%   { opacity: 1; }
  100% { opacity: var(--st-target-bg-opacity, 0.12); }
}

/* 楼层对话页（threaded）：背景做景深，遮罩按变量淡入到目标不透明度 */
body.st-bg-anim-threaded .st-threaded::before,
body.st-bg-anim-threaded [data-scope="chat-threaded"]::before {
  will-change: transform, filter;
  /* 终点对齐 --st-threaded-bg-blur，避免结束后跳变 */
  animation: stDepthIntroBgVarThreaded 4s cubic-bezier(.22,.61,.36,1) forwards;
}
body.st-bg-anim-threaded .st-threaded::after,
body.st-bg-anim-threaded [data-scope="chat-threaded"]::after {
  will-change: opacity;
  animation: stDepthOverlayToVar 4s cubic-bezier(.22,.61,.36,1) forwards;
}

/* 前端沙盒页（sandbox）：背景做景深，遮罩按变量淡入到目标不透明度 */
body.st-bg-anim-sandbox .st-sandbox::before,
body.st-bg-anim-sandbox [data-scope="chat-sandbox"]::before {
  will-change: transform, filter;
  /* 终点对齐 --st-sandbox-bg-blur，避免结束后跳变 */
  animation: stDepthIntroBgVarSandbox 4s cubic-bezier(.22,.61,.36,1) forwards;
}
body.st-bg-anim-sandbox .st-sandbox::after,
body.st-bg-anim-sandbox [data-scope="chat-sandbox"]::after {
  will-change: opacity;
  animation: stDepthOverlayToVar 4s cubic-bezier(.22,.61,.36,1) forwards;
}


</style>


<style scoped>

/* 开始视图（Hero） */
.st-start {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  padding: 16px;
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
  opacity: 1;
  z-index: 0; /* 确保背景图位于内容层后面但不被 body 白底影响 */
  pointer-events: none;
}
@media (max-width: 980px) { .st-start { grid-template-columns: 1fr; } }


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
  opacity: 1; /* 背景图始终全可见，遮罩由 ::after 控制 */
  /* 直接对背景图片层应用模糊，避免 backdrop-filter 在某些栈顺序下不生效 */
  filter: blur(var(--st-threaded-bg-blur, 0px));
  will-change: filter;
  z-index: -1;
  pointer-events: none;
}
.st-threaded::after {
  content: '';
  position: fixed;
  inset: 0;
  /* 遮罩色固定为纯墨色/纯白色，由不透明度变量控制强度 */
  background: rgb(var(--st-overlay-ink) / 1);
  /* 终点与用户配置一致，动画也会过渡到该变量值，避免闪烁 */
  opacity: var(--st-threaded-bg-opacity, 0.12);
  z-index: -1;
  pointer-events: none;
  /* 为 overlay 动画提供目标变量（线程页）：始终与不透明度变量一致 */
  --st-target-bg-opacity: var(--st-threaded-bg-opacity, 0.12);
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
  opacity: 1; /* 背景图始终全可见，遮罩由 ::after 控制 */
  /* 直接对背景图片层应用模糊（更稳定的实现） */
  filter: blur(var(--st-sandbox-bg-blur, 0px));
  will-change: filter;
  z-index: -1;
  pointer-events: none;
}
.st-sandbox::after {
  content: '';
  position: fixed;
  inset: 0;
  /* 主题自适应遮罩（不透明度独立为元素 opacity，避免动画终值跳跃） */
  background: rgb(var(--st-overlay-ink) / 1);
  opacity: var(--st-sandbox-bg-opacity, 0.12);
  /* 新增：对背景图片应用可调模糊（通过遮罩层的 backdrop-filter 实现） */
  backdrop-filter: blur(var(--st-sandbox-bg-blur, 0px));
  -webkit-backdrop-filter: blur(var(--st-sandbox-bg-blur, 0px));
  z-index: -1;
  pointer-events: none;
  /* 为 overlay 动画提供目标变量（沙盒页） */
  --st-target-bg-opacity: var(--st-sandbox-bg-opacity, 0.12);
}



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
  color: rgb(var(--st-color-text) /0.65);
}

</style>
