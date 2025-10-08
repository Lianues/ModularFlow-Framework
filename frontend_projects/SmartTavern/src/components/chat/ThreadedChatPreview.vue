<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
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

// 选项菜单状态
const activeMenu = ref(null)

function toggleMenu(msgId) {
  activeMenu.value = activeMenu.value === msgId ? null : msgId
}

function copyMessage(msg) {
  navigator.clipboard.writeText(msg.content).then(() => {
    console.log('已复制到剪贴板')
    activeMenu.value = null
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

// 输入框逻辑
const inputText = ref('')
const messageListRef = ref(null)
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
})

onBeforeUnmount(() => {
  removeWheel?.()
})

watch(() => props.messages.length, () => {
  // 消息数量变化后，下一拍更新滚动条
  nextTick(() => messageListRef.value?.update?.())
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
  
  // 添加到消息列表
  props.messages.push(newMessage)
  
  // 清空输入框
  inputText.value = ''
  
  // 滚动到底部（等待过渡动画更丝滑）
  nextTick(() => {
    setTimeout(() => {
      if (messageListRef.value?.$el) {
        const container = messageListRef.value.$el.querySelector('.scroll-container')
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      }
    }, 320)
  })
}

// 支持Ctrl+Enter发送
function onKeydown(e) {
  if (e.key === 'Enter' && e.ctrlKey) {
    e.preventDefault()
    sendMessage()
  }
}
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
                <!-- 三点菜单按钮 -->
                <div class="menu-wrapper">
                  <button
                    class="menu-btn"
                    @click.stop="toggleMenu(m.id)"
                    :aria-expanded="activeMenu === m.id"
                  >
                    ⋮
                  </button>
                  <!-- 选项菜单（向左弹出） -->
                  <transition name="menu-slide">
                    <div v-if="activeMenu === m.id" class="menu-dropdown">
                      <button class="menu-item" @click="copyMessage(m)">
                        <span class="menu-icon">📋</span>
                        复制
                      </button>
                      <button
                        v-if="idx === props.messages.length - 1"
                        class="menu-item menu-danger"
                        @click="deleteMessage(m.id)"
                      >
                        <span class="menu-icon">🗑️</span>
                        删除
                      </button>
                    </div>
                  </transition>
                </div>
              </header>
              <section data-part="content" class="floor-content">
                {{ m.content }}
              </section>
              
              <!-- 分支切换器（仅最新楼层显示） -->
              <div v-if="idx === props.messages.length - 1 && totalBranches > 1" class="branch-switcher">
                <button
                  class="branch-btn"
                  @click="switchBranch('left')"
                  :disabled="activeBranch <= 1"
                  title="上一个分支"
                >
                  ◀
                </button>
                <span class="branch-indicator">{{ activeBranch }}/{{ totalBranches }}</span>
                <button
                  class="branch-btn"
                  @click="switchBranch('right')"
                  :disabled="activeBranch >= totalBranches"
                  title="下一个分支"
                >
                  ▶
                </button>
              </div>
            </div>
            </div>
          </article>
        </transition-group>
      </div>
    </CustomScrollbar>

    <!-- 输入区（多行文本） -->
    <div class="tch-input-row">
      <textarea
        v-model="inputText"
        class="tch-input"
        placeholder="输入消息... (Ctrl+Enter 发送)"
        @keydown="onKeydown"
      ></textarea>
      <button class="tch-send" @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<style scoped>
/* 容器布局 */
.tch-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

/* 滚动列表容器（CustomScrollbar占位） */
.tch-list {
  flex: 1;
  min-height: 0;
}

/* 内部容器（供过渡动画使用） */
.tch-list-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 4px;
}

/* 楼层卡（玻璃拟态） */
.floor-card {
  padding: 14px;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(var(--st-surface), 0.82);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  box-shadow: var(--st-shadow-md);
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease, border-color .18s ease;
  will-change: transform, opacity, filter;
}
.floor-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(0,0,0,0.10);
  border-color: rgba(var(--st-primary), 0.35);
  background: rgba(var(--st-surface), 0.88);
}

/* 楼层布局：左侧头像+徽章，右侧名称+楼层+内容 */
.floor-layout {
  display: flex;
  gap: 14px;
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
.avatar {
  width: var(--st-avatar-size, 56px);
  height: var(--st-avatar-size, 56px);
  border-radius: 14px;
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
  word-break: break-word;
  white-space: pre-wrap;
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
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
  transition: all 0.15s ease;
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
  border-radius: 10px;
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
  transition: background 0.12s ease;
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

/* 分支切换器 */
.branch-switcher {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(var(--st-border), 0.3);
}

.branch-btn {
  appearance: none;
  background: rgba(var(--st-primary), 0.08);
  border: 1px solid rgba(var(--st-primary), 0.3);
  color: rgb(var(--st-primary));
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.15s ease;
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

/* 输入行 */
.tch-input-row {
  display: flex;
  gap: 8px;
  align-items: stretch;
  flex-shrink: 0;
  height: var(--st-input-height, 100px);
}
.tch-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid rgb(var(--st-border));
  border-radius: var(--st-radius-md);
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  font-family: var(--st-font-body);
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}
.tch-input:focus {
  outline: none;
  border-color: rgba(var(--st-primary), 0.5);
  box-shadow: 0 0 0 3px rgba(var(--st-primary), 0.1);
}
.tch-send {
  padding: 10px 14px;
  border-radius: var(--st-radius-md);
  background: linear-gradient(135deg, rgba(var(--st-primary),1), rgba(var(--st-accent),1));
  color: var(--st-primary-contrast);
  border: none;
  cursor: pointer;
  height: 100%;
  box-sizing: border-box;
  transition: filter .15s ease, transform .15s ease;
}
.tch-send:hover {
  filter: saturate(1.1) brightness(1.05);
  transform: translateY(-1px);
}
.tch-send:active {
  transform: translateY(0);
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
</style>