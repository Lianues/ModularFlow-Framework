<template>
  <!-- 当 html 为空时，不渲染舞台，仅透传默认插槽（由父级自行处理回退内容） -->
  <div v-if="html">
    <div v-if="before" class="floor-text">{{ before }}</div>

    <!-- 楼层内 iframe 舞台（宽度百分比受 --st-threaded-stage-maxw 控制，不超过消息宽度） -->
    <div class="floor-html-stage">
      <div class="floor-html-stage-inner">
        <HtmlIframeSandbox :html="html" />
      </div>
    </div>

    <div v-if="after" class="floor-text">{{ after }}</div>
  </div>
  <slot v-else />
</template>

<script setup>
import HtmlIframeSandbox from '@/components/sandbox/HtmlIframeSandbox.vue'

const props = defineProps({
  before: { type: String, default: '' },
  html:   { type: String, default: '' },
  after:  { type: String, default: '' },
})
</script>

<style scoped>
/* 楼层内 HTML 舞台（iframe 渲染） */
.floor-html-stage {
  width: min(100%, calc(var(--st-threaded-stage-maxw, 100) * 1%));
  margin: 6px 0;
}
.floor-html-stage-inner {
  position: relative;
  width: 100%;
  aspect-ratio: var(--st-threaded-stage-aspect, 16 / 9);
  padding: var(--st-threaded-stage-padding, 8px);
  border-radius: var(--st-threaded-stage-radius, 12px);
  border: 1px solid rgba(var(--st-border), 0.6);
  background: rgb(var(--st-surface) / var(--st-threaded-stage-container-bg-opacity, 0.82)) !important;
  box-shadow: var(--st-shadow-sm);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  overflow: hidden;
}
/* 让 HtmlIframeSandbox 内部 iframe 铺满舞台 */
.floor-html-stage-inner :deep(.st-iframe) {
  width: 100%;
  height: 100%;
  display: block;
  border: 0;
}
</style>