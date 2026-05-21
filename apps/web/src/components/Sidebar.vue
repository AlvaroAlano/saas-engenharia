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
    <div class="flex flex-col justify-between py-6 h-full">
      <div>
        <!-- Brand Anchor -->
        <div class="px-6 mb-8 flex items-center justify-between">
          <div>
            <h1 class="text-lg font-bold text-ink tracking-tight">Engenharia</h1>
            <p class="text-xs text-ink-muted">SaaS Dashboard</p>
          </div>
          <button @click="isSidebarOpen = false" class="lg:hidden p-1.5 text-ink-muted hover:text-ink hover:bg-surface-hover rounded-md transition-all duration-300 hover:rotate-90 active:rotate-180 active:scale-95 flex items-center justify-center">
            <span class="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
        <nav class="space-y-1">
          <router-link to="/dashboard" @click="isSidebarOpen = false"
            :class="[route.path === '/dashboard' ? 'bg-canvas text-brand-primary border-l-2 border-brand-primary' : 'text-ink-muted hover:text-ink hover:bg-canvas border-l-2 border-transparent', 'flex items-center gap-3 px-6 py-3 font-medium transition-colors duration-200']">
            <span class="material-symbols-outlined">home</span>
            <span class="text-sm">Início</span>
          </router-link>
          <div
            @click="isSidebarOpen = false"
            class="flex items-center gap-3 text-ink-muted opacity-50 cursor-not-allowed px-6 py-3 border-l-2 border-transparent"
            title="Funcionalidade em desenvolvimento">
            <span class="material-symbols-outlined">foundation</span>
            <span class="text-sm">Projetos</span>
          </div>
          <router-link to="/engenharia" @click="isSidebarOpen = false"
            :class="[route.path.startsWith('/engenharia') || route.path.startsWith('/orcamento') ? 'bg-canvas text-brand-primary border-l-2 border-brand-primary' : 'text-ink-muted hover:text-ink hover:bg-canvas border-l-2 border-transparent', 'flex items-center gap-3 px-6 py-3 font-medium transition-colors duration-200']">
            <span class="material-symbols-outlined">payments</span>
            <span class="text-sm">Engenharia</span>
          </router-link>
          <div @click="isSidebarOpen = false" class="flex items-center gap-3 text-ink-muted opacity-50 cursor-not-allowed px-6 py-3"
            title="Funcionalidade em desenvolvimento">
            <span class="material-symbols-outlined">group</span>
            <span class="text-sm">Clientes</span>
          </div>
          <router-link to="/configuracoes/contratos" @click="isSidebarOpen = false"
            :class="[route.path.startsWith('/configuracoes') ? 'bg-canvas text-brand-primary border-l-2 border-brand-primary' : 'text-ink-muted hover:text-ink hover:bg-canvas border-l-2 border-transparent', 'flex items-center gap-3 px-6 py-3 font-medium transition-colors duration-200']">
            <span class="material-symbols-outlined">settings</span>
            <span class="text-sm">Configurações</span>
          </router-link>
        </nav>
      </div>
      <div class="px-4 mt-auto space-y-4">
        <router-link to="/admin" @click="isSidebarOpen = false"
          :class="[route.path === '/admin' ? 'text-brand-primary bg-canvas font-semibold' : 'text-ink-muted hover:text-ink hover:bg-canvas', 'flex items-center gap-3 px-4 py-3 rounded-md transition-colors duration-200']">
          <span class="material-symbols-outlined">sync</span>
          <span class="text-sm">Sincronizar SINAPI</span>
        </router-link>
        <div
          @click="isSidebarOpen = false"
          class="w-full flex items-center justify-center gap-2 bg-canvas border border-hairline text-ink-muted font-medium py-3 px-4 rounded-md opacity-50 cursor-not-allowed"
          title="Funcionalidade em desenvolvimento">
          <span class="material-symbols-outlined text-[18px]">add_circle</span>
          <span class="text-sm">Novo Dossiê Caixa</span>
        </div>
        <div @click="isSidebarOpen = false" class="flex items-center gap-3 text-ink-muted opacity-50 cursor-not-allowed px-4 py-3"
          title="Funcionalidade em desenvolvimento">
          <span class="material-symbols-outlined">help</span>
          <span class="text-sm">Ajuda</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useSidebar } from '../composables/useSidebar'

const route = useRoute()
const { isSidebarOpen, toggleSidebar } = useSidebar()
</script>
