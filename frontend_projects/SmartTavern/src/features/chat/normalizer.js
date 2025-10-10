// SmartTavern Chat Normalizer (v1)
// 作用：与对话文本相关的通用解析/拆分工具，便于组件复用与后续拆分。
// 目前包含：在消息文本中提取/拆分完整 HTML 文档（支持围栏代码块 ```html ... ``` 与纯文本形态）
// 参考现有逻辑：ThreadedChatPreview.vue 中的实现（已抽出为通用函数）

/** @type {RegExp} 匹配完整 HTML 文档开头（DOCTYPE） */
export const HTML_DOC_RE = /<!DOCTYPE\s+html/i

/** @type {RegExp} 匹配围栏代码块（```html ... ``` 或 ```HTML ... ```），提取中间内容 */
export const FENCE_RE = /```(?:html|HTML)?\s*([\s\S]*?)```/i

/**
 * 判断文本中是否包含完整 HTML 文档
 * @param {string} text
 * @returns {boolean}
 */
export function hasHtmlDoc(text) {
  return !!extractHtmlDocFromText(text)
}

/**
 * 若文本中包含完整 HTML 文档，返回该 HTML 文档文本，否则返回空串
 * 支持：
 *  - ```html ... ``` 或 ```HTML ... ``` 围栏中包含 <!DOCTYPE html>
 *  - 纯文本中包含 <!DOCTYPE html> ... </html>
 * @param {string} text
 * @returns {string}
 */
export function extractHtmlDocFromText(text) {
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

/**
 * 将消息文本拆分为 前置文本 / HTML 文档 / 后置文本 三段，仅替换中间代码块
 * 支持：
 *  - ```html ... ``` 或 ```HTML ... ``` 围栏中包含 <!DOCTYPE html>
 *  - 纯文本中包含 <!DOCTYPE html> ... </html>
 * @param {string} text
 * @returns {{ before: string, html: string, after: string }}
 */
export function splitHtmlFromText(text) {
  if (!text || typeof text !== 'string') return { before: '', html: '', after: '' }

  // 优先匹配围栏代码块
  const fence = text.match(/```(?:html|HTML)?\s*([\s\S]*?)```/i)
  if (fence && fence[0]) {
    const fenceIdx = text.indexOf(fence[0])
    const code = fence[1] ?? ''
    if (HTML_DOC_RE.test(code)) {
      const before = text.slice(0, fenceIdx)
      const after = text.slice(fenceIdx + fence[0].length)
      return { before, html: code.trim(), after }
    }
  }

  // 回退：匹配纯文本中的 <!DOCTYPE html> ... </html>
  const doctypeRe = /<!DOCTYPE\s+html[^>]*>/i
  const endHtmlRe = /<\/html>/i
  const m = text.match(doctypeRe)
  if (m) {
    const start = m.index ?? -1
    if (start >= 0) {
      const tail = text.slice(start)
      const endMatchIdx = tail.search(endHtmlRe)
      const end = endMatchIdx >= 0 ? start + endMatchIdx + '</html>'.length : text.length
      const before = text.slice(0, start)
      const html = text.slice(start, end).trim()
      const after = text.slice(end)
      return { before, html, after }
    }
  }

  return { before: '', html: '', after: '' }
}