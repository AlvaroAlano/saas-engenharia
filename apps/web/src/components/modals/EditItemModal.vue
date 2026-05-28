<script setup>
import { ref, watch, computed } from 'vue'
import { ETAPAS_OBRA } from '../../constants/etapas'
import { ChevronDown, Loader2, Check } from 'lucide-vue-next'
import BaseModal from './BaseModal.vue'

const props = defineProps({
  isOpen: Boolean,
  itemData: Object,
  isEditing: Boolean,
  isSaving: Boolean
})

const emit = defineEmits(['close', 'salvarItem'])

const quantidadeInput = ref(1)
const bdiInput = ref(20) // BDI padrão em %
const etapaObra = ref('servicos_preliminares')

const etapas = ETAPAS_OBRA

// Sincroniza os dados locais com o itemData fornecido
watch(() => props.isOpen, (newVal) => {
  if (newVal && props.itemData) {
    quantidadeInput.value = props.itemData.quantidade || 1
    bdiInput.value = props.itemData.bdi !== undefined ? props.itemData.bdi : 20
    etapaObra.value = props.itemData.etapa_obra || 'servicos_preliminares'
  }
})

// Preço unitário extraído de forma segura (suporta formato SINAPI ou formato do carrinho)
const precoUnitario = computed(() => {
  if (!props.itemData) return 0
  const preco = props.itemData.preco !== undefined ? props.itemData.preco : props.itemData.valor_unitario
  return Number(preco) || 0
})

// Cálculo reativo do valor total com BDI
const valorTotalCalculado = computed(() => {
  const base = quantidadeInput.value * precoUnitario.value
  const bdiMultiplier = 1 + (Number(bdiInput.value) || 0) / 100
  return base * bdiMultiplier
})

const handleConfirm = () => {
  if (quantidadeInput.value > 0) {
    const payloadData = {
      codigo_sinapi: props.itemData.codigo_item || props.itemData.codigo_sinapi,
      descricao: props.itemData.descricao,
      unidade: props.itemData.unidade,
      valor_unitario: precoUnitario.value,
      quantidade: Number(quantidadeInput.value),
      bdi: Number(bdiInput.value),
      valor_total_com_bdi: valorTotalCalculado.value,
      tipo_item: props.itemData.tipo || props.itemData.tipo_item || 'insumo',
      etapa_obra: etapaObra.value
    }
    emit('salvarItem', payloadData)
  }
}
</script>

<template>
  <BaseModal :isOpen="isOpen" @close="emit('close')" maxWidthClass="max-w-md" zIndexClass="z-50">
    <template #header>
      <h3 class="text-lg font-medium text-ink">
        {{ isEditing ? 'Editar Quantidade / BDI' : 'Adicionar ao Orçamento' }}
      </h3>
    </template>

    <div class="space-y-4">
      <!-- Card de Resumo do Item -->
      <div v-if="itemData" class="p-4 bg-canvas rounded-md border border-hairline">
        <p class="text-xs font-mono text-ink-muted mb-1 select-none">
          Cód. {{ itemData.codigo_item || itemData.codigo_sinapi }}
        </p>
        <p class="text-sm font-semibold text-ink line-clamp-2 select-text">{{ itemData.descricao }}</p>
        <div class="flex items-center justify-between mt-3 pt-2 border-t border-hairline">
          <span class="text-xs text-ink-muted select-none">Custo Unitário Base:</span>
          <span class="text-xs font-bold text-ink tabular-nums">
            R$ {{ precoUnitario.toFixed(2).replace('.', ',') }} / {{ itemData.unidade }}
          </span>
        </div>
      </div>

      <!-- Etapa da Obra -->
      <div>
        <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Etapa da Obra</label>
        <div class="relative">
          <select 
            v-model="etapaObra" 
            class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all appearance-none cursor-pointer font-medium font-sans"
          >
            <option v-for="etapa in etapas" :key="etapa.value" :value="etapa.value">{{ etapa.label }}</option>
          </select>
          <ChevronDown class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
        </div>
      </div>

      <!-- Grade: Quantidade e BDI -->
      <div class="grid grid-cols-2 gap-3">
        <!-- Quantidade -->
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Quantidade</label>
          <div class="relative">
            <input 
              v-model.number="quantidadeInput" 
              type="number" 
              min="0.01" 
              step="0.01"
              @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }"
              class="w-full pl-3 pr-10 py-2 bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md focus:ring-2 focus:ring-blue-500/40 focus:border-transparent outline-none transition-all font-bold text-base font-sans"
              placeholder="1.0"
            />
            <div class="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none select-none">
              <span class="text-ink-muted font-bold text-xs">{{ itemData?.unidade }}</span>
            </div>
          </div>
        </div>

        <!-- BDI (%) -->
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">BDI (%)</label>
          <div class="relative">
            <input 
              v-model.number="bdiInput" 
              type="number" 
              min="0" 
              max="100"
              step="0.1"
              @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }"
              class="w-full px-3 py-2 bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md focus:ring-2 focus:ring-blue-500/40 focus:border-transparent outline-none transition-all font-bold text-base text-right pr-8 font-sans"
              placeholder="20"
            />
            <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none select-none">
              <span class="text-ink-muted font-bold text-sm">%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Cálculo Total Reativo em Tempo Real -->
      <div class="bg-blue-500/10 border border-blue-500/20 rounded-md p-3.5 flex items-center justify-between">
        <div>
          <span class="block text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider select-none">Valor Total Calculado</span>
          <span class="text-xs text-ink-muted font-medium select-none">Qtd × Custo Base + BDI</span>
        </div>
        <span class="font-bold text-base text-blue-600 dark:text-blue-400 font-mono tabular-nums">
          R$ {{ valorTotalCalculado.toFixed(2).replace('.', ',') }}
        </span>
      </div>
    </div>
    
    <template #footer>
      <button 
        type="button"
        @click="emit('close')"
        class="h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink bg-transparent hover:bg-surface-hover rounded-md transition-colors cursor-pointer flex items-center justify-center"
      >
        Cancelar
      </button>
      <button 
        type="button"
        @click="handleConfirm"
        :disabled="isSaving || quantidadeInput <= 0"
        class="h-9 px-4 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" stroke-width="1.5" />
        <Check v-else class="w-4 h-4" stroke-width="1.5" />
        {{ isSaving ? 'Salvando...' : (isEditing ? 'Salvar Alteração' : 'Adicionar à Etapa') }}
      </button>
    </template>
  </BaseModal>
</template>

