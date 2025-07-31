import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

import App from './App.vue'
import router from './router'
import api from './utils/api'
import { setupInterceptors } from './utils/setupInterceptors'

import './assets/css/main.css'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)

// Set up axios interceptors after Pinia is initialized
setupInterceptors(api)

app.mount('#app')