import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { useMqttStore } from './stores/mqtt-store'
import './assets/css/theme.css'

const app = createApp(App)
app.use(createPinia())

// before mount(): onMounted hooks subscribe and publish, which needs the client to exist (even if not yet connected)
useMqttStore().initialize()

app.mount('#app')
