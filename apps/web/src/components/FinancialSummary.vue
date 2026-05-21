<script setup>
import { computed, onBeforeUnmount, watch, ref } from 'vue'
import { formatCurrency } from '../utils/formatters'

const props = defineProps({
  cartItems: {
    type: Array,
    default: () => []
  },
  activeOrcamento: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['remove-item', 'update-quantity', 'item-added'])

import axios from 'axios'
import ManualItemModal from './ManualItemModal.vue'

const showManualItemModal = ref(false)
const isSavingManualItem = ref(false)
const isDownloadingPDF = ref(false)

const adicionarItemManual = async (itemData) => {
  if (!itemData.descricao || !props.activeOrcamento) return
  isSavingManualItem.value = true
  try {
    const payload = {
      codigo_sinapi: 'MANUAL',
      descricao: itemData.descricao,
      unidade: itemData.unidade || 'UN',
      valor_unitario: itemData.valor_unitario || 0,
      quantidade: itemData.quantidade || 1,
      tipo_item: 'insumo',
      etapa_obra: itemData.etapa_obra || 'servicos_preliminares'
    }
    const res = await axios.post(`/projetos/${props.activeOrcamento.id}/itens`, payload)
    if (res.data.success) {
      showManualItemModal.value = false
      emit('item-added', res.data.data)
    }
  } catch(e) {
    console.error(e)
  } finally {
    isSavingManualItem.value = false
  }
}

const baixarPropostaPDF = async () => {
  if (!props.activeOrcamento) return
  isDownloadingPDF.value = true
  try {
    const res = await axios.get(`/projetos/${props.activeOrcamento.id}/pdf-comercial`, {
      responseType: 'blob' // IMPORTANTE: Impede que o axios converta os binários do PDF para string
    })
    
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `proposta_comercial_${props.activeOrcamento.id}.pdf`)
    document.body.appendChild(link)
    link.click()
    
    // Limpa a URL temporária da memória
    link.parentNode.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Erro ao gerar Proposta em PDF:', error)
    
    // Como o responseType é 'blob', precisamos decodificar a mensagem de erro do backend
    let detalheErro = "Rota não encontrada ou erro de rede."
    if (error.response && error.response.data instanceof Blob) {
      const text = await error.response.data.text()
      try {
        const json = JSON.parse(text)
        detalheErro = json.detail || text
      } catch(e) {
        detalheErro = text
      }
    }
    alert(`Falha ao gerar PDF (Status ${error.response?.status}).\nMensagem do Servidor: ${detalheErro}`)
  } finally {
    isDownloadingPDF.value = false
  }
}

// Local formatCurrency removed (imported from formatters.js)

const searchQuery = ref('')
const isExpanded = ref(false)

const filteredCartItems = computed(() => {
  if (!searchQuery.value) return props.cartItems
  const query = searchQuery.value.toLowerCase()
  return props.cartItems.filter(item => 
    (item.descricao && item.descricao.toLowerCase().includes(query)) ||
    (item.codigo_sinapi && item.codigo_sinapi.toLowerCase().includes(query))
  )
})

const bdiRate = computed(() => {
  if (props.activeOrcamento && props.activeOrcamento.bdi) {
    return props.activeOrcamento.bdi / 100
  }
  return 0
})

const subtotal = computed(() => {
  return props.cartItems.reduce((acc, item) => {
    return acc + (Number(item.quantidade) * Number(item.valor_unitario))
  }, 0)
})

let debounceTimeout = null
let pendingUpdate = null

const flushPending = () => {
  if (pendingUpdate) {
    if (debounceTimeout) clearTimeout(debounceTimeout)
    emit('update-quantity', pendingUpdate.id, pendingUpdate.val)
    pendingUpdate = null
  }
}

onBeforeUnmount(() => {
  flushPending()
  document.body.classList.remove('overflow-hidden')
})

watch(() => props.activeOrcamento, () => {
  flushPending()
})

watch(isExpanded, (newVal) => {
  if (newVal) {
    document.body.classList.add('overflow-hidden')
  } else {
    document.body.classList.remove('overflow-hidden')
  }
})

