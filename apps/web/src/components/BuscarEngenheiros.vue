<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, MapPin, Star, HardHat, ChevronDown, ArrowRight, CheckCircle2, Users, X } from 'lucide-vue-next'
import VerticeLogo from './VerticeLogo.vue'
import { ENGENHEIROS_MOCK } from '../data/mockEngenheiros'
import { supabase } from '../supabase'

const router = useRouter()
const filtroUF = ref('')
const filtroBusca = ref('')
const userName = ref('')

onMounted(async () => {
  const { data } = await supabase.auth.getSession()
  if (data.session?.user) {
    userName.value = data.session.user.user_metadata?.full_name?.split(' ')[0] || ''
  }
})

const ufs = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO']

const engenheiros = computed(() => {
  return ENGENHEIROS_MOCK.filter(eng => {
    const matchUF = !filtroUF.value || eng.uf_principal === filtroUF.value
    const matchBusca = !filtroBusca.value ||
      eng.nome_completo.toLowerCase().includes(filtroBusca.value.toLowerCase()) ||
      eng.cidades_atuacao.some(c => c.toLowerCase().includes(filtroBusca.value.toLowerCase()))
    return matchUF && matchBusca
  })
})

const ratingLabel = (r) => {
  if (r >= 4.8) return 'Excelente'
  if (r >= 4.5) return 'Ótimo'
  if (r >= 4.0) return 'Muito bom'
  return 'Bom'
}

const ratingColor = (r) => {
  if (r >= 4.8) return 'text-emerald-500'
  if (r >= 4.5) return 'text-green-500'
  return 'text-yellow-500'
}

