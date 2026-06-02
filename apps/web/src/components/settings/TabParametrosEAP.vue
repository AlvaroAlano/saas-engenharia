<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useToast } from '../../composables/useToast'
import { useFases } from '../../composables/useFases'
import BaseButton from '../ui/BaseButton.vue'
import TabFasesEAP from './TabFasesEAP.vue'
import {
  Lock, Star, Plus, Trash2, Save, Loader2, Copy,
  Search, X, ChevronDown, ChevronRight,
  HardHat, Layers, Building, Zap, Paintbrush,
  Wrench, Home, Package, Settings2, LayoutGrid,
  AlertCircle, FileText, Info
} from 'lucide-vue-next'

// ── Icon / Color maps ────────────────────────────────────────────────────────

const iconMap = {
  engineering:   HardHat,
  foundation:    Layers,
  domain:        Building,
  electric_bolt: Zap,
  format_paint:  Paintbrush,
  wrench:        Wrench,
  home:          Home,
  package:       Package,
  settings:      Settings2,
  grid:          LayoutGrid,
}

const _colorFallback = { text: 'text-blue-600', bg: 'bg-blue-500/10', border: 'border-blue-500/25', icon: 'text-blue-500', bar: 'bg-blue-500' }

const colorMap = {
  amber:   { text: 'text-amber-600',   bg: 'bg-amber-500/10',   border: 'border-amber-500/25',   icon: 'text-amber-500',   bar: 'bg-amber-500'   },
  orange:  { text: 'text-orange-600',  bg: 'bg-orange-500/10',  border: 'border-orange-500/25',  icon: 'text-orange-500',  bar: 'bg-orange-500'  },
  blue:    { text: 'text-blue-600',    bg: 'bg-blue-500/10',    border: 'border-blue-500/25',    icon: 'text-blue-500',    bar: 'bg-blue-500'    },
  violet:  { text: 'text-violet-600',  bg: 'bg-violet-500/10',  border: 'border-violet-500/25',  icon: 'text-violet-500',  bar: 'bg-violet-500'  },
  emerald: { text: 'text-emerald-600', bg: 'bg-emerald-500/10', border: 'border-emerald-500/25', icon: 'text-emerald-500', bar: 'bg-emerald-500' },
  red:     { text: 'text-red-600',     bg: 'bg-red-500/10',     border: 'border-red-500/25',     icon: 'text-red-500',     bar: 'bg-red-500'     },
  slate:   { text: 'text-slate-600',   bg: 'bg-slate-500/10',   border: 'border-slate-500/25',   icon: 'text-slate-500',   bar: 'bg-slate-500'   },
  cyan:    { text: 'text-cyan-600',    bg: 'bg-cyan-500/10',    border: 'border-cyan-500/25',    icon: 'text-cyan-500',    bar: 'bg-cyan-500'    },
  indigo:  { text: 'text-indigo-600',  bg: 'bg-indigo-500/10',  border: 'border-indigo-500/25',  icon: 'text-indigo-500',  bar: 'bg-indigo-500'  },
  green:   { text: 'text-green-600',   bg: 'bg-green-500/10',   border: 'border-green-500/25',   icon: 'text-green-500',   bar: 'bg-green-500'   },
}

const resolveColor = (color) => colorMap[color] ?? _colorFallback
const resolveIcon  = (icon)  => iconMap[icon]   ?? HardHat

const padraoBadge = {
  popular: { label: 'Popular',      text: 'text-emerald-700', bg: 'bg-emerald-500/12', border: 'border-emerald-500/25' },
  medio:   { label: 'Médio',        text: 'text-blue-700',   bg: 'bg-blue-500/12',   border: 'border-blue-500/25'   },
  alto:    { label: 'Alto Padrão',  text: 'text-orange-700', bg: 'bg-orange-500/12', border: 'border-orange-500/25' },
}

// ── State ────────────────────────────────────────────────────────────────────

const { showToast } = useToast()

const allTemplates  = reactive({ sistema: [], customizado: [] })
const activePerPadrao = ref({})

const selectedTemplateId = ref(null)
const editingTemplate    = ref(null)   // deep copy local para edição

const isLoading         = ref(true)
const isSaving          = ref(false)
const isDeleting        = ref(false)
const isSettingDefault  = ref(false)
const isDirty           = ref(false)

const newlyAdded  = reactive(new Set())
const collapsed   = reactive(new Set())
const panels      = reactive({})

// Modal Novo Template
const showCreateModal = ref(false)
const createForm = reactive({ nome: '', padrao_obra: 'medio', base_template_id: null, mode: 'copy' })
const isCreating = ref(false)

// ── Computed ─────────────────────────────────────────────────────────────────

const isSystemTemplate = computed(() => editingTemplate.value?.tipo === 'SISTEMA')

const isActiveTemplate = computed(() =>
  editingTemplate.value
    ? activePerPadrao.value[editingTemplate.value.padrao_obra] === editingTemplate.value.id
    : false
)

const { fases, ensureFases } = useFases()

const itensByFase = computed(() => {
  if (!editingTemplate.value) return {}
  const itens = editingTemplate.value.template_eap_itens ?? []
  return Object.fromEntries(
    fases.value.map(etapa => [
      etapa.value,
      itens.filter(i => i.fase_obra === etapa.value),
    ])
  )
})

const totalItens = computed(() =>
  (editingTemplate.value?.template_eap_itens ?? []).length
)

