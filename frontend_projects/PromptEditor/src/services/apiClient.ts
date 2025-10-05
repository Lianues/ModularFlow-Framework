/**
 * 轻量 API 客户端
 * - 遵循 DEVELOPMENT_NOTES：默认走 http://localhost:8050 + /api
 * - 仅实现 workflow POST 能力：/api/workflow/{path}
 */
const DEFAULT_BASE_URL = 'http://localhost:8050'
const DEFAULT_API_PREFIX = '/api'

type APIConfig = {
  baseURL: string
  apiPrefix: string
}

const cfg: APIConfig = {
  baseURL: DEFAULT_BASE_URL,
  apiPrefix: DEFAULT_API_PREFIX,
}

let inited = false
let initPromise: Promise<void> | null = null


// Deprecated: external config file is no longer used (see DEVELOPMENT_NOTES.md)

export async function ensureApiClientReady(): Promise<void> {
  if (inited) return
  if (!initPromise) {
    initPromise = (async () => {
      // external config removed; use defaults from core/config/api_config.py
      inited = true
    })()
  }
  return initPromise
}

export function getApiConfig(): Readonly<APIConfig> {
  return { ...cfg }
}

async function request(path: string, init: RequestInit): Promise<any> {
  await ensureApiClientReady()
  const url =
    cfg.baseURL.replace(/\/+$/, '') +
    cfg.apiPrefix +
    (path.startsWith('/') ? path : '/' + path)

  const res = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers || {}),
    },
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) {
    return res.json()
  }
  return res.text()
}

/**
 * POST /api/workflow/{path}
 */
export async function postWorkflow(path: string, body: any): Promise<any> {
  const safePath = path.replace(/^\/+/, '')
  return request('/workflow/' + safePath, {
    method: 'POST',
    body: JSON.stringify(body ?? {}),
  })
}