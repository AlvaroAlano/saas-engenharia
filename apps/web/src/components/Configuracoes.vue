<script setup>
import { ref, computed, markRaw } from 'vue'
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'
import TabPerfil from './settings/TabPerfil.vue'
import TabEmpresa from './settings/TabEmpresa.vue'
import TabPreferencias from './settings/TabPreferencias.vue'
import TabVitrine from './settings/TabVitrine.vue'
import TabParametrosEAP from './settings/TabParametrosEAP.vue'
import ConfiguracoesContratos from './ConfiguracoesContratos.vue'

const tabs = [
  { id: 'perfil',        label: 'Perfil',             icon: 'person',       component: markRaw(TabPerfil) },
  { id: 'empresa',       label: 'Empresa',             icon: 'domain',       component: markRaw(TabEmpresa) },
  { id: 'preferencias',  label: 'Preferências',        icon: 'tune',         component: markRaw(TabPreferencias) },
  { id: 'vitrine',       label: 'Vitrine',             icon: 'storefront',   component: markRaw(TabVitrine) },
  { id: 'parametros_eap', label: 'Parâmetros EAP',    icon: 'account_tree', component: markRaw(TabParametrosEAP) },
  { id: 'contratos',     label: 'Motor de Contratos',  icon: 'contract',     component: markRaw(ConfiguracoesContratos) },
]

const activeTabId = ref('perfil')
const currentTab = computed(() => tabs.find(t => t.id === activeTabId.value))
</script>

<template>
  <div class="flex h-screen bg-canvas font-sans text-ink overflow-hidden">
    <Sidebar />

    <main class="flex-1 flex flex-col min-w-0 overflow-hidden lg:pl-64 transition-all duration-300">
      <TopHeader />

      <!-- Tab Nav — shrink-0 garante que nunca comprime; fica sempre visível -->
      <div class="bg-canvas border-b border-hairline shrink-0">
        <nav class="flex overflow-x-auto scrollbar-none max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTabId = tab.id"
            class="flex items-center gap-2 py-3.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap mr-7 last:mr-0 focus:outline-none"
            :class="activeTabId === tab.id
              ? 'border-brand-primary text-ink'
              : 'border-transparent text-ink-muted hover:text-ink'"
          >
            <span class="material-symbols-outlined text-[17px]">{{ tab.icon }}</span>
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Aba Motor de Contratos: precisa de height explícita (editor flex-fill) -->
      <div v-if="activeTabId === 'contratos'" class="flex-1 flex flex-col min-h-0">
        <ConfiguracoesContratos />
      </div>

      <!-- Demais abas: scrollável, centrado, padrão cards -->
      <div v-else class="flex-1 overflow-y-auto">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <component :is="currentTab.component" />
        </div>
      </div>

    </main>
  </div>
</template>
