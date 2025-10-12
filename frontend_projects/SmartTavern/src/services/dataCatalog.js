// SmartTavern Frontend API Client — Data Catalog (v1)
// Calls backend gateway APIs to list presets/world_books/characters/personas/regex_rules.
// Gateway default: http://localhost:8050 (see core/config/api_config.py in backend)
//
// Usage:
//   import DataCatalog from '@/services/dataCatalog'
//   const res = await DataCatalog.listPresets()
//   console.log(res.items) // [{ file, name, description }, ...]
//
// Notes:
// - All endpoints are POST with empty JSON body as per backend contract (no params needed).
// - CORS is enabled by the gateway (allow-origins: *).
// - Errors are thrown with details; UI should handle and display gracefully.

const DEFAULT_BASE = 'http://localhost:8050/api/modules';

function ensureBase() {
  // Optionally read from global injection if provided in index.html
  // window.ST_API_BASE = 'http://localhost:8050/api/modules'
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
    const err = new Error(`[DataCatalog] Network error: ${networkError?.message || networkError}`);
    err.cause = networkError;
    err.url = url;
    throw err;
  }

  let data = null;
  const text = await resp.text().catch(() => '');
  try {
    data = text ? JSON.parse(text) : null;
  } catch (parseError) {
    const err = new Error(`[DataCatalog] Invalid JSON response (${resp.status}): ${text?.slice(0, 200)}`);
    err.cause = parseError;
    err.status = resp.status;
    err.url = url;
    throw err;
  }

  if (!resp.ok) {
    const err = new Error(`[DataCatalog] HTTP ${resp.status}: ${data && (data.message || data.error) || 'Unknown error'}`);
    err.status = resp.status;
    err.url = url;
    err.details = data;
    throw err;
  }
  return data;
}

 // Public API
const DataCatalog = {
  // All "list_*" endpoints ignore input and return full fields from fixed backend paths.
  listPresets() {
    return postJSON('smarttavern/data_catalog/list_presets', {});
  },
  listWorldBooks() {
    return postJSON('smarttavern/data_catalog/list_world_books', {});
  },
  listCharacters() {
    return postJSON('smarttavern/data_catalog/list_characters', {});
  },
  listPersonas() {
    return postJSON('smarttavern/data_catalog/list_personas', {});
  },
  listRegexRules() {
    return postJSON('smarttavern/data_catalog/list_regex_rules', {});
  },
  listConversations() {
    return postJSON('smarttavern/data_catalog/list_conversations', {});
  },

  // Lightweight cache (in-memory + localStorage)
  _lsKey: 'st.datacache.v1',
  _mem: new Map(),
  _ensureStore() {
    if (typeof window === 'undefined') return {};
    try {
      const raw = localStorage.getItem(this._lsKey);
      return raw ? JSON.parse(raw) : {};
    } catch (_) { return {}; }
  },
  _saveStore(store) {
    if (typeof window === 'undefined') return;
    try { localStorage.setItem(this._lsKey, JSON.stringify(store)); } catch (_) {}
  },
  _ck(type, file) { return `${type}:${String(file || '')}`; },
  _getCached(type, file) {
    const key = this._ck(type, file);
    if (this._mem.has(key)) return this._mem.get(key);
    const store = this._ensureStore();
    return store[key] || null;
  },
  _setCached(type, file, value, persist = true) {
    const key = this._ck(type, file);
    this._mem.set(key, value);
    if (persist) {
      const store = this._ensureStore();
      // naive cap: keep last 50 entries to avoid bloat
      store[key] = value;
      const keys = Object.keys(store);
      if (keys.length > 50) {
        const toDelete = keys.length - 50;
        for (let i = 0; i < toDelete; i++) delete store[keys[i]];
      }
      this._saveStore(store);
    }
  },

  // Detail fetchers with caching
  async _getDetail(type, file, opts = {}) {
    const useCache = opts.useCache !== false;
    if (useCache) {
      const cached = this._getCached(type, file);
      if (cached) return cached;
    }
    const pathMap = {
      preset: 'smarttavern/data_catalog/get_preset_detail',
      worldbook: 'smarttavern/data_catalog/get_world_book_detail',
      character: 'smarttavern/data_catalog/get_character_detail',
      persona: 'smarttavern/data_catalog/get_persona_detail',
      regex: 'smarttavern/data_catalog/get_regex_rule_detail',
      conversation: 'smarttavern/data_catalog/get_conversation_detail',
    };
    const path = pathMap[type];
    if (!path) throw new Error(`[DataCatalog] Unknown detail type: ${type}`);
    const res = await postJSON(path, { file });
    this._setCached(type, file, res, opts.persist !== false);
    return res;
  },

  getPresetDetail(file, opts)   { return this._getDetail('preset', file, opts); },
  getWorldBookDetail(file, opts){ return this._getDetail('worldbook', file, opts); },
  getCharacterDetail(file, opts){ return this._getDetail('character', file, opts); },
  getPersonaDetail(file, opts)  { return this._getDetail('persona', file, opts); },
  getRegexRuleDetail(file, opts){ return this._getDetail('regex', file, opts); },
  getConversationDetail(file, opts){ return this._getDetail('conversation', file, opts); },

  // Update APIs (create/update)
  updatePresetFile(file, content, name, description) {
    return postJSON('smarttavern/data_catalog/update_preset_file', { file, content, name, description });
  },
  updateWorldBookFile(file, content, name, description) {
    return postJSON('smarttavern/data_catalog/update_world_book_file', { file, content, name, description });
  },
  updateCharacterFile(file, content, name, description) {
    return postJSON('smarttavern/data_catalog/update_character_file', { file, content, name, description });
  },
  updatePersonaFile(file, content, name, description) {
    return postJSON('smarttavern/data_catalog/update_persona_file', { file, content, name, description });
  },
  updateRegexRuleFile(file, content, name, description) {
    return postJSON('smarttavern/data_catalog/update_regex_rule_file', { file, content, name, description });
  },

  // Small helper to map backend items to UI cards (icon per type)
  mapToCards(items, type = 'generic') {
    const iconMap = {
      presets: '🧩',
      world_books: '📚',
      characters: '👤',
      personas: '🧠',
      regex_rules: '🧹',
      generic: '📦',
    };
    const icon = iconMap[type] || iconMap.generic;

    return (Array.isArray(items) ? items : []).map((it) => {
      const file = String(it.file || '');
      const name = it.name || file.split('/').pop() || '未命名';
      const desc = it.description || '';
      return { key: file, icon, name, desc, file };
    });
  },
};

export default DataCatalog;