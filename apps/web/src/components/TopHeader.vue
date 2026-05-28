<script setup>
import { useRouter, useRoute } from 'vue-router'
import { supabase } from '../supabase'
import { useSidebar } from '../composables/useSidebar'
import { useProfile } from '../composables/useProfile'
import { isDark, toggleTheme } from '../composables/useTheme'
import { useNotificacoes } from '../composables/useNotificacoes'
import { ref, onMounted, onUnmounted, watch } from 'vue'
import {
  Menu, ArrowLeft, Search, Archive, PlusCircle,
  Sun, Moon, Bell, LogOut, User, UserCog, Settings,
  FileText, RefreshCw, CheckCheck, Check
} from 'lucide-vue-next'
import BaseButton from './ui/BaseButton.vue'

const router = useRouter()
const route = useRoute()
const isProfileOpen = ref(false)
const profileRef = ref(null)
const isBellOpen = ref(false)
const bellRef = ref(null)

const { profile } = useProfile()
const { notificacoes, naoLidas, marcarLida, marcarTodasLidas } = useNotificacoes()

const toggleProfile = () => {
  isProfileOpen.value = !isProfileOpen.value
  isBellOpen.value = false
}

const toggleBell = () => {
  isBellOpen.value = !isBellOpen.value
  isProfileOpen.value = false
}

const handleLogout = async () => {
  await supabase.auth.signOut()
  router.push('/auth')
}

