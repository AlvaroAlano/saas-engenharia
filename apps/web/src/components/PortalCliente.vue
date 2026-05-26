<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useToast } from '../composables/useToast'
import { forceLightMode } from '../composables/useTheme'
import { supabase } from '../supabase'
import Caixometro from './Caixometro.vue'
import {
  IdCard,
  Building,
  Users,
  Clock,
  XCircle,
  CheckCircle2,
  Ruler,
  FileText,
  Home,
  File,
  Layers,
  Lock,
  AlertTriangle,
  Eye,
  Loader2,
  Trash2,
  Upload,
  Send,
  Hourglass,
  Activity,
  User,
  Landmark,
  FolderOpen,
  Download,
  HardHat,
  Shield
} from 'lucide-vue-next'

const iconMap = {
  badge: IdCard,
  home_work: Building,
  family_restroom: Users
}

const route = useRoute()
const token = route.params.token
const { showToast } = useToast()

const arquivosCorrigidos = ref({
  identidade: null,
  residencia: null,
  estado_civil: null
})
const isEnviandoCorrecoes = ref(false)

const categoriasDocsB2C = [
  { id: 'identidade', label: 'Identidade (RG/CNH)', icon: 'badge', description: 'RG ou CNH legível (frente e verso)' },
  { id: 'residencia', label: 'Comprovante de Residência', icon: 'home_work', description: 'Conta de água, luz ou gás recente' },
  { id: 'estado_civil', label: 'Certidão de Estado Civil', icon: 'family_restroom', description: 'Certidão de Nascimento ou Casamento' }
]

