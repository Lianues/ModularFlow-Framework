<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import HtmlIframeSandbox from '@/components/sandbox/HtmlIframeSandbox.vue'
/**
 * 楼层对话预览（美化版）
 * 布局：头像占位 + 名称/角色 + 对话内容 + 楼层序号（#）
 * - 不依赖外部数据，仅美化现有 props.messages（id/role/content）
 * - 使用 Design Tokens，响应式与玻璃拟态风格
 * - data-scope/data-part 保持稳定选择器契约（便于主题包覆盖）
 * - 使用自定义滚动条替代原生滚动条
 */
const props = defineProps({
  messages: {
    type: Array,
    default: () => ([
      { id: 1, role: 'system', content: '欢迎来到 SmartTavern。' },
      { id: 2, role: 'user', content: '你好，介绍一下你自己？' },
      { id: 3, role: 'assistant', content: '我是一个对话助手，帮助你完成任务。' },
    ])
  }
})

const roleMap = {
  user: '用户',
  assistant: '助手',
  system: '系统',
}

function roleLabel(role) {
  return roleMap[role] ?? '未知'
}
function nameOf(msg) {
  // 名称占位规则：优先角色映射；可拓展为从 msg.meta 中读取昵称
  return roleLabel(msg.role)
}

/* 智能色条：根据头像图片/角色生成渐变色 */
const palettes = ref({}) // id -> { start, end }

