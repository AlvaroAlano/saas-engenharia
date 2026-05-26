<script setup>
import { ref, watch } from 'vue'
import { Network, AlertTriangle, Trash2, ListPlus } from 'lucide-vue-next'

const props = defineProps({
  isOpen:         { type: Boolean, required: true },
  cartItemsCount: { type: Number,  default: 0 },
})

const emit = defineEmits(['confirmar', 'cancelar'])

const modo = ref('mesclar')

watch(() => props.isOpen, (val) => {
  if (val) modo.value = 'mesclar'
})
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-sm"
    style="z-index: 140;"
  >
    <div class="bg-surface border border-hairline w-full max-w-sm overflow-hidden animate-in zoom-in duration-200 shadow-lg rounded-2xl">

      <!-- Header -->
      <div class="px-6 py-3 flex flex-col items-center text-center">
        <div class="w-12 h-12 rounded-2xl bg-brand-primary/10 flex items-center justify-center mb-4">
          <Network class="w-7 h-7 text-brand-primary" stroke-width="1.5" />
        </div>
        <h3 class="text-base font-extrabold text-ink">Como deseja importar?</h3>
        <p class="text-sm text-ink-muted mt-1.5 leading-snug">
          A árvore já possui <span class="font-bold text-ink">{{ cartItemsCount }} {{ cartItemsCount === 1 ? 'item' : 'itens' }}</span>.
          Escolha o que fazer com eles.
        </p>
      </div>

      <!-- Opções -->
      <div class="px-6 pb-4 space-y-2.5">
        <!-- Mesclar -->
        <div
          class="flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors"
          :class="modo === 'mesclar' ? 'border-brand-primary bg-brand-primary/5' : 'border-hairline bg-canvas hover:border-brand-primary/40'"
          @click="modo = 'mesclar'"
        >
          <div class="mt-0.5 shrink-0 w-4 h-4 rounded-full border-2 flex items-center justify-center transition-colors"
               :class="modo === 'mesclar' ? 'border-brand-primary' : 'border-ink-muted'">
            <div v-if="modo === 'mesclar'" class="w-2 h-2 rounded-full bg-brand-primary"></div>
          </div>
          <div>
            <p class="text-sm font-bold text-ink">Adicionar apenas os que faltam</p>
            <p class="text-xs text-ink-muted mt-0.5 leading-snug">Mantém os itens existentes e insere apenas os códigos do template que ainda não estão na árvore.</p>
          </div>
        </div>

        <!-- Substituir -->
        <div
          class="flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors"
          :class="modo === 'substituir' ? 'border-red-500 bg-red-50 dark:bg-red-500/10' : 'border-hairline bg-canvas hover:border-red-300'"
          @click="modo = 'substituir'"
        >
          <div class="mt-0.5 shrink-0 w-4 h-4 rounded-full border-2 flex items-center justify-center transition-colors"
               :class="modo === 'substituir' ? 'border-red-500' : 'border-ink-muted'">
            <div v-if="modo === 'substituir'" class="w-2 h-2 rounded-full bg-red-500"></div>
          </div>
          <div>
            <p class="text-sm font-bold text-ink">Substituir tudo</p>
            <p class="text-xs text-ink-muted mt-0.5 leading-snug">Remove todos os itens atuais da árvore e insere o template do zero. Esta ação não pode ser desfeita.</p>
          </div>
        </div>
      </div>

      <!-- Aviso substituição -->
      <transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
        <div v-if="modo === 'substituir'" class="mx-6 mb-4 flex items-start gap-2 p-3 bg-red-50 dark:bg-red-500/10 rounded-xl border border-red-200 dark:border-red-500/30">
          <AlertTriangle class="w-4 h-4 text-red-500 shrink-0 mt-0.5" stroke-width="1.5" />
          <p class="text-xs text-red-700 dark:text-red-400 leading-snug font-medium">
            Os {{ cartItemsCount }} itens existentes e suas quantidades serão apagados permanentemente.
          </p>
        </div>
      </transition>

      <!-- Botões -->
      <div class="flex gap-3 px-6 pb-6">
        <button
          type="button"
          @click="emit('cancelar')"
          class="flex-1 py-2.5 border border-hairline rounded-xl text-sm font-semibold text-ink-muted hover:bg-canvas transition-colors cursor-pointer"
        >
          Cancelar
        </button>
        <button
          type="button"
          @click="emit('confirmar', modo)"
          class="flex-[1.5] py-2.5 rounded-xl font-bold text-sm transition-colors cursor-pointer flex items-center justify-center gap-1.5 text-white"
          :class="modo === 'substituir' ? 'bg-red-500 hover:bg-red-600' : 'bg-brand-primary hover:bg-brand-hover'"
        >
          <Trash2 v-if="modo === 'substituir'" class="w-4 h-4" stroke-width="1.5" />
          <ListPlus v-else class="w-4 h-4" stroke-width="1.5" />
          {{ modo === 'substituir' ? 'Substituir tudo' : 'Adicionar os que faltam' }}
        </button>
      </div>
    </div>
  </div>
</template>
