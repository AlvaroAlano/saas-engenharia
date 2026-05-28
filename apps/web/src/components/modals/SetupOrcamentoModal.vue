<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import ConfirmarTemplateModal from './ConfirmarTemplateModal.vue'
import { Hammer, Info, Check, Lightbulb, Loader2, ChevronDown } from 'lucide-vue-next'
import BaseModal from './BaseModal.vue'
import { useToast } from '../../composables/useToast'

const { showToast } = useToast()

const props = defineProps({
  isOpen:            Boolean,
  project:           Object,
  cartItemsCount:    { type: Number,  default: 0 },
  hideTemplateOption:{ type: Boolean, default: false },
})

const emit = defineEmits(['close', 'salvar'])

const mesesDisponiveis = ref(['03/2026', '02/2026'])
const isSaving = ref(false)
const aplicarTemplate = ref(false)
const showConfirm = ref(false)

// Resetar checkbox quando o modal abre
watch(() => props.isOpen, (val) => { if (!val) aplicarTemplate.value = false })

const PADROES = [
  { id: 'popular', label: 'Popular' },
  { id: 'medio',   label: 'Médio' },
  { id: 'alto',    label: 'Alto Padrão' },
]

const form = ref({
  uf_obra: '',
  sinapi_desonerado: false,
  sinapi_mes_ano: '',
  bdi_padrao: null,
  padrao: '',
  area_m2: null,
})

const ufs = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

const carregarReferencias = async () => {
  try {
    const res = await axios.get('/sinapi/referencias')
    if (res.data.success && res.data.data.length > 0) {
      mesesDisponiveis.value = res.data.data
      if (!form.value.sinapi_mes_ano) {
        form.value.sinapi_mes_ano = res.data.data[0]
      }
    }
  } catch (e) {
    console.error('Erro ao buscar referências no modal:', e)
  }
}

const syncForm = () => {
  if (props.project) {
    form.value.uf_obra = props.project.uf_obra || ''
    form.value.sinapi_desonerado = props.project.sinapi_desonerado ?? false
    form.value.sinapi_mes_ano = props.project.sinapi_mes_ano || (mesesDisponiveis.value[0] || '')
    form.value.bdi_padrao = props.project.bdi_padrao ?? null
    
    // Normalize padrao from wizard string/name to ID
    let padraoObra = props.project.padrao || ''
    if (typeof padraoObra === 'string') {
      const p = padraoObra.toLowerCase()
      if (p.includes('popular')) {
        padraoObra = 'popular'
      } else if (p.includes('med') || p.includes('mdio') || p.includes('médio')) {
        padraoObra = 'medio'
      } else if (p.includes('alto')) {
        padraoObra = 'alto'
      }
    }
    form.value.padrao = padraoObra

    // Normalize area/size from string (e.g. "125m²") to number
    form.value.area_m2 = props.project.tamanho
      ? parseFloat(String(props.project.tamanho).replace(/[^0-9.,]/g, '').replace(',', '.')) || null
      : null
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    carregarReferencias().then(() => {
      syncForm()
    })
  }
})

onMounted(() => {
  carregarReferencias().then(() => {
    syncForm()
  })
})

const handleSubmit = async () => {
  if (!props.project?.id) return
  isSaving.value = true
  try {
    const payload = {
      uf_obra: form.value.uf_obra,
      sinapi_desonerado: form.value.sinapi_desonerado,
      sinapi_mes_ano: form.value.sinapi_mes_ano,
      bdi_padrao: form.value.bdi_padrao,
      padrao: form.value.padrao || null,
      tamanho: form.value.area_m2 ? `${form.value.area_m2}m²` : null,
    }

    await axios.patch(`/projetos/${props.project.id}`, payload)

    if (aplicarTemplate.value && form.value.padrao) {
      if (props.cartItemsCount > 0) {
        showConfirm.value = true
        return  // execução continua em onConfirmarTemplate
      }
      await _aplicarTemplate('mesclar')
    }

    emit('salvar', props.project.id)
  } catch (error) {
    console.error('Erro ao configurar obra:', error)
    showToast('Erro ao salvar configurações da obra.', 'error')
  } finally {
    isSaving.value = false
  }
}

const _aplicarTemplate = async (modo) => {
  try {
    const res = await axios.post(`/projetos/${props.project.id}/aplicar-template-padrao`, { modo })
    if (res.data?.sem_preco?.length) {
      console.warn(`[Template] ${res.data.sem_preco.length} código(s) sem preço no SINAPI:`, res.data.sem_preco)
    }
  } catch (e) {
    console.error('Erro ao aplicar template:', e)
  }
}

const onConfirmarTemplate = async (modo) => {
  showConfirm.value = false
  isSaving.value = true
  try {
    await _aplicarTemplate(modo)
    emit('salvar', props.project.id)
  } finally {
    isSaving.value = false
  }
}

const onCancelarTemplate = () => {
  showConfirm.value = false
  emit('salvar', props.project.id)
}
</script>