function clamp(v, min = 0, max = 255) { return Math.max(min, Math.min(max, v)) }
function lighten(rgb, amt = 24) {
  return { r: clamp(rgb.r + amt), g: clamp(rgb.g + amt), b: clamp(rgb.b + amt) }
}
function rgbToCss(rgb, a = 1) { return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${a})` }

function roleFallback(role) {
  // 角色回退配色（亮/暗主题下仍然清晰）
  if (role === 'assistant') return { start: 'rgba(14,165,233,1)', end: 'rgba(94,234,212,1)' }
  if (role === 'system')    return { start: 'rgba(251,191,36,1)', end: 'rgba(253,230,138,1)' }
  // user 回退使用主题主色-强调色
  return { start: 'rgb(var(--st-primary))', end: 'rgb(var(--st-accent))' }
}

async function extractPaletteFromImage(url) {
  return new Promise((resolve) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas')
        const w = canvas.width = 24
        const h = canvas.height = 24
        const ctx = canvas.getContext('2d', { willReadFrequently: true })
        ctx.drawImage(img, 0, 0, w, h)
        const data = ctx.getImageData(0, 0, w, h).data
        let r = 0, g = 0, b = 0, count = 0
        for (let i = 0; i < data.length; i += 4) {
          const a = data[i + 3]
          if (a < 32) continue // 忽略透明像素
          r += data[i]; g += data[i + 1]; b += data[i + 2]; count++
        }
        if (count === 0) throw new Error('no pixels')
        r = Math.round(r / count); g = Math.round(g / count); b = Math.round(b / count)
        const start = rgbToCss({ r, g, b })
        const end = rgbToCss(lighten({ r, g, b }, 28))
        resolve({ start, end })
      } catch (_) {
        resolve(null)
      }
    }
    img.onerror = () => resolve(null)
    img.src = url
  })
}

async function ensurePaletteFor(msg) {
  // 约定：若消息含 avatarUrl，则尝试从图片提取主色；否则按角色回退
  let pal = null
  if (msg.avatarUrl) {
    pal = await extractPaletteFromImage(msg.avatarUrl)
  }
  if (!pal) pal = roleFallback(msg.role)
  palettes.value[msg.id] = pal
}

function stripeStyle(msg) {
  const pal = palettes.value[msg.id] || roleFallback(msg.role)
  return {
    '--stripe-start': pal.start,
    '--stripe-end': pal.end,
  }
}

// Lucide 图标刷新（局部调用，避免 race）
function refreshIcons() {
  nextTick(() => {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons()
    }
    if (typeof window.initFlowbite === 'function') {
      try { window.initFlowbite() } catch (_) {}
    }
  })
}

// 选项菜单状态
const activeMenu = ref(null)
const copiedState = ref({})
function isCopied(id) { return !!copiedState.value[id] }
function markCopied(id) {
  copiedState.value[id] = true
  refreshIcons()
  setTimeout(() => {
    copiedState.value[id] = false
    refreshIcons()
  }, 1600)
}

function toggleMenu(msgId) {
  activeMenu.value = activeMenu.value === msgId ? null : msgId
  refreshIcons()
}

function copyMessage(msg) {
  navigator.clipboard.writeText(msg.content).then(() => {
    activeMenu.value = null
    markCopied(msg.id)
  })
}

function deleteMessage(msgId) {
  const idx = props.messages.findIndex(m => m.id === msgId)
  if (idx >= 0) {
    props.messages.splice(idx, 1)
  }
  activeMenu.value = null
}

// 全局点击监听：关闭菜单
function handleGlobalClick(e) {
  // 检查点击是否在菜单按钮或菜单内部
  const menuWrapper = e.target.closest('.menu-wrapper')
  if (!menuWrapper) {
    activeMenu.value = null
  }
}

// 监听菜单状态，添加/移除全局点击监听
watch(activeMenu, (newVal) => {
  if (newVal !== null) {
    // 菜单打开，添加监听器（下一帧，避免立即触发）
    nextTick(() => {
      document.addEventListener('click', handleGlobalClick)
    })
  } else {
    // 菜单关闭，移除监听器
    document.removeEventListener('click', handleGlobalClick)
  }
  refreshIcons()
  // 初始化为现有消息生成色条调色板
  props.messages.forEach(m => { ensurePaletteFor(m) })
})

// 组件卸载时清理
onBeforeUnmount(() => {
  document.removeEventListener('click', handleGlobalClick)
})

// 分支切换（演示功能）
const activeBranch = ref(1)
const totalBranches = ref(2)

function switchBranch(direction) {
  if (direction === 'left' && activeBranch.value > 1) {
    activeBranch.value--
  } else if (direction === 'right' && activeBranch.value < totalBranches.value) {
    activeBranch.value++
  }
  console.log(`切换到分支 ${activeBranch.value}/${totalBranches.value}`)
}

/* 输入框逻辑 */
const inputText = ref('')
const messageListRef = ref(null)
const inputRef = ref(null)
let removeWheel = null

onMounted(() => {
  // 首次挂载后强制更新滚动条（确保容器尺寸已稳定）
  messageListRef.value?.update?.()

  // 在 chat-unified 与 main 区域（包括空白处）使用滚轮也能滚动消息列表
  const chatUnified = document.querySelector('[data-scope="chat-unified"]')
  const mainArea = document.querySelector('[data-scope="main"]')
  const wheelHandler = (e) => {
    const container = messageListRef.value?.$el?.querySelector('.scroll-container')
    if (!container) return
    // 如果事件来源本就在列表容器内，让原生滚动处理
    if (container.contains(e.target)) return
    // 位于聊天统一区域或主区域空白时，拦截并转发滚动到消息容器
    const inChatUnified = chatUnified && chatUnified.contains(e.target)
    const inMainArea = mainArea && mainArea.contains(e.target)
    if (inChatUnified || inMainArea) {
      container.scrollTop += e.deltaY
      e.preventDefault()
    }
  }
  chatUnified?.addEventListener('wheel', wheelHandler, { passive: false })
  mainArea?.addEventListener('wheel', wheelHandler, { passive: false })
  removeWheel = () => {
    chatUnified?.removeEventListener('wheel', wheelHandler)
    mainArea?.removeEventListener('wheel', wheelHandler)
  }
  refreshIcons()
  // 初始化现有消息的智能色条调色板（若有头像则提取主色）
  props.messages.forEach(m => { ensurePaletteFor(m) })
})

onBeforeUnmount(() => {
  removeWheel?.()
  if (pendingTimer) { clearTimeout(pendingTimer); pendingTimer = null }
  if (pendingInterval) { clearInterval(pendingInterval); pendingInterval = null }
})

watch(() => props.messages.length, () => {
  // 消息数量变化后，下一拍更新滚动条
  nextTick(() => {
    messageListRef.value?.update?.()
    refreshIcons()
  })
})

function sendMessage() {
  const text = inputText.value.trim()
  if (!text) return
  
  // 创建新消息
  const newMessage = {
    id: Date.now(), // 简单的ID生成
    role: 'user',
    content: text
  }
  
  // 若等待中则直接返回（不允许再次发送）
  if (pendingMessageId?.value) return

  // 添加到消息列表
  props.messages.push(newMessage)
  // 为新消息生成色条调色板（若有头像则尝试提取主色）
  ensurePaletteFor(newMessage)
  // 启动 10 秒等待占位
  startPendingFor(newMessage.id)
  
  // 清空输入框
  inputText.value = ''
  
  // 滚动到底部（丝滑且自然）
  nextTick(() => {
    setTimeout(() => {
      if (messageListRef.value?.$el) {
        const container = messageListRef.value.$el.querySelector('.scroll-container')
        if (container) {
          // 优先使用原生平滑滚动
          try {
            container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
          } catch (_) {
            // 回退：rAF 动画
            const start = container.scrollTop
            const end = container.scrollHeight
            const dur = 420
            const t0 = performance.now()
            const ease = t => 1 - Math.pow(1 - t, 3) // easeOutCubic
            const step = (now) => {
              const p = Math.min(1, (now - t0) / dur)
              container.scrollTop = start + (end - start) * ease(p)
              if (p < 1) requestAnimationFrame(step)
            }
            requestAnimationFrame(step)
          }
        }
      }
    }, 60)
  })
}

// 输入行为：Enter 发送，Shift+Enter 换行（遵循 UI 规范）
function onKeydown(e) {
  if (pendingMessageId?.value) {
    // 等待中不允许再次发送（允许输入编辑）
    if (e.key === 'Enter' && !e.shiftKey) e.preventDefault()
    return
  }
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

/* 快捷操作（编辑/再生），更多行为可接入后端 */
function startEdit(msg) {
  inputText.value = msg.content
  nextTick(() => inputRef.value?.focus?.())
}
function regenerateMessage(msg) {
  console.log('请求重新生成：', msg.id)
}

/* 发送后等待占位：10 秒等待动画 + 禁止再次发送，支持手动停止 */
const pendingMessageId = ref(null)
const pendingSeconds = ref(0)
let pendingTimer = null
let pendingInterval = null

function startPendingFor(id) {
  // 先清理旧等待
  if (pendingTimer) { clearTimeout(pendingTimer); pendingTimer = null }
  if (pendingInterval) { clearInterval(pendingInterval); pendingInterval = null }
  
  pendingMessageId.value = id
  pendingSeconds.value = 0
  refreshIcons()
  
  // 每100ms更新一次正数计时显示（从0递增至10）
  const startTime = Date.now()
  const duration = 10000
  pendingInterval = setInterval(() => {
    const elapsed = Date.now() - startTime
    const current = Math.min(10, Math.floor(elapsed / 1000))
    pendingSeconds.value = current
    if (current >= 10) {
      clearInterval(pendingInterval)
      pendingInterval = null
    }
  }, 100)
  
  // 10秒后自动完成
  pendingTimer = setTimeout(() => {
    if (pendingInterval) { clearInterval(pendingInterval); pendingInterval = null }
    pendingMessageId.value = null
    pendingTimer = null
    refreshIcons()
  }, 10000)
}

function cancelPending() {
  if (pendingTimer) { clearTimeout(pendingTimer); pendingTimer = null }
  if (pendingInterval) { clearInterval(pendingInterval); pendingInterval = null }
  pendingMessageId.value = null
  pendingSeconds.value = 0
  refreshIcons()
}

// 基于 DOCTYPE 检测 HTML 文档代码块（支持 ```html/```HTML/``` 或纯文本包含 <!DOCTYPE html>）
const HTML_DOC_RE = /<!DOCTYPE\s+html/i
const FENCE_RE = /```(?:html|HTML)?\s*([\s\S]*?)```/i

