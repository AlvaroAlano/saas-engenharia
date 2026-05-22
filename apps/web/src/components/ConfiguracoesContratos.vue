<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const templates = ref([])
const activeTemplate = ref(null)
const isLoading = ref(true)
const isSaving = ref(false)

const variaveis = [
  { tag: '{{cliente_nome}}', label: 'Nome do Cliente' },
  { tag: '{{valor}}', label: 'Valor da Obra (R$)' },
  { tag: '{{tamanho}}', label: 'Tamanho (Área)' },
  { tag: '{{padrao}}', label: 'Padrão da Obra' }
]

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
    alert('Erro ao carregar a lista de modelos de contrato. Verifique a conexão com o banco.')
  } finally {
    isLoading.value = false
  }
}

const selectTemplate = async (id) => {
  if (id === 'new') {
    activeTemplate.value = {
      id: 'new',
      titulo: 'Novo Template',
      conteudo: 'Digite o conteúdo do contrato aqui...'
    }
    return
  }
  
  try {
    const { data } = await axios.get(`/contratos-templates/${id}`)
    activeTemplate.value = { ...data }
  } catch (error) {
    console.error('Erro ao selecionar template:', error)
    alert('Erro ao carregar os dados deste modelo.')
  }
}

const saveTemplate = async () => {
  isSaving.value = true
  try {
    if (activeTemplate.value.id === 'new') {
      const { data } = await axios.post('/contratos-templates', {
        titulo: activeTemplate.value.titulo,
        conteudo: activeTemplate.value.conteudo
      })
      await fetchTemplates()
      selectTemplate(data.data.id)
    } else {
      await axios.patch(`/contratos-templates/${activeTemplate.value.id}`, {
        titulo: activeTemplate.value.titulo,
        conteudo: activeTemplate.value.conteudo
      })
      await fetchTemplates()
    }
    alert('Template salvo com sucesso!')
  } catch (error) {
    console.error('Erro ao salvar template:', error)
    alert('Erro ao salvar o template. Verifique o console.')
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
    alert('Erro ao excluir template.')
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

  // Reposiciona o cursor logo após a tag inserida
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
        <div class="p-4 border-b border-hairline bg-canvas flex justify-between items-center">
          <h2 class="text-xs font-bold text-ink-muted uppercase tracking-wider">Templates Salvos</h2>
          <button @click="() => selectTemplate('new')" class="flex items-center gap-1 text-xs font-semibold text-brand-primary hover:bg-brand-primary/10 px-2 py-1 rounded-lg transition-colors cursor-pointer">
            <span class="material-symbols-outlined text-[16px]">add</span>
            Novo
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-3 space-y-1">
          <div v-if="isLoading" class="text-center py-6 text-ink-muted text-sm">Carregando...</div>
          <template v-else>
            <button 
              v-for="tpl in templates" 
              :key="tpl.id"
              @click="selectTemplate(tpl.id)"
              class="w-full text-left px-3 py-3 rounded-lg text-sm font-medium transition-all flex justify-between items-center group cursor-pointer"
              :class="activeTemplate?.id === tpl.id ? 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20' : 'text-ink-muted hover:bg-canvas border border-transparent'"
            >
              <span class="truncate pr-2">{{ tpl.titulo }}</span>
              <span class="material-symbols-outlined text-[16px] opacity-0 group-hover:opacity-100 transition-opacity">chevron_right</span>
            </button>
            <div v-if="templates.length === 0" class="text-center py-6 text-ink-muted text-sm italic">
              Nenhum template encontrado.
            </div>
          </template>
        </div>
      </aside>

      <!-- Main Editor -->
      <main class="flex-1 flex flex-col bg-canvas overflow-hidden" v-if="activeTemplate">
        <div class="flex-1 flex flex-col min-h-0 p-5">

          <div class="flex-1 flex flex-col min-h-0 bg-surface rounded-xl border border-hairline overflow-hidden">
            <div class="px-5 py-3.5 border-b border-hairline bg-canvas flex justify-between items-center shrink-0">
              <input 
                v-model="activeTemplate.titulo" 
                class="text-lg font-bold text-ink bg-transparent border-b-2 border-transparent focus:border-brand-primary focus:outline-none transition-colors w-1/2 px-1 py-0.5"
                placeholder="Título do Template"
              >
              <div class="flex gap-2">
                <button v-if="activeTemplate.id !== 'new'" @click="deleteTemplate(activeTemplate.id)" class="px-3 py-1.5 text-red-655 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg text-xs font-bold transition-colors border border-transparent hover:border-red-200 dark:hover:border-red-900 cursor-pointer">
                  Excluir
                </button>
                <button 
                  @click="saveTemplate" 
                  :disabled="isSaving"
                  class="bg-brand-primary hover:bg-brand-hover text-white px-4 py-1.5 rounded-lg font-bold text-sm flex items-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <span v-if="isSaving" class="material-symbols-outlined animate-spin text-[16px]">sync</span>
                  <span v-else class="material-symbols-outlined text-[16px]">save</span>
                  {{ isSaving ? 'Salvando...' : 'Salvar Template' }}
                </button>
              </div>
            </div>

            <!-- Informational Banner + Variables Panel -->
            <div class="px-5 py-4 border-b border-hairline bg-brand-primary/5 dark:bg-brand-primary/10 shrink-0">
              <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/30 rounded-lg p-3.5 flex gap-3 text-blue-800 dark:text-blue-200 text-xs mb-4">
                <span class="material-symbols-outlined shrink-0 text-blue-500 dark:text-blue-400 text-base">info</span>
                <p>
                  <strong>Como funciona:</strong> Crie seus modelos padrão de contrato abaixo. Clique nas variáveis para copiar e cole no texto. Na geração do documento, o sistema substituirá as tags pelos dados reais do cliente.
                </p>
              </div>
              <p class="text-xs font-bold text-brand-primary mb-2 uppercase tracking-wider flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">data_object</span> Variáveis Dinâmicas
              </p>
              <p class="text-xs text-ink-muted mb-3">Clique em uma tag para copiar e cole no corpo do texto.</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="variavel in variaveis"
                  :key="variavel.tag"
                  @click="insertTag(variavel.tag)"
                  class="bg-surface border border-brand-primary/30 text-brand-primary hover:bg-brand-primary hover:text-white px-2.5 py-1.5 rounded-md text-xs font-mono transition-colors flex items-center gap-1.5 group cursor-pointer"
                  title="Copiar tag"
                >
                  {{ variavel.tag }}
                  <span class="text-[10px] opacity-70 font-sans group-hover:text-white/80">({{ variavel.label }})</span>
                </button>
              </div>
            </div>

            <!-- Textarea: preenche o espaço restante do card -->
            <div class="flex-1 flex flex-col min-h-0 p-5">
              <textarea
                ref="textareaRef"
                v-model="activeTemplate.conteudo"
                class="flex-1 min-h-0 w-full p-4 bg-canvas border border-hairline text-ink rounded-lg focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none resize-none font-serif leading-relaxed"
                placeholder="Escreva o corpo do contrato aqui..."
              ></textarea>
            </div>
          </div>
        </div>
      </main>
      
      <div v-else class="flex-1 flex items-center justify-center bg-canvas">
        <div class="text-center text-ink-muted">
          <span class="material-symbols-outlined text-4xl mb-2 opacity-50">description</span>
          <p class="text-sm font-medium">Selecione um template na lateral ou crie um novo.</p>
        </div>
      </div>
    </div>
  </div>
</template>
