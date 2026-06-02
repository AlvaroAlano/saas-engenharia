<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useProfile } from '../composables/useProfile'
import SetupOrcamentoModal from './modals/SetupOrcamentoModal.vue'
import EditProjectModal from './EditProjectModal.vue'
import DiarioObraModal from './modals/DiarioObraModal.vue'
import RejeicaoDocumentoModal from './modals/RejeicaoDocumentoModal.vue'
import DrawerDetalheProjeto from './DrawerDetalheProjeto.vue'
import { formatCurrency } from '../utils/formatters'
import BaseButton from './ui/BaseButton.vue'
import { 
  Maximize2, MoreHorizontal, MessageSquare, Camera, Pen, History,
  Loader2, CheckCircle2, Copy, Undo, FileSignature, Archive, FolderOpen,
  User, Home, Users, FileText, Link, AlertTriangle, HelpCircle, Send,
  Eye, X, ExternalLink, Download, Info, Plus, ChevronDown, HardHat, ArrowLeft
} from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const { empresa } = useProfile()
const { showToast } = useToast()
const router = useRouter()

const isDrawerOpen = ref(false)
const isRejeicaoModalOpen = ref(false)
const selectedDocParaRejeicao = ref(null)

const abrirModalRejeicao = (doc) => {
  selectedDocParaRejeicao.value = doc
  isRejeicaoModalOpen.value = true
}

const onDocRejeitado = () => {
  emit('update')
}

const selectedDocParaVisualizar = ref(null)

const verDocumentoNoDrawer = (doc) => {
  if (window.innerWidth < 1024) {
    window.open(doc.url, '_blank')
  } else {
    selectedDocParaVisualizar.value = doc
    isDrawerOpen.value = true
  }
}

watch(isDrawerOpen, (newVal) => {
  if (!newVal) {
    selectedDocParaVisualizar.value = null
  }
})


const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update', 'projeto-arquivado'])

const isMenuOpen = ref(false)
const isCopied = ref(false)

const temDocumentosPendentesRevisao = computed(() => {
  if (props.project.coluna !== 'contrato_pendente') return false
  if (props.project.status === 'docs_validados') return false
  return Array.isArray(props.project.documentos) && props.project.documentos.some(doc =>
    !!doc.url && doc.status !== 'aprovado' && doc.status !== 'rejeitado'
  )
})

// Estado do Modal de Contrato
const isContractModalOpen = ref(false)
const isGeneratingContract = ref(false)
const selectedTemplateId = ref('')
const pdfPreviewUrl = ref(null)
const templates = ref([])
const isLoadingTemplates = ref(false)

const isDocsExpanded = ref(false)

const docCategoriaLabels = {
  identidade:   { label: 'Identidade',   badge: 'RG/CNH',      icon: User },
  residencia:   { label: 'Residência',   badge: 'Comprovante', icon: Home },
  estado_civil: { label: 'Estado Civil', badge: 'Certidão',    icon: Users }
}
const isAdvancing = ref(false)
const isSendingToZapSign = ref(false)
const isApprovingContract = ref(false)
const isSetupModalOpen = ref(false)

const isEditModalOpen = ref(false)
const isDiarioModalOpen = ref(false)

const isBypassing = ref(false)

const toggleDocs = () => {
  isDocsExpanded.value = !isDocsExpanded.value
}

const abrirParaCima = ref(false)

const toggleMenu = (event) => {
  if (!isMenuOpen.value) {
    const triggerEl = event.currentTarget || event.target
    if (triggerEl) {
      const rect = triggerEl.getBoundingClientRect()
      const spaceBelow = window.innerHeight - rect.bottom
      abrirParaCima.value = spaceBelow < 210
    }
  }
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}

// Fechar menu se clicar fora (simplificado)
onMounted(() => {
  document.addEventListener('click', closeMenu)
})
onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
})

const leftBorderClass = computed(() => {
  // Coluna 1: Estimativa Enviada — Aguardando ação do CLIENTE
  if (props.project.coluna === 'estimativa_enviada') {
    return 'border-l-orange-400'
  }

  // Coluna 2: Contrato Pendente
  if (props.project.coluna === 'contrato_pendente') {
    // Docs validados + contrato já gerado — próximo passo: marcar assinado
    if (props.project.contrato_gerado) return 'border-l-emerald-500'
    // Docs validados mas sem contrato — Ação: Gerar Contrato
    if (props.project.status === 'docs_validados') return 'border-l-blue-500'
    // Docs ainda não validados — Ação: Validar Documentos
    return 'border-l-emerald-500'
  }

  // Coluna 3: Engenharia & Caixa — Ação: Orçamento SINAPI
  if (props.project.coluna === 'engenharia_caixa') {
    return 'border-l-indigo-500'
  }

  // Coluna 4: Obra Liberada
  if (props.project.coluna === 'obra_liberada') {
    return 'border-l-violet-500'
  }

  return 'border-l-slate-300'
})

const statusDotClass = computed(() => {
  if (props.project.coluna === 'estimativa_enviada') {
    return 'bg-orange-500'
  }
  if (props.project.coluna === 'contrato_pendente') {
    if (props.project.contrato_gerado) return 'bg-emerald-500'
    if (props.project.status === 'docs_validados') return 'bg-blue-500'
    return 'bg-emerald-500'
  }
  if (props.project.coluna === 'engenharia_caixa') {
    return 'bg-indigo-500'
  }
  if (props.project.coluna === 'obra_liberada') {
    return 'bg-violet-500'
  }
  return 'bg-neutral-500'
})

const totalSinapi = computed(() => {
  return parseFloat(props.project.valor) || 0
})

