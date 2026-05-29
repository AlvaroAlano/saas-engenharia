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
const isSubmitting = ref(false)

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
  isSubmitting.value = true

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
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#0A0A0A] flex items-center justify-center p-0 sm:p-4 text-neutral-100">
    <div class="w-full min-h-screen flex flex-col justify-center bg-[#0A0A0A] rounded-none border-none sm:min-h-0 sm:h-auto sm:w-full sm:max-w-md sm:bg-[#111111] sm:rounded-xl sm:border sm:border-neutral-800 sm:shadow-2xl sm:overflow-hidden">
      
      <!-- Cabeçalho -->
      <div class="px-8 pt-8 pb-6 text-center border-b border-neutral-800">
        <div class="w-12 h-12 bg-[#005CA9]/10 text-[#005CA9] rounded-lg flex items-center justify-center mx-auto mb-4 border border-[#005CA9]/20">
          <Layers class="w-6 h-6" stroke-width="1.5" />
        </div>
        <h2 class="text-2xl font-bold text-white mb-1">
          {{ isLogin ? 'Acesse o Painel' : 'Cadastro de Engenheiro' }}
        </h2>
        <p class="text-sm text-neutral-400">
          {{ isLogin ? 'Plataforma B2B para construtoras e orçamentistas.' : 'Crie seu Tenant B2B e isole seus orçamentos.' }}
        </p>
      </div>

      <!-- Abas Internas -->
      <div class="relative flex border-b border-neutral-800">
        <button 
          type="button"
          @click="isLogin = true" 
          :class="isLogin ? 'text-white font-bold' : 'text-neutral-400 hover:text-white'"
          class="flex-1 py-3 px-4 transition-all text-sm outline-none cursor-pointer z-10"
        >
          Login
        </button>
        <button 
          type="button"
          @click="isLogin = false" 
          :class="!isLogin ? 'text-white font-bold' : 'text-neutral-400 hover:text-white'"
          class="flex-1 py-3 px-4 transition-all text-sm outline-none cursor-pointer z-10"
        >
          Criar Conta
        </button>
        <!-- Indicador Deslizante (Laranja Caixa Sólido) -->
        <div 
          class="absolute bottom-0 h-0.5 bg-[#F39200] transition-transform duration-300 ease-in-out w-1/2"
          :class="isLogin ? 'translate-x-0' : 'translate-x-full'"
        ></div>
      </div>

      <!-- Formulários com Transição -->
      <div class="p-8">
        <Transition mode="out-in" name="fade-slide">
          <!-- Formulário de Login -->
          <form v-if="isLogin" key="login" @submit.prevent="handleAuth" class="space-y-4">
            <div>
              <label class="block text-xs font-bold text-neutral-400 uppercase tracking-wide mb-1.5">E-mail Profissional</label>
              <input 
                v-model="email" 
                type="email" 
                required 
                class="w-full bg-[#1A1A1A] border border-transparent text-white rounded-md py-2.5 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#005CA9] transition-all placeholder:text-neutral-600" 
                placeholder="engenharia@empresa.com.br"
              >
            </div>

            <div>
              <label class="block text-xs font-bold text-neutral-400 uppercase tracking-wide mb-1.5">Senha Segura</label>
              <input 
                v-model="password" 
                type="password" 
                required 
                minlength="6" 
                class="w-full bg-[#1A1A1A] border border-transparent text-white rounded-md py-2.5 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#005CA9] transition-all placeholder:text-neutral-600" 
                placeholder="••••••••"
              >
            </div>

            <button 
              type="submit" 
              :disabled="isSubmitting" 
              class="w-full bg-[#005CA9] hover:bg-[#004A88] text-white font-bold py-3 px-4 rounded-md transition-colors flex items-center justify-center gap-2 mt-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer border-none shadow-none"
            >
              <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" stroke-width="1.5" />
              <span>{{ isSubmitting ? 'Aguarde...' : 'Entrar no Sistema' }}</span>
            </button>
          </form>

          <!-- Formulário de Cadastro -->
          <form v-else key="register" @submit.prevent="handleAuth" class="space-y-4">
            <div>
              <label class="block text-xs font-bold text-neutral-400 uppercase tracking-wide mb-1.5">Nome Completo</label>
              <input 
                v-model="fullName" 
                @input="fullName = fullName.replace(/[0-9]/g, '')" 
                type="text" 
                required 
                class="w-full bg-[#1A1A1A] border border-transparent text-white rounded-md py-2.5 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#005CA9] transition-all placeholder:text-neutral-600" 
                placeholder="Eng. João Silva"
              >
            </div>

            <div>
              <label class="block text-xs font-bold text-neutral-400 uppercase tracking-wide mb-1.5">E-mail Profissional</label>
              <input 
                v-model="email" 
                type="email" 
                required 
                class="w-full bg-[#1A1A1A] border border-transparent text-white rounded-md py-2.5 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#005CA9] transition-all placeholder:text-neutral-600" 
                placeholder="engenharia@empresa.com.br"
              >
            </div>

            <div>
              <label class="block text-xs font-bold text-neutral-400 uppercase tracking-wide mb-1.5">Senha Segura</label>
              <input 
                v-model="password" 
                type="password" 
                required 
                minlength="6" 
                class="w-full bg-[#1A1A1A] border border-transparent text-white rounded-md py-2.5 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#005CA9] transition-all placeholder:text-neutral-600" 
                placeholder="••••••••"
              >
            </div>

            <div>
              <label class="block text-xs font-bold text-neutral-400 uppercase tracking-wide mb-1.5">Registro CREA/CAU</label>
              <input 
                v-model="creaCau" 
                type="text" 
                required 
                class="w-full bg-[#1A1A1A] border border-transparent text-white rounded-md py-2.5 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#005CA9] transition-all placeholder:text-neutral-600" 
                placeholder="Ex: SP-123456/D"
              >
            </div>

            <button 
              type="submit" 
              :disabled="isSubmitting" 
              class="w-full bg-[#005CA9] hover:bg-[#004A88] text-white font-bold py-3 px-4 rounded-md transition-colors flex items-center justify-center gap-2 mt-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer border-none shadow-none"
            >
              <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" stroke-width="1.5" />
              <span>{{ isSubmitting ? 'Aguarde...' : 'Criar Tenant B2B' }}</span>
            </button>
          </form>
        </Transition>
      </div>

    </div>
  </div>
</template>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(5px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
