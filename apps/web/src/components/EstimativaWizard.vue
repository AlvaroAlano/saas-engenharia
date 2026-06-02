<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { formatCurrency } from '../utils/formatters'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { supabase } from '../supabase'
import { forceLightMode } from '../composables/useTheme'
import { useToast } from '../composables/useToast'
import VerticeLogo from './VerticeLogo.vue'

const { showToast } = useToast()
import { 
  ArrowLeft, Building, CheckCircle2, Sofa, Utensils, Bed, Bath, 
  CheckCircle, Landmark, ExternalLink, Check, ChevronDown, Loader2, 
  HardHat, User, X, ArrowRight, Calculator, ThumbsUp, IdCard, Users, 
  AlertTriangle, FileText, Upload, Hourglass, PartyPopper 
} from 'lucide-vue-next'

const route = useRoute()
const step = ref(1)

const projetoId = ref(route.params.id || '')
const isWaitingRoom = ref(false)
const isFetchingProject = ref(false)

// --- Matchmaking B2C State ---
const isMatchmakingFlow = computed(() => {
  return !projetoId.value || projetoId.value === 'nova' || projetoId.value === 'nova-simulacao'
})
const ufObra = ref(route.query.uf?.toString().toUpperCase() || 'SC')
const ufs = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']
const engineers = ref([])
const isFetchingEngineers = ref(false)
const isSubmittingLead = ref(false)
const concluidoSemConectar = ref(false)
const dadosContato = ref({ nome: '', telefone: '' })
const urlPublicaPortal = ref('')
const pinAcessoPortal = ref('')
const linkCopiado = ref(false)

const loadProjectStatus = async () => {
  if (isMatchmakingFlow.value) return
  isFetchingProject.value = true
  try {
    const res = await axios.get(`/matchmaking/projetos/${projetoId.value}`)
    if (res.data) {
      dadosContato.value.nome = res.data.cliente_nome || ''
      dadosContato.value.telefone = res.data.telefone || ''
      
      // Preenche os slots com documentos existentes
      if (res.data.documentos && Array.isArray(res.data.documentos)) {
        res.data.documentos.forEach(doc => {
          const cat = doc.categoria
          if (docSlots[cat]) {
            docSlots[cat].existingUrl = doc.url
            docSlots[cat].existingName = doc.name
            docSlots[cat].status = doc.status
            docSlots[cat].motivo = doc.motivo
          }
        })
      }
      
      // Preenche os dados da simulação caso já existam
      if (res.data.padrao) {
        const found = padroes.find(p => p.nome === res.data.padrao)
        if (found) {
          padraoSelecionado.value = found
        }
      }
      if (res.data.tamanho) {
        const metragem = parseFloat(res.data.tamanho)
        if (metragem > 0) {
          tamanhos.value.sala = metragem
          tamanhos.value.cozinha = null
          tamanhos.value.quartos = null
          tamanhos.value.banheiros = null
        }
      }
      
      // Detecta documentos rejeitados pelo engenheiro
      const temRejeitados = (res.data.documentos || []).some(doc => doc.status === 'rejeitado')

      if (res.data.status === 'docs_completos') {
        isSuccess.value = true
        if (temRejeitados) {
          // Há rejeições: reabre a tela de upload em vez da sala de espera
          isUploadComplete.value = false
          isWaitingRoom.value = false
        } else {
          isUploadComplete.value = true
          isWaitingRoom.value = true
        }
      } else if (res.data.status === 'docs_incompletos' || res.data.status === 'docs_pendentes' || res.data.coluna === 'contrato_pendente') {
        isSuccess.value = true
        isUploadComplete.value = false
      }
    }
  } catch (error) {
    console.error('Erro ao carregar status do projeto:', error)
  } finally {
    isFetchingProject.value = false
  }
}

onMounted(() => {
  forceLightMode()

  // Prefill in B2C Matchmaking mode
  if (isMatchmakingFlow.value) {
    if (route.query.uf) {
      ufObra.value = route.query.uf.toString().toUpperCase()
    }
    if (route.query.padrao) {
      const pId = route.query.padrao.toString().toLowerCase()
      const found = padroes.find(p => p.id === pId)
      if (found) {
        padraoSelecionado.value = found
      }
    }
    if (route.query.metragem) {
      const metragem = Number(route.query.metragem)
      if (metragem > 0) {
        tamanhos.value.sala = metragem
        tamanhos.value.cozinha = null
        tamanhos.value.quartos = null
        tamanhos.value.banheiros = null
      }
    }
  } else {
    loadProjectStatus()
  }
})
const isLoading = ref(false)
const isSuccess = ref(false)
const isUploading = ref(false)
const isUploadComplete = ref(false)

const docSlots = reactive({
  identidade:   { file: null, isDragging: false, existingUrl: null, existingName: null, status: null, motivo: null },
  residencia:   { file: null, isDragging: false, existingUrl: null, existingName: null, status: null, motivo: null },
  estado_civil: { file: null, isDragging: false, existingUrl: null, existingName: null, status: null, motivo: null }
})