function extractHtmlDocFromText(text) {
  if (!text || typeof text !== 'string') return ''
  const fence = text.match(FENCE_RE)
  if (fence && fence[1] && HTML_DOC_RE.test(fence[1])) {
    return fence[1].trim()
  }
  if (HTML_DOC_RE.test(text)) {
    return text.trim()
  }
  return ''
}
function hasHtmlDoc(msg) { return !!extractHtmlDocFromText(msg.content) }
function getHtmlDoc(msg) { return extractHtmlDocFromText(msg.content) }
</script>

<template>
  <div data-scope="chat-threaded" class="tch-container">
    <CustomScrollbar
      class="tch-list"
      ref="messageListRef"
      :width="8"
    >
      <div data-scope="message-list" class="tch-list-inner">
        <transition-group name="msg" tag="div">
          <article
            v-for="(m, idx) in props.messages"
            :key="m.id"
            data-scope="message-item"
            :data-role="m.role"
            class="floor-card glass"
            :style="stripeStyle(m)"
          >
          <div class="floor-layout">
            <!-- 左侧：头像、徽章、楼层号 -->
            <div class="floor-left">
              <div class="avatar role-user" v-if="m.role === 'user'">
                <span class="avatar-letter">{{ nameOf(m).charAt(0) }}</span>
              </div>
              <div class="avatar role-assistant" v-else-if="m.role === 'assistant'">
                <span class="avatar-letter">{{ nameOf(m).charAt(0) }}</span>
              </div>
              <div class="avatar role-system" v-else>
                <span class="avatar-letter">{{ nameOf(m).charAt(0) }}</span>
              </div>
              <div class="role-badge">{{ roleLabel(m.role) }}</div>
              <div class="floor-index-left" :title="'楼层序号'">#{{ idx + 1 }}</div>
            </div>

            <!-- 右侧：消息内容 -->
            <div class="floor-right">
              <header class="floor-header">
                <div class="name">{{ nameOf(m) }}</div>
                <!-- 右侧区：等待chip + 更多操作按钮 -->
                <div class="header-right">
                  <!-- 等待占位动画：右对齐，更多操作按钮左侧 -->
                  <div v-if="pendingMessageId === m.id" class="pending-chip" aria-live="polite">
                    <span class="chip-spinner" aria-hidden="true"></span>
                    <span class="chip-text">等待中...{{ pendingSeconds }}s</span>
                  </div>
                  <!-- 三点菜单按钮 -->
                  <div class="menu-wrapper">
                  <button
                    class="menu-btn"
                    @click.stop="toggleMenu(m.id)"
                    :aria-expanded="activeMenu === m.id"
                    aria-label="更多操作"
                    title="更多操作"
                  >
                    <i data-lucide="more-vertical" class="icon-16" aria-hidden="true"></i>
                    <span class="sr-only">更多</span>
                  </button>
                  <!-- 选项菜单（向左弹出） -->
                  <transition name="menu-slide">
                    <div v-if="activeMenu === m.id" class="menu-dropdown">
                      <button class="menu-item" @click="copyMessage(m)">
                        <i data-lucide="copy" class="icon-14" aria-hidden="true"></i>
                        复制
                      </button>
                      <button
                        v-if="idx === props.messages.length - 1"
                        class="menu-item menu-danger"
                        @click="deleteMessage(m.id)"
                      >
                        <i data-lucide="trash-2" class="icon-14" aria-hidden="true"></i>
                        删除
                      </button>
                    </div>
                  </transition>
                  </div>
                </div>
              </header>
              <section data-part="content" class="floor-content">
                <template v-if="hasHtmlDoc(m)">
                  <!-- 楼层内 iframe 舞台（宽度百分比受 --st-threaded-stage-maxw 控制，不超过消息宽度） -->
                  <div class="floor-html-stage">
                    <div class="floor-html-stage-inner">
                      <HtmlIframeSandbox :html="getHtmlDoc(m)" />
                    </div>
                  </div>
                </template>
                <template v-else>
                  {{ m.content }}
                </template>
              </section>
              
              <!-- 楼层页脚：左侧操作按钮 + 右侧分支切换（同一行） -->
              <div class="floor-footer">
                <div class="floor-actions">
                  <transition name="copy-tip">
                    <div v-if="isCopied(m.id)" class="copy-tip">已复制</div>
                  </transition>

                  <button class="act-btn" :class="{ success: isCopied(m.id) }" @click="copyMessage(m)" :title="isCopied(m.id) ? '已复制' : '复制'" :aria-label="isCopied(m.id) ? '已复制' : '复制'">
                    <i :data-lucide="isCopied(m.id) ? 'check' : 'copy'" class="icon-16" aria-hidden="true"></i>
                  </button>
                  <button class="act-btn" @click="regenerateMessage(m)" title="重试" aria-label="重试">
                    <i data-lucide="refresh-cw" class="icon-16" aria-hidden="true"></i>
                  </button>
                  <button class="act-btn" @click="startEdit(m)" title="编辑" aria-label="编辑">
                    <i data-lucide="pencil" class="icon-16" aria-hidden="true"></i>
                  </button>
                </div>

                <div v-if="idx === props.messages.length - 1 && totalBranches > 1" class="branch-switcher">
                  <button
                    class="branch-btn"
                    @click="switchBranch('left')"
                    :disabled="activeBranch <= 1"
                    title="上一个分支"
                    aria-label="上一个分支"
                  >
                    <i data-lucide="chevron-left" class="icon-16" aria-hidden="true"></i>
                  </button>
                  <span class="branch-indicator">{{ activeBranch }}/{{ totalBranches }}</span>
                  <button
                    class="branch-btn"
                    @click="switchBranch('right')"
                    :disabled="activeBranch >= totalBranches"
                    title="下一个分支"
                    aria-label="下一个分支"
                  >
                    <i data-lucide="chevron-right" class="icon-16" aria-hidden="true"></i>
                  </button>
                </div>
              </div>
            </div>
            </div>


          </article>
        </transition-group>
      </div>
    </CustomScrollbar>

    <!-- 输入区（多行文本，玻璃拟态容器 + 工具栏 + Lucide 图标） -->
    <div class="tch-input-row glass">
      <div class="tch-tools-left">
        <button class="tool-btn round" title="拓展" aria-label="拓展" data-tooltip-target="tt-expand">
          <i data-lucide="plus" class="icon-16" aria-hidden="true"></i>
        </button>
        <div id="tt-expand" role="tooltip" class="absolute z-10 invisible inline-block px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded-md shadow-sm opacity-0 tooltip">
          拓展
          <div class="tooltip-arrow" data-popper-arrow></div>
        </div>
      </div>
      <textarea
        ref="inputRef"
        v-model="inputText"
        class="tch-input"
        placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
        @keydown="onKeydown"
      ></textarea>
      <div class="tch-tools-right">
        <button
          class="tch-send"
          :disabled="pendingMessageId ? false : !inputText.trim()"
          @click="pendingMessageId ? cancelPending() : sendMessage()"
          :title="pendingMessageId ? '停止等待' : '发送 (Enter)'"
          :aria-label="pendingMessageId ? '停止等待' : '发送'"
          data-tooltip-target="tt-send"
        >
          <i :data-lucide="pendingMessageId ? 'square' : 'send'" class="icon-16" aria-hidden="true"></i>
          <span class="tch-send-text">{{ pendingMessageId ? '停止' : '发送' }}</span>
        </button>
        <div id="tt-send" role="tooltip" class="absolute z-10 invisible inline-block px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded-md shadow-sm opacity-0 tooltip">
          发送
          <div class="tooltip-arrow" data-popper-arrow></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 容器布局 */
