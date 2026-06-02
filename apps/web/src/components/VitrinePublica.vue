<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { Frown, User, MapPin, Image, Calculator, ChevronDown, Loader2, AlertTriangle, Handshake, Star } from 'lucide-vue-next'
import VerticeLogo from './VerticeLogo.vue'
import { ENGENHEIROS_MOCK } from '../data/mockEngenheiros'

const route = useRoute()
const router = useRouter()

const engenheiro = ref(null)
const isLoading = ref(true)
const notFound = ref(false)

// Simulador
const form = reactive({ uf: 'SC', metragem: 120, padrao: 'medio' })
const loadingCalculo = ref(false)
const resultado = ref(null)
const erroCalculo = ref(null)

// Solicitação
const contato = reactive({ nome: '', telefone: '' })
const loadingSolicitar = ref(false)
const erroSolicitar = ref(null)

const ufs = [
  'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA',
  'MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN',
  'RO','RR','RS','SC','SE','SP','TO'
]

const padroes = [
  { value: 'baixo', label: 'Popular' },
  { value: 'medio', label: 'Médio' },
  { value: 'alto', label: 'Alto' }
]

const fotoPrincipal = ref(0)

const fetchEngenheiro = async () => {
  try {
    const { data } = await axios.get(`/api/vitrine/${route.params.slug}`)
    engenheiro.value = data
    if (data.cidades_atuacao?.length) {
      const primeiraUF = data.cidades_atuacao[0].match(/\b([A-Z]{2})\b/)
      if (primeiraUF) form.uf = primeiraUF[1]
    }
  } catch (e) {
    if (e.response?.status === 404) {
      const mock = ENGENHEIROS_MOCK.find(m => m.slug === route.params.slug)
      if (mock) {
        engenheiro.value = mock
        if (mock.cidades_atuacao?.length) {
          const primeiraUF = mock.cidades_atuacao[0].match(/\b([A-Z]{2})\b/)
          if (primeiraUF) form.uf = primeiraUF[1]
        }
      } else {
        notFound.value = true
      }
    } else {
      console.error('Erro ao carregar vitrine:', e)
    }
  } finally {
    isLoading.value = false
  }
}

const calcular = async () => {
  loadingCalculo.value = true
  resultado.value = null
  erroCalculo.value = null
  try {
    const { data } = await axios.post('/simulador/calcular', {
      padrao: form.padrao,
      metragem: parseFloat(form.metragem),
      uf: form.uf
    })
    resultado.value = data
  } catch (e) {
    erroCalculo.value = e.response?.data?.detail || 'Erro ao calcular. Tente novamente.'
  } finally {
    loadingCalculo.value = false
  }
}

const formatCurrency = (val) => {
  if (!val && val !== 0) return 'R$ –'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)
}

const solicitarOrcamento = async () => {
  if (!contato.nome.trim()) { erroSolicitar.value = 'Informe seu nome.'; return }
  if (!contato.telefone.trim() || contato.telefone.replace(/\D/g, '').length < 10) {
    erroSolicitar.value = 'Informe um WhatsApp válido (com DDD).'; return
  }
  erroSolicitar.value = null
  loadingSolicitar.value = true
  try {
    const { data } = await axios.post('/matchmaking/solicitar', {
      usuario_id: engenheiro.value.id,
      cliente_nome: contato.nome.trim(),
      telefone: contato.telefone.trim(),
      valor: resultado.value.valor_estimado,
      padrao: padroes.find(p => p.value === form.padrao)?.label || form.padrao,
      tamanho: `${form.metragem}m²`,
      uf_obra: form.uf
    })
    if (data.success && data.projeto_id) {
      router.push(`/estimativa/${data.projeto_id}`)
    } else {
      erroSolicitar.value = 'Erro ao enviar solicitação. Tente novamente.'
    }
  } catch (e) {
    erroSolicitar.value = e.response?.data?.detail || 'Erro ao enviar. Tente novamente.'
  } finally {
    loadingSolicitar.value = false
  }
}

const nomeAbreviado = computed(() => {
  const nome = engenheiro.value?.nome_completo || ''
  const partes = nome.split(' ')
  return partes.length > 1 ? `${partes[0]} ${partes[partes.length - 1]}` : nome
})

onMounted(fetchEngenheiro)
</script>

