<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import SidebarNav from '@/components/sidebar/SidebarNav.vue'
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
import NewChatModal from '@/components/home/NewChatModal.vue'
import LoadGameModal from '@/components/home/LoadGameModal.vue'
import GalleryModal from '@/components/home/GalleryModal.vue'
import OptionsModal from '@/components/home/OptionsModal.vue'
import AppShell from '@/layouts/AppShell.vue'
import { useHomeMenuInk } from '@/composables/useHomeMenuInk'
import { useBackgroundFx } from '@/composables/useBackgroundFx'
import { useSidebar } from '@/composables/useSidebar.js'
import { usePanels } from '@/composables/usePanels'
import { useHomeModal } from '@/composables/useHomeModal'
import { useThemeMode } from '@/composables/useThemeMode'
import { useUiAssets } from '@/composables/useUiAssets'
import { useViewModal } from '@/composables/useViewModal'
import StartView from '@/views/StartView.vue'
import ThreadedView from '@/views/ThreadedView.vue'
import SandboxView from '@/views/SandboxView.vue'
import { useNewGame } from '@/composables/useNewGame'
import ChatBranches from '@/services/chatBranches.js'

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
const { appearanceOpen, appSettingsOpen, presetsOpen, worldbookOpen, charactersOpen, personaOpen, regexOpen, aiConfigOpen, togglePanel, closeAllPanels } = usePanels()

// 右侧列表面板是否有任一打开（用于显示半透明遮罩：浅色=白、深色=黑）
const anyPanelOpen = computed(() =>
  showSidebar.value && (
    appearanceOpen.value ||
    appSettingsOpen.value ||
    presetsOpen.value ||
    worldbookOpen.value ||
    charactersOpen.value ||
    personaOpen.value ||
    regexOpen.value ||
    aiConfigOpen.value
  )
)

const { updateHomeMenuInk } = useHomeMenuInk(() => view.value === 'start')
const { playHomeBgFX, playThreadedBgFX, playSandboxBgFX } = useBackgroundFx()

 const {
   viewModalOpen,
   viewModalTitle,
   viewModalType,
   viewModalData,
   viewModalLoading,
   viewModalError,
   viewModalFile,
   currentPresetData,
   openViewModal,
   closeViewModal,
 } = useViewModal()

 // 主页功能模态（Load / Gallery / Options）
 const { homeModalOpen, homeModalTitle, homeModalType, openHomeModal, closeHomeModal } = useHomeModal()

 // 主题模式：system/dark/light（跟随系统 + 持久化 + 同步 ThemeManager）
 const { theme, initTheme, onThemeUpdate: __onThemeUpdateMode, applyTheme } = useThemeMode()
 // UI 资产（图标/Flowbite）加载与刷新
 const { ensureUIAssets, refreshIcons } = useUiAssets()

 /* New Game 模态：新建对话（组合式 useNewGame 管理表单状态与行为） */
 const { newGameOpen, openNewGame, cancelNewGame, onNewChatConfirm } = useNewGame({
   setView: (v) => { if (v === 'threaded' || v === 'sandbox' || v === 'start') { view.value = v } },
   refreshIcons,
 })

// 当侧边栏抽屉关闭时，同步关闭右侧“应用设置”面板，保持同层同生命周期
watch(drawerOpen, (v) => {
  if (!v) {
    closeAllPanels()
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



 // 楼层对话消息（仅用于 Threaded 页面），确认存档后由后端数据填充
 const currentThreadMessages = ref([])


onMounted(() => {
  initTheme()

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
  __onThemeUpdateMode(t)
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
 * 处理 LoadGame 的确认：
 * - 调用后端 openai_messages，传入文件路径
 * - 将返回的 {role, content} 映射为楼层对话的消息结构
 * - 关闭模态并切换到 threaded 视图
 */
async function onLoadGameConfirm(file) {
  try {
    // 拉取 OAI 消息
    const result = await ChatBranches.openaiMessagesByFile(file)
    const arr = Array.isArray(result?.messages) ? result.messages : []
    // 映射为 ThreadedChatPreview 所需的消息结构（带 id）
    const mapped = arr.map((m, idx) => ({
      id: Date.now() + idx,
      role: (m.role === 'user' || m.role === 'assistant' || m.role === 'system') ? m.role : 'system',
      content: String(m.content ?? '')
    }))
    // 更新并切换视图
    currentThreadMessages.value = mapped.length ? mapped : [{ id: Date.now(), role: 'system', content: '（空对话）' }]
    closeHomeModal()
    view.value = 'threaded'
    nextTick(() => refreshIcons())
  } catch (e) {
    // 失败时保底：保持原消息并提示
    console.error('openai_messages 调用失败:', e)
    closeHomeModal()
  }
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
          @openAppearance="togglePanel('appearance')"
          @openAppSettings="togglePanel('appSettings')"
          @openPresets="togglePanel('presets')"
          @openWorldbook="togglePanel('worldbook')"
          @openCharacters="togglePanel('characters')"
          @openPersona="togglePanel('persona')"
          @openRegex="togglePanel('regex')"
          @openAIConfig="togglePanel('aiConfig')"
        />
      </SidebarDrawer>
    </template>

    <template #overlays>
      <transition name="st-panel-backdrop">
        <div v-if="anyPanelOpen" class="st-panel-backdrop" @click="closeAllPanels()"></div>
      </transition>
      
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

    
    
    <StartView
      v-if="view === 'start'"
      @new-game="openNewGame"
      @open-load="openHomeModal('load')"
      @open-gallery="openHomeModal('gallery')"
      @open-options="openHomeModal('options')"
    />

    
    <ThreadedView v-else-if="view === 'threaded'" :messages="currentThreadMessages" />

    
    <SandboxView v-else />

    
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
      icon="swords"
      @confirm="onNewChatConfirm"
      @close="cancelNewGame"
    />

    
    <LoadGameModal
      :show="homeModalOpen && homeModalType === 'load'"
      :title="homeModalTitle || '读取存档'"
      icon="history"
      @confirm="onLoadGameConfirm"
      @update:show="(v) => { if (!v) closeHomeModal() }"
      @close="closeHomeModal"
    />
    <GalleryModal
      :show="homeModalOpen && homeModalType === 'gallery'"
      :title="homeModalTitle || '画廊'"
      icon="image"
      @update:show="(v) => { if (!v) closeHomeModal() }"
      @close="closeHomeModal"
    />
    <OptionsModal
      :show="homeModalOpen && homeModalType === 'options'"
      :title="homeModalTitle || '选项'"
      icon="settings"
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




/* 子页面展开/收起动画（AppearancePanel 组件在 App 层的过渡） */
.st-subpage-enter-from { opacity: 0; transform: translateX(-10px) scale(0.98); filter: blur(4px); }
.st-subpage-leave-to   { opacity: 0; transform: translateX(-12px) scale(0.98); filter: blur(4px); }
.st-subpage-enter-active,
.st-subpage-leave-active { transition: opacity .2s ease, transform .24s cubic-bezier(.22,.61,.36,1), filter .24s ease; }

/* 右侧列表面板背板：浅色=白半透明，深色=黑半透明（由 --st-overlay-ink 控制） */
.st-panel-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(var(--st-overlay-ink), 0.18);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 58; /* 低于各面板(59)，高于内容 */
}
/* 背板淡入淡出动画 */
.st-panel-backdrop-enter-from,
.st-panel-backdrop-leave-to { opacity: 0; }
.st-panel-backdrop-enter-active,
.st-panel-backdrop-leave-active { transition: opacity .18s ease; }

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
