<script setup>
import { formatCurrency } from '../utils/formatters'
import { Plus, ChevronsLeft, ChevronLeft, ChevronRight, ChevronsRight, Loader2 } from 'lucide-vue-next'

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
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const goToPage = (e) => {
  const page = Math.max(1, Math.min(props.totalPages, Number(e.target.value)))
  if (page !== props.currentPage) emit('change-page', page)
}

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

    <!-- Overlay de loading (compartilhado entre os dois layouts) -->
    <div class="relative">
      <Transition
        enter-active-class="transition-opacity duration-150"
        leave-active-class="transition-opacity duration-150"
        enter-from-class="opacity-0" leave-to-class="opacity-0"
      >
        <div v-if="isLoading" class="absolute inset-0 bg-canvas/70 backdrop-blur-[1px] flex items-center justify-center z-10 min-h-[200px]">
          <Loader2 class="w-6 h-6 text-brand-blue animate-spin" stroke-width="1.5" />
        </div>
      </Transition>

      <!-- ── Cards (mobile / tablet portrait < md) ──────────────────────── -->
      <div class="md:hidden divide-y divide-hairline">
        <div v-if="items.length === 0 && !isLoading" class="px-4 py-10 text-center text-ink-muted text-sm">
          Nenhum item encontrado.
        </div>
        <div
          v-for="item in items"
          :key="item.id"
          class="flex items-center gap-3 px-4 py-3 active:bg-surface-hover transition-colors"
        >
          <!-- Botão + grande para touch -->
          <button
            @click="emit('add-item', item)"
            class="shrink-0 w-11 h-11 rounded-xl bg-brand-blue/10 text-brand-blue flex items-center justify-center active:bg-brand-blue active:text-white transition-colors cursor-pointer"
          >
            <Plus class="w-5 h-5" stroke-width="2" />
          </button>

          <!-- Info do item -->
          <div class="flex-1 min-w-0">
            <p class="text-[10px] font-mono text-ink-muted leading-none mb-0.5">{{ item.codigo_item }}</p>
            <p class="text-sm font-semibold text-ink leading-snug line-clamp-2">{{ item.descricao }}</p>
            <div class="flex items-center gap-2 mt-1">
              <span class="text-[11px] text-ink-muted bg-canvas border border-hairline px-1.5 py-0.5 rounded font-medium">{{ item.unidade }}</span>
              <span class="text-[11px] font-bold text-ink">{{ formatCurrency(item.preco) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Tabela (desktop md+) ───────────────────────────────────────── -->
      <div class="hidden md:block overflow-x-auto">
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
            <tr v-if="items.length === 0 && !isLoading">
              <td colspan="5" class="px-6 py-8 text-center text-ink-muted text-sm">Nenhum item encontrado.</td>
            </tr>
            <tr v-for="item in items" :key="item.id" class="hover:bg-surface-hover transition-colors">
              <td class="px-6 py-4">
                <button
                  @click="emit('add-item', item)"
                  title="Adicionar ao Orçamento"
                  class="flex items-center justify-center w-8 h-8 rounded-md text-ink-muted hover:text-brand-blue hover:bg-brand-blue/10 transition-colors cursor-pointer"
                >
                  <Plus class="w-[18px] h-[18px]" stroke-width="1.5" />
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
    </div>

    <!-- Footer com Paginação -->
    <div class="bg-canvas px-4 sm:px-6 py-3 sm:py-4 flex flex-col sm:flex-row items-center justify-between border-t border-hairline gap-3">

      <!-- Contador + itens por página -->
      <div class="flex items-center gap-2 sm:gap-3 w-full sm:w-auto justify-between sm:justify-start">
        <span class="text-xs sm:text-sm text-ink-muted">
          <span class="font-semibold text-ink">{{ items.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0 }}</span>–<span class="font-semibold text-ink">{{ MathMin(currentPage * itemsPerPage, totalItems) }}</span>
          <span class="text-ink-muted"> / </span>
          <span class="font-semibold text-ink">{{ totalItems }}</span>
          <span class="hidden sm:inline text-ink-muted"> itens</span>
        </span>
        <select @change="onLimitChange" :value="itemsPerPage" class="text-xs sm:text-sm border border-hairline rounded-md bg-surface px-2 py-1 outline-none focus:ring-1 focus:ring-brand-primary text-ink-muted cursor-pointer transition-colors">
          <option v-for="opt in limitOptions" :key="opt" :value="opt" class="dark:bg-zinc-900">{{ opt }} por pág.</option>
        </select>
      </div>

      <!-- Navegação de páginas -->
      <div class="flex items-center gap-1.5 sm:gap-2">
        <button @click="firstPage" :disabled="currentPage === 1" class="hidden sm:flex px-2 py-1.5 border border-hairline rounded-md hover:bg-surface transition-all text-ink-muted disabled:opacity-50 disabled:cursor-not-allowed items-center justify-center" title="Primeira Página">
          <ChevronsLeft class="w-4 h-4 sm:w-5 sm:h-5" stroke-width="1.5" />
        </button>
        <button @click="prevPage" :disabled="currentPage === 1" class="px-2 py-1.5 border border-hairline rounded-md hover:bg-surface transition-all text-ink-muted disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center" title="Página Anterior">
          <ChevronLeft class="w-4 h-4 sm:w-5 sm:h-5" stroke-width="1.5" />
        </button>

        <div class="flex items-center gap-1 px-1">
          <input
            type="number"
            :min="1"
            :max="totalPages"
            :value="currentPage"
            :disabled="totalPages <= 1"
            @change="goToPage"
            class="w-10 sm:w-12 text-center text-xs sm:text-sm font-bold text-ink border border-hairline rounded-md bg-surface px-1 py-1 outline-none focus:ring-1 focus:ring-brand-primary disabled:opacity-40 disabled:cursor-not-allowed"
          />
          <span class="text-xs text-ink-muted">/{{ totalPages }}</span>
        </div>

        <button @click="nextPage" :disabled="currentPage === totalPages || totalPages === 0" class="px-2 py-1.5 border border-hairline rounded-md hover:bg-surface transition-all text-ink-muted disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center" title="Próxima Página">
          <ChevronRight class="w-4 h-4 sm:w-5 sm:h-5" stroke-width="1.5" />
        </button>
        <button @click="lastPage" :disabled="currentPage === totalPages || totalPages === 0" class="hidden sm:flex px-2 py-1.5 border border-hairline rounded-md hover:bg-surface transition-all text-ink-muted disabled:opacity-50 disabled:cursor-not-allowed items-center justify-center" title="Última Página">
          <ChevronsRight class="w-4 h-4 sm:w-5 sm:h-5" stroke-width="1.5" />
        </button>
      </div>
    </div>
  </div>
</template>
