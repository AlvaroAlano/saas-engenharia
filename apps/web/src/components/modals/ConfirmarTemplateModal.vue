<script setup>
import { ref, watch } from 'vue'
import { Network, AlertTriangle, Trash2, ListPlus } from 'lucide-vue-next'
import BaseModal from './BaseModal.vue'

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
  <BaseModal :isOpen="isOpen" @close="emit('cancelar')" maxWidthClass="max-w-md" zIndexClass="z-[140]">
    <template #header>
      <div class="flex items-center gap-2">
        <Network class="w-5 h-5 text-blue-600" stroke-width="1.5" />
        <h3 class="text-lg font-medium text-ink">Importar Template</h3>
      </div>
    </template>

    <div class="space-y-4">
      <p class="text-sm text-ink-muted leading-snug">
        A árvore de orçamento já possui <span class="font-semibold text-ink">{{ cartItemsCount }} {{ cartItemsCount === 1 ? 'item' : 'itens' }}</span>.
        Escolha como deseja prosseguir com a importação do template:
      </p>

      <!-- Opções -->
      <div class="space-y-2.5">
        <!-- Mesclar -->
        <div
          class="flex items-start gap-3 p-4 rounded-md border cursor-pointer transition-all"
          :class="modo === 'mesclar' ? 'border-blue-500 bg-blue-500/[0.04]' : 'border-hairline bg-transparent hover:bg-surface-hover'"
          @click="modo = 'mesclar'"
        >
          <div class="mt-0.5 shrink-0 w-4 h-4 rounded-full border flex items-center justify-center transition-colors"
               :class="modo === 'mesclar' ? 'border-blue-500' : 'border-neutral-400'">
            <div v-if="modo === 'mesclar'" class="w-2 h-2 rounded-full bg-blue-600"></div>
          </div>
          <div>
            <p class="text-sm font-semibold text-ink">Adicionar apenas os que faltam (Recomendado)</p>
            <p class="text-xs text-ink-muted mt-0.5 leading-relaxed">Mantém os itens existentes e insere apenas os serviços do template que ainda não estão no seu orçamento.</p>
          </div>
        </div>

        <!-- Substituir -->
        <div
          class="flex items-start gap-3 p-4 rounded-md border cursor-pointer transition-all"
          :class="modo === 'substituir' ? 'border-red-500 bg-red-500/[0.04]' : 'border-hairline bg-transparent hover:bg-surface-hover'"
          @click="modo = 'substituir'"
        >
          <div class="mt-0.5 shrink-0 w-4 h-4 rounded-full border flex items-center justify-center transition-colors"
               :class="modo === 'substituir' ? 'border-red-500' : 'border-neutral-400'">
            <div v-if="modo === 'substituir'" class="w-2 h-2 rounded-full bg-red-600"></div>
          </div>
          <div>
            <p class="text-sm font-semibold text-ink">Substituir tudo (Limpar orçamento)</p>
            <p class="text-xs text-ink-muted mt-0.5 leading-relaxed">Remove todos os itens atuais e insere o template do zero. <strong>Esta ação não pode ser desfeita.</strong></p>
          </div>
        </div>
      </div>

      <!-- Aviso substituição -->
      <transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
        <div v-if="modo === 'substituir'" class="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-500/10 rounded-md border border-red-100 dark:border-red-500/20">
          <AlertTriangle class="w-4 h-4 text-red-500 shrink-0 mt-0.5" stroke-width="1.5" />
          <p class="text-xs text-red-700 dark:text-red-400 leading-snug font-medium">
            Atenção: Os {{ cartItemsCount }} itens existentes e suas quantidades editadas serão perdidos permanentemente.
          </p>
        </div>
      </transition>
    </div>

    <template #footer>
      <button
        type="button"
        @click="emit('cancelar')"
        class="h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink bg-transparent hover:bg-surface-hover rounded-md transition-colors cursor-pointer flex items-center justify-center"
      >
        Cancelar
      </button>
      <button
        type="button"
        @click="emit('confirmar', modo)"
        class="h-9 px-4 text-sm font-medium text-white rounded-md transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-sm"
        :class="modo === 'substituir' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'"
      >
        <Trash2 v-if="modo === 'substituir'" class="w-4 h-4" stroke-width="1.5" />
        <ListPlus v-else class="w-4 h-4" stroke-width="1.5" />
        {{ modo === 'substituir' ? 'Substituir Tudo' : 'Confirmar Importação' }}
      </button>
    </template>
  </BaseModal>
</template>