const docMeta = {
  identidade:   { label: 'Documento de Identidade',    sublabel: 'RG ou CNH',                            icon: IdCard },
  residencia:   { label: 'Comprovante de Residência',  sublabel: 'Atualizado (máx. 3 meses)',             icon: Building },
  estado_civil: { label: 'Certidão de Estado Civil',   sublabel: 'Nascimento, casamento ou divórcio',     icon: Users }
}

const allDocsReady = computed(() =>
  ['identidade', 'residencia', 'estado_civil'].every(cat => {
    const slot = docSlots[cat]
    return !!(slot.file || (slot.existingUrl && slot.status !== 'rejeitado'))
  })
)

const temDocumentosRecusados = computed(() =>
  Object.values(docSlots).some(slot => slot.status === 'rejeitado')
)
const padraoSelecionado = ref(null)
const simulacaoCaixaConcluida = ref(false)


const padroes = [
  { 
    id: 'popular', 
    nome: 'Popular', 
    descricao: 'Acabamento simples, functional e econômico.',
    precoBase: 1800 
  },
  { 
    id: 'medio', 
    nome: 'Médio Padrão', 
    descricao: 'Acabamento intermediário, porcelanato e esquadrias de qualidade.',
    precoBase: 2800 
  },
  { 
    id: 'alto', 
    nome: 'Alto Padrão', 
    descricao: 'Acabamento premium, automação e materiais de importação.',
    precoBase: 4500 
  }
]

const tamanhos = ref({
  sala: null,
  cozinha: null,
  quartos: null,
  banheiros: null
})

const metragem_total = computed(() => {
  return (Number(tamanhos.value.sala) || 0) + 
         (Number(tamanhos.value.cozinha) || 0) + 
         (Number(tamanhos.value.quartos) || 0) + 
         (Number(tamanhos.value.banheiros) || 0)
})

const valor_estimado = computed(() => {
  if (!padraoSelecionado.value) return 0
  return metragem_total.value * padraoSelecionado.value.precoBase
})

// Local formatCurrency removed (imported from formatters.js)

const nextStep = () => {
  const maxStep = isMatchmakingFlow.value ? 4 : 3
  if (step.value < maxStep) step.value++
}

const prevStep = () => {
  if (step.value > 1) step.value--
}

const selectPadrao = (padrao) => {
  padraoSelecionado.value = padrao
}

const fetchEngineers = async () => {
  isFetchingEngineers.value = true
  try {
    const response = await axios.get('/matchmaking', {
      params: {
        uf: ufObra.value,
        padrao: padraoSelecionado.value?.id
      }
    })
    engineers.value = response.data
  } catch (error) {
    console.error('Erro ao realizar matchmaking:', error)
  } finally {
    isFetchingEngineers.value = false
  }
}

watch(step, (newStep) => {
  if (newStep === 4) {
    fetchEngineers()
  }
})

const copyPortalLink = () => {
  if (!urlPublicaPortal.value) return
  navigator.clipboard.writeText(urlPublicaPortal.value)
  linkCopiado.value = true
  setTimeout(() => {
    linkCopiado.value = false
  }, 2000)
}

const solicitarOrcamento = async (eng) => {
  if (!dadosContato.value.nome.trim()) {
    showToast('Por favor, informe seu nome completo.', 'warning')
    return
  }
  if (!dadosContato.value.telefone.trim() || dadosContato.value.telefone.replace(/\D/g, '').length < 10) {
    showToast('Por favor, informe um telefone/WhatsApp válido.', 'warning')
    return
  }

  isSubmittingLead.value = true
  try {
    const payload = {
      usuario_id: eng.usuario_id,
      cliente_nome: dadosContato.value.nome.trim(),
      telefone: dadosContato.value.telefone.trim(),
      valor: valor_estimado.value,
      padrao: padraoSelecionado.value?.nome || 'Popular',
      tamanho: metragem_total.value.toString() + 'm²',
      uf_obra: ufObra.value
    }
    
    const response = await axios.post('/matchmaking/solicitar', payload)
    
    if (response.data.success) {
      projetoId.value = response.data.projeto_id || ''
      urlPublicaPortal.value = response.data.url_publica || ''
      pinAcessoPortal.value = response.data.pin_acesso || ''
      isSuccess.value = true
      isUploadComplete.value = false // Direciona para o envio de documentos
    } else {
      showToast('Erro ao enviar solicitação de orçamento.', 'error')
    }
  } catch (error) {
    console.error('Erro ao solicitar orçamento:', error)
    showToast(error.response?.data?.detail || 'Erro ao enviar dados. Tente novamente.', 'error')
  } finally {
    isSubmittingLead.value = false
  }
}

const concluirSemSelecionar = () => {
  concluidoSemConectar.value = true
  isSuccess.value = true
  isUploadComplete.value = true
}

