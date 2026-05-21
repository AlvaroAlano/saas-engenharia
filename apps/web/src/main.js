import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import { supabase } from './supabase'
import { MaskInput } from "maska"

// Configuração base do Axios (aponta para o backend via variável de ambiente)
// VITE_API_BASE_URL deve ser configurada nos arquivos .env.development e .env.production
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL
console.log("Ambiente:", import.meta.env.MODE)
console.log("URL da API injetada:", axios.defaults.baseURL)

// Configura o interceptor global do Axios para injetar o JWT
axios.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

const app = createApp(App)
app.use(router)

// Diretiva global de máscara usando maska v3
app.directive("maska", {
  mounted(el, binding) {
    const input = el.tagName === 'INPUT' ? el : el.querySelector('input')
    if (!input) return
    input._maskInstance = new MaskInput(input, { mask: binding.value })
  },
  updated(el, binding) {
    if (binding.value !== binding.oldValue) {
      const input = el.tagName === 'INPUT' ? el : el.querySelector('input')
      if (!input) return
      if (input._maskInstance) input._maskInstance.destroy()
      input._maskInstance = new MaskInput(input, { mask: binding.value })
    }
  },
  unmounted(el) {
    const input = el.tagName === 'INPUT' ? el : el.querySelector('input')
    if (input?._maskInstance) input._maskInstance.destroy()
  }
})

app.mount('#app')
