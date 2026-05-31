<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSidebar } from '../composables/useSidebar'
import {
  Home,
  FolderGit2,
  Calculator,
  Users,
  Settings,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  PlusCircle,
  HelpCircle,
  Fingerprint,
  Building2,
  SlidersHorizontal,
  Globe,
  Network,
  PenTool,
  X
} from 'lucide-vue-next'
import VerticeLogo from './VerticeLogo.vue'

const route = useRoute()
const { isSidebarOpen, toggleSidebar } = useSidebar()

const isConfigsRoute = computed(() => route.path.startsWith('/configuracoes'))

// Controla qual nav exibir de forma independente da rota
const showSettingsNav = ref(isConfigsRoute.value)

// Quando o sidebar abre, sincroniza com a rota atual
watch(isSidebarOpen, (open) => {
  if (open) showSettingsNav.value = isConfigsRoute.value
})

// Se o usuário navegar diretamente para uma rota de configs, garante que o sub-menu apareça
watch(isConfigsRoute, (val) => {
  if (val) showSettingsNav.value = true
})

const settingsNav = [
  { path: '/configuracoes/perfil',         label: 'Perfil',             icon: Fingerprint },
  { path: '/configuracoes/empresa',        label: 'Empresa',            icon: Building2 },
  { path: '/configuracoes/preferencias',   label: 'Preferências',       icon: SlidersHorizontal },
  { path: '/configuracoes/vitrine',        label: 'Vitrine',            icon: Globe },
  { path: '/configuracoes/parametros-eap', label: 'Parâmetros EAP',     icon: Network },
  { path: '/configuracoes/contratos',      label: 'Motor de Contratos', icon: PenTool },
]
</script>

<template>
  <!-- Overlay escurecido para mobile -->
  <Transition
    enter-active-class="transition-opacity duration-300 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-300 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="isSidebarOpen"
      @click="toggleSidebar"
      class="fixed inset-0 bg-zinc-950/40 dark:bg-black/60 z-[90] lg:hidden"
    ></div>
  </Transition>

  <aside :class="[
    'h-screen w-[85%] max-w-[320px] lg:w-64 fixed left-0 top-0 flex flex-col bg-surface border-r border-hairline z-[100] transition-transform duration-300 ease-in-out',
    isSidebarOpen ? 'translate-x-0' : '-translate-x-full',
    'lg:translate-x-0'
  ]">
    <div class="flex flex-col justify-between pb-6 h-full overflow-y-auto overflow-x-hidden">
      <div>
        <!-- Brand -->
        <div class="px-4 pt-1 mb-6 flex items-center justify-between">
          <VerticeLogo class="h-[66px] text-logo" />
          <button
            @click="isSidebarOpen = false"
            class="lg:hidden p-1.5 text-ink-muted hover:text-ink hover:bg-surface-hover rounded-md transition-all duration-300 hover:rotate-90 active:rotate-180 active:scale-95 flex items-center justify-center"
          >
            <X class="w-[18px] h-[18px]" stroke-width="1.5" />
          </button>
        </div>

        <Transition name="menu-slide" mode="out-in">
          <!-- Nav principal -->
          <nav v-if="!showSettingsNav" key="main" class="space-y-1 nav-container">
            <router-link to="/dashboard" @click="isSidebarOpen = false"
              :class="[route.path === '/dashboard' ? 'bg-brand-blue/[0.08] text-brand-blue font-semibold' : 'text-ink-muted hover:text-ink hover:bg-surface-hover', 'nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200']">
              <Home class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
              <span>Início</span>
            </router-link>

            <div class="nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium text-ink-muted/50 cursor-not-allowed">
              <FolderGit2 class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
              <span>Projetos</span>
              <span class="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-surface-hover text-ink-muted">Em breve</span>
            </div>

            <router-link to="/engenharia" @click="isSidebarOpen = false"
              :class="[route.path.startsWith('/engenharia') || route.path.startsWith('/orcamento') ? 'bg-brand-blue/[0.08] text-brand-blue font-semibold' : 'text-ink-muted hover:text-ink hover:bg-surface-hover', 'nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200']">
              <Calculator class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
              <span>Engenharia</span>
            </router-link>

            <div class="nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium text-ink-muted/50 cursor-not-allowed">
              <Users class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
              <span>Clientes</span>
              <span class="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-surface-hover text-ink-muted">Em breve</span>
            </div>

            <!-- Configurações: abre sub-menu sem fechar o sidebar -->
            <router-link
              to="/configuracoes"
              @click.prevent="showSettingsNav = true"
              class="group nav-item text-ink-muted hover:text-ink hover:bg-surface-hover flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200"
            >
              <Settings class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
              <span>Configurações</span>
              <ChevronRight class="w-4 h-4 ml-auto text-ink-muted group-hover:text-ink transition-colors" stroke-width="1.5" />
            </router-link>
          </nav>

          <!-- Nav de configurações -->
          <nav v-else key="settings" class="space-y-1 nav-container">
            <!-- Voltar ao nav principal sem fechar nem navegar -->
            <button
              @click="showSettingsNav = false"
              class="w-full nav-item text-ink-muted hover:text-ink hover:bg-surface-hover flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200 group cursor-pointer"
            >
              <ChevronLeft class="w-[18px] h-[18px] text-current transition-transform group-hover:-translate-x-1" stroke-width="1.5" />
              <span>Configurações</span>
            </button>

            <div class="mx-6 border-t border-hairline my-2"></div>

            <!-- Sub-itens: navega E fecha o sidebar -->
            <router-link
              v-for="item in settingsNav"
              :key="item.path"
              :to="item.path"
              @click="isSidebarOpen = false"
              :class="[
                route.path === item.path
                  ? 'bg-brand-blue/[0.08] text-brand-blue font-semibold'
                  : 'text-ink-muted hover:text-ink hover:bg-surface-hover',
                'nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200'
              ]"
            >
              <component :is="item.icon" class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
              <span>{{ item.label }}</span>
            </router-link>
          </nav>
        </Transition>
      </div>

      <!-- Rodapé -->
      <Transition name="fade" mode="out-in">
        <div v-if="!showSettingsNav" key="footer" class="mt-auto space-y-1 mb-6">
          <div class="mx-4 border-t border-hairline my-2"></div>

          <router-link to="/admin" @click="isSidebarOpen = false"
            :class="[route.path === '/admin' ? 'bg-brand-blue/[0.08] text-brand-blue font-semibold' : 'text-ink-muted hover:text-ink hover:bg-surface-hover', 'flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200']">
            <RefreshCw class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
            <span>Sincronizar SINAPI</span>
            <span class="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded bg-canvas border border-hairline text-ink-muted">Admin</span>
          </router-link>

          <div class="flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium text-ink-muted/50 cursor-not-allowed">
            <PlusCircle class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
            <span>Novo Dossiê Caixa</span>
            <span class="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-surface-hover text-ink-muted">Em breve</span>
          </div>

          <div class="flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium text-ink-muted/50 cursor-not-allowed">
            <HelpCircle class="w-[18px] h-[18px] text-current" stroke-width="1.5" />
            <span>Ajuda</span>
            <span class="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-surface-hover text-ink-muted">Em breve</span>
          </div>
        </div>
      </Transition>
    </div>
  </aside>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
