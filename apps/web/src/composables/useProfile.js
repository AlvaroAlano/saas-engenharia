import { ref, onMounted } from 'vue'
import { supabase } from '../supabase'

const profile = ref(null)
const empresa = ref(null)
const isLoading = ref(false)

export function useProfile() {
  const fetchProfileData = async (force = false) => {
    if (profile.value && !force) return // Já carregado

    isLoading.value = true
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      // Buscar Perfil
      const { data: pData } = await supabase
        .from('perfis_b2b')
        .select('*')
        .eq('id', user.id)
        .single()
      
      if (pData) profile.value = pData

      // Buscar Empresa
      const { data: eData } = await supabase
        .from('dados_empresa')
        .select('*')
        .eq('usuario_id', user.id)
        .single()
      
      if (eData) empresa.value = eData

    } catch (error) {
      console.error('Erro no useProfile:', error)
    } finally {
      isLoading.value = false
    }
  }

  onMounted(fetchProfileData)

  return {
    profile,
    empresa,
    isLoading,
    refreshProfile: fetchProfileData
  }
}
