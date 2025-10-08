<script setup>
import { reactive, computed, ref, onMounted, nextTick } from 'vue'
import cfg from '@/data/editor_pages.json'

// props: 页面类型 + 基本信息（来自列表项）
const props = defineProps({
  type: { type: String, default: 'preset' }, // 'preset' | 'regex'
  name: { type: String, default: '' },
  desc: { type: String, default: '' },
})

// 选择 JSON 配置页
const page = computed(() => (props.type === 'regex' ? cfg.regex : cfg.presets))
const isPreset = computed(() => props.type !== 'regex')
const isRegex = computed(() => props.type === 'regex')

// UI 状态（面板开合 + 表单占位值）
const ui = reactive({
  // header
  fileTitle: props.name || '',

  // presets - api panel switches/fields
  apiOpen: isPreset.value ? (page.value?.apiPanel?.defaultOpen ?? false) : false,
  switches: {},
  fields: {},

  // presets - sections open state
  sectionsOpen: {},

  // presets - special select / custom inputs (占位状态)
  specialSelect: '',
  newRelId: '',
  newRelName: '',
  newChatId: '',
  newChatName: '',
  newRegexId: '',
  newRegexName: '',

  // regex - toolbar / new rule inputs (占位状态)
  regexNewId: '',
  regexNewName: '',
})

// 初始化开关与字段默认值
function initFromJson() {
  if (isPreset.value) {
    // switches
    const sw = page.value?.apiPanel?.switches || []
    for (const s of sw) ui.switches[s.key] = s.default ?? false

    // fields
    const fields = page.value?.apiPanel?.fields || []
    for (const f of fields) ui.fields[f.key] = f.default

    // sections open
    const sections = page.value?.sections || []
    for (const sec of sections) {
      ui.sectionsOpen[sec.key] = !!sec.defaultOpen
      // groups下的 defaultOpen 也记一下
      if (Array.isArray(sec.groups)) {
        for (const grp of sec.groups) {
          ui.sectionsOpen[`${sec.key}.${grp.key}`] = !!grp.defaultOpen
        }
      }
    }
  }
}
onMounted(() => {
  initFromJson()
  nextTick(() => (window?.lucide?.createIcons?.()))
})

// 占位交互（不写入后端，仅用于 UI 展示）
function onRename() {
  // 仅 UI 占位
}
function onToggleSection(key) {
  ui.sectionsOpen[key] = !ui.sectionsOpen[key]
}
function onToggleApiPanel() {
  ui.apiOpen = !ui.apiOpen
}
function onToolbarAction(key) {
  // import/export/save/reset 等占位动作
}
function onAddPresetSpecial() {
  // JSON 驱动 UI 占位
}
function onAddPresetRelative() {
  // JSON 驱动 UI 占位
}
function onAddPresetInChat() {
  // JSON 驱动 UI 占位
}
function onAddRegexRule() {
  // JSON 驱动 UI 占位
}
function onRegexToolbarInput(key, ev) {
  const v = ev && ev.target ? ev.target.value : ''
  if (key === 'newId') ui.regexNewId = v
  else ui.regexNewName = v
}
</script>

