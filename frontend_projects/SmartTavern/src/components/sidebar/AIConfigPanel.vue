<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

const props = defineProps({
  anchorLeft: { type: Number, default: 308 }, // 12 + 280 + 16，与其他面板一致
  width: { type: Number, default: 560 },
  zIndex: { type: Number, default: 59 },
  top: { type: Number, default: 64 },
  bottom: { type: Number, default: 12 },
  title: { type: String, default: 'AI配置 AI Config' },
  currentPreset: { type: Object, default: null }, // 当前使用的预设数据
})

const emit = defineEmits(['close'])

const panelStyle = computed(() => ({
  position: 'fixed',
  left: props.anchorLeft + 'px',
  top: props.top + 'px',
  bottom: props.bottom + 'px',
  width: props.width + 'px',
  zIndex: String(props.zIndex),
}))

function close(){ emit('close') }

onMounted(() => {
  window.lucide?.createIcons?.()
})

/** =============== 本地占位状态（不接后端） =============== */
const providers = ['openai', 'anthropic', 'gemini', 'openai_compatible', 'custom']

const form = reactive({
  // 基础
  provider: 'openai',
  base_url: 'https://api.openai.com/v1',
  api_key: '',
  model_id: '',
  // 解码参数
  max_tokens: 2048,
  temperature: 0.7,
  top_p: 1.0,
  presence_penalty: 0,
  frequency_penalty: 0,
  stream: false,
  // 网络与日志
  timeout: 60,
  connect_timeout: 10,
  enable_logging: false,
  // 自定义参数
  custom_params_json: '',
  // 厂商高级
  gemini: {
    topP: 1.0,
    maxOutputTokens: 2048,
    topK: null,
    candidateCount: null,
    stopSequences: '',
    responseMimeType: '',
    safetySettings: '',
    customParams: ''
  },
  anthropic: {
    stop_sequences: '',
    enable_thinking: false,
    thinking_budget: 16000
  }
})
// 请求参数启用开关（默认启用）
const apiToggleKeys = ['max_tokens', 'temperature', 'top_p', 'presence_penalty', 'frequency_penalty', 'stream']
const apiToggles = reactive(Object.fromEntries(apiToggleKeys.map(k => [k, true])))

const showGemini = computed(() => form.provider === 'gemini')
const showAnthropic = computed(() => form.provider === 'anthropic')

// 预设API配置覆盖检测
const presetApiConfig = computed(() => {
  if (!props.currentPreset?.api_config) return null
  const config = props.currentPreset.api_config
  if (!config.enabled) return null
  
  // 获取启用的字段列表
  const enabledFields = config.enabled_fields || []
  if (enabledFields.length === 0) return null
  
  // 提取启用字段的值
  const enabledParams = {}
  enabledFields.forEach(field => {
    if (config[field] !== undefined) {
      enabledParams[field] = config[field]
    }
  })
  
  return {
    enabled: true,
    enabledFields,
    params: enabledParams
  }
})

const showPresetOverride = computed(() => !!presetApiConfig.value)

// 模型列表下拉菜单
const showModelDropdown = ref(false)
const modelListPlaceholder = ref([
  'gpt-4o-mini',
  'gpt-4o',
  'gpt-4-turbo',
  'gpt-3.5-turbo',
  'claude-3-5-sonnet-20241022',
  'claude-3-5-haiku-20241022',
  'gemini-2.0-flash-exp',
  'gemini-1.5-pro'
])

function selectModel(modelId) {
  form.model_id = modelId
  showModelDropdown.value = false
}

function toggleModelDropdown() {
  showModelDropdown.value = !showModelDropdown.value
}

// 文本与JSON辅助
function parseList(s) {
  if (!s) return []
  return String(s).split(',').map(x => x.trim()).filter(Boolean)
}
function parseJSONSafe(s) {
  if (!s) return undefined
  try {
    const obj = JSON.parse(s)
    return obj && typeof obj === 'object' ? obj : undefined
  } catch {
    return undefined
  }
}

