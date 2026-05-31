<script setup>
import { ref, computed, onMounted } from 'vue'
import { supabase } from '../supabase'
import { useProfile } from '../composables/useProfile'
import { Camera, IdCard, Loader2, ExternalLink, Lock, Eye, EyeOff, ShieldCheck } from 'lucide-vue-next'
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
    const { data } = await supabase
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

  const ALLOWED = ['image/jpeg', 'image/png', 'image/webp']
  const MAX_MB  = 5

  if (!ALLOWED.includes(file.type)) {
    showToast('Formato inválido. Use JPG, PNG ou WebP.', 'error')
    return
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    showToast(`Imagem muito grande. Máximo ${MAX_MB} MB.`, 'error')
    return
  }

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return

  const fileExt = file.name.split('.').pop().toLowerCase()
  // Path fixo por usuário — sobrescreve automaticamente o avatar anterior
  const filePath = `avatars/${user.id}.${fileExt}`

  try {
    uploadProgress.value = 10
    const { error: uploadError } = await supabase.storage
      .from('identidade')
      .upload(filePath, file, { upsert: true })

    if (uploadError) throw uploadError

    uploadProgress.value = 80
    const { data: { publicUrl } } = supabase.storage
      .from('identidade')
      .getPublicUrl(filePath)

    // Força revalidação do cache do browser adicionando timestamp
    profile.value.foto_perfil = `${publicUrl}?t=${Date.now()}`
    uploadProgress.value = 100
    setTimeout(() => uploadProgress.value = 0, 2000)
  } catch (error) {
    console.error('Erro no upload:', error)
    showToast('Erro ao enviar imagem.', 'error')
    uploadProgress.value = 0
  }
}

const saveProfile = async () => {
  if (!profile.value.nome_completo?.trim()) {
    showToast('Nome completo é obrigatório.', 'error')
    return
  }
  if (!profile.value.telefone?.replace(/\D/g, '')) {
    showToast('Telefone é obrigatório.', 'error')
    return
  }

  isSaving.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()

    const { error } = await supabase
      .from('perfis_b2b')
      .upsert({
        id: user.id,
        nome_completo: profile.value.nome_completo.trim(),
        telefone: profile.value.telefone.replace(/\D/g, ''),
        registro_crea_cau: profile.value.registro_crea_cau || null,
        foto_perfil: profile.value.foto_perfil || null,
        updated_at: new Date()
      })

    if (error) throw error
    await refreshProfile(true)
    showToast('Perfil atualizado com sucesso!', 'success')
  } catch (error) {
    console.error('Erro ao salvar perfil:', error)
    showToast('Erro ao salvar dados.', 'error')
  } finally {
    isSaving.value = false
  }
}

// ─── Iniciais do avatar ───────────────────────────────────────────────────────
const initials = computed(() => {
  const name = (profile.value.nome_completo || '').replace(/^Eng\.\s*/i, '').trim()
  if (!name) return '?'
  const words = name.split(/\s+/).filter(Boolean)
  return words.length === 1
    ? words[0][0].toUpperCase()
    : (words[0][0] + words[words.length - 1][0]).toUpperCase()
})

const AVATAR_COLORS = [
  'bg-brand-blue', 'bg-brand-orange', 'bg-brand-secure',
  'bg-emerald-600', 'bg-violet-600'
]
const avatarBg = computed(() => {
  const seed = (profile.value.nome_completo || 'A').charCodeAt(0)
  return AVATAR_COLORS[seed % AVATAR_COLORS.length]
})

// ─── Completude do perfil ─────────────────────────────────────────────────────
const CAMPOS_COMPLETUDE = [
  { key: 'nome_completo', label: 'Nome' },
  { key: 'telefone',       label: 'Telefone' },
  { key: 'registro_crea_cau', label: 'CREA/CAU' },
  { key: 'foto_perfil',    label: 'Foto' },
]
const completude = computed(() => {
  const filled = CAMPOS_COMPLETUDE.filter(c => !!profile.value[c.key]).length
  return Math.round((filled / CAMPOS_COMPLETUDE.length) * 100)
})
const camposFaltando = computed(() =>
  CAMPOS_COMPLETUDE.filter(c => !profile.value[c.key]).map(c => c.label)
)

// Validação de formato CREA/CAU — permissiva para cobrir variações regionais
// Ex: CREA/SC 123456-D · CREA-SC 123456 · CAU-BR 12345-0 · CAU A12345-0
const creaValido = computed(() => {
  const val = profile.value.registro_crea_cau?.trim()
  if (!val) return null // campo vazio → sem feedback
  return /^(CREA|CAU)[^a-z]{1,5}\d+/i.test(val)
})

// ─── Alterar senha ────────────────────────────────────────────────────────────
const senha = ref({ nova: '', confirmar: '' })
const isSavingSenha = ref(false)
const showNovaSenha = ref(false)
const showConfirmarSenha = ref(false)

