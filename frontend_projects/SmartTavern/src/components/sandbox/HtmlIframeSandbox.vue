<template>
  <iframe
    ref="frame"
    class="st-iframe"
    :sandbox="sandbox"
    :allow="allow"
    allowfullscreen
    :srcdoc="computedSrcdoc">
  </iframe>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'

const props = defineProps({
  html: { type: String, default: '' },
  baseUrl: { type: String, default: '' },
  sandbox: { type: String, default: 'allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-popups-to-escape-sandbox allow-presentation allow-pointer-lock allow-orientation-lock allow-top-navigation-by-user-activation allow-storage-access-by-user-activation' },
  allow: { type: String, default: 'fullscreen *; clipboard-read *; clipboard-write *; geolocation *; microphone *; camera *; autoplay *; encrypted-media *; payment *; usb *; serial *; midi *; gyroscope *; magnetometer *; xr-spatial-tracking *; display-capture *; gamepad *; idle-detection *' },
  injectCss: { type: String, default: '' },
  csp: { type: String, default: '' }
})

const frame = ref<HTMLIFrameElement | null>(null)

const computedSrcdoc = computed(() => {
  const base = props.baseUrl ? `<base href="${props.baseUrl}">` : ''
  const csp = props.csp ? `<meta http-equiv="Content-Security-Policy" content="${props.csp}">` : ''
  const injected = props.injectCss ? `<style>${props.injectCss}</style>` : ''
  const normalize = `<style>html,body{height:100%;margin:0;padding:0;background:transparent}</style>`
  return `<!doctype html><html><head><meta charset="utf-8">${csp}${base}${normalize}${injected}</head><body>${props.html}</body></html>`
})

// Optional: message bridge setup for future use
onMounted(() => {
  // Example: listen for ping from child if needed
})

watch(() => props.html, () => {
  // srcdoc binding will refresh automatically
})
</script>

<style scoped>
.st-iframe {
  width: 100%;
  height: 100%;
  border: 0;
  border-radius: inherit;
  background: transparent;
  display: block;
}
</style>