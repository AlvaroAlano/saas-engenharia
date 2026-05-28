<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 antialiased transition-colors">
    <!-- Sidebar persistente de nível superior em rotas autenticadas -->
    <Sidebar v-if="route.matched.some(r => r.meta.requiresAuth)" />

    <router-view v-slot="{ Component, route }">
      <!-- Rotas autenticadas têm sidebar: sem transição de página para ela não "voar" -->
      <!-- Rotas públicas (landing, auth, portal) mantêm o fade rápido -->
      <transition
        :name="route.matched.some(r => r.meta.requiresAuth) ? '' : 'page'"
        mode="out-in"
      >
        <component :is="Component" />
      </transition>
    </router-view>
    <GlobalToast />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import GlobalToast from './components/GlobalToast.vue'
import { initTheme } from './composables/useTheme'

const route = useRoute()

onMounted(() => {
  initTheme()
})
</script>

