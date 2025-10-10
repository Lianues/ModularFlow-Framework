// SmartTavern Theme Runtime - Minimal Store (v1)
// Purpose:
// - Provide a lightweight runtime to apply external beautification themes at runtime
// - Allow importing a theme pack (JSON) with tokens and optional CSS
// - Persist selected theme pack in localStorage (browser-only, non-secure)
// - Reserve hooks for future sandboxed script execution (disabled by default)
// - Emit events so UI can react (e.g., re-apply AppearancePanel overrides)
//
// Notes:
// - This is a JS module; SmartTavern app uses JS in this project.
// - Token policy: keys should be valid CSS custom properties (e.g. "--st-primary").
// - CSS injection: one <style id="st-theme-css"> node in <head>, replaced on each apply.
// - Persistence key: "st.themePack.v1"
// - Security: Scripts in theme packs are NOT executed by default.
// - Precedence: Theme tokens/stylesheet can be overridden by user AppearancePanel changes later.
//
// Usage:
//   import ThemeStore from '@/features/themes/store'
//   await ThemeStore.init()                 // load persisted theme (if any)
//   await ThemeStore.applyThemePack(pack)   // apply new theme pack (persisted by default)
//   ThemeStore.resetTheme()                 // clear theme, remove CSS, wipe persistence
//
// Events:
//   'change'           -> any state change (apply/reset/update)
//   'theme-applied'    -> after theme pack is applied
//   'theme-reset'      -> after theme pack is reset
//
// Pack shape (v1, recommended):
// {
//   "id": "my-theme-id",
//   "name": "My Theme",
//   "version": "1.0.0",
//   "tokens": { "--st-primary": "56 189 248", "--st-accent": "168 85 247", ... },
//   "css": "/* optional additional CSS, can reference the tokens above */",
//   // reserved (disabled by default):
//   "script": {
//     "code": "/* optional sandboxed script string */",
//     "permissions": { "dom": false, "network": false },
//     "scopes": ["chat-threaded", "sandbox"] // logical scopes (docs contract)
//   }
// }

const STORAGE_KEY = 'st.themePack.v1'
const STYLE_TAG_ID = 'st-theme-css'
const META_TAG_ID = 'st-theme-meta'
const VERSION = 'v1'

// Internal event emitter (simple)
function createEmitter() {
  const all = Object.create(null)
  return {
    on(event, cb) {
      if (!all[event]) all[event] = new Set()
      all[event].add(cb)
      return () => { all[event]?.delete(cb) }
    },
    off(event, cb) {
      all[event]?.delete(cb)
    },
    emit(event, payload) {
      if (!all[event]) return
      for (const cb of all[event]) {
        try { cb(payload) } catch (e) { console.error('[ThemeStore] listener error:', e) }
      }
    },
  }
}

// DOM helpers
function ensureStyleTag(id = STYLE_TAG_ID) {
  let el = document.getElementById(id)
  if (!el) {
    el = document.createElement('style')
    el.id = id
    el.type = 'text/css'
    document.head.appendChild(el)
  }
  return el
}

function removeElementById(id) {
  const el = document.getElementById(id)
  if (el && el.parentNode) el.parentNode.removeChild(el)
}

function setMeta(name, content) {
  let el = document.getElementById(META_TAG_ID)
  if (!el) {
    el = document.createElement('meta')
    el.id = META_TAG_ID
    el.setAttribute('data-scope', 'st-theme')
    document.head.appendChild(el)
  }
  el.setAttribute('name', name)
  el.setAttribute('content', content)
}

