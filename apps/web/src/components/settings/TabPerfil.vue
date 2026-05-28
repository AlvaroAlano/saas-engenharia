<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '../../supabase'
import { useProfile } from '../../composables/useProfile'
import { useToast } from '../../composables/useToast'
import { User, Camera, Loader2 } from 'lucide-vue-next'
import BaseButton from '../ui/BaseButton.vue'

const { refreshProfile } = useProfile()
const { showToast } = useToast()

const profile = ref({ nome_completo: '', email: '', telefone: '', registro_crea_cau: '', foto_perfil: '' })
const isLoading = ref(true)
const isSavingProfile = ref(false)
const isSavingPassword = ref(false)
const password = ref({ nova: '', confirmar: '' })

const fetchProfile = async () => {
  isLoading.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return
    const { data } = await supabase.from('perfis_b2b').select('*').eq('id', user.id).single()
    if (data) profile.value = { ...data }
    else profile.value.email = user.email || ''
  } catch (e) {
    console.error('Erro ao carregar perfil:', e)
  } finally {
    isLoading.value = false
  }
}

const handleAvatarUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  const ext = file.name.split('.').pop()
  const filePath = `avatars/${Math.random().toString(36).slice(2)}.${ext}`
  const { error } = await supabase.storage.from('identidade').upload(filePath, file)
  if (error) { showToast('Erro ao enviar imagem.', 'error'); return }
  const { data: { publicUrl } } = supabase.storage.from('identidade').getPublicUrl(filePath)
  profile.value.foto_perfil = publicUrl
}

const saveProfile = async () => {
  isSavingProfile.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    const { error } = await supabase.from('perfis_b2b').upsert({
      id: user.id,
      nome_completo: profile.value.nome_completo,
      email: profile.value.email,
      telefone: (profile.value.telefone || '').replace(/\D/g, ''),
      registro_crea_cau: profile.value.registro_crea_cau,
      foto_perfil: profile.value.foto_perfil,
      updated_at: new Date()
    })
    if (error) throw error
    await refreshProfile(true)
    showToast('Perfil atualizado com sucesso!', 'success')
  } catch (e) {
    showToast('Erro ao salvar perfil.', 'error')
  } finally {
    isSavingProfile.value = false
  }
}

const savePassword = async () => {
  if (!password.value.nova) return
  if (password.value.nova !== password.value.confirmar) {
    showToast('As senhas não conferem.', 'error'); return
  }
  if (password.value.nova.length < 8) {
    showToast('A senha deve ter ao menos 8 caracteres.', 'error'); return
  }
  isSavingPassword.value = true
  try {
    const { error } = await supabase.auth.updateUser({ password: password.value.nova })
    if (error) throw error
    password.value = { nova: '', confirmar: '' }
    showToast('Senha alterada com sucesso!', 'success')
  } catch (e) {
    showToast('Erro ao alterar senha.', 'error')
  } finally {
    isSavingPassword.value = false
  }
}

const deleteAccount = () => {
  showToast('Para excluir sua conta entre em contato com o suporte.', 'info', 5000)
}

onMounted(fetchProfile)
</script>

<template>
  <div v-if="isLoading" class="flex justify-center py-16">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary"></div>
  </div>

  <div v-else class="space-y-5">

    <!-- Card: Foto de Perfil -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Foto de Perfil</h3>
        <p class="text-xs text-ink-muted mt-0.5">Visível no painel, contratos e vitrine pública.</p>
      </div>
      <div class="px-6 py-5 flex items-center gap-5">
        <div class="relative shrink-0">
          <div class="h-20 w-20 rounded-md overflow-hidden border-2 border-hairline bg-canvas flex items-center justify-center">
            <img v-if="profile.foto_perfil" :src="profile.foto_perfil" class="h-full w-full object-cover" />
            <User v-else class="w-8 h-8 text-ink-muted" stroke-width="1.5" />
          </div>
          <label class="absolute -bottom-1.5 -right-1.5 bg-surface border border-hairline p-1.5 rounded-lg cursor-pointer hover:bg-canvas transition-colors flex items-center justify-center">
            <Camera class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
            <input type="file" class="hidden" accept="image/*" @change="handleAvatarUpload" />
          </label>
        </div>
        <div>
          <p class="text-sm font-semibold text-ink">{{ profile.nome_completo || 'Sem nome' }}</p>
          <p class="text-xs text-ink-muted">{{ profile.email }}</p>
        </div>
      </div>
    </div>

    <!-- Card: Informações Pessoais -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Informações Profissionais</h3>
        <p class="text-xs text-ink-muted mt-0.5">Nome, contato e registro profissional exibidos nos documentos.</p>
      </div>
      <div class="px-6 py-5 grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Nome Completo <span class="text-red-500">*</span></label>
          <input v-model="profile.nome_completo" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-md px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="Ex: Eng. Álvaro Alano" />
        </div>
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">E-mail</label>
          <input v-model="profile.email" type="email" class="w-full bg-canvas border border-hairline text-ink-muted rounded-md px-4 py-2.5 text-sm cursor-not-allowed" readonly />
        </div>
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Telefone / WhatsApp</label>
          <input v-model="profile.telefone" v-maska="'(##) #####-####'" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-md px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="(48) 99999-9999" />
        </div>
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Registro CREA/CAU</label>
          <input v-model="profile.registro_crea_cau" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-md px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="CREA/SC 123456-D" />
        </div>
      </div>
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex justify-end">
        <BaseButton variant="primary" @click="saveProfile" :disabled="isSavingProfile" class="px-5 h-9 font-bold gap-2">
          <Loader2 v-if="isSavingProfile" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          {{ isSavingProfile ? 'Salvando...' : 'Salvar Alterações' }}
        </BaseButton>
      </div>
    </div>

    <!-- Card: Alterar Senha -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Alterar Senha</h3>
        <p class="text-xs text-ink-muted mt-0.5">Mínimo de 8 caracteres. Use uma senha forte e única.</p>
      </div>
      <div class="px-6 py-5 grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Nova Senha</label>
          <input v-model="password.nova" type="password" class="w-full bg-canvas border border-hairline text-ink rounded-md px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="••••••••" />
        </div>
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Confirmar Senha</label>
          <input v-model="password.confirmar" type="password" class="w-full bg-canvas border border-hairline text-ink rounded-md px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="••••••••" />
        </div>
      </div>
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex justify-end">
        <BaseButton variant="primary" @click="savePassword" :disabled="isSavingPassword || !password.nova" class="px-5 h-9 font-bold gap-2">
          <Loader2 v-if="isSavingPassword" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          {{ isSavingPassword ? 'Alterando...' : 'Alterar Senha' }}
        </BaseButton>
      </div>
    </div>

    <!-- Card: Danger Zone -->
    <div class="bg-surface rounded-md border border-red-200 dark:border-red-900/50 overflow-hidden">
      <div class="px-6 py-5 border-b border-red-100 dark:border-red-900/30">
        <h3 class="text-sm font-bold text-red-600 dark:text-red-400">Danger Zone</h3>
        <p class="text-xs text-ink-muted mt-0.5">Ações permanentes e irreversíveis.</p>
      </div>
      <div class="px-6 py-5">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-sm font-semibold text-ink">Excluir Conta</p>
            <p class="text-xs text-ink-muted mt-0.5">Remove permanentemente sua conta e todos os dados associados.</p>
          </div>
          <BaseButton variant="danger" size="sm" @click="deleteAccount" class="shrink-0 font-bold px-4 py-2">
            Excluir Conta
          </BaseButton>
        </div>
      </div>
    </div>

  </div>
</template>
