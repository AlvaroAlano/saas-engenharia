<script setup>
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'

const route = useRoute()

const tabs = [
  { id: 'geral', label: 'Geral', path: '/configuracoes/geral', icon: 'settings' },
  { id: 'empresa', label: 'Minha Empresa', path: '/configuracoes/empresa', icon: 'domain' },
  { id: 'contratos', label: 'Motor de Contratos', path: '/configuracoes/contratos', icon: 'contract' }
]
</script>

<template>
  <div class="flex h-screen bg-canvas font-sans text-ink overflow-hidden">
    <Sidebar />

    <main class="flex-1 flex flex-col min-w-0 overflow-hidden lg:pl-64 transition-all duration-300">
      <TopHeader />

      <div class="flex-1 overflow-y-auto">
        <div class="max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8">
          
          <div class="mb-8">
            <h1 class="text-2xl font-bold text-ink tracking-tight">Configurações</h1>
            <p class="text-sm text-ink-muted mt-1">Gerencie as preferências e modelos da sua construtora.</p>
          </div>

          <!-- Tabs Navigation -->
          <div class="border-b border-hairline mb-8">
            <nav class="flex overflow-x-auto gap-8">
              <router-link 
                v-for="tab in tabs" 
                :key="tab.id"
                :to="tab.path"
                class="flex items-center gap-2 pb-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap"
                :class="route.path === tab.path ? 'border-brand-primary text-brand-primary' : 'border-transparent text-ink-muted hover:text-ink hover:border-hairline'"
              >
                <span class="material-symbols-outlined text-[18px]">{{ tab.icon }}</span>
                {{ tab.label }}
              </router-link>
            </nav>
          </div>

          <!-- Render Child Routes Here -->
          <div class="h-full">
            <router-view></router-view>
          </div>

        </div>
      </div>
    </main>
  </div>
</template>
