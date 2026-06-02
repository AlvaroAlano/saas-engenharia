<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { supabase } from '../supabase'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '../composables/useToast'
import { Loader2, Eye, EyeOff, CheckCircle2, Star, HardHat, Building2 } from 'lucide-vue-next'
import VerticeLogo from './VerticeLogo.vue'

const router = useRouter()
const route = useRoute()
const { showToast } = useToast()

const isCliente = computed(() => route.query.tipo === 'cliente')
const redirectTarget = computed(() => route.query.redirect || (isCliente.value ? '/buscar' : '/dashboard'))

// ─── Auth state ────────────────────────────────────────────────────────────
const isLogin = ref(true)
const email = ref('')
const password = ref('')
const fullName = ref('')
const creaCau = ref('')
const isSubmitting = ref(false)
const isGoogleLoading = ref(false)
const showPassword = ref(false)
const showResetSent = ref(false)
const isSendingReset = ref(false)

// ─── Testimonials ──────────────────────────────────────────────────────────
const ALL_TESTIMONIALS = [
  {
    tipo: 'engenheiro',
    nome: 'Rafael Souza',
    cargo: 'Eng. Civil',
    cidade: 'São Paulo, SP',
    foto: 'https://randomuser.me/api/portraits/men/55.jpg',
    nota: 5,
    texto: '"O Vértice transformou minha relação com clientes. Tudo num lugar só — orçamento SINAPI, contrato ZapSign, diário de obra e portal do cliente."',
  },
  {
    tipo: 'cliente',
    nome: 'Fernanda Costa',
    cargo: 'Proprietária · Obra 320m²',
    cidade: 'São Paulo, SP',
    foto: 'https://randomuser.me/api/portraits/women/68.jpg',
    nota: 5,
    texto: '"Encontrei o Rafael pelo Vértice e minha casa ficou incrível. Todo o processo foi transparente: via cada etapa em tempo real pelo portal."',
  },
  {
    tipo: 'engenheiro',
    nome: 'Patrícia Fernandes',
    cargo: 'Eng. Civil · LEED AP',
    cidade: 'Curitiba, PR',
    foto: 'https://randomuser.me/api/portraits/women/23.jpg',
    nota: 5,
    texto: '"A integração com o ZapSign e o SINAPI me poupam horas por semana. Consigo fechar mais obras sem aumentar minha equipe."',
  },
  {
    tipo: 'cliente',
    nome: 'Eduardo Vieira',
    cargo: 'Proprietário · Obra 180m²',
    cidade: 'Curitiba, PR',
    foto: 'https://randomuser.me/api/portraits/men/41.jpg',
    nota: 5,
    texto: '"Acompanhar a obra pelo portal foi uma experiência incrível. Sabia de cada etapa sem precisar ligar para o engenheiro toda hora."',
  },
  {
    tipo: 'engenheiro',
    nome: 'Marcos Toledo',
    cargo: 'Eng. Civil',
    cidade: 'Salvador, BA',
    foto: 'https://randomuser.me/api/portraits/men/32.jpg',
    nota: 5,
    texto: '"Antes eu levava um dia inteiro para montar um orçamento. Hoje faço em 20 minutos com o SINAPI integrado. Produtividade triplicou."',
  },
  {
    tipo: 'cliente',
    nome: 'Maria das Graças',
    cargo: 'Proprietária · Financiamento Caixa',
    cidade: 'Recife, PE',
    foto: 'https://randomuser.me/api/portraits/women/85.jpg',
    nota: 5,
    texto: '"O João me guiou em cada etapa do financiamento Caixa pelo sistema. Nunca imaginei que construir minha casa seria tão organizado."',
  },
  {
    tipo: 'engenheiro',
    nome: 'Carlos Mendes',
    cargo: 'Eng. Civil',
    cidade: 'Belo Horizonte, MG',
    foto: 'https://randomuser.me/api/portraits/men/71.jpg',
    nota: 5,
    texto: '"O Portal do Cliente me diferencia de qualquer concorrente. Transparência total cria confiança — e clientes satisfeitos indicam mais clientes."',
  },
  {
    tipo: 'cliente',
    nome: 'Luiz Henrique',
    cargo: 'Proprietário · Casa Sustentável',
    cidade: 'Rio de Janeiro, RJ',
    foto: 'https://randomuser.me/api/portraits/men/22.jpg',
    nota: 5,
    texto: '"Com a Ana, vi cada etapa da construção em tempo real. Segurança absoluta no processo. Minha família está completamente encantada com o resultado."',
  },
]

