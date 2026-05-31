<script setup>
import { ref, computed, onMounted } from 'vue'
import { supabase } from '../supabase'
import { Building, Upload, Briefcase, Loader2, Globe, Mail, Phone } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'
import { useProfile } from '../composables/useProfile'

const { showToast } = useToast()
const { refreshProfile } = useProfile()

const empresa = ref({
  nome_fantasia: '',
  cnpj: '',
  endereco_completo: '',
  logo_url: '',
  site_url: '',
  email_empresa: '',
  telefone_empresa: ''
})

const isLoading     = ref(true)
const isSaving      = ref(false)
const isUploadingLogo = ref(false)
const uploadProgress  = ref(0)

const fetchEmpresa = async () => {
  isLoading.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    const { data } = await supabase
      .from('dados_empresa')
      .select('*')
      .eq('usuario_id', user.id)
      .single()

    if (data) empresa.value = { ...data }
  } catch (error) {
    console.error('Erro ao carregar dados da empresa:', error)
  } finally {
    isLoading.value = false
  }
}

// ─── Iniciais da empresa como fallback ───────────────────────────────────────
const empresaInitials = computed(() => {
  const name = empresa.value.nome_fantasia?.trim()
  if (!name) return null
  const words = name.split(/\s+/).filter(Boolean)
  return words.length === 1
    ? words[0][0].toUpperCase()
    : (words[0][0] + words[words.length - 1][0]).toUpperCase()
})

// ─── Validação de CNPJ (algoritmo dos dígitos verificadores) ─────────────────
const validarCNPJ = (cnpj) => {
  const d = cnpj.replace(/\D/g, '')
  if (d.length !== 14) return false
  if (/^(\d)\1+$/.test(d)) return false // rejeita sequências iguais (00000000000000)

  const calc = (digits, weights) => {
    const sum = digits.reduce((acc, n, i) => acc + n * weights[i], 0)
    const rem = sum % 11
    return rem < 2 ? 0 : 11 - rem
  }

  const nums = d.split('').map(Number)
  const d1 = calc(nums.slice(0, 12), [5,4,3,2,9,8,7,6,5,4,3,2])
  const d2 = calc(nums.slice(0, 13), [6,5,4,3,2,9,8,7,6,5,4,3,2])
  return nums[12] === d1 && nums[13] === d2
}

const cnpjStatus = computed(() => {
  const digits = empresa.value.cnpj?.replace(/\D/g, '') || ''
  if (!digits) return null          // vazio → sem feedback
  if (digits.length < 14) return 'incompleto'
  return validarCNPJ(digits) ? 'valido' : 'invalido'
})

// ─── Upload da logo — auto-save após upload ───────────────────────────────────
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const ALLOWED = ['image/jpeg', 'image/png', 'image/webp', 'image/svg+xml']
  const MAX_MB  = 5

  if (!ALLOWED.includes(file.type)) {
    showToast('Formato inválido. Use JPG, PNG, WebP ou SVG.', 'error')
    return
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    showToast(`Logo muito grande. Máximo ${MAX_MB} MB.`, 'error')
    return
  }

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return

  const fileExt = file.name.split('.').pop().toLowerCase()
  // Path fixo por usuário — sobrescreve automaticamente a logo anterior
  const filePath = `logos/${user.id}.${fileExt}`

  isUploadingLogo.value = true
  uploadProgress.value  = 10
  try {
    const { error: uploadError } = await supabase.storage
      .from('identidade')
      .upload(filePath, file, { upsert: true })

    if (uploadError) throw uploadError

    uploadProgress.value = 70
    const { data: { publicUrl } } = supabase.storage
      .from('identidade')
      .getPublicUrl(filePath)

    const logoUrl = `${publicUrl}?t=${Date.now()}`
    empresa.value.logo_url = logoUrl

    // Auto-save da logo no banco — não depende do botão principal
    await supabase.from('dados_empresa').upsert({
      usuario_id: user.id,
      logo_url: logoUrl,
      updated_at: new Date()
    })
    await refreshProfile(true)

    uploadProgress.value = 100
    showToast('Logo atualizada!', 'success')
    setTimeout(() => { uploadProgress.value = 0 }, 2000)
  } catch (error) {
    console.error('Erro no upload da logo:', error)
    showToast('Erro ao enviar logo.', 'error')
    uploadProgress.value = 0
  } finally {
    isUploadingLogo.value = false
  }
}