<template>
  <div class="min-h-screen bg-canvas text-ink font-sans antialiased overflow-x-hidden">

    <!-- Header -->
    <header class="sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-hairline h-14 flex items-center px-6">
      <div class="w-full max-w-4xl mx-auto flex items-center justify-between">
        <VerticeLogo class="h-[28px] text-logo" />
        <router-link to="/" class="text-xs text-ink-muted hover:text-ink transition-colors">
          Área do Construtor →
        </router-link>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-[60vh]">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-primary"></div>
    </div>

    <!-- Not Found -->
    <div v-else-if="notFound" class="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center px-6">
      <Frown class="w-12 h-12 text-ink-muted" stroke-width="1.5" />
      <h1 class="text-xl font-bold text-ink">Perfil não encontrado</h1>
      <p class="text-sm text-ink-muted max-w-xs">O endereço <span class="font-mono text-brand-primary">/p/{{ route.params.slug }}</span> não existe ou ainda não foi configurado pelo engenheiro.</p>
      <router-link to="/simulador" class="mt-2 text-sm text-brand-primary hover:underline">Encontre um engenheiro na sua região →</router-link>
    </div>

    <!-- Conteúdo da Vitrine -->
    <div v-else class="w-full max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-10">

      <!-- Hero: Perfil do Engenheiro -->
      <section class="flex flex-col sm:flex-row gap-6 items-start">
        <!-- Foto -->
        <div class="shrink-0">
          <div class="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl overflow-hidden border-2 border-hairline bg-surface flex items-center justify-center">
            <img v-if="engenheiro.foto_perfil" :src="engenheiro.foto_perfil" class="w-full h-full object-cover" />
            <User v-else class="w-10 h-10 text-ink-muted" stroke-width="1.5" />
          </div>
        </div>

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <div class="flex flex-wrap items-center gap-2 mb-1">
            <h1 class="text-2xl sm:text-3xl font-bold text-ink tracking-tight">{{ engenheiro.nome_completo }}</h1>
            <span class="text-xs bg-brand-primary/10 text-brand-primary border border-brand-primary/20 px-2 py-0.5 rounded-full font-semibold">Verificado</span>
          </div>
          <p v-if="engenheiro.registro_crea_cau" class="text-sm text-ink-muted font-mono mb-2">{{ engenheiro.registro_crea_cau }}</p>
          <div v-if="engenheiro.cidades_atuacao?.length" class="flex flex-wrap gap-1.5 mb-3">
            <span
              v-for="cidade in engenheiro.cidades_atuacao"
              :key="cidade"
              class="flex items-center gap-1 text-xs text-ink-muted bg-surface border border-hairline px-2 py-1 rounded-lg"
            >
              <MapPin class="w-3 h-3 text-ink-muted" stroke-width="1.5" />
              {{ cidade }}
            </span>
          </div>
          <p v-if="engenheiro.descricao_vitrine" class="text-sm text-ink leading-relaxed">{{ engenheiro.descricao_vitrine }}</p>
        </div>
      </section>

      <!-- Galeria de Portfólio -->
      <section v-if="engenheiro.fotos_portfolio?.length">
        <h2 class="text-xs font-bold text-ink-muted uppercase tracking-wider mb-4 flex items-center gap-1.5">
          <Image class="w-3.5 h-3.5" stroke-width="1.5" />
          Portfólio de Obras
        </h2>
        <!-- Foto em destaque -->
        <div class="rounded-2xl overflow-hidden border border-hairline bg-surface aspect-video mb-3">
          <img :src="engenheiro.fotos_portfolio[fotoPrincipal]" class="w-full h-full object-cover" />
        </div>
        <!-- Thumbnails -->
        <div v-if="engenheiro.fotos_portfolio.length > 1" class="flex gap-2 overflow-x-auto pb-1">
          <button
            v-for="(url, i) in engenheiro.fotos_portfolio"
            :key="url"
            @click="fotoPrincipal = i"
            class="shrink-0 w-16 h-16 rounded-xl overflow-hidden border-2 transition-all cursor-pointer"
            :class="fotoPrincipal === i ? 'border-brand-primary' : 'border-hairline opacity-60 hover:opacity-100'"
          >
            <img :src="url" class="w-full h-full object-cover" />
          </button>
        </div>
      </section>

      <!-- Avaliações -->
      <section v-if="engenheiro.avaliacoes?.length">
        <h2 class="text-xs font-bold text-ink-muted uppercase tracking-wider mb-4 flex items-center gap-1.5">
          <Star class="w-3.5 h-3.5" stroke-width="1.5" />
          Avaliações de Clientes
        </h2>

        <!-- Resumo de nota -->
        <div class="flex items-center gap-4 bg-surface border border-hairline rounded-2xl px-6 py-5 mb-4">
          <div class="text-center shrink-0">
            <p class="text-4xl font-black text-ink">{{ engenheiro.rating?.toFixed(1) }}</p>
            <div class="flex gap-0.5 justify-center mt-1">
              <Star
                v-for="i in 5"
                :key="i"
                class="w-3.5 h-3.5"
                :class="i <= Math.round(engenheiro.rating || 0) ? 'text-yellow-400 fill-yellow-400' : 'text-hairline fill-hairline'"
                stroke-width="0"
              />
            </div>
            <p class="text-[11px] text-ink-muted mt-1">{{ engenheiro.total_reviews }} avaliações</p>
          </div>
          <div class="flex-1 space-y-1.5 min-w-0">
            <div v-for="estrelas in [5,4,3,2,1]" :key="estrelas" class="flex items-center gap-2">
              <span class="text-[11px] text-ink-muted w-3 shrink-0">{{ estrelas }}</span>
              <Star class="w-3 h-3 text-yellow-400 fill-yellow-400 shrink-0" stroke-width="0" />
              <div class="flex-1 h-1.5 bg-canvas rounded-full overflow-hidden">
                <div
                  class="h-full bg-yellow-400 rounded-full"
                  :style="{ width: `${(engenheiro.avaliacoes.filter(a => a.nota === estrelas).length / engenheiro.avaliacoes.length) * 100}%` }"
                ></div>
              </div>
              <span class="text-[11px] text-ink-muted w-3 shrink-0">{{ engenheiro.avaliacoes.filter(a => a.nota === estrelas).length }}</span>
            </div>
          </div>
        </div>

        <!-- Lista de comentários -->
        <div class="space-y-3">
          <div
            v-for="(av, i) in engenheiro.avaliacoes"
            :key="i"
            class="bg-surface border border-hairline rounded-2xl p-5"
          >
            <div class="flex items-start justify-between gap-3 mb-2">
              <div>
                <p class="text-sm font-semibold text-ink">{{ av.autor }}</p>
                <div class="flex gap-0.5 mt-0.5">
                  <Star
                    v-for="j in 5"
                    :key="j"
                    class="w-3 h-3"
                    :class="j <= av.nota ? 'text-yellow-400 fill-yellow-400' : 'text-hairline fill-hairline'"
                    stroke-width="0"
                  />
                </div>
              </div>
              <span class="text-[11px] text-ink-muted shrink-0">
                {{ new Date(av.data).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' }) }}
              </span>
            </div>
            <p class="text-sm text-ink-muted leading-relaxed">{{ av.comentario }}</p>
          </div>
        </div>
      </section>

      <!-- Simulador Inline -->
      <section id="simular">
        <div class="bg-surface border border-hairline rounded-2xl overflow-hidden">
          <!-- Header do card -->
          <div class="px-6 py-5 border-b border-hairline bg-brand-primary/5">
            <div class="flex items-center gap-2 mb-1">
              <Calculator class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
              <h2 class="text-base font-bold text-ink">Simule sua obra com {{ nomeAbreviado }}</h2>
            </div>
            <p class="text-xs text-ink-muted">Estimativa baseada nas tabelas SINAPI e CUB da sua região. Gratuito e sem compromisso.</p>
          </div>

          <div class="px-6 py-6 space-y-5">

            <!-- Formulário -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <!-- UF -->
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Estado (UF)</label>
                <div class="relative">
                  <select v-model="form.uf" class="w-full bg-canvas border border-hairline rounded-xl px-3 py-2.5 text-sm text-ink focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary appearance-none cursor-pointer transition-all">
                    <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
                  </select>
                  <ChevronDown class="w-[18px] h-[18px] absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
                </div>
              </div>

              <!-- Metragem -->
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Área (m²)</label>
                <div class="relative">
                  <input
                    v-model.number="form.metragem"
                    type="number"
                    min="30"
                    max="10000"
                    class="w-full bg-canvas border border-hairline text-ink rounded-xl py-2.5 px-3 pr-10 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all font-mono"
                    placeholder="120"
                  />
                  <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-ink-muted font-mono pointer-events-none">m²</span>
                </div>
              </div>

              <!-- Padrão -->
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Padrão</label>
                <div class="grid grid-cols-3 bg-canvas p-1 rounded-xl border border-hairline gap-1">
                  <button
                    v-for="p in padroes"
                    :key="p.value"
                    type="button"
                    @click="form.padrao = p.value"
                    class="py-2 text-xs font-medium rounded-lg transition-all cursor-pointer"
                    :class="form.padrao === p.value ? 'bg-brand-primary text-white font-semibold' : 'text-ink-muted hover:bg-surface'"
                  >
                    {{ p.label }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Botão calcular -->
            <button
              @click="calcular"
              :disabled="loadingCalculo"
              class="w-full bg-brand-primary hover:bg-brand-hover text-white py-3 rounded-xl text-sm font-bold transition-all cursor-pointer flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-50"
            >
              <Loader2 v-if="loadingCalculo" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
              <Calculator v-else class="w-[18px] h-[18px]" stroke-width="1.5" />
              {{ loadingCalculo ? 'Calculando...' : 'Calcular Custo Estimado' }}
            </button>

            <!-- Erro cálculo -->
            <p v-if="erroCalculo" class="text-xs text-red-500 flex items-center gap-1">
              <AlertTriangle class="w-3.5 h-3.5 text-red-500 inline-block align-text-bottom mr-1" stroke-width="1.5" />{{ erroCalculo }}
            </p>
          </div>

          <!-- Resultado + Formulário de contato -->
          <div v-if="resultado" class="border-t border-hairline px-6 py-6 space-y-6 bg-canvas/50">

            <!-- Valores estimados -->
            <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div>
                <p class="text-xs text-ink-muted uppercase font-bold tracking-wide mb-1">Custo Estimado da Obra</p>
                <p class="text-3xl font-black text-ink tracking-tight font-mono">{{ formatCurrency(resultado.valor_estimado) }}</p>
              </div>
              <div class="flex gap-6 text-right">
                <div>
                  <p class="text-[10px] text-ink-muted uppercase font-bold tracking-wide">Custo/m²</p>
                  <p class="text-sm font-bold text-ink font-mono">{{ formatCurrency(resultado.custo_m2) }}</p>
                </div>
                <div>
                  <p class="text-[10px] text-ink-muted uppercase font-bold tracking-wide">Financ. Caixa (80%)</p>
                  <p class="text-sm font-bold text-ink font-mono">{{ formatCurrency(resultado.margem_financiamento) }}</p>
                </div>
              </div>
            </div>

            <!-- Separador com CTA -->
            <div class="flex items-center gap-3">
              <div class="flex-1 h-px bg-hairline"></div>
              <span class="text-xs font-bold text-ink-muted uppercase tracking-wider">Solicitar orçamento formal</span>
              <div class="flex-1 h-px bg-hairline"></div>
            </div>

            <!-- Formulário de contato -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Seu Nome <span class="text-red-500">*</span></label>
                <input
                  v-model="contato.nome"
                  type="text"
                  class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
                  placeholder="Ex: Maria Silva"
                />
              </div>
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">WhatsApp (com DDD) <span class="text-red-500">*</span></label>
                <input
                  v-model="contato.telefone"
                  type="tel"
                  class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted font-mono"
                  placeholder="(48) 99999-9999"
                />
              </div>
            </div>

            <p v-if="erroSolicitar" class="text-xs text-red-500 flex items-center gap-1">
              <AlertTriangle class="w-3.5 h-3.5 text-red-500 inline-block align-text-bottom mr-1" stroke-width="1.5" />{{ erroSolicitar }}
            </p>

            <!-- Botão principal de conversão -->
            <button
              @click="solicitarOrcamento"
              :disabled="loadingSolicitar"
              class="w-full bg-green-600 hover:bg-green-500 text-white py-4 rounded-xl text-sm font-bold transition-all cursor-pointer flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-50 shadow-lg shadow-green-500/20 font-sans"
            >
              <Loader2 v-if="loadingSolicitar" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
              <Handshake v-else class="w-[18px] h-[18px]" stroke-width="1.5" />
              {{ loadingSolicitar ? 'Enviando...' : `Solicitar Orçamento para ${nomeAbreviado}` }}
            </button>
            <p class="text-[11px] text-center text-ink-muted">Sem compromisso. {{ nomeAbreviado }} entrará em contato para agendar uma visita técnica.</p>
          </div>
        </div>
      </section>

      <!-- Footer da vitrine -->
      <footer class="text-center pt-4 pb-10">
        <p class="text-xs text-ink-muted">
          Perfil gerenciado pelo engenheiro via
          <router-link to="/" class="text-brand-primary hover:underline font-semibold">Plataforma Vértice</router-link>
        </p>
      </footer>

    </div>
  </div>
</template>

<style scoped>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
</style>