// Template base sugerido para o modal de criação
const suggestedBase = computed(() =>
  allTemplates.sistema.find(t => t.padrao_obra === createForm.padrao_obra) || null
)

// ── Load ─────────────────────────────────────────────────────────────────────

const loadAll = async () => {
  isLoading.value = true
  try {
    const res = await axios.get('/configuracoes/templates')
    allTemplates.sistema     = res.data.sistema     || []
    allTemplates.customizado = res.data.customizado || []
    activePerPadrao.value    = res.data.active_per_padrao || {}

    // Mantém a seleção atual se o template ainda existir
    if (selectedTemplateId.value && !isDirty.value) {
      const all = [...allTemplates.sistema, ...allTemplates.customizado]
      const fresh = all.find(t => t.id === selectedTemplateId.value)
      if (fresh) {
        editingTemplate.value = JSON.parse(JSON.stringify(fresh))
      } else {
        selectedTemplateId.value = null
        editingTemplate.value = null
      }
    }
  } catch {
    showToast('Erro ao carregar templates EAP.', 'error')
  } finally {
    isLoading.value = false
  }
}

// ── Template selection ────────────────────────────────────────────────────────

const selectTemplate = (template) => {
  if (isDirty.value && selectedTemplateId.value !== template.id) {
    if (!confirm('Há alterações não salvas. Descartar e abrir outro template?')) return
  }
  selectedTemplateId.value = template.id
  editingTemplate.value    = JSON.parse(JSON.stringify(template))
  isDirty.value = false
  newlyAdded.clear()
  Object.keys(panels).forEach(k => {
    panels[k] = { open: false, query: '', results: [], selected: null, factor: 0.01, searching: false }
  })
}

// ── Save ─────────────────────────────────────────────────────────────────────

const saveTemplate = async () => {
  if (!editingTemplate.value || isSystemTemplate.value) return
  isSaving.value = true
  try {
    const payload = {
      nome:        editingTemplate.value.nome,
      padrao_obra: editingTemplate.value.padrao_obra,
      itens: (editingTemplate.value.template_eap_itens ?? []).map(i => ({
        codigo_sinapi:             i.codigo_sinapi,
        fase_obra:                 i.fase_obra,
        fator_area_multiplicador:  Number(i.fator_area_multiplicador),
      })),
    }
    await axios.put(`/configuracoes/templates/${editingTemplate.value.id}`, payload)
    isDirty.value = false
    newlyAdded.clear()
    showToast('Template salvo com sucesso!', 'success')
    await loadAll()
  } catch {
    showToast('Erro ao salvar template.', 'error')
  } finally {
    isSaving.value = false
  }
}

// ── Delete ────────────────────────────────────────────────────────────────────

const deleteTemplate = async () => {
  if (!editingTemplate.value || isSystemTemplate.value) return
  const nome = editingTemplate.value.nome
  const isAtivo = isActiveTemplate.value
  const msg = isAtivo
    ? `Excluir "${nome}"? Este é o template ativo para o padrão ${editingTemplate.value.padrao_obra}. O próximo template disponível será promovido, ou o sistema voltará ao padrão do sistema.`
    : `Excluir "${nome}"? Esta ação não pode ser desfeita.`
  if (!confirm(msg)) return

  isDeleting.value = true
  try {
    const res = await axios.delete(`/configuracoes/templates/${editingTemplate.value.id}`)
    selectedTemplateId.value = null
    editingTemplate.value    = null
    isDirty.value = false

    if (res.data.fallback_to_sistema) {
      showToast('Template excluído. Voltou para o padrão do sistema.', 'info')
    } else if (res.data.promoted_id) {
      showToast('Template excluído. O próximo template foi definido como ativo.', 'success')
    } else {
      showToast('Template excluído.', 'success')
    }
    await loadAll()
  } catch {
    showToast('Erro ao excluir template.', 'error')
  } finally {
    isDeleting.value = false
  }
}

// ── Set Default ──────────────────────────────────────────────────────────────

// Aceita templateId explícito (clique na estrela do sidebar)
// ou usa o template aberto no editor (botão no header do editor)
const setDefault = async (templateId) => {
  const tid  = templateId ?? editingTemplate.value?.id
  if (!tid) return
  const all = [...allTemplates.sistema, ...allTemplates.customizado]
  const tpl = all.find(t => t.id === tid)
  if (!tpl || tpl.is_active) return   // já é ativo → nada a fazer

  isSettingDefault.value = true
  try {
    await axios.post(`/configuracoes/templates/${tid}/set-default`)
    showToast(`"${tpl.nome}" definido como template ativo!`, 'success')
    await loadAll()
  } catch {
    showToast('Erro ao definir template ativo.', 'error')
  } finally {
    isSettingDefault.value = false
  }
}

// ── Duplicate (usar sistema como base) ───────────────────────────────────────

const duplicateAsMine = (template) => {
  createForm.nome            = `Cópia de ${template.nome}`
  createForm.padrao_obra     = template.padrao_obra
  createForm.base_template_id = template.id
  createForm.mode            = 'copy'
  showCreateModal.value      = true
}

// ── Create ────────────────────────────────────────────────────────────────────

const openCreateModal = () => {
  createForm.nome             = ''
  createForm.padrao_obra      = 'medio'
  createForm.mode             = 'copy'
  createForm.base_template_id = suggestedBase.value?.id || null
  showCreateModal.value       = true
}

