import { createApp } from 'vue'
import App from './App.vue'
import CustomScrollbar from '@/components/common/CustomScrollbar.vue'
import './tailwind.css'
import './styles/tokens.css'
import ThemeManager from '@/features/themes/manager'

const app = createApp(App)

// 注册全局组件
app.component('CustomScrollbar', CustomScrollbar)

// 初始化主题运行时后再挂载，减少样式闪烁
ThemeManager.init().finally(() => {
  app.mount('#app')
})
