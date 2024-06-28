import { createApp } from 'vue'
import App from './App.vue'
import 'bootstrap'
import 'bootstrap/dist/css/bootstrap.min.css'
import './assets/css/style.css'
import { register } from 'swiper/element/bundle'

// Create and mount the root instance.
const app = createApp(App)
// register Swiper custom elements
register()
app.mount('#app')