const updateQuantity = (item, event) => {
  let val = parseFloat(event.target.value)
  if (isNaN(val) || val <= 0) val = 1
  
  // Atualiza localmente para reatividade imediata no visual
  item.quantidade = val
  pendingUpdate = { id: item.id, val }
  
  if (debounceTimeout) clearTimeout(debounceTimeout)
  debounceTimeout = setTimeout(() => {
    emit('update-quantity', item.id, val)
    pendingUpdate = null
  }, 500)
}

const bdiValue = computed(() => {
  return subtotal.value * bdiRate.value
})

const totalValue = computed(() => {
  return subtotal.value + bdiValue.value
})
</script>

<template>
  <div class="h-full">
    <div class="bg-surface p-6 rounded-xl border border-hairline flex flex-col max-h-[calc(100vh-8rem)]">
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-xl font-bold text-ink flex items-center gap-2">
          <span class="material-symbols-outlined text-brand-primary">analytics</span>
          Resumo Financeiro
        </h3>
        <button @click="isExpanded = true" class="text-ink-muted hover:text-brand-primary transition-colors cursor-pointer" title="Modo de Foco (Expandir)">
          <span class="material-symbols-outlined">fullscreen</span>
        </button>
      </div>
      <div class="flex flex-col flex-1 min-h-0">
        <div class="flex justify-between items-center py-3 border-b border-hairline shrink-0">
          <span class="text-ink-muted font-medium text-sm">Subtotal de Custos</span>
          <span class="text-ink font-mono font-semibold text-sm">{{ formatCurrency(subtotal) }}</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <div class="flex items-center gap-2">
            <span class="text-ink-muted font-medium text-sm">BDI</span>
            <span class="bg-canvas text-ink-muted text-[10px] px-1.5 py-0.5 rounded font-bold border border-hairline">{{ (bdiRate * 100).toFixed(1) }}%</span>
          </div>
          <span class="text-ink font-mono font-semibold text-sm">{{ formatCurrency(bdiValue) }}</span>
        </div>
        
        <!-- Lista de itens do carrinho -->
        <div v-if="cartItems.length > 0" class="mt-4 flex-1 overflow-y-auto min-h-[300px] pr-2 space-y-2 border-t border-hairline pt-4">
          <div class="flex items-center justify-between mb-4 shrink-0 gap-2">
            <h4 class="text-xs font-semibold text-ink-muted uppercase tracking-wider">Itens ({{ cartItems.length }})</h4>
            <div class="flex items-center gap-2">
              <button @click="showManualItemModal = true" class="text-xs bg-surface hover:bg-canvas text-ink px-2.5 py-1.5 rounded-lg font-semibold transition-all border border-hairline flex items-center gap-1 cursor-pointer">
                <span class="material-symbols-outlined text-[14px] text-brand-primary">add</span> Item Manual
              </button>
              <div class="relative w-48">
                <span class="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-ink-muted text-sm">search</span>
                <input v-model="searchQuery" class="w-full bg-canvas border border-hairline rounded-lg px-2 py-1.5 pl-8 text-xs focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all text-ink" placeholder="Buscar no carrinho..." type="text"/>
              </div>
            </div>
          </div>
          
          <div v-for="item in filteredCartItems" :key="item.id" class="flex justify-between items-start p-2 hover:bg-canvas rounded-lg group border border-transparent hover:border-hairline transition-colors">
            <div class="flex-1 min-w-0 pr-2">
              <p class="text-xs font-semibold text-ink truncate" :title="item.descricao">
                {{ item.descricao }}
              </p>
              <div class="flex items-center gap-2 mt-1">
                  <input 
                    type="number" 
                    step="0.01" 
                    min="0.01" 
                    :value="item.quantidade"
                    @input="(e) => updateQuantity(item, e)"
                    @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }"
                    class="w-16 bg-surface border border-hairline rounded px-1.5 py-0.5 text-[10px] focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all text-ink font-semibold"
                  />
                <span class="text-[10px] text-ink-muted">
                  {{ item.unidade }} x {{ formatCurrency(item.valor_unitario) }}
                </span>
              </div>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span class="text-xs font-mono font-bold text-ink">
                {{ formatCurrency(Number(item.quantidade) * Number(item.valor_unitario)) }}
              </span>
              <button @click="emit('remove-item', item.id)" class="text-ink-muted hover:text-red-500 transition-colors cursor-pointer" title="Remover">
                <span class="material-symbols-outlined text-[14px]">delete</span>
              </button>
            </div>
          </div>
        </div>
        
        <!-- Final Total Card -->
        <div class="mt-6 shrink-0 bg-brand-primary/10 p-6 rounded-xl border border-brand-primary/20 flex flex-col items-center text-center">
          <span class="text-xs font-semibold tracking-wider text-brand-primary uppercase mb-2">Valor Total Final da Obra</span>
          <div class="text-[32px] font-bold text-brand-primary tracking-tight">
            {{ formatCurrency(totalValue) }}
          </div>
          <div class="mt-4 flex items-center gap-1 text-brand-primary text-xs font-semibold opacity-90">
            <span class="material-symbols-outlined text-[16px]">check_circle</span>
            Valores atualizados com SINAPI
          </div>
        </div>
        
        <button @click="baixarPropostaPDF" :disabled="isDownloadingPDF" class="w-full shrink-0 mt-6 flex items-center justify-center gap-2 bg-brand-primary text-white py-3 rounded-lg hover:bg-brand-hover transition-all font-semibold disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer">
          <span v-if="isDownloadingPDF" class="material-symbols-outlined animate-spin">progress_activity</span>
          <span v-else class="material-symbols-outlined">picture_as_pdf</span> 
          {{ isDownloadingPDF ? 'Gerando PDF...' : 'Gerar Proposta Comercial' }}
        </button>
        
        <button class="w-full shrink-0 mt-3 flex items-center justify-center gap-2 bg-zinc-950 dark:bg-zinc-900 text-white hover:bg-zinc-900 dark:hover:bg-zinc-800 border border-transparent dark:border-hairline py-3 rounded-lg transition-all font-semibold cursor-pointer">
          <span class="material-symbols-outlined">description</span> Gerar Dossiê Caixa
        </button>
      </div>
    </div>
    
    <!-- Modal Modo de Foco -->
    <Teleport to="body">
      <Transition 
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div v-if="isExpanded" class="fixed inset-[-50px] z-[60] bg-zinc-950/40 dark:bg-zinc-950/80 backdrop-blur-md flex items-center justify-center p-6">
        <div class="bg-surface w-full max-w-6xl h-[90vh] rounded-2xl flex flex-col overflow-hidden border border-hairline shadow-lg">
          
          <!-- Modal Header -->
          <div class="px-8 py-5 border-b border-hairline flex items-center justify-between bg-canvas shrink-0">
            <div class="flex items-center gap-3">
              <div class="bg-brand-primary/10 p-2 rounded-lg border border-brand-primary/20">
                <span class="material-symbols-outlined text-brand-primary">fullscreen</span>
              </div>
              <div>
                <h2 class="text-xl font-bold text-ink">Modo de Foco: Carrinho</h2>
                <p class="text-sm text-ink-muted">Edite as quantidades e visualize o orçamento em tela cheia.</p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="relative w-64">
                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted text-sm">search</span>
                <input v-model="searchQuery" class="w-full bg-canvas border border-hairline rounded-lg py-2 pl-9 pr-4 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all text-ink" placeholder="Buscar item..." type="text"/>
              </div>
              <button @click="isExpanded = false" class="p-2 text-ink-muted hover:text-ink hover:bg-surface-hover rounded-lg transition-colors cursor-pointer">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
          </div>
          
          <!-- Modal Body (Table) -->
          <div class="flex-1 overflow-y-auto bg-canvas/50 p-6">
            <div class="bg-surface border border-hairline rounded-xl overflow-hidden">
              <table class="w-full text-left border-collapse">
                <thead class="bg-canvas border-b border-hairline">
                  <tr>
                    <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider w-24">Código</th>
                    <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider">Descrição do Item</th>
                    <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider w-20 text-center">Unid.</th>
                    <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider w-32 text-right">Valor Unitário</th>
                    <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider w-40 text-center">Quantidade</th>
                    <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider w-32 text-right">Subtotal</th>
                    <th class="px-6 py-4 text-xs font-semibold text-ink-muted uppercase tracking-wider w-16 text-center">Ações</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-hairline">
                  <tr v-if="filteredCartItems.length === 0">
                    <td colspan="7" class="px-6 py-8 text-center text-ink-muted">Nenhum item corresponde à busca.</td>
                  </tr>
                  <tr v-for="item in filteredCartItems" :key="item.id" class="hover:bg-canvas transition-colors">
                    <td class="px-6 py-4 font-mono text-sm text-ink-muted">{{ item.codigo_sinapi }}</td>
                    <td class="px-6 py-4 font-medium text-ink text-sm max-w-md truncate" :title="item.descricao">{{ item.descricao }}</td>
                    <td class="px-6 py-4 text-ink-muted text-sm text-center">{{ item.unidade }}</td>
                    <td class="px-6 py-4 text-ink-muted text-sm text-right font-mono">{{ formatCurrency(item.valor_unitario) }}</td>
                    <td class="px-6 py-4">
                      <div class="flex items-center justify-center">
                        <input 
                          type="number" 
                          step="0.01" 
                          min="0.01" 
                          :value="item.quantidade"
                          @input="(e) => updateQuantity(item, e)"
                          @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }"
                          class="w-24 bg-canvas border border-hairline rounded-lg px-3 py-1.5 text-sm text-center focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all font-semibold text-ink"
                        />
                      </div>
                    </td>
                    <td class="px-6 py-4 font-mono font-bold text-ink text-sm text-right">
                      {{ formatCurrency(Number(item.quantidade) * Number(item.valor_unitario)) }}
                    </td>
                    <td class="px-6 py-4 text-center">
                      <button @click="emit('remove-item', item.id)" class="text-ink-muted hover:text-red-500 transition-colors p-1.5 rounded hover:bg-red-50 dark:hover:bg-canvas cursor-pointer" title="Remover Item">
                        <span class="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <!-- Modal Footer (Totais) -->
          <div class="px-8 py-5 border-t border-hairline bg-surface flex items-center justify-between shrink-0">
            <div class="flex items-center gap-6">
              <div>
                <span class="text-xs font-semibold text-ink-muted uppercase tracking-wider block mb-1">Subtotal (Custos)</span>
                <span class="text-lg font-mono font-medium text-ink">{{ formatCurrency(subtotal) }}</span>
              </div>
              <div class="h-10 w-px bg-hairline"></div>
              <div>
                <span class="text-xs font-semibold text-ink-muted uppercase tracking-wider block mb-1">BDI ({{ (bdiRate * 100).toFixed(1) }}%)</span>
                <span class="text-lg font-mono font-medium text-ink">{{ formatCurrency(bdiValue) }}</span>
              </div>
            </div>
            
            <div class="flex items-center gap-6">
              <div class="text-right">
                <span class="text-xs font-semibold text-brand-primary uppercase tracking-wider block mb-1">Valor Total Final</span>
                <span class="text-3xl font-bold tracking-tight text-brand-primary">{{ formatCurrency(totalValue) }}</span>
              </div>
              <button @click="isExpanded = false" class="bg-brand-primary hover:bg-brand-hover text-white px-8 py-3 rounded-xl font-bold transition-all active:scale-95 cursor-pointer">
                Concluir Edição
              </button>
            </div>
          </div>
          
        </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Reaproveitamento do componente ManualItemModal -->
    <ManualItemModal
      :is-open="showManualItemModal"
      :is-saving="isSavingManualItem"
      @close="showManualItemModal = false"
      @confirm="adicionarItemManual"
    />
  </div>
</template>