.tch-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

/* 滚动列表容器（CustomScrollbar占位） */
.tch-list {
  flex: 1;
  min-height: 0;
  padding: 8px;
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: var(--st-radius-lg);
  background: rgba(var(--st-surface), 0.62);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  box-shadow: var(--st-shadow-sm);
  overflow: visible;
}

/* 内部容器（供过渡动画使用） */
.tch-list-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 4px;
  padding-bottom: 24px;
}

/* 楼层卡（玻璃拟态） */
.floor-card {
  padding: 12px;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(var(--st-surface), 0.82);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  box-shadow: none;
  overflow: visible; /* 确保伪元素色条与悬浮阴影不被裁剪 */
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease, border-color .18s ease;
  will-change: transform, opacity, filter;
}
.floor-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(0,0,0,0.10);
  border-color: rgba(var(--st-primary), 0.35);
  background: rgba(var(--st-surface), 0.88);
  z-index: 2;
}

/* 智能渐变色条（变量驱动，带柔和光晕），assistant/system 左侧，user 右侧 */
.floor-card { position: relative; }

.floor-card::before,
.floor-card::after {
  content: '';
  position: absolute;
  top: 0; bottom: 0;
  width: 8px;
  pointer-events: none;
  z-index: 1;
}

/* 主色条（渐变） - 默认左侧 */
.floor-card::before {
  left: 0;
  border-top-left-radius: var(--st-radius-lg);
  border-bottom-left-radius: var(--st-radius-lg);
  background: linear-gradient(180deg,
    var(--stripe-start, rgb(var(--st-primary))),
    var(--stripe-end,   rgb(var(--st-accent))));
  box-shadow: 0 0 0 1px rgba(0,0,0,0.02) inset;
}

