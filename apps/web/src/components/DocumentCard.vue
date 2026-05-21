<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  status: {
    type: String,
    validator(value) {
      return ['pending', 'verifying', 'approved', 'rejected'].includes(value)
    }
  },
  icon: String,
  message: String,
  fileName: String,
  actionText: String,
  actionIcon: String
})

const statusConfig = computed(() => {
  switch (props.status) {
    case 'pending':
      return {
        label: 'Pendente',
        badgeClass: 'bg-canvas text-ink-muted border border-transparent',
        badgeIcon: '',
        cardClass: 'border-hairline'
      }
    case 'verifying':
      return {
        label: 'Em Verificação',
        badgeClass: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-100 dark:border-amber-500/30',
        badgeIcon: 'schedule',
        cardClass: 'border-hairline'
      }
    case 'approved':
      return {
        label: 'Aprovado',
        badgeClass: 'bg-green-50 dark:bg-emerald-500/10 text-green-700 dark:text-emerald-400 border border-green-100 dark:border-emerald-500/30',
        badgeIcon: 'check_circle',
        cardClass: 'border-hairline'
      }
    case 'rejected':
      return {
        label: 'Rejeitado',
        badgeClass: 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/30',
        badgeIcon: 'error',
        cardClass: 'border-red-500/50 dark:border-red-500/50'
      }
    default:
      return {}
  }
})
</script>

<template>
  <div :class="['bg-surface rounded-lg p-5 flex flex-col gap-4 border transition-colors', statusConfig.cardClass]">
    <div class="flex justify-between items-start">
      <div class="flex-1">
        <h3 class="text-xl font-bold text-ink mb-1">{{ title }}</h3>
        <div :class="['inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] uppercase tracking-wider font-semibold', statusConfig.badgeClass]">
          <span v-if="statusConfig.badgeIcon" class="material-symbols-outlined text-[14px]" :style="status === 'approved' ? 'font-variation-settings: \'FILL\' 1;' : ''">
            {{ statusConfig.badgeIcon }}
          </span>
          {{ statusConfig.label }}
        </div>
      </div>
      <span class="material-symbols-outlined text-ink-muted">{{ icon }}</span>
    </div>

    <!-- Content variations based on status -->
    <template v-if="status === 'pending'">
      <button class="w-full bg-brand-primary hover:bg-brand-hover text-white font-semibold text-xs uppercase tracking-wider py-3 rounded-md active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer">
        <span v-if="actionIcon" class="material-symbols-outlined text-lg">{{ actionIcon }}</span>
        {{ actionText }}
      </button>
    </template>

    <template v-else-if="status === 'verifying'">
      <p class="text-sm text-ink-muted italic">{{ message }}</p>
    </template>

    <template v-else-if="status === 'approved'">
      <div class="flex items-center gap-2 p-3 bg-green-50/30 dark:bg-emerald-500/5 rounded-md border border-green-100/50 dark:border-emerald-500/20">
        <span class="material-symbols-outlined text-green-600 dark:text-emerald-400 text-sm">attachment</span>
        <span class="font-mono text-green-700 dark:text-emerald-400 text-xs">{{ fileName }}</span>
      </div>
    </template>

    <template v-else-if="status === 'rejected'">
      <div class="p-3 bg-red-50 dark:bg-red-500/10 rounded-md text-red-600 dark:text-red-400 text-sm border-l-2 border-red-500 font-medium">
        {{ message }}
      </div>
      <button class="w-full bg-surface border border-hairline text-ink font-semibold text-xs uppercase tracking-wider py-3 rounded-md hover:bg-canvas active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer">
        <span v-if="actionIcon" class="material-symbols-outlined text-lg">{{ actionIcon }}</span>
        {{ actionText }}
      </button>
    </template>
  </div>
</template>
