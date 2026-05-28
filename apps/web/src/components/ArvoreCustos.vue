<script setup>
import { computed, ref, nextTick } from 'vue'
import { formatCurrency } from '../utils/formatters'
import { ETAPAS_OBRA } from '../constants/etapas'
import { 
  Network, 
  Loader2, 
  Sparkles, 
  Plus, 
  Maximize2, 
  Package, 
  Download, 
  ChevronDown, 
  ListPlus, 
  AlertTriangle, 
  X,
  HardHat,
  Layers,
  Building,
  Zap,
  Paintbrush
} from 'lucide-vue-next'

const iconMap = {
  engineering: HardHat,
  foundation: Layers,
  domain: Building,
  electric_bolt: Zap,
  format_paint: Paintbrush
}

const props = defineProps({
  items:               { type: Array,   default: () => [] },
  bdi:                 { type: Number,  default: 0 },
  isApplyingTemplate:  { type: Boolean, default: false },
})

const emit = defineEmits(['remove-item', 'update-quantity', 'add-manual-item', 'import-template', 'aplicar-template-padrao', 'expandir'])

const etapas = ETAPAS_OBRA

const expandedEtapas = ref(new Set())

const toggleEtapa = (etapa) => {
  if (expandedEtapas.value.has(etapa)) {
    expandedEtapas.value.delete(etapa)
  } else {
    expandedEtapas.value.add(etapa)
  }
}

const itensPorEtapa = computed(() => {
  const grouped = {}
  for (const etapa of etapas) {
    grouped[etapa.value] = props.items.filter(i => i.etapa_obra === etapa.value)
  }
  return grouped
})

const subtotalEtapa = (etapaKey) => {
  return itensPorEtapa.value[etapaKey].reduce((sum, item) => {
    return sum + (item.quantidade * item.valor_unitario)
  }, 0)
}

const totalGeral = computed(() => {
  return props.items.reduce((sum, item) => {
    return sum + (item.quantidade * item.valor_unitario)
  }, 0)
})

const totalComBdi = computed(() => {
  return totalGeral.value * (1 + (props.bdi / 100))
})

const colorClasses = {
  amber: { bg: 'bg-amber-50 dark:bg-amber-500/10', border: 'border-amber-200 dark:border-amber-500/30', text: 'text-amber-700 dark:text-amber-400', icon: 'text-amber-500 dark:text-amber-400', badge: 'bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400', ring: 'ring-amber-500/20' },
  orange: { bg: 'bg-orange-50 dark:bg-orange-500/10', border: 'border-orange-200 dark:border-orange-500/30', text: 'text-orange-700 dark:text-orange-400', icon: 'text-orange-500 dark:text-orange-400', badge: 'bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-400', ring: 'ring-orange-500/20' },
  blue: { bg: 'bg-blue-50 dark:bg-blue-500/10', border: 'border-blue-200 dark:border-blue-500/30', text: 'text-blue-700 dark:text-blue-400', icon: 'text-blue-500 dark:text-blue-400', badge: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400', ring: 'ring-blue-500/20' },
  violet: { bg: 'bg-violet-50 dark:bg-violet-500/10', border: 'border-violet-200 dark:border-violet-500/30', text: 'text-violet-700 dark:text-violet-400', icon: 'text-violet-500 dark:text-violet-400', badge: 'bg-violet-100 dark:bg-violet-500/20 text-violet-700 dark:text-violet-400', ring: 'ring-violet-500/20' },
  emerald: { bg: 'bg-emerald-50 dark:bg-emerald-500/10', border: 'border-emerald-200 dark:border-emerald-500/30', text: 'text-emerald-700 dark:text-emerald-400', icon: 'text-emerald-500 dark:text-emerald-400', badge: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400', ring: 'ring-emerald-500/20' }
}

// Inline quantity editing
const editingItemId = ref(null)
const editQty = ref(0)
let debounceTimer = null
let isTabbing = false

const orderedItems = computed(() =>
  etapas.flatMap(e => itensPorEtapa.value[e.value])
)

const startEditQty = (item) => {
  editingItemId.value = item.id
  editQty.value = item.quantidade === 0 ? null : item.quantidade
}

const commitEditQty = (item) => {
  if (isTabbing) return
  const val = editQty.value
  if (val != null && val > 0 && val !== item.quantidade) {
    emit('update-quantity', item.id, val)
  }
  editingItemId.value = null
}

const tabToNextItem = (item) => {
  isTabbing = true
  clearTimeout(debounceTimer)
  const val = editQty.value
  if (val != null && val > 0 && val !== item.quantidade) {
    emit('update-quantity', item.id, val)
  }
  const list = orderedItems.value
  const idx = list.findIndex(i => i.id === item.id)
  const next = list[idx + 1]
  if (next) {
    if (!expandedEtapas.value.has(next.etapa_obra)) {
      expandedEtapas.value.add(next.etapa_obra)
    }
    startEditQty(next)
  } else {
    editingItemId.value = null
  }
  setTimeout(() => { isTabbing = false }, 0)
}

const debouncedUpdateQty = (item) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    if (editQty.value > 0) {
      emit('update-quantity', item.id, editQty.value)
    }
  }, 600)
}
</script>