const ctaInfo = computed(() => {
  if (props.project.status === 'docs_pendentes') {
    return { text: 'Aguardando Reenvio', variant: 'secondary', class: 'bg-canvas text-ink-muted opacity-75' }
  }
  if (props.project.coluna === 'estimativa_enviada' && props.project.status === 'aguardando_cliente') {
    return {
      text: isCopied.value ? 'Copiado!' : 'Copiar Link',
      icon: isCopied.value ? CheckCircle2 : Link,
      variant: 'secondary',
      class: isCopied.value 
        ? 'bg-emerald-955/25 text-emerald-500 border border-emerald-800/80 hover:bg-emerald-955/25 hover:text-emerald-500' 
        : 'bg-canvas text-ink',
      action: 'copy_link'
    }
  }
  if (props.project.coluna === 'estimativa_enviada') {
    return { text: 'Cobrar Cliente', variant: 'secondary', class: 'bg-canvas text-ink', action: 'send_whatsapp_reminder' }
  }
  if (props.project.status === 'docs_incompletos') {
    return { text: 'Lembrar Cliente', variant: 'secondary', class: 'bg-canvas text-amber-550', action: 'send_whatsapp_reminder' }
  }

  // --- Fase: Contrato Pendente (Geração de Proposta Comercial) ---
  if (props.project.coluna === 'contrato_pendente' && props.project.status === 'docs_validados') {
    // Estado A: Não Gerado
    if (!props.project.contrato_gerado) {
      return { 
        text: 'Gerar Proposta Comercial', 
        icon: FileText, 
        variant: 'primary', 
        class: 'font-semibold', 
        action: 'generate_contract' 
      }
    }
    // Estado B: Gerado/Aprovado mas não enviado
    if (!props.project.status_assinatura || props.project.status_assinatura === 'nao_enviado') {
      return { 
        text: '✒️ Enviar ZapSign', 
        variant: 'secondary', 
        class: 'bg-canvas text-blue-500 hover:text-blue-600', 
        action: 'send_to_zapsign' 
      }
    }
    // Estado Final: Ambos assinaram
    if (props.project.status_assinatura === 'assinado') {
      return { 
        text: 'Finalizar', 
        icon: CheckCircle2, 
        variant: 'primary', 
        class: 'font-semibold', 
        action: 'advance_phase' 
      }
    }
  }

  // --- Fase: Engenharia & Caixa (Geração de Contrato de Construção) ---
  if (props.project.coluna === 'engenharia_caixa') {
    // Se a planilha não possui itens
    if (totalSinapi.value <= 0) {
      return {
        text: 'Gerar Contrato de Construção',
        icon: FileText,
        variant: 'primary',
        class: 'font-semibold opacity-50 cursor-not-allowed',
        disabled: true,
        tooltip: 'Adicione itens ao orçamento antes de gerar o contrato',
        action: 'generate_contract'
      }
    }

    // Planilha tem itens:
    // Estado A: Não Gerado (status_assinatura voltou para nao_enviado na transição de fase ou reset do contrato)
    if (!props.project.contrato_gerado) {
      return {
        text: 'Gerar Contrato de Construção',
        icon: FileText,
        variant: 'primary',
        class: 'font-semibold',
        action: 'generate_contract'
      }
    }
    // Estado B: Gerado/Aprovado mas não enviado
    if (props.project.status_assinatura === 'nao_enviado') {
      return {
        text: '✒️ Enviar ZapSign',
        variant: 'secondary',
        class: 'bg-canvas text-blue-500 hover:text-blue-600',
        action: 'send_to_zapsign'
      }
    }
    // Estado Final: Ambos assinaram o Contrato de Construção
    if (props.project.status_assinatura === 'assinado') {
      return {
        text: 'Liberar Obra',
        icon: CheckCircle2,
        variant: 'primary',
        class: 'font-semibold',
        action: 'liberar_obra'
      }
    }
  }

  return null
})

const handleCtaClick = () => {
  if (ctaInfo.value && ctaInfo.value.action === 'copy_link') {
    const url = `${window.location.origin}/estimativa/${props.project.id}`
    navigator.clipboard.writeText(url)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } else if (ctaInfo.value && ctaInfo.value.action === 'generate_contract') {
    openContractModal()
  } else if (ctaInfo.value && ctaInfo.value.action === 'send_to_zapsign') {
    enviarParaZapSign()
  } else if (ctaInfo.value && ctaInfo.value.action === 'advance_phase') {
    avancarParaEngenharia()
  } else if (ctaInfo.value && ctaInfo.value.action === 'liberar_obra') {
    liberarObra()
  } else if (ctaInfo.value && ctaInfo.value.action === 'send_portal_access') {
    sendPortalAccess()
  } else if (ctaInfo.value && ctaInfo.value.action === 'send_whatsapp_reminder') {
    sendWhatsAppReminder()
  }
}

const isSendingPortalAccess = ref(false)
const isCopyingPortalLink = ref(false)
const hasCopiedPortalLink = ref(false)

const sendPortalAccess = async () => {
  if (isSendingPortalAccess.value) return
  isSendingPortalAccess.value = true
  try {
    const res = await axios.get(`/portal/projetos/${props.project.id}/link`)
    if (res.data && res.data.url_publica) {
      // Extrai o token e reconstrói a URL baseada no ambiente atual (localhost ou produção)
      const urlParts = res.data.url_publica.split('/')
      const token = urlParts[urlParts.length - 1]
      const dynamicUrl = `${window.location.origin}/portal/${token}`
      const pin = res.data.pin_acesso
      const msg = `Olá ${props.project.cliente_nome}! Segue o link para acompanhar a evolução da sua obra em tempo real:\n${dynamicUrl}\n\nPIN de acesso: ${pin}`
      
      const telefoneLimpo = props.project.telefone ? props.project.telefone.replace(/\D/g, '') : ''
      window.open(`https://wa.me/${telefoneLimpo}?text=${encodeURIComponent(msg)}`, '_blank')
    } else {
      showToast('Não foi possível obter ou criar o link do portal.', 'error')
    }
  } catch (error) {
    console.error('Erro ao buscar link do portal:', error)
    showToast(error.response?.data?.detail || 'Erro ao gerar/recuperar o acesso ao portal do cliente.', 'error')
  } finally {
    isSendingPortalAccess.value = false
  }
}

const copyPortalAccessLink = async () => {
  if (isCopyingPortalLink.value || hasCopiedPortalLink.value) return
  isCopyingPortalLink.value = true
  try {
    const res = await axios.get(`/portal/projetos/${props.project.id}/link`)
    if (res.data && res.data.url_publica) {
      const urlParts = res.data.url_publica.split('/')
      const token = urlParts[urlParts.length - 1]
      const dynamicUrl = `${window.location.origin}/portal/${token}`

      await navigator.clipboard.writeText(dynamicUrl)
      
      hasCopiedPortalLink.value = true
      setTimeout(() => {
        hasCopiedPortalLink.value = false
        closeMenu()
      }, 1500)
    } else {
      showToast('Não foi possível obter ou criar o link do portal.', 'error')
    }
  } catch (error) {
    console.error('Erro ao copiar link do portal:', error)
    showToast(error.response?.data?.detail || 'Erro ao gerar/recuperar o acesso ao portal do cliente.', 'error')
  } finally {
    isCopyingPortalLink.value = false
  }
}

const handleAbrirSinapi = () => {
  // Se já tiver os dados preenchidos, vai direto
  if (props.project.uf_obra && props.project.sinapi_mes_ano) {
    router.push(`/orcamento/${props.project.id}`)
  } else {
    isSetupModalOpen.value = true
  }
}

const onSetupSuccess = (projectId) => {
  isSetupModalOpen.value = false
  if (props.project.coluna === 'engenharia_caixa' || props.project.coluna === 'obra_liberada') {
    router.push(`/orcamento/${projectId}`)
  } else {
    emit('update')
  }
}

const openContractModal = async () => {
  isContractModalOpen.value = true
  selectedTemplateId.value = ''
  pdfPreviewUrl.value = null
  isGeneratingContract.value = false
  
  isLoadingTemplates.value = true
  try {
    const { data } = await axios.get('/contratos-templates')
    const tipoDesejado = props.project.coluna === 'engenharia_caixa' ? 'contrato' : 'proposta'
    templates.value = data.filter(t => {
      if (tipoDesejado === 'contrato') {
        return t.tipo === 'contrato'
      } else {
        return !t.tipo || t.tipo === 'proposta'
      }
    })
    if (templates.value.length > 0) {
      selectedTemplateId.value = templates.value[0].id
    }
  } catch (error) {
    console.error('Erro ao buscar templates:', error)
    showToast('Não foi possível carregar os templates.', 'error')
  } finally {
    isLoadingTemplates.value = false
  }
}

const closeContractModal = () => {
  isContractModalOpen.value = false
  if (pdfPreviewUrl.value) {
    URL.revokeObjectURL(pdfPreviewUrl.value)
    pdfPreviewUrl.value = null
  }
}

