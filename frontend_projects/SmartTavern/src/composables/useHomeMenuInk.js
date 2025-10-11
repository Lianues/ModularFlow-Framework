/**
 * 智能前景色（Home 左下菜单）计算组合式
 * - 从 CSS 变量 --st-bg-start 取得背景图 URL
 * - 将背景绘制到离屏 canvas，采样按钮区域的亮度，自动选择墨色/白色
 * - 随窗口 resize/scroll 轻量更新
 *
 * 用法（在父组件中）：
 *   import { useHomeMenuInk } from '@/composables/useHomeMenuInk'
 *   const view = ref('start')
 *   const { updateHomeMenuInk } = useHomeMenuInk(() => view.value === 'start')
 *   // 可在视图切换到 start 后主动触发：
 *   // nextTick(() => updateHomeMenuInk())
 */
import { onMounted, onBeforeUnmount } from 'vue'

/**
 * useHomeMenuInk
 * @param {() => boolean} isActive - 返回是否处于 Home/需要更新的状态（例如 view === 'start'）
 * @returns {{ updateHomeMenuInk: () => Promise<void> }}
 */
export function useHomeMenuInk(isActive = () => true) {
  // 离屏绘制资源
  let __bgImg = null
  let __bgUrlCache = null
  let __cv = null
  let __ctx = null

  function getBgUrlFromCSS() {
    const raw = getComputedStyle(document.documentElement).getPropertyValue('--st-bg-start') || ''
    const m = raw.match(/url\((["']?)(.*?)\1\)/)
    return m ? m[2] : ''
  }

  async function ensureBgImage() {
    const url = getBgUrlFromCSS()
    if (!url) return null
    if (__bgImg && __bgUrlCache === url) return __bgImg
    __bgUrlCache = url
    __bgImg = await new Promise((resolve) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = () => resolve(null)
      img.src = url
    })
    return __bgImg
  }

  function ensureCanvas() {
    const vw = window.innerWidth, vh = window.innerHeight
    if (!__cv) {
      __cv = document.createElement('canvas')
      __ctx = __cv.getContext('2d', { willReadFrequently: true })
    }
    if (__cv.width !== vw || __cv.height !== vh) {
      __cv.width = vw
      __cv.height = vh
    }
  }

  function drawBgToCanvas(img) {
    if (!img || !__ctx) return
    const vw = window.innerWidth, vh = window.innerHeight
    const iw = img.naturalWidth, ih = img.naturalHeight
    const scale = Math.max(vw / iw, vh / ih)
    const sw = iw * scale, sh = ih * scale
    const ox = (vw - sw) / 2
    const oy = (vh - sh) / 2
    __ctx.clearRect(0, 0, vw, vh)
    __ctx.drawImage(img, ox, oy, sw, sh)
  }

  function sampleBrightnessAt(x, y, r = 8) {
    if (!__ctx || !__cv) return null
    const x0 = Math.max(0, Math.floor(x - r))
    const y0 = Math.max(0, Math.floor(y - r))
    const w = Math.min(__cv.width - x0, r * 2)
    const h = Math.min(__cv.height - y0, r * 2)
    if (w <= 0 || h <= 0) return null
    try {
      const data = __ctx.getImageData(x0, y0, w, h).data
      let sum = 0, n = 0
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2]
        // sRGB 相对亮度
        sum += 0.2126 * r + 0.7152 * g + 0.0722 * b
        n++
      }
      return n ? (sum / n) : null
    } catch (e) {
      // Canvas 污染或数据不可读
      return null
    }
  }

  function chooseInkFor(brightness) {
    // 背景亮 → 深色字；背景暗 → 白字
    return brightness > 160 ? '#0f1226' : '#ffffff'
  }

  async function updateHomeMenuInk() {
    if (!isActive()) return
    const img = await ensureBgImage()
    ensureCanvas()
    drawBgToCanvas(img)
    const buttons = document.querySelectorAll('.home-menu .menu-btn')
    buttons.forEach(btn => {
      const rect = btn.getBoundingClientRect()
      // 采样 5 点（中心 + 四角中点）
      const pts = [
        [rect.left + rect.width * 0.5, rect.top + rect.height * 0.5],
        [rect.left + rect.width * 0.25, rect.top + rect.height * 0.35],
        [rect.right - rect.width * 0.25, rect.top + rect.height * 0.35],
        [rect.left + rect.width * 0.25, rect.bottom - rect.height * 0.35],
        [rect.right - rect.width * 0.25, rect.bottom - rect.height * 0.35],
      ]
      const samples = pts
        .map(([x, y]) => sampleBrightnessAt(x, y, 10))
        .filter(v => typeof v === 'number')
      const avg = samples.length ? (samples.reduce((a, b) => a + b, 0) / samples.length) : null
      const ink = avg == null ? '#ffffff' : chooseInkFor(avg)

      // 智能前景色 + 阴影/边框提升可读性
      const shadow = ink === '#ffffff'
        ? '0 1px 2px rgba(0,0,0,0.55), 0 0 8px rgba(0,0,0,0.20)'
        : '0 1px 0 rgba(255,255,255,0.35)'
      const border = ink === '#ffffff'
        ? 'rgba(255,255,255,0.55)'
        : 'rgba(0,0,0,0.45)'

      btn.style.setProperty('--menu-fg', ink)
      btn.style.setProperty('--menu-shadow', shadow)
      btn.style.setProperty('--menu-border', border)
    })
  }

  function __onResizeOrScroll() {
    // 轻量更新（按钮较少，不做节流）
    updateHomeMenuInk()
  }

  onMounted(() => {
    window.addEventListener('resize', __onResizeOrScroll, { passive: true })
    window.addEventListener('scroll', __onResizeOrScroll, { passive: true })
    if (isActive()) setTimeout(updateHomeMenuInk, 50)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', __onResizeOrScroll)
    window.removeEventListener('scroll', __onResizeOrScroll)
  })

  return { updateHomeMenuInk }
}