// 预览：合成 llm_api/chat 的示例入参（只读展示）
const previewPayload = computed(() => {
  const payload = {
    provider: form.provider,
    api_key: form.api_key || '••••••',
    base_url: form.base_url,
    messages: [{ role: 'user', content: '示例输入' }],
    model: form.model_id || undefined,
    timeout: form.timeout,
    connect_timeout: form.connect_timeout,
    enable_logging: form.enable_logging
  }
  if (apiToggles.max_tokens) payload.max_tokens = form.max_tokens
  if (apiToggles.temperature) payload.temperature = form.temperature
  if (apiToggles.stream) payload.stream = form.stream
  if (apiToggles.top_p && form.top_p != null) payload.top_p = form.top_p
  if (apiToggles.presence_penalty && form.presence_penalty != null) payload.presence_penalty = form.presence_penalty
  if (apiToggles.frequency_penalty && form.frequency_penalty != null) payload.frequency_penalty = form.frequency_penalty

  // 通用自定义参数
  const baseCustomParams = parseJSONSafe(form.custom_params_json) || {}
  
  // 应用预设覆盖
  if (presetApiConfig.value) {
    const presetParams = presetApiConfig.value.params
    Object.keys(presetParams).forEach(key => {
      if (presetParams[key] !== undefined) {
        payload[key] = presetParams[key]
      }
    })
  }

  if (form.provider === 'gemini') {
    const gen = {
      temperature: form.temperature,
      topP: form.gemini.topP,
      maxOutputTokens: form.gemini.maxOutputTokens
    }
    if (form.gemini.topK != null) gen.topK = form.gemini.topK
    if (form.gemini.candidateCount != null) gen.candidateCount = form.gemini.candidateCount
    if (form.gemini.stopSequences) gen.stopSequences = parseList(form.gemini.stopSequences)
    if (form.gemini.responseMimeType) gen.responseMimeType = form.gemini.responseMimeType

    const safety = parseJSONSafe(form.gemini.safetySettings)
    const cust = parseJSONSafe(form.gemini.customParams) || {}
    payload.custom_params = { ...baseCustomParams, ...cust, generationConfig: gen }
    if (safety) payload.safety_settings = safety
  } else if (form.provider === 'anthropic') {
    const cust = {}
    if (form.anthropic.stop_sequences) cust.stop_sequences = parseList(form.anthropic.stop_sequences)
    if (form.anthropic.enable_thinking) {
      cust.enable_thinking = true
      cust.thinking_budget = form.anthropic.thinking_budget
    }
    payload.custom_params = { ...baseCustomParams, ...cust }
  } else {
    // 其他供应商直接使用通用自定义参数
    if (Object.keys(baseCustomParams).length > 0) {
      payload.custom_params = baseCustomParams
    }
  }

  return payload
})
</script>

