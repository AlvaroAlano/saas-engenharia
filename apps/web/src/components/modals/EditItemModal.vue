<script setup>
import { ref, watch, computed } from 'vue'
import { ETAPAS_OBRA } from '../../constants/etapas'

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
      // Preserva identificadores
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
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/40 dark:bg-zinc-950/60 backdrop-blur-sm" @click.self="emit('close')">
      <div class="bg-surface border border-hairline w-full max-w-md overflow-hidden transform transition-all animate-in zoom-in duration-200 shadow-sm">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-ink">
              {{ isEditing ? 'Editar Quantidade / BDI' : 'Adicionar ao Orçamento' }}
            </h3>
            <button @click="emit('close')" class="p-1 rounded-lg hover:bg-surface-hover text-ink-muted transition-all">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          
          <!-- Card de Resumo do Item -->
          <div v-if="itemData" class="mb-5 p-4 bg-canvas rounded-xl border border-hairline">
            <p class="text-xs font-mono text-ink-muted mb-1">
              Cód. {{ itemData.codigo_item || itemData.codigo_sinapi }}
            </p>
            <p class="text-sm font-semibold text-ink line-clamp-2">{{ itemData.descricao }}</p>
            <div class="flex items-center justify-between mt-3 pt-2 border-t border-hairline">
              <span class="text-xs text-ink-muted">Custo Unitário Base:</span>
              <span class="text-xs font-bold text-ink">
                R$ {{ precoUnitario.toFixed(2).replace('.', ',') }} / {{ itemData.unidade }}
              </span>
            </div>
          </div>

          <!-- Etapa da Obra -->
          <div class="space-y-1.5 mb-4">
            <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider">Etapa da Obra</label>
            <div class="relative">
              <select 
                v-model="etapaObra" 
                class="w-full bg-canvas border border-hairline rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary appearance-none cursor-pointer font-medium text-ink"
              >
                <option v-for="etapa in etapas" :key="etapa.value" :value="etapa.value">{{ etapa.label }}</option>
              </select>
              <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none text-[20px]">expand_more</span>
            </div>
          </div>

          <!-- Grade: Quantidade e BDI -->
          <div class="grid grid-cols-2 gap-3 mb-5">
            <!-- Quantidade -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider">Quantidade</label>
              <div class="relative">
                <input 
                  v-model.number="quantidadeInput" 
                  type="number" 
                  min="0.01" 
                  step="0.01"
                  @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }"
                  class="w-full pl-3 pr-10 py-2.5 bg-surface border border-hairline rounded-xl text-ink focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all font-bold text-base"
                  placeholder="1.0"
                />
                <div class="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none">
                  <span class="text-ink-muted font-bold text-xs">{{ itemData?.unidade }}</span>
                </div>
              </div>
            </div>

            <!-- BDI (%) -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider">BDI (%)</label>
              <div class="relative">
                <input 
                  v-model.number="bdiInput" 
                  type="number" 
                  min="0" 
                  max="100"
                  step="0.1"
                  @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }"
                  class="w-full px-3 py-2.5 bg-surface border border-hairline rounded-xl text-ink focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all font-bold text-base text-right pr-8"
                  placeholder="20"
                />
                <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <span class="text-ink-muted font-bold text-sm">%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Cálculo Total Reativo em Tempo Real -->
          <div class="bg-brand-primary/10 border border-brand-primary/30 rounded-xl p-3.5 flex items-center justify-between">
            <div>
              <span class="block text-[10px] font-bold text-brand-primary uppercase tracking-wider">Valor Total Calculado</span>
              <span class="text-xs text-ink-muted font-medium">Qtd × Preço Base + BDI</span>
            </div>
            <span class="font-bold text-base text-brand-primary font-mono">
              R$ {{ valorTotalCalculado.toFixed(2).replace('.', ',') }}
            </span>
          </div>
        </div>
        
        <!-- Rodapé de Ações -->
        <div class="px-6 py-4 bg-canvas border-t border-hairline flex justify-end gap-3">
          <button 
            @click="emit('close')"
            class="px-5 py-2.5 text-sm font-semibold text-ink-muted hover:text-ink hover:bg-surface-hover rounded-xl transition-colors"
          >
            Cancelar
          </button>
          <button 
            @click="handleConfirm"
            :disabled="isSaving || quantidadeInput <= 0"
            class="px-6 py-2.5 text-sm font-bold text-white bg-brand-primary hover:bg-brand-hover rounded-xl transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isSaving" class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
            <span v-else class="material-symbols-outlined text-[18px]">
              {{ isEditing ? 'save' : 'add_circle' }}
            </span>
            {{ isSaving ? 'Salvando...' : (isEditing ? 'Salvar Alteração' : 'Adicionar à Etapa') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