watch(() => createForm.padrao_obra, (newPadrao) => {
  if (createForm.mode === 'copy') {
    createForm.base_template_id = allTemplates.sistema.find(t => t.padrao_obra === newPadrao)?.id || null
  }
})

watch(() => createForm.mode, (mode) => {
  if (mode === 'copy') {
    createForm.base_template_id = allTemplates.sistema.find(t => t.padrao_obra === createForm.padrao_obra)?.id || null
  } else {
    createForm.base_template_id = null
  }
})

const createTemplate = async () => {
  if (!createForm.nome.trim()) { showToast('Informe um nome para o template.', 'warning'); return }
  isCreating.value = true
  try {
    const res = await axios.post('/configuracoes/templates', {
      nome:             createForm.nome.trim(),
      padrao_obra:      createForm.padrao_obra,
      base_template_id: createForm.base_template_id,
    })
    showCreateModal.value = false
    const newTpl = res.data.data
    if (res.data.auto_set_default) {
      showToast(`"${newTpl.nome}" criado e definido como template ativo para o padrão ${newTpl.padrao_obra}!`, 'success')
    } else {
      showToast(`"${newTpl.nome}" criado com sucesso!`, 'success')
    }
    await loadAll()
    // Seleciona o novo template
    const all = [...allTemplates.sistema, ...allTemplates.customizado]
    const fresh = all.find(t => t.id === newTpl.id)
    if (fresh) selectTemplate(fresh)
  } catch {
    showToast('Erro ao criar template.', 'error')
  } finally {
    isCreating.value = false
  }
}

// ── Add / Remove item ─────────────────────────────────────────────────────────

const getPanel = (faseValue) => {
  if (!panels[faseValue]) {
    panels[faseValue] = { open: false, query: '', results: [], selected: null, factor: 0.01, searching: false }
  }
  return panels[faseValue]
}

const searchTimers = {}

const onSearchInput = (faseValue) => {
  const p = getPanel(faseValue)
  p.selected = null
  if (searchTimers[faseValue]) clearTimeout(searchTimers[faseValue])
  if (!p.query || p.query.length < 2) { p.results = []; return }
  searchTimers[faseValue] = setTimeout(async () => {
    p.searching = true
    try {
      const res = await axios.get('/configuracoes/sinapi-search', { params: { q: p.query } })
      p.results = res.data.data || []
    } catch {
      p.results = []
    } finally {
      p.searching = false
    }
  }, 300)
}

const selectResult = (faseValue, item) => {
  const p = getPanel(faseValue)
  p.selected = item
  p.query    = `${item.codigo_item} — ${item.descricao}`
  p.results  = []
}

const clearSearch = (faseValue) => {
  const p = getPanel(faseValue)
  p.query = ''; p.results = []; p.selected = null
}

const closePanel = (faseValue) => {
  const p = getPanel(faseValue)
  p.open = false; clearSearch(faseValue); p.factor = 0.01
}

const addItem = (faseValue) => {
  const p = getPanel(faseValue)
  if (!p.selected || !editingTemplate.value) return
  const factor = Math.max(0.001, Number(p.factor) || 0.01)
  const exists = (editingTemplate.value.template_eap_itens ?? []).some(
    i => i.codigo_sinapi === p.selected.codigo_item && i.fase_obra === faseValue
  )
  if (exists) { showToast('Este item já existe nesta fase.', 'warning'); return }
  if (!editingTemplate.value.template_eap_itens) editingTemplate.value.template_eap_itens = []
  editingTemplate.value.template_eap_itens.push({
    codigo_sinapi: p.selected.codigo_item,
    descricao:     p.selected.descricao,
    unidade:       p.selected.unidade,
    fase_obra:     faseValue,
    fator_area_multiplicador: factor,
  })
  newlyAdded.add(`${faseValue}_${p.selected.codigo_item}`)
  isDirty.value = true
  closePanel(faseValue)
  showToast('Item adicionado ao template.', 'success')
}

const removeItem = (item) => {
  if (!editingTemplate.value) return
  const idx = editingTemplate.value.template_eap_itens.findIndex(
    i => i.codigo_sinapi === item.codigo_sinapi && i.fase_obra === item.fase_obra
  )
  if (idx !== -1) {
    editingTemplate.value.template_eap_itens.splice(idx, 1)
    newlyAdded.delete(`${item.fase_obra}_${item.codigo_sinapi}`)
    isDirty.value = true
  }
}

const toggleCollapse = (faseValue) => {
  if (collapsed.has(faseValue)) collapsed.delete(faseValue)
  else collapsed.add(faseValue)
}

onMounted(async () => {
  await ensureFases()
  await loadAll()
})
</script>

