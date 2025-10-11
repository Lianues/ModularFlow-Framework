<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
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
import AIConfigPanel from '@/components/sidebar/AIConfigPanel.vue'
import ContentViewModal from '@/components/common/ContentViewModal.vue'
import PresetDetailView from '@/components/content/PresetDetailView.vue'
import WorldbookDetailView from '@/components/content/WorldbookDetailView.vue'
import CharacterDetailView from '@/components/content/CharacterDetailView.vue'
import PersonaDetailView from '@/components/content/PersonaDetailView.vue'
import RegexDetailView from '@/components/content/RegexDetailView.vue'
import LoadGameView from '@/components/home/LoadGameView.vue'
import GalleryView from '@/components/home/GalleryView.vue'
import OptionsView from '@/components/home/OptionsView.vue'
import SandboxStage from '@/components/sandbox/SandboxStage.vue'
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

/* New Game 模态：选择聊天方式（对话楼层 / 前端沙盒） */
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
function selectMode(mode) {
  if (mode === 'threaded' || mode === 'sandbox') {
    view.value = mode
  }
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

/* 主页左下菜单：根据所占背景像素自动选择黑/白前景色 */
let __bgImg = null
let __bgUrlCache = null
let __cv = null
let __ctx = null

function getBgUrlFromCSS() {
  const raw = getComputedStyle(document.documentElement).getPropertyValue('--st-bg-start') || ''
  const m = raw.match(/url\\((["']?)(.*?)\\1\\)/)
  return m ? m[2] : ''
}

async function ensureBgImage() {
  const url = getBgUrlFromCSS()
  if (!url) return null
  if (__bgImg && __bgUrlCache === url) return __bgImg
  __bgUrlCache = url
  __bgImg = await new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => resolve(null)
    img.src = url
  })
  return __bgImg
}

function ensureCanvas() {
  const vw = window.innerWidth, vh = window.innerHeight
  if (!__cv) {
    __cv = document.createElement('canvas')
    __ctx = __cv.getContext('2d', { willReadFrequently: true })
  }
  if (__cv.width !== vw || __cv.height !== vh) {
    __cv.width = vw
    __cv.height = vh
  }
}

function drawBgToCanvas(img) {
  if (!img || !__ctx) return
  const vw = window.innerWidth, vh = window.innerHeight
  const iw = img.naturalWidth, ih = img.naturalHeight
  const scale = Math.max(vw / iw, vh / ih)
  const sw = iw * scale, sh = ih * scale
  const ox = (vw - sw) / 2
  const oy = (vh - sh) / 2
  __ctx.clearRect(0, 0, vw, vh)
  __ctx.drawImage(img, ox, oy, sw, sh)
}

function sampleBrightnessAt(x, y, r = 8) {
  if (!__ctx) return null
  const x0 = Math.max(0, Math.floor(x - r))
  const y0 = Math.max(0, Math.floor(y - r))
  const w = Math.min(__cv.width - x0, r * 2)
  const h = Math.min(__cv.height - y0, r * 2)
  if (w <= 0 || h <= 0) return null
  try {
    const data = __ctx.getImageData(x0, y0, w, h).data
    let sum = 0, n = 0
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i], g = data[i + 1], b = data[i + 2]
      // 相对亮度（sRGB）
      sum += 0.2126 * r + 0.7152 * g + 0.0722 * b
      n++
    }
    return n ? (sum / n) : null
  } catch (e) {
    // Canvas 污染或数据不可读，返回空以触发降级方案
    return null
  }
}

function chooseInkFor(brightness) {
  // 背景亮 → 用深色字；背景暗 → 用白字
  return brightness > 160 ? '#0f1226' : '#ffffff'
}

async function updateHomeMenuInk() {
  if (view.value !== 'start') return
  const img = await ensureBgImage()
  ensureCanvas()
  drawBgToCanvas(img)
  const buttons = document.querySelectorAll('.home-menu .menu-btn')
  buttons.forEach(btn => {
    const rect = btn.getBoundingClientRect()
    // 采样 5 点（中心 + 四角中点），避免局部高亮/阴影导致误判
    const pts = [
      [rect.left + rect.width * 0.5, rect.top + rect.height * 0.5],
      [rect.left + rect.width * 0.25, rect.top + rect.height * 0.35],
      [rect.right - rect.width * 0.25, rect.top + rect.height * 0.35],
      [rect.left + rect.width * 0.25, rect.bottom - rect.height * 0.35],
      [rect.right - rect.width * 0.25, rect.bottom - rect.height * 0.35],
    ]
    const samples = pts
      .map(([x,y]) => sampleBrightnessAt(x, y, 10))
      .filter(v => typeof v === 'number')
    const avg = samples.length ? (samples.reduce((a,b)=>a+b,0) / samples.length) : null
    const ink = avg == null ? '#ffffff' : chooseInkFor(avg)

    // 智能前景色 + 辅助阴影与边框，提升在复杂背景下的可读性
    const shadow = ink === '#ffffff'
      ? '0 1px 2px rgba(0,0,0,0.55), 0 0 8px rgba(0,0,0,0.20)'
      : '0 1px 0 rgba(255,255,255,0.35)'
    const border = ink === '#ffffff'
      ? 'rgba(255,255,255,0.55)'
      : 'rgba(0,0,0,0.45)'

    btn.style.setProperty('--menu-fg', ink)
    btn.style.setProperty('--menu-shadow', shadow)
    btn.style.setProperty('--menu-border', border)
  })
}

function __onResizeOrScroll() {
  // 轻量更新（无需抖动：按钮较少）
  updateHomeMenuInk()
}

/* 高级背景动画：景深过渡 + 焦点位移（进入/切换各视图时触发）
 * 两段式：0-75% 焦点位移 + 模糊减弱；75-100% 仅清晰过渡
 */
let __bgFxTimer = null
function __triggerBgAnim(bodyClass) {
  const docEl = document.documentElement
  const target = document.body
  // 随机焦点位移（细微偏移，营造镜头对焦感）
  const rx = ((Math.random() * 2) - 1) * 14 // -14 ~ 14 px
  const ry = ((Math.random() * 2) - 1) * 10 // -10 ~ 10 px
  docEl.style.setProperty('--fx-shift-x', rx.toFixed(1) + 'px')
  docEl.style.setProperty('--fx-shift-y', ry.toFixed(1) + 'px')

  // 移除所有动画类，重新触发
  target.classList.remove('st-bg-anim', 'st-bg-anim-threaded', 'st-bg-anim-sandbox')
  // 强制重排以重触发动画
  void target.offsetWidth
  target.classList.add(bodyClass)

  clearTimeout(__bgFxTimer)
  // 总时长 4s：前 3s 焦点位移 + 模糊减弱，最后 1s 仅清晰过渡
  __bgFxTimer = setTimeout(() => {
    target.classList.remove(bodyClass)
    docEl.style.removeProperty('--fx-shift-x')
    docEl.style.removeProperty('--fx-shift-y')
  }, 4100)
}
function playHomeBgFX(){ __triggerBgAnim('st-bg-anim') }
function playThreadedBgFX(){ __triggerBgAnim('st-bg-anim-threaded') }
function playSandboxBgFX(){ __triggerBgAnim('st-bg-anim-sandbox') }

onMounted(() => {
  window.addEventListener('resize', __onResizeOrScroll, { passive: true })
  window.addEventListener('scroll', __onResizeOrScroll, { passive: true })
  // 首次进入主页时计算一次
  if (view.value === 'start') setTimeout(updateHomeMenuInk, 50)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', __onResizeOrScroll)
  window.removeEventListener('scroll', __onResizeOrScroll)
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

/**
 * ModeSwitch：在聊天页面内部切换（对话楼层 / 全局沙盒占位）
 */
// ModeSwitch moved to src/components/common/ModeSwitch.vue
</script>

<template>
  <div data-scope="app-shell" class="st-app-shell" :class="{ 'home-plain': view === 'start' }">
    <!-- 背景层（渐变 + 噪点） -->
    <div class="st-bg">
      <div class="st-gradient" />
      <div class="st-noise" />
    </div>


    <!-- 主体 -->
    <div class="st-body">
      <!-- 侧边栏（仅聊天视图显示） -->
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
          :theme="theme"
          @update:theme="onThemeUpdate"
          @close="appSettingsOpen = false"
        />
      </transition>

      <!-- 预设面板：模仿外观面板的弹出与定位（同层/同位置/同过渡） -->
      <transition name="st-subpage">
        <PresetsPanel
          v-if="showSidebar && presetsOpen"
          @close="presetsOpen = false"
          @view="(key) => openViewModal('preset', '预设详情 - ' + key, key)"
        />
      </transition>

      <!-- 世界书面板：同层/同位置/同过渡 -->
      <transition name="st-subpage">
        <WorldbookPanel
          v-if="showSidebar && worldbookOpen"
          @close="worldbookOpen = false"
          @view="(key) => openViewModal('worldbook', '世界书详情 - ' + key, key)"
        />
      </transition>

      <!-- 角色卡面板：同层/同位置/同过渡 -->
      <transition name="st-subpage">
        <CharactersPanel
          v-if="showSidebar && charactersOpen"
          @close="charactersOpen = false"
          @view="(key) => openViewModal('character', '角色卡详情 - ' + key, key)"
        />
      </transition>

      <!-- 用户信息面板：同层/同位置/同过渡 -->
      <transition name="st-subpage">
        <PersonaPanel
          v-if="showSidebar && personaOpen"
          @close="personaOpen = false"
          @view="(key) => openViewModal('persona', '用户信息详情 - ' + key, key)"
        />
      </transition>

      <!-- 正则面板：同层/同位置/同过渡 -->
      <transition name="st-subpage">
        <RegexPanel
          v-if="showSidebar && regexOpen"
          @close="regexOpen = false"
          @view="(key) => openViewModal('regex', '正则规则详情 - ' + key, key)"
        />
      </transition>

      <!-- AI 配置面板：同层/同位置/同过渡（占位页面） -->
      <transition name="st-subpage">
        <AIConfigPanel
          v-if="showSidebar && aiConfigOpen"
          :currentPreset="currentPresetData"
          @close="aiConfigOpen = false"
        />
      </transition>

      <!-- 主内容 -->
      <main data-scope="main" class="st-main">
        <!-- 开始视图（无侧边栏） -->
        <section v-if="view === 'start'" data-scope="start-view" class="st-start">
          <!-- hero removed: 主页采用神话风格行动面板全屏居中 -->

          <div class="st-home-menu">
            <nav class="home-menu">
              <button class="menu-btn" type="button" @click="openNewGame">
                <i data-lucide="swords" class="icon-20" aria-hidden="true"></i>
                <span>New Game</span>
              </button>
              <button class="menu-btn" type="button" @click="openHomeModal('load')">
                <i data-lucide="history" class="icon-20" aria-hidden="true"></i>
                <span>Load Game</span>
              </button>
              <button class="menu-btn" type="button" @click="openHomeModal('gallery')">
                <i data-lucide="image" class="icon-20" aria-hidden="true"></i>
                <span>Gallery</span>
              </button>
              <button class="menu-btn" type="button" @click="openHomeModal('options')">
                <i data-lucide="settings" class="icon-20" aria-hidden="true"></i>
                <span>Options</span>
              </button>
            </nav>
          </div>
        </section>

        <!-- 楼层对话独立视图 -->
        <section v-else-if="view === 'threaded'" data-scope="chat-threaded" class="st-threaded">
          <ThreadedChatPreview :messages="messages" />
        </section>

        <!-- 全局沙盒独立视图 -->
        <section v-else data-scope="chat-sandbox" class="st-sandbox">
          <SandboxStage />
        </section>
      </main>
    </div>

    <!-- 内容查看模态框 -->
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

    <!-- New Game 选择聊天方式 -->
    <ContentViewModal
      v-model:show="newGameOpen"
      title="选择聊天方式"
      @close="newGameOpen = false"
    >
      <div class="mode-select">
        <button class="mode-card" type="button" @click="selectMode('threaded')">
          <span class="mode-icon"><i data-lucide="message-square" class="icon-24" aria-hidden="true"></i></span>
          <div class="mode-title">对话楼层</div>
          <div class="mode-sub">Threaded Chat</div>
        </button>
        <button class="mode-card" type="button" @click="selectMode('sandbox')">
          <span class="mode-icon"><i data-lucide="app-window" class="icon-24" aria-hidden="true"></i></span>
          <div class="mode-title">前端沙盒</div>
          <div class="mode-sub">Frontend Sandbox</div>
        </button>
      </div>
    </ContentViewModal>

    <!-- Home menu modals: Load/Gallery/Options -->
    <ContentViewModal
      v-model:show="homeModalOpen"
      :title="homeModalTitle"
      @close="closeHomeModal"
    >
      <div v-if="homeModalType === 'load'">
        <LoadGameView />
      </div>
      <div v-else-if="homeModalType === 'gallery'">
        <GalleryView />
      </div>
      <div v-else-if="homeModalType === 'options'">
        <OptionsView :theme="theme" @update:theme="onThemeUpdate" />
      </div>
      <div v-else class="modal-placeholder">
        <div class="placeholder-icon">🗂️</div>
        <div class="placeholder-text">主页功能</div>
        <div class="placeholder-desc">类型：{{ homeModalType || '未选择' }}</div>
      </div>
    </ContentViewModal>
  </div>
</template>

<!-- 全局：设计令牌 + 主题（不加 scoped，供全局使用） -->
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
body.st-live-tuning[data-active-slider="sandboxRadius"] [data-scope="settings-view"] .st-control[data-slider="sandboxRadius"],
/* NEW: Threaded HTML stage sliders */
body.st-live-tuning[data-active-slider="threadedStageMaxWidthPct"] [data-scope="settings-view"] .st-control[data-slider="threadedStageMaxWidthPct"],
body.st-live-tuning[data-active-slider="threadedStagePadding"] [data-scope="settings-view"] .st-control[data-slider="threadedStagePadding"],
body.st-live-tuning[data-active-slider="threadedStageRadius"] [data-scope="settings-view"] .st-control[data-slider="threadedStageRadius"],
/* NEW: Background opacity sliders */
body.st-live-tuning[data-active-slider="threadedBgOpacity"] [data-scope="settings-view"] .st-control[data-slider="threadedBgOpacity"],
body.st-live-tuning[data-active-slider="threadedMsgBgOpacity"] [data-scope="settings-view"] .st-control[data-slider="threadedMsgBgOpacity"],
body.st-live-tuning[data-active-slider="sandboxBgOpacity"] [data-scope="settings-view"] .st-control[data-slider="sandboxBgOpacity"],
body.st-live-tuning[data-active-slider="sandboxStageBgOpacity"] [data-scope="settings-view"] .st-control[data-slider="sandboxStageBgOpacity"],
/* NEW: Background blur sliders */
body.st-live-tuning[data-active-slider="threadedBgBlur"] [data-scope="settings-view"] .st-control[data-slider="threadedBgBlur"],
body.st-live-tuning[data-active-slider="sandboxBgBlur"] [data-scope="settings-view"] .st-control[data-slider="sandboxBgBlur"] {
  visibility: visible !important;
}

/* 新增：live-tuning 仅显示新加入的滑条（对话容器/输入框背景不透明度） */
body.st-live-tuning[data-active-slider="threadedListBgOpacity"] [data-scope="settings-view"] .st-control[data-slider="threadedListBgOpacity"],
body.st-live-tuning[data-active-slider="threadedInputBgOpacity"] [data-scope="settings-view"] .st-control[data-slider="threadedInputBgOpacity"] {
  visibility: visible !important;
}

/* Live-tuning 时隐藏外观面板中的自定义滚动条（避免干扰聚焦） */
body.st-live-tuning [data-scope="settings-view"] .custom-scrollbar-wrapper .scroll-track {
  opacity: 0 !important;
  transform: translateX(8px) !important;
  pointer-events: none !important;
}

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

/* 禁止侧边栏按钮与展开面板文本被选中复制（保留表单可编辑） */
[data-scope="sidebar"],
[data-scope="sidebar"] *,
[data-scope="sidebar-nav"],
[data-scope="sidebar-nav"] *,
[data-scope="settings-view"],
[data-scope="settings-view"] *,
[data-scope="presets-view"],
[data-scope="presets-view"] *,
[data-scope="worldbook-view"],
[data-scope="worldbook-view"] *,
[data-scope="characters-view"],
[data-scope="characters-view"] *,
[data-scope="persona-view"],
[data-scope="persona-view"] *,
[data-scope="regex-view"],
[data-scope="regex-view"] *,
[data-scope="appsettings-view"],
[data-scope="appsettings-view"] * {
  user-select: none;
  -webkit-user-select: none;
  -ms-user-select: none;
  -webkit-touch-callout: none;
}

/* 例外：面板内的表单控件允许选中文本，保证可编辑性 */
[data-scope$="-view"] input,
[data-scope$="-view"] textarea,
[data-scope$="-view"] select,
[data-scope="settings-view"] input,
[data-scope="settings-view"] textarea,
[data-scope="settings-view"] select {
  user-select: text;
  -webkit-user-select: text;
  -ms-user-select: text;
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

/* Home plain mode: remove gradient/noise overlay */
.home-plain .st-bg { display: none; }
/* Home plain: 所有容器完全透明，不带颜色 */
.home-plain .st-body,
.home-plain .st-main,
.home-plain [data-scope="start-view"] {
  background: transparent !important;
}

/* 玻璃拟态与卡片 */
.glass {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: saturate(140%) blur(10px);
  -webkit-backdrop-filter: saturate(140%) blur(10px);
  border: 1px solid rgb(var(--st-border) /0.7);
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
/* 旧 st-header 样式已移除，改用 AppTopBar 统一顶栏组件 */

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

.st-hero {
  padding: 24px; border-radius: var(--st-radius-lg);
  box-shadow: var(--st-shadow-lg);
}
.st-title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  font-family: var(--st-font-myth);
  letter-spacing: .6px;
  background: linear-gradient(90deg, #e9d8a6, #ffd166);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.st-desc { margin: 0 0 12px; color: rgb(var(--st-color-text) /0.75); }
.st-cta { display: flex; gap: 12px; margin-top: 6px; }
.st-btn {
  appearance: none; border: 1px solid rgb(var(--st-border)); background: rgb(var(--st-surface));
  padding: 10px 14px; border-radius: var(--st-radius-md); cursor: pointer; color: rgb(var(--st-color-text));
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
}
.st-btn:hover { transform: translateY(-1px); box-shadow: var(--st-shadow-md); }
.st-btn.st-primary { background: linear-gradient(135deg, rgb(var(--st-primary) /1), rgb(var(--st-accent) /1)); color: var(--st-primary-contrast); border-color: transparent; }
.st-btn.st-primary:hover { filter: saturate(1.05); }

.st-features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 980px) { .st-features { grid-template-columns: 1fr; } }
.st-feature { padding: 18px; border-radius: var(--st-radius-lg); }
.st-feature-icon { font-size: 20px; }
.st-feature-title { margin-top: 8px; font-weight: 600; }
.st-feature-desc { margin-top: 4px; color: rgb(var(--st-color-text) /0.7); }

/* Mythic home actions */
.st-myth-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(420px, 1fr));
  grid-template-rows: repeat(2, 1fr);
  gap: 24px;
  width: 100%;
  max-width: 1400px;
  height: clamp(560px, 74vh, 900px);
  margin: 0 auto;
  padding: 16px;
}
@media (max-width: 980px) {
  .st-myth-actions {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    height: auto;
    padding: 12px;
  }
}

.myth-action {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  grid-template-areas:
    "icon label"
    "icon sub";
  align-items: center;
  gap: 12px 20px;
  padding: 28px 30px;
  height: 100%;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgb(var(--st-border) /0.9);
  background: rgb(var(--st-surface) /0.72);
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  box-shadow: var(--st-shadow-md);
  cursor: pointer;
  transition: transform .22s cubic-bezier(.22,.61,.36,1), box-shadow .22s cubic-bezier(.22,.61,.36,1), border-color .2s ease, background .2s ease;
  overflow: hidden;
}
.myth-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(0,0,0,0.14);
  border-color: rgb(var(--st-primary) /0.5);
  background: rgb(var(--st-surface) /0.78);
}
.myth-icon {
  grid-area: icon;
  width: 84px; height: 84px;
  border-radius: 9999px;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, rgb(var(--st-primary) /.16), rgb(var(--st-accent) /.16));
  border: 1px solid rgb(var(--st-border) /0.9);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 6px 14px rgba(0,0,0,0.08);
  color: var(--menu-fg, rgb(var(--st-color-text)));
  z-index: 1;
}
.icon-20 { width: 28px; height: 28px; stroke: currentColor; }

.myth-label {
  grid-area: label;
  font-family: var(--st-font-myth);
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 28px;
  color: rgb(var(--st-color-text));
}
.myth-sub {
  grid-area: sub;
  font-size: 14px;
  color: rgb(var(--st-color-text) /0.78);
  letter-spacing: .4px;
}

/* Ornament ring */
.myth-ring {
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  background:
    radial-gradient(1200px 400px at 0% 0%, rgba(255,255,255,0.12), transparent 50%),
    conic-gradient(from 0deg at 50% 50%, rgba(233,216,166,0.35), rgba(94,234,212,0.25), rgba(88,80,236,0.25), rgba(233,216,166,0.35));
  mask: linear-gradient(#000, #000) content-box, linear-gradient(#000, #000);
  -webkit-mask: linear-gradient(#000, #000) content-box, linear-gradient(#000, #000);
  padding: 1px; /* hairline */
  border: 1px solid rgb(var(--st-border) /0.6);
  opacity: .65;
  pointer-events: none;
}

/* New Game 模态选择样式 */
.mode-select {
  display: grid;
  grid-template-columns: repeat(2, minmax(260px, 1fr));
  gap: 16px;
}
@media (max-width: 720px) {
  .mode-select { grid-template-columns: 1fr; }
}
.mode-card {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  grid-template-areas:
    "icon title"
    "icon sub";
  align-items: center;
  gap: 8px 12px;
  padding: 16px 18px;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgb(var(--st-border) /0.9);
  background: rgb(var(--st-surface) /0.72);
  backdrop-filter: blur(8px) saturate(140%);
  -webkit-backdrop-filter: blur(8px) saturate(140%);
  box-shadow: var(--st-shadow-sm);
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1), border-color .18s ease;
}
.mode-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--st-shadow-md);
  border-color: rgb(var(--st-primary) /0.5);
}
.mode-icon {
  grid-area: icon;
  width: 48px; height: 48px;
  border-radius: 9999px;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, rgb(var(--st-primary) /.16), rgb(var(--st-accent) /.16));
  border: 1px solid rgb(var(--st-border) /0.9);
  color: rgb(var(--st-color-text));
}
.icon-24 { width: 24px; height: 24px; stroke: currentColor; }
.mode-title {
  grid-area: title;
  font-family: var(--st-font-myth);
  font-weight: 700;
  letter-spacing: .6px;
  color: rgb(var(--st-color-text));
}
.mode-sub {
  grid-area: sub;
  font-size: 12px;
  color: rgb(var(--st-color-text) /0.75);
}