<template>
  <div
    data-scope="aiconfig-view"
    class="ai-panel glass"
    :style="panelStyle"
  >
    <header class="ai-header">
      <div class="ai-title">
        <span class="ai-icon"><i data-lucide="plug"></i></span>
        {{ props.title }}
      </div>
      <button class="ai-close" type="button" title="关闭" @click="close">✕</button>
    </header>

    <CustomScrollbar class="ai-body">
      <!-- 基础配置 -->
      <section class="ai-section">
        <div class="ai-card">
          <div class="ai-card-title">
            <i data-lucide="plug" class="icon-16"></i>
            <span>基础配置</span>
          </div>
          <div class="ai-grid-rows">
            <div class="ai-row">
              <label class="ai-label">Provider</label>
              <select v-model="form.provider" class="ai-input">
                <option v-for="p in providers" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
            <div class="ai-row">
              <label class="ai-label">Base URL</label>
              <input v-model="form.base_url" class="ai-input" placeholder="https://api.openai.com/v1" />
            </div>
            <div class="ai-row">
              <label class="ai-label">API Key</label>
              <input v-model="form.api_key" type="password" class="ai-input" placeholder="占位，仅前端演示，不会保存" />
            </div>
            <div class="ai-row">
              <label class="ai-label">模型ID</label>
              <div class="ai-model-selector">
                <input
                  v-model="form.model_id"
                  class="ai-input"
                  placeholder="如 gpt-4o-mini / claude-3-5-sonnet..."
                />
                <button
                  type="button"
                  class="ai-model-dropdown-btn"
                  @click="toggleModelDropdown"
                  title="选择模型"
                >
                  <i data-lucide="chevron-down" class="icon-16"></i>
                </button>
                <div v-if="showModelDropdown" class="ai-model-dropdown">
                  <div class="ai-model-dropdown-header">
                    <span>选择模型</span>
                    <span class="ai-model-hint">（占位，后续接入 list_models）</span>
                  </div>
                  <div
                    v-for="model in modelListPlaceholder"
                    :key="model"
                    class="ai-model-item"
                    @click="selectModel(model)"
                  >
                    {{ model }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 解码参数 -->
      <section class="ai-section">
        <div class="ai-card">
          <div class="ai-card-title">
            <i data-lucide="sliders-horizontal" class="icon-16"></i>
            <span>请求参数</span>
          </div>
          <div class="ai-grid-2">
            <div class="ai-row ai-row-col">
              <div class="ai-row-head">
                <label class="ai-label">max_tokens</label>
                <label class="ai-toggle">
                  <input type="checkbox" v-model="apiToggles.max_tokens" />
                  <span>启用</span>
                </label>
              </div>
              <input v-model.number="form.max_tokens" type="number" min="1" class="ai-input" :disabled="!apiToggles.max_tokens" />
            </div>
            <div class="ai-row ai-row-col">
              <div class="ai-row-head">
                <label class="ai-label">temperature</label>
                <label class="ai-toggle">
                  <input type="checkbox" v-model="apiToggles.temperature" />
                  <span>启用</span>
                </label>
              </div>
              <input v-model.number="form.temperature" type="number" step="0.01" min="0" class="ai-input" :disabled="!apiToggles.temperature" />
            </div>
            <div class="ai-row ai-row-col">
              <div class="ai-row-head">
                <label class="ai-label">top_p</label>
                <label class="ai-toggle">
                  <input type="checkbox" v-model="apiToggles.top_p" />
                  <span>启用</span>
                </label>
              </div>
              <input v-model.number="form.top_p" type="number" step="0.01" min="0" max="1" class="ai-input" :disabled="!apiToggles.top_p" />
            </div>
            <div class="ai-row ai-row-col">
              <div class="ai-row-head">
                <label class="ai-label">presence_penalty</label>
                <label class="ai-toggle">
                  <input type="checkbox" v-model="apiToggles.presence_penalty" />
                  <span>启用</span>
                </label>
              </div>
              <input v-model.number="form.presence_penalty" type="number" step="0.01" class="ai-input" :disabled="!apiToggles.presence_penalty" />
            </div>
            <div class="ai-row ai-row-col">
              <div class="ai-row-head">
                <label class="ai-label">frequency_penalty</label>
                <label class="ai-toggle">
                  <input type="checkbox" v-model="apiToggles.frequency_penalty" />
                  <span>启用</span>
                </label>
              </div>
              <input v-model.number="form.frequency_penalty" type="number" step="0.01" class="ai-input" :disabled="!apiToggles.frequency_penalty" />
            </div>
            <div class="ai-row ai-row-col">
              <div class="ai-row-head">
                <label class="ai-label">流式输出</label>
                <label class="ai-toggle">
                  <input type="checkbox" v-model="apiToggles.stream" />
                  <span>启用</span>
                </label>
              </div>
              <input type="checkbox" v-model="form.stream" :disabled="!apiToggles.stream" />
            </div>
          </div>
        </div>
      </section>

      <!-- 网络与日志 -->
      <section class="ai-section">
        <div class="ai-card">
          <div class="ai-card-title">
            <i data-lucide="network" class="icon-16"></i>
            <span>网络与日志</span>
          </div>
          <div class="ai-grid-2">
            <div class="ai-row">
              <label class="ai-label">连接超时（秒）</label>
              <input v-model.number="form.connect_timeout" type="number" min="0" class="ai-input" />
            </div>
            <div class="ai-row">
              <label class="ai-label">请求超时（秒）</label>
              <input v-model.number="form.timeout" type="number" min="0" class="ai-input" />
            </div>
            <div class="ai-row">
              <label class="ai-label">启用日志</label>
              <input type="checkbox" v-model="form.enable_logging" />
            </div>
          </div>
        </div>
      </section>

      <!-- 自定义参数 -->
      <section class="ai-section">
        <div class="ai-card">
          <div class="ai-card-title">
            <i data-lucide="code" class="icon-16"></i>
            <span>自定义参数</span>
          </div>
          <div class="ai-grid-rows">
            <div class="ai-row ai-row-col">
              <label class="ai-label">custom_params（JSON）</label>
              <textarea
                v-model="form.custom_params_json"
                class="ai-input"
                rows="4"
                placeholder='{ "seed": 42, "logprobs": true }'
              ></textarea>
              <p class="ai-hint">输入JSON格式的自定义参数，将合并到请求的 custom_params 字段中。</p>
            </div>
          </div>
        </div>

      <!-- 预设API配置覆盖 -->
      <section v-if="showPresetOverride" class="ai-section">
        <div class="ai-card ai-card-warning">
          <div class="ai-card-title">
            <i data-lucide="alert-triangle" class="icon-16"></i>
            <span>预设API配置覆盖</span>
          </div>
          <div class="ai-preset-warning">
            <p class="ai-warning-text">
              ⚠️ 当前预设启用了API配置，以下参数将覆盖上方全局配置的同名参数：
            </p>
          </div>
          <div class="ai-grid-2">
            <div 
              v-for="(value, key) in presetApiConfig.params" 
              :key="key"
              class="ai-row ai-row-readonly"
            >
              <label class="ai-label">{{ key }}</label>
              <div class="ai-value">{{ value }}</div>
            </div>
          </div>
        </div>
      </section>
      </section>

      <!-- 厂商高级：Gemini -->
      <section class="ai-section" v-if="showGemini">
        <div class="ai-card">
          <div class="ai-card-title">
            <i data-lucide="orbit" class="icon-16"></i>
            <span>Gemini 高级配置</span>
          </div>
          <div class="ai-grid-2">
            <div class="ai-row">
              <label class="ai-label">generation.topP</label>
              <input v-model.number="form.gemini.topP" type="number" step="0.01" min="0" max="1" class="ai-input" />
            </div>
            <div class="ai-row">
              <label class="ai-label">generation.maxOutputTokens</label>
              <input v-model.number="form.gemini.maxOutputTokens" type="number" min="1" class="ai-input" />
            </div>
            <div class="ai-row">
              <label class="ai-label">generation.topK</label>
              <input v-model.number="form.gemini.topK" type="number" min="0" class="ai-input" />
            </div>
            <div class="ai-row">
              <label class="ai-label">generation.candidateCount</label>
              <input v-model.number="form.gemini.candidateCount" type="number" min="1" class="ai-input" />
            </div>
            <div class="ai-row">
              <label class="ai-label">generation.stopSequences</label>
              <input v-model="form.gemini.stopSequences" class="ai-input" placeholder="以英文逗号分隔" />
            </div>
            <div class="ai-row">
              <label class="ai-label">generation.responseMimeType</label>
              <input v-model="form.gemini.responseMimeType" class="ai-input" placeholder="text/plain 或 text/html 等" />
            </div>
            <div class="ai-row ai-row-col">
              <label class="ai-label">safetySettings（JSON）</label>
              <textarea v-model="form.gemini.safetySettings" class="ai-input" rows="3" placeholder='{ "HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE" }'></textarea>
            </div>
            <div class="ai-row ai-row-col">
              <label class="ai-label">customParams（JSON）</label>
              <textarea v-model="form.gemini.customParams" class="ai-input" rows="3" placeholder='{ "responseLogprobs": false }'></textarea>
            </div>
          </div>
        </div>
      </section>

      <!-- 厂商高级：Anthropic -->
      <section class="ai-section" v-if="showAnthropic">
        <div class="ai-card">
          <div class="ai-card-title">
            <i data-lucide="brain" class="icon-16"></i>
            <span>Anthropic 高级配置</span>
          </div>
          <div class="ai-grid-2">
            <div class="ai-row">
              <label class="ai-label">stop_sequences</label>
              <input v-model="form.anthropic.stop_sequences" class="ai-input" placeholder="以英文逗号分隔" />
            </div>
            <div class="ai-row">
              <label class="ai-label">enable_thinking</label>
              <label class="ai-switch">
                <input type="checkbox" v-model="form.anthropic.enable_thinking" />
                <span>启用</span>
              </label>
            </div>
            <div class="ai-row" :class="{ 'ai-disabled': !form.anthropic.enable_thinking }">
              <label class="ai-label">thinking_budget</label>
              <input v-model.number="form.anthropic.thinking_budget" type="number" min="0" class="ai-input" :disabled="!form.anthropic.enable_thinking" />
            </div>
          </div>
        </div>
      </section>

      <!-- 诊断（占位） -->
      <section class="ai-section">
        <div class="ai-card">
          <div class="ai-card-title">
            <i data-lucide="stethoscope" class="icon-16"></i>
            <span>诊断（占位）</span>
          </div>
          <div class="ai-actions">
            <button type="button" class="ai-btn" disabled title="即将接入">get_defaults</button>
            <button type="button" class="ai-btn" disabled title="即将接入">list_models</button>
            <button type="button" class="ai-btn" disabled title="即将接入">health</button>
          </div>
          <p class="ai-hint">以上按钮为占位，稍后接入后端网关 API（llm_api/get_defaults、llm_api/list_models、llm_api/health）。</p>
        </div>
      </section>

      <!-- JSON 预览 -->
      <section class="ai-section">
        <div class="ai-card">
          <div class="ai-card-title">
            <i data-lucide="file-code" class="icon-16"></i>
            <span>llm_api/chat 入参预览（只读）</span>
          </div>
          <pre class="ai-pre">{{ JSON.stringify(previewPayload, null, 2) }}</pre>
        </div>
      </section>
</CustomScrollbar>
  </div>
</template>

<style scoped>
.ai-panel {
  display: grid;
  grid-template-rows: auto 1fr;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(var(--st-surface), 0.92);
  backdrop-filter: blur(8px) saturate(130%);
  -webkit-backdrop-filter: blur(8px) saturate(130%);
  box-shadow: var(--st-shadow-md);
  overflow: hidden;
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--st-border), 0.85);
}
.ai-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.ai-icon i { width: 18px; height: 18px; display: inline-block; }
.ai-close {
  appearance: none;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.22,.61,.36,1), background .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s cubic-bezier(.22,.61,.36,1);
}
.ai-close:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}

