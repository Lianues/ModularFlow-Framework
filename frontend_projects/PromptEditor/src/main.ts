import { createApp, nextTick } from 'vue'
import './style.css'
import App from './App.vue'

const app = createApp(App)
app.mount('#app')

// 初始化 Lucide 图标（挂载后）
nextTick(() => {
  (window as any).lucide?.createIcons?.()
})
