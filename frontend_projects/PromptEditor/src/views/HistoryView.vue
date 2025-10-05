<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

/**
 * 分支对话可视化（仅分支，不包含线性示例）
 * - 输入优先支持 chat-branches v2 标准文件（export）
 * - 也可接收 branch_table / get_path / openai_messages 的派生视图数据
 * - 暂不接入后端，仅做前端展示；无状态修改
 *
 * 参考：
 * - [python.chat_branches.README](api/modules/SmartTraven/chat_branches/README.md:1)
 * - [python.function(export)](api/modules/SmartTraven/chat_branches/chat_branches.py:237)
 * - [python.function(branch_table)](api/modules/SmartTraven/chat_branches/chat_branches.py:222)
 * - [python.function(get_path)](api/modules/SmartTraven/chat_branches/chat_branches.py:61)
 * - [python.function(openai_messages)](api/modules/SmartTraven/chat_branches/chat_branches.py:207)
 */

type MsgRole = 'system' | 'user' | 'assistant'

interface BranchDoc {
  schema: { name: 'chat-branches'; version: number }
  meta: { id: string; title?: string | null }
  root: string
  nodes: Record<string, { pid: string | null; role: MsgRole; content?: string | null }>
  children: Record<string, string[]>
  active_path: string[]
}
interface BranchTable {
  session_id: string
  latest: { depth: number; j: number | null; n: number | null; node_id: string | null }
  levels: { depth: number; node_id: string; j: number | null; n: number | null }[]
}
interface PathView {
  session_id: string
  status: string
  path: { id: string; depth: number; role: MsgRole; content: string | null; branch_j: number | null; branch_n: number | null }[]
}
interface OpenAIView {
  conversation_id: string
  session_id: string
  messages: { role: MsgRole; content: string }[]
}

const props = defineProps<{
  branchDoc?: BranchDoc
  branchTable?: BranchTable
  pathView?: PathView
  messagesView?: OpenAIView
  title?: string
}>()

// Demo（若未传入，则使用示例数据）
// 对应 backend_projects/SmartTraven/data/conversations/branch_demo.json
const demoDoc = computed<BranchDoc>(() => ({
  schema: { name: 'chat-branches', version: 2 },
  meta: { id: 'c_demo_branch', title: '示例：分支重试对话（V2）' },
  root: 'n_root',
  nodes: {
    n_root: { pid: null, role: 'system', content: '对话上下文：这是一个分支重试示例。' },
    n_user1: { pid: 'n_root', role: 'user', content: '你好，请介绍一下分支机制。' },
    n_ass1: { pid: 'n_user1', role: 'assistant', content: '分支机制允许你在任意楼层（通过修剪）切换分支并生成新的对话会话。' },
    n_ass2: { pid: 'n_user1', role: 'assistant', content: '另一种解释：你可以回到某层，向左/向右切换已存在或新建分支，旧会话归档，新会话继续。' },
    n_user2: { pid: 'n_ass1', role: 'user', content: '那怎么导出当前分支为 OpenAI messages 呢？' },
    n_ass3: { pid: 'n_user2', role: 'assistant', content: '可调用 openai_messages 接口，返回 [{role, content}] 数组直接给 LLM 使用。' },
  },
  children: {
    n_root: ['n_user1'],
    n_user1: ['n_ass1', 'n_ass2'],
    n_ass1: ['n_user2'],
    n_user2: ['n_ass3'],
  },
  active_path: ['n_root', 'n_user1', 'n_ass1', 'n_user2', 'n_ass3'],
}))

// 使用 props.branchDoc 或 demo
const doc = computed<BranchDoc>(() => props.branchDoc ?? demoDoc.value)

// 归一化 active_path（确保 root 开头）
const activePath = computed<string[]>(() => {
  const ap = (doc.value.active_path ?? []).slice()
  if (!ap.length) return [doc.value.root]
  if (ap[0] !== doc.value.root) ap.unshift(doc.value.root)
  return ap
})

function listDepthFirst(d: BranchDoc): string[] {
  const order: string[] = []
  const dfs = (nid: string) => {
    order.push(nid)
    const kids = d.children[nid] ?? []
    for (const k of kids) dfs(k)
  }
  dfs(d.root)
  return order
}

