<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (val) => ['primary', 'secondary', 'ghost', 'danger'].includes(val)
  },
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md', 'lg', 'icon'].includes(val)
  },
  disabled: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'button'
  }
})

const variantClasses = {
  primary: 'bg-brand-primary text-white dark:text-black hover:opacity-90 border border-transparent shadow-sm',
  secondary: 'bg-transparent border border-hairline text-ink hover:bg-surface-hover shadow-sm',
  ghost: 'bg-transparent border border-transparent text-ink-muted hover:text-ink hover:bg-surface-hover',
  danger: 'bg-red-500/10 text-red-600 border border-red-500/20 hover:bg-red-500/20 dark:text-red-400'
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
  icon: 'p-2'
}

const buttonClasses = computed(() => {
  return [
    'inline-flex items-center justify-center font-medium transition-colors rounded-md focus:outline-none select-none',
    props.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
    variantClasses[props.variant] || variantClasses.primary,
    sizeClasses[props.size] || sizeClasses.md
  ]
})
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    :class="buttonClasses"
  >
    <slot></slot>
  </button>
</template>