// Fechar ao clicar fora
const handleClickOutside = (event) => {
  if (profileRef.value && !profileRef.value.contains(event.target)) {
    isProfileOpen.value = false
  }
  if (bellRef.value && !bellRef.value.contains(event.target)) {
    isBellOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Fechar ao mudar de rota
watch(() => route.path, () => {
  isProfileOpen.value = false
  isBellOpen.value = false
})

const { toggleSidebar } = useSidebar()
const emit = defineEmits(['new-client', 'open-archived'])

const abrirModalArquivados = () => {
  emit('open-archived')
}

const formatarTempo = (data) => {
  const diff = Date.now() - new Date(data).getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return 'agora'
  if (min < 60) return `${min}min atrás`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h}h atrás`
  return `${Math.floor(h / 24)}d atrás`
}
</script>

<template>
  <header class="h-16 w-full sticky top-0 z-50 bg-surface border-b border-hairline shadow-sm flex items-center justify-between px-4 lg:px-8 gap-4 transition-colors text-ink select-none">
    <div class="flex items-center flex-1 gap-2">
      <BaseButton 
        variant="ghost"
        size="icon"
        @click="toggleSidebar" 
        class="lg:hidden -ml-2"
      >
        <Menu class="w-[18px] h-[18px]" stroke-width="1.5" />
      </BaseButton>
      
      <BaseButton
        v-if="route.path.startsWith('/orcamento')"
        variant="ghost"
        size="sm"
        @click="router.push('/engenharia')"
        class="hidden sm:flex items-center gap-1 font-semibold text-ink-muted hover:text-ink shrink-0"
      >
        <ArrowLeft class="w-[18px] h-[18px]" stroke-width="1.5" />
        Obras
      </BaseButton>
      
      <BaseButton
        v-if="route.path.startsWith('/configuracoes')"
        variant="ghost"
        size="sm"
        @click="router.push('/dashboard')"
        class="hidden sm:flex items-center gap-1 font-semibold text-ink-muted hover:text-ink shrink-0"
      >
        <ArrowLeft class="w-[18px] h-[18px]" stroke-width="1.5" />
        Dashboard
      </BaseButton>
      
      <!-- Input de busca global Vercel Aesthetic -->
      <div class="relative w-full max-w-md select-none">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted w-4.5 h-4.5 pointer-events-none" stroke-width="1.5" />
        <input 
          class="w-full bg-canvas border border-hairline rounded-md py-2 pl-10 pr-4 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-all font-sans" 
          placeholder="Buscar cliente ou obra..." 
          type="text"
        />
      </div>
    </div>

    <div class="flex items-center gap-4">
      <!-- Botão de Projetos Arquivados (Visível apenas no Início) -->
      <BaseButton 
        v-if="route.path === '/dashboard'"
        variant="secondary"
        size="icon"
        @click="abrirModalArquivados"
        title="Ver Projetos Arquivados"
        class="hidden sm:flex w-10 h-10 group"
      >
        <Archive class="w-5 h-5 group-hover:scale-110 transition-transform duration-200" stroke-width="1.5" />
      </BaseButton>

      <!-- Botão Novo Cliente Primário Vercel Style (Alto Contraste) -->
      <BaseButton 
        v-if="route.path === '/dashboard'" 
        variant="primary"
        size="md"
        @click="emit('new-client')" 
        title="Novo Cliente" 
        class="px-2 sm:px-6 gap-2"
      >
        <PlusCircle class="w-5 h-5 sm:w-[18px] sm:h-[18px]" stroke-width="1.5" />
        <span class="hidden sm:inline">Novo Cliente</span>
      </BaseButton>

      <div class="h-8 w-[1px] bg-hairline mx-2"></div>

      <div class="flex items-center gap-3">
        <BaseButton 
          variant="ghost"
          size="icon"
          @click="toggleTheme" 
          title="Alternar Tema"
        >
          <Sun v-if="!isDark" class="w-5 h-5" stroke-width="1.5" />
          <Moon v-else class="w-5 h-5" stroke-width="1.5" />
        </BaseButton>
        
        <!-- Sininho de Notificações -->
        <div class="relative" ref="bellRef">
          <button
            @click="toggleBell"
            class="relative w-10 h-10 flex items-center justify-center rounded-md text-ink-muted hover:text-ink hover:bg-surface-hover transition-colors cursor-pointer"
            title="Notificações"
          >
            <Bell class="w-5 h-5" stroke-width="1.5" />
            <span
              v-if="naoLidas > 0"
              class="absolute top-1.5 right-1.5 min-w-[16px] h-4 px-1 bg-blue-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center leading-none"
            >{{ naoLidas > 9 ? '9+' : naoLidas }}</span>
          </button>

          <!-- Dropdown de Notificações -->
          <transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95"
          >
            <div v-if="isBellOpen" class="absolute right-0 mt-2 w-80 bg-surface rounded-md border border-hairline shadow-xl z-50 overflow-hidden">
              <!-- Header -->
              <div class="flex items-center justify-between px-4 py-3 border-b border-hairline bg-canvas">
                <span class="text-sm font-semibold text-ink">Notificações</span>
                <button
                  v-if="naoLidas > 0"
                  @click="marcarTodasLidas"
                  class="flex items-center gap-1 text-xs text-ink-muted hover:text-ink transition-colors cursor-pointer"
                  title="Marcar todas como lidas"
                >
                  <CheckCheck class="w-3.5 h-3.5" stroke-width="1.5" />
                  Limpar
                </button>
              </div>

              <!-- Lista -->
              <div class="max-h-80 overflow-y-auto">
                <div v-if="notificacoes.length === 0" class="flex flex-col items-center justify-center py-10 gap-2 text-ink-muted">
                  <Bell class="w-8 h-8 opacity-30" stroke-width="1.5" />
                  <span class="text-sm">Nenhuma notificação</span>
                </div>

                <div
                  v-for="n in notificacoes"
                  :key="n.id"
                  class="flex items-start gap-3 px-4 py-3 hover:bg-surface-hover transition-colors border-b border-hairline last:border-b-0"
                  :class="n.lida ? 'opacity-50' : ''"
                >
                  <div class="shrink-0 mt-0.5 w-7 h-7 rounded-full flex items-center justify-center"
                    :class="n.tipo === 'reenvio' ? 'bg-amber-500/10' : 'bg-blue-500/10'"
                  >
                    <RefreshCw v-if="n.tipo === 'reenvio'" class="w-3.5 h-3.5 text-amber-500" stroke-width="2" />
                    <FileText v-else class="w-3.5 h-3.5 text-blue-500" stroke-width="2" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm text-ink leading-snug">{{ n.mensagem }}</p>
                    <span class="text-xs text-ink-muted mt-0.5 block">{{ formatarTempo(n.criadaEm) }}</span>
                  </div>
                  <button
                    v-if="!n.lida"
                    @click="marcarLida(n.id)"
                    title="Marcar como lida"
                    class="shrink-0 mt-0.5 w-6 h-6 flex items-center justify-center rounded-md text-ink-muted hover:text-emerald-500 hover:bg-emerald-500/10 transition-colors cursor-pointer"
                  >
                    <Check class="w-3.5 h-3.5" stroke-width="2.5" />
                  </button>
                  <div v-else class="shrink-0 w-6 h-6" />
                </div>
              </div>
            </div>
          </transition>
        </div>
        <!-- Avatar / Profile Dropdown -->
        <div class="relative" ref="profileRef">
          <button @click="toggleProfile" class="flex items-center focus:outline-none cursor-pointer">
            <img 
              v-if="profile?.foto_perfil"
              class="h-9 w-9 rounded-full border border-hairline object-cover hover:border-neutral-500/50 transition-colors" 
              alt="User" 
              :src="profile.foto_perfil"
            />
            <div
              v-else
              class="h-9 w-9 rounded-full border border-hairline hover:border-neutral-500/50 transition-colors flex items-center justify-center bg-canvas text-ink-muted hover:text-ink"
            >
              <User class="w-5 h-5" stroke-width="1.5" />
            </div>
          </button>
  
          <!-- Dropdown Menu -->
          <transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95"
          >
            <div v-if="isProfileOpen" class="absolute right-0 mt-2 w-64 bg-surface rounded-md border border-hairline shadow-xl py-2 z-50 text-ink">
              <!-- Header Profile -->
              <div class="px-4 py-3 border-b border-hairline bg-canvas rounded-t-md">
                <div class="flex flex-col">
                  <span class="text-sm font-medium text-ink">{{ profile?.nome_completo || 'Usuário' }}</span>
                  <div class="flex items-center gap-1.5 mt-1" v-if="profile?.registro_crea_cau">
                    <span class="text-[10px] bg-canvas text-blue-500 border border-hairline px-1.5 py-0.5 rounded-md font-bold uppercase tracking-tight">{{ profile.registro_crea_cau }}</span>
                  </div>
                  <span class="text-[11px] text-ink-muted mt-1 font-mono">ID: #{{ profile?.id ? profile.id.slice(0, 4).toUpperCase() : '----' }}</span>
                </div>
              </div>
  
              <!-- Menu Items -->
              <div class="py-1">
                <button @click="router.push('/configuracoes')" class="w-full text-left px-4 py-2.5 text-sm text-ink-muted hover:bg-surface-hover hover:text-ink flex items-center gap-3 transition-colors cursor-pointer">
                  <UserCog class="w-[18px] h-[18px] text-ink-muted" stroke-width="1.5" />
                  Editar Cadastro
                </button>
                <button @click="router.push('/configuracoes')" class="w-full text-left px-4 py-2.5 text-sm text-ink-muted hover:bg-surface-hover hover:text-ink flex items-center gap-3 transition-colors cursor-pointer">
                  <Settings class="w-[18px] h-[18px] text-ink-muted" stroke-width="1.5" />
                  Configurações
                </button>
              </div>
  
              <!-- Logout -->
              <div class="border-t border-hairline mt-1 pt-1">
                <button @click="handleLogout" class="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-3 transition-colors font-medium cursor-pointer">
                  <LogOut class="w-[18px] h-[18px]" stroke-width="1.5" />
                  Sair do Sistema
                </button>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </header>
</template>
