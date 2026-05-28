import { ref, computed } from 'vue'

const notificacoes = ref([])

export function useNotificacoes() {
  const naoLidas = computed(() => notificacoes.value.filter(n => !n.lida).length)

  const adicionarNotificacao = (projeto, tipo) => {
    const msg = tipo === 'reenvio'
      ? `${projeto.cliente_nome} reencaminhou os documentos que haviam sido recusados.`
      : `${projeto.cliente_nome} encaminhou os documentos para analisar.`

    notificacoes.value.unshift({
      id: Date.now(),
      projetoId: projeto.id,
      clienteNome: projeto.cliente_nome,
      mensagem: msg,
      tipo,
      lida: false,
      criadaEm: new Date()
    })
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