<template>
  <div class="space-y-5">

    <!-- Info banner -->
    <div class="flex items-start gap-3 px-4 py-3 rounded-md bg-blue-500/8 border border-blue-500/20">
      <Info class="w-4 h-4 text-blue-500 shrink-0 mt-0.5" stroke-width="1.5" />
      <p class="text-xs text-blue-700 leading-relaxed">
        Os <strong>templates EAP</strong> definem os serviços SINAPI e seus fatores (qtd / m²) usados para montar automaticamente a árvore de custos de uma obra.
        O template <strong>ativo</strong> (★) é aplicado automaticamente pelo padrão da obra; se houver mais de um, você pode escolher na tela de orçamento.
      </p>
    </div>

    <!-- Main card: sidebar + editor -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden flex h-[680px]">

      <!-- ── Sidebar ── -->
      <div class="w-60 shrink-0 bg-canvas/40 border-r border-hairline flex flex-col">

        <!-- Sidebar header -->
        <div class="px-4 py-3.5 border-b border-hairline">
          <h4 class="text-xs font-bold text-ink uppercase tracking-wide">Templates EAP</h4>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="p-3 space-y-2">
          <div v-for="i in 5" :key="i" class="h-10 bg-canvas rounded-md animate-pulse" />
        </div>

        <template v-else>

          <!-- Sistema templates -->
          <div class="px-3 pt-3 pb-1">
            <p class="text-[10px] font-bold text-ink-muted uppercase tracking-wider px-1 mb-1.5">Padrões do sistema</p>
            <div
              v-for="t in allTemplates.sistema"
              :key="t.id"
              class="flex items-center gap-1 mb-0.5"
            >
              <button
                @click="selectTemplate(t)"
                class="flex-1 flex items-center gap-2 px-2 py-2 rounded-md text-left transition-all min-w-0"
                :class="selectedTemplateId === t.id
                  ? 'bg-blue-500/10 border border-blue-500/20 shadow-sm'
                  : 'hover:bg-surface border border-transparent'"
              >
                <Lock class="w-3.5 h-3.5 text-ink-muted shrink-0" stroke-width="1.5" />
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-ink truncate">{{ t.nome }}</p>
                  <div class="flex items-center gap-1 mt-0.5">
                    <span class="text-[10px] font-semibold" :class="padraoBadge[t.padrao_obra].text">
                      {{ padraoBadge[t.padrao_obra].label }}
                    </span>
                    <span class="text-[10px] text-ink-muted">· {{ t.total_itens }} itens</span>
                  </div>
                </div>
              </button>

              <!-- Estrela: preenchida = ativo, borda = não ativo (clicável) -->
              <button
                v-if="t.is_active"
                type="button"
                class="p-1 rounded shrink-0 cursor-default"
                title="Template ativo"
              >
                <Star class="w-3.5 h-3.5 text-amber-500" fill="currentColor" stroke-width="0" />
              </button>
              <button
                v-else
                type="button"
                @click="setDefault(t.id)"
                :disabled="isSettingDefault"
                class="p-1 rounded shrink-0 text-ink-muted/40 hover:text-amber-500 transition-colors disabled:cursor-not-allowed"
                title="Definir como template ativo"
              >
                <Star class="w-3.5 h-3.5" stroke-width="1.5" />
              </button>
            </div>
          </div>

          <div class="mx-3 my-1 h-px bg-hairline" />

          <!-- Custom templates -->
          <div class="px-3 pt-1 flex-1 overflow-y-auto">
            <p class="text-[10px] font-bold text-ink-muted uppercase tracking-wider px-1 mb-1.5">Meus templates</p>

            <div v-if="!allTemplates.customizado.length" class="px-1 py-3 text-center">
              <p class="text-xs text-ink-muted">Nenhum template criado ainda.</p>
              <p class="text-[11px] text-ink-muted mt-0.5">Clique em "+ Novo Template" abaixo.</p>
            </div>

            <div
              v-for="t in allTemplates.customizado"
              :key="t.id"
              class="flex items-center gap-1 mb-0.5"
            >
              <!-- Template row (seleciona) -->
              <button
                @click="selectTemplate(t)"
                class="flex-1 flex items-center gap-2 px-2 py-2 rounded-md text-left transition-all min-w-0"
                :class="selectedTemplateId === t.id
                  ? 'bg-blue-500/10 border border-blue-500/20 shadow-sm'
                  : 'hover:bg-surface border border-transparent'"
              >
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-ink truncate">{{ t.nome }}</p>
                  <div class="flex items-center gap-1.5 mt-0.5">
                    <span
                      class="text-[10px] font-bold px-1.5 py-px rounded-full border"
                      :class="[padraoBadge[t.padrao_obra].text, padraoBadge[t.padrao_obra].bg, padraoBadge[t.padrao_obra].border]"
                    >
                      {{ padraoBadge[t.padrao_obra].label }}
                    </span>
                    <span class="text-[10px] text-ink-muted">{{ t.total_itens }} itens</span>
                  </div>
                </div>
              </button>

              <!-- Estrela: preenchida = ativo, borda = não ativo (clicável) -->
              <button
                v-if="t.is_active"
                type="button"
                class="p-1 rounded shrink-0 cursor-default"
                title="Template ativo"
              >
                <Star class="w-3.5 h-3.5 text-amber-500" fill="currentColor" stroke-width="0" />
              </button>
              <button
                v-else
                type="button"
                @click="setDefault(t.id)"
                :disabled="isSettingDefault"
                class="p-1 rounded shrink-0 text-ink-muted/40 hover:text-amber-500 transition-colors disabled:cursor-not-allowed"
                title="Definir como template ativo"
              >
                <Star class="w-3.5 h-3.5" stroke-width="1.5" />
              </button>
            </div>
          </div>

          <!-- New template button -->
          <div class="px-3 py-3 border-t border-hairline">
            <button
              @click="openCreateModal"
              class="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-orange-500 text-white hover:bg-orange-600 transition-colors"
            >
              <Plus class="w-3.5 h-3.5" stroke-width="2" />
              Novo Template
            </button>
          </div>

        </template>
      </div>

      <!-- ── Editor ── -->
      <div class="flex-1 flex flex-col min-w-0">

        <!-- Loading state -->
        <div v-if="isLoading && !editingTemplate" class="flex-1 flex items-center justify-center p-10">
          <Loader2 class="w-6 h-6 text-ink-muted animate-spin" stroke-width="1.5" />
        </div>

        <!-- Empty state -->
        <div v-else-if="!editingTemplate && !isLoading" class="flex-1 flex items-center justify-center p-10">
          <div class="text-center max-w-xs">
            <div class="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-3">
              <FileText class="w-6 h-6 text-blue-500" stroke-width="1.5" />
            </div>
            <p class="text-sm font-semibold text-ink">Selecione um template</p>
            <p class="text-xs text-ink-muted mt-1.5 leading-relaxed">
              Escolha um template na barra ao lado para visualizar ou editar seus itens. Para criar o seu próprio, clique em "Novo Template".
            </p>
          </div>
        </div>

        <template v-else-if="editingTemplate && !isLoading">

          <!-- Editor header -->
          <div class="px-6 py-4 border-b border-hairline">
            <div class="flex items-start gap-4 flex-wrap">
              <div class="flex-1 min-w-0">
                <!-- Nome (editável apenas em CUSTOMIZADO) -->
                <input
                  v-if="!isSystemTemplate"
                  v-model="editingTemplate.nome"
                  @input="isDirty = true"
                  type="text"
                  placeholder="Nome do template"
                  class="text-sm font-bold text-ink bg-transparent border-b border-transparent hover:border-hairline focus:border-brand-primary outline-none transition-all w-full pb-0.5"
                />
                <p v-else class="text-sm font-bold text-ink">{{ editingTemplate.nome }}</p>

                <!-- Padrão de obra -->
                <div class="flex items-center gap-2 mt-2 flex-wrap">
                  <span class="text-[11px] text-ink-muted">Padrão de obra:</span>
                  <template v-if="!isSystemTemplate">
                    <button
                      v-for="(badge, key) in padraoBadge"
                      :key="key"
                      @click="editingTemplate.padrao_obra = key; isDirty = true"
                      class="text-[11px] font-bold px-2 py-0.5 rounded-full border transition-all"
                      :class="editingTemplate.padrao_obra === key
                        ? [badge.text, badge.bg, badge.border]
                        : 'text-ink-muted bg-transparent border-hairline hover:border-ink-muted'"
                    >
                      {{ badge.label }}
                    </button>
                  </template>
                  <span v-else class="text-[11px] font-bold px-2 py-0.5 rounded-full border"
                    :class="[padraoBadge[editingTemplate.padrao_obra].text, padraoBadge[editingTemplate.padrao_obra].bg, padraoBadge[editingTemplate.padrao_obra].border]">
                    {{ padraoBadge[editingTemplate.padrao_obra].label }}
                  </span>
                </div>
              </div>

              <!-- Status badges -->
              <div class="flex items-center gap-2 flex-wrap">
                <!-- Stats -->
                <span class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-blue-500/8 text-blue-600 border border-blue-500/20">
                  <Info class="w-3.5 h-3.5" stroke-width="1.5" />
                  {{ totalItens }} itens · {{ fases.length }} fases
                </span>

                <!-- Ativo -->
                <span v-if="isActiveTemplate" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-500/10 text-amber-600 border border-amber-500/25">
                  <Star class="w-3.5 h-3.5" fill="currentColor" stroke-width="0" />
                  Template ativo
                </span>

                <!-- Sistema -->
                <span v-if="isSystemTemplate" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-ink-muted/10 text-ink-muted border border-hairline">
                  <Lock class="w-3.5 h-3.5" stroke-width="1.5" />
                  Padrão do sistema
                </span>

                <!-- Alterações -->
                <span v-if="isDirty" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-orange-500/10 text-orange-600 border border-orange-500/20">
                  <AlertCircle class="w-3.5 h-3.5" stroke-width="1.5" />
                  Não salvo
                </span>
              </div>
            </div>

            <!-- Definir como ativo (apenas CUSTOMIZADO não-ativo) -->
            <button
              v-if="!isSystemTemplate && !isActiveTemplate"
              @click="setDefault"
              :disabled="isSettingDefault"
              class="mt-3 flex items-center gap-1.5 text-xs font-medium text-ink-muted hover:text-amber-600 transition-colors disabled:opacity-50"
            >
              <Loader2 v-if="isSettingDefault" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
              <Star v-else class="w-3.5 h-3.5" stroke-width="1.5" />
              Definir como template ativo para o padrão {{ editingTemplate.padrao_obra }}
            </button>
          </div>

          <!-- Aviso somente leitura (SISTEMA) -->
          <div v-if="isSystemTemplate" class="px-6 py-2.5 bg-canvas/60 border-b border-hairline flex items-center gap-2">
            <Lock class="w-3.5 h-3.5 text-ink-muted shrink-0" stroke-width="1.5" />
            <p class="text-xs text-ink-muted">
              Templates do sistema são somente leitura. Para personalizar, clique em
              <button @click="duplicateAsMine(editingTemplate)" class="font-semibold text-orange-600 hover:underline">Criar cópia editável</button>.
            </p>
          </div>

          <!-- Phase sections -->
          <div class="flex-1 overflow-y-auto divide-y divide-hairline">
            <div v-for="etapa in fases" :key="etapa.value">

              <!-- Phase header -->
              <button
                type="button"
                @click="toggleCollapse(etapa.value)"
                class="w-full flex items-center gap-3 px-5 py-3 hover:bg-canvas/50 transition-colors text-left select-none"
              >
                <span class="w-1 h-5 rounded-full shrink-0" :class="resolveColor(etapa.color).bar" />
                <component :is="resolveIcon(etapa.icon)" class="w-4 h-4 shrink-0" :class="resolveColor(etapa.color).icon" stroke-width="1.5" />
                <span class="flex-1 text-xs font-bold text-ink uppercase tracking-wide">{{ etapa.label }}</span>
                <span class="text-[11px] font-bold px-2 py-0.5 rounded-full border"
                  :class="[resolveColor(etapa.color).bg, resolveColor(etapa.color).text, resolveColor(etapa.color).border]">
                  {{ (itensByFase[etapa.value] ?? []).length }} itens
                </span>
                <ChevronDown v-if="!collapsed.has(etapa.value)" class="w-4 h-4 text-ink-muted shrink-0" stroke-width="1.5" />
                <ChevronRight v-else class="w-4 h-4 text-ink-muted shrink-0" stroke-width="1.5" />
              </button>

              <!-- Phase content -->
              <div v-if="!collapsed.has(etapa.value)" class="px-5 pb-4">

                <!-- Items table -->
                <div v-if="(itensByFase[etapa.value] ?? []).length" class="rounded-md border border-hairline overflow-hidden mb-3">
                  <table class="w-full text-xs">
                    <thead>
                      <tr class="bg-canvas/60 border-b border-hairline">
                        <th class="text-left px-4 py-2 text-ink-muted font-semibold w-16">SINAPI</th>
                        <th class="text-left px-4 py-2 text-ink-muted font-semibold">Serviço / Insumo</th>
                        <th class="text-center px-4 py-2 text-ink-muted font-semibold w-14">Unid.</th>
                        <th class="text-right px-4 py-2 text-ink-muted font-semibold w-36">Fator (qtd / m²)</th>
                        <th v-if="!isSystemTemplate" class="w-8 px-1" />
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in itensByFase[etapa.value]"
                        :key="`${etapa.value}_${item.codigo_sinapi}`"
                        class="border-b border-hairline last:border-0 hover:bg-canvas/40 transition-colors group"
                      >
                        <td class="px-4 py-2.5 text-ink-muted font-mono text-[11px]">{{ item.codigo_sinapi }}</td>
                        <td class="px-4 py-2.5 text-ink">
                          <div class="flex items-center gap-2">
                            {{ item.descricao }}
                            <span
                              v-if="newlyAdded.has(`${etapa.value}_${item.codigo_sinapi}`)"
                              class="shrink-0 text-[10px] font-bold px-1.5 py-px rounded-full bg-orange-500/15 text-orange-600 border border-orange-500/20"
                            >Novo</span>
                          </div>
                        </td>
                        <td class="px-4 py-2.5 text-center text-ink-muted">{{ item.unidade }}</td>
                        <td class="px-4 py-2.5">
                          <div class="flex items-center justify-end gap-1.5">
                            <input
                              v-if="!isSystemTemplate"
                              v-model.number="item.fator_area_multiplicador"
                              type="number" min="0.001" step="0.01"
                              @change="isDirty = true"
                              class="w-24 text-right bg-canvas border border-hairline text-ink rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all"
                            />
                            <span v-else class="text-xs text-ink font-medium">{{ item.fator_area_multiplicador }}</span>
                            <span class="text-ink-muted shrink-0">/ m²</span>
                          </div>
                        </td>
                        <td v-if="!isSystemTemplate" class="px-1.5 py-2.5">
                          <button
                            type="button"
                            @click="removeItem(item)"
                            class="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-ink-muted hover:text-red-500 hover:bg-red-500/10 transition-all"
                            title="Remover item"
                          >
                            <Trash2 class="w-3.5 h-3.5" stroke-width="1.5" />
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <p v-else class="text-xs text-ink-muted italic mb-3">Nenhum item nesta fase.</p>

                <!-- Add item (só em templates customizados) -->
                <template v-if="!isSystemTemplate">
                  <div v-if="!getPanel(etapa.value).open">
                    <button
                      type="button"
                      @click="getPanel(etapa.value).open = true"
                      class="flex items-center gap-1.5 text-xs font-medium text-ink-muted hover:text-orange-600 transition-colors py-0.5 group"
                    >
                      <span class="w-5 h-5 rounded-md flex items-center justify-center bg-canvas border border-hairline group-hover:bg-orange-500/10 group-hover:border-orange-500/30 transition-all">
                        <Plus class="w-3 h-3" stroke-width="2.5" />
                      </span>
                      Adicionar item SINAPI
                    </button>
                  </div>

                  <div v-else class="rounded-lg border border-dashed border-orange-500/40 bg-orange-500/5 p-3 mt-1">
                    <p class="text-[11px] font-semibold text-orange-600 mb-2.5">Adicionar item em "{{ etapa.label }}"</p>
                    <div class="flex items-start gap-2.5 flex-wrap">

                      <!-- Search -->
                      <div class="flex-1 min-w-[220px] relative">
                        <div class="flex items-center gap-2 bg-surface border border-hairline rounded-lg px-3 py-2 focus-within:border-orange-500/60 focus-within:ring-1 focus-within:ring-orange-500/20 transition-all">
                          <Search class="w-3.5 h-3.5 text-ink-muted shrink-0" stroke-width="1.5" />
                          <input
                            v-model="getPanel(etapa.value).query"
                            @input="onSearchInput(etapa.value)"
                            type="text" autocomplete="off"
                            placeholder="Nome ou código SINAPI..."
                            class="flex-1 text-xs bg-transparent outline-none text-ink placeholder:text-ink-muted min-w-0"
                          />
                          <Loader2 v-if="getPanel(etapa.value).searching" class="w-3.5 h-3.5 text-ink-muted animate-spin shrink-0" stroke-width="1.5" />
                          <button v-else-if="getPanel(etapa.value).query" type="button" @click="clearSearch(etapa.value)" class="p-0.5 rounded text-ink-muted hover:text-ink transition-colors">
                            <X class="w-3 h-3" stroke-width="2" />
                          </button>
                        </div>
                        <!-- Dropdown -->
                        <div v-if="getPanel(etapa.value).results.length" class="absolute top-full left-0 right-0 z-20 mt-1 bg-surface border border-hairline rounded-lg shadow-lg overflow-hidden">
                          <button
                            v-for="r in getPanel(etapa.value).results" :key="r.codigo_item"
                            type="button" @click="selectResult(etapa.value, r)"
                            class="w-full flex items-center gap-3 px-3 py-2 hover:bg-canvas/70 transition-colors text-left border-b border-hairline last:border-0"
                          >
                            <span class="font-mono text-[10px] text-ink-muted w-12 shrink-0">{{ r.codigo_item }}</span>
                            <span class="flex-1 text-xs text-ink truncate">{{ r.descricao }}</span>
                            <span class="text-[10px] text-ink-muted shrink-0 ml-2">{{ r.unidade }}</span>
                          </button>
                        </div>
                        <div
                          v-else-if="getPanel(etapa.value).query.length >= 2 && !getPanel(etapa.value).searching && !getPanel(etapa.value).selected"
                          class="absolute top-full left-0 right-0 z-20 mt-1 bg-surface border border-hairline rounded-lg shadow-sm px-3 py-2.5"
                        >
                          <p class="text-xs text-ink-muted text-center">Nenhum item encontrado.</p>
                        </div>
                      </div>

                      <!-- Factor -->
                      <div class="flex flex-col shrink-0">
                        <span class="text-[10px] text-ink-muted mb-1 font-medium">Fator</span>
                        <div class="flex items-center gap-1">
                          <input
                            v-model.number="getPanel(etapa.value).factor"
                            type="number" min="0.001" step="0.001" placeholder="0.01"
                            class="w-20 text-right bg-surface border border-hairline text-ink rounded-lg px-2.5 py-2 text-xs focus:ring-1 focus:ring-orange-500/50 focus:border-orange-500 outline-none transition-all"
                          />
                          <span class="text-[11px] text-ink-muted">/ m²</span>
                        </div>
                      </div>

                      <!-- Buttons -->
                      <div class="flex items-end gap-1.5 shrink-0">
                        <button
                          type="button" @click="addItem(etapa.value)"
                          :disabled="!getPanel(etapa.value).selected"
                          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                        >
                          <Plus class="w-3.5 h-3.5" stroke-width="2" /> Adicionar
                        </button>
                        <button type="button" @click="closePanel(etapa.value)" class="px-2.5 py-2 rounded-lg text-xs text-ink-muted hover:bg-canvas transition-colors">
                          Cancelar
                        </button>
                      </div>
                    </div>
                    <p class="text-[10px] text-ink-muted mt-2">Digite ao menos 2 caracteres para buscar no banco SINAPI. Selecione o item e ajuste o fator antes de adicionar.</p>
                  </div>
                </template>

              </div>
            </div>
          </div>

          <!-- Editor footer -->
          <div class="px-6 py-3.5 bg-canvas/50 border-t border-hairline flex items-center gap-3 flex-wrap">
            <!-- Ações SISTEMA -->
            <template v-if="isSystemTemplate">
              <button
                @click="duplicateAsMine(editingTemplate)"
                class="flex items-center gap-1.5 text-xs font-semibold text-ink-muted hover:text-orange-600 transition-colors"
              >
                <Copy class="w-3.5 h-3.5" stroke-width="1.5" />
                Criar cópia editável
              </button>
            </template>

            <!-- Ações CUSTOMIZADO -->
            <template v-else>
              <button
                @click="deleteTemplate"
                :disabled="isDeleting"
                class="flex items-center gap-1.5 text-xs font-semibold text-ink-muted hover:text-red-500 transition-colors disabled:opacity-50"
              >
                <Loader2 v-if="isDeleting" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                <Trash2 v-else class="w-3.5 h-3.5" stroke-width="1.5" />
                Excluir template
              </button>

              <button
                @click="duplicateAsMine(editingTemplate)"
                class="flex items-center gap-1.5 text-xs font-semibold text-ink-muted hover:text-blue-600 transition-colors"
              >
                <Copy class="w-3.5 h-3.5" stroke-width="1.5" />
                Duplicar
              </button>

              <div class="ml-auto">
                <BaseButton variant="primary" @click="saveTemplate" :disabled="isSaving" class="px-5 h-9 font-bold gap-2">
                  <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" stroke-width="1.5" />
                  <Save v-else class="w-4 h-4" stroke-width="1.5" />
                  Salvar template
                </BaseButton>
              </div>
            </template>
          </div>

        </template>
      </div>
    </div>

    <!-- Card: Fases de Obra -->
    <TabFasesEAP />

  </div>

  <!-- ══ Modal: Novo Template ══ -->
  <Teleport to="body">
    <Transition name="fade-overlay">
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[120] flex items-center justify-center p-4"
        @click.self="showCreateModal = false"
      >
        <div class="bg-surface rounded-xl border border-hairline shadow-xl w-full max-w-md overflow-hidden">

          <!-- Modal header -->
          <div class="px-6 py-4 border-b border-hairline flex items-center justify-between">
            <h3 class="text-base font-bold text-ink">Criar novo template EAP</h3>
            <button @click="showCreateModal = false" class="p-1.5 rounded-lg hover:bg-canvas transition-colors text-ink-muted">
              <X class="w-4 h-4" stroke-width="1.5" />
            </button>
          </div>

          <div class="px-6 py-5 space-y-5">

            <!-- Nome -->
            <div>
              <label class="block text-xs font-semibold text-ink mb-1.5">Nome do template <span class="text-red-500">*</span></label>
              <input
                v-model="createForm.nome"
                type="text"
                placeholder="Ex: Residencial Alto Padrão 2025"
                class="w-full bg-canvas border border-hairline rounded-lg px-3 py-2.5 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all"
              />
            </div>

            <!-- Padrão -->
            <div>
              <label class="block text-xs font-semibold text-ink mb-1.5">Padrão de obra</label>
              <div class="flex gap-2">
                <button
                  v-for="(badge, key) in padraoBadge"
                  :key="key"
                  type="button"
                  @click="createForm.padrao_obra = key"
                  class="flex-1 py-2 rounded-lg border text-xs font-bold transition-all"
                  :class="createForm.padrao_obra === key
                    ? [badge.text, badge.bg, badge.border]
                    : 'text-ink-muted bg-transparent border-hairline hover:border-ink-muted'"
                >
                  {{ badge.label }}
                </button>
              </div>
            </div>

            <!-- Modo de início -->
            <div>
              <label class="block text-xs font-semibold text-ink mb-2">Como deseja começar?</label>
              <div class="space-y-2">
                <div
                  @click="createForm.mode = 'copy'"
                  class="flex items-start gap-3 p-3.5 rounded-lg border cursor-pointer transition-all"
                  :class="createForm.mode === 'copy'
                    ? 'border-blue-500/50 bg-blue-500/5'
                    : 'border-hairline hover:bg-canvas/60'"
                >
                  <div class="mt-0.5 w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors"
                    :class="createForm.mode === 'copy' ? 'border-blue-500' : 'border-neutral-400'">
                    <div v-if="createForm.mode === 'copy'" class="w-2 h-2 rounded-full bg-blue-500" />
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-ink">Copiar de um template existente</p>
                    <p class="text-xs text-ink-muted mt-0.5 leading-relaxed">
                      Começa com os itens do padrão
                      <strong>{{ padraoBadge[createForm.padrao_obra]?.label }}</strong> do sistema.
                      Ideal para ajustar fatores sem partir do zero.
                    </p>
                  </div>
                </div>

                <div
                  @click="createForm.mode = 'blank'"
                  class="flex items-start gap-3 p-3.5 rounded-lg border cursor-pointer transition-all"
                  :class="createForm.mode === 'blank'
                    ? 'border-orange-500/50 bg-orange-500/5'
                    : 'border-hairline hover:bg-canvas/60'"
                >
                  <div class="mt-0.5 w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors"
                    :class="createForm.mode === 'blank' ? 'border-orange-500' : 'border-neutral-400'">
                    <div v-if="createForm.mode === 'blank'" class="w-2 h-2 rounded-full bg-orange-500" />
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-ink">Começar do zero</p>
                    <p class="text-xs text-ink-muted mt-0.5 leading-relaxed">
                      Template em branco. Você adiciona cada serviço manualmente usando a busca SINAPI.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Info sobre default automático -->
            <div class="flex items-start gap-2 p-3 rounded-lg bg-amber-500/8 border border-amber-500/20">
              <Star class="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" fill="currentColor" stroke-width="0" />
              <p class="text-[11px] text-amber-700 leading-relaxed">
                Se não existir outro template ativo para o padrão
                <strong>{{ padraoBadge[createForm.padrao_obra]?.label }}</strong>,
                este será definido automaticamente como template ativo.
              </p>
            </div>

          </div>

          <!-- Modal footer -->
          <div class="px-6 py-4 border-t border-hairline flex items-center justify-end gap-2">
            <button
              type="button"
              @click="showCreateModal = false"
              class="h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink hover:bg-canvas rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="button"
              @click="createTemplate"
              :disabled="isCreating || !createForm.nome.trim()"
              class="h-9 px-5 text-sm font-bold text-white bg-orange-500 hover:bg-orange-600 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="isCreating" class="w-4 h-4 animate-spin" stroke-width="1.5" />
              <Plus v-else class="w-4 h-4" stroke-width="2" />
              Criar template
            </button>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-overlay-enter-active,
.fade-overlay-leave-active {
  transition: opacity 0.2s ease;
}
.fade-overlay-enter-from,
.fade-overlay-leave-to {
  opacity: 0;
}
</style>
