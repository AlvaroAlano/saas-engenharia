import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'vertice_notificacoes'
const TTL_MS      = 7 * 24 * 60 * 60 * 1000  // 7 dias
const MAX_ITEMS   = 50
const DEDUP_MS    = 60_000                     // ignora duplicata dentro de 1 min

function carregarDoStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const agora = Date.now()
    return JSON.parse(raw)
      .filter(n => agora - new Date(n.criadaEm).getTime() < TTL_MS)
      .map(n => ({ ...n, criadaEm: new Date(n.criadaEm) }))
  } catch {
    return []
  }
}

function salvarNoStorage(lista) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(lista))
  } catch {
    /* quota exceeded — silent */
  }
}

// Estado global compartilhado entre todos os chamadores do composable
const notificacoes = ref(carregarDoStorage())

// Persiste automaticamente a cada mudança
watch(notificacoes, (val) => salvarNoStorage(val), { deep: true })

export function useNotificacoes() {
  const naoLidas = computed(() => notificacoes.value.filter(n => !n.lida).length)

  const adicionarNotificacao = (projeto, tipo) => {
    // Deduplicação: ignora se já existe notif não-lida recente do mesmo projeto+tipo
    const duplicata = notificacoes.value.find(n =>
      n.projetoId === projeto.id &&
      n.tipo === tipo &&
      !n.lida &&
      Date.now() - new Date(n.criadaEm).getTime() < DEDUP_MS
    )
    if (duplicata) return

    const mensagem = tipo === 'reenvio'
      ? `${projeto.cliente_nome} reencaminhou os documentos que haviam sido recusados.`
      : `${projeto.cliente_nome} encaminhou os documentos para analisar.`

    notificacoes.value.unshift({
      id: Date.now(),
      projetoId: projeto.id,
      clienteNome: projeto.cliente_nome,
      mensagem,
      tipo,
      lida: false,
      criadaEm: new Date(),
    })

    // Mantém máximo de MAX_ITEMS para não inflar o localStorage
    if (notificacoes.value.length > MAX_ITEMS) {
      notificacoes.value = notificacoes.value.slice(0, MAX_ITEMS)
    }
  }

  const marcarLida = (id) => {
    const n = notificacoes.value.find(n => n.id === id)
    if (n) n.lida = true
  }

  const marcarTodasLidas = () => {
    notificacoes.value.forEach(n => { n.lida = true })
  }

  return { notificacoes, naoLidas, adicionarNotificacao, marcarLida, marcarTodasLidas }
}