// ─── Save dos dados da empresa ────────────────────────────────────────────────
const saveEmpresa = async () => {
  if (!empresa.value.nome_fantasia?.trim()) {
    showToast('Nome fantasia é obrigatório.', 'error')
    return
  }
  const cnpjDigits = empresa.value.cnpj?.replace(/\D/g, '') || ''
  if (cnpjDigits && !validarCNPJ(cnpjDigits)) {
    showToast('CNPJ inválido. Verifique os dígitos e tente novamente.', 'error')
    return
  }

  isSaving.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()

    const { error } = await supabase
      .from('dados_empresa')
      .upsert({
        usuario_id: user.id,
        nome_fantasia: empresa.value.nome_fantasia.trim(),
        cnpj: cnpjDigits || null,
        endereco_completo: empresa.value.endereco_completo?.trim() || null,
        logo_url: empresa.value.logo_url || null,
        site_url: empresa.value.site_url?.trim() || null,
        email_empresa: empresa.value.email_empresa?.trim() || null,
        telefone_empresa: empresa.value.telefone_empresa?.replace(/\D/g, '') || null,
        updated_at: new Date()
      })

    if (error) throw error
    await refreshProfile(true)
    showToast('Dados da empresa salvos!', 'success')
  } catch (error) {
    console.error('Erro ao salvar empresa:', error)
    showToast('Erro ao salvar dados.', 'error')
  } finally {
    isSaving.value = false
  }
}

onMounted(fetchEmpresa)
</script>