/* 柔光外晕（与主色一致，增强高级感） */
.floor-card::after {
  left: 0;
  filter: blur(12px);
  opacity: .28;
  background: linear-gradient(180deg,
    var(--stripe-start, rgb(var(--st-primary))),
    transparent 72%);
}

/* 用户在右侧显示色条与光晕 */
.floor-card[data-role="user"]::before {
  left: auto; right: 0;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-top-right-radius: var(--st-radius-lg);
  border-bottom-right-radius: var(--st-radius-lg);
}
.floor-card[data-role="user"]::after {
  left: auto; right: 0;
}

/* 悬浮时层级提升，避免被相邻元素/容器遮挡（阴影在 .floor-card:hover） */
.floor-card:hover { z-index: 2; }

/* 楼层布局：左侧头像+徽章，右侧名称+楼层+内容 */
.floor-layout {
  display: flex;
  gap: 12px;
}

/* 左侧区域 */
.floor-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 右侧区域 */
.floor-right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 楼层头部：名称和楼层号 */
.floor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.header-right {
  display: inline-flex;
  align-items: center;
  gap: 0; /* chip 的 margin-right 会提供间隔 */
}
.avatar {
  width: var(--st-avatar-size, 56px);
  height: var(--st-avatar-size, 56px);
  border-radius: var(--st-radius-lg);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--st-primary-contrast);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.25), 0 6px 14px rgba(0,0,0,0.08);
  user-select: none;
}
.avatar-letter {
  font-weight: 700;
  font-size: calc(var(--st-avatar-size, 56px) * 0.36);
  text-transform: uppercase;
}

/* 头像占位渐变（不同角色差异） */
.role-user {
  background: linear-gradient(135deg, rgba(59,130,246,0.85), rgba(99,102,241,0.85));
}
.role-assistant {
  background: linear-gradient(135deg, rgba(14,165,233,0.85), rgba(94,234,212,0.85));
}
.role-system {
  background: linear-gradient(135deg, rgba(251,191,36,0.85), rgba(253,230,138,0.85));
}

.name {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  font-size: var(--st-name-font-size, 16px);
}

.role-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--st-badge-font-size, 11px);
  color: rgb(var(--st-color-text));
  background: rgba(var(--st-primary),0.12);
  border: 1px solid rgba(var(--st-primary),0.32);
  border-radius: 9999px;
  padding: 4px 8px;
  white-space: nowrap;
  text-align: center;
}

.floor-index-left {
  font-weight: 700;
  color: rgba(var(--st-color-text), 0.6);
  letter-spacing: .3px;
  font-size: var(--st-floor-font-size, 14px);
  text-align: center;
  margin-top: 4px;
}

