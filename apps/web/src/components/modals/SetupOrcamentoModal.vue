<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  isOpen: Boolean,
  project: Object
})

const emit = defineEmits(['close', 'salvar'])

const mesesDisponiveis = ref(['03/2026', '02/2026'])
const isSaving = ref(false)

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
    emit('salvar', props.project.id)
  } catch (error) {
    console.error('Erro ao configurar obra:', error)
    alert('Erro ao salvar configurações da obra.')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-zinc-950/40 dark:bg-zinc-950/60 backdrop-blur-sm" style="z-index: 120;" @click.self="emit('close')">
    <div class="bg-surface border border-hairline w-full max-w-md overflow-hidden animate-in zoom-in duration-200 shadow-sm">
      <!-- Header -->
      <div class="px-6 py-5 border-b border-hairline flex items-center justify-between bg-canvas">
        <div class="flex items-center gap-3">
          <div class="bg-brand-primary/10 text-brand-primary p-2 rounded-lg">
            <span class="material-symbols-outlined text-[24px]">construction</span>
          </div>
          <div>
            <h3 class="text-lg font-bold text-ink">Setup da Obra</h3>
            <p class="text-xs text-ink-muted">Configure a base de preços SINAPI</p>
          </div>
        </div>
        <button @click="emit('close')" class="text-ink-muted hover:text-ink p-1 rounded-md hover:bg-surface-hover transition-colors">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <!-- Body -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-5">
        <div class="grid grid-cols-2 gap-4">
          <!-- UF -->
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">Estado (UF)</label>
            <div class="relative">
              <select v-model="form.uf_obra" class="w-full bg-canvas border border-hairline rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary appearance-none cursor-pointer text-ink">
                <option value="" disabled selected>Selecione...</option>
                <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
              </select>
              <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none">expand_more</span>
            </div>
          </div>

          <!-- Encargos -->
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">Encargos Sociais</label>
            <div class="relative">
              <select v-model="form.sinapi_desonerado" class="w-full bg-canvas border border-hairline rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary appearance-none cursor-pointer text-ink">
                <option :value="false">Não Desonerado</option>
                <option :value="true">Desonerado</option>
              </select>
              <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none">expand_more</span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <!-- Mês Referência -->
          <div class="space-y-1.5">
            <div class="flex items-center gap-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">Mês de Referência</label>
              <div class="group relative cursor-help">
                <span class="material-symbols-outlined text-[14px] text-ink-muted">info</span>
                <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2 bg-zinc-800 text-white text-[10px] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl leading-tight">
                  A base de preços do SINAPI é atualizada no sistema mediante a disponibilização oficial do arquivo pela Caixa Econômica Federal. Exibimos sempre a versão mais recente.
                  <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-zinc-800"></div>
                </div>
              </div>
            </div>
            <div class="relative">
              <select v-model="form.sinapi_mes_ano" class="w-full bg-canvas border border-hairline rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary appearance-none cursor-pointer text-ink">
                <option v-for="mes in mesesDisponiveis" :key="mes" :value="mes">{{ mes }}</option>
              </select>
              <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none">expand_more</span>
            </div>
          </div>

          <!-- BDI -->
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">BDI da Obra (%)</label>
            <input 
              v-model.number="form.bdi_padrao" 
              type="number" 
              step="0.1"
              placeholder="Ex: 25.0"
              @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }"
              class="w-full bg-canvas border border-hairline rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary font-mono font-bold text-ink"
            />
          </div>
        </div>

        <!-- Padrão da Obra + Área -->
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">Padrão da Obra</label>
            <div class="relative">
              <select v-model="form.padrao" class="w-full bg-canvas border border-hairline rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary appearance-none cursor-pointer text-ink">
                <option value="" disabled>Selecione...</option>
                <option v-for="p in PADROES" :key="p.id" :value="p.id">{{ p.label }}</option>
              </select>
              <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none">expand_more</span>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">Área Total (m²)</label>
            <input
              v-model.number="form.area_m2"
              type="number"
              min="1"
              step="0.01"
              placeholder="Ex: 150"
              class="w-full bg-canvas border border-hairline rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary font-mono font-bold text-ink"
            />
          </div>
        </div>

        <!-- UX Hint -->
        <div class="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-500/10 rounded-xl border border-amber-100 dark:border-amber-500/20">
          <span class="material-symbols-outlined text-amber-500 text-[22px]">lightbulb</span>
          <p class="text-sm text-amber-900 dark:text-amber-500 leading-snug font-medium">
            Fique tranquilo! Você poderá alterar o Estado, Mês e BDI a qualquer momento dentro do painel do orçamento.
          </p>
        </div>

        <!-- Footer -->
        <div class="flex gap-3 pt-2">
          <button type="button" @click="emit('close')" class="flex-1 py-3 border border-hairline rounded-xl text-sm font-semibold text-ink-muted hover:bg-canvas transition-colors">
            Cancelar
          </button>
          <button 
            type="submit" 
            :disabled="isSaving"
            class="flex-[1.5] py-3 bg-brand-primary hover:bg-brand-hover text-white rounded-xl font-bold text-sm transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
          >
            <span v-if="isSaving" class="material-symbols-outlined animate-spin text-[18px]">sync</span>
            {{ isSaving ? 'Configurando...' : 'Salvar Configurações' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
