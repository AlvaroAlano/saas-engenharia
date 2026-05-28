<script setup>
import { X } from 'lucide-vue-next'
import BaseButton from '../ui/BaseButton.vue'

defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  title: {
    type: String,
    default: ''
  },
  maxWidthClass: {
    type: String,
    default: 'max-w-md' // ex: max-w-sm, max-w-md, max-w-lg, max-w-xl, max-w-2xl, max-w-6xl
  },
  zIndexClass: {
    type: String,
    default: 'z-[100]'
  }
})

const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div 
      v-if="isOpen" 
      :class="[
        'fixed inset-0 flex items-center justify-center bg-black/45 dark:bg-black/65 backdrop-blur-sm p-4',
        zIndexClass
      ]"
      @click.self="emit('close')"
    >
      <div 
        :class="[
          'bg-surface rounded-md w-full overflow-hidden border border-hairline shadow-2xl transition-all',
          maxWidthClass
        ]"
      >
        <!-- Header -->
        <div class="px-6 py-4 border-b border-hairline flex items-center justify-between bg-surface shrink-0">
          <slot name="header">
            <h3 class="text-lg font-medium text-ink">{{ title }}</h3>
          </slot>
          <BaseButton 
            variant="ghost"
            size="icon"
            @click="emit('close')"
          >
            <X class="w-4 h-4" stroke-width="1.25" />
          </BaseButton>
        </div>

        <!-- Body -->
        <div class="p-6 overflow-y-auto max-h-[calc(85vh-110px)]">
          <slot></slot>
        </div>

        <!-- Footer -->
        <div v-if="$slots.footer" class="px-6 py-4 bg-canvas border-t border-hairline flex items-center justify-end gap-2 shrink-0">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>