<template>
  <div data-scope="editor-json-viewer" class="ejv-root">
    <!-- Header -->
    <div class="ejv-card">
      <div class="ejv-header">
        <div class="ejv-title">
          <span class="ejv-icon">{{ page.icon || (isPreset ? '🎛️' : '🧹') }}</span>
          <h2>{{ page.title }}</h2>
        </div>
        <div class="ejv-file">
          <label class="ejv-label">{{ (page.fileLabel || (isPreset ? '预设文件' : '正则文件')) + '：' }}</label>
          <input class="ejv-input" v-model="ui.fileTitle" :placeholder="(isPreset ? 'Preset.json' : 'Regex.json')" />
          <button
            v-if="page?.header?.renameEnabled"
            class="ejv-btn ejv-btn-outline"
            @click="onRename"
          >{{ page?.header?.renameButtonText || '重命名' }}</button>
        </div>
      </div>
      <p v-if="page?.header?.subtitle" class="ejv-muted">{{ page.header.subtitle }}</p>
      <p v-if="desc" class="ejv-desc">{{ desc }}</p>
    </div>

    <!-- Preset - API 配置 -->
    <div v-if="isPreset" class="ejv-card">
      <button type="button" class="ejv-panel-toggle" @click="onToggleApiPanel">
        <div class="ejv-panel-toggle-left">
          <i data-lucide="server-cog" class="w-4 h-4 text-black"></i>
          <span> {{ page.apiPanel?.title || 'API 配置' }} </span>
        </div>
        <i data-lucide="chevron-down" class="w-4 h-4 text-black" :class="ui.apiOpen ? 'rotate-180' : ''"></i>
      </button>

      <div v-show="ui.apiOpen" class="ejv-panel-body">
        <!-- 开关列表 -->
        <div class="ejv-row">
          <template v-for="s in (page.apiPanel?.switches || [])" :key="s.key">
            <div class="ejv-switch">
              <label class="ejv-switch-label">{{ s.label || s.key }}</label>
              <label class="ejv-switch-ctrl">
                <input type="checkbox" v-model="ui.switches[s.key]" />
                <span class="ejv-switch-text">{{ ui.switches[s.key] ? '已启用' : '未启用' }}</span>
              </label>
            </div>
          </template>
        </div>
        <!-- 字段编辑 -->
        <div class="ejv-grid-2">
          <template v-for="f in (page.apiPanel?.fields || [])" :key="f.key">
            <div class="ejv-field">
              <div class="ejv-field-head">
                <label>{{ f.key }}</label>
                <span class="ejv-field-unit">{{ f.type }}</span>
              </div>
              <input
                v-if="f.type === 'number'"
                type="number"
                class="ejv-input w-full"
                :min="f.min"
                :max="f.max"
                :step="f.step || 1"
                v-model.number="ui.fields[f.key]"
              />
              <label v-else-if="f.type === 'boolean'" class="ejv-switch-ctrl">
                <input type="checkbox" v-model="ui.fields[f.key]" />
                <span class="ejv-switch-text">{{ ui.fields[f.key] ? 'true' : 'false' }}</span>
              </label>
              <input
                v-else
                type="text"
                class="ejv-input w-full"
                v-model="ui.fields[f.key]"
              />
              <div class="ejv-help">当前：{{ String(ui.fields[f.key]) }}</div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Preset - Sections -->
    <template v-if="isPreset">
      <template v-for="sec in (page.sections || [])" :key="sec.key">
        <div class="ejv-card">
          <button type="button" class="ejv-panel-toggle" @click="onToggleSection(sec.key)">
            <div class="ejv-panel-toggle-left">
              <i data-lucide="edit-3" class="w-4 h-4 text-black"></i>
              <span> {{ sec.title }} </span>
            </div>
            <i data-lucide="chevron-down" class="w-4 h-4 text-black" :class="ui.sectionsOpen[sec.key] ? 'rotate-180' : ''"></i>
          </button>

          <div v-show="ui.sectionsOpen[sec.key]" class="ejv-panel-body">
            <!-- groups -->
            <template v-for="grp in (sec.groups || [])" :key="grp.key">
              <div class="ejv-subsection">
                <button type="button" class="ejv-sub-toggle" @click="onToggleSection(`${sec.key}.${grp.key}`)">
                  <div class="ejv-sub-left">
                    <i data-lucide="layers" class="w-4 h-4 text-black"></i>
                    <span> {{ grp.title }} </span>
                  </div>
                  <i data-lucide="chevron-down" class="w-4 h-4 text-black" :class="ui.sectionsOpen[`${sec.key}.${grp.key}`] ? 'rotate-180' : ''"></i>
                </button>

                <!-- 新增工具行 -->
                <div v-show="ui.sectionsOpen[`${sec.key}.${grp.key}`]">
                  <!-- special select -->
                  <div v-if="grp.specialSelect" class="ejv-row ejv-row-space">
                    <div class="ejv-flex">
                      <select v-model="ui.specialSelect" class="ejv-input">
                        <option value="" disabled>{{ grp.specialSelect.placeholder }}</option>
                        <option v-for="op in grp.specialSelect.options" :key="op.id" :value="op.id">
                          {{ op.name }} (id: {{ op.id }})
                        </option>
                      </select>
                      <button class="ejv-btn ejv-btn-outline" :disabled="!ui.specialSelect" @click="onAddPresetSpecial">
                        {{ (grp.newButtons?.find(b => b.key==='addSpecial')?.label) || '添加特殊' }}
                      </button>
                    </div>
                  </div>

                  <!-- custom inputs -->
                  <div v-if="grp.customInputs" class="ejv-row ejv-row-end ejv-row-gap">
                    <template v-for="ci in grp.customInputs" :key="ci.key">
                      <input
                        v-if="ci.key!=='submit'"
                        class="ejv-input"
                        :style="{ width: (ci.width||128) + 'px' }"
                        :placeholder="ci.placeholder"
                        v-model="ui[ci.key]"
                      />
                      <button
                        v-else
                        class="ejv-btn ejv-btn-outline"
                        @click="grp.key==='relative' ? onAddPresetRelative() : onAddPresetInChat()"
                      >{{ ci.label }}</button>
                    </template>
                  </div>

                  <!-- 占位条目卡 -->
                  <div class="ejv-list">
                    <div class="ejv-item">
                      <div class="ejv-item-head">
                        <div class="ejv-chip">{{ grp.key === 'relative' ? 'Relative' : 'In-Chat' }}</div>
                        <div class="ejv-item-title">{{ grp.key === 'relative' ? '系统前置提示词（占位）' : '对话内提示词（占位）' }}</div>
                      </div>
                      <div class="ejv-item-body">
                        <p class="ejv-item-text">
                          {{ grp.key==='relative'
                            ? '用于相对位置插入的系统提示（示例，仅 UI 占位）'
                            : '在对话过程中生效的提示词条目（示例，仅 UI 占位）'
                          }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- sec.customInputs（如 regex 小段） -->
            <div v-if="sec.customInputs" class="ejv-row ejv-row-end ejv-row-gap">
              <template v-for="ci in sec.customInputs" :key="ci.key">
                <input
                  v-if="ci.key!=='submit'"
                  class="ejv-input"
                  :style="{ width: (ci.width||128) + 'px' }"
                  :placeholder="ci.placeholder"
                  v-model="ui[ci.key]"
                />
                <button
                  v-else
                  class="ejv-btn ejv-btn-outline"
                  @click="onAddPresetInChat"
                >{{ ci.label }}</button>
              </template>
            </div>
          </div>
        </div>
      </template>

      <!-- Preset 预览区 -->
      <div v-if="false" class="ejv-card">
        <div class="ejv-preview">
          <div v-for="(pv, idx) in page.preview.sections" :key="idx" class="ejv-preview-box">
            <div class="ejv-preview-title">{{ pv.title }}</div>
            <div class="ejv-preview-body" v-html="pv.content"></div>
          </div>
        </div>
      </div>
    </template>

    <!-- Regex Toolbar -->
    <div v-if="isRegex" class="ejv-card">
      <div class="ejv-toolbar">
        <div class="ejv-stats">
          {{ (page?.toolbar?.statsLabel || '规则数量：') }} {{ (cfg.regex?.examples?.length || 0) }}
        </div>
        <div class="ejv-flex">
          <button
            v-for="act in (page?.toolbar?.actions||[])"
            :key="act.key"
            class="ejv-btn ejv-btn-outline ejv-btn-xs"
            @click="onToolbarAction(act.key)"
          >{{ act.label }}</button>
          <div class="ejv-divider"></div>
          <template v-for="ci in (page?.toolbar?.newRuleInputs||[])" :key="ci.key">
            <input
              v-if="ci.key!=='submit'"
              class="ejv-input ejv-input-xs"
              :style="{ width: (ci.width||128) + 'px' }"
              :placeholder="ci.placeholder"
              :value="ci.key==='newId' ? ui.regexNewId : ui.regexNewName"
              @input="onRegexToolbarInput(ci.key, $event)"
            />
            <button
              v-else
              class="ejv-btn ejv-btn-outline ejv-btn-xs"
              @click="onAddRegexRule"
            >{{ ci.label }}</button>
          </template>
        </div>
      </div>
    </div>

    <!-- Regex 列表 + 预览区 -->
    <div v-if="isRegex" class="ejv-card">
      <div class="ejv-subtitle">
        <i data-lucide="sliders" class="w-4 h-4 text-black"></i>
        <h3>{{ page.list?.title || '正则编辑' }}</h3>
      </div>

      <div class="ejv-list">
        <div v-for="ex in (page.examples||[])" :key="ex.id" class="ejv-item">
          <div class="ejv-item-head">
            <div class="ejv-chip">Rule</div>
            <div class="ejv-item-title">{{ ex.name }}</div>
          </div>
          <div class="ejv-item-body">
            <p class="ejv-item-text">{{ ex.desc }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isRegex" class="ejv-card">
      <div class="ejv-preview ejv-preview-2">
        <div class="ejv-preview-box">
          <div class="ejv-preview-title">规则应用前</div>
          <div class="ejv-preview-body" v-html="page.preview?.before"></div>
        </div>
        <div class="ejv-preview-box">
          <div class="ejv-preview-title">规则应用后</div>
          <div class="ejv-preview-body" v-html="page.preview?.after"></div>
        </div>
      </div>
    </div>

    <div class="ejv-tip">
      当前视图完全由 JSON 驱动（editor_pages.json）。后续可逐步替换占位动作为真实数据逻辑。
    </div>
  </div>
</template>

<style scoped>
.ejv-root {
  display: grid;
  gap: 12px;
  min-width: 0;
  grid-template-columns: 1.2fr 1fr;
  align-items: start;
}
@media (max-width: 1200px) {
  .ejv-root { grid-template-columns: 1fr; }
}

/* Card */
.ejv-card {
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(255, 255, 255, 0.8);
  border-radius: var(--st-radius-lg);
  box-shadow: var(--st-shadow-sm);
  padding: 16px;
}

.ejv-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.ejv-title { display: inline-flex; align-items: center; gap: 8px; }
.ejv-icon { font-size: 18px; }
.ejv-file { display: inline-flex; align-items: center; gap: 6px; }
.ejv-label { font-size: 12px; color: rgba(var(--st-color-text), 0.7); }
.ejv-input {
  height: 28px; border-radius: 8px; border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2)); color: rgb(var(--st-color-text)); padding: 0 8px; font-size: 12px;
}
.ejv-input-xs { height: 26px; font-size: 12px; }
.ejv-muted { margin: 6px 0 0; color: rgba(var(--st-color-text), 0.7); font-size: 12px; }
.ejv-desc { margin: 4px 0 0; color: rgba(var(--st-color-text), 0.8); font-size: 12px; }