/* 楼层内容 */
.floor-content {
  color: rgba(var(--st-color-text), 0.95);
  font-size: var(--st-content-font-size, 18px);
  line-height: 1.75;
  letter-spacing: .2px;
  word-break: break-word;
  white-space: pre-wrap;
}
.floor-content p { margin: 0; }
.floor-content p + p { margin-top: 8px; }
.floor-content a {
  color: rgb(var(--st-primary));
  text-decoration: none;
  border-bottom: 1px dashed rgba(var(--st-primary), 0.4);
}
.floor-content a:hover { text-decoration: underline; }
.floor-content code {
  font-family: var(--st-font-mono);
  background: rgba(var(--st-color-text), 0.06);
  padding: 0 4px;
  border-radius: var(--st-radius-sm);
}
[data-theme="dark"] .floor-content code {
  background: rgba(var(--st-color-text), 0.14);
}

/* 三点菜单 */
.menu-wrapper {
  position: relative;
}

.menu-btn {
  appearance: none;
  background: transparent;
  border: 1px solid rgba(var(--st-border), 0.6);
  color: rgba(var(--st-color-text), 0.6);
  width: 28px;
  height: 28px;
  border-radius: var(--st-radius-lg);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
  transition: all .18s cubic-bezier(.22,.61,.36,1);
}

.menu-btn:hover {
  background: rgba(var(--st-surface-2), 0.8);
  border-color: rgba(var(--st-border), 0.9);
  color: rgba(var(--st-color-text), 0.9);
}

.menu-dropdown {
  position: absolute;
  right: 100%;
  top: 0;
  margin-right: 8px;
  background: rgb(var(--st-surface));
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: var(--st-radius-lg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  padding: 4px;
  min-width: 120px;
  z-index: 10;
}

.menu-item {
  appearance: none;
  background: transparent;
  border: none;
  width: 100%;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgb(var(--st-color-text));
  transition: background .18s cubic-bezier(.22,.61,.36,1);
  text-align: left;
}

.menu-item:hover {
  background: rgba(var(--st-surface-2), 0.8);
}

.menu-item.menu-danger {
  color: rgb(220, 38, 38);
}

.menu-item.menu-danger:hover {
  background: rgba(220, 38, 38, 0.08);
}

.menu-icon {
  font-size: 14px;
}
/* icon utilities */
.icon-14 { width: 14px; height: 14px; stroke: currentColor; }
.icon-16 { width: 16px; height: 16px; stroke: currentColor; }
/* a11y helper */
.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0);
  white-space: nowrap; border: 0;
}

/* 菜单弹出动画 */
.menu-slide-enter-active,
.menu-slide-leave-active {
  transition: opacity 0.15s ease, transform 0.2s cubic-bezier(0.22, 0.61, 0.36, 1);
}

.menu-slide-enter-from,
.menu-slide-leave-to {
  opacity: 0;
  transform: translateX(8px) scale(0.95);
}

/* 分支切换器（放在页脚右侧） */
.branch-switcher {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.branch-btn {
  appearance: none;
  background: rgba(var(--st-primary), 0.08);
  border: 1px solid rgba(var(--st-primary), 0.3);
  color: rgb(var(--st-primary));
  width: 32px;
  height: 32px;
  border-radius: var(--st-radius-lg);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all .18s cubic-bezier(.22,.61,.36,1);
}

.branch-btn:hover:not(:disabled) {
  background: rgba(var(--st-primary), 0.15);
  border-color: rgba(var(--st-primary), 0.5);
  transform: translateY(-1px);
}

.branch-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.branch-indicator {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--st-color-text), 0.75);
  padding: 0 8px;
}

/* 楼层页脚行（左操作 + 右分支） */
.floor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(var(--st-border), 0.3);
}

/* 楼层内操作按钮行（悬浮显示，居左） */
.floor-actions {
  position: relative;
  display: flex;
  justify-content: flex-start;
  gap: 8px;
  opacity: 0;
  transform: translateY(4px);
  transition: opacity .18s cubic-bezier(.22,.61,.36,1), transform .2s cubic-bezier(.22,.61,.36,1);
}
.floor-card:hover .floor-actions {
  opacity: 1;
  transform: translateY(0);
}

/* 操作按钮样式（与工具按钮一致的设计语言） */
.act-btn {
  appearance: none;
  background: rgba(var(--st-surface-2), 0.6);
  border: 1px solid rgba(var(--st-border), 0.9);
  color: rgba(var(--st-color-text), 0.8);
  border-radius: var(--st-radius-md);
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background .18s cubic-bezier(.22,.61,.36,1), border-color .18s cubic-bezier(.22,.61,.36,1), transform .18s cubic-bezier(.22,.61,.36,1), box-shadow .18s cubic-bezier(.22,.61,.36,1);
}
.act-btn:hover {
  background: rgba(var(--st-surface-2), 0.9);
  border-color: rgba(var(--st-border), 1);
  transform: translateY(-1px);
}
.act-btn:active {
  transform: translateY(0);
}
.act-btn.ghost {
  background: transparent;
  border-color: rgba(var(--st-border), 0.8);
}
.act-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(var(--st-primary), 0.14);
  border-color: rgba(var(--st-primary), 0.6);
}

