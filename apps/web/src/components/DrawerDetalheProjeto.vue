<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { formatCurrency } from '../utils/formatters'
import SetupOrcamentoModal from './modals/SetupOrcamentoModal.vue'
import RejeicaoDocumentoModal from './modals/RejeicaoDocumentoModal.vue'
import {
  X,
  Pen,
  HardHat,
  Info,
  UserCheck,
  Check,
  Copy,
  MessageSquare,
  Share2,
  Loader2,
  CheckCircle2,
  Lock,
  FolderOpen,
  Eye,
  FileText,
  User,
  History,
  IdCard,
  Home,
  Users,
  RotateCcw,
  Send,
  ExternalLink,
  Archive
} from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const { showToast } = useToast()

const iconMap = {
  badge: IdCard,
  home_work: Home,
  family_restroom: Users
}

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  project: {
    type: Object,
    required: true
  },
  documentoInicial: {
    type: Object,
    default: null
  },
  zIndex: {
    type: Number,
    default: 100
  },
  isArquivado: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'update'])

const router = useRouter()

const isLoadingHistory = ref(false)
const historico = ref([])
const portalUrl = ref('')
const portalPin = ref('')
const isLoadingPortal = ref(false)

const isQualificacaoCopied = ref(false)
const isPortalCopied = ref(false)

// Modals State
const isSetupOpen = ref(false)
const isRejeicaoModalOpen = ref(false)
const selectedDocParaRejeicao = ref(null)

// Split View Document Viewer State
const documentoAtivo = ref(null)

// Contrato Comercial flow state
const templatesContrato = ref([])
const isLoadingTemplates = ref(false)
const selectedTemplateId = ref('')
const isGeneratingContrato = ref(false)
const contratoBlobUrl = ref(null)
const foiPrevisualizando = ref(false)
const isEnviandoZapSign = ref(false)

const fetchTemplatesContrato = async () => {
  isLoadingTemplates.value = true
  try {
    const { data } = await axios.get('/contratos-templates')
    const tipoDesejado = props.project?.coluna === 'engenharia_caixa' ? 'contrato' : 'proposta'
    templatesContrato.value = data.filter(t => {
      if (tipoDesejado === 'contrato') {
        return t.tipo === 'contrato'
      } else {
        return !t.tipo || t.tipo === 'proposta'
      }
    })
    if (templatesContrato.value.length > 0) {
      selectedTemplateId.value = templatesContrato.value[0].id
    } else {
      selectedTemplateId.value = ''
    }
  } catch (error) {
    console.error('Erro ao buscar templates de contrato:', error)
  } finally {
    isLoadingTemplates.value = false
  }
}

const previewContrato = async () => {
  if (!selectedTemplateId.value) return
  isGeneratingContrato.value = true
  try {
    const response = await axios.get(`/projetos/${props.project.id}/contrato`, {
      params: { template_id: selectedTemplateId.value },
      responseType: 'blob'
    })
    if (contratoBlobUrl.value) URL.revokeObjectURL(contratoBlobUrl.value)
    contratoBlobUrl.value = URL.createObjectURL(response.data)
    documentoAtivo.value = { url: contratoBlobUrl.value, name: 'Contrato Comercial', categoria: 'contrato' }
    foiPrevisualizando.value = true
  } catch (error) {
    console.error('Erro ao gerar pré-visualização:', error)
    showToast('Erro ao gerar o documento. Tente novamente.', 'error')
  } finally {
    isGeneratingContrato.value = false
  }
}

const enviarParaZapSign = async () => {
  if (!selectedTemplateId.value || !foiPrevisualizando.value) return
  isEnviandoZapSign.value = true
  try {
    await axios.post(`/projetos/${props.project.id}/enviar-zapsign`, {
      template_id: selectedTemplateId.value
    })
    props.project.contrato_gerado = true
    props.project.status_assinatura = 'pendente'
    foiPrevisualizando.value = false
    if (contratoBlobUrl.value) {
      URL.revokeObjectURL(contratoBlobUrl.value)
      contratoBlobUrl.value = null
    }
  } catch (error) {
    console.error('Erro ao enviar para ZapSign:', error)
    showToast('Erro ao enviar contrato para assinatura. Tente novamente.', 'error')
  } finally {
    isEnviandoZapSign.value = false
  }
}

const totalSinapi = computed(() => {
  return parseFloat(props.project?.valor) || 0
})

const todosDocumentosAprovados = computed(() => {
  const docs = props.project?.documentos || []
  return ['identidade', 'residencia', 'estado_civil'].every(cat => {
    const doc = docs.find(d => d.categoria === cat)
    return doc?.status === 'aprovado'
  })
})

watch(todosDocumentosAprovados, (approved) => {
  if (approved) fetchTemplatesContrato()
})

// Pan & Zoom state (used for image viewer)
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })

const resetViewer = () => {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
}


const startDrag = (e) => {
  isDragging.value = true
  dragStart.value = { x: e.clientX - panX.value, y: e.clientY - panY.value }
}

const onDrag = (e) => {
  if (!isDragging.value) return
  panX.value = e.clientX - dragStart.value.x
  panY.value = e.clientY - dragStart.value.y
}

const endDrag = () => { isDragging.value = false }

const isImage = computed(() => {
  if (!documentoAtivo.value?.url) return false
  return /\.(jpg|jpeg|png|gif|webp|svg|bmp)(\?|$)/i.test(documentoAtivo.value.url)
})

// Zoom-toward-cursor para imagens (transformOrigin: center center)
const handleWheelImage = (e) => {
  const factor = e.deltaY > 0 ? 0.9 : 1.1
  const newZoom = Math.max(0.25, Math.min(5, zoom.value * factor))
  const rect = e.currentTarget.getBoundingClientRect()
  const cx = rect.width / 2
  const cy = rect.height / 2
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top
  const ratio = newZoom / zoom.value
  panX.value = (mx - cx) * (1 - ratio) + panX.value * ratio
  panY.value = (my - cy) * (1 - ratio) + panY.value * ratio
  zoom.value = newZoom
}

watch(documentoAtivo, (doc) => { if (doc) resetViewer() })

const visualizarDocumento = (doc) => {
  if (window.innerWidth < 1024) {
    window.open(doc.url, '_blank')
  } else {
    documentoAtivo.value = doc
  }
}

const nomeDocumentoAtivo = computed(() => {
  if (!documentoAtivo.value) return ''
  return docCategoriaLabels[documentoAtivo.value.categoria]?.label || documentoAtivo.value.name || 'Documento'
})

const docCategoriaLabels = {
  identidade:   { label: 'Identidade',   badge: 'RG/CNH',      icon: 'badge' },
  residencia:   { label: 'Residência',   badge: 'Comprovante', icon: 'home_work' },
  estado_civil: { label: 'Estado Civil', badge: 'Certidão',    icon: 'family_restroom' }
}

