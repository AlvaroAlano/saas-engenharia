import { ref, onMounted } from 'vue'
import { supabase } from '../supabase'

// Estado singleton — compartilhado entre todos os consumidores
const profile   = ref(null)
const empresa   = ref(null)
const isLoading = ref(false)

// Promise da requisição em andamento — evita fetches paralelos simultâneos
let _fetchPromise = null

export function useProfile() {
  const fetchProfileData = async (force = false) => {
    if (profile.value && !force) return
    // Se já existe uma requisição em andamento, aguarda a mesma promise
    if (_fetchPromise && !force) return _fetchPromise

    isLoading.value = true
    _fetchPromise = (async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser()
        if (!user) return

        const { data: pData } = await supabase
          .from('perfis_b2b')
          .select('*')
          .eq('id', user.id)
          .single()
        if (pData) profile.value = pData

        const { data: eData } = await supabase
          .from('dados_empresa')
          .select('*')
          .eq('usuario_id', user.id)
          .single()
        if (eData) empresa.value = eData

      } catch (error) {
        console.error('Erro no useProfile:', error)
      } finally {
        isLoading.value  = false
        _fetchPromise    = null
      }
    })()

    return _fetchPromise
  }

  onMounted(fetchProfileData)

  return {
    profile,
    empresa,
    isLoading,
    refreshProfile: fetchProfileData,
  }
}
