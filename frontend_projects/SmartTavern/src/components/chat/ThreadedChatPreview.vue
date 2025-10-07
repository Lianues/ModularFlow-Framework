<script setup>
/**
 * 楼层对话预览（美化版）
 * 布局：头像占位 + 名称/角色 + 对话内容 + 楼层序号（#）
 * - 不依赖外部数据，仅美化现有 props.messages（id/role/content）
 * - 使用 Design Tokens，响应式与玻璃拟态风格
 * - data-scope/data-part 保持稳定选择器契约（便于主题包覆盖）
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
</script>

<template>
  <div data-scope="chat-threaded" class="tch-container">
    <div data-scope="message-list" class="tch-list">
      <article
        v-for="(m, idx) in props.messages"
        :key="m.id"
        data-scope="message-item"
        :data-role="m.role"
        class="floor-card glass"
      >
        <header class="floor-header">
          <div class="avatar role-user" v-if="m.role === 'user'">
            <span class="avatar-letter">{{ nameOf(m).charAt(0) }}</span>
          </div>
          <div class="avatar role-assistant" v-else-if="m.role === 'assistant'">
            <span class="avatar-letter">{{ nameOf(m).charAt(0) }}</span>
          </div>
          <div class="avatar role-system" v-else>
            <span class="avatar-letter">{{ nameOf(m).charAt(0) }}</span>
          </div>

          <div class="meta">
            <div class="name">{{ nameOf(m) }}</div>
            <div class="role-badge">{{ roleLabel(m.role) }}</div>
          </div>

          <div class="floor-index" :title="'楼层序号'">#{{ idx + 1 }}</div>
        </header>

        <section data-part="content" class="floor-content">
          {{ m.content }}
        </section>
      </article>
    </div>

    <!-- 输入区（多行文本） -->
    <div class="tch-input-row">
      <textarea
        class="tch-input"
        placeholder="输入消息（演示占位）"
        disabled
      ></textarea>
      <button class="tch-send" disabled>发送</button>
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
.tch-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
  min-height: 0;
}

/* 楼层卡（玻璃拟态） */
.floor-card {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 10px;
  padding: 14px;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(var(--st-surface), 0.82);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  box-shadow: var(--st-shadow-md);
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease, border-color .18s ease;
}
.floor-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(0,0,0,0.10);
  border-color: rgba(var(--st-primary), 0.35);
  background: rgba(var(--st-surface), 0.88);
}

/* 楼层头部 */
.floor-header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 12px;
}
.avatar {
  width: 56px;
  height: 56px;
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
  font-size: 20px;
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

.meta {
  display: grid;
  grid-auto-rows: auto;
  gap: 2px;
}
.name {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  font-size: 18px;
}
.role-badge {
  display: inline-block;
  font-size: 14px;
  color: rgb(var(--st-color-text));
  background: rgba(var(--st-primary),0.12);
  border: 1px solid rgba(var(--st-primary),0.32);
  border-radius: 9999px;
  padding: 4px 10px;
}

.floor-index {
  font-weight: 700;
  color: rgba(var(--st-color-text), 0.7);
  letter-spacing: .3px;
  font-size: 16px;
}

/* 楼层内容 */
.floor-content {
  color: rgba(var(--st-color-text), 0.95);
  font-size: var(--st-chat-font-size, 18px);
  line-height: 1.75;
  word-break: break-word;
  white-space: pre-wrap;
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
  cursor: not-allowed;
  opacity: .7;
  height: 100%;
  box-sizing: border-box;
}
</style>