.ejv-btn {
  appearance: none; border: 1px solid rgb(var(--st-border)); background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text)); padding: 8px 10px; border-radius: 10px; font-size: 12px;
  cursor: pointer; transition: transform .12s ease, box-shadow .12s ease, background .12s ease, border-color .12s ease;
  min-width: 64px; text-align: center;
}
.ejv-btn:hover { transform: translateY(-1px); box-shadow: var(--st-shadow-sm); }
.ejv-btn-outline { border-color: rgba(var(--st-border), 0.9); background: rgb(var(--st-surface)); }
.ejv-btn-xs { padding: 6px 8px; font-size: 12px; min-width: 0; }

.ejv-panel-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 8px; background: transparent; border: 0; padding: 8px 6px; }
.ejv-panel-toggle-left { display: inline-flex; align-items: center; gap: 8px; }
.ejv-panel-body { padding: 10px 6px; }
.ejv-row { display: grid; gap: 10px; }
.ejv-row-space { margin-bottom: 8px; }
.ejv-row-end { display: flex; align-items: center; justify-content: flex-end; }
.ejv-row-gap { gap: 8px; }
.ejv-flex { display: inline-flex; align-items: center; gap: 8px; }

.ejv-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (max-width: 900px) { .ejv-grid-2 { grid-template-columns: 1fr; } }

