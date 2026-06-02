<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { Plus, ChevronRight, Loader2, Save, Info, Braces, FileText, Copy, Menu, X as IconX, Eye } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const { showToast } = useToast()

const templates = ref([])
const activeTemplate = ref(null)
const originalTemplate = ref(null) // snapshot para detectar mudanças não salvas
const isLoading = ref(true)
const isSaving = ref(false)

// Modal de confirmação de exclusão
const deleteModal = ref({ isOpen: false, isDeleting: false, id: null, titulo: '' })

// Guard de mudanças não salvas
const isDirty = computed(() =>
  activeTemplate.value &&
  originalTemplate.value &&
  (activeTemplate.value.titulo   !== originalTemplate.value.titulo ||
   activeTemplate.value.conteudo !== originalTemplate.value.conteudo)
)

const VARIAVEIS_PROPOSTA = [
  { tag: '{{cliente_nome}}', label: 'Nome do Cliente' },
  { tag: '{{valor}}', label: 'Valor da Obra (R$)' },
  { tag: '{{tamanho}}', label: 'Tamanho (Área)' },
  { tag: '{{padrao}}', label: 'Padrão da Obra' },
]

const VARIAVEIS_CONTRATO = [
  { tag: '{{cliente_nome}}', label: 'Nome do Cliente' },
  { tag: '{{tamanho}}', label: 'Tamanho (Área)' },
  { tag: '{{padrao}}', label: 'Padrão da Obra' },
  { tag: '{{valor_total_sinapi}}', label: 'Total SINAPI c/ BDI' },
  { tag: '{{mes_referencia_sinapi}}', label: 'Mês de Referência SINAPI' },
  { tag: '{{bdi}}', label: 'BDI (%)' },
  { tag: '{{valor_por_m2_sinapi}}', label: 'Valor por m² (SINAPI)' },
]

const variaveis = computed(() =>
  activeTemplate.value?.tipo === 'contrato' ? VARIAVEIS_CONTRATO : VARIAVEIS_PROPOSTA
)

const templatesPropostas = computed(() => templates.value.filter(t => t.tipo !== 'contrato'))
const templatesContratos = computed(() => templates.value.filter(t => t.tipo === 'contrato'))

const fetchTemplates = async () => {
  isLoading.value = true
  try {
    const { data } = await axios.get('/contratos-templates')
    templates.value = data
    if (data.length > 0 && !activeTemplate.value) {
      selectTemplate(data[0].id)
    }
  } catch (error) {
    console.error('Erro ao buscar templates:', error)
    showToast('Erro ao carregar modelos de contrato.', 'error')
  } finally {
    isLoading.value = false
  }
}

const selectTemplate = async (id) => {
  // Guard: avisa se há mudanças não salvas
  if (isDirty.value) {
    if (!window.confirm('Você tem alterações não salvas. Deseja continuar sem salvar?')) return
  }

  if (id === 'new-proposta' || id === 'new-contrato') {
    const tipo = id === 'new-contrato' ? 'contrato' : 'proposta'
    const draft = {
      id: 'new',
      titulo: tipo === 'contrato' ? 'Novo Contrato de Construção' : 'Nova Proposta Comercial',
      conteudo: 'Digite o conteúdo aqui...',
      tipo,
    }
    activeTemplate.value  = { ...draft }
    originalTemplate.value = { ...draft }
    return
  }

  try {
    const { data } = await axios.get(`/contratos-templates/${id}`)
    activeTemplate.value   = { ...data }
    originalTemplate.value = { ...data }
  } catch (error) {
    console.error('Erro ao selecionar template:', error)
    showToast('Erro ao carregar os dados deste modelo.', 'error')
  }
}

