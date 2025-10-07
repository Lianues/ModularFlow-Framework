<script setup>
const props = defineProps({
  messages: {
    type: Array,
    default: () => ([
      { id: 1, role: 'system', content: '欢迎来到 SmartTraven。' },
      { id: 2, role: 'user', content: '你好，介绍一下你自己？' },
      { id: 3, role: 'assistant', content: '我是一个对话助手，帮助你完成任务。' },
    ])
  }
})

function roleClass(role) {
  return role === 'user' ? 'tch-bubble-user'
       : role === 'assistant' ? 'tch-bubble-ai'
       : 'tch-bubble-system'
}
</script>

<template>
  <div data-scope="chat-threaded" class="tch-container card">
    <div data-scope="message-list" class="tch-list">
      <div
        v-for="m in props.messages"
        :key="m.id"
        data-scope="message-item"
        :data-role="m.role"
        class="tch-item"
      >
        <div data-part="bubble" class="tch-bubble" :class="roleClass(m.role)">
          {{ m.content }}
        </div>
      </div>
    </div>
    <div class="tch-input-row">
      <input class="tch-input" placeholder="输入消息（演示占位）" disabled />
      <button class="tch-send" disabled>发送</button>
    </div>
  </div>
</template>

<style scoped>
.tch-container { display: flex; flex-direction: column; gap: 12px; padding: 14px; }
/* 列表 */
.tch-list { display: flex; flex-direction: column; gap: 8px; max-height: 48vh; overflow: auto; padding-right: 6px; }
.tch-item { display: flex; }
/* 气泡 */
.tch-bubble { padding: 10px 12px; border-radius: 14px; background: rgb(var(--st-surface-2)); border: 1px solid rgb(var(--st-border)); box-shadow: var(--st-shadow-sm); }
.tch-bubble-user { background: rgba(59,130,246,0.1); margin-left: auto; border-color: rgba(59,130,246,0.35); }
.tch-bubble-ai { background: rgba(148,163,184,0.12); border-color: rgba(148,163,184,0.4); }
.tch-bubble-system { background: rgba(253,230,138,0.15); border-color: rgba(251,191,36,0.45); }
/* 输入行 */
.tch-input-row { display: flex; gap: 8px; }
.tch-input { flex: 1; padding: 10px 12px; border: 1px solid rgb(var(--st-border)); border-radius: var(--st-radius-md); background: rgb(var(--st-surface)); color: rgb(var(--st-color-text)); }
.tch-send { padding: 10px 14px; border-radius: var(--st-radius-md); background: linear-gradient(135deg, rgba(var(--st-primary),1), rgba(var(--st-accent),1)); color: var(--st-primary-contrast); border: none; cursor: not-allowed; opacity: .7; }
</style>