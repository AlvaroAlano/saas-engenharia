<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '../supabase'
import { useProfile } from '../composables/useProfile'
import { User, Camera, IdCard, Loader2 } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const { refreshProfile } = useProfile()
const { showToast } = useToast()

const profile = ref({
  nome_completo: '',
  email: '',
  telefone: '',
  registro_crea_cau: '',
  foto_perfil: ''
})

const isLoading = ref(true)
const isSaving = ref(false)
const uploadProgress = ref(0)

const fetchProfile = async () => {
  isLoading.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    // Tentar buscar perfil existente no banco
    const { data, error } = await supabase
      .from('perfis_b2b')
      .select('*')
      .eq('id', user.id)
      .single()

    if (data) {
      profile.value = { ...data }
    } else {
      // Fallback: usar dados do auth se o perfil b2b ainda não existir
      profile.value.email = user.email
      profile.value.nome_completo = user.user_metadata?.full_name || ''
    }
  } catch (error) {
    console.error('Erro ao carregar perfil:', error)
  } finally {
    isLoading.value = false
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const fileExt = file.name.split('.').pop()
  const fileName = `${Math.random().toString(36).substring(2)}.${fileExt}`
  const filePath = `avatars/${fileName}`

  try {
    uploadProgress.value = 10
    // Upload para o bucket 'identidade'
    const { error: uploadError } = await supabase.storage
      .from('identidade')
      .upload(filePath, file)

    if (uploadError) throw uploadError

    uploadProgress.value = 50
    // Obter URL pública
    const { data: { publicUrl } } = supabase.storage
      .from('identidade')
      .getPublicUrl(filePath)

    profile.value.foto_perfil = publicUrl
    uploadProgress.value = 100
    setTimeout(() => uploadProgress.value = 0, 2000)
  } catch (error) {
    console.error('Erro no upload:', error)
    showToast('Erro ao enviar imagem.', 'error')
    uploadProgress.value = 0
  }
}

const saveProfile = async () => {
  isSaving.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    
    const { error } = await supabase
      .from('perfis_b2b')
      .upsert({
        id: user.id,
        nome_completo: profile.value.nome_completo,
        email: profile.value.email,
        telefone: profile.value.telefone.replace(/\D/g, ''),
        registro_crea_cau: profile.value.registro_crea_cau,
        foto_perfil: profile.value.foto_perfil,
        updated_at: new Date()
      })

    if (error) throw error
    // Atualizar o cache do composable para refletir no TopHeader
    await refreshProfile(true)
    showToast('Perfil atualizado com sucesso!', 'success')
  } catch (error) {
    console.error('Erro ao salvar perfil:', error)
    showToast('Erro ao salvar dados.', 'error')
  } finally {
    isSaving.value = false
  }
}

onMounted(fetchProfile)
</script>

<template>
  <div class="max-w-4xl animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary"></div>
    </div>

    <div v-else class="space-y-6">
      <!-- Profile Header / Photo -->
      <div class="bg-surface p-6 rounded-2xl border border-hairline flex flex-col sm:flex-row items-center gap-6">
        <div class="relative group">
          <div class="h-24 w-24 rounded-2xl overflow-hidden border-2 border-hairline bg-canvas flex items-center justify-center">
            <img v-if="profile.foto_perfil" :src="profile.foto_perfil" class="h-full w-full object-cover" />
            <User v-else class="w-10 h-10 text-ink-muted" stroke-width="1.5" />
          </div>
          <label class="absolute -bottom-2 -right-2 bg-surface border border-hairline p-1.5 rounded-lg cursor-pointer hover:bg-canvas transition-colors flex items-center justify-center">
            <Camera class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
            <input type="file" class="hidden" accept="image/*" @change="handleFileUpload" />
          </label>
        </div>
        
        <div class="flex-1 text-center sm:text-left">
          <h2 class="text-xl font-bold text-ink">{{ profile.nome_completo || 'Seu Nome' }}</h2>
          <p class="text-sm text-ink-muted">{{ profile.email }}</p>
          <div v-if="uploadProgress > 0" class="mt-3 w-full max-w-xs bg-canvas rounded-full h-1.5 overflow-hidden">
            <div class="bg-brand-primary h-full transition-all duration-300" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
        </div>
      </div>

      <!-- Main Form -->
      <div class="bg-surface rounded-2xl border border-hairline overflow-hidden">
        <div class="px-6 py-4 border-b border-hairline bg-canvas/50">
          <h3 class="text-sm font-bold text-ink flex items-center gap-2">
            <IdCard class="w-4.5 h-4.5 text-ink" stroke-width="1.5" />
            Informações Pessoais e Profissionais
          </h3>
        </div>
        
        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Nome Completo <span class="text-red-500">*</span></label>
            <input v-model="profile.nome_completo" @input="profile.nome_completo = profile.nome_completo.replace(/[0-9]/g, '')" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="Ex: Eng. Alvaro Alano" required>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">E-mail de Contato</label>
            <input v-model="profile.email" type="email" class="w-full bg-canvas border border-hairline text-ink-muted rounded-xl px-4 py-2.5 text-sm cursor-not-allowed" readonly>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Telefone / WhatsApp <span class="text-red-500">*</span></label>
            <input v-model="profile.telefone" v-maska="'(##) #####-####'" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="(48) 99999-9999" required>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Registro Profissional (CREA/CAU)</label>
            <input v-model="profile.registro_crea_cau" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="Ex: CREA/SC 123456-D">
          </div>
        </div>

        <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex justify-end">
          <button @click="saveProfile" :disabled="isSaving" class="bg-brand-primary hover:bg-brand-hover text-white px-6 py-2 rounded-xl font-bold text-sm transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer">
            <Loader2 v-if="isSaving" class="w-4.5 h-4.5 animate-spin" stroke-width="1.5" />
            {{ isSaving ? 'Salvando...' : 'Salvar Alterações' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
