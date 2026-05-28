<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { Plus, ChevronRight, Loader2, Save, Info, Braces, FileText } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const { showToast } = useToast()

const templates = ref([])
const activeTemplate = ref(null)
const isLoading = ref(true)
const isSaving = ref(false)

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
  if (id === 'new-proposta' || id === 'new-contrato') {
    const tipo = id === 'new-contrato' ? 'contrato' : 'proposta'
    activeTemplate.value = {
      id: 'new',
      titulo: tipo === 'contrato' ? 'Novo Contrato de Construção' : 'Nova Proposta Comercial',
      conteudo: 'Digite o conteúdo aqui...',
      tipo,
    }
    return
  }

  try {
    const { data } = await axios.get(`/contratos-templates/${id}`)
    activeTemplate.value = { ...data }
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
        titulo: activeTemplate.value.titulo,
        conteudo: activeTemplate.value.conteudo,
        tipo: activeTemplate.value.tipo,
      })
      await fetchTemplates()
      selectTemplate(data.data.id)
    } else {
      await axios.patch(`/contratos-templates/${activeTemplate.value.id}`, {
        titulo: activeTemplate.value.titulo,
        conteudo: activeTemplate.value.conteudo,
        tipo: activeTemplate.value.tipo,
      })
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

const deleteTemplate = async (id) => {
  if (!confirm('Tem certeza que deseja excluir este template?')) return
  try {
    await axios.delete(`/contratos-templates/${id}`)
    activeTemplate.value = null
    await fetchTemplates()
  } catch (error) {
    console.error('Erro ao excluir template:', error)
    showToast('Erro ao excluir template.', 'error')
  }
}

const textareaRef = ref(null)

const insertTag = (tag) => {
  const el = textareaRef.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  const text = activeTemplate.value.conteudo
  activeTemplate.value.conteudo = text.slice(0, start) + tag + text.slice(end)
  const newPos = start + tag.length
  el.focus()
  requestAnimationFrame(() => {
    el.setSelectionRange(newPos, newPos)
  })
}

onMounted(() => {
  fetchTemplates()
})
</script>

<template>
  <div class="flex h-full flex-col font-sans text-ink">
    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-72 bg-surface border-r border-hairline flex flex-col shrink-0">
        <div v-if="isLoading" class="flex-1 flex items-center justify-center text-ink-muted text-sm">
          Carregando...
        </div>
        <template v-else>
          <!-- Grupo: Propostas Comerciais -->
          <div class="border-b border-hairline">
            <div class="px-4 py-2.5 bg-canvas flex justify-between items-center">
              <h2 class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Propostas Comerciais</h2>
              <button
                @click="selectTemplate('new-proposta')"
                class="flex items-center gap-1 text-xs font-semibold text-brand-primary hover:bg-brand-primary/10 px-2 py-1 rounded-lg transition-colors cursor-pointer"
              >
                <Plus class="w-3.5 h-3.5" stroke-width="1.5" />
                Nova
              </button>
            </div>
            <div class="p-2 space-y-1">
              <button
                v-for="tpl in templatesPropostas"
                :key="tpl.id"
                @click="selectTemplate(tpl.id)"
                class="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-all flex justify-between items-center group cursor-pointer"
                :class="activeTemplate?.id === tpl.id ? 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20' : 'text-ink-muted hover:bg-canvas border border-transparent'"
              >
                <span class="truncate pr-2">{{ tpl.titulo }}</span>
                <ChevronRight class="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" stroke-width="1.5" />
              </button>
              <p v-if="templatesPropostas.length === 0" class="text-center py-3 text-ink-muted text-xs italic">
                Nenhuma proposta criada.
              </p>
            </div>
          </div>

          <!-- Grupo: Contratos de Construção -->
          <div class="flex-1 flex flex-col overflow-hidden">
            <div class="px-4 py-2.5 bg-canvas flex justify-between items-center">
              <h2 class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Contratos de Construção</h2>
              <button
                @click="selectTemplate('new-contrato')"
                class="flex items-center gap-1 text-xs font-semibold text-brand-primary hover:bg-brand-primary/10 px-2 py-1 rounded-lg transition-colors cursor-pointer"
              >
                <Plus class="w-3.5 h-3.5" stroke-width="1.5" />
                Novo
              </button>
            </div>
            <div class="flex-1 overflow-y-auto p-2 space-y-1">
              <button
                v-for="tpl in templatesContratos"
                :key="tpl.id"
                @click="selectTemplate(tpl.id)"
                class="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-all flex justify-between items-center group cursor-pointer"
                :class="activeTemplate?.id === tpl.id ? 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20' : 'text-ink-muted hover:bg-canvas border border-transparent'"
              >
                <span class="truncate pr-2">{{ tpl.titulo }}</span>
                <ChevronRight class="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" stroke-width="1.5" />
              </button>
              <p v-if="templatesContratos.length === 0" class="text-center py-3 text-ink-muted text-xs italic">
                Nenhum contrato criado.
              </p>
            </div>
          </div>
        </template>
      </aside>

      <!-- Main Editor -->
      <main class="flex-1 flex flex-col bg-canvas overflow-hidden" v-if="activeTemplate">
        <div class="flex-1 flex flex-col min-h-0 p-5">
          <div class="flex-1 flex flex-col min-h-0 bg-surface rounded-xl border border-hairline overflow-hidden">
            <div class="px-5 py-3.5 border-b border-hairline bg-canvas flex justify-between items-center shrink-0">
              <div class="flex items-center gap-3 w-1/2">
                <input
                  v-model="activeTemplate.titulo"
                  class="text-lg font-bold text-ink bg-transparent border-b-2 border-transparent focus:border-brand-primary focus:outline-none transition-colors flex-1 px-1 py-0.5"
                  placeholder="Título do Template"
                >
                <span
                  class="shrink-0 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
                  :class="activeTemplate.tipo === 'contrato' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'"
                >
                  {{ activeTemplate.tipo === 'contrato' ? 'Contrato' : 'Proposta' }}
                </span>
              </div>
              <div class="flex gap-2">
                <button
                  v-if="activeTemplate.id !== 'new'"
                  @click="deleteTemplate(activeTemplate.id)"
                  class="px-3 py-1.5 text-red-655 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg text-xs font-bold transition-colors border border-transparent hover:border-red-200 dark:hover:border-red-900 cursor-pointer"
                >
                  Excluir
                </button>
                <button
                  @click="saveTemplate"
                  :disabled="isSaving"
                  class="bg-brand-primary hover:bg-brand-hover text-white px-4 py-1.5 rounded-lg font-bold text-sm flex items-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" stroke-width="1.5" />
                  <Save v-else class="w-4 h-4" stroke-width="1.5" />
                  {{ isSaving ? 'Salvando...' : 'Salvar Template' }}
                </button>
              </div>
            </div>

            <!-- Informational Banner + Variables Panel -->
            <div class="px-5 py-4 border-b border-hairline bg-brand-primary/5 dark:bg-brand-primary/10 shrink-0">
              <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/30 rounded-lg p-3.5 flex gap-3 text-blue-800 dark:text-blue-200 text-xs mb-4">
                <Info class="w-4 h-4 shrink-0 text-blue-500 dark:text-blue-400" stroke-width="1.5" />
                <p>
                  <strong>Como funciona:</strong> Crie seus modelos padrão abaixo. Clique nas variáveis para inserir no texto — o sistema as substituirá pelos dados reais do cliente na hora da geração do documento.
                  <template v-if="activeTemplate.tipo === 'contrato'">
                    Variáveis <strong>SINAPI</strong> exigem que o projeto tenha itens de orçamento preenchidos.
                  </template>
                </p>
              </div>
              <p class="text-xs font-bold text-brand-primary mb-2 uppercase tracking-wider flex items-center gap-1">
                <Braces class="w-3.5 h-3.5" stroke-width="1.5" />
                Variáveis para {{ activeTemplate.tipo === 'contrato' ? 'Contratos de Construção' : 'Propostas Comerciais' }}
              </p>
              <p class="text-xs text-ink-muted mb-3">Clique em uma tag para inserir no corpo do texto.</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="variavel in variaveis"
                  :key="variavel.tag"
                  @click="insertTag(variavel.tag)"
                  class="bg-surface border border-brand-primary/30 text-brand-primary hover:bg-brand-primary hover:text-white px-2.5 py-1.5 rounded-md text-xs font-mono transition-colors flex items-center gap-1.5 group cursor-pointer"
                  title="Inserir no texto"
                >
                  {{ variavel.tag }}
                  <span class="text-[10px] opacity-70 font-sans group-hover:text-white/80">({{ variavel.label }})</span>
                </button>
              </div>
            </div>

            <!-- Textarea -->
            <div class="flex-1 flex flex-col min-h-0 p-5">
              <textarea
                ref="textareaRef"
                v-model="activeTemplate.conteudo"
                class="flex-1 min-h-0 w-full p-4 bg-canvas border border-hairline text-ink rounded-lg focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none resize-none font-serif leading-relaxed"
                placeholder="Escreva o corpo do documento aqui..."
              ></textarea>
            </div>
          </div>
        </div>
      </main>

      <div v-else class="flex-1 flex items-center justify-center bg-canvas">
        <div class="text-center text-ink-muted flex flex-col items-center justify-center">
          <FileText class="w-12 h-12 mb-3 opacity-40 text-ink-muted" stroke-width="1.5" />
          <p class="text-sm font-medium">Selecione um template na lateral ou crie um novo.</p>
        </div>
      </div>
    </div>
  </div>
</template>