/* 成功态复制按钮 */
.act-btn.success {
  background: linear-gradient(135deg, rgba(var(--st-accent),1), rgba(var(--st-primary),1));
  color: var(--st-primary-contrast);
  border-color: transparent;
  box-shadow: 0 8px 18px rgba(0,0,0,0.12);
  transform: translateY(-1px);
}
.act-btn.success:hover {
  filter: saturate(1.05) brightness(1.03);
}

/* 复制提示气泡 */
.copy-tip {
  position: absolute;
  left: 0;
  bottom: calc(100% + 6px);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: 9999px;
  background: rgba(var(--st-surface), 0.86);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: rgba(var(--st-color-text), 0.95);
  box-shadow: var(--st-shadow-sm);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .2px;
  pointer-events: none;
  z-index: 2;
}

/* 复制提示动效 */
.copy-tip-enter-from,
.copy-tip-leave-to { opacity: 0; transform: translateY(4px); }
.copy-tip-enter-active,
.copy-tip-leave-active { transition: opacity .18s ease, transform .2s cubic-bezier(.22,.61,.36,1); }

/* 输入行（玻璃拟态输入容器） */
.tch-input-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: var(--st-radius-lg);
  background: rgba(var(--st-surface), 0.80);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  box-shadow: var(--st-shadow-sm);
  flex-shrink: 0;
  min-height: clamp(calc(var(--st-content-font-size) * 2.8 + 28px), var(--st-input-height, 100px), 100vh);
  transition: box-shadow .2s cubic-bezier(.22,.61,.36,1), border-color .2s cubic-bezier(.22,.61,.36,1), background .2s cubic-bezier(.22,.61,.36,1), transform .2s cubic-bezier(.22,.61,.36,1);
}
.tch-input-row:focus-within {
  border-color: rgba(var(--st-primary), 0.45);
  box-shadow: 0 8px 30px rgba(0,0,0,0.08), 0 0 0 3px rgba(var(--st-primary), 0.08);
  background: rgba(var(--st-surface), 0.86);
}

/* 工具栏按钮 */
.tch-tools-left,
.tch-tools-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.tool-btn {
  appearance: none;
  background: rgba(var(--st-surface-2), 0.6);
  border: 1px solid rgba(var(--st-border), 0.9);
  color: rgba(var(--st-color-text), 0.8);
  border-radius: var(--st-radius-md);
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background .18s cubic-bezier(.22,.61,.36,1), border-color .18s cubic-bezier(.22,.61,.36,1), transform .18s cubic-bezier(.22,.61,.36,1), box-shadow .18s cubic-bezier(.22,.61,.36,1);
}
.tool-btn:hover {
  background: rgba(var(--st-surface-2), 0.9);
  border-color: rgba(var(--st-border), 1);
  transform: translateY(-1px);
}
.tool-btn:active {
  transform: translateY(0);
}
.tool-btn.ghost {
  background: transparent;
  border-color: rgba(var(--st-border), 0.8);
}
/* 圆形拓展按钮 */
.tool-btn.round {
  border-radius: 9999px;
  width: 36px;
  height: 36px;
}

.tool-btn:focus-visible,
.menu-btn:focus-visible,
.tch-send:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(var(--st-primary), 0.14);
  border-color: rgba(var(--st-primary), 0.6);
}

/* 多行输入区域 */
.tch-input {
  width: 100%;
  min-height: calc(var(--st-content-font-size) * 2.2 + 12px);
  padding: 10px 2px;
  border: none;
  border-radius: 0;
  background: transparent;
  color: rgb(var(--st-color-text));
  caret-color: rgb(var(--st-color-text));
  font-family: var(--st-font-body);
  font-size: var(--st-content-font-size);
  line-height: 1.6;
  resize: none;
  overflow-y: auto;
  box-sizing: border-box;
}
.tch-input::placeholder {
  color: rgba(var(--st-color-text), 0.45);
  font-size: var(--st-content-font-size);
}
.tch-input:focus {
  outline: none;
}