const saveTemplate = async () => {
  isSaving.value = true
  try {
    if (activeTemplate.value.id === 'new') {
      const { data } = await axios.post('/contratos-templates', {
        titulo:   activeTemplate.value.titulo,
        conteudo: activeTemplate.value.conteudo,
        tipo:     activeTemplate.value.tipo,
      })
      await fetchTemplates()
      selectTemplate(data.data.id)
    } else {
      await axios.patch(`/contratos-templates/${activeTemplate.value.id}`, {
        titulo:   activeTemplate.value.titulo,
        conteudo: activeTemplate.value.conteudo,
        tipo:     activeTemplate.value.tipo,
      })
      // Reseta snapshot após salvar
      originalTemplate.value = { ...activeTemplate.value }
      await fetchTemplates()
    }
    showToast('Template salvo com sucesso!', 'success')
  } catch (error) {
    console.error('Erro ao salvar template:', error)
    showToast('Erro ao salvar o template.', 'error')
  } finally {
    isSaving.value = false
  }
}

// Abre modal de confirmação de exclusão
const abrirModalExclusao = (id, titulo) => {
  deleteModal.value = { isOpen: true, isDeleting: false, id, titulo }
}

const confirmarExclusao = async () => {
  deleteModal.value.isDeleting = true
  const id = deleteModal.value.id
  try {
    await axios.delete(`/contratos-templates/${id}`)
    deleteModal.value.isOpen = false
    activeTemplate.value   = null
    originalTemplate.value = null
    await fetchTemplates()
    // Auto-seleciona o primeiro template disponível
    if (templates.value.length > 0) selectTemplate(templates.value[0].id)
    showToast('Template excluído.', 'success')
  } catch (error) {
    console.error('Erro ao excluir template:', error)
    showToast('Erro ao excluir template.', 'error')
    deleteModal.value.isDeleting = false
  }
}

const textareaRef = ref(null)

const insertTag = (tag) => {
  const el = textareaRef.value
  if (!el) return
  // Se o textarea não está focado, insere no final do conteúdo
  const isFocused = document.activeElement === el
  const start = isFocused ? el.selectionStart : (activeTemplate.value.conteudo?.length ?? 0)
  const end   = isFocused ? el.selectionEnd   : start
  const text = activeTemplate.value.conteudo ?? ''
  activeTemplate.value.conteudo = text.slice(0, start) + tag + text.slice(end)
  const newPos = start + tag.length
  el.focus()
  requestAnimationFrame(() => el.setSelectionRange(newPos, newPos))
}

// ─── Preview com dados fictícios ─────────────────────────────────────────────
const showPreview = ref(false)

const PREVIEW_VALUES = {
  '{{cliente_nome}}':         'Carlos Eduardo Silva',
  '{{valor}}':                'R$ 385.000,00',
  '{{tamanho}}':              '145 m²',
  '{{padrao}}':               'Médio Padrão',
  '{{valor_total_sinapi}}':   'R$ 312.450,00',
  '{{mes_referencia_sinapi}}':'03/2026',
  '{{bdi}}':                  '25%',
  '{{valor_por_m2_sinapi}}':  'R$ 2.155,00',
}

const previewContent = computed(() => {
  if (!activeTemplate.value?.conteudo) return ''
  return Object.entries(PREVIEW_VALUES).reduce(
    (text, [tag, val]) => text.replaceAll(tag, `<mark class="bg-brand-orange/20 text-brand-orange rounded px-0.5 not-italic">${val}</mark>`),
    activeTemplate.value.conteudo
  )
})

// ─── Mobile sidebar ──────────────────────────────────────────────────────────
const sidebarOpen = ref(false)

const abrirSidebar = () => { sidebarOpen.value = true }
const fecharSidebar = () => { sidebarOpen.value = false }

const selectTemplateAndClose = (id) => {
  selectTemplate(id)
  fecharSidebar()
}

// ─── Duplicar template ────────────────────────────────────────────────────────
const isDuplicating = ref(false)

