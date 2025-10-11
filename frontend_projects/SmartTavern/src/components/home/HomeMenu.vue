<script setup>
const emit = defineEmits(['new-game', 'open-load', 'open-gallery', 'open-options'])

function onClickNew() {
  emit('new-game')
}
function onClickLoad() {
  emit('open-load')
}
function onClickGallery() {
  emit('open-gallery')
}
function onClickOptions() {
  emit('open-options')
}
</script>

<template>
  <div class="st-home-menu">
    <nav class="home-menu">
      <button class="menu-btn" type="button" @click="onClickNew">
        <i data-lucide="swords" class="icon-20" aria-hidden="true"></i>
        <span>New Game</span>
      </button>
      <button class="menu-btn" type="button" @click="onClickLoad">
        <i data-lucide="history" class="icon-20" aria-hidden="true"></i>
        <span>Load Game</span>
      </button>
      <button class="menu-btn" type="button" @click="onClickGallery">
        <i data-lucide="image" class="icon-20" aria-hidden="true"></i>
        <span>Gallery</span>
      </button>
      <button class="menu-btn" type="button" @click="onClickOptions">
        <i data-lucide="settings" class="icon-20" aria-hidden="true"></i>
        <span>Options</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
/* Home vertical menu (bottom-left) */
.st-home-menu {
  position: absolute;
  left: 24px;
  bottom: 24px;
  z-index: 2;
}
.home-menu {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.menu-btn {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-radius: var(--st-radius-lg);
  border: 1px solid var(--menu-border, rgb(var(--st-border) /0.7));
  background: transparent; /* no white mask on home */
  color: var(--menu-fg, rgb(var(--st-color-text)));
  text-shadow: var(--menu-shadow, none);
  font-family: var(--st-font-myth);
  font-weight: 800;
  font-size: 20px;
  letter-spacing: .8px;
  cursor: pointer;
  transition:
    transform .18s cubic-bezier(.22,.61,.36,1),
    border-color .18s ease,
    color .18s ease,
    text-shadow .18s ease;
}
.menu-btn:hover {
  transform: translateX(4px);
  border-color: rgb(var(--st-primary) /0.6);
  color: var(--menu-fg, rgb(var(--st-color-text)));
}
.icon-20 { width: 26px; height: 26px; stroke: currentColor; }
</style>