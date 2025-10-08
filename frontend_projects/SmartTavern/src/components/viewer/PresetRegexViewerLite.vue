<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'preset' }, // 'preset' | 'regex'
  name: { type: String, default: '' },
  desc: { type: String, default: '' },
})

const isPreset = computed(() => props.type === 'preset')
const isRegex = computed(() => props.type === 'regex')

const title = computed(() => (isPreset.value ? '预设编辑器（简版预览）' : '正则规则（简版预览）'))
const leadingIcon = computed(() => (isPreset.value ? '🎛️' : '🧹'))
const fileLabel = computed(() => (isPreset.value ? '预设文件' : '正则文件'))
</script>

<template>
  <div data-scope="lite-viewer" class="lv-root">
    <!-- 顶部信息条 -->
    <div class="lv-card">
      <div class="lv-card-header">
        <div class="lv-title">
          <span class="lv-icon">{{ leadingIcon }}</span>
          <h2>{{ title }}</h2>
        </div>
        <div class="lv-file">
          <label class="lv-label">{{ fileLabel }}：</label>
          <input class="lv-input" :value="name || '未命名.json'" readonly />
        </div>
      </div>
      <p class="lv-muted">
        说明：这是嵌入的简版占位视图，用于联调“查看”流程与 UI 容器。后续将替换为 PromptEditor 真正的主面板组件。
      </p>
      <p v-if="desc" class="lv-desc">{{ desc }}</p>
    </div>

    <!-- 主区：根据类型显示不同的占位内容 -->
    <div class="lv-card">
      <div class="lv-section-title">
        <span class="lv-mini-icon">🧩</span>
        <h3 v-if="isPreset">提示词条目（占位）</h3>
        <h3 v-else>正则规则条目（占位）</h3>
      </div>

      <div class="lv-list">
        <div class="lv-item">
          <div class="lv-item-head">
            <div class="lv-chip">{{ isPreset ? 'Relative' : 'Rule' }}</div>
            <div class="lv-item-title">{{ isPreset ? '系统前置提示词（占位）' : '移除 XML 标签（占位）' }}</div>
          </div>
          <div class="lv-item-body">
            <p class="lv-item-text">
              {{ isPreset
                ? '用于相对位置插入的系统提示（示例文本，仅用于 UI 演示）。'
                : '示例说明：用于清洗文本中出现的 XML/HTML 标签（仅 UI 占位）。'
              }}
            </p>
          </div>
        </div>

        <div class="lv-item">
          <div class="lv-item-head">
            <div class="lv-chip">{{ isPreset ? 'In-Chat' : 'Rule' }}</div>
            <div class="lv-item-title">{{ isPreset ? '对话内提示词（占位）' : '替换缩进（占位）' }}</div>
          </div>
          <div class="lv-item-body">
            <p class="lv-item-text">
              {{ isPreset
                ? '在对话过程中生效的提示词条目（仅 UI 占位）。'
                : '将连续空格替换为一致的缩进风格（仅 UI 占位）。'
              }}
            </p>
          </div>
        </div>

        <div class="lv-item">
          <div class="lv-item-head">
            <div class="lv-chip">{{ isPreset ? 'API' : 'Rule' }}</div>
            <div class="lv-item-title">{{ isPreset ? 'API 参数示例（占位）' : '移除尾随空白（占位）' }}</div>
          </div>
          <div class="lv-item-body">
            <p class="lv-item-text">
              {{ isPreset
                ? 'temperature=1, top_p=1, max_tokens=300（仅 UI 占位）。'
                : '将行尾多余空白删除（仅 UI 占位）。'
              }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="lv-card">
      <div class="lv-section-title">
        <span class="lv-mini-icon">🧪</span>
        <h3>快速预览（占位）</h3>
      </div>
      <div class="lv-preview">
        <div class="lv-preview-box">
          <div class="lv-preview-title">{{ isPreset ? '合成后的提示词预览' : '规则应用前的文本' }}</div>
          <div class="lv-preview-body">
            <p v-if="isPreset">
              这里展示组合后的提示词上下文（仅 UI 占位）。
            </p>
            <p v-else>
              原始内容：<note>Keep & Clean</note>  —— 将通过示例规则移除标签、整理缩进（仅 UI 占位）。
            </p>
          </div>
        </div>
        <div class="lv-preview-box">
          <div class="lv-preview-title">{{ isPreset ? '合成参数（占位）' : '规则应用后的文本' }}</div>
          <div class="lv-preview-body">
            <p v-if="isPreset">
              temperature=1, top_p=1, stream=true ...
            </p>
            <p v-else>
              结果内容：Keep & Clean —— 示例清洗结果（仅 UI 占位）。
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="lv-tip">
      当前为组件内联版本，无需 iframe。后续替换为 PromptEditor 真实组件并打通数据流。
    </div>
  </div>
</template>

<style scoped>
.lv-root {
  display: grid;
  gap: 12px;
  min-width: 0;
}

/* 通用卡片 */
.lv-card {
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface));
  border-radius: var(--st-radius-lg);
  box-shadow: var(--st-shadow-sm);
  padding: 12px;
}

.lv-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.lv-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.lv-icon { font-size: 18px; }

.lv-file {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.lv-label { font-size: 12px; color: rgba(var(--st-color-text), 0.7); }
.lv-input {
  height: 28px;
  border-radius: 8px;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgb(var(--st-surface-2));
  color: rgb(var(--st-color-text));
  padding: 0 8px;
  font-size: 12px;
}

.lv-muted {
  margin: 6px 0 0;
  color: rgba(var(--st-color-text), 0.7);
  font-size: 12px;
}
.lv-desc {
  margin: 4px 0 0;
  color: rgba(var(--st-color-text), 0.8);
  font-size: 12px;
}

/* 小节标题 */
.lv-section-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.lv-mini-icon { font-size: 16px; }

/* 列表占位 */
.lv-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
.lv-item {
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: 10px;
  background: rgb(var(--st-surface));
  padding: 10px;
}
.lv-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.lv-chip {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  font-size: 11px;
  border-radius: 9999px;
  border: 1px solid rgba(var(--st-border), 0.9);
  background: rgba(var(--st-primary), 0.06);
  color: rgb(var(--st-color-text));
}
.lv-item-title {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  font-size: 13px;
}
.lv-item-text {
  margin: 0;
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.75);
}

/* 预览两栏 */
.lv-preview {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
@media (max-width: 900px) {
  .lv-preview { grid-template-columns: 1fr; }
}
.lv-preview-box {
  border: 1px solid rgba(var(--st-border), 0.9);
  border-radius: 10px;
  background: rgb(var(--st-surface));
  box-shadow: var(--st-shadow-sm);
  padding: 10px;
}
.lv-preview-title {
  font-weight: 700;
  color: rgb(var(--st-color-text));
  margin-bottom: 6px;
}
.lv-preview-body {
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.8);
}

/* 下方提示 */
.lv-tip {
  font-size: 12px;
  color: rgba(var(--st-color-text), 0.6);
  text-align: center;
  padding: 6px;
}
</style>