const alterarSenha = async () => {
  if (senha.value.nova.length < 6) {
    showToast('A senha deve ter pelo menos 6 caracteres.', 'error')
    return
  }
  if (senha.value.nova !== senha.value.confirmar) {
    showToast('As senhas não coincidem.', 'error')
    return
  }
  isSavingSenha.value = true
  try {
    const { error } = await supabase.auth.updateUser({ password: senha.value.nova })
    if (error) throw error
    senha.value = { nova: '', confirmar: '' }
    showToast('Senha alterada com sucesso!', 'success')
  } catch (error) {
    console.error('Erro ao alterar senha:', error)
    showToast('Erro ao alterar senha.', 'error')
  } finally {
    isSavingSenha.value = false
  }
}

onMounted(fetchProfile)
</script>

<template>
  <div class="max-w-4xl animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div v-if="isLoading" class="flex justify-center py-12">
      <Loader2 class="w-8 h-8 animate-spin text-brand-primary" stroke-width="1.5" />
    </div>

    <div v-else class="space-y-6">

      <!-- ── Card de Perfil ──────────────────────────────────────────── -->
      <div class="bg-surface p-6 rounded-2xl border border-hairline">
        <div class="flex flex-col sm:flex-row items-center sm:items-start gap-6">

          <!-- Avatar -->
          <div class="relative shrink-0">
            <div class="h-24 w-24 rounded-2xl overflow-hidden border-2 border-hairline">
              <img v-if="profile.foto_perfil" :src="profile.foto_perfil" class="h-full w-full object-cover" />
              <div v-else :class="['h-full w-full flex items-center justify-center', avatarBg]">
                <span class="text-2xl font-black text-white tracking-tight select-none">{{ initials }}</span>
              </div>
            </div>
            <label class="absolute -bottom-2 -right-2 bg-surface border border-hairline p-1.5 rounded-lg cursor-pointer hover:bg-canvas transition-colors flex items-center justify-center shadow-sm" title="Alterar foto">
              <Camera class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
              <input type="file" class="hidden" accept="image/jpeg,image/png,image/webp" @change="handleFileUpload" />
            </label>
          </div>

          <!-- Info + completude -->
          <div class="flex-1 min-w-0 text-center sm:text-left w-full">
            <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
              <div>
                <h2 class="text-xl font-bold text-ink">{{ profile.nome_completo || 'Seu Nome' }}</h2>
                <p class="text-sm text-ink-muted">{{ profile.email }}</p>
              </div>
              <!-- Link vitrine -->
              <a
                v-if="profile.slug_vitrine"
                :href="`/vitrine/${profile.slug_vitrine}`"
                target="_blank"
                class="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-blue hover:underline underline-offset-2 shrink-0 transition-colors"
              >
                <ExternalLink class="w-3.5 h-3.5" stroke-width="2" />
                Ver minha vitrine
              </a>
            </div>

            <!-- Barra de completude -->
            <div class="mt-4">
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-xs font-semibold text-ink-muted">Perfil {{ completude }}% completo</span>
                <span v-if="camposFaltando.length" class="text-[11px] text-ink-muted">
                  Faltam: <span class="font-semibold text-ink">{{ camposFaltando.join(', ') }}</span>
                </span>
              </div>
              <div class="w-full bg-canvas rounded-full h-1.5 overflow-hidden border border-hairline">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="completude === 100 ? 'bg-semantic-success' : completude >= 50 ? 'bg-brand-blue' : 'bg-brand-orange'"
                  :style="{ width: `${completude}%` }"
                />
              </div>
            </div>

            <!-- Progress upload -->
            <div v-if="uploadProgress > 0" class="mt-2 w-full bg-canvas rounded-full h-1 overflow-hidden">
              <div class="bg-brand-blue h-full transition-all duration-300" :style="{ width: `${uploadProgress}%` }" />
            </div>
          </div>
        </div>
      </div>

      <!-- ── Informações Pessoais ────────────────────────────────────── -->
      <div class="bg-surface rounded-2xl border border-hairline overflow-hidden">
        <div class="px-6 py-4 border-b border-hairline bg-canvas/50">
          <h3 class="text-sm font-bold text-ink flex items-center gap-2">
            <IdCard class="w-5 h-5 text-ink" stroke-width="1.5" />
            Informações Pessoais e Profissionais
          </h3>
        </div>

        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Nome Completo <span class="text-red-500">*</span></label>
            <input v-model="profile.nome_completo" @input="profile.nome_completo = profile.nome_completo.replace(/[0-9]/g, '')" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="Ex: Eng. Alvaro Alano" />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase flex items-center gap-1.5">
              E-mail de acesso
              <span class="normal-case font-normal text-[10px] bg-canvas border border-hairline text-ink-muted px-1.5 py-0.5 rounded">somente leitura</span>
            </label>
            <input v-model="profile.email" type="email" class="w-full bg-canvas/50 border border-hairline text-ink-muted rounded-xl px-4 py-2.5 text-sm cursor-not-allowed select-none opacity-70" readonly tabindex="-1" />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Telefone / WhatsApp <span class="text-red-500">*</span></label>
            <input v-model="profile.telefone" v-maska="'(##) #####-####'" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="(48) 99999-9999" />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Registro Profissional (CREA/CAU)</label>
            <input
              v-model="profile.registro_crea_cau"
              type="text"
              placeholder="Ex: CREA/SC 123456-D"
              class="w-full bg-canvas border text-ink rounded-xl px-4 py-2.5 text-sm outline-none transition-all placeholder:text-ink-muted focus:ring-1"
              :class="creaValido === false
                ? 'border-red-400 focus:ring-red-400 focus:border-red-400'
                : creaValido === true
                  ? 'border-semantic-success focus:ring-semantic-success focus:border-semantic-success'
                  : 'border-hairline focus:ring-brand-primary focus:border-brand-primary'"
            />
            <p v-if="creaValido === false" class="text-xs text-red-500 font-medium">
              Formato inválido. Use ex: CREA/SC 123456-D ou CAU-BR 12345-0
            </p>
            <p v-else-if="creaValido === true" class="text-xs text-semantic-success font-medium">
              Formato válido ✓
            </p>
          </div>
        </div>

        <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex items-center justify-between gap-4">
          <p class="text-xs text-ink-muted hidden sm:block">Nome e telefone são obrigatórios. CREA/CAU aparece na sua vitrine pública.</p>
          <button @click="saveProfile" :disabled="isSaving" class="bg-brand-primary hover:bg-brand-hover text-white px-6 py-2 rounded-xl font-bold text-sm transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer shrink-0">
            <Loader2 v-if="isSaving" class="w-5 h-5 animate-spin" stroke-width="1.5" />
            {{ isSaving ? 'Salvando...' : 'Salvar Alterações' }}
          </button>
        </div>
      </div>

      <!-- ── Alterar Senha ───────────────────────────────────────────── -->
      <div class="bg-surface rounded-2xl border border-hairline overflow-hidden">
        <div class="px-6 py-4 border-b border-hairline bg-canvas/50">
          <h3 class="text-sm font-bold text-ink flex items-center gap-2">
            <ShieldCheck class="w-5 h-5 text-ink" stroke-width="1.5" />
            Segurança — Alterar Senha
          </h3>
        </div>

        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Nova Senha</label>
            <div class="relative">
              <Lock class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted pointer-events-none" stroke-width="1.5" />
              <input
                v-model="senha.nova"
                :type="showNovaSenha ? 'text' : 'password'"
                class="w-full bg-canvas border border-hairline text-ink rounded-xl pl-10 pr-10 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
                placeholder="Mínimo 6 caracteres"
              />
              <button type="button" @click="showNovaSenha = !showNovaSenha" class="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-ink-muted hover:text-ink transition-colors cursor-pointer">
                <EyeOff v-if="showNovaSenha" class="w-4 h-4" stroke-width="1.5" />
                <Eye v-else class="w-4 h-4" stroke-width="1.5" />
              </button>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Confirmar Nova Senha</label>
            <div class="relative">
              <Lock class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted pointer-events-none" stroke-width="1.5" />
              <input
                v-model="senha.confirmar"
                :type="showConfirmarSenha ? 'text' : 'password'"
                class="w-full bg-canvas border border-hairline text-ink rounded-xl pl-10 pr-10 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
                :class="senha.confirmar && senha.nova !== senha.confirmar ? 'border-red-400 focus:ring-red-400' : ''"
                placeholder="Repita a nova senha"
              />
              <button type="button" @click="showConfirmarSenha = !showConfirmarSenha" class="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-ink-muted hover:text-ink transition-colors cursor-pointer">
                <EyeOff v-if="showConfirmarSenha" class="w-4 h-4" stroke-width="1.5" />
                <Eye v-else class="w-4 h-4" stroke-width="1.5" />
              </button>
            </div>
            <p v-if="senha.confirmar && senha.nova !== senha.confirmar" class="text-xs text-red-500 font-medium">As senhas não coincidem.</p>
          </div>
        </div>

        <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex items-center justify-between gap-4">
          <p class="text-xs text-ink-muted hidden sm:block">Use no mínimo 6 caracteres. Você será mantido logado após a alteração.</p>
          <button
            @click="alterarSenha"
            :disabled="isSavingSenha || !senha.nova || senha.nova !== senha.confirmar"
            class="bg-brand-primary hover:bg-brand-hover text-white px-6 py-2 rounded-xl font-bold text-sm transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
          >
            <Loader2 v-if="isSavingSenha" class="w-5 h-5 animate-spin" stroke-width="1.5" />
            {{ isSavingSenha ? 'Alterando...' : 'Alterar Senha' }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
