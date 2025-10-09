<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import ModeSwitch from '@/components/common/ModeSwitch.vue'
import ThemeSwitch from '@/components/common/ThemeSwitch.vue'

const props = defineProps({
  view: { type: String, default: 'start' },
  showSidebar: { type: Boolean, default: false },
  theme: { type: String, default: 'system' }
})
const emit = defineEmits(['update:view','update:theme'])

const condensed = ref(false)

function onScroll() {
  const y = window.scrollY || document.documentElement.scrollTop || 0
  condensed.value = y > 8
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
  window.lucide?.createIcons?.()
  if (typeof window.initFlowbite === 'function') { try { window.initFlowbite() } catch (_) {} }
})
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll))

function setView(v){ emit('update:view', v) }
function setTheme(t){ emit('update:theme', t) }

const viewMap = { threaded:'对话楼层', sandbox:'全局沙盒', start:'开始' }
function viewTitle(){ return viewMap[props.view] || 'SmartTavern' }
</script>

<template>
  <header class="st-topbar glass" :class="{ condensed }" data-scope="topbar">
    <div class="tb-left">
      <button class="brand" type="button" title="返回开始" @click="setView('start')">
        <span class="logo">∞</span>
        <span class="brand-name">SmartTavern</span>
        <span class="divider">•</span>
        <span class="view-title">{{ viewTitle() }}</span>
      </button>
    </div>
    <div class="tb-center">
      <ModeSwitch
        v-if="showSidebar"
        :modelValue="view"
        @update:modelValue="setView"
        class="mode-switch"
      />
    </div>
    <div class="tb-right">
      <div class="actions">
        <ThemeSwitch :theme="theme" @update:theme="setTheme" />
        <button class="icon-btn" type="button" title="帮助" data-tooltip-target="tt-help">
          <i data-lucide="help-circle" class="icon-16" aria-hidden="true"></i>
          <span class="sr-only">帮助</span>
        </button>
        <div id="tt-help" role="tooltip" class="absolute z-10 invisible inline-block px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded-md shadow-sm opacity-0 tooltip">
          帮助
          <div class="tooltip-arrow" data-popper-arrow></div>
        </div>
      </div>
    </div>
    <div class="tb-hairline"></div>
  </header>
</template>

<style scoped>
.st-topbar{
 position: sticky; top:0; z-index:10;
 display:grid; grid-template-columns: 1fr auto 1fr;
 align-items:center;
 padding: 10px 16px;
 border-radius: var(--st-radius-lg);
 backdrop-filter: saturate(140%) blur(10px);
 -webkit-backdrop-filter: saturate(140%) blur(10px);
 border: 1px solid rgba(var(--st-border),0.7);
 box-shadow: 0 8px 24px rgba(0,0,0,0.04);
 margin: 8px 8px 0;
 transition: padding .22s cubic-bezier(.22,.61,.36,1), box-shadow .22s cubic-bezier(.22,.61,.36,1), background .22s ease, border-color .22s ease;
}
.st-topbar.condensed{
 padding: 6px 14px;
 box-shadow: 0 10px 28px rgba(0,0,0,0.08);
}
.tb-left, .tb-center, .tb-right { display:flex; align-items:center; }
.tb-left { justify-content:flex-start; min-width:0; }
.tb-center { justify-content:center; }
.tb-right { justify-content:flex-end; gap:8px; }
.brand{
 appearance:none; background:transparent; border:0; color: rgb(var(--st-color-text));
 display:inline-flex; align-items:center; gap:10px; cursor:pointer; padding:6px 8px; border-radius: var(--st-radius-md);
 transition: background .18s cubic-bezier(.22,.61,.36,1), transform .18s cubic-bezier(.22,.61,.36,1);
}
.brand:hover{ background: rgba(var(--st-surface-2),0.6); transform: translateY(-1px); }
.logo{
 width: 28px; height: 28px; border-radius: var(--st-radius-lg);
 display:inline-flex; align-items:center; justify-content:center;
 background: linear-gradient(135deg, rgba(var(--st-primary),1), rgba(var(--st-accent),1));
 color: #fff; font-weight: 800;
}
.brand-name{ font-weight: 700; letter-spacing: .2px; }
.divider{ opacity: .35; }
.view-title{ font-weight: 600; opacity: .85; }
.mode-switch { margin-left: 8px; }
.actions { display:inline-flex; align-items:center; gap: 8px; }
.icon-btn{
 appearance:none; background: transparent; border: 1px solid rgba(var(--st-border),0.9);
 color: rgba(var(--st-color-text),0.7);
 width: 32px; height: 32px; border-radius: var(--st-radius-md);
 display:inline-flex; align-items:center; justify-content:center; cursor:pointer;
 transition: all .18s cubic-bezier(.22,.61,.36,1);
}
.icon-btn:hover{ background: rgba(var(--st-surface-2),0.9); color: rgba(var(--st-color-text),0.95); transform: translateY(-1px); }
.icon-16 { width: 16px; height: 16px; stroke: currentColor; }
.sr-only{ position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
.tb-hairline{
 position: absolute; left: 0; right: 0; bottom: -1px; height: 1px;
 background: linear-gradient(90deg, rgba(var(--st-primary),0) 0%, rgba(var(--st-primary),.35) 15%, rgba(var(--st-accent),.35) 85%, rgba(var(--st-accent),0) 100%);
 pointer-events: none;
 opacity: .6;
 transition: opacity .22s cubic-bezier(.22,.61,.36,1);
}
.st-topbar.condensed .tb-hairline { opacity: 1; }
.tb-tooltip {
  position: absolute; z-index: 50; visibility: hidden; opacity: 0;
  padding: 6px 8px; font-size: 12px;
  color: #fff; background: rgba(0,0,0,0.9);
  border-radius: 8px; box-shadow: 0 6px 14px rgba(0,0,0,0.25);
}

.brand:focus-visible,
.icon-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(var(--st-primary), 0.14);
  border-color: rgba(var(--st-primary), 0.6);
}
@media (max-width: 640px) {
  .brand-name, .divider, .view-title { display: none; }
  .st-topbar { grid-template-columns: auto 1fr auto; }
}
</style>