const statusColunaLabels = {
  estimativa_enviada: { label: 'Estimativa Enviada', class: 'bg-orange-55/10 text-orange-600 dark:text-orange-400 border-orange-100 dark:border-orange-950/30' },
  contrato_pendente: { label: 'Contrato Pendente', class: 'bg-blue-55/10 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-950/30' },
  engenharia_caixa: { label: 'Engenharia & Caixa', class: 'bg-indigo-55/10 text-indigo-600 dark:text-indigo-400 border-indigo-100 dark:border-indigo-950/30' },
  obra_liberada: { label: 'Obra Liberada', class: 'bg-violet-55/10 text-violet-600 dark:text-violet-400 border-violet-100 dark:border-violet-950/30' }
}

const qualificacaoUrl = computed(() => {
  if (!props.project?.id) return ''
  return `${window.location.origin}/estimativa/${props.project.id}`
})

const getDocumentStatus = (categoria) => {
  const isEstimativa = props.project?.coluna === 'estimativa_enviada'
  
  if (!props.project?.documentos) {
    if (isEstimativa) {
      return { text: 'Não solicitado', class: 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-zinc-800/30 dark:text-zinc-500 dark:border-zinc-800/50', isPending: true }
    }
    return { text: 'Pendente', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30', isPending: true }
  }
  
  const doc = props.project.documentos.find(d => d.categoria === categoria)
  if (!doc) {
    if (isEstimativa) {
      return { text: 'Não solicitado', class: 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-zinc-800/30 dark:text-zinc-500 dark:border-zinc-800/50', isPending: true }
    }
    return { text: 'Pendente', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30', isPending: true }
  }
  
  if (!doc.url && doc.status === 'rejeitado') {
    return { text: 'Recusado', class: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900/30', isRejected: true, motivo: doc.motivo }
  }
  
  if (doc.url) {
    if (props.project.status === 'docs_validados' || doc.status === 'aprovado') {
      return { text: 'Aprovado', class: 'bg-emerald-55/10 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-950/30', doc }
    }
    return { text: 'Em Análise', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30', doc }
  }
  
  if (isEstimativa) {
    return { text: 'Não solicitado', class: 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-zinc-800/30 dark:text-zinc-500 dark:border-zinc-800/50', isPending: true }
  }
  return { text: 'Pendente', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30', isPending: true }
}

const temDocumentosPendentesRevisao = computed(() => {
  if (props.project?.coluna !== 'contrato_pendente') return false
  if (props.project?.status === 'docs_validados') return false
  return Array.isArray(props.project?.documentos) && props.project.documentos.some(doc =>
    !!doc.url && doc.status !== 'aprovado' && doc.status !== 'rejeitado'
  )
})

const documentsList = computed(() => {
  return ['identidade', 'residencia', 'estado_civil'].map(cat => {
    const statusInfo = getDocumentStatus(cat)
    return {
      categoria: cat,
      label: docCategoriaLabels[cat].label,
      badge: docCategoriaLabels[cat].badge,
      icon: docCategoriaLabels[cat].icon,
      status: statusInfo
    }
  })
})

const getContractStatus = computed(() => {
  if (props.project?.status_assinatura === 'assinado') {
    return { text: 'Assinado', class: 'bg-emerald-55/10 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-950/30' }
  }
  if (props.project?.status_assinatura === 'pendente') {
    return { text: 'Aguardando Assinatura', class: 'bg-blue-55/10 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-950/30' }
  }
  if (props.project?.contrato_gerado) {
    return { text: 'Gerado (Não enviado)', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30' }
  }
  return { text: 'Não Gerado', class: 'bg-slate-50 text-slate-500 border-slate-200 dark:bg-zinc-800/50 dark:text-zinc-400 dark:border-zinc-800' }
})

const fetchHistorico = async () => {
  if (!props.project?.id) return
  isLoadingHistory.value = true
  try {
    const res = await axios.get(`/projetos/${props.project.id}/historico`)
    if (res.data && res.data.success) {
      historico.value = res.data.data.slice(0, 5) // Top 5
    }
  } catch (error) {
    console.error('Erro ao buscar histórico do projeto:', error)
  } finally {
    isLoadingHistory.value = false
  }
}

const fetchPortalLink = async () => {
  if (!props.project?.id) return
  isLoadingPortal.value = true
  try {
    const res = await axios.get(`/portal/projetos/${props.project.id}/link`)
    if (res.data && res.data.url_publica) {
      const urlParts = res.data.url_publica.split('/')
      const token = urlParts[urlParts.length - 1]
      portalUrl.value = `${window.location.origin}/portal/${token}`
      portalPin.value = res.data.pin_acesso
    } else {
      portalUrl.value = ''
      portalPin.value = ''
    }
  } catch (error) {
    console.error('Erro ao carregar link do portal:', error)
    portalUrl.value = ''
    portalPin.value = ''
  } finally {
    isLoadingPortal.value = false
  }
}

const handleWhatsAppShare = () => {
  if (!portalUrl.value) return
  const msg = `Olá ${props.project.cliente_nome}! Segue o link para acompanhar a evolução da sua obra em tempo real:\n${portalUrl.value}\n\nPIN de acesso: ${portalPin.value}`
  const telefoneLimpo = props.project.telefone ? props.project.telefone.replace(/\D/g, '') : ''
  window.open(`https://wa.me/${telefoneLimpo}?text=${encodeURIComponent(msg)}`, '_blank')
}

const handleCopyLink = () => {
  if (!portalUrl.value || isPortalCopied.value) return
  navigator.clipboard.writeText(portalUrl.value)
  isPortalCopied.value = true
  setTimeout(() => {
    isPortalCopied.value = false
  }, 2000)
}

const handleCopyQualificacao = () => {
  if (!qualificacaoUrl.value || isQualificacaoCopied.value) return
  navigator.clipboard.writeText(qualificacaoUrl.value)
  isQualificacaoCopied.value = true
  setTimeout(() => {
    isQualificacaoCopied.value = false
  }, 2000)
}

const handleWhatsAppQualificacao = () => {
  if (!qualificacaoUrl.value) return
  const msg = `Olá ${props.project.cliente_nome}! Segue o link para realizar a simulação da sua obra e enviar os documentos:\n${qualificacaoUrl.value}`
  const telefoneLimpo = props.project.telefone ? props.project.telefone.replace(/\D/g, '') : ''
  window.open(`https://wa.me/${telefoneLimpo}?text=${encodeURIComponent(msg)}`, '_blank')
}

const formatarData = (dataStr) => {
  if (!dataStr) return ''
  try {
    const dateObj = new Date(dataStr.includes('T') ? dataStr : dataStr.replace(' ', 'T') + 'Z')
    if (isNaN(dateObj.getTime())) {
      const partes = dataStr.split(' ')
      if (partes.length < 2) return dataStr
      const dataPart = partes[0]
      const horaPart = partes[1].slice(0, 5)
      const dataSplit = dataPart.split('-')
      if (dataSplit.length < 3) return dataStr
      const [ano, mes, dia] = dataSplit
      return `${dia}/${mes}/${ano} ${horaPart}`
    }
    const dia = String(dateObj.getDate()).padStart(2, '0')
    const mes = String(dateObj.getMonth() + 1).padStart(2, '0')
    const ano = dateObj.getFullYear()
    const hora = String(dateObj.getHours()).padStart(2, '0')
    const minuto = String(dateObj.getMinutes()).padStart(2, '0')
    return `${dia}/${mes}/${ano} ${hora}:${minuto}`
  } catch (e) {
    const partes = dataStr.split(' ')
    if (partes.length < 2) return dataStr
    const dataPart = partes[0]
    const horaPart = partes[1].slice(0, 5)
    const dataSplit = dataPart.split('-')
    if (dataSplit.length < 3) return dataStr
    const [ano, mes, dia] = dataSplit
    return `${dia}/${mes}/${ano} ${horaPart}`
  }
}

const irParaOrcamento = () => {
  router.push(`/orcamento/${props.project.id}`)
  emit('close')
}

const closeDrawer = () => {
  emit('close')
}

const abrirModalRejeicao = (doc) => {
  selectedDocParaRejeicao.value = doc
  isRejeicaoModalOpen.value = true
}

const onDocRejeitado = (docsAtualizados) => {
  if (docsAtualizados) {
    props.project.documentos = [...docsAtualizados]
  }
}

const onSetupSuccess = () => {
  isSetupOpen.value = false
  emit('update')
}

const aprovarDocumento = async (doc) => {
  try {
    const docsAtualizados = (props.project.documentos || []).map(d => {
      if (d.categoria === doc.categoria) {
        return { ...d, status: 'aprovado', done: true }
      }
      return d
    })
    await axios.patch(`/projetos/${props.project.id}`, { documentos: docsAtualizados })
    props.project.documentos = [...docsAtualizados]
  } catch (error) {
    console.error('Erro ao aprovar documento:', error)
    showToast('Erro ao aprovar documento. Tente novamente.', 'error')
  }
}

const isLiberandoObra = ref(false)

const liberarObra = async () => {
  if (isLiberandoObra.value) return
  isLiberandoObra.value = true
  try {
    await axios.patch(`/projetos/${props.project.id}`, {
      coluna: 'obra_liberada',
      status: 'liberada'
    })
    props.project.coluna = 'obra_liberada'
    props.project.status = 'liberada'
    emit('update')
  } catch (error) {
    console.error('Erro ao liberar obra:', error)
    showToast('Erro ao liberar a obra. Tente novamente.', 'error')
  } finally {
    isLiberandoObra.value = false
  }
}

const validarDocumentos = async () => {
  try {
    const docsAtualizados = (props.project.documentos || []).map(doc => {
      if (doc.url) {
        return { ...doc, status: 'aprovado', done: true }
      }
      return doc
    })

    await axios.patch(`/projetos/${props.project.id}`, {
      status: 'docs_validados',
      documentos: docsAtualizados
    })
    
    props.project.status = 'docs_validados'
    props.project.documentos = [...docsAtualizados]
  } catch (error) {
    console.error('Erro ao validar documentos:', error)
    showToast('Erro ao validar documentos. Tente novamente.', 'error')
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchHistorico()
    fetchPortalLink()
    if (props.project?.coluna === 'engenharia_caixa' || todosDocumentosAprovados.value) {
      fetchTemplatesContrato()
    }
    if (props.documentoInicial) {
      documentoAtivo.value = props.documentoInicial
    }
  } else {
    documentoAtivo.value = null
    foiPrevisualizando.value = false
    templatesContrato.value = []
    if (contratoBlobUrl.value) {
      URL.revokeObjectURL(contratoBlobUrl.value)
      contratoBlobUrl.value = null
    }
  }
})
</script>

<template>
  <Teleport to="body">
    <!-- Overlay backdrop -->
    <Transition
      enter-active-class="transition-opacity duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-0 lg:p-4"
        :style="`z-index: ${zIndex}`"
        @click.self="closeDrawer"
      >
        <!-- Modal Panel -->
        <div 
          class="bg-canvas border border-hairline shadow-2xl flex flex-row w-full h-full lg:max-h-[85vh] lg:rounded-2xl overflow-hidden animate-in zoom-in duration-200 transition-all duration-300 ease-in-out"
          :class="documentoAtivo ? 'lg:w-[1200px] max-w-7xl' : 'lg:w-[600px] max-w-2xl'"
          @click.stop
        >
          <!-- Painel Esquerdo: Detalhamento do Projeto -->
          <div class="w-full lg:w-[600px] shrink-0 flex flex-col h-full bg-canvas">
          <!-- Header -->
          <div class="px-6 py-5 border-b border-hairline bg-surface shrink-0 flex items-center justify-between">
            <div>
              <span class="text-[10px] font-bold text-ink-muted uppercase tracking-wider block">Detalhamento do Projeto</span>
              <h2 class="text-lg font-bold text-ink truncate max-w-[320px] mt-0.5" :title="project.titulo_projeto || project.cliente_nome">
                {{ project.titulo_projeto || 'Sem título' }}
              </h2>
            </div>
            <button @click="closeDrawer" class="p-2 rounded-xl bg-canvas text-ink-muted hover:bg-surface-hover hover:text-ink transition-colors cursor-pointer flex items-center justify-center">
              <X class="w-5 h-5" stroke-width="1.5" />
            </button>
          </div>

          <!-- Scrollable Content -->
          <div class="flex-1 overflow-y-auto min-h-0 p-6 custom-scrollbar flex flex-col gap-6">

            <!-- Banner: Modo Leitura (Arquivado) -->
            <div
              v-if="isArquivado"
              class="flex items-start gap-3 px-4 py-3 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40"
            >
              <Archive class="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" stroke-width="1.5" />
              <p class="text-xs text-amber-800 dark:text-amber-300 leading-relaxed font-medium">
                Este projeto está arquivado — visualização somente leitura. Restaure-o para o Kanban para realizar qualquer ação.
              </p>
            </div>

            <!-- 1. Identificação -->
            <div class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs text-ink-muted">Cliente</p>
                  <p class="text-sm font-bold text-ink mt-0.5">{{ project.cliente_nome }}</p>
                </div>
                <div class="flex items-center gap-2">
                  <!-- Botão Editar Configurações da Obra -->
                  <button 
                    @click="isSetupOpen = true"
                    class="p-1.5 rounded-lg bg-canvas border border-hairline hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors flex items-center justify-center cursor-pointer shadow-sm"
                    title="Editar Configurações da Obra"
                  >
                    <Pen class="w-4 h-4" stroke-width="1.5" />
                  </button>
                  <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full border shrink-0', statusColunaLabels[project.coluna]?.class]">
                    {{ statusColunaLabels[project.coluna]?.label || project.coluna }}
                  </span>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4 pt-3 border-t border-hairline">
                <div>
                  <p class="text-[11px] text-ink-muted">UF da Obra</p>
                  <p class="text-xs font-semibold text-ink mt-0.5">{{ project.uf_obra || 'Não informado' }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-ink-muted">BDI Padrão</p>
                  <p class="text-xs font-semibold text-ink mt-0.5">{{ project.bdi_padrao != null ? `${project.bdi_padrao}%` : '20%' }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-ink-muted">Mês SINAPI</p>
                  <p class="text-xs font-semibold text-ink mt-0.5">{{ project.sinapi_mes_ano || 'Não informado' }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-ink-muted">Metragem (m²)</p>
                  <p class="text-xs font-mono font-semibold text-ink mt-0.5">{{ project.tamanho || '-' }} m²</p>
                </div>
              </div>
              
              <div class="pt-3 border-t border-hairline flex items-center justify-between">
                <p class="text-xs text-ink-muted">Valor Total Estimado</p>
                <p class="text-base font-bold text-ink">{{ formatCurrency(project.valor, 'Aguardando preenchimento') }}</p>
              </div>
            </div>

            <!-- 2. Ações Rápidas (Acesso & Compartilhamento) — oculto em modo arquivado -->
            <div v-if="!isArquivado" class="space-y-4">
              <!-- Orçamento Completo Visível Apenas em Engenharia & Caixa ou Obra Liberada -->
              <button 
                v-if="project.coluna === 'engenharia_caixa' || project.coluna === 'obra_liberada'"
                @click="irParaOrcamento"
                class="w-full py-3 bg-ink hover:bg-brand-hover text-canvas rounded-xl font-semibold text-sm transition-all shadow-md flex items-center justify-center gap-2 group cursor-pointer"
              >
                <HardHat class="w-4 h-4 group-hover:translate-x-0.5 transition-transform" stroke-width="1.5" />
                Acessar Orçamento Completo
              </button>

              <div v-else-if="project.coluna === 'estimativa_enviada'" class="p-4 bg-amber-55/10 border border-amber-100 dark:border-amber-950/30 rounded-xl flex items-start gap-3">
                <Info class="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" stroke-width="1.5" />
                <p class="text-xs text-amber-800 dark:text-amber-300 leading-relaxed font-medium">
                  O orçamento detalhado estará disponível após o cliente realizar a simulação e enviar os documentos para análise.
                </p>
              </div>

              <div v-else-if="project.coluna === 'contrato_pendente'" class="p-4 bg-amber-55/10 border border-amber-100 dark:border-amber-950/30 rounded-xl flex items-start gap-3">
                <Info class="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" stroke-width="1.5" />
                <p class="text-xs text-amber-800 dark:text-amber-300 leading-relaxed font-medium">
                  O orçamento detalhado estará disponível após a validação dos documentos e a assinatura do contrato (esteira Engenharia & Caixa).
                </p>
              </div>

              <!-- B2C Jornada de Qualificação -->
              <div v-if="project.coluna === 'estimativa_enviada' || project.coluna === 'contrato_pendente'" class="bg-surface border border-hairline p-4 rounded-xl shadow-sm space-y-3">
                <div class="flex items-center gap-2">
                  <UserCheck class="w-4 h-4 text-blue-600" stroke-width="1.5" />
                  <span class="text-xs font-bold text-ink uppercase tracking-wider">Jornada de Qualificação (B2C)</span>
                </div>
                <p class="text-xs text-ink-muted leading-relaxed">
                  Link para o cliente realizar a simulação Caixa, especificar padrão/tamanho da obra e anexar documentos iniciais.
                </p>
                <div class="space-y-3">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 bg-canvas border border-hairline rounded-lg px-3 py-2 text-xs font-mono text-ink select-all overflow-x-auto whitespace-nowrap">
                      {{ qualificacaoUrl }}
                    </div>
                    <button 
                      @click="handleCopyQualificacao"
                      class="p-2 rounded-lg bg-canvas border border-hairline hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors cursor-pointer flex items-center justify-center shrink-0"
                      title="Copiar Link"
                    >
                      <Check v-if="isQualificacaoCopied" class="w-4 h-4 text-emerald-600" stroke-width="1.5" />
                      <Copy v-else class="w-4 h-4" stroke-width="1.5" />
                    </button>
                  </div>
                  <div class="flex justify-end">
                    <button 
                      @click="handleWhatsAppQualificacao"
                      class="px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                    >
                      <MessageSquare class="w-4 h-4 text-emerald-700" stroke-width="1.5" />
                      Compartilhar no WhatsApp
                    </button>
                  </div>
                </div>
              </div>

              <!-- B2C Portal de Acompanhamento (Obra Liberada) -->
              <div v-if="project.coluna === 'obra_liberada'" class="bg-surface border border-hairline p-4 rounded-xl shadow-sm space-y-3">
                <div class="flex items-center gap-2">
                  <Share2 class="w-4 h-4 text-indigo-600" stroke-width="1.5" />
                  <span class="text-xs font-bold text-ink uppercase tracking-wider">Portal de Acompanhamento</span>
                </div>
                <p class="text-xs text-ink-muted leading-relaxed">
                  Este cliente possui acesso ao Portal da Obra para acompanhar o feed e a medição Caixa em tempo real.
                </p>
                <div v-if="isLoadingPortal" class="flex items-center gap-2 text-xs text-ink-muted">
                  <Loader2 class="w-4 h-4 animate-spin text-brand-primary" stroke-width="1.5" />
                  Carregando link do portal...
                </div>
                <div v-else class="space-y-3">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 bg-canvas border border-hairline rounded-lg px-3 py-2 text-xs font-mono text-ink select-all overflow-x-auto whitespace-nowrap">
                      {{ portalUrl }}
                    </div>
                    <button 
                      @click="handleCopyLink"
                      class="p-2 rounded-lg bg-canvas border border-hairline hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors cursor-pointer flex items-center justify-center shrink-0"
                      title="Copiar Link"
                    >
                      <Check v-if="isPortalCopied" class="w-4 h-4 text-emerald-600" stroke-width="1.5" />
                      <Copy v-else class="w-4 h-4" stroke-width="1.5" />
                    </button>
                  </div>
                  <div class="flex items-center justify-between gap-3">
                    <div class="text-xs">
                      <span class="text-ink-muted">PIN de Acesso: </span>
                      <span class="font-bold font-mono text-ink">{{ portalPin }}</span>
                    </div>
                    <button 
                      @click="handleWhatsAppShare"
                      class="px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                    >
                      <MessageSquare class="w-4 h-4 text-emerald-700" stroke-width="1.5" />
                      Enviar WhatsApp
                    </button>
                  </div>
                </div>
              </div>

              <!-- Botão Liberar Obra (Engenharia & Caixa → Obra Liberada) -->
              <button
                v-if="project.coluna === 'engenharia_caixa'"
                @click="liberarObra"
                :disabled="isLiberandoObra"
                class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-xl font-semibold text-sm transition-all shadow-md flex items-center justify-center gap-2 group cursor-pointer"
              >
                <Loader2 v-if="isLiberandoObra" class="w-4 h-4 animate-spin" stroke-width="1.5" />
                <CheckCircle2 v-else class="w-4 h-4" stroke-width="1.5" />
                {{ isLiberandoObra ? 'Liberando...' : 'Aprovar e Liberar Obra' }}
              </button>

              <!-- B2C Portal Bloqueado (Engenharia & Caixa) -->
              <div v-if="project.coluna === 'engenharia_caixa'" class="bg-surface/60 border border-hairline p-4 rounded-xl shadow-sm space-y-2.5">
                <div class="flex items-center gap-2 text-ink-muted">
                  <Lock class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
                  <span class="text-xs font-bold uppercase tracking-wider">Acesso ao Portal de Obra</span>
                </div>
                <p class="text-xs text-ink-muted leading-relaxed font-medium">
                  O Portal de Acompanhamento da Obra (feed em tempo real e medições da Caixa) será liberado automaticamente após a assinatura do contrato e a liberação da obra (coluna Obra Liberada).
                </p>
              </div>
            </div>

            <!-- 3. Vault de Documentos -->
            <div class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <FolderOpen class="w-4 h-4 text-blue-600" stroke-width="1.5" />
                  <span class="text-xs font-bold text-ink uppercase tracking-wider">Cofre de Documentos</span>
                  <span 
                    v-if="temDocumentosPendentesRevisao" 
                    class="w-2 h-2 rounded-full bg-blue-500 animate-pulse shrink-0 cursor-help"
                    title="Documento pendente de visualização"
                  ></span>
                </div>
                <!-- Botão Aprovar Todos (visível se tiver documentos pendentes — oculto quando arquivado) -->
                <button
                  v-if="temDocumentosPendentesRevisao && !isArquivado"
                  @click="validarDocumentos"
                  class="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg transition-colors text-xs font-bold flex items-center gap-1.5 cursor-pointer shadow-sm"
                >
                  <CheckCircle2 class="w-4 h-4 text-emerald-700" stroke-width="1.5" />
                  Aprovar Todos
                </button>
              </div>
              
              <ul class="space-y-3">
                <li 
                  v-for="doc in documentsList" 
                  :key="doc.categoria"
                  class="flex flex-col gap-2 p-3 rounded-lg border border-hairline bg-canvas/50"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <component :is="iconMap[doc.icon]" class="w-4 h-4 text-blue-500" stroke-width="1.5" />
                      <span class="text-xs font-bold text-ink">{{ doc.label }}</span>
                    </div>
                    <span :class="['text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider', doc.status.class]">
                      {{ doc.status.text }}
                    </span>
                  </div>
                  
                  <div v-if="doc.status.doc" class="flex items-center justify-between text-xs mt-1 bg-surface p-2 rounded border border-hairline">
                    <span class="text-ink-muted truncate max-w-[200px]" :title="doc.status.doc.name">{{ doc.status.doc.name }}</span>
                    <div class="flex items-center gap-2 shrink-0">
                      <button @click.prevent="visualizarDocumento(doc.status.doc)" class="text-brand-primary hover:underline flex items-center gap-1 font-semibold cursor-pointer">
                        <Eye class="w-3.5 h-3.5" stroke-width="1.5" />
                        Visualizar
                      </button>
                      <template v-if="!isArquivado && project.coluna === 'contrato_pendente' && project.status !== 'docs_validados' && doc.status.text !== 'Aprovado' && doc.status.doc.url">
                        <button
                          @click.stop="aprovarDocumento(doc.status.doc)"
                          title="Aprovar Documento"
                          class="w-6 h-6 flex items-center justify-center rounded border border-emerald-200 bg-emerald-50/50 text-emerald-600 hover:bg-emerald-100 transition-colors cursor-pointer"
                        >
                          <Check class="w-3.5 h-3.5" stroke-width="2.5" />
                        </button>
                        <button
                          @click.stop="abrirModalRejeicao(doc.status.doc)"
                          title="Recusar Documento"
                          class="w-6 h-6 flex items-center justify-center rounded border border-red-200 bg-red-50/50 text-red-600 hover:bg-red-100 transition-colors cursor-pointer"
                        >
                          <X class="w-3.5 h-3.5" stroke-width="2.5" />
                        </button>
                      </template>
                    </div>
                  </div>
                  
                  <div v-else-if="doc.status.isRejected" class="text-xs text-red-600 bg-red-50/50 p-2 rounded border border-red-100 leading-relaxed">
                    <span class="font-bold">Motivo da recusa:</span> {{ doc.status.motivo }}
                  </div>
                </li>
              </ul>
            </div>

            <!-- 3b. Contrato Comercial (coluna contrato_pendente + docs aprovados) -->
            <Transition
              enter-active-class="transition-all duration-300 ease-out"
              enter-from-class="opacity-0 -translate-y-2"
              enter-to-class="opacity-100 translate-y-0"
            >
              <div v-if="todosDocumentosAprovados && project.coluna === 'contrato_pendente'" class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
                
                <!-- Header da seção -->
                <div class="flex items-center gap-2">
                  <FileText class="w-4 h-4 text-blue-600 shrink-0" stroke-width="1.5" />
                  <span class="text-xs font-bold text-ink uppercase tracking-wider">Contrato Comercial</span>
                  <span class="ml-auto text-[10px] font-bold px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-900/40 uppercase tracking-wider shrink-0">
                    Docs Validados ✓
                  </span>
                </div>

                <!-- Status do Contrato (Sempre visível) -->
                <div class="flex items-center justify-between p-3 rounded-lg border border-hairline bg-canvas/50">
                  <span class="text-xs text-ink-muted">Status do Contrato</span>
                  <span :class="['text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider', getContractStatus.class]">
                    {{ getContractStatus.text }}
                  </span>
                </div>

                <!-- ESTADO 1: Selecionar e enviar — oculto quando arquivado -->
                <template v-if="(!project.status_assinatura || project.status_assinatura === 'nao_enviado') && !isArquivado">
                  <p class="text-xs text-ink-muted leading-relaxed">
                    Selecione o template da proposta comercial, pré-visualize o documento e confirme o envio para coleta de assinaturas via ZapSign.
                  </p>

                  <!-- Seletor de template -->
                  <div>
                    <label class="block text-[11px] font-semibold text-ink-muted mb-1.5 uppercase tracking-wider">Template do Contrato</label>
                    <div v-if="isLoadingTemplates" class="flex items-center gap-2 text-xs text-ink-muted py-2">
                      <Loader2 class="w-3.5 h-3.5 animate-spin text-brand-primary" stroke-width="1.5" />
                      Carregando templates...
                    </div>
                    <div v-else-if="templatesContrato.length === 0" class="text-xs text-ink-muted bg-canvas border border-dashed border-hairline p-3 rounded-lg flex flex-col items-center gap-2 text-center">
                      <span>Nenhuma proposta comercial cadastrada.</span>
                      <button 
                        @click="router.push('/configuracoes/contratos'); emit('close')" 
                        class="text-[11px] text-blue-500 hover:text-blue-600 font-semibold flex items-center gap-1.5 cursor-pointer hover:underline border-0 bg-transparent p-0"
                      >
                        <Pen class="w-3.5 h-3.5" stroke-width="1.5" />
                        Configurar Templates
                      </button>
                    </div>
                    <div v-else class="relative">
                      <select
                        v-model="selectedTemplateId"
                        @change="foiPrevisualizando = false"
                        class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2 px-3 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/30 appearance-none cursor-pointer font-medium"
                      >
                        <option v-for="t in templatesContrato" :key="t.id" :value="t.id">{{ t.titulo }}</option>
                      </select>
                      <ExternalLink class="w-3.5 h-3.5 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
                    </div>
                  </div>

                  <!-- Ações -->
                  <div class="flex items-center gap-2">
                    <!-- Pré-visualizar -->
                    <button
                      @click="previewContrato"
                      :disabled="!selectedTemplateId || isGeneratingContrato"
                      class="flex-1 py-2 flex items-center justify-center gap-1.5 rounded-lg border border-hairline bg-canvas hover:bg-surface-hover text-ink text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                      <Loader2 v-if="isGeneratingContrato" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                      <Eye v-else class="w-3.5 h-3.5" stroke-width="1.5" />
                      {{ isGeneratingContrato ? 'Gerando...' : 'Pré-visualizar' }}
                    </button>

                    <!-- Enviar para ZapSign -->
                    <button
                      @click="enviarParaZapSign"
                      :disabled="!foiPrevisualizando || isEnviandoZapSign"
                      :title="!foiPrevisualizando ? 'Pré-visualize o contrato antes de enviar' : ''"
                      class="flex-1 py-2 flex items-center justify-center gap-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-900/40 disabled:cursor-not-allowed text-white text-xs font-semibold transition-colors cursor-pointer"
                    >
                      <Loader2 v-if="isEnviandoZapSign" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                      <Send v-else class="w-3.5 h-3.5" stroke-width="1.5" />
                      {{ isEnviandoZapSign ? 'Enviando...' : 'Enviar para ZapSign' }}
                    </button>
                  </div>

                  <!-- Hint de desbloqueio do botão ZapSign -->
                  <p v-if="!foiPrevisualizando && selectedTemplateId" class="text-[10px] text-ink-muted text-center">
                    Pré-visualize o documento para habilitar o envio.
                  </p>
                </template>

                <!-- ESTADO 2: Aguardando assinaturas -->
                <template v-else-if="project.status_assinatura === 'pendente'">
                  <div class="flex items-center gap-2 text-blue-600">
                    <Loader2 class="w-4 h-4 animate-spin" stroke-width="1.5" />
                    <span class="text-xs font-semibold">Aguardando Assinaturas via ZapSign</span>
                  </div>
                  <p class="text-xs text-ink-muted leading-relaxed">O contrato foi enviado. As partes receberão o link de assinatura por e-mail.</p>

                  <!-- Progresso de assinaturas -->
                  <div class="space-y-2">
                    <div class="flex items-center justify-between p-2.5 rounded-lg border border-hairline bg-canvas/60 text-xs">
                      <div class="flex items-center gap-2">
                        <User class="w-3.5 h-3.5 text-ink-muted" stroke-width="1.5" />
                        <span :class="project.engenheiro_assinou ? 'text-emerald-600 font-bold' : 'text-ink-muted'">Engenheiro</span>
                      </div>
                      <span class="text-[10px] font-bold px-2 py-0.5 rounded border"
                        :class="project.engenheiro_assinou
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-600 border-amber-200'">
                        {{ project.engenheiro_assinou ? 'Assinou ✓' : 'Pendente' }}
                      </span>
                    </div>
                    <div class="flex items-center justify-between p-2.5 rounded-lg border border-hairline bg-canvas/60 text-xs">
                      <div class="flex items-center gap-2">
                        <User class="w-3.5 h-3.5 text-ink-muted" stroke-width="1.5" />
                        <span :class="project.cliente_assinou ? 'text-emerald-600 font-bold' : 'text-ink-muted'">{{ project.cliente_nome }}</span>
                      </div>
                      <span class="text-[10px] font-bold px-2 py-0.5 rounded border"
                        :class="project.cliente_assinou
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-600 border-amber-200'">
                        {{ project.cliente_assinou ? 'Assinou ✓' : 'Pendente' }}
                      </span>
                    </div>
                  </div>
                </template>

                <!-- ESTADO 3: Contrato assinado por ambos -->
                <template v-else-if="project.status_assinatura === 'assinado'">
                  <div class="flex items-center gap-2">
                    <CheckCircle2 class="w-4 h-4 text-emerald-600" stroke-width="2" />
                    <span class="text-xs font-bold text-emerald-600">Contrato Assinado por Ambas as Partes</span>
                  </div>

                  <!-- Confirmação visual de quem assinou -->
                  <div class="space-y-1.5">
                    <div class="flex items-center justify-between p-2.5 rounded-lg border border-emerald-100 dark:border-emerald-900/40 bg-emerald-50/50 dark:bg-emerald-950/20 text-xs">
                      <div class="flex items-center gap-2">
                        <User class="w-3.5 h-3.5 text-emerald-600" stroke-width="1.5" />
                        <span class="text-emerald-700 dark:text-emerald-400 font-semibold">Engenheiro</span>
                      </div>
                      <span class="text-[10px] font-bold px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-900/40">
                        Assinou ✓
                      </span>
                    </div>
                    <div class="flex items-center justify-between p-2.5 rounded-lg border border-emerald-100 dark:border-emerald-900/40 bg-emerald-50/50 dark:bg-emerald-950/20 text-xs">
                      <div class="flex items-center gap-2">
                        <User class="w-3.5 h-3.5 text-emerald-600" stroke-width="1.5" />
                        <span class="text-emerald-700 dark:text-emerald-400 font-semibold">{{ project.cliente_nome }}</span>
                      </div>
                      <span class="text-[10px] font-bold px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-900/40">
                        Assinou ✓
                      </span>
                    </div>
                  </div>

                  <p class="text-xs text-ink-muted leading-relaxed">
                    O projeto está pronto para avançar para <strong class="text-ink">Engenharia & Caixa</strong>.
                  </p>

                  <!-- Botão de visualização do contrato assinado -->
                  <a
                    v-if="project.url_contrato_assinado"
                    :href="project.url_contrato_assinado"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="flex items-center justify-center gap-2 py-2 px-4 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/30 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 text-xs font-semibold transition-colors w-full"
                  >
                    <ExternalLink class="w-3.5 h-3.5" stroke-width="1.5" />
                    Visualizar Contrato Assinado
                  </a>
                </template>

              </div>
            </Transition>

            <!-- 4. Contrato de Serviço (apenas em Engenharia & Caixa / Obra Liberada) -->
            <div v-if="project.coluna === 'engenharia_caixa' || project.coluna === 'obra_liberada'" class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
              <div class="flex items-center gap-2">
                <FileText class="w-4 h-4 text-emerald-600" stroke-width="1.5" />
                <span class="text-xs font-bold text-ink uppercase tracking-wider">Contrato de Serviço</span>
              </div>

              <!-- Status do Contrato (Sempre visível) -->
              <div class="flex items-center justify-between p-3 rounded-lg border border-hairline bg-canvas/50">
                <span class="text-xs text-ink-muted">Status do Contrato</span>
                <span :class="['text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider', getContractStatus.class]">
                  {{ getContractStatus.text }}
                </span>
              </div>

              <!-- Se estiver em Engenharia & Caixa e contrato NÃO enviado — oculto quando arquivado -->
              <template v-if="!isArquivado && project.coluna === 'engenharia_caixa' && (!project.status_assinatura || project.status_assinatura === 'nao_enviado')">
                <!-- Caso o orçamento esteja vazio -->
                <div v-if="totalSinapi <= 0" class="p-3 bg-amber-55/10 border border-amber-100 rounded-lg flex items-start gap-2.5">
                  <Info class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" stroke-width="1.5" />
                  <p class="text-[11px] text-amber-800 leading-relaxed font-medium">
                    Adicione itens ao orçamento SINAPI antes de gerar o Contrato de Construção.
                  </p>
                </div>
                
                <!-- Caso possua orçamento montado -->
                <div v-else class="space-y-4 pt-2">
                  <p class="text-xs text-ink-muted leading-relaxed">
                    Selecione o template do contrato de serviço, pré-visualize o documento e confirme o envio para coleta de assinaturas via ZapSign.
                  </p>

                  <!-- Seletor de template -->
                  <div>
                    <label class="block text-[11px] font-semibold text-ink-muted mb-1.5 uppercase tracking-wider">Template do Contrato</label>
                    <div v-if="isLoadingTemplates" class="flex items-center gap-2 text-xs text-ink-muted py-2">
                      <Loader2 class="w-3.5 h-3.5 animate-spin text-brand-primary" stroke-width="1.5" />
                      Carregando templates...
                    </div>
                    
                    <!-- EMPTY STATE UX (Ponto 3) -->
                    <div v-else-if="templatesContrato.length === 0" class="text-xs text-ink-muted bg-canvas border border-dashed border-hairline p-3 rounded-lg flex flex-col items-center gap-2 text-center">
                      <span>Nenhum template de contrato cadastrado.</span>
                      <button 
                        @click="router.push('/configuracoes/contratos'); emit('close')" 
                        class="text-[11px] text-blue-500 hover:text-blue-600 font-semibold flex items-center gap-1.5 cursor-pointer hover:underline border-0 bg-transparent p-0"
                      >
                        <Pen class="w-3.5 h-3.5" stroke-width="1.5" />
                        Configurar Templates
                      </button>
                    </div>
                    
                    <div v-else class="relative">
                      <select
                        v-model="selectedTemplateId"
                        @change="foiPrevisualizando = false"
                        class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2 px-3 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/30 appearance-none cursor-pointer font-medium"
                      >
                        <option v-for="t in templatesContrato" :key="t.id" :value="t.id">{{ t.titulo }}</option>
                      </select>
                      <ExternalLink class="w-3.5 h-3.5 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
                    </div>
                  </div>

                  <!-- Ações -->
                  <div class="flex items-center gap-2">
                    <!-- Pré-visualizar -->
                    <button
                      @click="previewContrato"
                      :disabled="!selectedTemplateId || isGeneratingContrato"
                      class="flex-1 py-2 flex items-center justify-center gap-1.5 rounded-lg border border-hairline bg-canvas hover:bg-surface-hover text-ink text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                      <Loader2 v-if="isGeneratingContrato" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                      <Eye v-else class="w-3.5 h-3.5" stroke-width="1.5" />
                      {{ isGeneratingContrato ? 'Gerando...' : 'Pré-visualizar' }}
                    </button>

                    <!-- Enviar para ZapSign -->
                    <button
                      @click="enviarParaZapSign"
                      :disabled="!foiPrevisualizando || isEnviandoZapSign"
                      :title="!foiPrevisualizando ? 'Pré-visualize o contrato antes de enviar' : ''"
                      class="flex-1 py-2 flex items-center justify-center gap-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-900/40 disabled:cursor-not-allowed text-white text-xs font-semibold transition-colors cursor-pointer"
                    >
                      <Loader2 v-if="isEnviandoZapSign" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                      <Send v-else class="w-3.5 h-3.5" stroke-width="1.5" />
                      {{ isEnviandoZapSign ? 'Enviando...' : 'Enviar para ZapSign' }}
                    </button>
                  </div>

                  <!-- Hint de desbloqueio do botão ZapSign -->
                  <p v-if="!foiPrevisualizando && selectedTemplateId" class="text-[10px] text-ink-muted text-center">
                    Pré-visualize o documento para habilitar o envio.
                  </p>
                </div>
              </template>

              <!-- Assinaturas: pendente ou assinado (engenharia_caixa / obra_liberada) -->
              <div v-else-if="project.status_assinatura === 'pendente' || project.status_assinatura === 'assinado'" class="space-y-3">

                <!-- Progresso de assinaturas -->
                <div class="p-3 bg-canvas/30 rounded-lg border border-hairline space-y-2">
                  <p class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">
                    {{ project.status_assinatura === 'assinado' ? 'Contrato Assinado por Ambas as Partes' : 'Aguardando Assinaturas' }}
                  </p>
                  <div class="flex items-center justify-between text-xs">
                    <div class="flex items-center gap-1.5">
                      <User class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
                      <span class="font-medium" :class="project.engenheiro_assinou ? 'text-emerald-600 font-bold' : 'text-ink-muted'">Engenheiro</span>
                    </div>
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded border"
                      :class="project.engenheiro_assinou
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-900/40'
                        : 'bg-amber-50 text-amber-600 border-amber-200'">
                      {{ project.engenheiro_assinou ? 'Assinou ✓' : 'Pendente' }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between text-xs">
                    <div class="flex items-center gap-1.5">
                      <User class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
                      <span class="font-medium" :class="project.cliente_assinou ? 'text-emerald-600 font-bold' : 'text-ink-muted'">{{ project.cliente_nome }}</span>
                    </div>
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded border"
                      :class="project.cliente_assinou
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-900/40'
                        : 'bg-amber-50 text-amber-600 border-amber-200'">
                      {{ project.cliente_assinou ? 'Assinou ✓' : 'Pendente' }}
                    </span>
                  </div>
                </div>

                <!-- Botão de visualização disponível após assinatura total -->
                <a
                  v-if="project.status_assinatura === 'assinado' && project.url_contrato_assinado"
                  :href="project.url_contrato_assinado"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center justify-center gap-2 py-2 px-4 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/30 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 text-xs font-semibold transition-colors w-full"
                >
                  <ExternalLink class="w-3.5 h-3.5" stroke-width="1.5" />
                  Visualizar Contrato Assinado
                </a>
              </div>
            </div>

            <!-- 5. Histórico de Auditoria & Notas -->
            <div class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
              <div class="flex items-center gap-2">
                <History class="w-4 h-4 text-indigo-600" stroke-width="1.5" />
                <span class="text-xs font-bold text-ink uppercase tracking-wider">Histórico Recente (Últimos 5)</span>
              </div>

              <!-- Loading State -->
              <div v-if="isLoadingHistory" class="flex flex-col items-center justify-center py-6 text-ink-muted text-xs gap-2">
                <Loader2 class="w-6 h-6 animate-spin text-brand-primary" stroke-width="1.5" />
                Carregando histórico...
              </div>

              <!-- Empty State -->
              <div v-else-if="historico.length === 0" class="text-center py-4 text-xs text-ink-muted">
                Nenhuma entrada de histórico encontrada.
              </div>

              <!-- Timeline -->
              <div v-else class="relative border-l-2 border-hairline ml-3 space-y-5 py-1">
                <div v-for="item in historico" :key="item.id" class="relative pl-6">
                  <!-- Dot -->
                  <div class="absolute -left-[7px] top-1.5 w-3 h-3 bg-brand-primary rounded-full ring-4 ring-surface"></div>
                  <div class="space-y-0.5">
                    <div class="flex items-center justify-between text-[10px] text-ink-muted">
                      <span class="font-bold text-ink">{{ item.autor }}</span>
                      <span>{{ formatarData(item.data) }}</span>
                    </div>
                    <p class="text-xs text-ink leading-relaxed font-medium bg-canvas/30 p-2 rounded border border-hairline mt-1">
                      {{ item.texto }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- Painel Direito: Visualizador de Documentos -->
        <Transition name="slide-panel">
          <div v-if="documentoAtivo" class="hidden lg:flex flex-col flex-1 border-l border-hairline bg-canvas/50 h-full overflow-hidden">
            <!-- Header do Visualizador -->
            <div class="px-6 py-5 border-b border-hairline bg-surface shrink-0 flex items-center justify-between">
              <div>
                <span class="text-[10px] font-bold text-ink-muted uppercase tracking-wider block">Visualização do Documento</span>
                <h3 class="text-sm font-bold text-ink truncate max-w-[280px] mt-0.5" :title="nomeDocumentoAtivo">
                  {{ nomeDocumentoAtivo }}
                </h3>
              </div>
              <button @click="documentoAtivo = null" title="Fechar Visualizador" class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-hover text-ink-muted hover:text-ink cursor-pointer border-0 bg-transparent transition-colors">
                <X class="w-4 h-4" stroke-width="1.5" />
              </button>
            </div>
            <!-- Corpo do Visualizador -->
            <div class="flex-1 relative overflow-hidden select-none bg-[#0A0A0A]">

              <!-- === Modo Imagem (.jpg / .png / etc.) === -->
              <div
                v-if="isImage"
                class="w-full h-full flex items-center justify-center"
                :class="isDragging ? 'cursor-grabbing' : 'cursor-grab'"
                @wheel.prevent="handleWheelImage"
                @mousedown.prevent="startDrag"
                @mousemove="onDrag"
                @mouseup="endDrag"
                @mouseleave="endDrag"
                @dblclick="resetViewer"
              >
                <img
                  :src="documentoAtivo.url"
                  class="max-w-full max-h-full object-contain will-change-transform pointer-events-none"
                  :style="{
                    transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
                    transformOrigin: 'center center',
                    transition: isDragging ? 'none' : 'transform 0.1s ease-out'
                  }"
                  draggable="false"
                />
              </div>

              <!-- === Modo PDF / iframe === -->
              <div v-else class="w-full h-full">
                <iframe
                  :src="documentoAtivo.url"
                  class="w-full h-full bg-[#0A0A0A]"
                  frameborder="0"
                />
              </div>

              <!-- Toolbar flutuante (apenas para imagens) -->
              <div v-if="isImage" class="absolute bottom-4 right-4 z-20 flex items-center gap-0.5 bg-black/65 backdrop-blur-sm rounded-xl px-2 py-1.5 border border-neutral-700/80">
                <button
                  @click="zoom = Math.max(0.25, parseFloat((zoom - 0.25).toFixed(2)))"
                  class="w-6 h-6 flex items-center justify-center text-neutral-300 hover:text-white rounded hover:bg-white/10 transition-colors cursor-pointer text-base font-light leading-none"
                >−</button>
                <span class="text-neutral-400 text-[10px] font-mono min-w-[2.75rem] text-center">{{ Math.round(zoom * 100) }}%</span>
                <button
                  @click="zoom = Math.min(5, parseFloat((zoom + 0.25).toFixed(2)))"
                  class="w-6 h-6 flex items-center justify-center text-neutral-300 hover:text-white rounded hover:bg-white/10 transition-colors cursor-pointer text-base font-light leading-none"
                >+</button>
                <div class="w-px h-3.5 bg-neutral-700 mx-1" />
                <button
                  @click="resetViewer"
                  title="Resetar visualização"
                  class="w-6 h-6 flex items-center justify-center text-neutral-300 hover:text-white rounded hover:bg-white/10 transition-colors cursor-pointer"
                >
                  <RotateCcw class="w-3 h-3" stroke-width="2" />
                </button>
              </div>

            </div>
          </div>
        </Transition>

      </div>
    </div>
  </Transition>

    <!-- Modais adicionais -->
    <RejeicaoDocumentoModal
      v-if="isRejeicaoModalOpen"
      :is-open="isRejeicaoModalOpen"
      :projeto-id="project.id"
      :documento="selectedDocParaRejeicao"
      :documentos="project.documentos || []"
      @close="isRejeicaoModalOpen = false"
      @rejeitado="onDocRejeitado"
    />

    <SetupOrcamentoModal
      v-if="isSetupOpen"
      :is-open="isSetupOpen"
      :project="project"
      @close="isSetupOpen = false"
      @salvar="onSetupSuccess"
    />
  </Teleport>
</template>

<style scoped>
.slide-panel-enter-active, .slide-panel-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.slide-panel-enter-from, .slide-panel-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