const duplicarTemplate = async () => {
  if (!activeTemplate.value || activeTemplate.value.id === 'new') return
  isDuplicating.value = true
  try {
    const { data } = await axios.post('/contratos-templates', {
      titulo:   `Cópia de ${activeTemplate.value.titulo}`,
      conteudo: activeTemplate.value.conteudo,
      tipo:     activeTemplate.value.tipo,
    })
    await fetchTemplates()
    selectTemplate(data.data.id)
    showToast('Template duplicado!', 'success')
  } catch (error) {
    console.error('Erro ao duplicar template:', error)
    showToast('Erro ao duplicar template.', 'error')
  } finally {
    isDuplicating.value = false
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>

<template>
  <div class="flex h-full flex-col font-sans text-ink">

    <!-- ── Barra superior mobile ──────────────────────────────────────── -->
    <div class="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-hairline bg-surface shrink-0">
      <button
        @click="abrirSidebar"
        class="p-2 rounded-lg hover:bg-canvas transition-colors cursor-pointer text-ink-muted hover:text-ink"
      >
        <Menu class="w-5 h-5" stroke-width="1.5" />
      </button>
      <span class="text-sm font-semibold text-ink truncate flex-1">
        {{ activeTemplate?.titulo || 'Modelos de Contrato' }}
      </span>
      <span v-if="isDirty" class="text-[10px] font-semibold text-brand-orange bg-brand-orange/10 px-2 py-0.5 rounded-full shrink-0">
        Não salvo
      </span>
    </div>

    <div class="flex flex-1 overflow-hidden relative">

      <!-- Overlay mobile -->
      <Transition enter-active-class="transition-opacity duration-300" enter-from-class="opacity-0" enter-to-class="opacity-100" leave-active-class="transition-opacity duration-200" leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="sidebarOpen" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 lg:hidden" @click="fecharSidebar" />
      </Transition>

      <!-- ── Sidebar ──────────────────────────────────────────────────── -->
      <aside
        class="bg-surface border-r border-hairline flex flex-col shrink-0 transition-transform duration-300 ease-in-out
               fixed inset-y-0 left-0 z-50 w-72
               lg:relative lg:inset-auto lg:z-auto lg:translate-x-0"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
      >
        <!-- Header mobile do drawer -->
        <div class="lg:hidden flex items-center justify-between px-4 py-3 border-b border-hairline bg-canvas shrink-0">
          <span class="text-xs font-bold text-ink-muted uppercase tracking-wider">Modelos</span>
          <button @click="fecharSidebar" class="p-1.5 rounded-lg hover:bg-surface-hover transition-colors cursor-pointer text-ink-muted">
            <IconX class="w-4 h-4" stroke-width="1.5" />
          </button>
        </div>
        <div v-if="isLoading" class="flex-1 flex items-center justify-center">
          <Loader2 class="w-6 h-6 animate-spin text-brand-primary" stroke-width="1.5" />
        </div>

        <template v-else>
          <!-- Propostas Comerciais -->
          <div class="border-b border-hairline">
            <div class="px-4 py-2.5 bg-canvas flex justify-between items-center">
              <h2 class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Propostas Comerciais</h2>
              <button
                @click="selectTemplate('new-proposta')"
                class="flex items-center gap-1 text-xs font-semibold text-brand-primary hover:bg-brand-primary/10 px-2 py-1 rounded-lg transition-colors cursor-pointer"
              >
                <Plus class="w-3.5 h-3.5" stroke-width="1.5" /> Nova
              </button>
            </div>
            <div class="p-2 space-y-1">
              <button
                v-for="tpl in templatesPropostas" :key="tpl.id"
                @click="selectTemplateAndClose(tpl.id)"
                class="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-all flex justify-between items-center group cursor-pointer"
                :class="activeTemplate?.id === tpl.id
                  ? 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20'
                  : 'text-ink-muted hover:bg-canvas border border-transparent'"
              >
                <span class="truncate pr-2 flex items-center gap-1.5">
                  {{ tpl.titulo }}
                  <span v-if="activeTemplate?.id === tpl.id && isDirty" class="w-1.5 h-1.5 rounded-full bg-brand-orange shrink-0" title="Alterações não salvas" />
                </span>
                <ChevronRight class="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" stroke-width="1.5" />
              </button>
              <div v-if="templatesPropostas.length === 0" class="py-4 text-center">
                <p class="text-xs text-ink-muted mb-2">Nenhuma proposta criada.</p>
                <button @click="selectTemplate('new-proposta')" class="text-xs font-semibold text-brand-primary hover:underline cursor-pointer">
                  Criar primeira proposta →
                </button>
              </div>
            </div>
          </div>

          <!-- Contratos de Construção -->
          <div class="flex-1 flex flex-col overflow-hidden">
            <div class="px-4 py-2.5 bg-canvas flex justify-between items-center">
              <h2 class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Contratos de Construção</h2>
              <button
                @click="selectTemplate('new-contrato')"
                class="flex items-center gap-1 text-xs font-semibold text-brand-primary hover:bg-brand-primary/10 px-2 py-1 rounded-lg transition-colors cursor-pointer"
              >
                <Plus class="w-3.5 h-3.5" stroke-width="1.5" /> Novo
              </button>
            </div>
            <div class="flex-1 overflow-y-auto p-2 space-y-1">
              <button
                v-for="tpl in templatesContratos" :key="tpl.id"
                @click="selectTemplateAndClose(tpl.id)"
                class="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-all flex justify-between items-center group cursor-pointer"
                :class="activeTemplate?.id === tpl.id
                  ? 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20'
                  : 'text-ink-muted hover:bg-canvas border border-transparent'"
              >
                <span class="truncate pr-2 flex items-center gap-1.5">
                  {{ tpl.titulo }}
                  <span v-if="activeTemplate?.id === tpl.id && isDirty" class="w-1.5 h-1.5 rounded-full bg-brand-orange shrink-0" title="Alterações não salvas" />
                </span>
                <ChevronRight class="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" stroke-width="1.5" />
              </button>
              <div v-if="templatesContratos.length === 0" class="py-4 text-center">
                <p class="text-xs text-ink-muted mb-2">Nenhum contrato criado.</p>
                <button @click="selectTemplate('new-contrato')" class="text-xs font-semibold text-brand-primary hover:underline cursor-pointer">
                  Criar primeiro contrato →
                </button>
              </div>
            </div>
          </div>
        </template>
      </aside>

      <!-- ── Editor Principal ──────────────────────────────────────────── -->
      <main v-if="activeTemplate" class="flex-1 flex flex-col bg-canvas overflow-hidden">
        <div class="flex-1 flex flex-col min-h-0 p-5">
          <div class="flex-1 flex flex-col min-h-0 bg-surface rounded-xl border border-hairline overflow-hidden">

            <!-- Toolbar -->
            <div class="px-5 py-3.5 border-b border-hairline bg-canvas flex justify-between items-center shrink-0 gap-3">
              <div class="flex items-center gap-3 min-w-0">
                <input
                  v-model="activeTemplate.titulo"
                  class="text-lg font-bold text-ink bg-transparent border-b-2 border-transparent focus:border-brand-primary focus:outline-none transition-colors flex-1 px-1 py-0.5 min-w-0"
                  placeholder="Título do Template"
                />
                <span
                  class="shrink-0 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
                  :class="activeTemplate.tipo === 'contrato'
                    ? 'bg-brand-blue/10 text-brand-blue'
                    : 'bg-brand-orange/10 text-brand-orange'"
                >
                  {{ activeTemplate.tipo === 'contrato' ? 'Contrato' : 'Proposta' }}
                </span>
                <!-- Indicador não salvo -->
                <span
                  v-if="isDirty"
                  class="shrink-0 text-[10px] font-semibold text-brand-orange bg-brand-orange/10 px-2 py-0.5 rounded-full"
                >
                  Não salvo
                </span>
              </div>
              <div class="flex gap-2 shrink-0">
                <!-- Pré-visualizar -->
                <button
                  v-if="activeTemplate.conteudo?.trim()"
                  @click="showPreview = true"
                  class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold border border-hairline text-ink-muted hover:text-ink hover:bg-canvas transition-colors cursor-pointer"
                  title="Pré-visualizar com dados de exemplo"
                >
                  <Eye class="w-3.5 h-3.5" stroke-width="1.5" />
                  Preview
                </button>
                <!-- Duplicar -->
                <button
                  v-if="activeTemplate.id !== 'new'"
                  @click="duplicarTemplate"
                  :disabled="isDuplicating"
                  class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold border border-hairline text-ink-muted hover:text-ink hover:bg-canvas transition-colors cursor-pointer disabled:opacity-50"
                  title="Duplicar template"
                >
                  <Copy class="w-3.5 h-3.5" stroke-width="1.5" />
                  Duplicar
                </button>
                <!-- Excluir -->
                <button
                  v-if="activeTemplate.id !== 'new'"
                  @click="abrirModalExclusao(activeTemplate.id, activeTemplate.titulo)"
                  class="px-3 py-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg text-xs font-bold transition-colors border border-transparent hover:border-red-200 dark:hover:border-red-900 cursor-pointer"
                >
                  Excluir
                </button>
                <!-- Salvar -->
                <button
                  @click="saveTemplate"
                  :disabled="isSaving"
                  class="bg-brand-primary hover:bg-brand-hover text-white px-4 py-1.5 rounded-lg font-bold text-sm flex items-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" stroke-width="1.5" />
                  <Save v-else class="w-4 h-4" stroke-width="1.5" />
                  <span class="hidden sm:inline">{{ isSaving ? 'Salvando...' : 'Salvar Template' }}</span>
                </button>
              </div>
            </div>

            <!-- Painel de Variáveis -->
            <div class="px-5 py-4 border-b border-hairline bg-canvas/50 shrink-0">
              <div class="bg-brand-blue/5 border border-brand-blue/15 rounded-lg p-3.5 flex gap-3 text-xs mb-4">
                <Info class="w-4 h-4 shrink-0 text-brand-blue mt-0.5" stroke-width="1.5" />
                <p class="text-ink-muted leading-relaxed">
                  <strong class="text-ink">Como funciona:</strong> Clique nas variáveis abaixo para inserí-las no texto. O sistema as substituirá pelos dados reais do cliente ao gerar o documento.
                  <template v-if="activeTemplate.tipo === 'contrato'">
                    Variáveis <strong>SINAPI</strong> exigem itens de orçamento preenchidos no projeto.
                  </template>
                </p>
              </div>
              <p class="text-xs font-bold text-brand-primary mb-2 uppercase tracking-wider flex items-center gap-1">
                <Braces class="w-3.5 h-3.5" stroke-width="1.5" />
                Variáveis — {{ activeTemplate.tipo === 'contrato' ? 'Contratos de Construção' : 'Propostas Comerciais' }}
              </p>
              <div class="flex flex-wrap gap-2 mt-2">
                <button
                  v-for="variavel in variaveis" :key="variavel.tag"
                  @click="insertTag(variavel.tag)"
                  class="bg-surface border border-brand-primary/25 text-brand-primary hover:bg-brand-primary hover:text-white px-2.5 py-1.5 rounded-md text-xs font-mono transition-colors flex items-center gap-1.5 group cursor-pointer"
                  :title="`Inserir: ${variavel.tag}`"
                >
                  {{ variavel.tag }}
                  <span class="text-[10px] opacity-60 font-sans group-hover:opacity-90">({{ variavel.label }})</span>
                </button>
              </div>
            </div>

            <!-- Textarea -->
            <div class="flex-1 flex flex-col min-h-0 p-5">
              <textarea
                ref="textareaRef"
                v-model="activeTemplate.conteudo"
                class="flex-1 min-h-0 w-full p-4 bg-canvas border border-hairline text-ink rounded-lg focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none resize-none font-serif leading-relaxed text-sm"
                placeholder="Escreva o corpo do documento aqui..."
              />
            </div>
          </div>
        </div>
      </main>

      <!-- Empty state do editor -->
      <div v-else class="flex-1 flex items-center justify-center bg-canvas">
        <div class="text-center text-ink-muted flex flex-col items-center">
          <FileText class="w-12 h-12 mb-3 opacity-30" stroke-width="1.5" />
          <p class="text-sm font-semibold text-ink mb-1">Nenhum template selecionado</p>
          <p class="text-xs text-ink-muted">Selecione um modelo na lateral ou crie um novo.</p>
          <button @click="abrirSidebar" class="lg:hidden mt-3 text-xs font-semibold text-brand-primary hover:underline cursor-pointer">
            Abrir lista de modelos →
          </button>
        </div>
      </div>

    </div>

    <!-- ── Modal de Preview ─────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showPreview"
          class="fixed inset-0 z-[120] bg-black/50 backdrop-blur-sm flex items-start justify-center p-4 sm:p-8 overflow-y-auto"
          @click.self="showPreview = false"
        >
          <div class="bg-surface border border-hairline rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden my-4">

            <!-- Header do preview -->
            <div class="px-6 py-4 border-b border-hairline flex items-center justify-between bg-canvas sticky top-0 z-10">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-brand-blue/10 flex items-center justify-center">
                  <Eye class="w-4 h-4 text-brand-blue" stroke-width="1.5" />
                </div>
                <div>
                  <h3 class="text-sm font-bold text-ink">Pré-visualização</h3>
                  <p class="text-xs text-ink-muted">Valores em <mark class="bg-brand-orange/20 text-brand-orange rounded px-0.5 not-italic font-semibold">laranja</mark> são exemplos fictícios</p>
                </div>
              </div>
              <button
                @click="showPreview = false"
                class="p-2 rounded-xl text-ink-muted hover:bg-surface-hover hover:text-ink transition-colors cursor-pointer"
              >
                <IconX class="w-5 h-5" stroke-width="1.5" />
              </button>
            </div>

            <!-- Conteúdo renderizado -->
            <div class="p-8 sm:p-12">
              <!-- Título do template -->
              <h2 class="text-xl font-bold text-ink mb-6 pb-4 border-b border-hairline">
                {{ activeTemplate.titulo }}
              </h2>
              <!-- Corpo com variáveis destacadas -->
              <div
                class="text-sm text-ink font-serif leading-loose whitespace-pre-wrap"
                v-html="previewContent"
              />
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 bg-canvas border-t border-hairline flex items-center justify-between gap-4">
              <p class="text-xs text-ink-muted">Este é apenas um preview — os dados reais são preenchidos na geração do documento.</p>
              <button @click="showPreview = false" class="px-4 py-2 rounded-xl bg-brand-primary hover:bg-brand-hover text-white text-sm font-bold transition-colors cursor-pointer shrink-0">
                Fechar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Modal de Confirmação de Exclusão ─────────────────────────── -->
    <Teleport to="body">
      <Transition enter-active-class="transition-all duration-200 ease-out" enter-from-class="opacity-0 scale-95" enter-to-class="opacity-100 scale-100" leave-active-class="transition-all duration-150 ease-in" leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
        <div
          v-if="deleteModal.isOpen"
          class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          @click.self="deleteModal.isOpen = false"
        >
          <div class="bg-surface rounded-2xl border border-hairline shadow-2xl w-full max-w-sm overflow-hidden">
            <div class="px-6 py-4 border-b border-hairline bg-red-50 dark:bg-red-950/20 flex items-center gap-3">
              <div class="w-9 h-9 rounded-xl bg-red-100 dark:bg-red-900/40 flex items-center justify-center shrink-0">
                <FileText class="w-4.5 h-4.5 text-red-600" stroke-width="1.5" />
              </div>
              <div>
                <h3 class="text-sm font-bold text-ink">Excluir template</h3>
                <p class="text-xs text-red-600 font-semibold mt-0.5">Esta ação não pode ser desfeita</p>
              </div>
            </div>
            <div class="px-6 py-4">
              <p class="text-sm text-ink-muted">O template <strong class="text-ink">"{{ deleteModal.titulo }}"</strong> será excluído permanentemente.</p>
            </div>
            <div class="px-6 py-4 bg-canvas border-t border-hairline flex items-center justify-end gap-3">
              <button @click="deleteModal.isOpen = false" :disabled="deleteModal.isDeleting" class="px-4 py-2 rounded-lg text-sm font-semibold text-ink-muted hover:text-ink hover:bg-surface-hover transition-colors cursor-pointer disabled:opacity-50">
                Cancelar
              </button>
              <button @click="confirmarExclusao" :disabled="deleteModal.isDeleting" class="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-bold transition-colors cursor-pointer disabled:opacity-60">
                <Loader2 v-if="deleteModal.isDeleting" class="w-4 h-4 animate-spin" stroke-width="1.5" />
                {{ deleteModal.isDeleting ? 'Excluindo...' : 'Sim, excluir' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>