.ai-body {
  padding: 12px;
  overflow: hidden;
}



.ai-card {
  border: 1px solid rgb(var(--st-border));
  border-radius: var(--st-radius-md);
  background: rgb(var(--st-surface));
  padding: 14px;
  text-align: left;
  transition: background .12s ease, border-color .12s ease, transform .12s ease, box-shadow .12s ease;
}
.ai-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--st-shadow-sm);
}
.ai-card-icon { font-size: 22px; margin-bottom: 6px; }
.ai-card-title {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  margin-bottom: 4px;
}
.ai-card-desc {
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.7);
  line-height: 1.4;
}
/* =============== 新增：表单与分区样式（占位） =============== */
.icon-16 { width: 16px; height: 16px; stroke: currentColor; }

.ai-section { margin-top: 12px; }

.ai-grid-rows { display: grid; gap: 10px; }
.ai-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 12px; }
@media (max-width: 720px) { .ai-grid-2 { grid-template-columns: 1fr; } }

.ai-row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 10px;
  align-items: center;
}
.ai-row.ai-row-col {
  grid-template-columns: 1fr;
  align-items: start;
}
.ai-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--st-color-text), 0.85);
}
.ai-input, .ai-input[type="number"], .ai-input[type="password"], .ai-input[type="text"], select.ai-input, textarea.ai-input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface-2));
  color: rgb(var(--st-color-text));
}
.ai-switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: rgb(var(--st-color-text));
  font-size: 12px;
}
.ai-actions { display: flex; gap: 8px; margin-top: 8px; }
.ai-btn {
  appearance: none;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: not-allowed;
  opacity: 0.7;
}
.ai-hint {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.7);
}
.ai-pre {
  margin: 6px 0 0;
  padding: 10px;
  border-radius: 8px;
  background: rgb(var(--st-surface-2));
  border: 1px solid rgb(var(--st-border));
  color: rgb(var(--st-color-text));
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}
.ai-disabled { opacity: 0.6; }

