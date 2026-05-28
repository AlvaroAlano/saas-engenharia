<script setup>
import { computed } from 'vue'
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

const route = useRoute()
const { isSidebarOpen, toggleSidebar } = useSidebar()

const isConfigsRoute = computed(() => route.path.startsWith('/configuracoes'))

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
    <div class="flex flex-col justify-between py-6 h-full overflow-y-auto overflow-x-hidden">
      <div>
        <!-- Brand -->
        <div class="px-6 mb-8 flex items-center justify-between">
          <div>
            <h1 class="text-lg font-bold text-ink tracking-tight">Engenharia</h1>
            <p class="text-xs text-ink-muted">SaaS Dashboard</p>
          </div>
          <button
            @click="isSidebarOpen = false"
            class="lg:hidden p-1.5 text-ink-muted hover:text-ink hover:bg-surface-hover rounded-md transition-all duration-300 hover:rotate-90 active:rotate-180 active:scale-95 flex items-center justify-center"
          >
            <X class="w-[18px] h-[18px]" stroke-width="1.5" />
          </button>
        </div>

        <Transition name="menu-slide" mode="out-in">
          <!-- Nav principal -->
          <nav v-if="!isConfigsRoute" key="main" class="space-y-1 nav-container">
            <router-link to="/dashboard" @click="isSidebarOpen = false"
              :class="[route.path === '/dashboard' ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800', 'nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200']">
              <Home class="w-[18px] h-[18px]" stroke-width="1.5" />
              <span>Início</span>
            </router-link>

            <div class="nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium text-neutral-400 opacity-50 cursor-not-allowed" title="Funcionalidade em desenvolvimento">
              <FolderGit2 class="w-[18px] h-[18px]" stroke-width="1.5" />
              <span>Projetos</span>
            </div>

            <router-link to="/engenharia" @click="isSidebarOpen = false"
              :class="[route.path.startsWith('/engenharia') || route.path.startsWith('/orcamento') ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800', 'nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200']">
              <Calculator class="w-[18px] h-[18px]" stroke-width="1.5" />
              <span>Engenharia</span>
            </router-link>

            <div class="nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium text-neutral-400 opacity-50 cursor-not-allowed" title="Funcionalidade em desenvolvimento">
              <Users class="w-[18px] h-[18px]" stroke-width="1.5" />
              <span>Clientes</span>
            </div>

            <router-link to="/configuracoes" @click="isSidebarOpen = false"
              class="group nav-item text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200">
              <Settings class="w-[18px] h-[18px]" stroke-width="1.5" />
              <span>Configurações</span>
              <ChevronRight class="w-4 h-4 ml-auto text-neutral-500 group-hover:text-neutral-300 transition-colors" stroke-width="1.5" />
            </router-link>
          </nav>

          <!-- Nav de configurações (Substitui o principal) -->
          <nav v-else key="settings" class="space-y-1 nav-container">
            <router-link to="/dashboard" @click="isSidebarOpen = false"
              class="nav-item text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200 group">
              <ChevronLeft class="w-[18px] h-[18px] transition-transform group-hover:-translate-x-1" stroke-width="1.5" />
              <span>Configurações</span>
            </router-link>

            <div class="mx-6 border-t border-hairline my-2"></div>

            <router-link
              v-for="item in settingsNav"
              :key="item.path"
              :to="item.path"
              @click="isSidebarOpen = false"
              :class="[
                route.path === item.path
                  ? 'bg-neutral-800 text-white'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800',
                'nav-item flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200'
              ]"
            >
              <component :is="item.icon" class="w-[18px] h-[18px]" stroke-width="1.5" />
              <span>{{ item.label }}</span>
            </router-link>
          </nav>
        </Transition>
      </div>

      <!-- Rodapé -->
      <Transition name="fade" mode="out-in">
        <div v-if="!isConfigsRoute" key="footer" class="mt-auto space-y-1 mb-6">
          <router-link to="/admin" @click="isSidebarOpen = false"
            :class="[route.path === '/admin' ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800', 'flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200']">
            <RefreshCw class="w-[18px] h-[18px]" stroke-width="1.5" />
            <span>Sincronizar SINAPI</span>
          </router-link>
          <div class="flex items-center justify-center gap-2 mx-2 px-3 py-1.5 rounded-md text-sm font-medium text-neutral-400 border border-neutral-800 opacity-50 cursor-not-allowed transition-colors" title="Funcionalidade em desenvolvimento">
            <PlusCircle class="w-[18px] h-[18px]" stroke-width="1.5" />
            <span>Novo Dossiê Caixa</span>
          </div>
          <div class="flex items-center gap-3 mx-2 px-3 py-1.5 rounded-md text-sm font-medium text-neutral-400 opacity-50 cursor-not-allowed" title="Funcionalidade em desenvolvimento">
            <HelpCircle class="w-[18px] h-[18px]" stroke-width="1.5" />
            <span>Ajuda</span>
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