/* Home vertical menu (bottom-left) */
.st-home-menu {
  position: absolute;
  left: 24px;
  bottom: 24px;
  z-index: 2;
}
.home-menu {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.menu-btn {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-radius: var(--st-radius-lg);
  border: 1px solid var(--menu-border, rgb(var(--st-border) /0.7));
  background: transparent; /* no white mask on home */
  color: var(--menu-fg, rgb(var(--st-color-text)));
  text-shadow: var(--menu-shadow, none);
  font-family: var(--st-font-myth);
  font-weight: 800;
  font-size: 20px;
  letter-spacing: .8px;
  cursor: pointer;
  transition:
    transform .18s cubic-bezier(.22,.61,.36,1),
    border-color .18s ease,
    color .18s ease,
    text-shadow .18s ease;
}
.menu-btn:hover {
  transform: translateX(4px);
  border-color: rgb(var(--st-primary) /0.6);
  color: var(--menu-fg, rgb(var(--st-color-text)));
}
.home-menu .icon-20 { width: 26px; height: 26px; stroke: currentColor; }

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
  /* 同步舞台透明度：边框/背景/玻璃强度随 --st-sandbox-stage-bg-opacity 变化 */
  border: 2px solid rgb(var(--st-primary) / calc(var(--st-sandbox-stage-bg-opacity, 0.82) * 0.25));
  background: rgb(var(--st-surface) / var(--st-sandbox-stage-bg-opacity, 0.82)) !important;
  backdrop-filter: blur(calc(var(--st-sandbox-stage-bg-opacity, 0.82) * 4px)) saturate(calc(1 + var(--st-sandbox-stage-bg-opacity, 0.82) * 0.4));
  -webkit-backdrop-filter: blur(calc(var(--st-sandbox-stage-bg-opacity, 0.82) * 4px)) saturate(calc(1 + var(--st-sandbox-stage-bg-opacity, 0.82) * 0.4));
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
  color: rgb(var(--st-color-text) /0.7);
}

.st-sandbox-body {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 0 12px 12px;
}

.st-sandbox-demo-box {
  background: rgb(var(--st-surface) /0.6);
  border: 1px solid rgb(var(--st-border) /0.6);
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
  color: rgb(var(--st-color-text) /0.8);
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
  color: rgb(var(--st-color-text) /0.65);
}
</style>