// Core store
const ThemeStore = (() => {
  const emitter = createEmitter()
  // In-memory state
  let state = {
    version: VERSION,
    // current theme pack (null = none)
    pack: null,            // { id, name, version, tokens, css, script? }
    // bookkeeping for DOM cleanup
    styleId: STYLE_TAG_ID,
    metaId: META_TAG_ID,
  }

  function getVersion() { return state.version }

  function getState() {
    return { ...state, pack: state.pack ? { ...state.pack } : null }
  }

  function getCurrentTheme() {
    return state.pack ? { ...state.pack } : null
  }

  // Persistence
  function saveToStorage() {
    try {
      const payload = state.pack ? {
        version: state.version,
        pack: {
          id: state.pack.id ?? null,
          name: state.pack.name ?? null,
          version: state.pack.version ?? null,
          tokens: state.pack.tokens ?? null,
          css: state.pack.css ?? null,
          // DO NOT persist script by default for safety
        }
      } : null
      if (!payload) {
        localStorage.removeItem(STORAGE_KEY)
      } else {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
      }
    } catch (e) {
      console.warn('[ThemeStore] Failed to save theme to localStorage:', e)
    }
  }

  function loadFromStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return null
      const obj = JSON.parse(raw)
      if (!obj || typeof obj !== 'object' || !obj.pack) return null
      return obj.pack
    } catch (e) {
      console.warn('[ThemeStore] Failed to load theme from localStorage:', e)
      return null
    }
  }

  // Token application
  function applyTokens(tokens) {
    if (!tokens || typeof tokens !== 'object') return
    const root = document.documentElement
    for (const [key, value] of Object.entries(tokens)) {
      // Expect full custom property name, e.g. "--st-primary"
      if (!key.startsWith('--')) continue
      try {
        root.style.setProperty(key, String(value))
      } catch (e) {
        console.warn('[ThemeStore] Failed to set token', key, e)
      }
    }
  }

  // CSS injection
  function injectCSS(cssText) {
    if (!cssText) return
    const style = ensureStyleTag(state.styleId)
    style.textContent = String(cssText)
  }

  function clearCSS() {
    removeElementById(state.styleId)
  }

  // Public API

  async function init() {
    // Load persisted theme and apply it
    const saved = loadFromStorage()
    if (saved) {
      await applyThemePack(saved, { persist: false }) // already persisted
    }
    emitter.emit('change', getState())
    return getState()
  }

  // Pack format is permissive: accepts missing fields
  // options:
  //  - persist: boolean = true
  //  - allowScript: boolean = false (reserved; not executed by default)
  async function applyThemePack(pack, options = {}) {
    const { persist = true, allowScript = false } = options
    const nextPack = { ...pack }

    // Apply tokens first
    if (nextPack.tokens) applyTokens(nextPack.tokens)
    // Apply CSS next
    if (nextPack.css) injectCSS(nextPack.css)
    else clearCSS()

    // Reserved: script execution (disabled)
    if (nextPack.script && allowScript) {
      console.warn('[ThemeStore] Script execution is disabled by default. Ignored for safety.')
    }

    // Update meta (debug info)
    setMeta('st-theme-id', String(nextPack.id ?? ''))
    setMeta('st-theme-name', String(nextPack.name ?? ''))
    setMeta('st-theme-version', String(nextPack.version ?? ''))

    state.pack = nextPack

    if (persist) saveToStorage()

    emitter.emit('theme-applied', getCurrentTheme())
    emitter.emit('change', getState())
    return getCurrentTheme()
  }

  async function resetTheme(options = {}) {
    const { persist = true } = options

    // Clear tokens we know? We cannot know all keys; avoid mass removal.
    // Rely on app defaults and AppearancePanel overrides to take precedence.
    clearCSS()

    state.pack = null
    if (persist) saveToStorage()

    // Clear meta
    removeElementById(state.metaId)

    emitter.emit('theme-reset')
    emitter.emit('change', getState())
  }

  // Utility to update a single token dynamically (and remember into current pack if present)
  function setToken(name, value, options = {}) {
    if (!name || !name.startsWith?.('--')) return
    applyTokens({ [name]: value })
    if (state.pack) {
      state.pack.tokens = state.pack.tokens || {}
      state.pack.tokens[name] = value
      if (options.persist !== false) saveToStorage()
      emitter.emit('change', getState())
    }
  }

  // Subscribe helper
  function on(event, cb) { return emitter.on(event, cb) }
  function off(event, cb) { return emitter.off(event, cb) }

  // Back-compat alias
  function subscribe(cb) { return on('change', cb) }

  return {
    // lifecycle
    init,
    // apply/reset
    applyThemePack,
    resetTheme,
    // state
    getState,
    getCurrentTheme,
    getVersion,
    // tokens
    setToken,
    // events
    on, off, subscribe,
    // low-level helpers (exported for advanced usage)
    applyTokens,
    injectCSS,
    clearCSS,
    // constants
    STORAGE_KEY,
    STYLE_TAG_ID,
    META_TAG_ID,
    VERSION,
  }
})()

export default ThemeStore