function parentMap(d: BranchDoc): Record<string, string | null> {
  const m: Record<string, string | null> = {}
  for (const [pid, arr] of Object.entries(d.children)) {
    for (const cid of arr) m[cid] = pid
  }
  m[d.root] = null
  return m
}

function depthOf(d: BranchDoc, nid: string): number {
  const pm: Record<string, string | null> = parentMap(d)
  let cur: string | null = nid
  let depth = 0
  while (cur !== null) {
    const parentVal: string | null | undefined = pm[cur as string]
    if (parentVal === null || typeof parentVal === 'undefined') break
    depth++
    cur = parentVal
  }
  return depth
}

function jnOf(d: BranchDoc, nid: string): { j: number | null; n: number | null } {
  const pm: Record<string, string | null> = parentMap(d)
  const pid: string | null | undefined = pm[nid]
  if (pid === null || typeof pid === 'undefined') return { j: null, n: null }
  const siblings: string[] = d.children[pid] ?? []
  const idx = siblings.indexOf(nid)
  const j: number | null = idx >= 0 ? idx + 1 : null
  const n: number | null = siblings.length ? siblings.length : null
  return { j, n }
}

function branchLevelsFromDoc(d: BranchDoc): { depth: number; node_id: string; j: number | null; n: number | null }[] {
  const ap: string[] = activePath.value
  const levels: { depth: number; node_id: string; j: number | null; n: number | null }[] = []
  for (let depth = 2; depth <= ap.length; depth++) {
    const parentId: string = ap[depth - 2] as string
    const childId: string | undefined = ap[depth - 1]
    if (typeof childId === 'undefined') continue
    const siblings: string[] = d.children[parentId] ?? []
    const idx = siblings.indexOf(childId)
    const j: number | null = idx >= 0 ? idx + 1 : null
    const n: number | null = siblings.length ? siblings.length : null
    levels.push({ depth, node_id: childId, j, n })
  }
  return levels
}

// OpenAI messages 视图（若未传入，则从 doc 的 active_path 构造）
const messages = computed<{ role: MsgRole; content: string }[]>(() => {
  if (props.messagesView?.messages?.length) return props.messagesView.messages
  const out: { role: MsgRole; content: string }[] = []
  for (const nid of activePath.value) {
    const node = doc.value.nodes[nid]
    if (node && (node.role === 'system' || node.role === 'user' || node.role === 'assistant')) {
      out.push({ role: node.role, content: String(node.content ?? '') })
    }
  }
  return out
})

const onlyActive = ref(false)
const order = computed(() => (onlyActive.value ? activePath.value : listDepthFirst(doc.value)))
const levels = computed(() => props.branchTable?.levels ?? branchLevelsFromDoc(doc.value))

const latest = computed(() => {
  const ap: string[] = activePath.value
  const depth = ap.length
  const node_id = ap.length ? ap[ap.length - 1] : null
  if (depth < 2 || !node_id) return { depth, j: null as number | null, n: null as number | null, node_id }
  const jn = jnOf(doc.value, node_id)
  return { depth, j: jn.j, n: jn.n, node_id }
})

const metaTitle = computed(() => props.title ?? doc.value.meta?.title ?? '分支会话')

// UI helpers
function isInActivePath(nid: string) {
  return activePath.value.includes(nid)
}

onMounted(() => {
  ;(window as any).lucide?.createIcons?.()
})
</script>