// Intercala: primário (modo atual) e secundário alternados
const orderedTestimonials = computed(() => {
  const primary = ALL_TESTIMONIALS.filter(t => t.tipo === (isCliente.value ? 'cliente' : 'engenheiro'))
  const secondary = ALL_TESTIMONIALS.filter(t => t.tipo !== (isCliente.value ? 'cliente' : 'engenheiro'))
  const result = []
  const max = Math.max(primary.length, secondary.length)
  for (let i = 0; i < max; i++) {
    if (primary[i]) result.push(primary[i])
    if (secondary[i]) result.push(secondary[i])
  }
  return result
})

const currentIndex = ref(0)
const progressKey = ref(0)
let timer = null

const currentTest = computed(() => orderedTestimonials.value[currentIndex.value] || orderedTestimonials.value[0])

const startTimer = () => {
  clearInterval(timer)
  timer = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % orderedTestimonials.value.length
    progressKey.value++
  }, 5500)
}

const jumpTo = (i) => {
  currentIndex.value = i
  progressKey.value++
  startTimer()
}

watch(isCliente, () => {
  currentIndex.value = 0
  progressKey.value++
  startTimer()
})

onMounted(() => startTimer())
onUnmounted(() => clearInterval(timer))

// ─── Auth helpers ───────────────────────────────────────────────────────────
const translateError = (errorMsg) => {
  if (!errorMsg) return 'Ocorreu um erro desconhecido.'
  const msg = errorMsg.toLowerCase()
  if (msg.includes('invalid login credentials')) return 'E-mail ou senha incorretos.'
  if (msg.includes('email not confirmed')) return 'Confirme seu e-mail antes de entrar.'
  if (msg.includes('user already registered')) return 'Este e-mail já possui uma conta.'
  if (msg.includes('password should be at least')) return 'A senha deve ter pelo menos 6 caracteres.'
  if (msg.includes('invalid email')) return 'E-mail inválido.'
  if (msg.includes('rate limit exceeded')) return 'Muitas tentativas. Aguarde alguns minutos.'
  if (msg.includes('signups are disabled')) return 'Cadastro temporariamente desativado.'
  return errorMsg
}