<template>
  <BaseModal :isOpen="isOpen" @close="emit('close')" maxWidthClass="max-w-md" zIndexClass="z-[120]">
    <template #header>
      <div class="flex items-center gap-3">
        <div class="bg-blue-500/10 text-blue-600 p-2 rounded-md flex items-center justify-center shrink-0">
          <Hammer class="w-6 h-6" stroke-width="1.5" />
        </div>
        <div>
          <h3 class="text-lg font-medium text-ink">Setup da Obra</h3>
          <p class="text-xs text-ink-muted select-none">Configure a base de preços SINAPI</p>
        </div>
      </div>
    </template>

    <!-- Body -->
    <form id="setup-obra-form" @submit.prevent="handleSubmit" class="space-y-4">
      <div class="grid grid-cols-2 gap-4">
        <!-- UF -->
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 select-none">Estado (UF)</label>
          <div class="relative">
            <select v-model="form.uf_obra" class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all appearance-none cursor-pointer font-medium font-sans">
              <option value="" disabled selected>Selecione...</option>
              <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
            </select>
            <ChevronDown class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
          </div>
        </div>

        <!-- Encargos -->
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 select-none">Encargos Sociais</label>
          <div class="relative">
            <select v-model="form.sinapi_desonerado" class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all appearance-none cursor-pointer font-medium font-sans">
              <option :value="false">Não Desonerado</option>
              <option :value="true">Desonerado</option>
            </select>
            <ChevronDown class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <!-- Mês Referência -->
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 flex items-center gap-1.5 select-none">
            Mês de Referência
            <div class="group relative cursor-help flex items-center">
              <Info class="w-3.5 h-3.5 text-neutral-400" stroke-width="1.5" />
              <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2 bg-zinc-800 text-white text-[10px] rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl leading-tight font-normal">
                A base de preços do SINAPI é atualizada no sistema mediante a disponibilização oficial do arquivo pela Caixa Econômica Federal. Exibimos sempre a versão mais recente.
                <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-zinc-800"></div>
              </div>
            </div>
          </label>
          <div class="relative">
            <select v-model="form.sinapi_mes_ano" class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all appearance-none cursor-pointer font-medium font-sans">
              <option v-for="mes in mesesDisponiveis" :key="mes" :value="mes">{{ mes }}</option>
            </select>
            <ChevronDown class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
          </div>
        </div>

        <!-- BDI -->
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 select-none">BDI da Obra (%)</label>
          <input 
            v-model.number="form.bdi_padrao" 
            type="number" 
            step="0.1"
            placeholder="Ex: 25.0"
            @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }"
            class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all font-mono font-bold font-sans"
          />
        </div>
      </div>

      <!-- Padrão da Obra + Área -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 select-none">Padrão da Obra</label>
          <div class="relative">
            <select v-model="form.padrao" class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all appearance-none cursor-pointer font-medium font-sans">
              <option value="" disabled>Selecione...</option>
              <option v-for="p in PADROES" :key="p.id" :value="p.id">{{ p.label }}</option>
            </select>
            <ChevronDown class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 select-none">Área Total (m²)</label>
          <input
            v-model.number="form.area_m2"
            type="number"
            min="1"
            step="0.01"
            placeholder="Ex: 150"
            class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all font-mono font-bold font-sans"
          />
        </div>
      </div>

      <!-- Checkbox: Preencher com itens padrão (oculto quando hideTemplateOption=true) -->
      <div 
        v-if="form.padrao && !hideTemplateOption" 
        class="flex items-start gap-3 p-4 bg-blue-500/5 rounded-md border border-blue-500/20 cursor-pointer select-none transition-all hover:bg-blue-500/10" 
        @click="aplicarTemplate = !aplicarTemplate"
      >
        <div class="mt-0.5 shrink-0">
          <div class="w-4 h-4 rounded border flex items-center justify-center transition-all"
               :class="aplicarTemplate ? 'bg-blue-600 border-blue-600' : 'border-neutral-400 bg-surface'">
            <Check v-if="aplicarTemplate" class="w-3 h-3 text-white" stroke-width="2" />
          </div>
        </div>
        <div>
          <p class="text-sm font-semibold text-ink leading-tight">Preencher árvore com itens padrão</p>
          <p class="text-xs text-ink-muted mt-0.5 leading-relaxed">Insere os serviços típicos do padrão <strong>{{ form.padrao }}</strong> já vinculados ao SINAPI. As quantidades ficam em zero para você preencher.</p>
        </div>
      </div>

      <!-- UX Hint -->
      <div class="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-500/10 rounded-md border border-amber-100 dark:border-amber-500/20 select-none">
        <Lightbulb class="w-5 h-5 text-amber-500 shrink-0" stroke-width="1.5" />
        <p class="text-xs text-amber-900 dark:text-amber-500 leading-relaxed font-medium">
          Dica: Você poderá alterar o Estado (UF), Mês de Referência e BDI a qualquer momento dentro do painel do orçamento.
        </p>
      </div>
    </form>

    <template #footer>
      <button 
        type="button" 
        @click="emit('close')" 
        class="h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink bg-transparent hover:bg-surface-hover rounded-md transition-colors cursor-pointer flex items-center justify-center"
      >
        Cancelar
      </button>
      <button 
        type="submit" 
        form="setup-obra-form"
        :disabled="isSaving"
        class="h-9 px-4 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center justify-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-60"
      >
        <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" stroke-width="1.5" />
        {{ isSaving ? 'Configurando...' : 'Salvar Configurações' }}
      </button>
    </template>
  </BaseModal>

  <ConfirmarTemplateModal
    :is-open="showConfirm"
    :cart-items-count="cartItemsCount"
    @confirmar="onConfirmarTemplate"
    @cancelar="onCancelarTemplate"
  />
</template>