<template>
  <section class="space-y-6">
    <!-- 顶部：标题与统计 -->
    <div class="bg-white rounded-4 card-shadow border border-gray-200 p-6 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <i data-lucide="git-branch" class="w-6 h-6 text-black"></i>
          <h2>{{ metaTitle }}</h2>
        </div>
        <div class="flex items-center gap-2 text-xs text-black/60">
          <span class="px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">nodes: {{ Object.keys(doc.nodes).length }}</span>
          <span class="px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">path: {{ activePath.length }}</span>
        </div>
      </div>

      <div class="mt-3 flex flex-wrap items-center gap-2">
        <span class="text-xs text-black/60">Active Path:</span>
        <span v-for="nid in activePath" :key="nid" class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ nid }}</span>
      </div>

      <div class="mt-2 flex flex-wrap items-center gap-2">
        <span class="text-xs text-black/60">j/n 指示：</span>
        <span
          v-for="r in levels"
          :key="r.depth"
          class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent"
        >
          d{{ r.depth }} → j={{ r.j ?? '—' }} / n={{ r.n ?? '—' }}
        </span>
      </div>

      <!-- 图例与切换方向提示 -->
      <div class="mt-3 bg-white rounded-4 border border-gray-200 p-3">
        <div class="flex items-center gap-2 mb-2">
          <i data-lucide="info" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">图例与切换方向提示</span>
        </div>
        <div class="text-xs text-black/70 leading-6">
          <div class="flex flex-wrap items-center gap-2 mb-1">
            <span class="px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">j/n</span>
            <span>同一父节点下的兄弟序号/总数（1 开始）</span>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <i data-lucide="arrow-left" class="w-4 h-4 text-black"></i>
            <span>左切换：选择同层前一个兄弟（j-1，最小为 1）</span>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <i data-lucide="arrow-right" class="w-4 h-4 text-black"></i>
            <span>右切换：若 j < n → 选择 j+1；若 j = n → 新建 assistant 子节点（n+1）</span>
          </div>
          <div class="mt-2 flex flex-wrap items-center gap-2 text-black/70">
            <span class="text-black/60">当前末层：</span>
            <span class="px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">d{{ latest.depth }}</span>
            <span class="px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">j={{ latest.j ?? '—' }}/n={{ latest.n ?? '—' }}</span>
            <span class="px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent" v-if="(latest.j ?? 0) > 1">
              ← 可切左 (j-1)
            </span>
            <span class="px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent" v-if="latest.j !== null && latest.n !== null && latest.j < latest.n">
              → 可切右 (j+1)
            </span>
            <span class="px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent" v-if="latest.j !== null && latest.n !== null && latest.j === latest.n">
              → 新建 (n+1)
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 树视图 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <i data-lucide="tree-deciduous" class="w-4 h-4 text-black"></i>
          <span class="text-sm font-medium text-black">分支树</span>
        </div>
        <label class="inline-flex items-center gap-2 select-none">
          <input
            type="checkbox"
            v-model="onlyActive"
            class="w-5 h-5 border border-gray-400 rounded-4 accent-black focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2"
          />
          <span class="text-sm text-black/80">仅显示活动路径</span>
        </label>
      </div>

      <div>
        <div
          v-for="nid in order"
          :key="nid"
          class="py-2 border-b last:border-b-0 border-gray-100"
          :style="{ paddingLeft: `${Math.max(0, depthOf(doc, nid)) * 16}px` }"
        >
          <div class="flex items-center gap-2">
            <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ nid }}</span>
            <span class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ doc.nodes[nid]?.role || 'unknown' }}</span>
            <span class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">
              d{{ (depthOf(doc, nid) + 1) }}
            </span>
            <span
              v-if="jnOf(doc, nid).j !== null"
              class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent"
            >
              {{ jnOf(doc, nid).j }}/{{ jnOf(doc, nid).n ?? '—' }}
            </span>
            <span
              v-if="isInActivePath(nid)"
              class="text-2xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-gray-100"
            >active</span>
          </div>
          <div class="mt-1 text-sm text-black/70 leading-6 line-clamp-3">
            {{ doc.nodes[nid]?.content || '（无内容）' }}
          </div>
        </div>
      </div>
    </div>

    <!-- OpenAI messages 预览 -->
    <div class="bg-white rounded-4 border border-gray-200 p-5 transition-all duration-200 ease-soft hover:shadow-elevate">
      <div class="flex items-center gap-2 mb-2">
        <i data-lucide="messages-square" class="w-4 h-4 text-black"></i>
        <span class="text-sm font-medium text-black">OpenAI 消息视图（按活动路径）</span>
      </div>
      <div class="space-y-2">
        <div v-for="(m, idx) in messages" :key="idx" class="border border-gray-200 rounded-4 p-3">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs px-2 py-0.5 rounded-4 border border-gray-900 text-black bg-transparent">{{ m.role }}</span>
            <span class="text-xs text-black/60">#{{ idx + 1 }}</span>
          </div>
          <div class="text-sm text-black/70 leading-6 break-words">{{ m.content }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 局部样式最小化，遵循黑白主题与 4/8pt 间距系统 */
</style>