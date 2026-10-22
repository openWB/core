import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { useMqttStore } from './stores/mqtt-store'
import './assets/css/theme.css'

const app = createApp(App)
app.use(createPinia())

// must run before mount() - mounting fires every component's onMounted synchronously,
// and the mqtt client must already exist (even if not yet connected) for subscribe()/
// publish() calls made during that initial mount to not be silently dropped
useMqttStore().initialize()

app.mount('#app')
