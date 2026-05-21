<script setup>
defineProps({
  badgeText: {
    type: String,
    required: true
  },
  badgeClass: {
    type: String,
    default: 'bg-canvas text-ink-muted'
  },
  title: {
    type: String,
    required: true
  },
  clientName: {
    type: String,
    required: true
  }
})
</script>

<template>
  <div class="bg-surface border border-hairline p-4 hover:border-brand-primary transition-colors cursor-pointer rounded-lg">
    <div class="flex justify-between items-start mb-3">
      <span :class="['text-[10px] font-bold px-2 py-0.5 rounded', badgeClass]">
        {{ badgeText }}
      </span>
      <span class="material-symbols-outlined text-ink-muted text-sm">more_horiz</span>
    </div>
    <h4 class="text-sm font-semibold text-ink mb-1">{{ title }}</h4>
    <p class="text-xs text-ink-muted mb-4">{{ clientName }}</p>
    <div class="flex items-center justify-between pt-3 border-t border-hairline">
      <slot name="footer"></slot>
    </div>
  </div>
</template>
