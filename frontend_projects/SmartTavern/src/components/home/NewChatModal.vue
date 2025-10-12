<script setup>
import { ref, watch, nextTick } from 'vue'
import ContentViewModal from '@/components/common/ContentViewModal.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '新建对话' },
  icon: { type: String, default: '' },
})

const emit = defineEmits(['update:show', 'confirm', 'close'])

const newChatName = ref('')
const newChatType = ref('threaded') // 'threaded' | 'sandbox'

const presetOptions = ref([
  { value: '', label: '请选择预设' },
  { value: 'Default', label: 'Default（占位）' },
  { value: 'Story', label: 'Story（占位）' },
])
const characterOptions = ref([
  { value: '', label: '请选择角色卡' },
  { value: '心与露', label: '心与露（占位）' },
  { value: '许莲笙', label: '许莲笙（占位）' },
])
const personaOptions = ref([
  { value: '', label: '请选择用户信息' },
  { value: '用户1', label: '用户1（占位）' },
  { value: '用户2', label: '用户2（占位）' },
])
const regexOptions = ref([
  { value: '', label: '（可不选）' },
  { value: 'remove_xml_tags', label: '移除XML标签（占位）' },
])
const worldbookOptions = ref([
  { value: '', label: '（可不选）' },
  { value: '参考用main_world', label: '参考用世界书（占位）' },
])

const selectedPreset = ref('')
const selectedCharacter = ref('')
const selectedPersona = ref('')
const selectedRegex = ref('')
const selectedWorldbook = ref('')

const newGameError = ref('')

function resetForm() {
  newChatName.value = ''
  newChatType.value = 'threaded'
  selectedPreset.value = ''
  selectedCharacter.value = ''
  selectedPersona.value = ''
  selectedRegex.value = ''
  selectedWorldbook.value = ''
  newGameError.value = ''
}

watch(() => props.show, (v) => {
  if (v) {
    resetForm()
    nextTick(() => {
      window?.lucide?.createIcons?.()
      if (typeof window.initFlowbite === 'function') {
        try { window.initFlowbite() } catch (_) {}
      }
    })
  }
})

function onSubmit() {
  const name = (newChatName.value ?? '').trim() || '未命名会话'
  if (!selectedPreset.value || !selectedCharacter.value || !selectedPersona.value) {
    newGameError.value = '请先选择：预设、角色卡、用户信息（必选）'
    return
  }
  const payload = {
    name,
    type: newChatType.value,
    preset: selectedPreset.value,
    character: selectedCharacter.value,
    persona: selectedPersona.value,
    regex: selectedRegex.value || null,
    worldbook: selectedWorldbook.value || null,
  }
  emit('confirm', payload)
  emit('update:show', false)
}

function onCancel() {
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
    <form class="new-chat-form" @submit.prevent="onSubmit">
      <div class="form-row">
        <label for="new-chat-name">新对话名称</label>
        <input id="new-chat-name" type="text" v-model="newChatName" placeholder="请输入对话名称（占位）" />
      </div>

      <div class="form-row">
        <label for="new-chat-preset">预设（必选）</label>
        <select id="new-chat-preset" v-model="selectedPreset">
          <option v-for="opt in presetOptions" :key="opt.value" :value="opt.value" :disabled="opt.value === ''">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="new-chat-character">角色卡（必选）</label>
        <select id="new-chat-character" v-model="selectedCharacter">
          <option v-for="opt in characterOptions" :key="opt.value" :value="opt.value" :disabled="opt.value === ''">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="new-chat-persona">用户信息（必选）</label>
        <select id="new-chat-persona" v-model="selectedPersona">
          <option v-for="opt in personaOptions" :key="opt.value" :value="opt.value" :disabled="opt.value === ''">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="new-chat-regex">正则（可选）</label>
        <select id="new-chat-regex" v-model="selectedRegex">
          <option v-for="opt in regexOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="new-chat-worldbook">世界书（可选）</label>
        <select id="new-chat-worldbook" v-model="selectedWorldbook">
          <option v-for="opt in worldbookOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>

      <div class="form-row">
        <label>对话类型</label>
        <div class="type-options">
          <label class="type-option">
            <input type="radio" value="threaded" v-model="newChatType" />
            <span>对话楼层</span>
            <small>Threaded Chat</small>
          </label>
          <label class="type-option">
            <input type="radio" value="sandbox" v-model="newChatType" />
            <span>前端沙盒</span>
            <small>Frontend Sandbox</small>
          </label>
        </div>
      </div>

      <div v-if="newGameError" class="form-error">{{ newGameError }}</div>

      <div class="form-actions">
        <button type="submit" class="btn primary">确认</button>
        <button type="button" class="btn" @click="onCancel">取消</button>
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