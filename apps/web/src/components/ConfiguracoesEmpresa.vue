<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '../supabase'
import { Building, Upload, Briefcase, Loader2 } from 'lucide-vue-next'

const empresa = ref({
  nome_fantasia: '',
  cnpj: '',
  endereco_completo: '',
  logo_url: ''
})

const isLoading = ref(true)
const isSaving = ref(false)
const uploadProgress = ref(0)

const fetchEmpresa = async () => {
  isLoading.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    const { data, error } = await supabase
      .from('dados_empresa')
      .select('*')
      .eq('usuario_id', user.id)
      .single()

    if (data) {
      empresa.value = { ...data }
    }
  } catch (error) {
    console.error('Erro ao carregar dados da empresa:', error)
  } finally {
    isLoading.value = false
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const fileExt = file.name.split('.').pop()
  const fileName = `logo_${Math.random().toString(36).substring(2)}.${fileExt}`
  const filePath = `logos/${fileName}`

  try {
    uploadProgress.value = 10
    const { error: uploadError } = await supabase.storage
      .from('identidade')
      .upload(filePath, file)

    if (uploadError) throw uploadError

    const { data: { publicUrl } } = supabase.storage
      .from('identidade')
      .getPublicUrl(filePath)

    empresa.value.logo_url = publicUrl
    uploadProgress.value = 100
    setTimeout(() => uploadProgress.value = 0, 2000)
  } catch (error) {
    console.error('Erro no upload da logo:', error)
    alert('Erro ao enviar logo.')
    uploadProgress.value = 0
  }
}

const saveEmpresa = async () => {
  isSaving.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    
    const { error } = await supabase
      .from('dados_empresa')
      .upsert({
        usuario_id: user.id,
        nome_fantasia: empresa.value.nome_fantasia,
        cnpj: empresa.value.cnpj.replace(/\D/g, ''),
        endereco_completo: empresa.value.endereco_completo,
        logo_url: empresa.value.logo_url,
        updated_at: new Date()
      })

    if (error) throw error
    alert('Dados da empresa salvos com sucesso!')
  } catch (error) {
    console.error('Erro ao salvar empresa:', error)
    alert('Erro ao salvar dados.')
  } finally {
    isSaving.value = false
  }
}

onMounted(fetchEmpresa)
</script>

<template>
  <div class="max-w-4xl animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary"></div>
    </div>

    <div v-else class="space-y-6">
      <!-- Company Branding Section -->
      <div class="bg-surface p-6 rounded-2xl border border-hairline flex flex-col sm:flex-row items-center gap-8">
        <div class="relative group">
          <div class="h-32 w-48 rounded-2xl overflow-hidden border-2 border-hairline bg-canvas flex items-center justify-center p-4">
            <img v-if="empresa.logo_url" :src="empresa.logo_url" class="max-h-full max-w-full object-contain" />
            <div v-else class="text-center flex flex-col items-center justify-center">
              <Building class="w-10 h-10 text-ink-muted" stroke-width="1.5" />
              <p class="text-[10px] text-ink-muted mt-1 font-bold uppercase">Logo da Empresa</p>
            </div>
          </div>
          <label class="absolute -bottom-2 -right-2 bg-surface border border-hairline p-2 rounded-xl cursor-pointer hover:bg-canvas transition-colors flex items-center justify-center">
            <Upload class="w-4.5 h-4.5 text-ink-muted" stroke-width="1.5" />
            <input type="file" class="hidden" accept="image/*" @change="handleFileUpload" />
          </label>
        </div>
        
        <div class="flex-1 text-center sm:text-left">
          <h2 class="text-xl font-bold text-ink">{{ empresa.nome_fantasia || 'Nome da Construtora' }}</h2>
          <p class="text-sm text-ink-muted">Esta logo será utilizada nos cabeçalhos dos contratos e relatórios gerados.</p>
          <div v-if="uploadProgress > 0" class="mt-4 w-full max-w-xs bg-canvas rounded-full h-1.5 overflow-hidden">
            <div class="bg-brand-primary h-full transition-all duration-300" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
        </div>
      </div>

      <!-- Company Data Form -->
      <div class="bg-surface rounded-2xl border border-hairline overflow-hidden">
        <div class="px-6 py-4 border-b border-hairline bg-canvas/50">
          <h3 class="text-sm font-bold text-ink flex items-center gap-2">
            <Briefcase class="w-4.5 h-4.5 text-ink" stroke-width="1.5" />
            Dados Jurídicos e Localização
          </h3>
        </div>
        
        <div class="p-6 space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase">Nome Fantasia <span class="text-red-500">*</span></label>
              <input v-model="empresa.nome_fantasia" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="Ex: Alano Engenharia & Construções" required>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase">CNPJ <span class="text-red-500">*</span></label>
              <input v-model="empresa.cnpj" v-maska="'##.###.###/####-##'" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="00.000.000/0001-00" required>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-ink-muted uppercase">Endereço Completo</label>
            <input v-model="empresa.endereco_completo" type="text" class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted" placeholder="Rua, Número, Bairro, Cidade - UF">
          </div>
        </div>

        <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex justify-end">
          <button @click="saveEmpresa" :disabled="isSaving" class="bg-brand-primary hover:bg-brand-hover text-white px-6 py-2 rounded-xl font-bold text-sm transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer">
            <Loader2 v-if="isSaving" class="w-4.5 h-4.5 animate-spin" stroke-width="1.5" />
            {{ isSaving ? 'Salvando...' : 'Salvar Dados da Empresa' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