const finishWizard = async () => {
  isLoading.value = true
  try {
    const payload = {
      valor: valor_estimado.value,
      padrao: padraoSelecionado.value.nome,
      tamanho: metragem_total.value.toString() + 'm²',
      coluna: 'contrato_pendente',
      status: 'docs_incompletos'
    }
    
    await axios.patch(`/matchmaking/projetos/${projetoId.value}`, payload)
    
    isSuccess.value = true
  } catch (error) {
    console.error('Erro ao aprovar estimativa:', error)
    showToast('Erro ao processar sua aprovação. Tente novamente.', 'error')
  } finally {
    isLoading.value = false
  }
}


const handleDocFileSelect = (categoria, event) => {
  const file = event.target.files[0]
  if (file) docSlots[categoria].file = file
}

const handleDocDrop = (categoria, event) => {
  docSlots[categoria].isDragging = false
  const file = event.dataTransfer.files[0]
  if (file) docSlots[categoria].file = file
}

const removeDoc = (categoria) => {
  docSlots[categoria].file = null
}

const uploadFiles = async () => {
  if (!allDocsReady.value) return
  isUploading.value = true

  try {
    const uploadedDocs = []

    for (const [categoria, slot] of Object.entries(docSlots)) {
      const file = slot.file
      if (file) {
        const cleanFileName = file.name.replace(/[^\w.-]/g, '_')
        const filePath = `${projetoId.value}/${categoria}/${cleanFileName}`

        const { error } = await supabase.storage
          .from('documentos_clientes')
          .upload(filePath, file, { upsert: true })

        if (error) throw new Error(`Falha no armazenamento: ${error.message}`)

        const { data: urlData } = supabase.storage
          .from('documentos_clientes')
          .getPublicUrl(filePath)

        uploadedDocs.push({
          name: file.name,
          url: urlData.publicUrl,
          categoria,
          done: true
        })
      } else if (slot.existingUrl && slot.status !== 'rejeitado') {
        uploadedDocs.push({
          name: slot.existingName || `${categoria}.pdf`,
          url: slot.existingUrl,
          categoria,
          status: slot.status,
          done: true
        })
      }
    }

    const apiResponse = await axios.patch(`/matchmaking/projetos/${projetoId.value}`, {
      documentos: uploadedDocs,
      status: 'docs_completos'
    })

    if (apiResponse.data.success || apiResponse.status === 200) {
      isUploadComplete.value = true
      isWaitingRoom.value = true
    } else {
      throw new Error('O servidor não confirmou o recebimento dos documentos.')
    }
  } catch (error) {
    console.error('Erro detalhado no upload:', error)
    showToast(error.message || 'Verifique sua conexão e tente novamente.', 'error')
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <div class="bg-canvas min-h-screen font-sans text-ink md:py-10 flex items-center justify-center">
    
    <!-- Main Container -->
    <div class="w-full min-h-screen md:min-h-[auto] md:max-w-4xl bg-surface md:rounded-2xl border border-transparent md:border-hairline overflow-hidden relative flex flex-col shadow-sm">
      
      <!-- Top Progress Bar -->
      <div v-if="!isSuccess" class="bg-surface border-b border-hairline z-10 sticky top-0 md:static">
        <div class="h-1.5 w-full bg-canvas">
          <div 
            class="h-full bg-brand-primary transition-all duration-500 ease-out" 
            :style="{ width: `${(step / (isMatchmakingFlow ? 4 : 3)) * 100}%` }"
          ></div>
        </div>
        <div class="px-6 py-4 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <button v-if="step > 1" @click="prevStep" class="text-ink-muted hover:text-ink transition-colors cursor-pointer flex items-center">
              <ArrowLeft class="w-5 h-5" stroke-width="1.5" />
            </button>
            <span class="text-sm font-bold tracking-wide text-ink-muted uppercase">Passo {{ step }} de {{ isMatchmakingFlow ? 4 : 3 }}</span>
          </div>
          <VerticeLogo class="h-[24px] text-logo" />
        </div>
      </div>


      <!-- Step Content Area -->
      <div v-if="!isSuccess" class="p-6 md:p-10 flex-1 flex flex-col">
        
        <!-- STEP 1: Padrão -->
        <div v-if="step === 1" class="flex-1 animate-in fade-in slide-in-from-right-4 duration-500">
          <h1 class="text-2xl md:text-3xl font-bold text-ink mb-2">Qual o padrão da obra?</h1>
          <p class="text-ink-muted mb-8 md:text-lg">Isso define o custo base. Você poderá ajustar o tamanho no próximo passo.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              v-for="padrao in padroes" 
              :key="padrao.id"
              @click="selectPadrao(padrao)"
              class="text-left border rounded-xl p-5 transition-all relative overflow-hidden group cursor-pointer"
              :class="padraoSelecionado?.id === padrao.id ? 'border-brand-primary bg-brand-primary/10' : 'border-hairline hover:border-brand-primary hover:bg-canvas'"
            >
              <div v-if="padraoSelecionado?.id === padrao.id" class="absolute top-3 right-3 text-brand-primary">
                <CheckCircle2 class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
              </div>
              <h3 class="text-lg font-bold text-ink mb-1" :class="padraoSelecionado?.id === padrao.id ? 'text-brand-primary' : ''">{{ padrao.nome }}</h3>
              <p class="text-xs text-brand-primary font-semibold mb-3">a partir de R$ {{ padrao.precoBase }}/m²</p>
              <p class="text-sm text-ink-muted leading-relaxed">{{ padrao.descricao }}</p>
            </button>
          </div>
        </div>

        <!-- STEP 2: Tamanhos -->
        <div v-if="step === 2" class="flex-1 animate-in fade-in slide-in-from-right-4 duration-500">
          <h1 class="text-2xl md:text-3xl font-bold text-ink mb-2">Qual o tamanho aproximado?</h1>
          <p class="text-ink-muted mb-8 md:text-lg">Informe a metragem quadrada de cada ambiente.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
            <div class="bg-canvas p-4 rounded-xl border border-hairline flex items-center gap-4">
              <div class="w-12 h-12 bg-surface border border-hairline rounded-full flex items-center justify-center text-ink-muted">
                <Sofa class="w-6 h-6 text-ink-muted" stroke-width="1.5" />
              </div>
              <div class="flex-1">
                <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider mb-1">Sala / Estar</label>
                <div class="flex items-center gap-2">
                  <input v-model="tamanhos.sala" @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }" type="number" min="0" class="w-full bg-transparent text-xl font-bold text-ink focus:outline-none border-b border-hairline focus:border-brand-primary transition-colors pb-1" placeholder="0">
                  <span class="text-ink-muted font-medium">m²</span>
                </div>
              </div>
            </div>

            <div class="bg-canvas p-4 rounded-xl border border-hairline flex items-center gap-4">
              <div class="w-12 h-12 bg-surface border border-hairline rounded-full flex items-center justify-center text-ink-muted">
                <Utensils class="w-6 h-6 text-ink-muted" stroke-width="1.5" />
              </div>
              <div class="flex-1">
                <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider mb-1">Cozinha</label>
                <div class="flex items-center gap-2">
                  <input v-model="tamanhos.cozinha" @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }" type="number" min="0" class="w-full bg-transparent text-xl font-bold text-ink focus:outline-none border-b border-hairline focus:border-brand-primary transition-colors pb-1" placeholder="0">
                  <span class="text-ink-muted font-medium">m²</span>
                </div>
              </div>
            </div>

            <div class="bg-canvas p-4 rounded-xl border border-hairline flex items-center gap-4">
              <div class="w-12 h-12 bg-surface border border-hairline rounded-full flex items-center justify-center text-ink-muted">
                <Bed class="w-6 h-6 text-ink-muted" stroke-width="1.5" />
              </div>
              <div class="flex-1">
                <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider mb-1">Quartos</label>
                <div class="flex items-center gap-2">
                  <input v-model="tamanhos.quartos" @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }" type="number" min="0" class="w-full bg-transparent text-xl font-bold text-ink focus:outline-none border-b border-hairline focus:border-brand-primary transition-colors pb-1" placeholder="0">
                  <span class="text-ink-muted font-medium">m²</span>
                </div>
              </div>
            </div>

            <div class="bg-canvas p-4 rounded-xl border border-hairline flex items-center gap-4">
              <div class="w-12 h-12 bg-surface border border-hairline rounded-full flex items-center justify-center text-ink-muted">
                <Bath class="w-6 h-6 text-ink-muted" stroke-width="1.5" />
              </div>
              <div class="flex-1">
                <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider mb-1">Banheiros</label>
                <div class="flex items-center gap-2">
                  <input v-model="tamanhos.banheiros" @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }" type="number" min="0" class="w-full bg-transparent text-xl font-bold text-ink focus:outline-none border-b border-hairline focus:border-brand-primary transition-colors pb-1" placeholder="0">
                  <span class="text-ink-muted font-medium">m²</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-6 p-4 bg-brand-primary/10 rounded-lg border border-brand-primary/20 flex items-center justify-between">
            <span class="text-sm font-semibold text-brand-primary">Metragem Total Calculada:</span>
            <span class="text-xl font-bold text-brand-primary">{{ metragem_total }} m²</span>
          </div>
        </div>

        <!-- STEP 3: Resultado -->
        <div v-if="step === 3" class="flex-1 flex flex-col items-center justify-center text-center animate-in fade-in zoom-in-95 duration-500 py-10">
          <div class="w-20 h-20 bg-brand-primary/10 text-brand-primary rounded-full flex items-center justify-center mb-6 border border-brand-primary/20">
            <CheckCircle class="w-10 h-10 text-brand-primary" stroke-width="1.5" />
          </div>
          
          <h2 class="text-xl font-semibold text-ink-muted uppercase tracking-widest mb-2">Valor Estimado da Obra</h2>
          <div class="text-5xl md:text-6xl font-black text-ink tracking-tight mb-4">
            {{ formatCurrency(valor_estimado) }}
          </div>
          
          <div class="flex flex-wrap justify-center gap-3 mt-2 mb-8">
            <span class="px-3 py-1 bg-canvas text-ink-muted text-sm font-medium rounded-full border border-hairline">{{ padraoSelecionado?.nome }}</span>
            <span class="px-3 py-1 bg-canvas text-ink-muted text-sm font-medium rounded-full border border-hairline">{{ metragem_total }} m² Totais</span>
          </div>
          
          <p class="text-sm text-ink-muted max-w-md mx-auto leading-relaxed border-t border-hairline pt-6">
             Este valor é uma estimativa inicial baseada nos padrões de construção civil e na metragem informada.
          </p>

          <!-- Caixa Simulation Box -->
          <div class="mt-8 w-full max-w-lg bg-brand-primary/5 border border-brand-primary/20 rounded-xl p-6 text-left">
            <div class="flex items-start gap-4 mb-4">
              <Landmark class="w-6 h-6 text-brand-primary" stroke-width="1.5" />
              <div>
                <h3 class="text-lg font-bold text-brand-primary dark:text-white mb-1">Pré-qualificação Caixa</h3>
                <p class="text-sm text-brand-primary dark:text-ink leading-relaxed">
                  Para prosseguirmos, precisamos que você realize uma simulação rápida de financiamento no site da Caixa Econômica Federal utilizando o valor estimado acima.
                </p>
              </div>
            </div>
            
            <a 
              href="https://habitacao.caixa.gov.br/siopiweb-web/simulaOperacaoInternet.do?method=inicializarCasoUso&pk_campaign=habitacao&pk_kwd=direct&pk_source=redirect" 
              target="_blank"
              class="w-full py-3 mb-4 rounded-lg font-bold text-sm transition-all flex items-center justify-center gap-2 border border-brand-primary text-brand-primary hover:bg-brand-primary hover:text-white"
            >
              Acessar Simulador da Caixa <ExternalLink class="w-[18px] h-[18px]" stroke-width="1.5" />
            </a>

            <label class="flex items-start gap-3 cursor-pointer group p-2 rounded-lg hover:bg-brand-primary/10 transition-colors">
              <div class="relative flex items-center pt-1">
                <input 
                  type="checkbox" 
                  v-model="simulacaoCaixaConcluida"
                  class="peer appearance-none w-5 h-5 border border-brand-primary/30 rounded-md checked:bg-brand-primary checked:border-brand-primary cursor-pointer transition-all focus:outline-none focus:ring-1 focus:ring-brand-primary dark:focus:ring-offset-slate-900"
                >
                <Check class="w-3 h-3 absolute text-white pointer-events-none opacity-0 peer-checked:opacity-100 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" stroke-width="2" />
              </div>
              <span class="text-sm font-medium text-brand-primary dark:text-white leading-tight">
                Confirmo que realizei a simulação na Caixa e tenho margem aprovada.
              </span>
            </label>
          </div>
        </div>

        <!-- STEP 4: Encontre seu Engenheiro (B2C Matchmaking) -->
        <div v-if="step === 4 && isMatchmakingFlow" class="flex-1 animate-in fade-in slide-in-from-right-4 duration-500">
          
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
              <h1 class="text-2xl md:text-3xl font-bold text-ink">Encontre seu Engenheiro</h1>
              <p class="text-ink-muted">Escolha um profissional para receber e validar seu orçamento.</p>
            </div>
            
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-ink-muted">UF da Obra:</span>
              <div class="relative w-28">
                <select 
                  v-model="ufObra" 
                  @change="fetchEngineers"
                  class="w-full bg-surface border border-hairline rounded-md px-3 py-1.5 text-sm text-ink focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/50 appearance-none cursor-pointer transition-colors"
                >
                  <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
                </select>
                <ChevronDown class="w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
              </div>
            </div>
          </div>

          <!-- Formulário de Contato -->
          <div class="mb-8 p-6 bg-canvas border border-hairline rounded-xl">
            <h3 class="text-sm font-bold text-ink uppercase tracking-wide mb-4">Seus Dados de Contato</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider mb-1">Seu Nome Completo</label>
                <input 
                  v-model="dadosContato.nome" 
                  type="text" 
                  class="w-full bg-surface border border-hairline rounded-md py-2 px-3 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/50 transition-colors"
                  placeholder="Ex: Álvaro Alano"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider mb-1">Seu WhatsApp / Telefone</label>
                <input 
                  v-model="dadosContato.telefone" 
                  v-maska="'(##) #####-####'"
                  type="text" 
                  class="w-full bg-surface border border-hairline rounded-md py-2 px-3 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/50 transition-colors"
                  placeholder="(99) 99999-9999"
                />
              </div>
            </div>
          </div>

          <!-- Lista de Engenheiros -->
          <div v-if="isFetchingEngineers" class="text-center py-12 flex flex-col items-center">
            <Loader2 class="w-8 h-8 animate-spin text-brand-primary" stroke-width="1.5" />
            <p class="text-ink-muted text-sm mt-2">Buscando profissionais...</p>
          </div>

          <div v-else-if="engineers.length === 0" class="text-center py-12 border border-hairline border-dashed rounded-xl bg-canvas flex flex-col items-center justify-center">
            <HardHat class="w-10 h-10 text-ink-muted" stroke-width="1.5" />
            <p class="text-ink font-semibold mt-2">Nenhum engenheiro disponível para {{ ufObra }}</p>
            <p class="text-ink-muted text-sm mt-1">Tente selecionar outra UF acima.</p>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div 
              v-for="eng in engineers" 
              :key="eng.id"
              class="bg-surface border border-hairline rounded-xl p-5 hover:border-brand-primary transition-all flex flex-col justify-between"
            >
              <div>
                <div class="flex items-start gap-4">
                  <!-- Avatar/Foto -->
                  <img 
                    v-if="eng.foto_perfil" 
                    :src="eng.foto_perfil" 
                    alt="Foto do Engenheiro" 
                    class="w-14 h-14 rounded-full object-cover border border-hairline shrink-0"
                  />
                  <div v-else class="w-14 h-14 rounded-full bg-canvas border border-hairline flex items-center justify-center text-ink-muted shrink-0">
                    <User class="w-7 h-7 text-ink-muted" stroke-width="1.5" />
                  </div>

                  <!-- Info -->
                  <div class="overflow-hidden">
                    <h4 class="font-bold text-ink leading-tight truncate">{{ eng.nome_completo }}</h4>
                    <p class="text-xs text-brand-primary font-medium mt-1">
                      CREA/CAU: {{ eng.registro_crea_cau || 'Não informado' }}
                    </p>
                  </div>
                </div>

                <!-- Especialidades -->
                <div class="flex flex-wrap gap-1 mt-4">
                  <span 
                    v-for="esp in eng.especialidades" 
                    :key="esp"
                    class="text-[10px] bg-canvas text-ink-muted px-2.5 py-0.5 rounded border border-hairline font-medium"
                  >
                    {{ esp }}
                  </span>
                </div>
              </div>

              <!-- Botão de Ação -->
              <div class="mt-6 pt-4 border-t border-hairline flex items-center justify-between">
                <span class="text-[11px] text-ink-muted">Atendimento: {{ eng.raio_km }}km</span>
                <button 
                  @click="solicitarOrcamento(eng)"
                  :disabled="isSubmittingLead"
                  class="bg-[#5e6ad2] hover:bg-[#828fff] text-white text-xs font-bold px-4 py-2 rounded-md transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50 font-sans"
                >
                  <Loader2 v-if="isSubmittingLead" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                  Solicitar Orçamento
                </button>
              </div>
            </div>
          </div>

          <!-- Opção secundária: Concluir sem conectar -->
          <div class="mt-8 pt-6 border-t border-hairline flex items-center justify-center">
            <button 
              @click="concluirSemSelecionar"
              class="text-xs text-ink-muted hover:text-ink font-semibold flex items-center gap-1 hover:underline cursor-pointer"
            >
              <X class="w-4 h-4" stroke-width="1.5" />
              Apenas concluir simulação sem conectar com um engenheiro
            </button>
          </div>

        </div>

      </div>

      <!-- Footer Buttons (Fixed on mobile, static on desktop) -->
      <div v-if="!isSuccess && step < 4" class="bg-surface border-t border-hairline p-6 flex flex-col gap-3 sticky bottom-0 z-10 md:static">
        
        <button 
          v-if="step === 1" 
          @click="nextStep"
          :disabled="!padraoSelecionado"
          class="w-full py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed border border-transparent cursor-pointer"
          :class="padraoSelecionado ? 'bg-zinc-950 dark:bg-zinc-900 text-white hover:bg-zinc-900 dark:hover:bg-zinc-800' : 'bg-canvas text-ink-muted'"
        >
          Continuar <ArrowRight class="w-5 h-5" stroke-width="1.5" />
        </button>

        <button 
          v-if="step === 2" 
          @click="nextStep"
          :disabled="metragem_total === 0"
          class="w-full py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2 bg-zinc-950 dark:bg-zinc-900 text-white hover:bg-zinc-900 dark:hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed border border-transparent cursor-pointer"
        >
          Calcular Estimativa <Calculator class="w-5 h-5" stroke-width="1.5" />
        </button>

        <button 
          v-if="step === 3" 
          @click="isMatchmakingFlow ? nextStep() : finishWizard()"
          :disabled="isLoading || !simulacaoCaixaConcluida"
          class="w-full py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed border border-transparent cursor-pointer"
          :class="isLoading ? 'bg-canvas text-ink-muted' : 'bg-brand-primary text-white hover:bg-brand-hover'"
        >
          <template v-if="isMatchmakingFlow">
            Avançar para Encontrar Engenheiro <ArrowRight class="w-5 h-5" stroke-width="1.5" />
          </template>
          <template v-else>
            <Loader2 v-if="isLoading" class="w-5 h-5 animate-spin" stroke-width="1.5" />
            <ThumbsUp v-else class="w-5 h-5" stroke-width="1.5" />
            {{ isLoading ? 'Processando...' : 'Aprovei, quero avançar!' }}
          </template>
        </button>
        
      </div>


      <!-- Success Screen & Upload -->
      <div v-if="isSuccess" class="p-6 md:p-10 flex-1 flex flex-col items-center justify-center animate-in fade-in zoom-in-95 duration-500 w-full overflow-y-auto">
        
        <div v-if="!isUploadComplete" class="w-full flex flex-col items-center">

          <!-- Header: Documentos recusados (retorno após rejeição) -->
          <template v-if="temDocumentosRecusados">
            <div class="w-24 h-24 bg-red-50 dark:bg-red-950/20 rounded-full flex items-center justify-center mb-6 border border-red-100 dark:border-red-900/30">
              <AlertTriangle class="w-12 h-12 text-red-500" stroke-width="1.5" />
            </div>
            <h2 class="text-2xl md:text-3xl font-black text-ink mb-4 tracking-tight text-center">Ação Necessária</h2>
            <div class="w-full max-w-md mb-8 bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
              <AlertTriangle class="w-5 h-5 text-red-500 shrink-0 mt-0.5" stroke-width="1.5" />
              <p class="text-sm text-red-600 dark:text-red-400 leading-relaxed">
                Alguns documentos foram recusados pela engenharia. Verifique os motivos abaixo e envie novamente.
              </p>
            </div>
          </template>

          <!-- Header: Primeiro envio -->
          <template v-else>
            <div class="w-24 h-24 bg-brand-primary/10 text-brand-primary rounded-full flex items-center justify-center mb-6 border border-brand-primary/20">
              <CheckCircle2 class="w-12 h-12 text-brand-primary" stroke-width="1.5" />
            </div>
            <h2 class="text-2xl md:text-3xl font-black text-ink mb-4 tracking-tight text-center">Estimativa Aprovada! 🚀</h2>
            <p class="text-ink-muted md:text-lg max-w-sm mx-auto leading-relaxed text-center mb-10">
              O engenheiro responsável foi notificado. O próximo passo é o envio dos documentos para seguirmos com o seu contrato.
            </p>
          </template>

          <!-- Dropzones por Documento -->
          <div class="w-full max-w-md space-y-3 mb-6">
            <h3 class="text-sm font-bold text-ink uppercase tracking-wide mb-1">Documentos Obrigatórios</h3>

            <div
              v-for="(slot, categoria) in docSlots"
              :key="categoria"
              class="bg-canvas border rounded-xl p-4 transition-all"
              :class="slot.isDragging ? 'border-brand-primary bg-brand-primary/5' : 'border-hairline'"
            >
              <!-- Cabeçalho do slot -->
              <div class="flex items-center gap-3 mb-3">
                <component :is="docMeta[categoria].icon" class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
                <div class="flex-1">
                  <p class="text-sm font-semibold text-ink">{{ docMeta[categoria].label }}</p>
                  <p class="text-xs text-ink-muted">{{ docMeta[categoria].sublabel }}</p>
                </div>
                <CheckCircle2 v-if="slot.file || (slot.existingUrl && slot.status !== 'rejeitado')" class="w-5 h-5 text-emerald-500" stroke-width="1.5" />
              </div>

              <!-- Motivo de Rejeição -->
              <div v-if="slot.status === 'rejeitado'" class="bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30 text-red-700 dark:text-red-400 text-xs p-3 rounded-lg flex flex-col gap-1 mb-3">
                <span class="font-bold flex items-center gap-1">
                  <AlertTriangle class="w-3.5 h-3.5 text-red-700 dark:text-red-400" stroke-width="1.5" />
                  Motivo da Recusa:
                </span>
                <span>{{ slot.motivo }}</span>
              </div>

              <!-- Se o documento já foi enviado e aprovado (tem URL e não está rejeitado) -->
              <div v-if="slot.existingUrl && slot.status !== 'rejeitado'" class="text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 p-3 rounded-lg flex items-center justify-between">
                <span class="truncate max-w-[80%] font-medium">✓ {{ slot.existingName || 'Documento enviado' }}</span>
                <span class="text-[10px] uppercase font-bold shrink-0">Preservado</span>
              </div>

              <!-- Se pendente ou recusado, liberar input ou exibir arquivo local -->
              <div v-else class="space-y-2">
                <!-- Arquivo selecionado -->
                <div v-if="slot.file" class="flex items-center justify-between bg-surface border border-hairline rounded-lg px-3 py-2">
                  <div class="flex items-center gap-2 overflow-hidden">
                    <FileText class="w-4 h-4 text-ink-muted shrink-0" stroke-width="1.5" />
                    <span class="text-sm text-ink truncate">{{ slot.file.name }}</span>
                  </div>
                  <button @click="removeDoc(categoria)" class="text-ink-muted hover:text-red-500 transition-colors p-1 cursor-pointer shrink-0 flex items-center justify-center">
                    <X class="w-4 h-4" stroke-width="1.5" />
                  </button>
                </div>

                <!-- Dropzone vazia -->
                <div
                  v-else
                  class="relative border border-dashed rounded-lg p-4 flex items-center gap-3 hover:bg-surface-hover transition-colors cursor-pointer text-ink-muted font-sans"
                  :class="slot.isDragging ? 'border-brand-primary bg-brand-primary/5' : 'border-hairline'"
                  @dragover.prevent="slot.isDragging = true"
                  @dragleave.prevent="slot.isDragging = false"
                  @drop.prevent="handleDocDrop(categoria, $event)"
                >
                  <input type="file" accept=".pdf,.jpg,.jpeg,.png" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" @change="handleDocFileSelect(categoria, $event)">
                  <Upload class="w-5 h-5 text-ink-muted" stroke-width="1.5" />
                  <p class="text-xs">Arraste ou <span class="text-brand-primary font-semibold">clique para buscar</span></p>
                  <span class="text-[10px] text-ink-muted ml-auto font-mono">PDF, JPG, PNG</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Botão de Envio -->
          <button
            @click="uploadFiles"
            :disabled="isUploading || !allDocsReady"
            class="w-full max-w-md py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed border border-transparent cursor-pointer font-sans"
            :class="isUploading ? 'bg-canvas text-ink-muted' : 'bg-brand-primary text-white hover:bg-brand-hover'"
          >
            <Loader2 v-if="isUploading" class="w-5 h-5 animate-spin" stroke-width="1.5" />
            <Upload v-else class="w-5 h-5" stroke-width="1.5" />
            {{ isUploading ? 'Enviando documentos...' : 'Finalizar Envio' }}
          </button>
        </div>

        <!-- Tela de Finalização Absoluta -->
        <div v-else class="w-full flex flex-col items-center justify-center text-center py-10 animate-in fade-in zoom-in-95 duration-500">
          
          <template v-if="concluidoSemConectar">
            <div class="w-24 h-24 bg-brand-primary text-white rounded-full flex items-center justify-center mb-6">
              <ThumbsUp class="w-12 h-12" stroke-width="1.5" />
            </div>
            <h2 class="text-2xl md:text-3xl font-black text-ink mb-4 tracking-tight">Simulação Concluída!</h2>
            <p class="text-ink-muted md:text-lg max-w-sm mx-auto leading-relaxed mb-6">
              Obrigado por simular conosco. Sua estimativa para a obra de <span class="font-bold text-ink">{{ metragem_total }}m²</span> (Padrão {{ padraoSelecionado?.nome }}) totalizou <span class="font-bold text-ink">{{ formatCurrency(valor_estimado) }}</span>.
            </p>
            <p class="text-sm text-ink-muted max-w-sm mx-auto leading-relaxed">
              Você pode voltar a esta página sempre que quiser para simular novamente ou conectar-se com nossos especialistas.
            </p>
          </template>
          
          <template v-else-if="isWaitingRoom">
            <div class="w-24 h-24 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-6 border border-emerald-200">
              <FileText class="w-12 h-12 text-emerald-600" stroke-width="1.5" />
            </div>
            <h2 class="text-2xl md:text-3xl font-black text-ink mb-4 tracking-tight">Documentos em Análise! 📑</h2>
            <p class="text-ink-muted md:text-lg max-w-md mx-auto leading-relaxed mb-8 text-center">
              Agradecemos o envio! Seus documentos foram recebidos com sucesso e nossa equipe de engenharia já está realizando a análise técnica.
            </p>
            <div class="w-full max-w-md bg-zinc-50 dark:bg-zinc-900 border border-hairline rounded-xl p-5 mb-6 text-left shadow-sm">
              <h4 class="text-xs font-bold text-ink uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <Hourglass class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Próximos Passos
              </h4>
              <p class="text-xs text-ink-muted leading-relaxed">
                Aguarde o contato do engenheiro responsável para a validação dos documentos e assinatura do contrato digital de prestação de serviços.
              </p>
            </div>
          </template>
          
          <template v-else>
            <div class="w-24 h-24 bg-brand-primary text-white rounded-full flex items-center justify-center mb-6">
              <PartyPopper class="w-12 h-12" stroke-width="1.5" />
            </div>
            <h2 class="text-2xl md:text-3xl font-black text-ink mb-4 tracking-tight">Tudo Pronto!</h2>
            <p class="text-ink-muted md:text-lg max-w-sm mx-auto leading-relaxed">
              Seus documentos foram recebidos com sucesso. Nossa equipe de engenharia iniciará as validações para a liberação da obra.
            </p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>
