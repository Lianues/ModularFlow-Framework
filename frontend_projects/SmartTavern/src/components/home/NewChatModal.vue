<script setup>
import { ref, watch, nextTick } from 'vue'
import ContentViewModal from '@/components/common/ContentViewModal.vue'
import DataCatalog from '@/services/dataCatalog.js'
import ChatBranches from '@/services/chatBranches.js'
 
const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '新建对话' },
  icon: { type: String, default: '' },
})
 
const emit = defineEmits(['update:show', 'confirm', 'close'])
 
const newChatName = ref('')
const newChatDesc = ref('')
const nameReplaced = ref(false)
const newChatType = ref('threaded') // 'threaded' | 'sandbox'
 
// 下拉选项（运行时从后端装载）
const presetOptions = ref([])
const characterOptions = ref([])
const personaOptions = ref([])
const regexOptions = ref([])
const worldbookOptions = ref([])
 
const selectedPreset = ref('')
const selectedCharacter = ref('')
const selectedPersona = ref('')
const selectedRegex = ref('')
const selectedWorldbook = ref('')
 
// 加载与提交状态
const loadingLists = ref(false)
const submitting = ref(false)
const fetchError = ref('')
const newGameError = ref('')
 
function resetForm() {
  newChatName.value = ''
  newChatDesc.value = ''
  newChatType.value = 'threaded'
  selectedPreset.value = ''
  selectedCharacter.value = ''
  selectedPersona.value = ''
  selectedRegex.value = ''
  selectedWorldbook.value = ''
  newGameError.value = ''
  fetchError.value = ''
}
 
/**
 * 名称输入最小化清洗：禁止 / \ : * ? " < > |，避免路径问题
 * 其余字符保留，后端仍做最终安全处理与唯一化
 */