const generateContractPreview = async () => {
  isGeneratingContract.value = true
  try {
    const response = await axios.get(`/projetos/${props.project.id}/contrato`, {
      params: { template_id: selectedTemplateId.value },
      responseType: 'blob'
    })
    
    // Create a temporary URL for the preview
    pdfPreviewUrl.value = URL.createObjectURL(response.data)
  } catch (error) {
    console.error('Erro ao gerar contrato:', error)
    if (error.response?.data instanceof Blob) {
      const reader = new FileReader()
      reader.onload = () => {
        try {
          const errObj = JSON.parse(reader.result)
          showToast(errObj.detail || 'Erro ao gerar o documento. Tente novamente.', 'error')
        } catch (e) {
          showToast('Erro ao gerar o documento. Tente novamente.', 'error')
        }
      }
      reader.readAsText(error.response.data)
    } else {
      showToast(error.response?.data?.detail || 'Erro ao gerar o documento. Tente novamente.', 'error')
    }
  } finally {
    isGeneratingContract.value = false
  }
}

const approveContract = async () => {
  isApprovingContract.value = true
  try {
    await axios.patch(`/projetos/${props.project.id}`, {
      contrato_gerado: true,
      status_assinatura: 'nao_enviado'
    })
    // Atualização local para reatividade instantânea
    props.project.contrato_gerado = true
    props.project.status_assinatura = 'nao_enviado'
    closeContractModal()
    emit('update')
  } catch (error) {
    console.error('Erro ao aprovar contrato:', error)
    showToast('Erro ao aprovar o contrato. Tente novamente.', 'error')
  } finally {
    isApprovingContract.value = false
  }
}

