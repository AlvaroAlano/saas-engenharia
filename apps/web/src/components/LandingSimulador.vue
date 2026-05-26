<template>
  <div class="min-h-screen bg-canvas text-ink font-sans antialiased overflow-x-hidden selection:bg-brand-primary/30 selection:text-white transition-colors duration-200">
    <!-- HEADER -->
    <header class="sticky top-0 z-50 w-full h-[56px] bg-surface/80 backdrop-blur-md border-b border-hairline transition-all duration-300 flex items-center">
      <div class="w-full max-w-[1280px] mx-auto px-6 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-brand-primary/10 rounded-md border border-brand-primary/30 flex items-center justify-center">
            <Layers class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
          </div>
          <span class="text-[18px] font-semibold text-ink tracking-[-0.4px]">Vértice</span>
          <span class="text-[10px] bg-canvas border border-hairline text-ink-muted px-2 py-0.5 rounded-full font-mono font-medium">B2C</span>
        </div>
        
        <div class="flex items-center gap-4">
          <!-- Theme Toggle -->
          <button 
            @click="toggleTheme" 
            class="p-2 text-ink-muted hover:text-ink hover:bg-surface-hover rounded-md transition-all cursor-pointer flex items-center justify-center focus:outline-none"
            title="Alternar Tema"
          >
            <Sun v-if="isDark" class="w-5 h-5" stroke-width="1.5" />
            <Moon v-else class="w-5 h-5" stroke-width="1.5" />
          </button>

          <!-- Back to home/B2B portal link -->
          <router-link 
            to="/" 
            class="inline-flex items-center justify-center bg-surface hover:bg-surface-hover text-ink border border-hairline rounded-md text-[13px] font-medium px-4 py-2 transition-all duration-200 cursor-pointer"
          >
            Área do Construtor
          </router-link>
        </div>
      </div>
    </header>

    <!-- MAIN BODY -->
    <main class="w-full max-w-[1280px] mx-auto px-6 py-12 md:py-20 flex flex-col lg:flex-row gap-12 items-center relative min-h-[calc(100vh-56px)]">
      <!-- Glow -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] md:w-[800px] md:h-[800px] bg-brand-primary/4 rounded-full blur-[140px] pointer-events-none z-0"></div>

      <!-- Left Column: Copy -->
      <div class="flex-1 text-left flex flex-col gap-6 relative z-10">
        <div class="inline-flex items-center gap-2 px-3 py-1 bg-surface border border-hairline rounded-full self-start">
          <span class="w-1.5 h-1.5 bg-brand-primary rounded-full"></span>
          <span class="text-[11px] font-bold text-ink-muted uppercase tracking-wider">Cálculo Rápido de Obra</span>
        </div>
        
        <h1 class="text-4xl md:text-5xl lg:text-6xl font-semibold text-ink leading-[1.08] tracking-[-1.5px] md:tracking-[-2.5px]">
          Descubra o custo estimado da sua obra em 60 segundos
        </h1>

        <p class="text-base md:text-lg text-ink-muted leading-relaxed max-w-xl">
          Simule o valor total de construção e financiamento da sua casa baseado das tabelas de referência SINAPI e CUB da sua região. Sem formulários complexos e 100% gratuito.
        </p>

        <!-- Bullet Highlights -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          <div class="flex items-center gap-3">
            <CheckCircle2 class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
            <span class="text-sm text-ink-muted font-medium">Dados atualizados do CUB por UF</span>
          </div>
          <div class="flex items-center gap-3">
            <CheckCircle2 class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
            <span class="text-sm text-ink-muted font-medium">Margem de financiamento da Caixa</span>
          </div>
          <div class="flex items-center gap-3">
            <CheckCircle2 class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
            <span class="text-sm text-ink-muted font-medium">Sem necessidade de cadastro prévio</span>
          </div>
          <div class="flex items-center gap-3">
            <CheckCircle2 class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
            <span class="text-sm text-ink-muted font-medium">Conecte-se com engenheiros locais</span>
          </div>
        </div>
      </div>

      <!-- Right Column: Interactive Card -->
      <div class="w-full max-w-lg lg:w-[480px] relative z-10 shrink-0">
        <div class="bg-surface border border-hairline rounded-xl p-6 md:p-8 flex flex-col gap-6 text-left">
          <h2 class="text-lg font-bold text-ink tracking-tight">Simulação Paramétrica</h2>
          
          <form @submit.prevent="calcularEstimativa" class="flex flex-col gap-5">
            <!-- UF Select -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">Estado (UF da Obra)</label>
              <div class="relative">
                <select 
                  v-model="form.uf" 
                  required
                  class="w-full bg-canvas border border-hairline rounded-md px-3 py-2.5 text-sm text-ink focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/50 appearance-none cursor-pointer transition-all"
                >
                  <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
                </select>
                <ChevronDown class="w-[18px] h-[18px] absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-[#8a8f98] pointer-events-none" stroke-width="1.5" />
              </div>
            </div>

            <!-- Metragem Input -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">Área Estimada (m²)</label>
              <div class="relative">
                <input 
                  type="number" 
                  v-model.number="form.metragem" 
                  min="30" 
                  max="10000" 
                  required
                  class="w-full bg-canvas border border-hairline text-ink rounded-md py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/50 transition-all font-mono"
                  placeholder="Ex: 120"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-ink-muted font-mono pointer-events-none">m²</span>
              </div>
            </div>

            <!-- Padrao Radio-like Choice -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-bold text-ink-muted uppercase tracking-wider">Padrão de Acabamento</label>
              <div class="grid grid-cols-3 bg-canvas p-1 rounded-md border border-hairline gap-1">
                <button 
                  type="button"
                  @click="form.padrao = 'baixo'"
                  :class="form.padrao === 'baixo' ? 'bg-[#5e6ad2] text-white font-semibold' : 'bg-surface hover:bg-surface-hover text-ink-muted'"
                  class="py-2 text-xs font-medium rounded-md transition-all cursor-pointer border border-transparent"
                >
                  Popular
                </button>
                <button 
                  type="button"
                  @click="form.padrao = 'medio'"
                  :class="form.padrao === 'medio' ? 'bg-[#5e6ad2] text-white font-semibold' : 'bg-surface hover:bg-surface-hover text-ink-muted'"
                  class="py-2 text-xs font-medium rounded-md transition-all cursor-pointer border border-transparent"
                >
                  Médio
                </button>
                <button 
                  type="button"
                  @click="form.padrao = 'alto'"
                  :class="form.padrao === 'alto' ? 'bg-[#5e6ad2] text-white font-semibold' : 'bg-surface hover:bg-surface-hover text-ink-muted'"
                  class="py-2 text-xs font-medium rounded-md transition-all cursor-pointer border border-transparent"
                >
                  Alto
                </button>
              </div>
            </div>

            <!-- Submit button -->
            <button 
              type="submit" 
              :disabled="loading"
              class="w-full bg-[#5e6ad2] hover:bg-[#828fff] text-white py-3 rounded-md text-sm font-semibold transition-all cursor-pointer flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-50"
            >
              <Loader2 v-if="loading" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
              <Calculator v-else class="w-[18px] h-[18px]" stroke-width="1.5" />
              {{ loading ? 'Calculando estimativa...' : 'Calcular Custo Estimado' }}
            </button>
          </form>

          <!-- Error Alert -->
          <div v-if="error" class="bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/20 p-3 rounded-md text-xs">
            {{ error }}
          </div>

          <!-- Calculated Results Block -->
          <div v-if="resultado" class="border-t border-hairline pt-6 flex flex-col gap-5">
            <div class="flex justify-between items-end">
              <div>
                <span class="text-xs text-ink-muted uppercase block font-semibold">Custo Estimado da Obra</span>
                <span class="text-2xl md:text-3xl font-black text-ink tracking-tight font-mono">
                  {{ formatCurrency(resultado.valor_estimado) }}
                </span>
              </div>
              <div class="text-right">
                <span class="text-[10px] text-ink-muted uppercase block font-semibold">Preço Médio / m²</span>
                <span class="text-xs font-bold text-ink font-mono">
                  {{ formatCurrency(resultado.custo_m2) }}/m²
                </span>
              </div>
            </div>

            <!-- Detail info card -->
            <div class="bg-canvas border border-hairline rounded-lg p-3 text-xs flex flex-col gap-2">
              <div class="flex items-center justify-between text-ink-muted">
                <span>Financiamento Caixa Sugerido (80%):</span>
                <span class="font-bold text-ink font-mono">{{ formatCurrency(resultado.margem_financiamento) }}</span>
              </div>
              <div class="flex items-center justify-between text-ink-muted">
                <span>Aporte Próprio Necessário (20%):</span>
                <span class="font-bold text-ink font-mono">{{ formatCurrency(resultado.valor_estimado * 0.20) }}</span>
              </div>
            </div>

            <!-- Next CTA Action: Go to wizard -->
            <button 
              @click="irParaWizard"
              class="w-full bg-[#27a644] hover:bg-[#2ecc71] text-white py-3 rounded-md text-sm font-semibold transition-all cursor-pointer flex items-center justify-center gap-2 active:scale-[0.98]"
            >
              <span>Personalizar & Encontrar Engenheiro</span>
              <ArrowRight class="w-[18px] h-[18px]" stroke-width="1.5" />
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { isDark, toggleTheme } from '../composables/useTheme'
import { Layers, Sun, Moon, CheckCircle2, ChevronDown, Loader2, Calculator, ArrowRight } from 'lucide-vue-next'

const router = useRouter()

const ufs = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
  "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
  "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]

const form = reactive({
  uf: 'SC',
  metragem: 120,
  padrao: 'medio'
})

const loading = ref(false)
const resultado = ref(null)
const error = ref(null)

const calcularEstimativa = async () => {
  loading.value = true
  resultado.value = null
  error.value = null
  
  try {
    const payload = {
      padrao: form.padrao,
      metragem: parseFloat(form.metragem),
      uf: form.uf
    }
    const response = await axios.post('/simulador/calcular', payload)
    resultado.value = response.data
  } catch (err) {
    console.error("Erro ao calcular estimativa:", err)
    error.value = err.response?.data?.detail || "Ocorreu um erro ao calcular os custos. Verifique a conexão."
  } finally {
    loading.value = false
  }
}

const formatCurrency = (val) => {
  if (val === null || val === undefined || isNaN(val)) return 'R$ 0,00'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)
}

const irParaWizard = () => {
  router.push({
    path: '/estimativa/nova',
    query: {
      uf: form.uf,
      padrao: form.padrao,
      metragem: form.metragem
    }
  })
}
</script>

<style scoped>
/* Remove spin-buttons for number inputs */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
</style>
