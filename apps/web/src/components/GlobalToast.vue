<template>
  <Transition name="slide-in-right">
    <div 
      v-if="toastVisible" 
      @mouseenter="pauseTimer"
      @mouseleave="resumeTimer"
      class="fixed top-6 right-6 px-6 py-4 rounded-xl flex items-center justify-between gap-4 z-[9999] border max-w-sm w-full transition-colors shadow-lg"
      :class="[
        toastType === 'error' ? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400' : 
        toastType === 'warning' ? 'bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/30 text-amber-700 dark:text-amber-400' : 
        toastType === 'info' ? 'bg-canvas border-hairline text-ink' : 
        'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
      ]"
    >
      <div class="flex items-center gap-3">
        <span class="material-symbols-outlined shrink-0" :class="toastType === 'error' ? 'text-red-500' : toastType === 'warning' ? 'text-amber-500' : toastType === 'info' ? 'text-brand-primary' : 'text-emerald-600 dark:text-emerald-400'">
          {{ 
            toastType === 'error' ? 'error' : 
            toastType === 'warning' ? 'warning' : 
            toastType === 'info' ? 'info' : 
            'check_circle' 
          }}
        </span>
        <span class="font-semibold text-sm leading-snug">{{ toastMessage }}</span>
      </div>
      <button @click="toastVisible = false" class="shrink-0 rounded-md p-1 transition-colors hover:bg-surface-hover opacity-70 hover:opacity-100 flex items-center justify-center">
        <span class="material-symbols-outlined text-[18px]">close</span>
      </button>
    </div>
  </Transition>
</template>

<script setup>
import { useToast } from '../composables/useToast'

const { toastVisible, toastMessage, toastType, pauseTimer, resumeTimer } = useToast()
</script>

<style scoped>
.slide-in-right-enter-active,
.slide-in-right-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-in-right-enter-from {
  opacity: 0;
  transform: translateX(50px);
}

.slide-in-right-leave-to {
  opacity: 0;
  transform: translateX(50px);
}
</style>