const getDocumentStatusInfo = (categoria) => {
  if (!projetoData.value || !projetoData.value.documentos) {
    return { status: 'pendente', label: 'Pendente', icon: Clock, badgeClass: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300' }
  }
  const doc = projetoData.value.documentos.find(d => d.categoria === categoria)
  if (!doc) {
    return { status: 'pendente', label: 'Pendente', icon: Clock, badgeClass: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300' }
  }
  if (doc.status === 'rejeitado') {
    return { status: 'rejeitado', label: 'Recusado', icon: XCircle, badgeClass: 'bg-red-50 text-red-600 border border-red-100 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900/30', motivo: doc.motivo }
  }
  if (doc.url) {
    return { status: 'aprovado', label: 'Aprovado', icon: CheckCircle2, badgeClass: 'bg-emerald-50 text-emerald-600 border border-emerald-100 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30', filename: doc.name }
  }
  return { status: 'pendente', label: 'Pendente', icon: Clock, badgeClass: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300' }
}

const handleFileSelect = (event, categoria) => {
  const file = event.target.files[0]
  if (file) {
    arquivosCorrigidos.value[categoria] = file
  }
}

const removerArquivoSelecionado = (categoria) => {
  arquivosCorrigidos.value[categoria] = null
  const input = document.getElementById(`file-input-${categoria}`)
  if (input) input.value = ''
}

const temArquivosSelecionados = computed(() => {
  return Object.values(arquivosCorrigidos.value).some(f => f !== null)
})

const enviarDocumentosCorrigidos = async () => {
  if (!temArquivosSelecionados.value) return
  isEnviandoCorrecoes.value = true
  
  try {
    const novosDocumentos = [...(projetoData.value.documentos || [])]
    
    for (const cat of ['identidade', 'residencia', 'estado_civil']) {
      const file = arquivosCorrigidos.value[cat]
      if (file) {
        const cleanFileName = file.name.replace(/[^\w.-]/g, '_')
        const filePath = `${projetoData.value.id}/${cat}/${cleanFileName}`
        
        const { error } = await supabase.storage
          .from('documentos_clientes')
          .upload(filePath, file, { upsert: true })
          
        if (error) throw new Error(`Falha no armazenamento do documento (${cat}): ${error.message}`)
        
        const { data: urlData } = supabase.storage
          .from('documentos_clientes')
          .getPublicUrl(filePath)
          
        const index = novosDocumentos.findIndex(d => d.categoria === cat)
        const novoDoc = {
          categoria: cat,
          name: file.name,
          url: urlData.publicUrl,
          done: true
        }
        if (index !== -1) {
          novosDocumentos[index] = novoDoc
        } else {
          novosDocumentos.push(novoDoc)
        }
      }
    }
    
    const todosValidos = ['identidade', 'residencia', 'estado_civil'].every(cat => {
      const doc = novosDocumentos.find(d => d.categoria === cat)
      return doc && doc.url && doc.status !== 'rejeitado'
    })
    
    const novoStatus = todosValidos ? 'docs_completos' : 'docs_pendentes'
    
    const apiResponse = await axios.patch(`/matchmaking/projetos/${projetoData.value.id}`, {
      documentos: novosDocumentos,
      status: novoStatus
    })
    
    if (apiResponse.data.success || apiResponse.status === 200) {
      showToast('Documentos enviados com sucesso!', 'success')
      arquivosCorrigidos.value = { identidade: null, residencia: null, estado_civil: null }
      projetoData.value.documentos = novosDocumentos
      projetoData.value.status = novoStatus
    } else {
      throw new Error('Servidor não confirmou o envio dos documentos.')
    }
  } catch (error) {
    console.error('Erro no reenvio de documentos:', error)
    showToast(error.message || 'Erro ao enviar documentos. Tente novamente.', 'error')
  } finally {
    isEnviandoCorrecoes.value = false
  }
}

onMounted(() => {
  forceLightMode()
})

// --- Estados da Página ---
const currentState = ref('pin')  // 'pin' | 'loading' | 'success' | 'error'
const pinDigits = ref(['', '', '', ''])
const errorMessage = ref('')
const projetoData = ref(null)

// --- Estados das Abas do Portal ---
const activeTab = ref('feed')
const feedData = ref([])
const documentosData = ref([])
const caixaData = ref(null)
const isLoadingTabs = ref(false)

const tabs = [
  { id: 'feed', label: 'Diário de Obra' },
  { id: 'caixa', label: 'Evolução Caixa' },
  { id: 'documentos', label: 'Documentos' },
  { id: 'detalhes', label: 'Dados da Obra' }
]

// PIN completo montado a partir dos 4 inputs
const pinCompleto = computed(() => pinDigits.value.join(''))
const isPinComplete = computed(() => pinCompleto.value.length === 4 && /^\d{4}$/.test(pinCompleto.value))

// --- Lógica dos Inputs do PIN ---
const focusNext = (index) => {
  const value = pinDigits.value[index]
  // Aceita apenas dígitos
  if (value && !/^\d$/.test(value)) {
    pinDigits.value[index] = ''
    return
  }
  // Avança para o próximo input
  if (value && index < 3) {
    const next = document.getElementById(`pin-${index + 1}`)
    if (next) next.focus()
  }
}

const handleBackspace = (index, event) => {
  if (event.key === 'Backspace' && !pinDigits.value[index] && index > 0) {
    const prev = document.getElementById(`pin-${index - 1}`)
    if (prev) prev.focus()
  }
}

const handlePaste = (event) => {
  event.preventDefault()
  const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 4)
  for (let i = 0; i < 4; i++) {
    pinDigits.value[i] = pasted[i] || ''
  }
  // Foca no último campo preenchido ou no próximo vazio
  const nextEmpty = pasted.length < 4 ? pasted.length : 3
  const target = document.getElementById(`pin-${nextEmpty}`)
  if (target) target.focus()
}

// --- Carregamento reativo das abas ---
const carregarDadosPortal = async () => {
  isLoadingTabs.value = true
  try {
    const [feedRes, docsRes, caixaRes] = await Promise.all([
      axios.get(`/portal/projetos/${token}/feed`),
      axios.get(`/portal/projetos/${token}/documentos`),
      axios.get(`/portal/projetos/${token}/caixa`)
    ])

    if (feedRes.data.success) feedData.value = feedRes.data.data
    if (docsRes.data.success) documentosData.value = docsRes.data.data
    if (caixaRes.data.success) caixaData.value = caixaRes.data.data
  } catch (err) {
    console.error("Erro ao carregar dados do portal do cliente:", err)
    showToast("Erro ao sincronizar dados da obra.", "error")
  } finally {
    isLoadingTabs.value = false
  }
}

// --- Chamada à API ---
const validarPin = async () => {
  if (!isPinComplete.value) return
  
  currentState.value = 'loading'
  errorMessage.value = ''
  
  try {
    const response = await axios.post('/portal/acessar-orcamento', {
      token_acesso: token,
      pin_acesso: pinCompleto.value
    })
    
    if (response.data.success) {
      projetoData.value = response.data.data.projeto
      await carregarDadosPortal()
      currentState.value = 'success'
    } else {
      errorMessage.value = 'Não foi possível carregar o orçamento.'
      currentState.value = 'pin'
    }
  } catch (err) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    
    if (status === 403) {
      errorMessage.value = 'PIN incorreto. Verifique os números e tente novamente.'
    } else if (status === 404) {
      errorMessage.value = 'Link inválido ou desativado. Solicite um novo ao engenheiro.'
    } else if (status === 410) {
      errorMessage.value = 'Este link expirou. Solicite um novo ao engenheiro.'
    } else {
      errorMessage.value = detail || 'Erro inesperado. Tente novamente.'
    }
    showToast(errorMessage.value, 'error')
    
    currentState.value = 'pin'
    // Limpar os campos do PIN para nova tentativa
    pinDigits.value = ['', '', '', '']
    setTimeout(() => {
      const first = document.getElementById('pin-0')
      if (first) first.focus()
    }, 100)
  }
}

// Formata data ISO para dd/mm/aaaa
const formatDate = (isoDate) => {
  if (!isoDate) return '—'
  const d = new Date(isoDate)
  return d.toLocaleDateString('pt-BR')
}

const formatCurrency = (val) => {
  if (val === undefined || val === null) return '0,00'
  return Number(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getDocIcon = (categoria) => {
  const cat = (categoria || '').toLowerCase()
  if (cat.includes('planta') || cat.includes('projeto')) return Ruler
  if (cat.includes('contrato')) return FileText
  if (cat.includes('habite')) return Home
  return File
}
</script>

<template>
  <div class="min-h-screen bg-canvas font-sans">
    <div class="max-w-md mx-auto w-full min-h-screen relative">

      <!-- ============================================ -->
      <!-- HEADER — Sempre visível, independente do app -->
      <!-- ============================================ -->
      <header class="bg-surface/80 backdrop-blur-lg border-b border-hairline/60 flex justify-between items-center w-full px-6 h-16 sticky top-0 z-40">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 bg-brand-primary/10 rounded-lg flex items-center justify-center border border-brand-primary/20">
            <Layers class="w-4.5 h-4.5 text-brand-primary" stroke-width="1.5" />
          </div>
          <span class="text-lg font-bold tracking-tight text-ink">Portal do Cliente</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-2 h-2 bg-brand-primary rounded-full animate-pulse"></span>
          <span class="text-xs text-ink-muted font-medium">Acesso Seguro</span>
        </div>
      </header>

      <!-- ============================================ -->
      <!-- ESTADO 1: TELA DE PIN (Bloqueio) -->
      <!-- ============================================ -->
      <div v-if="currentState === 'pin'" class="flex flex-col items-center justify-center px-6 pt-16 pb-8">
        
        <!-- Ícone de Cadeado -->
        <div class="w-20 h-20 bg-canvas rounded-2xl flex items-center justify-center mb-6 border border-hairline">
          <Lock class="w-10 h-10 text-ink-muted" stroke-width="1.5" />
        </div>

        <h1 class="text-2xl font-bold text-ink mb-2 text-center">Acesso ao Orçamento</h1>
        <p class="text-sm text-ink-muted text-center mb-8 leading-relaxed max-w-xs">
          Digite os <strong class="text-ink">4 últimos dígitos do seu telefone</strong> para visualizar o orçamento.
        </p>

        <!-- Inputs do PIN -->
        <form @submit.prevent="validarPin" class="w-full max-w-xs">
          <div class="flex justify-center gap-3 mb-6">
            <input
              v-for="(digit, index) in pinDigits"
              :key="index"
              :id="`pin-${index}`"
              v-model="pinDigits[index]"
              @input="focusNext(index)"
              @keydown="handleBackspace(index, $event)"
              @paste="handlePaste"
              type="text"
              inputmode="numeric"
              maxlength="1"
              autocomplete="off"
              class="w-14 h-16 text-center text-2xl font-bold text-ink bg-surface border rounded-xl outline-none transition-all duration-200"
              :class="[
                errorMessage 
                  ? 'border-red-300 dark:border-red-900 focus:border-red-500 focus:ring-1 focus:ring-red-500' 
                  : 'border-hairline focus:border-brand-primary focus:ring-1 focus:ring-brand-primary'
              ]"
            />
          </div>

          <!-- Mensagem de Erro -->
          <div v-if="errorMessage" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 text-sm p-3 rounded-xl flex items-start gap-2 mb-6 animate-shake">
            <AlertTriangle class="w-4 h-4 text-red-600 mt-0.5 shrink-0" stroke-width="1.5" />
            <span>{{ errorMessage }}</span>
          </div>

          <!-- Botão de Acesso -->
          <button
            type="submit"
            :disabled="!isPinComplete"
            class="w-full py-4 rounded-xl font-semibold text-sm uppercase tracking-wider transition-all duration-200 flex items-center justify-center gap-2 border border-transparent cursor-pointer"
          >
            <Eye class="w-4.5 h-4.5" stroke-width="1.5" />
            Visualizar Orçamento
          </button>
        </form>

        <p class="text-xs text-ink-muted mt-8 text-center">
          O PIN foi definido pelo engenheiro responsável pela obra.
        </p>
      </div>

      <!-- ============================================ -->
      <!-- ESTADO 2: CARREGAMENTO -->
      <!-- ============================================ -->
      <div v-else-if="currentState === 'loading'" class="flex flex-col items-center justify-center px-6 pt-32">
        <div class="w-16 h-16 bg-brand-primary/10 rounded-2xl flex items-center justify-center mb-6 border border-brand-primary/20">
          <Loader2 class="w-8 h-8 text-brand-primary animate-spin" stroke-width="1.5" />
        </div>
        <h2 class="text-lg font-bold text-ink mb-2">Validando acesso...</h2>
        <p class="text-sm text-ink-muted">Verificando seu PIN de segurança.</p>
      </div>

      <!-- ============================================ -->
      <!-- ESTADO 3: VISUALIZAÇÃO DO ORÇAMENTO -->
      <!-- ============================================ -->
      <div v-else-if="currentState === 'success' && projetoData" class="pb-8">
        
        <!-- Banner de Sucesso -->
        <div v-if="projetoData.status !== 'docs_pendentes' && projetoData.status !== 'docs_completos'" class="bg-brand-primary px-6 py-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <CheckCircle2 class="w-6 h-6 text-white" stroke-width="1.5" />
            </div>
            <div>
              <h2 class="text-white font-bold text-base">Acesso Liberado</h2>
              <p class="text-white/80 text-xs">Orçamento e progresso da obra verificados.</p>
            </div>
          </div>
        </div>

        <!-- Banner de Pendência de Documentos (docs_pendentes) -->
        <div v-else-if="projetoData.status === 'docs_pendentes'" class="bg-amber-500 px-6 py-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <AlertTriangle class="w-6 h-6 text-white" stroke-width="1.5" />
            </div>
            <div>
              <h2 class="text-white font-bold text-base">Ação Necessária</h2>
              <p class="text-white/80 text-xs">Algum documento foi recusado. Envie a correção abaixo.</p>
            </div>
          </div>
        </div>

        <!-- Banner de Documentos em Análise (docs_completos) -->
        <div v-else-if="projetoData.status === 'docs_completos'" class="bg-blue-600 px-6 py-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <Clock class="w-6 h-6 text-white" stroke-width="1.5" />
            </div>
            <div>
              <h2 class="text-white font-bold text-base">Documentos em Análise</h2>
              <p class="text-white/80 text-xs">Estamos revisando suas informações. Aguarde contato.</p>
            </div>
          </div>
        </div>

        <!-- Navegação por Abas (ocultar se estiver em docs_pendentes ou docs_completos) -->
        <div v-if="projetoData.status !== 'docs_pendentes' && projetoData.status !== 'docs_completos'" class="px-6 border-b border-hairline bg-surface sticky top-0 z-20 flex gap-4 overflow-x-auto scrollbar-none">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            @click="activeTab = tab.id"
            class="py-3.5 text-xs font-bold uppercase tracking-wider relative shrink-0 transition-colors focus:outline-none"
            :class="activeTab === tab.id ? 'text-brand-primary' : 'text-ink-muted hover:text-ink'"
          >
            {{ tab.label }}
            <span 
              v-if="activeTab === tab.id" 
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-primary rounded-full"
            ></span>
          </button>
        </div>

        <main class="px-6 pt-6">
          
          <!-- Seção de Documentos Pendentes (docs_pendentes) -->
          <div v-if="projetoData.status === 'docs_pendentes'" class="space-y-6">
            <div class="mb-5">
              <h3 class="text-sm font-bold text-ink mb-1 uppercase tracking-wider">Correção de Documentos</h3>
              <p class="text-xs text-ink-muted">Abaixo estão listados os documentos exigidos. Envie a versão corrigida dos itens recusados.</p>
            </div>

            <div class="space-y-4">
              <div v-for="cat in categoriasDocsB2C" :key="cat.id" class="border border-hairline rounded-xl bg-surface p-4 flex flex-col gap-3 shadow-sm">
                <!-- Status Header -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <component :is="iconMap[cat.icon]" class="w-4.5 h-4.5 text-ink-muted" stroke-width="1.5" />
                    <span class="text-xs font-bold text-ink">{{ cat.label }}</span>
                  </div>
                  
                  <!-- Badges reativas baseadas no status real do documento -->
                  <div class="flex items-center gap-1">
                    <span 
                      class="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full flex items-center gap-1"
                      :class="getDocumentStatusInfo(cat.id).badgeClass"
                    >
                      <component :is="getDocumentStatusInfo(cat.id).icon" class="w-3 h-3" stroke-width="1.5" />
                      {{ getDocumentStatusInfo(cat.id).label }}
                    </span>
                  </div>
                </div>

                <p class="text-[11px] text-ink-muted">{{ cat.description }}</p>

                <!-- Motivo de Rejeição -->
                <div v-if="getDocumentStatusInfo(cat.id).status === 'rejeitado'" class="bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30 text-red-700 dark:text-red-400 text-xs p-3 rounded-lg flex flex-col gap-1">
                  <span class="font-bold flex items-center gap-1">
                    <AlertTriangle class="w-4 h-4 text-red-700 dark:text-red-400 shrink-0" stroke-width="1.5" />
                    Motivo da Recusa:
                  </span>
                  <span>{{ getDocumentStatusInfo(cat.id).motivo }}</span>
                </div>

                <!-- Se o documento já foi enviado e aprovado (tem URL e não está rejeitado) -->
                <div v-if="getDocumentStatusInfo(cat.id).status === 'aprovado'" class="text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 p-3 rounded-lg flex items-center justify-between">
                  <span class="truncate max-w-[80%] font-medium">✓ {{ getDocumentStatusInfo(cat.id).filename }}</span>
                  <span class="text-[10px] uppercase font-bold shrink-0">Preservado</span>
                </div>

                <!-- Se pendente ou recusado, liberar input -->
                <div v-else class="space-y-2">
                  <!-- Se um arquivo local foi selecionado -->
                  <div v-if="arquivosCorrigidos[cat.id]" class="bg-zinc-50 dark:bg-zinc-900 border border-hairline p-3 rounded-lg flex items-center justify-between text-xs">
                    <span class="truncate font-semibold text-ink max-w-[80%]">{{ arquivosCorrigidos[cat.id].name }}</span>
                    <button @click="removerArquivoSelecionado(cat.id)" class="text-red-500 hover:text-red-700 flex items-center justify-center">
                      <Trash2 class="w-4 h-4" stroke-width="1.5" />
                    </button>
                  </div>
                  
                  <div v-else>
                    <label 
                      :for="`file-input-${cat.id}`"
                      class="flex items-center justify-center gap-2 border border-dashed border-hairline hover:border-brand-primary hover:bg-brand-primary/5 transition-all py-3 rounded-xl cursor-pointer text-xs font-semibold text-ink-muted hover:text-brand-primary"
                    >
                      <Upload class="w-4 h-4" stroke-width="1.5" />
                      Selecionar Arquivo
                    </label>
                    <input 
                      :id="`file-input-${cat.id}`" 
                      type="file" 
                      accept=".pdf,.png,.jpg,.jpeg" 
                      class="hidden" 
                      @change="handleFileSelect($event, cat.id)"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Botão geral de envio de correções -->
            <button
              @click="enviarDocumentosCorrigidos"
              :disabled="!temArquivosSelecionados || isEnviandoCorrecoes"
              class="w-full py-4 bg-brand-primary hover:bg-brand-hover text-white rounded-xl text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 border border-transparent shadow-sm mt-6 cursor-pointer"
            >
              <Loader2 v-if="isEnviandoCorrecoes" class="w-4.5 h-4.5 animate-spin" stroke-width="1.5" />
              <Send v-else class="w-4.5 h-4.5" stroke-width="1.5" />
              {{ isEnviandoCorrecoes ? 'Enviando Documentos...' : 'Enviar Documentos Corrigidos' }}
            </button>
          </div>

          <!-- Seção de Documentos em Análise (docs_completos / Lead) -->
          <div v-else-if="projetoData.status === 'docs_completos'" class="space-y-6 text-center py-10 flex flex-col items-center">
            <div class="w-20 h-20 bg-blue-50 dark:bg-blue-950/20 rounded-2xl flex items-center justify-center border border-blue-100 dark:border-blue-900/30 mb-4 animate-pulse">
              <Hourglass class="w-10 h-10 text-blue-500" stroke-width="1.5" />
            </div>
            <h3 class="text-base font-bold text-ink">Seus documentos estão em análise</h3>
            <p class="text-xs text-ink-muted leading-relaxed max-w-sm">
              Já recebemos os novos arquivos e eles estão em processo de validação pela nossa equipe de engenharia. 
              Por favor, aguarde! Você será contatado em breve para assinar o contrato da obra.
            </p>
          </div>

          <!-- Abas padrão do portal se NOT docs_pendentes e NOT docs_completos -->
          <div v-else>
            <!-- Aba 1: Diário de Obra (Timeline/Feed) -->
            <div v-if="activeTab === 'feed'">
            <div class="mb-5">
              <h3 class="text-sm font-bold text-ink mb-1 uppercase tracking-wider">Diário de Obra</h3>
              <p class="text-xs text-ink-muted">Acompanhe as atualizações e fotos enviadas do canteiro de obras.</p>
            </div>
            
            <div v-if="feedData.length === 0" class="border border-hairline rounded-2xl bg-surface p-8 text-center flex flex-col items-center">
              <Activity class="w-8 h-8 text-ink-muted mb-2" stroke-width="1.5" />
              <span class="text-xs font-semibold text-ink block mb-1">Nenhuma atualização no momento</span>
              <span class="text-[11px] text-ink-muted">As fotos e posts do canteiro de obras começarão em breve.</span>
            </div>
            
            <div v-else class="relative border-l border-hairline ml-3 pl-6 space-y-6">
              <div v-for="post in feedData" :key="post.id" class="relative">
                <span class="absolute -left-[29px] top-1.5 w-2.5 h-2.5 bg-brand-primary border-2 border-canvas rounded-full"></span>
                
                <div class="bg-surface border border-hairline rounded-xl overflow-hidden shadow-sm">
                  <div class="px-4 py-2.5 border-b border-hairline bg-canvas/30 flex justify-between items-center">
                    <span class="text-[11px] text-ink font-semibold flex items-center gap-1">
                      <User class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                      Responsável Técnico
                    </span>
                    <span class="text-[9px] text-ink-muted font-mono">{{ formatDate(post.criado_em) }}</span>
                  </div>
                  
                  <div class="p-4">
                    <h4 class="text-xs font-bold text-ink mb-1">{{ post.titulo }}</h4>
                    <p class="text-xs text-ink-muted leading-relaxed whitespace-pre-wrap">{{ post.conteudo }}</p>
                  </div>
                  
                  <div v-if="post.imagem_url" class="border-t border-hairline bg-canvas">
                    <img :src="post.imagem_url" alt="Foto da Obra" class="w-full h-40 object-cover" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Aba 2: Evolução Caixa (Caixômetro) -->
          <div v-else-if="activeTab === 'caixa'">
            <div class="mb-5">
              <h3 class="text-sm font-bold text-ink mb-1 uppercase tracking-wider">Evolução Caixa (PCI/PFUI)</h3>
              <p class="text-xs text-ink-muted">Valores medidos e liberados de acordo com o cronograma da Caixa.</p>
            </div>
            
            <div v-if="!caixaData" class="border border-hairline rounded-2xl bg-surface p-8 text-center flex flex-col items-center">
              <Landmark class="w-8 h-8 text-ink-muted mb-2" stroke-width="1.5" />
              <span class="text-xs font-semibold text-ink block mb-1">Dados não disponíveis</span>
              <span class="text-[11px] text-ink-muted">Aguardando a primeira medição técnica da Caixa.</span>
            </div>
            
            <Caixometro v-else :caixaData="caixaData" />
          </div>

          <!-- Aba 3: Documentos (Vault) -->
          <div v-else-if="activeTab === 'documentos'">
            <div class="mb-5">
              <h3 class="text-sm font-bold text-ink mb-1 uppercase tracking-wider">Cofre de Documentos</h3>
              <p class="text-xs text-ink-muted">Acesse as plantas, memoriais e contratos oficiais da obra.</p>
            </div>
            
            <div v-if="documentosData.length === 0" class="border border-hairline rounded-2xl bg-surface p-8 text-center flex flex-col items-center">
              <FolderOpen class="w-8 h-8 text-ink-muted mb-2" stroke-width="1.5" />
              <span class="text-xs font-semibold text-ink block mb-1">Nenhum documento publicado</span>
              <span class="text-[11px] text-ink-muted">Os arquivos do projeto serão disponibilizados aqui pelo engenheiro.</span>
            </div>
            
            <div v-else class="space-y-2.5">
              <div v-for="doc in documentosData" :key="doc.id" class="flex items-center gap-3 bg-surface border border-hairline rounded-xl p-3.5 hover:bg-surface-hover/20 transition-all">
                <div class="w-9 h-9 bg-brand-primary/10 rounded-lg flex items-center justify-center text-brand-primary shrink-0">
                  <component :is="getDocIcon(doc.categoria)" class="w-4.5 h-4.5" stroke-width="1.5" />
                </div>
                <div class="flex-1 min-w-0">
                  <span class="text-[8px] text-brand-primary font-bold uppercase tracking-wider block mb-0.5">{{ doc.categoria }}</span>
                  <span class="text-xs font-bold text-ink block truncate">{{ doc.nome_documento }}</span>
                  <span class="text-[9px] text-ink-muted font-mono">{{ formatDate(doc.criado_em) }}</span>
                </div>
                <a :href="doc.arquivo_url" target="_blank" class="w-8 h-8 rounded-lg bg-canvas border border-hairline flex items-center justify-center text-ink hover:bg-surface-hover transition-colors">
                  <Download class="w-4 h-4" stroke-width="1.5" />
                </a>
              </div>
            </div>
          </div>

          <!-- Aba 4: Dados da Obra (Detalhes) -->
          <div v-else-if="activeTab === 'detalhes'" class="space-y-4">
            <!-- Card Principal: Dados da Obra -->
            <div class="bg-surface border border-hairline rounded-xl overflow-hidden">
              <div class="bg-canvas px-4 py-2.5 border-b border-hairline">
                <div class="flex items-center gap-2">
                  <HardHat class="w-4 h-4 text-ink-muted shrink-0" stroke-width="1.5" />
                  <h3 class="text-xs font-bold text-ink uppercase tracking-wider">Dados Gerais</h3>
                </div>
              </div>

              <div class="divide-y divide-hairline">
                <div class="flex justify-between items-center px-4 py-3">
                  <span class="text-xs text-ink-muted">Nome da Obra</span>
                  <span class="text-xs font-semibold text-ink text-right max-w-[60%]">{{ projetoData.titulo_projeto || '—' }}</span>
                </div>
                <div class="flex justify-between items-center px-4 py-3">
                  <span class="text-xs text-ink-muted">Cliente</span>
                  <span class="text-xs font-semibold text-ink">{{ projetoData.cliente_nome || '—' }}</span>
                </div>
                <div class="flex justify-between items-center px-4 py-3">
                  <span class="text-xs text-ink-muted">BDI</span>
                  <span class="text-xs font-semibold text-brand-primary">{{ projetoData.bdi_padrao ? projetoData.bdi_padrao + '%' : '—' }}</span>
                </div>
                <div v-if="projetoData.endereco" class="flex justify-between items-center px-4 py-3">
                  <span class="text-xs text-ink-muted">Endereço</span>
                  <span class="text-xs font-semibold text-ink text-right max-w-[60%]">{{ projetoData.endereco }}</span>
                </div>
                <div class="flex justify-between items-center px-4 py-3">
                  <span class="text-xs text-ink-muted">Criado em</span>
                  <span class="text-xs font-semibold text-ink">{{ formatDate(projetoData.created_at) }}</span>
                </div>
              </div>
            </div>

            <!-- Card: Observações -->
            <div v-if="projetoData.observacoes" class="bg-surface border border-hairline rounded-xl overflow-hidden">
              <div class="bg-canvas px-4 py-2.5 border-b border-hairline">
                <div class="flex items-center gap-2">
                  <FileText class="w-4 h-4 text-ink-muted shrink-0" stroke-width="1.5" />
                  <h3 class="text-xs font-bold text-ink uppercase tracking-wider">Observações</h3>
                </div>
              </div>
              <div class="p-4">
                <p class="text-xs text-ink-muted leading-relaxed whitespace-pre-wrap">{{ projetoData.observacoes }}</p>
              </div>
            </div>
          </div>
        </div>

          <!-- Rodapé de segurança -->
          <div class="flex items-center justify-center gap-1.5 pt-8 pb-2">
            <Shield class="w-3.5 h-3.5 text-ink-muted shrink-0" stroke-width="1.5" />
            <span class="text-[10px] text-ink-muted font-semibold uppercase tracking-wider">Visualização protegida por PIN • Conexão Criptografada</span>
          </div>
        </main>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Animação de shake para erro do PIN */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}

.animate-shake {
  animation: shake 0.4s ease-in-out;
}
</style>