const downloadContract = () => {
  if (!pdfPreviewUrl.value) return
  
  const link = document.createElement('a')
  link.href = pdfPreviewUrl.value
  const projectName = props.project.cliente_nome ? props.project.cliente_nome.replace(/\s+/g, '_') : 'Projeto'
  link.setAttribute('download', `Contrato_${projectName}.pdf`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const openInNewTab = () => {
  if (pdfPreviewUrl.value) {
    window.open(pdfPreviewUrl.value, '_blank')
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
    
    // Atualiza localmente para refletir sem precisar de reload completo
    props.project.status = 'docs_validados'
    props.project.documentos = docsAtualizados
    
    emit('update')
  } catch (error) {
    console.error('Erro ao validar documentos:', error)
    showToast('Erro ao validar documentos. Tente novamente.', 'error')
  }
}

const confirmModal = ref({
  isOpen: false,
  title: '',
  message: '',
  confirmText: 'Confirmar',
  loadingText: 'Processando...',
  successText: 'Concluído!',
  isDanger: false,
  onConfirm: null
})

const statusBotao = ref('idle') // 'idle' | 'loading' | 'success'

const openConfirmModal = (title, message, onConfirm, isDanger = false, confirmText = 'Confirmar', loadingText = 'Processando...', successText = 'Concluído!') => {
  confirmModal.value = {
    isOpen: true,
    title,
    message,
    confirmText,
    loadingText,
    successText,
    isDanger,
    onConfirm
  }
  statusBotao.value = 'idle'
}

const closeConfirmModal = () => {
  confirmModal.value.isOpen = false
}

const executeConfirm = async () => {
  if (confirmModal.value.onConfirm) {
    const shouldClose = await confirmModal.value.onConfirm()
    // Só fecha automaticamente se a função não retornar expressamente 'false'
    if (shouldClose !== false) {
      closeConfirmModal()
    }
  } else {
    closeConfirmModal()
  }
}

const avancarParaEngenharia = async () => {
  openConfirmModal(
    'Avançar para Engenharia',
    'Confirmar que o contrato foi assinado e mover o projeto para a fase de Engenharia? Esta ação registrará o evento no histórico e reiniciará a esteira de assinatura para o Contrato de Construção.',
    async () => {
      isAdvancing.value = true
      try {
        await axios.patch(`/projetos/${props.project.id}`, {
          coluna: 'engenharia_caixa',
          status: 'em_analise_caixa',
          contrato_gerado: false,
          status_assinatura: 'nao_enviado',
          cliente_assinou: false,
          engenheiro_assinou: false,
          zapsign_document_token: null,
          url_assinatura_cliente: null,
          url_assinatura_engenheiro: null
        })
        
        // Atualização local reativa
        props.project.coluna = 'engenharia_caixa'
        props.project.status = 'em_analise_caixa'
        props.project.contrato_gerado = false
        props.project.status_assinatura = 'nao_enviado'
        props.project.cliente_assinou = false
        props.project.engenheiro_assinou = false
        props.project.zapsign_document_token = null
        props.project.url_assinatura_cliente = null
        props.project.url_assinatura_engenheiro = null
        
        emit('update')
      } catch (error) {
        console.error('Erro ao avançar fase:', error)
        showToast('Erro ao atualizar status do projeto.', 'error')
      } finally {
        isAdvancing.value = false
      }
    }
  )
}

const isLiberandoObra = ref(false)

const liberarObra = async () => {
  openConfirmModal(
    'Aprovar e Liberar Obra',
    'Tem certeza que deseja liberar esta obra? O status do projeto será atualizado para Liberado.',
    async () => {
      isLiberandoObra.value = true
      try {
        await axios.patch(`/projetos/${props.project.id}`, {
          coluna: 'obra_liberada',
          status: 'liberada'
        })
        props.project.coluna = 'obra_liberada'
        props.project.status = 'liberada'
        emit('update')
        showToast('Obra liberada com sucesso!', 'success')
      } catch (error) {
        console.error('Erro ao liberar obra:', error)
        showToast('Erro ao liberar a obra. Tente novamente.', 'error')
      } finally {
        isLiberandoObra.value = false
      }
    }
  )
}

const voltarEtapa = async () => {
  let novaColuna = ''
  let novoStatus = ''
  
  if (props.project.coluna === 'contrato_pendente') {
    novaColuna = 'estimativa_enviada'
    novoStatus = 'aguardando_cliente'
  } else if (props.project.coluna === 'engenharia_caixa') {
    novaColuna = 'contrato_pendente'
    novoStatus = 'docs_validados'
  } else if (props.project.coluna === 'obra_liberada') {
    novaColuna = 'engenharia_caixa'
    novoStatus = 'em_analise_caixa'
  }
  
  if (!novaColuna) return

  openConfirmModal(
    'Desfazer Avanço',
    `Deseja realmente retroceder o projeto para a coluna "${novaColuna.replace('_', ' ').toUpperCase()}"? O histórico registrará esta mudança.`,
    async () => {
      try {
        await axios.patch(`/projetos/${props.project.id}`, {
          coluna: novaColuna,
          status: novoStatus
        })
        emit('update')
      } catch (error) {
        console.error('Erro ao voltar etapa:', error)
        showToast('Erro ao retroceder status.', 'error')
      }
    },
    true,
    'Sim, Voltar Etapa'
  )
}

const formatDate = (dateString) => {
  if (!dateString) return 'Recém adicionado'
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR')
}

const sendWhatsAppReminder = () => {
  const nomeCliente = props.project.cliente_nome || 'Cliente'
  const nomeEmpresa = empresa.value?.nome_fantasia || 'Nossa Construtora'
  const telefone = props.project.telefone?.replace(/\D/g, '') || ''

  // Se engenheiro já assinou e existe URL de assinatura do cliente, enviar link da ZapSign
  if (props.project.engenheiro_assinou && props.project.url_assinatura_cliente) {
    const message = encodeURIComponent(
      `Olá ${nomeCliente}, aqui é da ${nomeEmpresa}. ` +
      `Seu contrato está pronto para assinatura digital! Acesse o link abaixo para assinar: ${props.project.url_assinatura_cliente}`
    )
    window.open(`https://wa.me/${telefone ? '55' + telefone : ''}?text=${message}`, '_blank')
  } else {
    const linkProjeto = `${window.location.origin}/estimativa/${props.project.id}`
    const message = encodeURIComponent(
      `Olá ${nomeCliente}, aqui é da ${nomeEmpresa}. Vi que você realizou uma simulação de obra. ` +
      `Para prosseguirmos com seu projeto, acesse este link e anexe seus documentos: ${linkProjeto}`
    )
    window.open(`https://wa.me/${telefone ? '55' + telefone : ''}?text=${message}`, '_blank')
  }
}

const openWhatsAppDirect = () => {
  const telefone = props.project.telefone?.replace(/\D/g, '') || ''
  window.open(`https://wa.me/${telefone ? '55' + telefone : ''}`, '_blank')
}

const enviarParaZapSign = async () => {
  // Precisa de um template selecionado — abre modal de contrato para selecionar
  if (!selectedTemplateId.value) {
    openContractModal()
    return
  }

  openConfirmModal(
    'Enviar para Assinatura Digital',
    `O contrato será enviado para a ZapSign e os links de assinatura serão gerados para você e para o cliente. Deseja continuar?`,
    async () => {
      isSendingToZapSign.value = true
      try {
        const { data } = await axios.post(`/projetos/${props.project.id}/enviar-zapsign`, {
          template_id: selectedTemplateId.value
        })
        if (data.success) {
          emit('update')
        }
      } catch (error) {
        console.error('Erro ao enviar para ZapSign:', error)
        showToast('Erro ao enviar contrato para assinatura digital.', 'error')
      } finally {
        isSendingToZapSign.value = false
      }
    }
  )
}

const assinarComoEngenheiro = () => {
  if (props.project.url_assinatura_engenheiro) {
    window.open(props.project.url_assinatura_engenheiro, '_blank')
  }
}

const enviarLinkAssinaturaWhatsApp = () => {
  if (!props.project.engenheiro_assinou) return
  sendWhatsAppReminder()
}

const marcarComoAssinado = async (projetoId) => {
  isBypassing.value = true
  try {
    await axios.patch(`/projetos/${projetoId}`, {
      coluna: 'engenharia_caixa',
      status: 'em_analise_caixa',
      status_assinatura: 'assinado',
      cliente_assinou: true,
      engenheiro_assinou: true
    })
    
    // Atualização local imediata para fazer o card mudar de coluna de forma reativa
    props.project.coluna = 'engenharia_caixa'
    props.project.status = 'em_analise_caixa'
    props.project.status_assinatura = 'assinado'
    props.project.cliente_assinou = true
    props.project.engenheiro_assinou = true
    
    emit('update') // Alerta o pai (Kanban) para refazer o fetch no background, mantendo sincronizado
  } catch (error) {
    console.error('Erro ao forçar assinatura (bypass):', error)
  } finally {
    isBypassing.value = false
  }
}

const openEditModal = () => {
  isEditModalOpen.value = true
  closeMenu()
}

const handleSaveProjectEdit = async (editedData) => {
  try {
    await axios.patch(`/projetos/${props.project.id}`, editedData)
    
    // Atualiza localmente para refletir na interface
    props.project.cliente_nome = editedData.cliente_nome
    props.project.titulo_projeto = editedData.titulo_projeto
    props.project.telefone = editedData.telefone
    
    isEditModalOpen.value = false
  } catch (error) {
    console.error('Erro ao editar projeto:', error)
    showToast('Erro ao salvar as alterações. Tente novamente.', 'error')
  }
}

const arquivarProjeto = () => {
  openConfirmModal(
    'Arquivar Projeto',
    'Tem certeza que deseja arquivar este projeto?',
    async () => {
      statusBotao.value = 'loading'
      try {
        await axios.patch(`/projetos/${props.project.id}`, { status: 'ARQUIVADO' })
        
        statusBotao.value = 'success'
        
        setTimeout(() => {
          closeConfirmModal()
          statusBotao.value = 'idle'
          emit('projeto-arquivado', props.project.id)
          closeMenu()
        }, 1000) // Feedback visual visível por 1 segundo
        
        return false // Impede o `executeConfirm` de fechar o modal na mesma hora
      } catch (error) {
        console.error('Erro ao arquivar projeto:', error)
        showToast('Falha ao arquivar o projeto. Tente novamente.', 'error')
        statusBotao.value = 'idle'
        return true // Permite fechar o modal em caso de erro
      }
    },
    true, // Define isDanger = true para deixar o botão vermelho
    'Sim, Arquivar',
    'Arquivando...',
    'Arquivado!'
  )
}

// --- Histórico e Notas ---
const isModalHistoricoAberto = ref(false)
const projetoAtualHistorico = ref(null)
const novaNota = ref('')
const notasHistorico = ref([])

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

const fetchHistorico = async () => {
  if (!props.project?.id) return
  try {
    const res = await axios.get(`/projetos/${props.project.id}/historico`)
    if (res.data && res.data.success) {
      notasHistorico.value = res.data.data
    }
  } catch (error) {
    console.error('Erro ao buscar histórico do projeto:', error)
  }
}

const abrirModalHistorico = (projeto) => {
  projetoAtualHistorico.value = projeto
  isModalHistoricoAberto.value = true
  fetchHistorico()
  closeMenu()
}

const salvarNovaNota = async () => {
  if (!novaNota.value.trim() || !props.project?.id) return
  try {
    const res = await axios.post(`/projetos/${props.project.id}/historico`, {
      texto: novaNota.value
    })
    if (res.data && res.data.success) {
      notasHistorico.value.unshift(res.data.data)
      novaNota.value = ''
    }
  } catch (error) {
    console.error('Erro ao salvar nota de histórico:', error)
    showToast('Erro ao salvar a nota. Tente novamente.', 'error')
  }
}
</script>

<template>
  <div class="bg-surface border border-hairline rounded-md p-4 transition-all hover:border-neutral-500/50 shadow-sm relative text-ink">
    <div class="flex justify-between items-start mb-3">
      <div class="pr-6">
        <div class="flex items-center gap-1.5">
          <div class="w-2 h-2 rounded-full shrink-0" :class="statusDotClass"></div>
          <p class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">{{ project.cliente_nome }}</p>
          <span 
            v-if="temDocumentosPendentesRevisao" 
            class="w-2 h-2 rounded-full bg-blue-500 animate-pulse shrink-0 cursor-help"
            title="Documento pendente de visualização"
          ></span>
        </div>
        <h4 class="text-sm font-medium text-ink mt-0.5 leading-snug">{{ project.titulo_projeto || '-' }}</h4>
      </div>
      
      <!-- Dropdown Menu -->
      <div class="absolute top-3 right-3 flex items-center gap-1" @click.stop>
        <BaseButton variant="ghost" size="icon" @click.stop="isDrawerOpen = true" title="Ver Detalhes">
          <Maximize2 class="w-[18px] h-[18px]" stroke-width="1.5" />
        </BaseButton>
        <BaseButton variant="ghost" size="icon" @click.stop="toggleMenu($event)">
          <MoreHorizontal class="w-[18px] h-[18px]" stroke-width="1.5" />
        </BaseButton>
        
        <Transition
          enter-active-class="transition-all duration-200 ease-out transform"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition-all duration-150 ease-in transform"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div 
            v-if="isMenuOpen" 
            :class="[
              'absolute right-0 w-44 bg-surface border border-hairline rounded-md shadow-xl z-10 py-1',
              abrirParaCima ? 'bottom-full mb-1 origin-bottom-right' : 'top-full mt-1 origin-top-right'
            ]" 
            @click.stop
          >
            <button @click.stop="openWhatsAppDirect" class="w-full text-left px-4 py-2.5 text-xs text-emerald-500 font-medium hover:bg-canvas flex items-center gap-2 cursor-pointer">
              <MessageSquare class="w-[14px] h-[14px]" stroke-width="1.5" /> Chamar no Whats
            </button>
            <button
              v-if="project.coluna === 'obra_liberada'"
              @click.stop="isDiarioModalOpen = true; closeMenu()"
              class="w-full text-left px-4 py-2.5 text-xs text-indigo-550 font-medium hover:bg-canvas flex items-center gap-2 cursor-pointer"
            >
              <Camera class="w-[14px] h-[14px]" stroke-width="1.5" /> Diário de Obra
            </button>
            <div class="border-t border-hairline my-1"></div>
            <button @click.stop="openEditModal" class="w-full text-left px-4 py-2.5 text-xs text-ink-muted hover:bg-canvas flex items-center gap-2 cursor-pointer">
              <Pen class="w-[14px] h-[14px]" stroke-width="1.5" /> Editar
            </button>
            <button @click.stop="abrirModalHistorico(project)" class="w-full text-left px-4 py-2.5 text-xs text-ink-muted hover:bg-canvas flex items-center gap-2 cursor-pointer">
              <History class="w-[14px] h-[14px]" stroke-width="1.5" /> Histórico e Notas
            </button>
            <div class="border-t border-hairline my-1"></div>
            <button
              v-if="project.coluna === 'obra_liberada'"
              @click.stop="copyPortalAccessLink"
              class="w-full text-left px-4 py-2.5 text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
              :class="hasCopiedPortalLink ? 'text-emerald-500 bg-canvas hover:bg-canvas' : 'text-indigo-500 hover:bg-canvas'"
            >
              <Loader2 v-if="isCopyingPortalLink" class="w-[14px] h-[14px] animate-spin" stroke-width="1.5" />
              <CheckCircle2 v-else-if="hasCopiedPortalLink" class="w-[14px] h-[14px]" stroke-width="1.5" />
              <Copy v-else class="w-[14px] h-[14px]" stroke-width="1.5" />
              {{ hasCopiedPortalLink ? 'Copiado!' : 'Copiar Link do Portal' }}
            </button>
            <div v-if="project.coluna === 'engenharia_caixa' || project.coluna === 'obra_liberada'" class="border-t border-hairline my-1"></div>
            <button 
              v-if="project.coluna !== 'estimativa_enviada'"
              @click.stop="voltarEtapa" 
              class="w-full text-left px-4 py-2.5 text-xs text-ink-muted hover:bg-canvas flex items-center gap-2 cursor-pointer"
            >
              <Undo class="w-[14px] h-[14px]" stroke-width="1.5" /> Voltar Etapa
            </button>
            <button 
              v-if="(project.coluna === 'contrato_pendente' || project.coluna === 'engenharia_caixa') && project.contrato_gerado"
              @click.stop="openContractModal" 
              class="w-full text-left px-4 py-2.5 text-xs text-blue-500 font-medium hover:bg-canvas flex items-center gap-2 cursor-pointer"
            >
              <FileSignature class="w-[14px] h-[14px]" stroke-width="1.5" /> Atualizar/Refazer Contrato
            </button>
            <div v-if="(project.coluna === 'contrato_pendente' || project.coluna === 'engenharia_caixa') && project.contrato_gerado" class="border-t border-hairline my-1"></div>
            <button @click.stop="arquivarProjeto" class="w-full text-left px-4 py-2.5 text-xs text-red-500 hover:bg-red-950/10 hover:text-red-400 flex items-center gap-2 cursor-pointer">
              <Archive class="w-[14px] h-[14px]" stroke-width="1.5" /> Arquivar
            </button>
          </div>
        </Transition>
      </div>
    </div>
    
    <!-- Parametric Data (Size, Pattern) inline near value -->
    <div class="flex items-end justify-between mb-3 gap-2">
      <div>
        <p class="text-sm font-bold" :class="project.valor ? 'text-ink' : 'text-ink-muted italic text-xs'">
          {{ formatCurrency(project.valor, 'Aguardando preenchimento') }}
        </p>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <span v-if="project.padrao" class="text-[10px] bg-canvas text-ink-muted px-1.5 py-0.5 rounded-md border border-hairline font-medium">{{ project.padrao }}</span>
        <span v-else class="text-[10px] text-ink-muted px-1 py-0.5">-</span>
        <span v-if="project.tamanho" class="text-[10px] text-ink-muted font-mono bg-canvas border border-hairline px-1.5 py-0.5 rounded-md">{{ project.tamanho }} m²</span>
      </div>
    </div>

    <!-- Checklist para contrato_pendente -->
    <div v-if="project.coluna === 'contrato_pendente' && project.documentos && project.documentos.length > 0" class="mb-4 bg-canvas rounded-md border border-hairline">
      <!-- Toggle Header -->
      <BaseButton 
        variant="ghost"
        size="md"
        @click="toggleDocs"
        class="w-full justify-between px-3 py-2.5 group"
      >
        <div class="flex items-center gap-2">
          <FolderOpen class="w-[18px] h-[18px] text-ink-muted group-hover:text-ink transition-colors" stroke-width="1.5" />
          <span class="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">{{ project.documentos.length }} Documentos Anexados</span>
          <span 
            v-if="temDocumentosPendentesRevisao" 
            class="w-2 h-2 rounded-full bg-blue-500 animate-pulse shrink-0"
            title="Documento pendente de visualização"
          ></span>
        </div>
        <ChevronDown 
          class="w-5 h-5 text-ink-muted transition-transform duration-300"
          :class="{ 'rotate-180': isDocsExpanded }"
          stroke-width="1.5"
        />
      </BaseButton>

      <!-- Expandable List -->
      <transition
        enter-active-class="transition-all duration-300 ease-out"
        leave-active-class="transition-all duration-300 ease-in"
        enter-from-class="max-h-0 opacity-0"
        enter-to-class="max-h-[500px] opacity-100"
        leave-from-class="max-h-[500px] opacity-100"
        leave-to-class="max-h-0 opacity-0"
        @after-enter="(el) => el.style.overflow = 'visible'"
        @before-leave="(el) => el.style.overflow = 'hidden'"
      >
        <div v-show="isDocsExpanded" class="px-3 pb-3 overflow-hidden">
          <ul class="space-y-2 mb-3 mt-1">
            <li v-for="(doc, index) in project.documentos" :key="index" class="flex items-center justify-between text-xs bg-surface p-2 rounded-md border border-hairline transition-all hover:border-neutral-500/30">
              <div class="flex items-center gap-2 overflow-hidden">
                <component 
                  :is="docCategoriaLabels[doc.categoria]?.icon || FileText" 
                  class="w-4 h-4 text-blue-500 shrink-0" 
                  stroke-width="1.5" 
                />
                <div class="flex flex-col overflow-hidden">
                  <span class="text-ink font-medium truncate">
                    {{ docCategoriaLabels[doc.categoria]?.label || doc.name }}
                  </span>
                  <span v-if="doc.categoria" class="text-[9px] text-ink-muted truncate">{{ doc.name }}</span>
                </div>
              </div>
              <div class="flex items-center gap-1.5 shrink-0">
                <span v-if="doc.categoria" class="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-canvas text-blue-500 border border-hairline">
                  {{ docCategoriaLabels[doc.categoria]?.badge }}
                </span>
                <span v-if="doc.url && (project.status === 'docs_validados' || doc.status === 'aprovado')" class="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-canvas text-emerald-500 border border-hairline">
                  Aprovado
                </span>
                <span v-else-if="doc.url" class="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-canvas text-amber-500 border border-hairline">
                  Em Análise
                </span>
                <span v-if="!doc.url && doc.status === 'rejeitado'" class="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-canvas text-red-500 border border-hairline" :title="doc.motivo">
                  Recusado
                </span>
                <button v-if="doc.url" @click.prevent="verDocumentoNoDrawer(doc)" class="text-ink-muted hover:bg-surface-hover hover:text-ink transition-colors flex items-center gap-1 border border-hairline bg-canvas px-2 py-1 rounded cursor-pointer border-0 bg-transparent">
                  <Eye class="w-[14px] h-[14px] text-ink-muted" stroke-width="1.5" />
                  <span class="hidden sm:inline font-medium">Ver</span>
                </button>
                <div v-if="project.coluna === 'contrato_pendente' && project.status !== 'docs_validados' && doc.status !== 'aprovado' && doc.url" class="relative group shrink-0">
                  <BaseButton 
                    @click.stop="abrirModalRejeicao(doc)" 
                    variant="ghost" 
                    size="icon" 
                    class="w-7 h-7 !p-0 text-ink-muted hover:text-red-500 hover:bg-red-500/10 rounded-md transition-colors"
                  >
                    <X class="w-4 h-4" stroke-width="1.5" />
                  </BaseButton>
                  <!-- Tooltip -->
                  <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-surface border border-hairline text-ink text-[10px] px-2 py-1 rounded shadow-md z-[100] whitespace-nowrap pointer-events-none">
                    Recusar Documento
                  </div>
                </div>
              </div>
            </li>
          </ul>

          <BaseButton
            v-if="temDocumentosPendentesRevisao"
            @click.stop="validarDocumentos"
            variant="secondary"
            size="sm"
            class="w-full py-2 text-emerald-500 hover:text-emerald-600 gap-1.5 font-semibold text-xs bg-canvas"
          >
            <CheckCircle2 class="w-4 h-4 text-emerald-500" stroke-width="1.5" /> Validar Documentos
          </BaseButton>
          <div v-else-if="project.status === 'docs_validados'" class="w-full py-2 bg-canvas text-emerald-500 font-semibold text-xs rounded-md flex items-center justify-center gap-1.5 border border-hairline">
            <CheckCircle2 class="w-4 h-4 text-emerald-500" stroke-width="1.5" /> Documentos Validados
          </div>
        </div>
      </transition>
    </div>

    <!-- Compact Signature Status -->
    <div v-if="project.status_assinatura === 'pendente' && project.coluna === 'contrato_pendente'" class="mb-3 px-3 py-2 bg-canvas rounded-md border border-hairline flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-1" :title="project.engenheiro_assinou ? 'Engenheiro assinou' : 'Aguardando engenheiro'">
          <User class="w-3.5 h-3.5" :class="project.engenheiro_assinou ? 'text-emerald-500' : 'text-ink-muted'" stroke-width="1.5" />
          <span class="text-[9px] font-bold" :class="project.engenheiro_assinou ? 'text-emerald-600' : 'text-ink-muted'">ENG</span>
        </div>
        <div class="w-px h-3 bg-hairline"></div>
        <div class="flex items-center gap-1" :title="project.cliente_assinou ? 'Cliente assinou' : 'Aguardando cliente'">
          <User class="w-3.5 h-3.5" :class="project.cliente_assinou ? 'text-emerald-500' : 'text-ink-muted'" stroke-width="1.5" />
          <span class="text-[9px] font-bold" :class="project.cliente_assinou ? 'text-emerald-600' : 'text-ink-muted'">CLI</span>
        </div>
      </div>
      
      <div class="flex gap-1.5">
        <BaseButton v-if="!project.engenheiro_assinou" @click.stop="assinarComoEngenheiro" variant="secondary" size="sm" class="text-[9px] px-2 py-1 h-auto font-semibold bg-canvas">Assinar</BaseButton>
        <BaseButton v-if="project.engenheiro_assinou && !project.cliente_assinou" @click.stop="enviarLinkAssinaturaWhatsApp" variant="secondary" size="sm" class="text-[9px] px-2 py-1 h-auto text-emerald-500 hover:text-emerald-600 font-semibold bg-canvas">Cobrar</BaseButton>
      </div>
    </div>

    <div class="flex items-center justify-between mt-4 pt-3 border-t border-hairline">
      <span class="text-[10px] text-ink-muted flex items-center gap-1 font-medium">
        <History class="w-3.5 h-3.5 text-ink-muted" stroke-width="1.5" />
        {{ formatDate(project.created_at) }}
      </span>
      
      <div class="flex items-center gap-2">
        <!-- Bypass Checkbox -->
        <label 
          v-if="project.coluna === 'contrato_pendente'"
          class="flex items-center gap-1.5 cursor-pointer opacity-70 hover:opacity-100 transition-opacity mr-1"
        >
          <input 
            type="checkbox" 
            :disabled="isBypassing"
            @change="marcarComoAssinado(project.id)"
            class="w-3.5 h-3.5 rounded-sm border-hairline bg-canvas text-ink focus:ring-0 cursor-pointer disabled:opacity-50 transition-all"
          >
          <span class="text-[10px] font-medium text-ink-muted select-none whitespace-nowrap">
            {{ isBypassing ? 'Movendo...' : 'Cliente assinou' }}
          </span>
        </label>

        <BaseButton 
          v-if="project.coluna === 'estimativa_enviada'"
          variant="secondary"
          size="icon"
          @click.stop="sendWhatsAppReminder"
          title="Lembrar via WhatsApp"
          class="text-emerald-500 hover:text-emerald-600 bg-canvas"
        >
          <MessageSquare class="w-[18px] h-[18px]" stroke-width="1.5" />
        </BaseButton>

      <!-- Botão SINAPI: visível em engenharia_caixa e obra_liberada -->
      <BaseButton
        v-if="project.coluna === 'engenharia_caixa' || project.coluna === 'obra_liberada'"
        variant="secondary"
        size="sm"
        @click.stop="handleAbrirSinapi"
        class="text-xs h-8 px-2.5 shrink-0 gap-1.5 font-medium bg-canvas"
      >
        <HardHat class="w-4 h-4" stroke-width="1.5" />
        SINAPI
      </BaseButton>

      <!-- Botão Gerar Contrato (Icon Button) ao lado do SINAPI -->
      <div 
        v-if="project.coluna === 'engenharia_caixa' && ctaInfo && ctaInfo.action === 'generate_contract'"
        class="relative group flex items-center shrink-0"
      >
        <BaseButton
          :variant="ctaInfo.variant"
          size="icon"
          @click.stop="handleCtaClick"
          :disabled="ctaInfo.disabled"
          :class="['h-8 w-8 shrink-0 shadow-sm justify-center items-center', ctaInfo.class]"
        >
          <FileText class="w-[18px] h-[18px]" stroke-width="1.5" />
        </BaseButton>
        <!-- Tooltip -->
        <div class="absolute bottom-full right-0 mb-2 w-48 p-2 bg-surface border border-hairline text-ink text-[10px] leading-relaxed rounded-md shadow-xl z-50 text-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          {{ ctaInfo.disabled ? ctaInfo.tooltip : 'Gerar Contrato de Construção' }}
          <div class="absolute top-full right-5 border-4 border-transparent border-t-neutral-900"></div>
        </div>
      </div>

      <!-- Botão Portal: somente após obra liberada -->
      <div
        v-if="project.coluna === 'obra_liberada'"
        class="relative group flex items-center shrink-0"
      >
        <BaseButton
          variant="secondary"
          size="sm"
          @click.stop="sendPortalAccess"
          :disabled="isSendingPortalAccess"
          class="text-xs h-8 px-2.5 shrink-0 gap-1.5 font-medium bg-canvas"
        >
          <Loader2 v-if="isSendingPortalAccess" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          <Send v-else class="w-4 h-4" stroke-width="1.5" />
          Portal
        </BaseButton>

        <!-- Tooltip Visível no Hover -->
        <div class="absolute bottom-full right-0 mb-2 w-48 p-2 bg-surface border border-hairline text-ink text-[10px] leading-relaxed rounded-md shadow-xl z-50 text-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          Enviar link de acesso exclusivo ao Portal da Obra para o cliente (via WhatsApp).
          <div class="absolute top-full right-5 border-4 border-transparent border-t-neutral-900"></div>
        </div>
      </div>

      <BaseButton 
        v-if="ctaInfo && !(project.coluna === 'engenharia_caixa' && ctaInfo.action === 'generate_contract')" 
        :variant="ctaInfo.variant"
        size="sm"
        @click.stop="handleCtaClick" 
        :disabled="ctaInfo.disabled"
        :title="ctaInfo.tooltip"
        :class="['text-xs h-8 px-2.5 font-medium shrink-0 gap-1.5 shadow-sm', ctaInfo.class]"
      >
        <component v-if="ctaInfo.icon" :is="ctaInfo.icon" class="w-3.5 h-3.5" stroke-width="1.5" />
        {{ ctaInfo.text }}
      </BaseButton>
      </div>
    </div>

    <!-- Contract Modal -->
    <div v-if="isContractModalOpen" class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/45 backdrop-blur-sm" @click.stop>
      <div 
        class="bg-surface rounded-md border border-hairline shadow-2xl w-full flex flex-col overflow-hidden transition-all"
        :class="pdfPreviewUrl ? 'max-w-4xl h-[90vh]' : 'max-w-md'"
      >
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-hairline flex items-center justify-between bg-surface shrink-0">
          <h3 class="text-lg font-bold text-ink flex items-center gap-2">
            <FileSignature class="w-5 h-5 text-emerald-600" stroke-width="1.5" />
            {{ pdfPreviewUrl ? 'Visualização do Contrato' : 'Gerar Contrato' }}
          </h3>
          <BaseButton variant="ghost" size="icon" @click.stop="closeContractModal">
            <X class="w-5 h-5" stroke-width="1.25" />
          </BaseButton>
        </div>

        <!-- Mode 1: Selection -->
        <div v-if="!pdfPreviewUrl" class="p-6">
          <p class="text-sm text-ink-muted mb-4">Selecione o modelo de contrato para este projeto:</p>
          
          <div class="space-y-3 mb-6">
            <div v-if="isLoadingTemplates" class="text-sm text-ink-muted py-4 text-center">
              Carregando modelos...
            </div>
            <label 
              v-else
              v-for="tpl in templates" 
              :key="tpl.id"
              class="flex items-start gap-3 p-3 rounded-md border-2 cursor-pointer transition-colors" 
              :class="selectedTemplateId === tpl.id ? 'border-emerald-500/50 bg-emerald-950/10' : 'border-hairline hover:border-neutral-700'"
            >
              <input type="radio" v-model="selectedTemplateId" :value="tpl.id" class="mt-1 shrink-0 text-emerald-600 focus:ring-emerald-500">
              <div>
                <span class="block text-sm font-bold text-ink">{{ tpl.titulo }}</span>
                <span class="block text-xs text-ink-muted mt-0.5">Criado em: {{ formatDate(tpl.created_at) }}</span>
              </div>
            </label>
            <div v-if="!isLoadingTemplates && templates.length === 0" class="text-sm text-ink-muted py-6 flex flex-col items-center gap-2 bg-canvas/30 border border-dashed border-hairline rounded-lg text-center">
              <span>Nenhum template cadastrado.</span>
              <button 
                @click="router.push('/configuracoes/contratos'); closeContractModal()" 
                class="text-xs text-blue-500 hover:text-blue-600 font-semibold flex items-center gap-1.5 cursor-pointer hover:underline border-0 bg-transparent p-0"
              >
                <Pen class="w-3.5 h-3.5" stroke-width="1.5" />
                Configurar Templates
              </button>
            </div>
          </div>

          <div class="flex gap-3 justify-end mt-6 pt-4 border-t border-hairline p-6">
            <BaseButton variant="ghost" size="md" @click.stop="closeContractModal" class="h-9">Cancelar</BaseButton>
            <BaseButton 
              variant="primary"
              size="md"
              @click.stop="generateContractPreview" 
              :disabled="isGeneratingContract || !selectedTemplateId"
              class="h-9 font-semibold gap-2"
            >
              <Loader2 v-if="isGeneratingContract" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
              {{ isGeneratingContract ? 'Gerando...' : 'Visualizar Contrato' }}
            </BaseButton>
          </div>
        </div>

        <!-- Mode 2: Preview -->
        <div v-else class="flex flex-col flex-1 overflow-hidden">
          <div class="flex-1 bg-[#0A0A0A] p-4 overflow-hidden">
            <iframe :src="pdfPreviewUrl" class="w-full h-full rounded shadow-sm border border-neutral-800 bg-[#0A0A0A]"></iframe>
          </div>
          
          <div class="px-6 py-4 border-t border-hairline bg-surface shrink-0">
            <div class="flex justify-between items-center">
              <BaseButton variant="ghost" size="sm" @click.stop="pdfPreviewUrl = null" class="font-semibold gap-1">
                <ArrowLeft class="w-[18px] h-[18px]" stroke-width="1.5" /> Voltar à seleção
              </BaseButton>
              <div class="flex gap-3">
                <BaseButton variant="secondary" size="md" @click.stop="openInNewTab" class="h-9 gap-2">
                  <ExternalLink class="w-[18px] h-[18px]" stroke-width="1.5" /> Abrir em Nova Aba
                </BaseButton>
                <BaseButton variant="secondary" size="md" @click.stop="downloadContract" class="h-9 gap-2">
                  <Download class="w-[18px] h-[18px]" stroke-width="1.5" /> Download
                </BaseButton>
              </div>
            </div>
            <div class="mt-4 pt-4 border-t border-hairline flex items-center justify-between gap-4">
              <p class="text-xs text-ink-muted max-w-xs leading-relaxed">
                <Info class="w-[14px] h-[14px] text-amber-500 mr-1 inline align-middle" stroke-width="1.5" />
                Revise o documento acima. Ao aprovar, o contrato será marcado como gerado e ficará disponível para envio à ZapSign.
              </p>
              <BaseButton 
                variant="primary"
                size="md"
                @click.stop="approveContract" 
                :disabled="isApprovingContract"
                class="px-6 h-10 font-semibold shrink-0 gap-2"
              >
                <Loader2 v-if="isApprovingContract" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
                <CheckCircle2 v-else class="w-[18px] h-[18px]" stroke-width="1.5" />
                {{ isApprovingContract ? 'Aprovando...' : 'Aprovar Contrato' }}
              </BaseButton>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Setup SINAPI Modal -->
    <SetupOrcamentoModal 
      :is-open="isSetupModalOpen" 
      :project="project"
      @close="isSetupModalOpen = false"
      @salvar="onSetupSuccess"
    />

    <!-- Modal Editar Projeto -->
    <EditProjectModal
      :is-open="isEditModalOpen"
      :projeto-origem="project"
      @close="isEditModalOpen = false"
      @save="handleSaveProjectEdit"
    />

    <!-- Modal Rejeição de Documento -->
    <RejeicaoDocumentoModal
      :is-open="isRejeicaoModalOpen"
      :projeto-id="project.id"
      :documento="selectedDocParaRejeicao"
      :documentos="project.documentos || []"
      @close="isRejeicaoModalOpen = false"
      @rejeitado="onDocRejeitado"
    />

    <!-- Modal Diário de Obra -->
    <DiarioObraModal
      :is-open="isDiarioModalOpen"
      :project-id="project.id"
      :project-name="project.titulo_projeto || project.cliente_nome"
      @close="isDiarioModalOpen = false"
      @posted="emit('update')"
    />

    <!-- Modal Histórico e Notas -->
    <div v-if="isModalHistoricoAberto" class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/45 backdrop-blur-sm" @click.stop>
      <div class="bg-surface rounded-md border border-hairline shadow-2xl w-full max-w-lg flex flex-col overflow-hidden animate-in zoom-in duration-200 text-ink">
        
        <!-- Header -->
        <div class="px-6 py-4 border-b border-hairline flex items-center justify-between bg-surface shrink-0">
          <h3 class="text-lg font-bold text-ink flex items-center gap-2">
            <History class="w-5 h-5 text-blue-500" stroke-width="1.5" />
            Histórico e Notas
          </h3>
          <BaseButton variant="ghost" size="icon" @click.stop="isModalHistoricoAberto = false">
            <X class="w-5 h-5" stroke-width="1.25" />
          </BaseButton>
        </div>

        <!-- Corpo Superior (Nova Nota) -->
        <div class="p-6 border-b border-hairline bg-surface">
          <textarea 
            v-model="novaNota" 
            rows="3" 
            placeholder="Digite uma nova observação..."
            class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent rounded-md py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all resize-none text-ink placeholder:text-ink-muted"
          ></textarea>
          <div class="flex justify-end mt-3">
            <BaseButton 
              variant="primary"
              size="md"
              @click.stop="salvarNovaNota"
              :disabled="!novaNota.trim()"
              class="h-9 font-semibold gap-2"
            >
              <Plus class="w-4 h-4" stroke-width="1.5" /> Adicionar Nota
            </BaseButton>
          </div>
        </div>

        <!-- Corpo Inferior (Timeline) -->
        <div class="p-6 bg-canvas flex-1 overflow-y-auto max-h-64">
          <div class="relative border-l-2 border-neutral-800 ml-3 space-y-6">
            <div v-for="nota in notasHistorico" :key="nota.id" class="relative pl-6">
              <div class="absolute -left-[7px] top-1.5 w-3 h-3 bg-blue-500 rounded-full ring-4 ring-canvas"></div>
              <div class="bg-surface p-3 rounded-md border border-hairline shadow-sm hover:border-neutral-700 transition-colors">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-bold text-ink">{{ nota.autor }}</span>
                  <span class="text-[10px] font-medium text-ink-muted">{{ formatarData(nota.data) }}</span>
                </div>
                <p class="text-sm text-ink-muted leading-relaxed">{{ nota.texto }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Confirmação Customizado (Padrão do Sistema) -->
    <div v-if="confirmModal.isOpen" class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/45 backdrop-blur-sm" @click.stop>
      <div class="bg-surface rounded-md border border-hairline shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in duration-200 text-ink">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-hairline flex items-center gap-3 bg-surface">
          <div :class="confirmModal.isDanger ? 'bg-red-955/20 text-red-400' : 'bg-amber-955/20 text-amber-400'" class="p-2 rounded-full flex items-center justify-center">
            <AlertTriangle v-if="confirmModal.isDanger" class="w-5 h-5" stroke-width="1.5" />
            <HelpCircle v-else class="w-5 h-5" stroke-width="1.5" />
          </div>
          <h3 class="text-base font-bold text-ink">{{ confirmModal.title }}</h3>
        </div>

        <!-- Body -->
        <div class="p-6">
          <p class="text-sm text-ink-muted leading-relaxed">{{ confirmModal.message }}</p>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 bg-canvas border-t border-hairline flex items-center justify-end gap-3">
          <BaseButton 
            variant="ghost"
            size="md"
            @click.stop="closeConfirmModal" 
            :disabled="statusBotao === 'loading'"
            class="h-9"
          >
            Cancelar
          </BaseButton>
          <BaseButton 
            @click.stop="executeConfirm" 
            :disabled="statusBotao !== 'idle'"
            :variant="confirmModal.isDanger ? 'danger' : 'primary'"
            size="md"
            :class="[
              statusBotao === 'success' ? '!bg-emerald-600 !text-white !border-transparent' : '',
              'h-9 font-bold gap-2'
            ]"
          >
            <Loader2 v-if="statusBotao === 'loading'" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
            <CheckCircle2 v-else-if="statusBotao === 'success'" class="w-[18px] h-[18px]" stroke-width="1.5" />
            <span>{{ 
              statusBotao === 'loading' ? confirmModal.loadingText : 
              statusBotao === 'success' ? confirmModal.successText : 
              confirmModal.confirmText 
            }}</span>
          </BaseButton>
        </div>
      </div>
    </div>
    
    <!-- Drawer Detalhes Projeto -->
    <DrawerDetalheProjeto
      :is-open="isDrawerOpen"
      :project="project"
      :documento-inicial="selectedDocParaVisualizar"
      @close="isDrawerOpen = false"
      @update="emit('update')"
    />
  </div>
</template>
