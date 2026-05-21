<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 antialiased transition-colors">
    <router-view v-slot="{ Component }">
      <transition name="fade-slide" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <GlobalToast />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import GlobalToast from './components/GlobalToast.vue'
import { initTheme } from './composables/useTheme'

onMounted(() => {
  initTheme()
})
</script>

<style>
/* Transições globais de página */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.3s ease-out, transform 0.3s ease-out;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(15px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-15px);
}
</style>
