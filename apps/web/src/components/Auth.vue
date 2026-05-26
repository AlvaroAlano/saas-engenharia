<script setup>
import { ref } from 'vue'
import { supabase } from '../supabase'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { Layers, Loader2 } from 'lucide-vue-next'

const router = useRouter()
const { showToast } = useToast()

const isLogin = ref(true)
const email = ref('')
const password = ref('')
const fullName = ref('')
const creaCau = ref('')
const isLoading = ref(false)

const translateError = (errorMsg) => {
  if (!errorMsg) return 'Ocorreu um erro desconhecido.'
  const msg = errorMsg.toLowerCase()
  
  if (msg.includes('invalid login credentials')) return 'E-mail ou senha incorretos.'
  if (msg.includes('email not confirmed')) return 'Por favor, confirme seu e-mail antes de entrar.'
  if (msg.includes('user already registered')) return 'Este e-mail já está cadastrado em nosso sistema.'
  if (msg.includes('password should be at least')) return 'A senha deve ter pelo menos 6 caracteres.'
  if (msg.includes('invalid email')) return 'E-mail inválido.'
  if (msg.includes('rate limit exceeded')) return 'Limite de tentativas excedido. Tente novamente mais tarde ou use outro e-mail.'
  if (msg.includes('signups are disabled')) return 'O cadastro de novas contas está temporariamente desativado.'
  
  return errorMsg
}

const handleAuth = async () => {
  isLoading.value = true

  try {
    if (isLogin.value) {
      const { error } = await supabase.auth.signInWithPassword({
        email: email.value,
        password: password.value,
      })
      if (error) throw error
      router.push('/dashboard')
    } else {
      const { error } = await supabase.auth.signUp({
        email: email.value,
        password: password.value,
        options: {
          data: {
            full_name: fullName.value,
            crea_cau: creaCau.value
          }
        }
      })
      if (error) throw error
      
      showToast("Conta criada com sucesso! Enviamos um link de confirmação para o seu e-mail.", 'success')
      isLogin.value = true
      email.value = ''
      password.value = ''
      fullName.value = ''
      creaCau.value = ''
    }
  } catch (error) {
    showToast(translateError(error.message), 'error')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-canvas flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-surface rounded-xl border border-hairline overflow-hidden">
      
      <!-- Cabeçalho -->
      <div class="px-8 pt-8 pb-6 text-center border-b border-hairline">
        <div class="w-12 h-12 bg-brand-primary/10 text-brand-primary rounded-lg flex items-center justify-center mx-auto mb-4">
          <Layers class="w-6 h-6" stroke-width="1.5" />
        </div>
        <h2 class="text-2xl font-bold text-ink mb-1">
          {{ isLogin ? 'Acesse o Painel' : 'Cadastro de Engenheiro' }}
        </h2>
        <p class="text-sm text-ink-muted">
          {{ isLogin ? 'Plataforma B2B para construtoras e orçamentistas.' : 'Crie seu Tenant B2B e isole seus orçamentos.' }}
        </p>
      </div>

      <!-- Abas Internas -->
      <div class="flex border-b border-hairline">
        <button 
          @click="isLogin = true" 
          :class="isLogin ? 'text-brand-primary border-b-2 border-brand-primary font-bold bg-surface' : 'text-ink-muted hover:text-ink'"
          class="flex-1 py-3 px-4 transition-all text-sm outline-none cursor-pointer"
        >
          Login
        </button>
        <button 
          @click="isLogin = false" 
          :class="!isLogin ? 'text-brand-primary border-b-2 border-brand-primary font-bold bg-surface' : 'text-ink-muted hover:text-ink'"
          class="flex-1 py-3 px-4 transition-all text-sm outline-none cursor-pointer"
        >
          Criar Conta
        </button>
      </div>

      <!-- Formulário -->
      <div class="p-8">
        <form @submit.prevent="handleAuth" class="space-y-4">

          <div v-if="!isLogin">
            <label class="block text-sm font-medium text-ink mb-1">Nome Completo</label>
            <input v-model="fullName" @input="fullName = fullName.replace(/[0-9]/g, '')" type="text" required class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all" placeholder="Eng. João Silva">
          </div>

          <div>
            <label class="block text-sm font-medium text-ink mb-1">E-mail Profissional</label>
            <input v-model="email" type="email" required class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all" placeholder="engenharia@empresa.com.br">
          </div>

          <div>
            <label class="block text-sm font-medium text-ink mb-1">Senha Segura</label>
            <input v-model="password" type="password" required minlength="6" class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all" placeholder="••••••••">
          </div>

          <div v-if="!isLogin">
            <label class="block text-sm font-medium text-ink mb-1">Registro CREA/CAU</label>
            <input v-model="creaCau" type="text" required class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all" placeholder="Ex: SP-123456/D">
          </div>

          <button type="submit" :disabled="isLoading" class="w-full bg-brand-primary hover:bg-brand-hover text-white font-medium py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-2 mt-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer">
            <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" stroke-width="1.5" />
            <span>{{ isLoading ? 'Processando...' : (isLogin ? 'Entrar no Sistema' : 'Criar Tenant B2B') }}</span>
          </button>
        </form>
      </div>

    </div>
  </div>
</template>
