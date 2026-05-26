<script setup>
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'

const route = useRoute()
</script>

<template>
  <div class="flex h-screen bg-canvas font-sans text-ink overflow-hidden">
    <Sidebar />

    <main class="flex-1 flex flex-col min-w-0 overflow-hidden lg:pl-64 transition-all duration-300">
      <TopHeader />

      <!-- Motor de Contratos: precisa de height explícita para o editor flex-fill -->
      <div v-if="route.path.endsWith('/contratos')" class="flex-1 flex flex-col min-h-0">
        <router-view />
      </div>

      <!-- Demais seções: scrollável, centrado, padrão cards -->
      <div v-else class="flex-1 overflow-y-auto">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <router-view />
        </div>
      </div>
    </main>
  </div>
</template>