/* 模型选择器样式 */
.ai-model-selector {
  position: relative;
  display: flex;
  gap: 4px;
  align-items: center;
}
.ai-model-selector .ai-input {
  flex: 1;
}
.ai-model-dropdown-btn {
  appearance: none;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface-2));
  color: rgb(var(--st-color-text));
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ai-model-dropdown-btn:hover {
  background: rgb(var(--st-surface));
  transform: translateY(-1px);
}
.ai-model-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  min-width: 280px;
  max-height: 320px;
  overflow-y: auto;
  background: rgb(var(--st-surface));
  border: 1px solid rgb(var(--st-border));
  border-radius: 8px;
  box-shadow: var(--st-shadow-md);
  z-index: 100;
}
.ai-model-dropdown-header {
  padding: 8px 12px;
  border-bottom: 1px solid rgb(var(--st-border));
  font-size: 12px;
  font-weight: 600;
  color: rgb(var(--st-color-text));
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ai-model-hint {
  font-size: 11px;
  font-weight: 400;
  color: rgba(var(--st-color-text), 0.6);
}
.ai-model-item {
  padding: 10px 12px;
  cursor: pointer;
  font-size: 13px;
  color: rgb(var(--st-color-text));
  transition: background 0.15s ease;
  border-bottom: 1px solid rgba(var(--st-border), 0.5);
}
.ai-model-item:last-child {
  border-bottom: none;
}
.ai-model-item:hover {
  background: rgba(var(--st-primary), 0.1);
}

[data-theme="dark"] .ai-input { background: rgb(var(--st-surface)); }
[data-theme="dark"] .ai-model-dropdown-btn { background: rgb(var(--st-surface)); }

/* 请求参数启用头 */
.ai-row-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.ai-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgb(var(--st-color-text));
}

/* 预设覆盖警告样式 */
.ai-card-warning {
  border-color: rgba(255, 193, 7, 0.5);
  background: rgba(255, 193, 7, 0.05);
}
[data-theme="dark"] .ai-card-warning {
  background: rgba(255, 193, 7, 0.08);
}
.ai-preset-warning {
  margin-bottom: 12px;
}
.ai-warning-text {
  margin: 0;
  font-size: 13px;
  color: rgb(var(--st-color-text));
  line-height: 1.5;
}
.ai-row-readonly {
  pointer-events: none;
}
.ai-value {
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(var(--st-border), 0.1);
  color: rgb(var(--st-color-text));
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

</style>