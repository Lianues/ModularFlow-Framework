<script setup>
import { ref, reactive, computed, defineComponent, h } from 'vue'

// 视图状态：单一路径（/）下的多视图切换
// start → 开始页（不显示侧边栏）
// threaded → 对话楼层页（显示侧边栏）
// sandbox → 全局沙盒占位（显示侧边栏）
const view = ref('start')
const showSidebar = computed(() => view.value !== 'start')

// 侧边栏：7 个配置入口的占位预览（后续接入设置页）
const SidebarNav = defineComponent({
  name: 'SidebarNav',
  setup() {
    const items = [
      { key: 'presets', title: '预设 Presets', desc: '管理提示词预设与切换' },
      { key: 'worldbook', title: '世界书 Worldbook', desc: '设定世界观/术语库' },
      { key: 'characters', title: '角色卡 Characters', desc: '管理角色信息卡' },
      { key: 'persona', title: '用户信息 Persona', desc: '配置用户画像与偏好' },
      { key: 'regex', title: '正则 Regex Rules', desc: '清洗/后处理规则' },
      { key: 'themes', title: '主题 Themes', desc: '外观与主题（可导入 Theme Pack）' },
      { key: 'app', title: '应用设置 App Settings', desc: '全局开关与权限' },
    ]
    return () =>
      h('div', { 'data-scope': 'sidebar-nav', class: 'st-sidebar-nav' }, [
        h('div', { class: 'st-sidebar-title' }, '配置预览'),
        h(
          'div',
          { class: 'st-preview' },
          items.map((it) =>
            h(
              'button',
              {
                type: 'button',
                class: 'st-preview-card',
                'data-part': `preview-${it.key}`,
                title: it.title,
              },
              [
                h('div', { class: 'st-preview-title' }, it.title),
                h('div', { class: 'st-preview-desc' }, it.desc),
                h('div', { class: 'st-preview-badge' }, '即将可配置'),
              ],
            ),
          ),
        ),
        h('div', { class: 'st-sidebar-hint' }, '在聊天页面右侧展示的配置入口（预览占位）'),
      ])
  },
})

// 楼层对话演示消息（占位）
const messages = reactive([
  { id: 1, role: 'system', content: '欢迎来到 SmartTraven。' },
  { id: 2, role: 'user', content: '你好，介绍一下你自己？' },
  { id: 3, role: 'assistant', content: '我是一个对话助手，帮助你完成任务。' },
])
const roleClass = (role) =>
  role === 'user' ? 'st-bubble-user' : role === 'assistant' ? 'st-bubble-ai' : 'st-bubble-system'
</script>

<template>
  <div data-scope="app-shell" class="st-app-shell">
    <header class="st-header">
      <button class="st-brand" @click="view = 'start'">SmartTraven</button>
      <div class="st-spacer" />
    </header>

    <div class="st-body">
      <!-- 仅在聊天相关视图显示侧边栏；开始页面不显示 -->
      <aside v-if="showSidebar" data-scope="sidebar" class="st-sidebar">
        <SidebarNav />
      </aside>

      <main data-scope="main" class="st-main">
        <!-- 开始页面 -->
        <section v-if="view === 'start'" data-scope="start-view" class="st-start">
          <h1 class="st-title">开始使用 SmartTraven</h1>
          <p class="st-desc">请选择模式进入聊天：</p>
          <div class="st-actions">
            <button class="st-btn" @click="view = 'threaded'">对话楼层</button>
            <button class="st-btn" @click="view = 'sandbox'">全局沙盒（占位）</button>
          </div>
        </section>

        <!-- 聊天页面：顶部模式切换（单页内切换组件） -->
        <section v-else data-scope="chat-unified" class="st-chat-unified">
          <div class="st-mode-switch">
            <button
              class="st-switch-btn"
              :class="{ active: view === 'threaded' }"
              @click="view = 'threaded'"
            >
              对话楼层
            </button>
            <button
              class="st-switch-btn"
              :class="{ active: view === 'sandbox' }"
              @click="view = 'sandbox'"
            >
              全局沙盒（占位）
            </button>
          </div>

          <!-- 楼层对话 -->
          <div v-if="view === 'threaded'" data-scope="chat-threaded" class="st-chat-threaded">
            <div data-scope="message-list" class="st-msg-list">
              <div
                v-for="m in messages"
                :key="m.id"
                data-scope="message-item"
                :data-role="m.role"
                class="st-msg-item"
              >
                <div data-part="bubble" class="st-bubble" :class="roleClass(m.role)">
                  {{ m.content }}
                </div>
              </div>
            </div>
            <div class="st-input-row">
              <input class="st-input" placeholder="输入消息（演示占位）" disabled />
              <button class="st-send" disabled>发送</button>
            </div>
          </div>

          <!-- 全局沙盒占位 -->
          <div v-else data-scope="chat-sandbox" class="st-sandbox">
            <h2 class="st-title">全局沙盒（占位）</h2>
            <p>此页面暂不渲染 iframe，仅为占位示意。</p>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<style scoped>