const handleLogout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen bg-canvas text-ink font-sans antialiased">

    <!-- Header -->
    <header class="sticky top-0 z-50 bg-surface/90 backdrop-blur-md border-b border-hairline h-14 flex items-center">
      <div class="w-full max-w-[1280px] mx-auto px-6 flex items-center justify-between">
        <router-link to="/">
          <VerticeLogo class="h-[28px] text-logo" />
        </router-link>
        <div class="flex items-center gap-4">
          <span v-if="userName" class="text-xs text-ink-muted hidden sm:block">
            Olá, <span class="font-semibold text-ink">{{ userName }}</span>
          </span>
          <router-link to="/simulador" class="text-xs text-ink-muted hover:text-ink transition-colors hidden sm:block">
            Simulador de Custos
          </router-link>
          <button @click="handleLogout" class="text-xs text-ink-muted hover:text-ink transition-colors cursor-pointer">
            Sair
          </button>
        </div>
      </div>
    </header>

    <!-- Hero -->
    <section class="bg-gradient-to-b from-brand-blue/[0.06] to-canvas border-b border-hairline py-12 px-6">
      <div class="max-w-[1280px] mx-auto">
        <div class="flex items-center gap-2 mb-3">
          <span class="w-1.5 h-1.5 bg-brand-orange rounded-full animate-pulse"></span>
          <span class="text-[11px] font-bold text-ink-muted tracking-wider uppercase font-mono">{{ ENGENHEIROS_MOCK.length }} engenheiros verificados · 6 estados</span>
        </div>
        <h1 class="text-3xl sm:text-4xl md:text-5xl font-black text-ink tracking-tight mb-3">
          Encontre o Engenheiro<br class="hidden sm:block" />
          <span class="text-brand-blue"> Ideal para sua Obra</span>
        </h1>
        <p class="text-sm sm:text-base text-ink-muted max-w-xl">
          Todos os profissionais são verificados, possuem registro CREA/CAU ativo e utilizam o sistema Vértice para transparência total na sua obra.
        </p>

        <!-- Stats -->
        <div class="flex flex-wrap gap-6 mt-6">
          <div class="flex items-center gap-2">
            <CheckCircle2 class="w-4 h-4 text-emerald-500" stroke-width="2" />
            <span class="text-xs text-ink-muted">CREA/CAU verificado</span>
          </div>
          <div class="flex items-center gap-2">
            <Star class="w-4 h-4 text-yellow-400 fill-yellow-400" stroke-width="0" />
            <span class="text-xs text-ink-muted">Avaliações reais de clientes</span>
          </div>
          <div class="flex items-center gap-2">
            <HardHat class="w-4 h-4 text-brand-blue" stroke-width="1.5" />
            <span class="text-xs text-ink-muted">Orçamento SINAPI gratuito</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Filtros -->
    <section class="border-b border-hairline bg-surface/50 py-4 px-6 sticky top-14 z-40">
      <div class="max-w-[1280px] mx-auto flex flex-col sm:flex-row gap-3">
        <!-- Busca por nome/cidade -->
        <div class="relative flex-1">
          <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" stroke-width="1.5" />
          <input
            v-model="filtroBusca"
            type="text"
            placeholder="Buscar por nome ou cidade..."
            class="w-full bg-canvas border border-hairline rounded-xl pl-9 pr-4 py-2.5 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all"
          />
          <button v-if="filtroBusca" @click="filtroBusca = ''" class="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink cursor-pointer">
            <X class="w-3.5 h-3.5" stroke-width="2" />
          </button>
        </div>

        <!-- Filtro por estado -->
        <div class="relative w-full sm:w-44">
          <select
            v-model="filtroUF"
            class="w-full bg-canvas border border-hairline rounded-xl px-3 pr-8 py-2.5 text-sm text-ink focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue appearance-none cursor-pointer transition-all"
          >
            <option value="">Todos os estados</option>
            <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
          </select>
          <ChevronDown class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
        </div>
      </div>
    </section>

    <!-- Resultados -->
    <main class="max-w-[1280px] mx-auto px-6 py-8">

      <!-- Contador -->
      <p class="text-xs text-ink-muted mb-6">
        <span class="font-semibold text-ink">{{ engenheiros.length }}</span> profissional{{ engenheiros.length !== 1 ? 'is' : '' }} encontrado{{ engenheiros.length !== 1 ? 's' : '' }}
        <span v-if="filtroUF"> em <span class="font-semibold text-ink">{{ filtroUF }}</span></span>
      </p>

      <!-- Sem resultados -->
      <div v-if="engenheiros.length === 0" class="flex flex-col items-center justify-center py-24 gap-4 text-center">
        <Users class="w-12 h-12 text-ink-muted/40" stroke-width="1" />
        <p class="text-sm text-ink-muted">Nenhum engenheiro encontrado com esses filtros.</p>
        <button @click="filtroUF = ''; filtroBusca = ''" class="text-xs text-brand-blue hover:underline cursor-pointer">Limpar filtros</button>
      </div>

      <!-- Grid de cards -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          v-for="eng in engenheiros"
          :key="eng.id"
          class="group bg-surface border border-hairline rounded-2xl overflow-hidden hover:border-brand-blue/40 hover:shadow-lg hover:shadow-brand-blue/5 transition-all duration-300"
        >
          <!-- Foto de portfólio de fundo (destaque) -->
          <div class="relative h-36 bg-canvas overflow-hidden">
            <img
              v-if="eng.fotos_portfolio?.[0]"
              :src="eng.fotos_portfolio[0]"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              loading="lazy"
            />
            <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent"></div>

            <!-- Badge rating no canto -->
            <div class="absolute top-3 right-3 flex items-center gap-1 bg-black/70 backdrop-blur-sm rounded-lg px-2 py-1">
              <Star class="w-3 h-3 text-yellow-400 fill-yellow-400" stroke-width="0" />
              <span class="text-xs font-bold text-white">{{ eng.rating.toFixed(1) }}</span>
            </div>
          </div>

          <!-- Corpo do card -->
          <div class="p-5">
            <!-- Foto + Nome -->
            <div class="flex items-start gap-3 mb-3 -mt-8 relative">
              <div class="w-14 h-14 rounded-xl border-2 border-surface overflow-hidden bg-canvas shrink-0 shadow-lg">
                <img :src="eng.foto_perfil" class="w-full h-full object-cover" loading="lazy" />
              </div>
              <div class="pt-6 min-w-0">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <h2 class="text-sm font-bold text-ink truncate">{{ eng.nome_completo }}</h2>
                  <CheckCircle2 class="w-3.5 h-3.5 text-brand-blue shrink-0" stroke-width="2.5" />
                </div>
                <p class="text-[11px] text-ink-muted font-mono mt-0.5">{{ eng.registro_crea_cau }}</p>
              </div>
            </div>

            <!-- Rating detalhado -->
            <div class="flex items-center gap-2 mb-3">
              <div class="flex gap-0.5">
                <Star
                  v-for="i in 5"
                  :key="i"
                  class="w-3.5 h-3.5"
                  :class="i <= Math.round(eng.rating) ? 'text-yellow-400 fill-yellow-400' : 'text-hairline fill-hairline'"
                  stroke-width="0"
                />
              </div>
              <span :class="ratingColor(eng.rating)" class="text-xs font-bold">{{ ratingLabel(eng.rating) }}</span>
              <span class="text-[11px] text-ink-muted">· {{ eng.total_reviews }} avaliações</span>
            </div>

            <!-- Projetos concluídos -->
            <div class="flex items-center gap-1.5 mb-3">
              <HardHat class="w-3.5 h-3.5 text-ink-muted" stroke-width="1.5" />
              <span class="text-xs text-ink-muted"><span class="font-semibold text-ink">{{ eng.projetos_concluidos }}</span> projetos concluídos</span>
            </div>

            <!-- Bio -->
            <p class="text-xs text-ink-muted leading-relaxed line-clamp-2 mb-3">{{ eng.descricao_vitrine }}</p>

            <!-- Cidades -->
            <div class="flex flex-wrap gap-1.5 mb-4">
              <span
                v-for="(cidade, i) in eng.cidades_atuacao.slice(0, 2)"
                :key="cidade"
                class="flex items-center gap-1 text-[11px] text-ink-muted bg-canvas border border-hairline px-2 py-0.5 rounded-lg"
              >
                <MapPin class="w-2.5 h-2.5" stroke-width="1.5" />
                {{ cidade.split('–')[0].trim() }}
              </span>
              <span
                v-if="eng.cidades_atuacao.length > 2"
                class="text-[11px] text-ink-muted bg-canvas border border-hairline px-2 py-0.5 rounded-lg"
              >
                +{{ eng.cidades_atuacao.length - 2 }}
              </span>
            </div>

            <!-- CTA -->
            <router-link
              :to="`/p/${eng.slug}`"
              class="w-full flex items-center justify-center gap-2 bg-brand-blue hover:bg-brand-blue-hover text-white text-xs font-bold py-2.5 rounded-xl transition-all duration-200 cursor-pointer border-none"
            >
              Ver Perfil Completo
              <ArrowRight class="w-3.5 h-3.5" stroke-width="2.5" />
            </router-link>
          </div>
        </div>
      </div>

      <!-- Nota mockup -->
      <div class="mt-12 p-4 bg-brand-orange/5 border border-brand-orange/20 rounded-xl text-center">
        <p class="text-xs text-ink-muted">
          <span class="font-semibold text-ink">Dados de demonstração.</span> Estes profissionais são fictícios e estão aqui para demonstrar o funcionamento da plataforma.
          Engenheiros reais se cadastram em <router-link to="/auth" class="text-brand-blue hover:underline">Acesso Construtor</router-link>.
        </p>
      </div>
    </main>

  </div>
</template>
