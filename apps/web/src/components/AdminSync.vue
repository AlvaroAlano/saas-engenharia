<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { 
  Loader2, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  Upload, 
  Database, 
  Clock, 
  Network, 
  CalendarRange, 
  Play 
} from 'lucide-vue-next'

// --- Tabs Control ---
const activeTab = ref('insumos')

// --- Estado: Insumos ---
const mesAno = ref('03/2026')
const desonerado = ref(false)
const file = ref(null)
const isUploading = ref(false)
const alertMessage = ref('')
const alertType = ref('')

const handleFileChange = (e) => {
  if (e.target.files.length > 0) {
    file.value = e.target.files[0]
  }
}

const syncSinapi = async () => {
    if (!file.value) {
      alertType.value = 'error'
      alertMessage.value = 'Por favor, selecione um arquivo Excel.'
      return
    }
    isUploading.value = true
    alertMessage.value = ''
    alertType.value = ''

    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('mes_ano', mesAno.value)
    formData.append('desonerado', desonerado.value)

    try {
      const response = await axios.post('/admin/sync-sinapi', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      if (response.data.success) {
        alertType.value = 'success'
        alertMessage.value = response.data.message
        file.value = null
      } else {
        alertType.value = 'error'
        alertMessage.value = response.data.message || 'Erro ao sincronizar banco de dados.'
      }
    } catch (error) {
      console.error('Erro na sincronização:', error)
      alertType.value = 'error'
      alertMessage.value = 'Ocorreu um erro de comunicação com o servidor.'
    } finally {
      isUploading.value = false
    }
}

// --- Estado: Composições (Analítico) ---
const fileComp = ref(null)
const isScheduled = ref(false)
const activationDate = ref('')
const isLoadingComp = ref(false)
const alertMessageComp = ref('')
const alertTypeComp = ref('')

const handleFileCompChange = (e) => {
  if (e.target.files.length > 0) {
    fileComp.value = e.target.files[0]
  }
}

const uploadComposicoes = async () => {
    if (!fileComp.value) {
      alertTypeComp.value = 'error'
      alertMessageComp.value = 'Por favor, selecione um arquivo Excel Analítico.'
      return
    }

    if (isScheduled.value && !activationDate.value) {
      alertTypeComp.value = 'error'
      alertMessageComp.value = 'Por favor, selecione uma data e hora para o agendamento.'
      return
    }

    isLoadingComp.value = true
    alertMessageComp.value = ''
    alertTypeComp.value = ''

    const formData = new FormData()
    formData.append('file', fileComp.value)
    
    if (isScheduled.value) {
      const dateObj = new Date(activationDate.value)
      formData.append('data_ativacao', dateObj.toISOString())
    }

    try {
      const response = await axios.post('/admin/sync-composicoes', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (response.data.success) {
        alertTypeComp.value = 'success'
        if (isScheduled.value) {
          alertMessageComp.value = response.data.message
        } else {
          alertMessageComp.value = `Sucesso: ${response.data.total_maes} Mães e ${response.data.total_filhos} Filhos inseridos.`
        }
        fileComp.value = null
        isScheduled.value = false
        activationDate.value = ''
      } else {
        alertTypeComp.value = 'error'
        alertMessageComp.value = response.data.message || 'Erro ao sincronizar composições.'
      }
    } catch (error) {
      console.error('Erro na sincronização:', error)
      alertTypeComp.value = 'error'
      alertMessageComp.value = 'Ocorreu um erro de comunicação com o servidor.'
    } finally {
      isLoadingComp.value = false
    }
}
</script>

<template>
  <div class="min-h-screen bg-canvas flex flex-col items-center p-8 font-sans text-ink">
    <div class="w-full max-w-2xl bg-surface rounded-2xl overflow-hidden border border-hairline relative mt-10">
      
      <!-- Overlay de Loading (Bloqueio de Tela) -->
      <div v-if="isLoadingComp || isUploading" class="absolute inset-0 z-50 bg-surface/60 dark:bg-zinc-950/80 backdrop-blur-sm flex flex-col items-center justify-center">
        <Loader2 class="w-12 h-12 text-brand-primary animate-spin mb-4" stroke-width="1.5" />
        <h3 class="text-xl font-bold text-ink">Processando dados da Caixa...</h3>
        <p class="text-ink-muted mt-2 font-medium">Isso pode levar alguns minutos. Por favor, aguarde.</p>
      </div>

      <div class="bg-zinc-950 px-8 py-6 border-b border-hairline">
        <h2 class="text-2xl font-bold text-white flex items-center gap-3">
          <RefreshCw class="w-6 h-6 text-brand-primary" stroke-width="1.5" />
          Central de Sincronização
        </h2>
        <p class="text-zinc-400 text-sm mt-2">Faça o upload dos catálogos da SINAPI para atualizar o motor de dados do sistema.</p>
      </div>

      <!-- Tabs Navigation -->
      <div class="flex border-b border-hairline bg-canvas">
        <button 
          @click="activeTab = 'insumos'" 
          :class="activeTab === 'insumos' ? 'text-brand-primary border-b-2 border-brand-primary font-bold bg-surface' : 'text-ink-muted hover:text-ink font-medium'"
          class="flex-1 py-4 px-6 transition-all outline-none flex flex-col items-center justify-center cursor-pointer"
        >
          <span class="text-xs font-bold tracking-wider uppercase mb-1 opacity-70">Step 1</span>
          <span>Insumos Básicos</span>
        </button>
        <button 
          @click="activeTab = 'composicoes'" 
          :class="activeTab === 'composicoes' ? 'text-brand-primary border-b-2 border-brand-primary font-bold bg-surface' : 'text-ink-muted hover:text-ink font-medium'"
          class="flex-1 py-4 px-6 transition-all outline-none flex flex-col items-center justify-center cursor-pointer"
        >
          <span class="text-xs font-bold tracking-wider uppercase mb-1 opacity-70">Step 2</span>
          <div class="flex items-center gap-2">
            <span>Composições (Analítico)</span>
            <span class="bg-brand-primary/10 text-brand-primary text-[10px] font-bold px-2 py-0.5 rounded-full border border-brand-primary/20">Novo</span>
          </div>
        </button>
      </div>

      <!-- Aba: INSUMOS -->
      <div v-if="activeTab === 'insumos'" class="p-8">
        <div v-if="alertMessage" :class="alertType === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'" class="mb-6 p-4 rounded-lg border text-sm font-medium flex items-center gap-2">
          <CheckCircle2 v-if="alertType === 'success'" class="w-5 h-5 text-emerald-600 shrink-0" stroke-width="1.5" />
          <AlertTriangle v-else class="w-5 h-5 text-red-600 shrink-0" stroke-width="1.5" />
          {{ alertMessage }}
        </div>

        <form @submit.prevent="syncSinapi" class="space-y-6">
          <div>
            <label class="block text-sm font-semibold text-ink mb-2">Mês/Ano de Referência</label>
            <input v-model="mesAno" type="text" placeholder="Ex: 03/2026" class="w-full px-4 py-3 bg-canvas border border-hairline text-ink rounded-lg focus:ring-1 focus:ring-brand-primary outline-none font-medium transition-colors" required />
          </div>

          <div class="flex items-center justify-between">
            <div>
              <label class="block text-sm font-semibold text-ink">Tabela Desonerada?</label>
              <p class="text-xs text-ink-muted mt-0.5">Selecione se os preços já possuem desoneração da folha.</p>
            </div>
            <button type="button" @click="desonerado = !desonerado" :class="desonerado ? 'bg-brand-primary' : 'bg-canvas'" class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none border border-hairline cursor-pointer">
              <span :class="desonerado ? 'translate-x-6' : 'translate-x-1'" class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" />
            </button>
          </div>

          <div>
            <label class="block text-sm font-semibold text-ink mb-2">Arquivo de Insumos (.xlsx)</label>
            <div class="mt-1 flex justify-center rounded-xl border border-dashed border-hairline px-6 py-10 hover:border-brand-primary hover:bg-brand-primary/5 transition-colors group relative cursor-pointer bg-canvas">
              <div class="text-center">
                <Upload class="w-10 h-10 text-ink-muted group-hover:text-brand-primary mb-2 mx-auto" stroke-width="1.5" />
                <div class="mt-2 flex text-sm text-ink-muted justify-center">
                  <label class="relative cursor-pointer font-semibold text-brand-primary hover:text-brand-hover">
                    <span>Selecione um arquivo</span>
                    <input type="file" accept=".xlsx, .xls" class="sr-only" @change="handleFileChange" required>
                  </label>
                  <p class="pl-1">ou arraste e solte</p>
                </div>
                <p class="text-sm font-bold text-brand-primary mt-2 truncate max-w-xs mx-auto" v-if="file">{{ file.name }}</p>
              </div>
            </div>
          </div>

          <button type="submit" class="w-full flex justify-center items-center gap-2 rounded-lg bg-brand-primary px-4 py-3 text-sm font-semibold text-white hover:bg-brand-hover transition-all disabled:opacity-50 border border-transparent cursor-pointer">
            <Database class="w-4 h-4" stroke-width="1.5" />
            Sincronizar Insumos
          </button>
        </form>
      </div>

      <!-- Aba: COMPOSIÇÕES -->
      <div v-if="activeTab === 'composicoes'" class="p-8">
        <div v-if="alertMessageComp" :class="alertTypeComp === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'" class="mb-6 p-4 rounded-lg border text-sm font-medium flex gap-2 items-start">
          <CheckCircle2 v-if="alertTypeComp === 'success'" class="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" stroke-width="1.5" />
          <AlertTriangle v-else class="w-5 h-5 text-red-600 mt-0.5 shrink-0" stroke-width="1.5" />
          <span class="flex-1">{{ alertMessageComp }}</span>
        </div>

        <form @submit.prevent="uploadComposicoes" class="space-y-6">
          
          <!-- Seção de Agendamento -->
          <div class="bg-canvas border border-hairline rounded-xl p-5">
            <div class="flex items-center justify-between">
              <div>
                <label class="block text-sm font-semibold text-ink flex items-center gap-2">
                  <Clock class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                  Processamento Agendado
                </label>
                <p class="text-xs text-ink-muted mt-1 pr-4 leading-relaxed">Adie a sincronização (carga pesada no servidor) para o futuro, ideal para rodar durante a madrugada.</p>
              </div>
              <button type="button" @click="isScheduled = !isScheduled" :class="isScheduled ? 'bg-brand-primary' : 'bg-canvas'" class="relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none border border-hairline cursor-pointer">
                <span :class="isScheduled ? 'translate-x-6' : 'translate-x-1'" class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" />
              </button>
            </div>
            
            <div v-if="isScheduled" class="mt-4 pt-4 border-t border-hairline animate-fade-in">
              <label class="block text-sm font-semibold text-ink mb-2">Data e Hora de Ativação</label>
              <input v-model="activationDate" type="datetime-local" class="w-full px-4 py-3 bg-surface border border-hairline text-ink rounded-lg focus:ring-1 focus:ring-brand-primary outline-none font-medium transition-all" required />
            </div>
          </div>

          <!-- File Upload -->
          <div>
            <label class="block text-sm font-semibold text-ink mb-2">Arquivo Analítico (.xlsx)</label>
            <div class="mt-1 flex justify-center rounded-xl border border-dashed border-hairline px-6 py-10 hover:border-brand-primary hover:bg-brand-primary/5 transition-colors group relative cursor-pointer bg-canvas/30">
              <div class="text-center">
                <Network class="w-10 h-10 text-ink-muted group-hover:text-brand-primary mb-2 mx-auto" stroke-width="1.5" />
                <div class="mt-2 flex text-sm text-ink-muted justify-center">
                  <label class="relative cursor-pointer font-semibold text-brand-primary hover:text-brand-hover">
                    <span>Selecione o Relatório Analítico</span>
                    <input type="file" accept=".xlsx, .xls" class="sr-only" @change="handleFileCompChange" required>
                  </label>
                </div>
                <p class="text-xs text-ink-muted mt-2 font-medium" v-if="!fileComp">O arquivo deve possuir a aba 'Analítico'.</p>
                <p class="text-sm font-bold text-brand-primary mt-2 truncate max-w-xs mx-auto bg-brand-primary/10 rounded-md px-2 py-1" v-else>{{ fileComp.name }}</p>
              </div>
            </div>
          </div>

          <button type="submit" class="w-full flex justify-center items-center gap-2 rounded-lg px-4 py-3 text-sm font-semibold text-white transition-all border border-transparent bg-brand-primary hover:bg-brand-hover disabled:opacity-50 cursor-pointer">
            <CalendarRange v-if="isScheduled" class="w-4 h-4" stroke-width="1.5" />
            <Play v-else class="w-4 h-4" stroke-width="1.5" />
            {{ isScheduled ? 'Agendar Sincronização' : 'Sincronizar Composições Agora' }}
          </button>
        </form>
      </div>

    </div>
  </div>
</template>

<style>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