/* 发送按钮 */
.tch-send {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--st-radius-md);
  background: linear-gradient(135deg, rgba(var(--st-primary),1), rgba(var(--st-accent),1));
  color: var(--st-primary-contrast);
  border: 1px solid transparent;
  cursor: pointer;
  height: 36px;
  box-sizing: border-box;
  transition: filter .18s cubic-bezier(.22,.61,.36,1), transform .18s cubic-bezier(.22,.61,.36,1), box-shadow .18s cubic-bezier(.22,.61,.36,1);
}
.tch-send[aria-label="停止等待"] {
  background: linear-gradient(135deg, rgba(220,38,38,1), rgba(244,63,94,1));
}
.tch-send:hover:enabled {
  filter: saturate(1.08) brightness(1.04);
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(0,0,0,0.10);
}
.tch-send:active:enabled {
  transform: translateY(0);
}
.tch-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(10%);
}

.tch-send-text {
  font-weight: 600;
  letter-spacing: .2px;
}

/* 消息出现/离场与重排过渡（丝滑高质感） */
.msg-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.985);
  filter: blur(8px) saturate(0.9);
}
.msg-enter-to {
  opacity: 1;
  transform: translateY(0) scale(1);
  filter: blur(0);
}
.msg-enter-active {
  transition:
    opacity .28s cubic-bezier(.22,.61,.36,1),
    transform .36s cubic-bezier(.22,.61,.36,1),
    filter .36s ease;
}
.msg-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.985);
  filter: blur(4px);
}
.msg-leave-active {
  transition:
    opacity .18s ease,
    transform .22s ease,
    filter .22s ease;
}
/* 列表重排移动过渡（transition-group v-move） */
.msg-move {
  transition: transform .32s cubic-bezier(.22,.61,.36,1);
  will-change: transform;
}

/* 等待占位动画（右上角 chip，位于更多操作按钮左侧） */
.pending-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: 9999px;
  background: rgba(var(--st-surface), 0.78);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: rgba(var(--st-color-text), 0.9);
  box-shadow: var(--st-shadow-sm);
  margin-right: 8px; /* 与更多菜单按钮分隔 */
}
.chip-spinner {
  width: 12px;
  height: 12px;
  border-radius: 9999px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  animation: st-spin 0.9s linear infinite;
  opacity: 0.9;
}
.chip-text {
  font-size: 12px;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}

/* 等待占位动画（右下角） */
.pending-indicator {
  position: absolute;
  right: 12px;
  bottom: 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: 9999px;
  background: rgba(var(--st-surface), 0.78);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: var(--st-shadow-sm);
  z-index: 3;
}

.fb-spinner {
  width: 14px;
  height: 14px;
  border-radius: 9999px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  animation: st-spin 0.9s linear infinite;
  opacity: 0.9;
}

.pending-text {
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.85);
}

@keyframes st-spin {
  to { transform: rotate(360deg); }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .msg-enter-active,
  .msg-leave-active,
  .msg-move {
    transition: none !important;
  }
  .msg-enter-from,
  .msg-enter-to,
  .msg-leave-to {
    filter: none !important;
    transform: none !important;
  }
}
/* 高级消息出现动画（更自然的入场与微超调），使用更高优先级选择器覆盖默认 */
.floor-card.msg-enter-from {
  opacity: 0;
  transform: translateY(10px) scale(0.985);
  filter: blur(10px) saturate(0.9);
}
.floor-card.msg-enter-to {
  opacity: 1;
  transform: translateY(0) scale(1);
  filter: blur(0);
}
.floor-card.msg-enter-active {
  transition:
    opacity .34s cubic-bezier(.22,.61,.36,1),
    transform .44s cubic-bezier(.22,.61,.36,1),
    filter .44s ease;
  will-change: opacity, transform, filter;
}

/* 轻微阶梯延时：最新的 1~3 条入场动画更靠后，营造自然“瀑布式”感觉 */
[data-scope="message-list"] .floor-card.msg-enter-active:nth-last-child(1) { transition-delay: 24ms; }
[data-scope="message-list"] .floor-card.msg-enter-active:nth-last-child(2) { transition-delay: 48ms; }
[data-scope="message-list"] .floor-card.msg-enter-active:nth-last-child(3) { transition-delay: 72ms; }

/* 楼层内 HTML 舞台（iframe 渲染） */
.floor-html-stage {
  width: min(100%, calc(var(--st-threaded-stage-maxw, 100) * 1%));
  margin: 6px 0;
}
.floor-html-stage-inner {
  position: relative;
  width: 100%;
  aspect-ratio: var(--st-threaded-stage-aspect, 16 / 9);
  padding: var(--st-threaded-stage-padding, 8px);
  border-radius: var(--st-threaded-stage-radius, 12px);
  border: 1px solid rgba(var(--st-border), 0.6);
  background: rgba(var(--st-surface), 0.82);
  box-shadow: var(--st-shadow-sm);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  overflow: hidden;
}
/* 让 HtmlIframeSandbox 内部 iframe 铺满舞台 */
.floor-html-stage-inner :deep(.st-iframe) {
  width: 100%;
  height: 100%;
  display: block;
  border: 0;
}
</style>