<template>
  <div class="max-w-4xl animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div v-if="isLoading" class="flex justify-center py-12">
      <Loader2 class="w-8 h-8 animate-spin text-brand-primary" stroke-width="1.5" />
    </div>

    <div v-else class="space-y-6">

      <!-- ── Card: Logo / Identidade Visual ────────────────────────── -->
      <div class="bg-surface rounded-2xl border border-hairline overflow-hidden">
        <div class="p-6 flex flex-col sm:flex-row items-center sm:items-start gap-6">

          <!-- Preview da logo -->
          <div class="relative shrink-0">
            <div class="h-28 w-44 rounded-xl overflow-hidden border-2 border-hairline bg-canvas flex items-center justify-center p-3">
              <img v-if="empresa.logo_url" :src="empresa.logo_url" class="max-h-full max-w-full object-contain" />
              <div v-else-if="empresaInitials" class="h-full w-full bg-brand-blue flex items-center justify-center rounded-lg">
                <span class="text-3xl font-black text-white tracking-tight select-none">{{ empresaInitials }}</span>
              </div>
              <div v-else class="flex flex-col items-center justify-center gap-1">
                <Building class="w-9 h-9 text-ink-muted" stroke-width="1.5" />
                <p class="text-[10px] text-ink-muted font-bold uppercase tracking-wider">Logo</p>
              </div>
            </div>

            <!-- Botão upload -->
            <label
              class="absolute -bottom-2 -right-2 bg-surface border border-hairline p-2 rounded-xl cursor-pointer hover:bg-canvas transition-colors flex items-center justify-center shadow-sm"
              :class="isUploadingLogo ? 'pointer-events-none' : ''"
              title="Enviar logo"
            >
              <Loader2 v-if="isUploadingLogo" class="w-4 h-4 animate-spin text-brand-primary" stroke-width="1.5" />
              <Upload v-else class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
              <input type="file" class="hidden" accept="image/jpeg,image/png,image/webp,image/svg+xml" @change="handleFileUpload" :disabled="isUploadingLogo" />
            </label>
          </div>

          <!-- Info + progress -->
          <div class="flex-1 min-w-0 text-center sm:text-left">
            <h2 class="text-xl font-bold text-ink">{{ empresa.nome_fantasia || 'Nome da Construtora' }}</h2>
            <p class="text-sm text-ink-muted mt-1">Esta logo aparece no cabeçalho dos contratos e relatórios gerados.</p>
            <p class="text-xs text-ink-muted mt-2">Formatos aceitos: JPG, PNG, WebP, SVG · Máximo 5 MB</p>

            <div v-if="uploadProgress > 0" class="mt-3 w-full bg-canvas rounded-full h-1.5 overflow-hidden border border-hairline">
              <div class="bg-brand-blue h-full transition-all duration-300" :style="{ width: `${uploadProgress}%` }" />
            </div>
          </div>
        </div>
      </div>

      <!-- ── Card: Dados Jurídicos ───────────────────────────────────── -->
      <div class="bg-surface rounded-2xl border border-hairline overflow-hidden">
        <div class="px-6 py-4 border-b border-hairline bg-canvas/50">
          <h3 class="text-sm font-bold text-ink flex items-center gap-2">
            <Briefcase class="w-5 h-5 text-ink" stroke-width="1.5" />
            Dados Jurídicos e Localização
          </h3>
        </div>

        <div class="p-6 space-y-6">

          <!-- Linha 1: Nome Fantasia + CNPJ -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase">Nome Fantasia <span class="text-red-500">*</span></label>
              <input
                v-model="empresa.nome_fantasia"
                type="text"
                placeholder="Ex: Alano Engenharia & Construções"
                class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
              />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase">CNPJ</label>
              <input
                v-model="empresa.cnpj"
                v-maska="'##.###.###/####-##'"
                type="text"
                placeholder="00.000.000/0001-00"
                class="w-full bg-canvas border text-ink rounded-xl px-4 py-2.5 text-sm outline-none transition-all placeholder:text-ink-muted focus:ring-1"
                :class="cnpjStatus === 'invalido'
                  ? 'border-red-400 focus:ring-red-400 focus:border-red-400'
                  : cnpjStatus === 'valido'
                    ? 'border-semantic-success focus:ring-semantic-success focus:border-semantic-success'
                    : 'border-hairline focus:ring-brand-primary focus:border-brand-primary'"
              />
              <p v-if="cnpjStatus === 'invalido'" class="text-xs text-red-500 font-medium">CNPJ inválido — verifique os dígitos.</p>
              <p v-else-if="cnpjStatus === 'valido'" class="text-xs text-semantic-success font-medium">CNPJ válido ✓</p>
            </div>
          </div>

          <!-- Linha 2: Endereço (largura total) -->
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Endereço Completo</label>
            <input
              v-model="empresa.endereco_completo"
              type="text"
              placeholder="Rua, Número, Bairro, Cidade - UF"
              class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
            />
          </div>

          <!-- Linha 3: Contato da Empresa -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase flex items-center gap-1.5">
                <Globe class="w-3.5 h-3.5" stroke-width="2" /> Site
              </label>
              <input
                v-model="empresa.site_url"
                type="url"
                placeholder="https://suaempresa.com.br"
                class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
              />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase flex items-center gap-1.5">
                <Mail class="w-3.5 h-3.5" stroke-width="2" /> E-mail da Empresa
              </label>
              <input
                v-model="empresa.email_empresa"
                type="email"
                placeholder="contato@suaempresa.com.br"
                class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
              />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase flex items-center gap-1.5">
                <Phone class="w-3.5 h-3.5" stroke-width="2" /> Telefone Comercial
              </label>
              <input
                v-model="empresa.telefone_empresa"
                v-maska="'(##) #####-####'"
                type="text"
                placeholder="(48) 99999-9999"
                class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
              />
            </div>
          </div>

        </div>

        <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex items-center justify-between gap-4">
          <p class="text-xs text-ink-muted hidden sm:block">Nome fantasia é obrigatório. Estes dados aparecem nos contratos gerados.</p>
          <button @click="saveEmpresa" :disabled="isSaving" class="bg-brand-primary hover:bg-brand-hover text-white px-6 py-2 rounded-xl font-bold text-sm transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer shrink-0">
            <Loader2 v-if="isSaving" class="w-5 h-5 animate-spin" stroke-width="1.5" />
            {{ isSaving ? 'Salvando...' : 'Salvar Dados da Empresa' }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