.ejv-switch { display: flex; align-items: center; justify-content: space-between; }
.ejv-switch-label { font-size: 13px; color: rgba(var(--st-color-text), 0.9); }
.ejv-switch-ctrl { display: inline-flex; align-items: center; gap: 6px; }
.ejv-switch-ctrl input[type="checkbox"] { width: 18px; height: 18px; }
.ejv-switch-text { font-size: 12px; color: rgba(var(--st-color-text), 0.75); }

.ejv-field-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.ejv-field-head label { font-size: 13px; font-weight: 600; color: rgb(var(--st-color-text)); }
.ejv-field-unit { font-size: 12px; color: rgba(var(--st-color-text), 0.55); }
.ejv-help { font-size: 12px; color: rgba(var(--st-color-text), 0.6); margin-top: 4px; }

.ejv-subsection { margin: 10px 0 12px; }
.ejv-sub-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 8px; background: transparent; border: 0; padding: 6px 0; }
.ejv-sub-left { display: inline-flex; align-items: center; gap: 8px; }

.ejv-list { display: grid; grid-template-columns: 1fr; gap: 8px; }
.ejv-item { border: 1px solid rgba(var(--st-border), 0.9); border-radius: 10px; background: rgb(var(--st-surface)); padding: 10px; }
.ejv-item-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.ejv-chip {
  display: inline-flex; align-items: center; height: 20px; padding: 0 8px; font-size: 11px; border-radius: 9999px;
  border: 1px solid rgba(var(--st-border), 0.9); background: rgba(var(--st-primary), 0.06); color: rgb(var(--st-color-text));
}
.ejv-item-title { font-weight: 700; color: rgb(var(--st-color-text)); font-size: 13px; }
.ejv-item-text { margin: 0; font-size: 12px; color: rgba(var(--st-color-text), 0.75); }

.ejv-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.ejv-stats { font-size: 12px; color: rgba(var(--st-color-text), 0.7); }
.ejv-divider { width: 1px; height: 20px; background: rgba(var(--st-border), 0.9); }

.ejv-subtitle { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.ejv-preview { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ejv-preview-2 { grid-template-columns: 1fr 1fr; }
@media (max-width: 900px) { .ejv-preview, .ejv-preview-2 { grid-template-columns: 1fr; } }
.ejv-preview-box { border: 1px solid rgba(var(--st-border), 0.9); border-radius: 10px; background: rgb(var(--st-surface)); box-shadow: var(--st-shadow-sm); padding: 10px; }
.ejv-preview-title { font-weight: 700; color: rgb(var(--st-color-text)); margin-bottom: 6px; }
.ejv-preview-body { font-size: 12px; color: rgba(var(--st-color-text), 0.8); }

.ejv-tip { font-size: 12px; color: rgba(var(--st-color-text), 0.6); text-align: center; padding: 6px; }
</style>