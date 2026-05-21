<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useToast } from '../composables/useToast'
import { forceLightMode } from '../composables/useTheme'
import Caixometro from './Caixometro.vue'

const route = useRoute()
const token = route.params.token
const { showToast } = useToast()

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

    if (feedRes.data.success) documentosData.value = docsRes.data.data
    if (docsRes.data.success) feedData.value = feedRes.data.data
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
  if (cat.includes('planta') || cat.includes('projeto')) return 'architecture'
  if (cat.includes('contrato')) return 'description'
  if (cat.includes('habite')) return 'home'
  return 'draft'
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
            <span class="material-symbols-outlined text-brand-primary text-lg">foundation</span>
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
          <span class="material-symbols-outlined text-4xl text-ink-muted" style="font-variation-settings: 'FILL' 1;">lock</span>
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
            <span class="material-symbols-outlined text-base mt-0.5 shrink-0">error</span>
            <span>{{ errorMessage }}</span>
          </div>

          <!-- Botão de Acesso -->
          <button
            type="submit"
            :disabled="!isPinComplete"
            class="w-full py-4 rounded-xl font-semibold text-sm uppercase tracking-wider transition-all duration-200 flex items-center justify-center gap-2 border border-transparent"
            :class="[
              isPinComplete
                ? 'bg-brand-primary hover:bg-brand-hover text-white active:scale-[0.98] cursor-pointer'
                : 'bg-canvas border-hairline text-ink-muted cursor-not-allowed'
            ]"
          >
            <span class="material-symbols-outlined text-lg">visibility</span>
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
          <span class="material-symbols-outlined text-3xl text-brand-primary animate-spin">progress_activity</span>
        </div>
        <h2 class="text-lg font-bold text-ink mb-2">Validando acesso...</h2>
        <p class="text-sm text-ink-muted">Verificando seu PIN de segurança.</p>
      </div>

      <!-- ============================================ -->
      <!-- ESTADO 3: VISUALIZAÇÃO DO ORÇAMENTO -->
      <!-- ============================================ -->
      <div v-else-if="currentState === 'success' && projetoData" class="pb-8">
        
        <!-- Banner de Sucesso -->
        <div class="bg-brand-primary px-6 py-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <span class="material-symbols-outlined text-white text-xl" style="font-variation-settings: 'FILL' 1;">check_circle</span>
            </div>
            <div>
              <h2 class="text-white font-bold text-base">Acesso Liberado</h2>
              <p class="text-white/80 text-xs">Orçamento e progresso da obra verificados.</p>
            </div>
          </div>
        </div>

        <!-- Navegação por Abas -->
        <div class="px-6 border-b border-hairline bg-surface sticky top-0 z-20 flex gap-4 overflow-x-auto scrollbar-none">
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
          
          <!-- Aba 1: Diário de Obra (Timeline/Feed) -->
          <div v-if="activeTab === 'feed'">
            <div class="mb-5">
              <h3 class="text-sm font-bold text-ink mb-1 uppercase tracking-wider">Diário de Obra</h3>
              <p class="text-xs text-ink-muted">Acompanhe as atualizações e fotos enviadas do canteiro de obras.</p>
            </div>
            
            <div v-if="feedData.length === 0" class="border border-hairline rounded-2xl bg-surface p-8 text-center flex flex-col items-center">
              <span class="material-symbols-outlined text-3xl text-ink-muted mb-2">timeline</span>
              <span class="text-xs font-semibold text-ink block mb-1">Nenhuma atualização no momento</span>
              <span class="text-[11px] text-ink-muted">As fotos e posts do canteiro de obras começarão em breve.</span>
            </div>
            
            <div v-else class="relative border-l border-hairline ml-3 pl-6 space-y-6">
              <div v-for="post in feedData" :key="post.id" class="relative">
                <span class="absolute -left-[29px] top-1.5 w-2.5 h-2.5 bg-brand-primary border-2 border-canvas rounded-full"></span>
                
                <div class="bg-surface border border-hairline rounded-xl overflow-hidden shadow-sm">
                  <div class="px-4 py-2.5 border-b border-hairline bg-canvas/30 flex justify-between items-center">
                    <span class="text-[11px] text-ink font-semibold flex items-center gap-1">
                      <span class="material-symbols-outlined text-brand-primary text-sm">person</span>
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
              <span class="material-symbols-outlined text-3xl text-ink-muted mb-2">account_balance</span>
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
              <span class="material-symbols-outlined text-3xl text-ink-muted mb-2">folder_open</span>
              <span class="text-xs font-semibold text-ink block mb-1">Nenhum documento publicado</span>
              <span class="text-[11px] text-ink-muted">Os arquivos do projeto serão disponibilizados aqui pelo engenheiro.</span>
            </div>
            
            <div v-else class="space-y-2.5">
              <div v-for="doc in documentosData" :key="doc.id" class="flex items-center gap-3 bg-surface border border-hairline rounded-xl p-3.5 hover:bg-surface-hover/20 transition-all">
                <div class="w-9 h-9 bg-brand-primary/10 rounded-lg flex items-center justify-center text-brand-primary shrink-0">
                  <span class="material-symbols-outlined text-lg">{{ getDocIcon(doc.categoria) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <span class="text-[8px] text-brand-primary font-bold uppercase tracking-wider block mb-0.5">{{ doc.categoria }}</span>
                  <span class="text-xs font-bold text-ink block truncate">{{ doc.nome_documento }}</span>
                  <span class="text-[9px] text-ink-muted font-mono">{{ formatDate(doc.criado_em) }}</span>
                </div>
                <a :href="doc.arquivo_url" target="_blank" class="w-8 h-8 rounded-lg bg-canvas border border-hairline flex items-center justify-center text-ink hover:bg-surface-hover transition-colors">
                  <span class="material-symbols-outlined text-base">download</span>
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
                  <span class="material-symbols-outlined text-ink-muted text-base">engineering</span>
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
                  <span class="material-symbols-outlined text-ink-muted text-base">sticky_note_2</span>
                  <h3 class="text-xs font-bold text-ink uppercase tracking-wider">Observações</h3>
                </div>
              </div>
              <div class="p-4">
                <p class="text-xs text-ink-muted leading-relaxed whitespace-pre-wrap">{{ projetoData.observacoes }}</p>
              </div>
            </div>
          </div>

          <!-- Rodapé de segurança -->
          <div class="flex items-center justify-center gap-1.5 pt-8 pb-2">
            <span class="material-symbols-outlined text-ink-muted text-sm">shield</span>
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
