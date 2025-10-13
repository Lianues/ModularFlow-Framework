// SmartTavern Frontend API Client — Chat Branches (v1)
// 调用后端 modules.smarttavern/chat_branches 系列接口。
// 默认网关：http://localhost:8050/api/modules（见后端 core/config/api_config.py）
//
// 用法：
//   import ChatBranches from '@/services/chatBranches'
//   const latest = await ChatBranches.getLatestMessageByFile('backend_projects/SmartTavern/data/conversations/branch_demo.json')
//   console.log(latest) // { node_id, role, content, depth }
//
// 说明：
// - 按后端契约，所有接口采用 POST + JSON 请求体。
// - CORS 已在网关侧开启。
// - 若需要其它派生接口，可使用 openaiMessages/branchTable。

const DEFAULT_BASE = 'http://localhost:8050/api/modules';

function ensureBase() {
  // 可通过 window.ST_API_BASE 覆盖
  const fromWindow = typeof window !== 'undefined' && window.ST_API_BASE;
  return String(fromWindow || DEFAULT_BASE).replace(/\/+$/, '');
}

async function postJSON(path, body = {}) {
  const base = ensureBase();
  const url = `${base}/${String(path).replace(/^\/+/, '')}`;
  let resp;
  try {
    resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
  } catch (networkError) {
    const err = new Error(`[ChatBranches] Network error: ${networkError?.message || networkError}`);
    err.cause = networkError;
    err.url = url;
    throw err;
  }

  let data = null;
  const text = await resp.text().catch(() => '');
  try {
    data = text ? JSON.parse(text) : null;
  } catch (parseError) {
    const err = new Error(`[ChatBranches] Invalid JSON response (${resp.status}): ${text?.slice(0, 200)}`);
    err.cause = parseError;
    err.status = resp.status;
    err.url = url;
    throw err;
  }

  if (!resp.ok) {
    const err = new Error(`[ChatBranches] HTTP ${resp.status}: ${data && (data.message || data.error) || 'Unknown error'}`);
    err.status = resp.status;
    err.url = url;
    err.details = data;
    throw err;
  }
  return data;
}

// 轻量缓存（仅本会话内存）
const _mem = new Map();
const _ck = (k) => `cb:${k}`;

const ChatBranches = {
  // 获取某个对话文件的最新消息（依据 active_path）
  // 后端实现参考：[python.function(get_latest_message)](api/modules/SmartTavern/chat_branches/chat_branches.py:130)
  async getLatestMessageByFile(file, { useCache = true } = {}) {
    const key = _ck(`latest:${file}`);
    if (useCache && _mem.has(key)) return _mem.get(key);

    const res = await postJSON('smarttavern/chat_branches/get_latest_message', { file });
    _mem.set(key, res);
    return res;
  },

  // 导出 OpenAI messages（可选）
  // 参考：[python.function(openai_messages)](api/modules/SmartTavern/chat_branches/chat_branches.py:68)
  async openaiMessagesByFile(file) {
    return postJSON('smarttavern/chat_branches/openai_messages', { file });
  },

  // 计算分支情况表（可选）
  // 参考：[python.function(branch_table)](api/modules/SmartTavern/chat_branches/chat_branches.py:98)
  async branchTableByFile(file) {
    return postJSON('smarttavern/chat_branches/branch_table', { file });
  },

  // 创建初始对话（从角色卡 messages[0] 作为根消息），返回三件套路径
  // 后端实现见：[python.function(create_conversation)](api/modules/SmartTavern/chat_branches/chat_branches.py:215)
  async createConversation({
    name,
    description = '',
    type = 'threaded',
    character,
    preset,
    persona,
    regex = null,
    worldbook = null,
  }) {
    return postJSON('smarttavern/chat_branches/create_conversation', {
      name,
      description,
      type,
      character_file: character,
      preset_file: preset,
      persona_file: persona,
      regex_file: regex ?? null,
      worldbook_file: worldbook ?? null,
    });
  },

  // 综合设置管理：读取(action=get)或更新(action=update)对话 settings
  // 使用 file 或 slug 二选一定位
  // 字段：preset(string)、character(string)、persona(string)、regex_rules(array)、world_books(array)
  // 后端实现见：[python.function(settings)](api/modules/SmartTavern/chat_branches/chat_branches.py:282)
  async settings({ action, patch, file, slug }) {
    if (!action || !['get', 'update'].includes(action)) {
      throw new Error('[ChatBranches] settings: action must be "get" or "update"');
    }
    if (action === 'update' && (!patch || typeof patch !== 'object')) {
      throw new Error('[ChatBranches] settings: patch required for action=update');
    }
    const body = { action };
    if (patch) body.patch = patch;
    if (file) body.file = file;
    if (slug) body.slug = slug;
    return postJSON('smarttavern/chat_branches/settings', body);
  },

  // 管理 variables：action=get|set|merge|reset；set/merge 需提供 data 对象
  // 使用 file 或 slug 二选一定位
  // 后端实现见：[python.function(variables)](api/modules/SmartTavern/chat_branches/chat_branches.py:215)
  async variables({ action, data, file, slug }) {
    const body = { action };
    if (data !== undefined) body.data = data;
    if (file) body.file = file;
    if (slug) body.slug = slug;
    return postJSON('smarttavern/chat_branches/variables', body);
  },

  // 追加新消息：创建新节点并更新父节点 children 与 active_path
  // 后端实现见：[python.function(append_message)](api/modules/SmartTavern/chat_branches/chat_branches.py:192)
  async appendMessage({ file, node_id, pid, role, content }) {
    if (!file) {
      throw new Error('[ChatBranches] appendMessage: file is required');
    }
    if (!node_id || !pid || !role || !content) {
      throw new Error('[ChatBranches] appendMessage: node_id, pid, role, content are required');
    }
    return postJSON('smarttavern/chat_branches/append_message', {
      file,
      node_id,
      pid,
      role,
      content
    });
  },

  // 更新消息内容：修改指定节点的 content
  // 后端实现见：[python.function(update_message)](api/modules/SmartTavern/chat_branches/chat_branches.py:138)
  async updateMessage({ file, node_id, content }) {
    if (!file) {
      throw new Error('[ChatBranches] updateMessage: file is required');
    }
    if (!node_id || content === undefined) {
      throw new Error('[ChatBranches] updateMessage: node_id and content are required');
    }
    return postJSON('smarttavern/chat_branches/update_message', {
      file,
      node_id,
      content
    });
  },

  // 修剪消息树：删除指定节点及其所有子孙
  // 后端实现见：[python.function(truncate_after)](api/modules/SmartTavern/chat_branches/chat_branches.py:165)
  async truncateAfter({ file, node_id }) {
    if (!file) {
      throw new Error('[ChatBranches] truncateAfter: file is required');
    }
    if (!node_id) {
      throw new Error('[ChatBranches] truncateAfter: node_id is required');
    }
    return postJSON('smarttavern/chat_branches/truncate_after', {
      file,
      node_id
    });
  },

  // 切换分支：切换 active_path 最后节点到目标分支序号
  // 后端实现见：[python.function(switch_branch)](api/modules/SmartTavern/chat_branches/chat_branches.py:222)
  async switchBranch({ file, target_j }) {
    if (!file) {
      throw new Error('[ChatBranches] switchBranch: file is required');
    }
    if (!target_j || target_j < 1) {
      throw new Error('[ChatBranches] switchBranch: target_j must be >= 1');
    }
    return postJSON('smarttavern/chat_branches/switch_branch', {
      file,
      target_j
    });
  },
};

export default ChatBranches;