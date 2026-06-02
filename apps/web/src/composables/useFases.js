import { ref, readonly } from 'vue'
import axios from 'axios'
import { ETAPAS_OBRA } from '../constants/etapas'

// Singleton compartilhado — um único fetch por sessão, independente de quantos
// componentes chamam useFases() simultaneamente.
const _fases      = ref([...ETAPAS_OBRA])
const _isLoading  = ref(false)
let   _initialized = false

export function useFases() {
  /**
   * Garante que as fases estejam carregadas. Seguro chamar em onMounted
   * de múltiplos componentes — só faz o fetch uma vez.
   */
  const ensureFases = async () => {
    if (_initialized) return
    _isLoading.value = true
    try {
      const res = await axios.get('/configuracoes/fases')
      if (res.data?.data?.length) {
        _fases.value = res.data.data
      }
      _initialized = true
    } catch {
      _initialized = true // mantém fallback, não tenta de novo
    } finally {
      _isLoading.value = false
    }
  }

  /**
   * Força recarregamento — chamar após criar, editar ou excluir fases
   * para que todos os componentes reflitam a mudança.
   */
  const reloadFases = async () => {
    _initialized = false
    _fases.value = [...ETAPAS_OBRA]
    await ensureFases()
  }

  return {
    fases:         readonly(_fases),
    isLoadingFases: readonly(_isLoading),
    ensureFases,
    reloadFases,
  }
}
