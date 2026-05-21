<script setup>
import { computed } from 'vue'
import { formatCurrency } from '../utils/formatters'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  currentPage: {
    type: Number,
    default: 1
  },
  totalPages: {
    type: Number,
    default: 1
  },
  totalItems: {
    type: Number,
    default: 0
  },
  itemsPerPage: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['add-item', 'change-page', 'change-limit'])

const limitOptions = [10, 20, 50, 100]

const firstPage = () => {
  if (props.currentPage > 1) {
    emit('change-page', 1)
  }
}

const prevPage = () => {
  if (props.currentPage > 1) {
    emit('change-page', props.currentPage - 1)
  }
}

const MathMin = Math.min

const nextPage = () => {
  if (props.currentPage < props.totalPages) {
    emit('change-page', props.currentPage + 1)
  }
}

const lastPage = () => {
  if (props.currentPage < props.totalPages) {
    emit('change-page', props.totalPages)
  }
}

const onLimitChange = (e) => {
  emit('change-limit', parseInt(e.target.value))
}
</script>

<template>
  <div class="bg-surface rounded-xl border border-hairline overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-canvas border-b border-hairline">
            <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider w-16">Ações</th>
            <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider">Código SINAPI</th>
            <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider">Descrição do Item</th>
            <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider">Unid.</th>
            <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider text-right">Unitário (R$)</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-hairline">
          <tr v-if="items.length === 0">
            <td colspan="5" class="px-6 py-8 text-center text-ink-muted text-sm">Nenhum item encontrado.</td>
          </tr>
          <tr v-for="item in items" :key="item.id" class="hover:bg-surface-hover transition-colors">
            <td class="px-6 py-4">
              <button @click="emit('add-item', item)" class="flex items-center justify-center w-8 h-8 rounded-md bg-brand-primary/10 text-brand-primary hover:bg-brand-primary hover:text-white transition-colors" title="Adicionar ao Orçamento">
                <span class="material-symbols-outlined text-[18px]">add</span>
              </button>
            </td>
            <td class="px-6 py-4 font-mono text-sm text-ink-muted">{{ item.codigo_item }}</td>
            <td class="px-6 py-4 font-medium text-ink text-sm">{{ item.descricao }}</td>
            <td class="px-6 py-4 text-ink-muted text-sm">{{ item.unidade }}</td>
            <td class="px-6 py-4 text-right text-ink-muted text-sm">{{ formatCurrency(item.preco) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Footer com Paginação e Itens por Página -->
    <div class="bg-canvas px-6 py-4 flex flex-col sm:flex-row items-center justify-between border-t border-hairline gap-4">
      <div class="flex items-center gap-3">
        <span class="text-sm text-ink-muted">
          Mostrando <span class="font-semibold text-ink">{{ items.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0 }}</span>
          até <span class="font-semibold text-ink">{{ MathMin(currentPage * itemsPerPage, totalItems) }}</span>
          de <span class="font-semibold text-ink">{{ totalItems }}</span> itens
        </span>
        <select @change="onLimitChange" :value="itemsPerPage" class="text-sm border border-hairline rounded-md bg-surface px-2 py-1 outline-none focus:ring-1 focus:ring-brand-primary text-ink-muted cursor-pointer transition-colors">
          <option v-for="opt in limitOptions" :key="opt" :value="opt" class="dark:bg-zinc-900">{{ opt }} por pág.</option>
        </select>
      </div>
      
      <div class="flex items-center gap-2">
        <button @click="firstPage" :disabled="currentPage === 1" class="px-2 py-1.5 border border-hairline rounded-md hover:bg-surface transition-all text-ink-muted disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center" title="Primeira Página">
          <span class="material-symbols-outlined text-[20px]">first_page</span>
        </button>
        <button @click="prevPage" :disabled="currentPage === 1" class="px-2 py-1.5 border border-hairline rounded-md hover:bg-surface transition-all text-ink-muted disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center" title="Página Anterior">
          <span class="material-symbols-outlined text-[20px]">chevron_left</span>
        </button>
        
        <span class="text-sm text-ink-muted font-medium px-2">
          Pág <span class="font-bold text-ink">{{ currentPage }}</span> de <span class="font-bold text-ink">{{ totalPages }}</span>
        </span>
        
        <button @click="nextPage" :disabled="currentPage === totalPages || totalPages === 0" class="px-2 py-1.5 border border-hairline rounded-md hover:bg-surface transition-all text-ink-muted disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center" title="Próxima Página">
          <span class="material-symbols-outlined text-[20px]">chevron_right</span>
        </button>
        <button @click="lastPage" :disabled="currentPage === totalPages || totalPages === 0" class="px-2 py-1.5 border border-hairline rounded-md hover:bg-surface transition-all text-ink-muted disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center" title="Última Página">
          <span class="material-symbols-outlined text-[20px]">last_page</span>
        </button>
      </div>
    </div>
  </div>
</template>
