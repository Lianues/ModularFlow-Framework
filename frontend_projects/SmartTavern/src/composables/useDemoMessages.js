import { reactive } from 'vue'

/**
 * useDemoMessages：提供线程预览所用的演示消息（与现有 UI 等价）
 * - 返回：messages（reactive 数组）
 * - 仅用于占位演示，后续可替换为真实数据源
 */
export function useDemoMessages() {
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

  return { messages }
}

export default useDemoMessages