import { createApp } from 'vue'
import App from './App.vue'
import CustomScrollbar from '@/components/common/CustomScrollbar.vue'

const app = createApp(App)

// 注册全局组件
app.component('CustomScrollbar', CustomScrollbar)

app.mount('#app')
