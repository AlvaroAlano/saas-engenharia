<script setup>
import { useRouter, useRoute } from 'vue-router'
import { supabase } from '../supabase'
import { useSidebar } from '../composables/useSidebar'
import { useProfile } from '../composables/useProfile'
import { isDark, toggleTheme } from '../composables/useTheme'
import { ref, onMounted, onUnmounted, watch } from 'vue'

const router = useRouter()
const route = useRoute()
const isProfileOpen = ref(false)
const profileRef = ref(null)

const { profile } = useProfile()

const toggleProfile = () => {
  isProfileOpen.value = !isProfileOpen.value
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
})

const { toggleSidebar } = useSidebar()
const emit = defineEmits(['new-client', 'open-archived'])

const abrirModalArquivados = () => {
  emit('open-archived')
}
</script>

<template>
  <header class="h-16 w-full sticky top-0 z-50 bg-surface border-b border-hairline flex items-center justify-between px-4 lg:px-8 gap-4 transition-colors">
    <div class="flex items-center flex-1 gap-2">
      <button @click="toggleSidebar" class="lg:hidden p-2 -ml-2 text-ink-muted hover:bg-surface-hover rounded-md transition-colors flex items-center justify-center cursor-pointer">
        <span class="material-symbols-outlined">menu</span>
      </button>
      <button
        v-if="route.path.startsWith('/orcamento')"
        @click="router.push('/engenharia')"
        class="hidden sm:flex items-center gap-1 text-sm font-semibold text-ink-muted hover:text-ink transition-colors shrink-0"
      >
        <span class="material-symbols-outlined text-[18px]">arrow_back</span>
        Obras
      </button>
      <button
        v-else-if="route.path === '/configuracoes'"
        @click="router.push('/dashboard')"
        class="hidden sm:flex items-center gap-1 text-sm font-semibold text-ink-muted hover:text-ink transition-colors shrink-0"
      >
        <span class="material-symbols-outlined text-[18px]">arrow_back</span>
        Dashboard
      </button>
      <div class="relative w-full max-w-md">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted text-lg">search</span>
        <input class="w-full bg-canvas border border-hairline rounded-md py-2 pl-10 pr-4 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/50 transition-colors" placeholder="Buscar cliente ou obra..." type="text"/>
      </div>
    </div>
    <div class="flex items-center gap-4">
      <!-- Botão de Projetos Arquivados (Visível apenas no Início) -->
      <button 
        v-if="route.path === '/dashboard'"
        @click="abrirModalArquivados"
        title="Ver Projetos Arquivados"
        class="hidden sm:flex items-center justify-center w-10 h-10 rounded-md border border-hairline bg-surface text-ink-muted hover:bg-surface-hover hover:text-ink transition-colors group"
      >
        <span class="material-symbols-outlined text-[20px] group-hover:scale-110 transition-transform duration-200">archive</span>
      </button>
      <button v-if="!route.path.startsWith('/orcamento')" @click="emit('new-client')" title="Novo Cliente" class="bg-brand-primary hover:bg-brand-hover text-white p-2 sm:px-6 sm:py-2 rounded-md font-medium transition-colors active:opacity-80 text-sm flex items-center justify-center gap-2 cursor-pointer">
        <span class="material-symbols-outlined text-[20px] sm:text-[18px]">add_circle</span>
        <span class="hidden sm:inline">Novo Cliente</span>
      </button>
      <div class="h-8 w-[1px] bg-hairline mx-2"></div>
      <div class="flex items-center gap-3">
        <button @click="toggleTheme" class="text-ink-muted hover:text-ink hover:bg-surface-hover transition-colors flex items-center cursor-pointer p-1.5 rounded-md" title="Alternar Tema">
          <span class="material-symbols-outlined text-[20px]">{{ isDark ? 'light_mode' : 'dark_mode' }}</span>
        </button>
        <button class="text-ink-muted hover:text-ink hover:bg-surface-hover transition-colors flex items-center cursor-pointer p-1.5 rounded-md">
          <span class="material-symbols-outlined text-[20px]">notifications</span>
        </button>
        <button @click="handleLogout" class="text-red-400 dark:text-red-500 hover:text-red-600 dark:hover:text-red-400 transition-colors flex items-center cursor-pointer p-1.5 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md" title="Sair (Logout)">
          <span class="material-symbols-outlined text-[20px]">logout</span>
        </button>
        
        <!-- Avatar / Profile Dropdown -->
        <div class="relative" ref="profileRef">
          <button @click="toggleProfile" class="flex items-center focus:outline-none cursor-pointer">
            <img 
              class="h-9 w-9 rounded-full border border-hairline object-cover hover:border-brand-primary transition-colors" 
              alt="User" 
              :src="profile?.foto_perfil || 'https://ui-avatars.com/api/?name=' + (profile?.nome_completo || 'User')"
            />
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
            <div v-if="isProfileOpen" class="absolute right-0 mt-2 w-64 bg-surface rounded-xl border border-hairline shadow-sm py-2 z-50">
              <!-- Header Profile -->
              <div class="px-4 py-3 border-b border-hairline bg-canvas">
                <div class="flex flex-col">
                  <span class="text-sm font-medium text-ink">{{ profile?.nome_completo || 'Usuário' }}</span>
                  <div class="flex items-center gap-1.5 mt-1" v-if="profile?.registro_crea_cau">
                    <span class="text-[10px] bg-canvas text-brand-primary border border-hairline px-1.5 py-0.5 rounded-full font-bold uppercase tracking-tight">{{ profile.registro_crea_cau }}</span>
                  </div>
                  <span class="text-[11px] text-ink-muted mt-1 font-mono">ID: #{{ profile?.id ? profile.id.slice(0, 4).toUpperCase() : '----' }}</span>
                </div>
              </div>
 
              <!-- Menu Items -->
              <div class="py-1">
                <button @click="router.push('/configuracoes')" class="w-full text-left px-4 py-2.5 text-sm text-ink hover:bg-surface-hover flex items-center gap-3 transition-colors">
                  <span class="material-symbols-outlined text-[18px] text-ink-muted">person_edit</span>
                  Editar Cadastro
                </button>
                <button @click="router.push('/configuracoes')" class="w-full text-left px-4 py-2.5 text-sm text-ink hover:bg-surface-hover flex items-center gap-3 transition-colors">
                  <span class="material-symbols-outlined text-[18px] text-ink-muted">settings</span>
                  Configurações
                </button>
              </div>
 
              <!-- Logout -->
              <div class="border-t border-hairline mt-1 pt-1">
                <button @click="handleLogout" class="w-full text-left px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center gap-3 transition-colors font-medium">
                  <span class="material-symbols-outlined text-[18px]">logout</span>
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
