// SmartTavern Theme Runtime - Pack helpers (v1)
// 提供 Theme Pack 的类型声明（JSDoc）、校验/规范化/合并等工具。
// 安全提示：主题脚本默认不执行；仅处理 tokens 与 CSS。脚本相关字段保留但不启用。

export const PACK_VERSION = 'v1'

/**
 * @typedef {Object} ThemeScriptPermissions
 * @property {boolean} [dom=false] 允许访问 DOM（默认 false）
 * @property {boolean} [network=false] 允许网络请求（默认 false）
 */

/**
 * @typedef {Object} ThemeScript
 * @property {string} code
 * @property {ThemeScriptPermissions} [permissions]
 * @property {string[]} [scopes] 适用范围（如 'chat-threaded', 'sandbox'）
 */

/**
 * @typedef {Object.<string,string|number>} ThemeTokens
 * CSS 自定义属性（--xxx）字典；值推荐字符串（可为 rgb/rgb(...) / 数字/px/% 等）
 * 例如：{ "--st-primary": "56 189 248", "--st-card-radius": "8px" }
 */

/**
 * @typedef {Object} ThemePackV1
 * @property {string|null} [id]
 * @property {string|null} [name]
 * @property {string|null} [version]
 * @property {ThemeTokens} [tokens]
 * @property {string} [css]  附加 CSS 文本
 * @property {ThemeScript} [script] 保留字段（默认不执行）
 */

/**
 * @typedef {Object} ThemeApplyOptions
 * @property {boolean} [persist=true] 应用后是否持久化
 * @property {boolean} [allowScript=false] 是否允许脚本（默认 false）
 */

function isPlainObject(v) {
  return !!v && typeof v === 'object' && !Array.isArray(v)
}

/**
 * 规范化 ThemePack（移除不支持字段、修正类型）
 * @param {any} input
 * @returns {ThemePackV1}
 */
export function normalizePack(input) {
  const p = isPlainObject(input) ? input : {}
  /** @type {ThemePackV1} */
  const out = {
    id: typeof p.id === 'string' ? p.id : (p.id == null ? null : String(p.id)),
    name: typeof p.name === 'string' ? p.name : (p.name == null ? null : String(p.name)),
    version: typeof p.version === 'string' ? p.version : (p.version == null ? null : String(p.version)),
    tokens: undefined,
    css: typeof p.css === 'string' ? p.css : undefined,
    script: undefined,
  }
  if (isPlainObject(p.tokens)) {
    out.tokens = {}
    for (const [k, v] of Object.entries(p.tokens)) {
      if (typeof k === 'string' && k.startsWith('--')) {
        out.tokens[k] = (typeof v === 'number' || typeof v === 'string') ? v : String(v)
      }
    }
    if (Object.keys(out.tokens).length === 0) delete out.tokens
  }
  if (isPlainObject(p.script)) {
    out.script = {
      code: typeof p.script.code === 'string' ? p.script.code : '',
      permissions: isPlainObject(p.script.permissions)
        ? {
            dom: !!p.script.permissions.dom,
            network: !!p.script.permissions.network,
          }
        : { dom: false, network: false },
      scopes: Array.isArray(p.script.scopes) ? p.script.scopes.filter(s => typeof s === 'string') : undefined,
    }
    // 注：脚本默认不执行，具体由上层管理器控制 allowScript 开关
  }
  return out
}

/**
 * 校验 ThemePack 内容合法性（非严格）
 * @param {any} pack
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validatePack(pack) {
  const errors = []
  const p = normalizePack(pack)
  if (p.tokens) {
    for (const k of Object.keys(p.tokens)) {
      if (!k.startsWith('--')) errors.push(`Token key must start with "--": ${k}`)
    }
  }
  if (p.css && typeof p.css !== 'string') {
    errors.push('css must be a string')
  }
  // 脚本校验（仅字段形态）
  if (p.script) {
    if (typeof p.script.code !== 'string') errors.push('script.code must be string')
    if (p.script.permissions && typeof p.script.permissions !== 'object') {
      errors.push('script.permissions must be object')
    }
    if (p.script.scopes && !Array.isArray(p.script.scopes)) {
      errors.push('script.scopes must be string[]')
    }
  }
  return { valid: errors.length === 0, errors }
}

/**
 * 合并 tokens（后者覆盖前者）
 * @param {ThemeTokens|undefined} base
 * @param {ThemeTokens|undefined} overrides
 * @returns {ThemeTokens|undefined}
 */
export function mergeTokens(base, overrides) {
  if (!base && !overrides) return undefined
  const out = { ...(base || {}) }
  if (overrides) {
    for (const [k, v] of Object.entries(overrides)) {
      if (typeof k === 'string' && k.startsWith('--')) out[k] = v
    }
  }
  return out
}

/**
 * 快速创建 ThemePack
 * @param {Partial<ThemePackV1>} spec
 * @returns {ThemePackV1}
 */
export function createPack(spec = {}) {
  const p = normalizePack(spec || {})
  return p
}

/**
 * 从 JSON 文本解析 ThemePack（安全模式）
 * @param {string} text
 * @returns {ThemePackV1|null}
 */
export function parsePackFromJSON(text) {
  try {
    const obj = JSON.parse(text)
    return normalizePack(obj)
  } catch (_) {
    return null
  }
}

/**
 * 将 ThemePack 序列化为 JSON（紧凑或美化）
 * @param {ThemePackV1} pack
 * @param {boolean} [pretty=false]
 */
export function stringifyPack(pack, pretty = false) {
  const n = normalizePack(pack)
  return JSON.stringify(n, null, pretty ? 2 : 0)
}