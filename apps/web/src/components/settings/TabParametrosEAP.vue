<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useToast } from '../../composables/useToast'
import { ETAPAS_OBRA } from '../../constants/etapas'
import {
  FilePenLine,
  Lock,
  RotateCcw,
  Loader2,
  Save,
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

const { showToast } = useToast()

const isLoading = ref(true)
const isSaving = ref(false)
const isResetting = ref(false)
const templates = ref([])
const source = ref('sistema')
const activePadrao = ref('medio')

const PADROES = [
  { id: 'popular', label: 'Popular' },
  { id: 'medio',   label: 'Médio' },
  { id: 'alto',    label: 'Alto Padrão' },
]

const activeTemplate = computed(() =>
  templates.value.find(t => t.padrao_obra === activePadrao.value)
)

const isCustomizado = computed(() => activeTemplate.value?.tipo === 'CUSTOMIZADO')

const itensByFase = computed(() => {
  if (!activeTemplate.value) return {}
  const itens = activeTemplate.value.template_eap_itens ?? []
  return Object.fromEntries(
    ETAPAS_OBRA.map(etapa => [
      etapa.value,
      itens.filter(i => i.fase_obra === etapa.value),
    ])
  )
})

const loadTemplates = async () => {
  isLoading.value = true
  try {
    const res = await axios.get('/configuracoes/templates')
    templates.value = res.data.data
    source.value = res.data.source
  } catch {
    showToast('Erro ao carregar parâmetros EAP.', 'error')
  } finally {
    isLoading.value = false
  }
}

const saveTemplate = async () => {
  if (!activeTemplate.value) return
  isSaving.value = true
  try {
    const itens = activeTemplate.value.template_eap_itens ?? []
    const payload = {
      padrao_obra: activeTemplate.value.padrao_obra,
      nome: activeTemplate.value.nome,
      itens: itens.map(({ codigo_sinapi, fase_obra, fator_area_multiplicador }) => ({
        codigo_sinapi, fase_obra, fator_area_multiplicador: Number(fator_area_multiplicador),
      })),
    }
    const res = await axios.post('/configuracoes/templates', payload)
    const idx = templates.value.findIndex(t => t.padrao_obra === payload.padrao_obra)
    if (idx !== -1) templates.value[idx] = res.data.data
    showToast('Parâmetros personalizados salvos com sucesso!', 'success')
  } catch {
    showToast('Erro ao salvar parâmetros.', 'error')
  } finally {
    isSaving.value = false
  }
}

const resetTemplate = async () => {
  if (!confirm(`Restaurar o template "${activePadrao.value}" para o padrão do sistema? Suas alterações serão perdidas.`)) return
  isResetting.value = true
  try {
    await axios.delete(`/configuracoes/templates/${activePadrao.value}`)
    await loadTemplates()
    showToast('Template restaurado para o padrão do sistema.', 'success')
  } catch {
    showToast('Erro ao restaurar template.', 'error')
  } finally {
    isResetting.value = false
  }
}

onMounted(loadTemplates)
</script>

<template>
  <div class="space-y-5">

    <!-- Header card -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Parâmetros de Estimativa (EAP Padrão)</h3>
        <p class="text-xs text-ink-muted mt-0.5">
          Defina os fatores multiplicadores usados para pré-calcular a EAP ao finalizar o setup de uma obra.
          O valor de cada fator representa a quantidade do serviço por m² de área de piso.
        </p>
      </div>

      <!-- Seletor de padrão -->
      <div class="px-6 py-4 flex items-center gap-2 border-b border-hairline bg-canvas/40">
        <button
          v-for="p in PADROES"
          :key="p.id"
          @click="activePadrao = p.id"
          class="px-4 py-1.5 rounded-md text-sm font-semibold transition-all focus:outline-none cursor-pointer"
          :class="activePadrao === p.id
            ? 'bg-brand-primary text-white'
            : 'bg-canvas border border-hairline text-ink-muted hover:text-ink'"
        >
          {{ p.label }}
        </button>

        <div class="ml-auto flex items-center gap-2">
          <span
            v-if="isCustomizado"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-500/10 text-amber-600 border border-amber-500/20"
          >
            <FilePenLine class="w-3.5 h-3.5" stroke-width="1.5" />
            Personalizado
          </span>
          <span
            v-else
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-ink-muted/10 text-ink-muted border border-hairline"
          >
            <Lock class="w-3.5 h-3.5" stroke-width="1.5" />
            Sistema
          </span>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="isLoading" class="px-6 py-8 space-y-3">
        <div v-for="i in 5" :key="i" class="h-8 bg-canvas rounded-md animate-pulse" />
      </div>

      <!-- Tabela de parâmetros -->
      <div v-else-if="activeTemplate" class="divide-y divide-hairline">
        <div
          v-for="etapa in ETAPAS_OBRA"
          :key="etapa.value"
          class="px-6 py-4"
        >
          <div class="flex items-center gap-2 mb-3">
            <component :is="iconMap[etapa.icon]" class="w-4 h-4 text-ink-muted shrink-0" stroke-width="1.5" />
            <span class="text-xs font-bold text-ink uppercase tracking-wide">{{ etapa.label }}</span>
            <span class="ml-1 text-[11px] text-ink-muted">({{ (itensByFase[etapa.value] ?? []).length }} itens)</span>
          </div>

          <div v-if="(itensByFase[etapa.value] ?? []).length" class="rounded-md border border-hairline overflow-hidden">
            <table class="w-full text-xs">
              <thead>
                <tr class="bg-canvas/60 border-b border-hairline">
                  <th class="text-left px-4 py-2 text-ink-muted font-semibold w-16">SINAPI</th>
                  <th class="text-left px-4 py-2 text-ink-muted font-semibold">Serviço / Insumo</th>
                  <th class="text-center px-4 py-2 text-ink-muted font-semibold w-16">Unid.</th>
                  <th class="text-right px-4 py-2 text-ink-muted font-semibold w-36">Fator (qtd / m²)</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in itensByFase[etapa.value]"
                  :key="item.id ?? item.codigo_sinapi"
                  class="border-b border-hairline last:border-0 hover:bg-canvas/40 transition-colors"
                >
                  <td class="px-4 py-2.5 text-ink-muted font-mono">{{ item.codigo_sinapi }}</td>
                  <td class="px-4 py-2.5 text-ink">{{ item.descricao }}</td>
                  <td class="px-4 py-2.5 text-center text-ink-muted">{{ item.unidade }}</td>
                  <td class="px-4 py-2.5">
                    <div class="flex items-center justify-end gap-1.5">
                      <input
                        v-model.number="item.fator_area_multiplicador"
                        type="number"
                        min="0.001"
                        step="0.01"
                        class="w-24 text-right bg-canvas border border-hairline text-ink rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all"
                      />
                      <span class="text-ink-muted shrink-0">/ m²</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="text-xs text-ink-muted italic">Nenhum item nesta fase.</p>
        </div>
      </div>

      <!-- Rodapé com ações -->
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex items-center justify-between gap-3">
        <button
          v-if="isCustomizado"
          @click="resetTemplate"
          :disabled="isResetting"
          class="flex items-center gap-1.5 text-xs text-ink-muted hover:text-ink transition-colors cursor-pointer disabled:opacity-50 flex items-center justify-center"
        >
          <RotateCcw class="w-3.5 h-3.5" stroke-width="1.5" />
          Restaurar padrão do sistema
        </button>
        <span v-else class="text-xs text-ink-muted italic">Editando os parâmetros criará sua versão personalizada.</span>

        <button
          @click="saveTemplate"
          :disabled="isSaving"
          class="ml-auto flex items-center gap-2 bg-brand-primary hover:bg-brand-hover text-white px-5 py-2 rounded-md font-bold text-sm transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center"
        >
          <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          <Save v-else class="w-4 h-4" stroke-width="1.5" />
          {{ isCustomizado ? 'Atualizar Parâmetros' : 'Salvar como Personalizado' }}
        </button>
      </div>
    </div>

  </div>
</template>