watch(newChatName, (v) => {
  if (v == null) return;
  const s = String(v);
  // 替换不允许字符，并去掉结尾的空格/点，避免路径问题
  const nv = s
    .replace(/[\\/:*?"<>|]/g, '-')   // 特殊字符 → “-”
    .replace(/[ \.]+$/g, '');        // 结尾空格与点移除
  nameReplaced.value = nv !== s;
  if (nv !== s) newChatName.value = nv;
});

function baseName(file) {
  const s = String(file || '')
  const i = s.lastIndexOf('/')
  return i >= 0 ? s.slice(i + 1) : s
}
 
async function loadLists() {
  loadingLists.value = true
  fetchError.value = ''
  try {
    const [presets, chars, personas, regex, worlds] = await Promise.all([
      DataCatalog.listPresets(),
      DataCatalog.listCharacters(),
      DataCatalog.listPersonas(),
      DataCatalog.listRegexRules(),
      DataCatalog.listWorldBooks(),
    ])
    const mapOpts = (res, required, placeholder) => {
      const items = Array.isArray(res?.items) ? res.items : []
      const opts = items.map(it => ({
        value: it.file,
        label: it.name || baseName(it.file),
        file: it.file,
      }))
      const head = { value: '', label: placeholder, file: '' }
      return required ? [head, ...opts] : [{ value: '', label: '（可不选）', file: '' }, ...opts]
    }
    presetOptions.value = mapOpts(presets, true, '请选择预设')
    characterOptions.value = mapOpts(chars, true, '请选择角色卡')
    personaOptions.value   = mapOpts(personas, true, '请选择用户信息')
    regexOptions.value     = mapOpts(regex, false, '（可不选）')
    worldbookOptions.value = mapOpts(worlds, false, '（可不选）')
 
    nextTick(() => {
      try { window?.lucide?.createIcons?.() } catch (_) {}
      if (typeof window.initFlowbite === 'function') {
        try { window.initFlowbite() } catch (_) {}
      }
    })
  } catch (e) {
    fetchError.value = e?.message || '加载列表失败'
  } finally {
    loadingLists.value = false
  }
}
 
watch(() => props.show, (v) => {
  if (v) {
    resetForm()
    loadLists()
  }
})
 
async function onSubmit() {
  const name = (newChatName.value ?? '').trim() || '未命名会话'
  if (!selectedPreset.value || !selectedCharacter.value || !selectedPersona.value) {
    newGameError.value = '请先选择：预设、角色卡、用户信息（必选）'
    return
  }
  newGameError.value = ''
  const payload = {
    name,
    description: (newChatDesc.value ?? '').trim(),
    type: newChatType.value,
    preset: selectedPreset.value,
    character: selectedCharacter.value,
    persona: selectedPersona.value,
    regex: selectedRegex.value || null,
    worldbook: selectedWorldbook.value || null,
  }

  if (newChatType.value === 'threaded') {
    // 调用后端创建初始对话 API（带提交等待动画）
    submitting.value = true
    try {
      const res = await ChatBranches.createConversation(payload)
      // 将创建结果上抛：包含文件路径，便于上层后续打开该对话
      emit('confirm', { ...payload, ...res })
      emit('update:show', false)
    } catch (e) {
      newGameError.value = e?.message || '创建对话失败'
    } finally {
      submitting.value = false
    }
  } else {
    // 其他类型保持原行为
    emit('confirm', payload)
    emit('update:show', false)
  }
}
 
function onCancel() {
  if (submitting.value) return
  emit('close')
  emit('update:show', false)
}
</script>

<template>
  <ContentViewModal
    :show="props.show"
    :title="props.title"
    :icon="props.icon"
    @update:show="(v) => emit('update:show', v)"
    @close="onCancel"
  >
    <!-- 加载中（与 LoadGame 一致的旋转等待风格） -->
    <div v-if="loadingLists" class="new-chat-loading">
      <div class="spinner" aria-hidden="true"></div>
      <div class="loading-text">正在加载列表…</div>
    </div>

    <!-- 加载失败 -->
    <div v-else-if="fetchError" class="form-error">{{ fetchError }}</div>

    <!-- 表单 -->
    <form v-else class="new-chat-form" @submit.prevent="onSubmit">
      <div class="form-row">
        <label for="new-chat-name">新对话名称</label>
        <input
          id="new-chat-name"
          type="text"
          v-model="newChatName"
          :disabled="submitting"
          placeholder="请输入对话名称"
          aria-describedby="name-help name-warn"
        />
        <div id="name-help" class="form-hint">
          允许字符：中文、字母、数字、空格、-、_；特殊字符（/ \ : * ? " < > |）将被直接替换为“-”。
        </div>
        <div id="name-warn" class="form-hint warn" aria-live="polite" v-if="nameReplaced">
          已替换不允许的字符为“-”以确保文件名安全。
        </div>
      </div>

      <div class="form-row">
        <label for="new-chat-desc">描述（可选）</label>
        <textarea id="new-chat-desc" v-model="newChatDesc" :disabled="submitting" rows="3" placeholder="请输入对话描述"></textarea>
      </div>
 
      <div class="form-row">
        <label for="new-chat-preset">预设（必选）</label>
        <select id="new-chat-preset" v-model="selectedPreset" :disabled="submitting">
          <option v-for="opt in presetOptions" :key="opt.value" :value="opt.value" :disabled="opt.value === ''">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="new-chat-character">角色卡（必选）</label>
        <select id="new-chat-character" v-model="selectedCharacter" :disabled="submitting">
          <option v-for="opt in characterOptions" :key="opt.value" :value="opt.value" :disabled="opt.value === ''">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="new-chat-persona">用户信息（必选）</label>
        <select id="new-chat-persona" v-model="selectedPersona" :disabled="submitting">
          <option v-for="opt in personaOptions" :key="opt.value" :value="opt.value" :disabled="opt.value === ''">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="new-chat-regex">正则（可选）</label>
        <select id="new-chat-regex" v-model="selectedRegex" :disabled="submitting">
          <option v-for="opt in regexOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="new-chat-worldbook">世界书（可选）</label>
        <select id="new-chat-worldbook" v-model="selectedWorldbook" :disabled="submitting">
          <option v-for="opt in worldbookOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label>对话类型</label>
        <div class="type-options">
          <label class="type-option">
            <input type="radio" value="threaded" v-model="newChatType" :disabled="submitting" />
            <span>对话楼层</span>
            <small>Threaded Chat</small>
          </label>
          <label class="type-option">
            <input type="radio" value="sandbox" v-model="newChatType" :disabled="submitting" />
            <span>前端沙盒</span>
            <small>Frontend Sandbox</small>
          </label>
        </div>
      </div>

      <div v-if="newGameError" class="form-error">{{ newGameError }}</div>

      <div class="form-actions">
        <button type="submit" class="btn primary" :disabled="submitting">
          <span v-if="!submitting">确认</span>
          <span v-else class="btn-loading"><span class="spinner spinner-sm" aria-hidden="true"></span> 正在创建…</span>
        </button>
        <button type="button" class="btn" :disabled="submitting" @click="onCancel">取消</button>
      </div>
    </form>
  </ContentViewModal>
</template>

<style scoped>
.new-chat-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
/* 顶部加载块 */
.new-chat-loading {
  display: grid;
  place-items: center;
  gap: 8px;
  padding: 40px 20px;
  color: rgba(var(--st-color-text), 0.9);
}
.loading-text { font-weight: 700; font-size: 14px; }
.spinner {
  width: 22px; height: 22px; border-radius: 50%;
  border: 3px solid currentColor; border-top-color: transparent;
  animation: st-spin 0.9s linear infinite;
  opacity: 0.9;
}
.spinner-sm { width: 16px; height: 16px; border-width: 2px; }
@keyframes st-spin { to { transform: rotate(360deg); } }
 
.new-chat-form .form-row label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: rgb(var(--st-color-text));
}
.new-chat-form .form-row input[type="text"] {
  width: 100%;
  padding: 10px 12px;
  border-radius: var(--st-radius-md);
  border: 1px solid rgb(var(--st-border) / 0.9);
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  outline: none;
}
.new-chat-form .form-row input[type="text"]::placeholder {
  color: rgb(var(--st-color-text) / 0.55);
}
.new-chat-form .form-row textarea {
  width: 100%;
  padding: 10px 12px;
  border-radius: var(--st-radius-md);
  border: 1px solid rgb(var(--st-border) / 0.9);
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  outline: none;
  resize: vertical;
}
.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.65);
}
.form-hint.warn {
  color: rgb(245, 158, 11); /* 提醒色：amber-500 */
}
.new-chat-form .form-row select {
  width: 100%;
  padding: 10px 12px;
  border-radius: var(--st-radius-md);
  border: 1px solid rgb(var(--st-border) / 0.9);
  background: rgb(var(--st-surface));
  color: rgb(var(--st-color-text));
  outline: none;
}
.new-chat-form .type-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
  gap: 12px;
}
@media (max-width: 720px) {
  .new-chat-form .type-options { grid-template-columns: 1fr; }
}
.new-chat-form .type-option {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  grid-template-areas:
    "radio title"
    "radio sub";
  align-items: center;
  column-gap: 10px;
  row-gap: 4px;
  padding: 12px;
  border-radius: var(--st-radius-lg);
  border: 1px solid rgb(var(--st-border) / 0.9);
  background: rgb(var(--st-surface) / 0.72);
  backdrop-filter: blur(6px) saturate(130%);
  -webkit-backdrop-filter: blur(6px) saturate(130%);
}
.new-chat-form .type-option input[type="radio"] {
  grid-area: radio;
  width: 16px;
  height: 16px;
  accent-color: rgb(var(--st-primary));
}
.new-chat-form .type-option span {
  grid-area: title;
  font-weight: 700;
  color: rgb(var(--st-color-text));
}
.new-chat-form .type-option small {
  grid-area: sub;
  font-size: 12px;
  color: rgb(var(--st-color-text) / 0.7);
}
.new-chat-form .form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 8px;
}
.new-chat-form .btn {
  appearance: none;
  border: 1px solid rgb(var(--st-border));
  background: rgb(var(--st-surface));
  padding: 10px 14px;
  border-radius: var(--st-radius-md);
  color: rgb(var(--st-color-text));
  cursor: pointer;
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease, border-color .12s ease;
}
.new-chat-form .btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--st-shadow-sm);
}
.new-chat-form .btn.primary {
  background: linear-gradient(135deg, rgb(var(--st-primary) / 1), rgb(var(--st-accent) / 1));
  color: var(--st-primary-contrast);
  border-color: transparent;
}
.btn-loading {
  display: inline-flex; align-items: center; gap: 8px;
}
.new-chat-form .form-error {
  margin-top: 4px;
  padding: 10px 12px;
  border-radius: var(--st-radius-md);
  border: 1px solid rgba(220, 38, 38, 0.6);
  background: rgba(220, 38, 38, 0.08);
  color: rgb(220, 38, 38);
  font-size: 13px;
}
</style>