<template>
  <div class="space-y-3">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <div class="flex items-center gap-2">
        <Network class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
        <h3 class="text-sm font-extrabold text-ink uppercase tracking-wider">Árvore de Custos (EAP)</h3>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="emit('aplicar-template-padrao')"
          :disabled="isApplyingTemplate"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-ink/10 border border-ink/20 rounded-lg text-[11px] font-bold text-ink hover:bg-ink/20 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          title="Preencher a árvore com os insumos padrão para o tipo desta obra"
        >
          <Loader2 v-if="isApplyingTemplate" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          <Sparkles v-else class="w-4 h-4" stroke-width="1.5" />
          {{ isApplyingTemplate ? 'Aplicando...' : 'Itens Padrão' }}
        </button>
        <button
          @click="emit('add-manual-item')"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-surface border border-hairline rounded-lg text-[11px] font-bold text-ink hover:bg-canvas hover:text-brand-primary transition-colors cursor-pointer"
        >
          <Plus class="w-4 h-4" stroke-width="1.5" />
          Item Manual
        </button>
        <span v-if="items.length" class="text-[10px] font-bold text-ink-muted bg-canvas px-2 py-1 rounded border border-hairline">{{ items.length }} itens</span>
        <button
          v-if="items.length"
          @click="emit('expandir')"
          class="flex items-center gap-1 px-2.5 py-1.5 bg-surface border border-hairline rounded-lg text-ink-muted hover:bg-canvas hover:text-brand-primary transition-colors cursor-pointer"
          title="Expandir em tela cheia"
        >
          <Maximize2 class="w-4 h-4" stroke-width="1.5" />
        </button>
      </div>
    </div>

    <!-- Empty State Global -->
    <div v-if="items.length === 0" class="bg-surface rounded-2xl border border-dashed border-hairline p-8 text-center flex flex-col items-center justify-center space-y-4">
      <div class="w-16 h-16 bg-brand-primary/10 rounded-full flex items-center justify-center">
        <Package class="w-8 h-8 text-brand-primary" stroke-width="1.5" />
      </div>
      <div>
        <h4 class="text-sm font-bold text-ink">Orçamento Vazio</h4>
        <p class="text-xs text-ink-muted mt-1 max-w-[240px] mx-auto">Esta obra não possui itens orçados. Importe um modelo salvo ou adicione itens manualmente para iniciar.</p>
      </div>
      <div class="flex flex-col sm:flex-row items-center gap-2.5 w-full max-w-sm">
        <button
          @click="emit('aplicar-template-padrao')"
          :disabled="isApplyingTemplate"
          class="w-full py-2.5 bg-ink hover:bg-brand-hover text-canvas rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-2 group cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="isApplyingTemplate" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          <Sparkles v-else class="w-4 h-4" stroke-width="1.5" />
          {{ isApplyingTemplate ? 'Aplicando...' : 'Itens Padrão' }}
        </button>
        <button
          @click="emit('import-template')"
          class="w-full py-2.5 bg-surface border border-hairline hover:bg-canvas text-ink rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-2 group cursor-pointer"
        >
          <Download class="w-4 h-4" stroke-width="1.5" />
          Importar Modelo
        </button>
        <button
          @click="emit('add-manual-item')"
          class="w-full py-2.5 bg-surface border border-hairline hover:bg-canvas text-ink rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-2 group cursor-pointer"
        >
          <Plus class="w-4 h-4" stroke-width="1.5" />
          Item Manual
        </button>
      </div>
    </div>

    <!-- Accordions -->
    <template v-else>
      <div 
        v-for="etapa in etapas" 
        :key="etapa.value" 
        class="rounded-xl border overflow-hidden transition-colors"
        :class="expandedEtapas.has(etapa.value) ? [colorClasses[etapa.color].border] : 'border-hairline'"
      >
        <!-- Accordion Header -->
        <button 
          @click="toggleEtapa(etapa.value)"
          class="w-full flex items-center justify-between px-4 py-3 transition-colors hover:bg-canvas/50 cursor-pointer"
          :class="expandedEtapas.has(etapa.value) ? colorClasses[etapa.color].bg : 'bg-surface'"
        >
          <div class="flex items-center gap-3">
            <component 
              :is="iconMap[etapa.icon]" 
              class="w-5 h-5" 
              :class="colorClasses[etapa.color].icon"
              stroke-width="1.5"
            />
            <span class="text-sm font-bold text-ink">{{ etapa.label }}</span>
            <span 
              class="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
              :class="colorClasses[etapa.color].badge"
            >{{ itensPorEtapa[etapa.value].length }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs font-bold text-ink-muted font-mono">{{ formatCurrency(subtotalEtapa(etapa.value)) }}</span>
            <ChevronDown 
              class="w-5 h-5 text-ink-muted transition-transform duration-300"
              :class="{ 'rotate-180': expandedEtapas.has(etapa.value) }"
              stroke-width="1.5"
            />
          </div>
        </button>

        <!-- Accordion Body -->
        <transition
          enter-active-class="transition-all duration-300 ease-out"
          leave-active-class="transition-all duration-200 ease-in"
          enter-from-class="max-h-0 opacity-0"
          enter-to-class="max-h-[2000px] opacity-100"
          leave-from-class="max-h-[2000px] opacity-100"
          leave-to-class="max-h-0 opacity-0"
        >
          <div v-show="expandedEtapas.has(etapa.value)" class="overflow-hidden border-t border-hairline">
            <!-- Empty State -->
            <div v-if="itensPorEtapa[etapa.value].length === 0" class="px-4 py-6 text-center bg-surface">
              <ListPlus class="w-8 h-8 text-ink-muted mx-auto mb-1" stroke-width="1.5" />
              <p class="text-[11px] text-ink-muted">Nenhum item nesta etapa.</p>
              <p class="text-[10px] text-ink-muted">Adicione insumos na tabela SINAPI ao lado.</p>
            </div>

            <!-- Items List -->
            <div v-else class="divide-y divide-hairline bg-surface">
              <!-- Wrapper for item -->
              <div 
                v-for="item in itensPorEtapa[etapa.value]" 
                :key="item.id" 
                class="flex flex-col"
              >
                <!-- Main Item Row -->
                <div class="px-4 py-3 flex items-center gap-3 group hover:bg-canvas/50 transition-colors">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-0.5">
                      <span v-if="item.codigo_sinapi && item.codigo_sinapi !== 'MANUAL'" class="text-[10px] font-mono text-ink-muted bg-canvas px-1.5 py-0.5 rounded border border-hairline">{{ item.codigo_sinapi }}</span>
                      <span v-else class="text-[9px] font-bold text-ink-muted bg-canvas border border-hairline px-1.5 py-0.5 rounded uppercase tracking-tighter">Manual</span>
                    </div>
                    <p class="text-xs font-semibold text-ink truncate">{{ item.descricao }}</p>
                    <div class="flex items-center gap-3 mt-1">
                      <span class="text-[10px] text-ink-muted">{{ formatCurrency(item.valor_unitario) }}/{{ item.unidade }}</span>
                    </div>
                  </div>

                  <!-- Quantity -->
                  <div class="flex items-center gap-1 shrink-0">
                    <AlertTriangle
                      v-if="item.quantidade == 0 && editingItemId !== item.id"
                      class="w-4 h-4 text-amber-500"
                      title="Quantidade não informada — clique no valor para preencher"
                      stroke-width="1.5"
                    />
                    <div
                      v-if="editingItemId === item.id"
                      class="flex items-center"
                    >
                      <input
                        :ref="el => { if (el) nextTick(() => el.focus()) }"
                        v-model.number="editQty"
                        type="number"
                        min="0.01"
                        step="0.01"
                        @input="debouncedUpdateQty(item)"
                        @blur="commitEditQty(item)"
                        @keyup.enter="commitEditQty(item)"
                        @keydown.tab.prevent="tabToNextItem(item)"
                        class="w-16 text-center text-xs font-bold bg-surface border border-brand-primary text-ink rounded-md py-1 focus:outline-none focus:ring-1 focus:ring-brand-primary"
                      />
                    </div>
                    <button
                      v-else
                      @click="startEditQty(item)"
                      class="text-xs font-bold px-2.5 py-1 rounded-md border border-transparent transition-colors cursor-pointer tabular-nums"
                      :class="item.quantidade == 0
                        ? 'text-amber-600 bg-amber-50 dark:bg-amber-500/10 hover:border-amber-300'
                        : 'text-brand-primary bg-brand-primary/10 hover:border-brand-primary/30'"
                    >
                      {{ item.quantidade }} {{ item.unidade }}
                    </button>
                  </div>

                  <!-- Subtotal -->
                  <span class="text-xs font-bold text-ink w-24 text-right shrink-0 tabular-nums">
                    {{ formatCurrency(item.quantidade * item.valor_unitario) }}
                  </span>

                  <!-- Delete -->
                  <button 
                    @click="$emit('remove-item', item.id)"
                    class="p-1 rounded-md text-ink-muted hover:text-red-550 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100 shrink-0 cursor-pointer"
                    title="Remover item"
                  >
                    <X class="w-4 h-4" stroke-width="1.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Grand Total -->
      <div class="mt-4 bg-canvas rounded-xl border border-hairline p-4 text-ink">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs text-ink-muted font-medium">Subtotal (sem BDI)</span>
          <span class="text-sm font-bold text-ink-muted tabular-nums">{{ formatCurrency(totalGeral) }}</span>
        </div>
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs text-ink-muted font-medium">BDI aplicado</span>
          <span class="text-sm font-bold text-brand-primary tabular-nums">+ {{ bdi }}%</span>
        </div>
        <div class="border-t border-hairline pt-3 flex items-center justify-between">
          <span class="text-sm font-bold text-ink uppercase tracking-wider">Total Final</span>
          <span class="text-xl font-black text-brand-primary tabular-nums">{{ formatCurrency(totalComBdi) }}</span>
        </div>
      </div>
    </template>
  </div>
</template>