const handleAuth = async () => {
  isSubmitting.value = true
  try {
    if (isLogin.value) {
      const { error } = await supabase.auth.signInWithPassword({ email: email.value, password: password.value })
      if (error) throw error
      router.push(redirectTarget.value)
    } else {
      const { error } = await supabase.auth.signUp({
        email: email.value,
        password: password.value,
        options: {
          data: {
            full_name: fullName.value,
            ...(isCliente.value ? {} : { crea_cau: creaCau.value }),
          }
        }
      })
      if (error) throw error
      showToast('Conta criada! Verifique seu e-mail para confirmar o acesso.', 'success')
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

const signInWithGoogle = async () => {
  isGoogleLoading.value = true
  try {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}${redirectTarget.value}` }
    })
    if (error) throw error
  } catch {
    showToast('Erro ao conectar com Google. Tente novamente.', 'error')
    isGoogleLoading.value = false
  }
}

const handleForgotPassword = async () => {
  if (!email.value) {
    showToast('Informe seu e-mail acima antes de redefinir a senha.', 'error')
    return
  }
  isSendingReset.value = true
  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email.value, {
      redirectTo: `${window.location.origin}/auth`
    })
    if (error) throw error
    showResetSent.value = true
  } catch {
    showToast('Erro ao enviar e-mail. Tente novamente.', 'error')
  } finally {
    isSendingReset.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#0A0A0A] flex items-stretch text-neutral-100">

    <!-- ── Painel esquerdo: social proof (lg+) ───────────────────────────── -->
    <div class="hidden lg:flex flex-col w-[460px] shrink-0 bg-[#0D0D0D] border-r border-neutral-800 relative overflow-hidden">

      <!-- Gradiente ambiente -->
      <div class="absolute inset-0 pointer-events-none">
        <div class="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-[0.06]"
          :class="isCliente ? 'bg-[#F39200]' : 'bg-[#005CA9]'"
          style="filter: blur(80px); transition: background-color 1s ease;"
        ></div>
        <div class="absolute bottom-0 right-0 w-64 h-64 rounded-full opacity-[0.04]"
          :class="isCliente ? 'bg-[#005CA9]' : 'bg-[#F39200]'"
          style="filter: blur(60px); transition: background-color 1s ease;"
        ></div>
      </div>

      <div class="relative z-10 flex flex-col h-full p-10">

        <!-- Logo -->
        <VerticeLogo class="h-[44px] text-white shrink-0" />

        <!-- Headline contextual -->
        <Transition name="ctx-fade" mode="out-in">
          <div :key="isCliente" class="mt-10">
            <p class="text-xs font-bold uppercase tracking-widest mb-2"
              :class="isCliente ? 'text-[#F39200]' : 'text-[#4FA8F5]'">
              {{ isCliente ? 'O que nossos clientes dizem' : 'O que nossos engenheiros dizem' }}
            </p>
            <h2 class="text-2xl font-black text-white leading-snug">
              {{ isCliente
                ? 'Obras entregues com\ntransparência total'
                : 'Mais obras. Menos\nburocracia. Mais lucro.' }}
            </h2>
          </div>
        </Transition>

        <!-- Carrossel de depoimentos -->
        <div class="flex-1 flex flex-col justify-center mt-8">
          <div class="relative min-h-[220px]">
            <Transition name="testimonial" mode="out-in">
              <div :key="currentIndex" class="space-y-5">

                <!-- Badge tipo -->
                <span
                  class="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest px-3 py-1 rounded-full border"
                  :class="currentTest.tipo === 'engenheiro'
                    ? 'bg-[#005CA9]/15 text-[#4FA8F5] border-[#005CA9]/30'
                    : 'bg-[#F39200]/15 text-[#F39200] border-[#F39200]/30'"
                >
                  <span class="w-1.5 h-1.5 rounded-full"
                    :class="currentTest.tipo === 'engenheiro' ? 'bg-[#4FA8F5]' : 'bg-[#F39200]'"
                  ></span>
                  {{ currentTest.tipo === 'engenheiro' ? 'Engenheiro' : 'Cliente' }}
                </span>

                <!-- Citação -->
                <p class="text-[17px] font-medium text-white leading-[1.6] tracking-[-0.2px]">
                  {{ currentTest.texto }}
                </p>

                <!-- Autor -->
                <div class="flex items-center gap-3">
                  <img
                    :src="currentTest.foto"
                    :alt="currentTest.nome"
                    class="w-11 h-11 rounded-full object-cover ring-2 ring-neutral-700"
                  />
                  <div>
                    <p class="text-sm font-semibold text-white">{{ currentTest.nome }}</p>
                    <p class="text-xs text-neutral-500">{{ currentTest.cargo }} · {{ currentTest.cidade }}</p>
                  </div>
                </div>

                <!-- Estrelas -->
                <div class="flex gap-0.5">
                  <Star
                    v-for="i in currentTest.nota"
                    :key="i"
                    class="w-3.5 h-3.5 text-yellow-400 fill-yellow-400"
                    stroke-width="0"
                  />
                </div>

              </div>
            </Transition>
          </div>

          <!-- Progress bar + dots -->
          <div class="mt-6 space-y-3">
            <!-- Progress bar animada (reinicia a cada depoimento via :key) -->
            <div class="h-px bg-neutral-800 rounded-full overflow-hidden">
              <div :key="progressKey" class="h-full rounded-full progress-bar"
                :class="currentTest.tipo === 'engenheiro' ? 'bg-[#005CA9]' : 'bg-[#F39200]'"
              ></div>
            </div>

            <!-- Dots -->
            <div class="flex items-center gap-1.5">
              <button
                v-for="(_, i) in orderedTestimonials"
                :key="i"
                @click="jumpTo(i)"
                class="h-1.5 rounded-full transition-all duration-300 cursor-pointer"
                :class="i === currentIndex
                  ? (currentTest.tipo === 'engenheiro' ? 'bg-[#4FA8F5] w-5' : 'bg-[#F39200] w-5')
                  : 'bg-neutral-700 w-1.5 hover:bg-neutral-500'"
                :aria-label="`Depoimento ${i + 1}`"
              />
            </div>
          </div>
        </div>

        <!-- Stats -->
        <Transition name="ctx-fade" mode="out-in">
          <div :key="isCliente" class="grid grid-cols-2 gap-4 py-6 border-t border-neutral-800">
            <div v-for="stat in (isCliente
              ? [{v:'120+',l:'obras entregues'},{v:'R$12M+',l:'contratos assinados'},{v:'98%',l:'satisfação de clientes'},{v:'18',l:'estados atendidos'}]
              : [{v:'120+',l:'obras gerenciadas'},{v:'R$12M+',l:'em contratos assinados'},{v:'20min',l:'orçamento SINAPI'},{v:'18',l:'estados com SINAPI'}]
            )" :key="stat.l">
              <p class="text-xl font-black text-white tabular-nums">{{ stat.v }}</p>
              <p class="text-xs text-neutral-500 mt-0.5 leading-snug">{{ stat.l }}</p>
            </div>
          </div>
        </Transition>

        <!-- Trust badges -->
        <div class="flex flex-wrap gap-2">
          <span class="flex items-center gap-1.5 text-[11px] text-neutral-400 bg-neutral-800/80 rounded-full px-3 py-1.5">
            <CheckCircle2 class="w-3 h-3 text-emerald-500" stroke-width="2.5" /> CREA/CAU verificado
          </span>
          <span class="flex items-center gap-1.5 text-[11px] text-neutral-400 bg-neutral-800/80 rounded-full px-3 py-1.5">
            <HardHat class="w-3 h-3 text-[#4FA8F5]" stroke-width="1.5" /> SINAPI oficial
          </span>
          <span class="flex items-center gap-1.5 text-[11px] text-neutral-400 bg-neutral-800/80 rounded-full px-3 py-1.5">
            <Building2 class="w-3 h-3 text-[#F39200]" stroke-width="1.5" /> Parceiro Caixa
          </span>
        </div>

      </div>
    </div>

    <!-- ── Painel direito: formulário ────────────────────────────────────── -->
    <div class="flex-1 flex flex-col items-center justify-center p-4 sm:p-8">
      <div class="w-full max-w-[420px]">

        <!-- Logo (mobile only) -->
        <div class="lg:hidden text-center mb-8">
          <VerticeLogo class="h-[48px] text-white mx-auto" />
        </div>

        <!-- Card -->
        <div class="bg-[#111111] rounded-2xl border border-neutral-800 shadow-2xl overflow-hidden">

          <!-- Header -->
          <Transition name="ctx-fade" mode="out-in">
            <div :key="`header-${isCliente}`" class="px-8 pt-7 pb-5 text-center">
              <h2 class="text-xl font-bold text-white mb-1">
                {{ isCliente
                  ? (isLogin ? 'Bem-vindo de volta' : 'Criar conta gratuita')
                  : (isLogin ? 'Acessar o painel' : 'Cadastro de engenheiro') }}
              </h2>
              <p class="text-sm text-neutral-400">
                {{ isCliente
                  ? (isLogin ? 'Encontre engenheiros verificados na sua região.' : 'Cadastre-se e explore os profissionais disponíveis.')
                  : (isLogin ? 'Plataforma B2B para construtoras e orçamentistas.' : 'Crie seu Tenant B2B e isole seus orçamentos.') }}
              </p>
            </div>
          </Transition>

          <!-- Abas -->
          <div class="relative flex border-y border-neutral-800">
            <button
              type="button"
              @click="isLogin = true; showResetSent = false"
              :class="isLogin ? 'text-white font-semibold' : 'text-neutral-400 hover:text-white'"
              class="flex-1 py-3 text-sm outline-none cursor-pointer z-10 transition-colors"
            >Entrar</button>
            <button
              type="button"
              @click="isLogin = false; showResetSent = false"
              :class="!isLogin ? 'text-white font-semibold' : 'text-neutral-400 hover:text-white'"
              class="flex-1 py-3 text-sm outline-none cursor-pointer z-10 transition-colors"
            >Criar Conta</button>
            <div
              class="absolute bottom-0 h-0.5 transition-all duration-300 ease-in-out w-1/2"
              :class="[
                isLogin ? 'translate-x-0' : 'translate-x-full',
                isCliente ? 'bg-[#F39200]' : 'bg-[#005CA9]'
              ]"
            ></div>
          </div>

          <div class="p-7 space-y-4">

            <!-- Botão Google -->
            <button
              type="button"
              @click="signInWithGoogle"
              :disabled="isGoogleLoading"
              class="w-full flex items-center justify-center gap-3 bg-white hover:bg-neutral-100 active:bg-neutral-200 text-neutral-900 font-semibold py-2.5 px-4 rounded-xl transition-colors cursor-pointer border-none disabled:opacity-70 disabled:cursor-not-allowed text-sm"
            >
              <Loader2 v-if="isGoogleLoading" class="w-4 h-4 animate-spin text-neutral-500" stroke-width="1.5" />
              <svg v-else width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
                <path d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.96L3.964 7.293C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              <span>{{ isLogin ? 'Entrar com Google' : 'Cadastrar com Google' }}</span>
            </button>

            <!-- Divider -->
            <div class="flex items-center gap-3">
              <div class="flex-1 h-px bg-neutral-800"></div>
              <span class="text-xs text-neutral-500">ou use seu e-mail</span>
              <div class="flex-1 h-px bg-neutral-800"></div>
            </div>

            <!-- Confirmação reset enviado -->
            <Transition name="slide-down">
              <div v-if="showResetSent" class="bg-emerald-500/10 border border-emerald-500/25 rounded-xl p-4 text-center">
                <CheckCircle2 class="w-6 h-6 text-emerald-500 mx-auto mb-2" stroke-width="1.5" />
                <p class="text-sm font-semibold text-emerald-400">E-mail enviado!</p>
                <p class="text-xs text-neutral-400 mt-1">Verifique sua caixa de entrada para redefinir a senha.</p>
              </div>
            </Transition>

            <!-- Formulários -->
            <Transition name="form-slide" mode="out-in">

              <!-- Login -->
              <form v-if="isLogin" key="login" @submit.prevent="handleAuth" class="space-y-4">
                <div class="space-y-1.5">
                  <label for="login-email" class="block text-xs font-semibold text-neutral-400 uppercase tracking-wide">
                    {{ isCliente ? 'E-mail' : 'E-mail Profissional' }}
                  </label>
                  <input
                    id="login-email"
                    v-model="email"
                    type="email"
                    required
                    autocomplete="email"
                    class="w-full bg-[#1A1A1A] border border-neutral-700 text-white rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-1 transition-all placeholder:text-neutral-600"
                    :class="isCliente ? 'focus:ring-[#F39200] focus:border-[#F39200]' : 'focus:ring-[#005CA9] focus:border-[#005CA9]'"
                    :placeholder="isCliente ? 'seuemail@gmail.com' : 'engenharia@empresa.com.br'"
                  />
                </div>

                <div class="space-y-1.5">
                  <label for="login-password" class="block text-xs font-semibold text-neutral-400 uppercase tracking-wide">Senha</label>
                  <div class="relative">
                    <input
                      id="login-password"
                      v-model="password"
                      :type="showPassword ? 'text' : 'password'"
                      required
                      autocomplete="current-password"
                      class="w-full bg-[#1A1A1A] border border-neutral-700 text-white rounded-xl py-2.5 pl-3 pr-10 text-sm focus:outline-none focus:ring-1 transition-all placeholder:text-neutral-600"
                      :class="isCliente ? 'focus:ring-[#F39200] focus:border-[#F39200]' : 'focus:ring-[#005CA9] focus:border-[#005CA9]'"
                      placeholder="••••••••"
                    />
                    <button type="button" @click="showPassword = !showPassword"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer p-0.5"
                      :aria-label="showPassword ? 'Ocultar senha' : 'Mostrar senha'"
                    >
                      <EyeOff v-if="showPassword" class="w-4 h-4" stroke-width="1.5" />
                      <Eye v-else class="w-4 h-4" stroke-width="1.5" />
                    </button>
                  </div>
                  <div class="text-right">
                    <button type="button" @click="handleForgotPassword" :disabled="isSendingReset"
                      class="text-xs text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer disabled:opacity-50">
                      {{ isSendingReset ? 'Enviando...' : 'Esqueceu a senha?' }}
                    </button>
                  </div>
                </div>

                <button type="submit" :disabled="isSubmitting"
                  class="w-full text-white font-bold py-2.5 px-4 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer border-none mt-1"
                  :class="isCliente ? 'bg-[#F39200] hover:bg-[#D97F00] active:bg-[#C07000]' : 'bg-[#005CA9] hover:bg-[#004A88] active:bg-[#003D74]'"
                >
                  <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" stroke-width="1.5" />
                  <span>{{ isSubmitting ? 'Aguarde...' : 'Entrar' }}</span>
                </button>
              </form>

              <!-- Cadastro -->
              <form v-else key="register" @submit.prevent="handleAuth" class="space-y-4">
                <div class="space-y-1.5">
                  <label for="reg-name" class="block text-xs font-semibold text-neutral-400 uppercase tracking-wide">Nome Completo</label>
                  <input id="reg-name" v-model="fullName" @input="fullName = fullName.replace(/[0-9]/g, '')"
                    type="text" required autocomplete="name"
                    class="w-full bg-[#1A1A1A] border border-neutral-700 text-white rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-1 transition-all placeholder:text-neutral-600"
                    :class="isCliente ? 'focus:ring-[#F39200] focus:border-[#F39200]' : 'focus:ring-[#005CA9] focus:border-[#005CA9]'"
                    :placeholder="isCliente ? 'Ex: Maria Silva' : 'Eng. João Silva'"
                  />
                </div>

                <div class="space-y-1.5">
                  <label for="reg-email" class="block text-xs font-semibold text-neutral-400 uppercase tracking-wide">
                    {{ isCliente ? 'E-mail' : 'E-mail Profissional' }}
                  </label>
                  <input id="reg-email" v-model="email" type="email" required autocomplete="email"
                    class="w-full bg-[#1A1A1A] border border-neutral-700 text-white rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-1 transition-all placeholder:text-neutral-600"
                    :class="isCliente ? 'focus:ring-[#F39200] focus:border-[#F39200]' : 'focus:ring-[#005CA9] focus:border-[#005CA9]'"
                    :placeholder="isCliente ? 'seuemail@gmail.com' : 'engenharia@empresa.com.br'"
                  />
                </div>

                <div class="space-y-1.5">
                  <label for="reg-password" class="block text-xs font-semibold text-neutral-400 uppercase tracking-wide">Senha</label>
                  <div class="relative">
                    <input id="reg-password" v-model="password" :type="showPassword ? 'text' : 'password'"
                      required autocomplete="new-password" minlength="6"
                      class="w-full bg-[#1A1A1A] border border-neutral-700 text-white rounded-xl py-2.5 pl-3 pr-10 text-sm focus:outline-none focus:ring-1 transition-all placeholder:text-neutral-600"
                      :class="isCliente ? 'focus:ring-[#F39200] focus:border-[#F39200]' : 'focus:ring-[#005CA9] focus:border-[#005CA9]'"
                      placeholder="••••••••"
                    />
                    <button type="button" @click="showPassword = !showPassword"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer p-0.5"
                      :aria-label="showPassword ? 'Ocultar senha' : 'Mostrar senha'"
                    >
                      <EyeOff v-if="showPassword" class="w-4 h-4" stroke-width="1.5" />
                      <Eye v-else class="w-4 h-4" stroke-width="1.5" />
                    </button>
                  </div>
                  <p class="text-[11px] text-neutral-600">Mínimo 6 caracteres</p>
                </div>

                <div v-if="!isCliente" class="space-y-1.5">
                  <label for="reg-crea" class="block text-xs font-semibold text-neutral-400 uppercase tracking-wide">Registro CREA/CAU</label>
                  <input id="reg-crea" v-model="creaCau" type="text" required
                    class="w-full bg-[#1A1A1A] border border-neutral-700 text-white rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#005CA9] focus:border-[#005CA9] transition-all placeholder:text-neutral-600"
                    placeholder="Ex: SP-123456/D"
                  />
                </div>

                <button type="submit" :disabled="isSubmitting"
                  class="w-full text-white font-bold py-2.5 px-4 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer border-none mt-1"
                  :class="isCliente ? 'bg-[#F39200] hover:bg-[#D97F00] active:bg-[#C07000]' : 'bg-[#005CA9] hover:bg-[#004A88] active:bg-[#003D74]'"
                >
                  <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" stroke-width="1.5" />
                  <span>{{ isSubmitting ? 'Aguarde...' : (isCliente ? 'Criar Conta' : 'Criar Tenant B2B') }}</span>
                </button>
              </form>

            </Transition>
          </div>
        </div>

        <!-- Link cruzado -->
        <p class="text-center text-xs text-neutral-600 mt-5">
          <template v-if="isCliente">
            É engenheiro?
            <router-link to="/auth" class="text-[#4FA8F5] hover:underline font-medium ml-1">Acessar painel B2B →</router-link>
          </template>
          <template v-else>
            Quer construir sua casa?
            <router-link to="/auth?tipo=cliente&redirect=/buscar" class="text-[#F39200] hover:underline font-medium ml-1">Encontrar engenheiro →</router-link>
          </template>
        </p>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* Carrossel de depoimentos */
.testimonial-enter-active {
  transition: opacity 0.45s cubic-bezier(0.25, 0.46, 0.45, 0.94),
              transform 0.45s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.testimonial-leave-active {
  transition: opacity 0.25s cubic-bezier(0.55, 0, 1, 0.45),
              transform 0.25s cubic-bezier(0.55, 0, 1, 0.45);
  position: absolute;
  width: 100%;
}
.testimonial-enter-from { opacity: 0; transform: translateY(18px); }
.testimonial-leave-to   { opacity: 0; transform: translateY(-12px); }

/* Contexto (modo eng/cliente) */
.ctx-fade-enter-active { transition: opacity 0.35s ease, transform 0.35s ease; }
.ctx-fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.ctx-fade-enter-from   { opacity: 0; transform: translateY(8px); }
.ctx-fade-leave-to     { opacity: 0; transform: translateY(-6px); }

/* Formulário */
.form-slide-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.form-slide-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.form-slide-enter-from   { opacity: 0; transform: translateX(8px); }
.form-slide-leave-to     { opacity: 0; transform: translateX(-8px); }

/* Reset enviado */
.slide-down-enter-active { transition: all 0.3s ease; }
.slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from   { opacity: 0; transform: translateY(-8px); max-height: 0; }
.slide-down-leave-to     { opacity: 0; transform: translateY(-4px); max-height: 0; }

/* Progress bar do carrossel */
@keyframes progress-run {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}
.progress-bar {
  transform-origin: left center;
  animation: progress-run 5.5s linear forwards;
}
</style>
