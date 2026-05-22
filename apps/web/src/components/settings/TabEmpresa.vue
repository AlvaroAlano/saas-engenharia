<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '../../supabase'
import { useToast } from '../../composables/useToast'

const { showToast } = useToast()
const empresa = ref({ nome_fantasia: '', cnpj: '', endereco_completo: '', logo_url: '' })
const isLoading = ref(true)
const isSaving = ref(false)

const fetchEmpresa = async () => {
  isLoading.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return
    const { data } = await supabase.from('dados_empresa').select('*').eq('usuario_id', user.id).single()
    if (data) empresa.value = { ...data }
  } catch (e) {
    console.error('Erro ao carregar empresa:', e)
  } finally {
    isLoading.value = false
  }
}

const handleLogoUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  const ext = file.name.split('.').pop()
  const filePath = `logos/logo_${Math.random().toString(36).slice(2)}.${ext}`
  const { error } = await supabase.storage.from('identidade').upload(filePath, file)
  if (error) { showToast('Erro ao enviar logo.', 'error'); return }
  const { data: { publicUrl } } = supabase.storage.from('identidade').getPublicUrl(filePath)
  empresa.value.logo_url = publicUrl
  showToast('Logo carregada. Salve para confirmar.', 'info')
}

const saveEmpresa = async () => {
  isSaving.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    const { error } = await supabase.from('dados_empresa').upsert({
      usuario_id: user.id,
      nome_fantasia: empresa.value.nome_fantasia,
      cnpj: (empresa.value.cnpj || '').replace(/\D/g, ''),
      endereco_completo: empresa.value.endereco_completo,
      logo_url: empresa.value.logo_url,
      updated_at: new Date()
    })
    if (error) throw error
    showToast('Dados da empresa salvos!', 'success')
  } catch (e) {
    showToast('Erro ao salvar dados da empresa.', 'error')
  } finally {
    isSaving.value = false
  }
}

onMounted(fetchEmpresa)
</script>

<template>
  <div v-if="isLoading" class="flex justify-center py-16">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary"></div>
  </div>

  <div v-else class="space-y-5">

    <!-- Card: Identidade da Marca -->
    <div class="bg-surface rounded-2xl border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Identidade da Marca</h3>
        <p class="text-xs text-ink-muted mt-0.5">Esta logo aparece nos cabeçalhos de contratos e relatórios gerados.</p>
      </div>
      <div class="px-6 py-5 flex items-center gap-6">
        <div class="relative shrink-0">
          <div class="h-24 w-36 rounded-2xl overflow-hidden border-2 border-hairline bg-canvas flex items-center justify-center p-3">
            <img v-if="empresa.logo_url" :src="empresa.logo_url" class="max-h-full max-w-full object-contain" />
            <div v-else class="text-center">
              <span class="material-symbols-outlined text-3xl text-ink-muted">domain</span>
              <p class="text-[9px] text-ink-muted mt-0.5 font-bold uppercase tracking-wide">Logo</p>
            </div>
          </div>
          <label class="absolute -bottom-1.5 -right-1.5 bg-surface border border-hairline p-1.5 rounded-xl cursor-pointer hover:bg-canvas transition-colors">
            <span class="material-symbols-outlined text-base text-ink-muted">upload_file</span>
            <input type="file" class="hidden" accept="image/*" @change="handleLogoUpload" />
          </label>
        </div>
        <div>
          <p class="text-sm font-semibold text-ink">{{ empresa.nome_fantasia || 'Nome da Construtora' }}</p>
          <p class="text-xs text-ink-muted mt-0.5">Formatos aceitos: PNG, JPG, SVG (recomendado fundo transparente).</p>
        </div>
      </div>
    </div>

    <!-- Card: Dados Jurídicos -->
    <div class="bg-surface rounded-2xl border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Dados Jurídicos e Localização</h3>
        <p class="text-xs text-ink-muted mt-0.5">Informações que constam nos documentos emitidos pela construtora.</p>
      </div>
      <div class="px-6 py-5 space-y-5">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Nome Fantasia <span class="text-red-500">*</span></label>
            <input v-model="empresa.nome_fantasia" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="Alano Engenharia & Construções" />
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">CNPJ <span class="text-red-500">*</span></label>
            <input v-model="empresa.cnpj" v-maska="'##.###.###/####-##'" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="00.000.000/0001-00" />
          </div>
        </div>
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Endereço Completo</label>
          <input v-model="empresa.endereco_completo" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="Rua, Número, Bairro, Cidade - UF" />
        </div>
      </div>
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex justify-end">
        <button @click="saveEmpresa" :disabled="isSaving" class="bg-brand-primary hover:bg-brand-hover text-white px-5 py-2 rounded-xl font-bold text-sm transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer">
          <span v-if="isSaving" class="material-symbols-outlined animate-spin text-base">sync</span>
          {{ isSaving ? 'Salvando...' : 'Salvar Dados da Empresa' }}
        </button>
      </div>
    </div>

  </div>
</template>
