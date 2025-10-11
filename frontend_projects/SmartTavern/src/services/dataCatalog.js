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