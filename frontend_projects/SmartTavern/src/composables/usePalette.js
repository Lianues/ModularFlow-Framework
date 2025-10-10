// SmartTavern composable: usePalette
// 负责从头像或角色生成渐变色，并输出可直接绑定到 style 的 CSS 变量映射

import { ref } from 'vue'

/**
 * @typedef {Object} ChatMessage
 * @property {number|string} id
 * @property {'user'|'assistant'|'system'|string} role
 * @property {string} [avatarUrl]
 * @property {any} [meta]
 */

/** @param {number} v @param {number} [min] @param {number} [max] */
function clamp(v, min = 0, max = 255) { return Math.max(min, Math.min(max, v)) }
/** @param {{r:number,g:number,b:number}} rgb @param {number} [amt] */
function lighten(rgb, amt = 24) { return { r: clamp(rgb.r + amt), g: clamp(rgb.g + amt), b: clamp(rgb.b + amt) } }
/** @param {{r:number,g:number,b:number}} rgb @param {number} [a] */
function rgbToCss(rgb, a = 1) { return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${a})` }

/**
 * 根据角色提供回退渐变色，确保亮/暗主题下均有足够对比度
 * @param {string} role
 * @returns {{start:string,end:string}}
 */
function roleFallback(role) {
  if (role === 'assistant') return { start: 'rgba(14,165,233,1)', end: 'rgba(94,234,212,1)' }
  if (role === 'system')    return { start: 'rgba(251,191,36,1)', end: 'rgba(253,230,138,1)' }
  // user：使用主题主色-强调色
  return { start: 'rgb(var(--st-primary))', end: 'rgb(var(--st-accent))' }
}

/**
 * 从头像 URL 提取主色，失败返回 null
 * @param {string} url
 * @returns {Promise<{start:string,end:string}|null>}
 */
async function extractPaletteFromImage(url) {
  return new Promise((resolve) => {
    try {
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
          if (!count) return resolve(null)
          r = Math.round(r / count); g = Math.round(g / count); b = Math.round(b / count)
          const start = rgbToCss({ r, g, b })
          const end = rgbToCss(lighten({ r, g, b }, 28))
          resolve({ start, end })
        } catch (_) { resolve(null) }
      }
      img.onerror = () => resolve(null)
      img.src = url
    } catch (_) { resolve(null) }
  })
}

/**
 * 提供消息色条渐变的获取与样式计算
 */
export function usePalette() {
  /** @type {import('vue').Ref<Record<string|number, {start:string,end:string}>>} */
  const palettes = ref({})

  /**
   * 计算某消息的色条 CSS 变量映射
   * @param {ChatMessage} msg
   * @returns {Record<string,string>}
   */
  function stripeStyle(msg) {
    const pal = palettes.value[msg.id] || roleFallback(msg.role)
    return { '--stripe-start': pal.start, '--stripe-end': pal.end }
  }

  /**
   * 确保为消息准备好调色板（优先头像分析）
   * @param {ChatMessage} msg
   * @returns {Promise<void>}
   */
  async function ensurePaletteFor(msg) {
    let pal = null
    if (msg && msg.avatarUrl) {
      pal = await extractPaletteFromImage(msg.avatarUrl)
    }
    if (!pal) pal = roleFallback(msg?.role)
    palettes.value[msg.id] = pal
  }

  /**
   * 清除某条消息的缓存调色板
   * @param {string|number} id
   */
  function clearPalette(id) { if (id in palettes.value) delete palettes.value[id] }

  /**
   * 读取当前已缓存的调色板
   * @param {string|number|ChatMessage} idOrMsg
   * @returns {{start:string,end:string}|null}
   */
  function getPalette(idOrMsg) {
    const key = typeof idOrMsg === 'object' ? idOrMsg?.id : idOrMsg
    return key != null ? palettes.value[key] ?? null : null
  }

  return {
    palettes,
    ensurePaletteFor,
    stripeStyle,
    clearPalette,
    getPalette,
    roleFallback,
    extractPaletteFromImage,
  }
}

// 兼容默认导出
export default usePalette