.st-app-shell { display: flex; flex-direction: column; height: 100vh; }
.st-header { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-bottom: 1px solid #e5e7eb; background: #fafafa; }
.st-brand { font-weight: 600; color: #111827; text-decoration: none; background: transparent; border: none; cursor: pointer; }
.st-body { display: flex; flex: 1; min-height: 0; }
.st-sidebar { width: 280px; border-right: 1px solid #e5e7eb; padding: 12px; background: #ffffff; overflow: auto; }
.st-main { flex: 1; padding: 16px; overflow: auto; }

/* Sidebar preview */
.st-sidebar-nav { display: flex; flex-direction: column; gap: 10px; }
.st-sidebar-title { font-weight: 600; color: #1f2937; }
.st-preview { display: grid; grid-template-columns: 1fr; gap: 8px; }
.st-preview-card { display: block; text-align: left; width: 100%; padding: 10px; border-radius: 10px; border: 1px solid #e5e7eb; background: #f9fafb; cursor: default; }
.st-preview-card:hover { background: #f3f4f6; }
.st-preview-title { font-size: 14px; font-weight: 600; color: #111827; }
.st-preview-desc { font-size: 12px; color: #6b7280; margin-top: 2px; }
.st-preview-badge { display: inline-block; margin-top: 6px; padding: 2px 6px; font-size: 11px; color: #4338ca; background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 9999px; }
.st-sidebar-hint { font-size: 12px; color: #6b7280; }

/* Start view */
.st-start { display: flex; flex-direction: column; gap: 8px; }
.st-title { margin: 0 0 4px; font-size: 20px; font-weight: 600; color: #111827; }
.st-desc { margin: 0 0 6px; color: #4b5563; }
.st-actions { display: flex; gap: 10px; margin-top: 6px; }
.st-btn { display: inline-block; padding: 10px 12px; background: #111827; color: #fff; border-radius: 8px; text-decoration: none; border: none; cursor: pointer; }

/* Chat unified / threaded */
.st-chat-unified { display: flex; flex-direction: column; gap: 12px; }
.st-mode-switch { display: flex; gap: 8px; }
.st-switch-btn { padding: 8px 10px; border-radius: 8px; border: 1px solid #e5e7eb; background: #fff; color: #374151; cursor: pointer; }
.st-switch-btn.active { background: #eef2ff; color: #3730a3; border-color: #c7d2fe; }

.st-chat-threaded { display: flex; flex-direction: column; gap: 12px; }
.st-msg-list { display: flex; flex-direction: column; gap: 8px; }
.st-msg-item { display: flex; }
.st-bubble { padding: 10px 12px; border-radius: 12px; background: #f3f4f6; }
.st-bubble-user { background: #dbeafe; margin-left: auto; }
.st-bubble-ai { background: #e5e7eb; }
.st-bubble-system { background: #fff7ed; border: 1px solid #fed7aa; }
.st-input-row { display: flex; gap: 8px; }
.st-input { flex: 1; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; }
.st-send { padding: 8px 12px; border-radius: 8px; background: #9ca3af; color: #fff; border: none; }

/* Sandbox placeholder */
.st-sandbox { color: #4b5563; }
</style>
