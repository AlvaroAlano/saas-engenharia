<template>
  <div class="min-h-screen bg-canvas text-ink font-sans antialiased overflow-x-hidden selection:bg-brand-primary/30 selection:text-white transition-colors duration-200">
    
    <!-- HEADER / NAVIGATION -->
    <header class="sticky top-0 z-50 w-full h-[56px] bg-surface/80 backdrop-blur-md border-b border-hairline transition-all duration-300 flex items-center">
      <div class="w-full max-w-[1280px] mx-auto px-6 flex items-center justify-between">
        <!-- Left: Logo & Wordmark -->
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-brand-primary/10 rounded-md border border-brand-primary/30 flex items-center justify-center">
            <Layers class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
          </div>
          <span class="text-[18px] font-semibold text-ink tracking-[-0.4px]">Vértice</span>
          <span class="text-[10px] bg-canvas border border-hairline text-ink-muted px-2 py-0.5 rounded-full font-mono font-medium">v1.0</span>
        </div>

        <!-- Right Side: Links + Actions -->
        <div class="flex items-center gap-6">
          <!-- Links (Desktop) -->
          <nav class="hidden md:flex items-center gap-6 text-[13px] font-medium text-ink-muted">
            <a href="#features" class="hover:text-ink transition-colors duration-200">Funcionalidades</a>
            <a href="#demo" class="hover:text-ink transition-colors duration-200">Simulador</a>
            <a href="#workflow" class="hover:text-ink transition-colors duration-200">Como Funciona</a>
            <a href="#pricing" class="hover:text-ink transition-colors duration-200">Preços</a>
          </nav>

          <!-- Divider -->
          <div class="hidden md:block w-[1px] h-5 bg-hairline"></div>

          <!-- Action Buttons -->
          <div class="flex items-center gap-3">
            <!-- Theme Toggle Button -->
            <button 
              @click="toggleTheme" 
              class="p-2 text-ink-muted hover:text-ink hover:bg-surface-hover rounded-md transition-all cursor-pointer flex items-center justify-center focus:outline-none"
              title="Alternar Tema"
            >
              <Sun v-if="isDark" class="w-5 h-5" stroke-width="1.5" />
              <Moon v-else class="w-5 h-5" stroke-width="1.5" />
            </button>

            <!-- Client Portal Access (Desktop only: hidden md:inline-flex) -->
            <button 
              @click="openClientModal = true" 
              class="hidden md:inline-flex items-center justify-center bg-surface hover:bg-surface-hover text-ink border border-hairline rounded-md text-[13px] font-medium px-4 py-2 transition-all duration-200 cursor-pointer"
            >
              Acesso Cliente
            </button>
            
            <!-- Builder Access (Desktop only: hidden md:inline-flex) -->
            <router-link 
              v-if="hasSession" 
              to="/dashboard" 
              class="hidden md:inline-flex items-center justify-center bg-brand-primary hover:bg-brand-hover text-white rounded-md text-[13px] font-medium px-4 py-2 transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-primary/50"
            >
              Entrar no Painel
            </router-link>
            <router-link 
              v-else 
              to="/auth" 
              class="hidden md:inline-flex items-center justify-center bg-brand-primary hover:bg-brand-hover text-white rounded-md text-[13px] font-medium px-4 py-2 transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-primary/50"
            >
              Acesso Construtor
            </router-link>

            <!-- Mobile Menu Trigger -->
            <button @click="toggleMobileMenu" class="md:hidden p-1 text-ink-muted hover:text-ink cursor-pointer flex items-center">
              <X v-if="mobileMenuOpen" class="w-5 h-5" stroke-width="1.5" />
              <Menu v-else class="w-5 h-5" stroke-width="1.5" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- MOBILE MENU OVERLAY -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-[-10px]"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-[-10px]"
    >
      <div v-if="mobileMenuOpen" class="fixed inset-x-0 top-[56px] p-6 bg-surface border-b border-hairline z-40 md:hidden flex flex-col gap-4 shadow-lg">
        <a href="#features" @click="mobileMenuOpen = false" class="text-ink-muted hover:text-ink py-2 text-sm font-medium">Funcionalidades</a>
        <a href="#demo" @click="mobileMenuOpen = false" class="text-ink-muted hover:text-ink py-2 text-sm font-medium">Simulador</a>
        <a href="#workflow" @click="mobileMenuOpen = false" class="text-ink-muted hover:text-ink py-2 text-sm font-medium">Como Funciona</a>
        <a href="#pricing" @click="mobileMenuOpen = false" class="text-ink-muted hover:text-ink py-2 text-sm font-medium">Preços</a>
        <div class="h-[1px] bg-hairline my-2"></div>
        <button 
          @click="toggleTheme" 
          class="w-full py-2.5 bg-canvas border border-hairline text-ink rounded-md text-sm font-medium flex items-center justify-center gap-2 cursor-pointer hover:bg-surface-hover"
        >
          <Sun v-if="isDark" class="w-[18px] h-[18px]" stroke-width="1.5" />
          <Moon v-else class="w-[18px] h-[18px]" stroke-width="1.5" />
          <span>Tema: {{ isDark ? 'Claro' : 'Escuro' }}</span>
        </button>
        <button 
          @click="openClientModal = true; mobileMenuOpen = false" 
          class="w-full text-center py-2.5 bg-surface border border-hairline text-ink hover:bg-surface-hover rounded-md text-sm font-medium cursor-pointer"
        >
          Acesso Cliente
        </button>
        <router-link 
          v-if="hasSession" 
          to="/dashboard" 
          @click="mobileMenuOpen = false" 
          class="w-full text-center py-2.5 bg-brand-primary text-white rounded-md text-sm font-medium cursor-pointer block"
        >
          Entrar no Painel
        </router-link>
        <router-link 
          v-else 
          to="/auth" 
          @click="mobileMenuOpen = false" 
          class="w-full text-center py-2.5 bg-brand-primary text-white rounded-md text-sm font-medium cursor-pointer block"
        >
          Acesso Construtor
        </router-link>
      </div>
    </transition>

    <!-- HERO SECTION (Full width gradient and glow) -->
    <section class="w-full bg-gradient-to-b from-canvas via-canvas to-surface/40 relative overflow-hidden pt-20 pb-16 md:pt-32 md:pb-24 border-b border-hairline">
      <!-- Soft Luxury Radial Glow -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] md:w-[800px] md:h-[800px] bg-brand-primary/4 rounded-full blur-[140px] pointer-events-none z-0"></div>
      
      <div class="relative z-10 flex flex-col px-6 max-w-[1280px] mx-auto">
        
        <!-- Hero Content: Text (Left) + Buttons (Right) -->
        <div class="flex flex-col lg:flex-row lg:items-end justify-between gap-8 mb-16">
          
          <!-- Left: Text content -->
          <div class="flex flex-col items-start text-left max-w-[700px]">
            <!-- Announcement Chip -->
            <div class="inline-flex items-center gap-2 px-3 py-1 bg-surface border border-hairline rounded-full mb-6 animate-blur-in-up">
              <span class="w-1.5 h-1.5 bg-semantic-success rounded-full animate-pulse"></span>
              <span class="text-[12px] font-medium text-ink-muted tracking-wide font-sans">VÉRTICE 1.0 — ORÇAMENTOS E MEDIÇÕES PARA CONSTRUTORAS</span>
            </div>

            <!-- Main Headline -->
            <h1 class="text-[36px] md:text-[64px] font-semibold text-ink leading-[1.05] tracking-[-1.5px] md:tracking-[-2.5px] mb-6 animate-blur-in-up delay-100">
              O sistema operacional da sua engenharia civil.
            </h1>

            <!-- Subheadline -->
            <p class="text-[16px] md:text-[18px] text-ink-muted leading-[1.5] tracking-[-0.1px] font-sans animate-blur-in-up delay-200">
              Orçamentos automáticos integrados à tabela SINAPI, cronogramas físico-financeiros Caixa e um portal de transparência completo para os seus clientes de obras financiadas.
            </p>
          </div>

          <!-- Right: CTA Buttons -->
          <div class="flex flex-col sm:flex-row items-center gap-4 animate-blur-in-up delay-300 shrink-0">
            <a href="#demo" class="w-full sm:w-auto inline-flex items-center justify-center bg-surface hover:bg-surface-hover text-ink border border-hairline rounded-md text-[14px] font-medium px-6 py-3 transition-all duration-200 cursor-pointer">
              Simular Custos
            </a>
            <router-link to="/auth" class="w-full sm:w-auto inline-flex items-center justify-center bg-brand-primary hover:bg-brand-hover text-white border border-transparent rounded-md text-[14px] font-medium px-6 py-3 transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-primary/50">
              Iniciar Teste Gratuito
              <ArrowRight class="w-4 h-4 ml-2" stroke-width="1.5" />
            </router-link>
          </div>

        </div>

        <!-- Interactive Product UI Panel (Screenshot/Mockup Card) -->
        <div class="w-full bg-surface border border-hairline rounded-xl p-4 md:p-6 text-left relative overflow-hidden transition-all duration-300 hover:border-hairline animate-blur-in-up delay-400">
        
        <!-- Chrome Navigation / Tabs -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-hairline pb-4 mb-6">
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-[#ff5f56]/80"></span>
            <span class="w-3 h-3 rounded-full bg-[#ffbd2e]/80"></span>
            <span class="w-3 h-3 rounded-full bg-[#27c93f]/80"></span>
            <span class="text-xs text-ink-muted ml-2 font-mono">vertice.app/obras/bella-vista</span>
          </div>

          <!-- Tabs Toggles -->
          <div class="flex items-center bg-canvas p-1 rounded-lg border border-hairline self-start md:self-auto">
            <button 
              @click="activeMockupTab = 'orcamento'" 
              :class="activeMockupTab === 'orcamento' ? 'bg-surface text-ink border border-hairline' : 'text-ink-muted hover:text-ink border border-transparent'"
              class="px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 flex items-center gap-2 cursor-pointer"
            >
              <DollarSign class="w-3.5 h-3.5" stroke-width="1.5" />
              Orçamento SINAPI
            </button>
            <button 
              @click="activeMockupTab = 'cronograma'" 
              :class="activeMockupTab === 'cronograma' ? 'bg-surface text-ink border border-hairline' : 'text-ink-muted hover:text-ink border border-transparent'"
              class="px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 flex items-center gap-2 cursor-pointer"
            >
              <Calendar class="w-3.5 h-3.5" stroke-width="1.5" />
              Cronograma Caixa
            </button>
            <button 
              @click="activeMockupTab = 'portal'" 
              :class="activeMockupTab === 'portal' ? 'bg-surface text-ink border border-hairline' : 'text-ink-muted hover:text-ink border border-transparent'"
              class="px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 flex items-center gap-2 cursor-pointer"
            >
              <Users class="w-3.5 h-3.5" stroke-width="1.5" />
              Portal do Cliente
            </button>
          </div>
        </div>

        <!-- Tab Content 1: ORÇAMENTO SINAPI -->
        <div v-if="activeMockupTab === 'orcamento'" class="animate-fade-in grid grid-cols-1 lg:grid-cols-4 gap-6">
          <!-- Sidebar in Dashboard Mockup -->
          <div class="lg:col-span-1 bg-canvas border border-hairline rounded-lg p-4 flex flex-col gap-4">
            <div class="flex flex-col">
              <span class="text-[10px] text-ink-muted tracking-[0.4px] font-semibold uppercase">Obra Selecionada</span>
              <span class="text-sm font-semibold text-ink mt-0.5">Residencial Bella Vista</span>
            </div>
            <div class="h-[1px] bg-hairline"></div>
            <div class="flex flex-col gap-1.5">
              <span class="text-[10px] text-ink-muted tracking-[0.4px] font-semibold uppercase mb-1">Estrutura de Custos</span>
              <button class="w-full text-left px-3 py-1.5 bg-surface text-brand-primary border border-hairline rounded-md text-xs font-medium flex items-center justify-between">
                <span>01. Serviços Preliminares</span>
                <span class="text-[10px] font-mono text-ink-muted">R$ 12k</span>
              </button>
              <button class="w-full text-left px-3 py-1.5 text-ink-muted hover:bg-surface-hover rounded-md text-xs font-medium flex items-center justify-between">
                <span>02. Infraestrutura</span>
                <span class="text-[10px] font-mono text-ink-muted">R$ 84k</span>
              </button>
              <button class="w-full text-left px-3 py-1.5 text-ink-muted hover:bg-surface-hover rounded-md text-xs font-medium flex items-center justify-between">
                <span>03. Superestrutura</span>
                <span class="text-[10px] font-mono text-ink-muted">R$ 210k</span>
              </button>
              <button class="w-full text-left px-3 py-1.5 text-ink-muted hover:bg-surface-hover rounded-md text-xs font-medium flex items-center justify-between">
                <span>04. Alvenarias</span>
                <span class="text-[10px] font-mono text-ink-muted">R$ 78k</span>
              </button>
              <button class="w-full text-left px-3 py-1.5 text-ink-muted hover:bg-surface-hover rounded-md text-xs font-medium flex items-center justify-between">
                <span>05. Acabamentos</span>
                <span class="text-[10px] font-mono text-ink-muted">R$ 145k</span>
              </button>
            </div>
          </div>

          <!-- Main Table in Dashboard Mockup -->
          <div class="lg:col-span-3 flex flex-col gap-4">
            <div class="flex items-center justify-between bg-canvas border border-hairline rounded-lg p-4">
              <div class="flex items-center gap-4">
                <span class="text-xs text-ink-muted">Sincronização SINAPI</span>
                <div class="flex items-center gap-1 bg-brand-primary/10 border border-brand-primary/25 px-2 py-0.5 rounded-full">
                  <span class="w-1 h-1 bg-brand-primary rounded-full"></span>
                  <span class="text-[10px] font-mono font-medium text-brand-primary">MAIO 2026 / SP</span>
                </div>
              </div>
              <div class="text-right">
                <span class="text-xs text-ink-muted block">Valor Estimado</span>
                <span class="text-lg font-bold text-ink tracking-tight font-mono">R$ 529.000,00</span>
              </div>
            </div>

            <!-- SINAPI Items Mockup List -->
            <div class="border border-hairline rounded-lg bg-canvas overflow-hidden">
              <div class="grid grid-cols-12 bg-surface border-b border-hairline px-4 py-2.5 text-[10px] font-semibold text-ink-muted tracking-[0.4px] uppercase font-mono">
                <div class="col-span-2">Código</div>
                <div class="col-span-5">Descrição SINAPI</div>
                <div class="col-span-1 text-center">Un.</div>
                <div class="col-span-2 text-right">Qtd.</div>
                <div class="col-span-2 text-right">Total</div>
              </div>

              <div class="divide-y divide-hairline">
                <div class="grid grid-cols-12 px-4 py-3 text-xs items-center hover:bg-surface-hover transition-colors">
                  <div class="col-span-2 font-mono text-ink-muted">98502</div>
                  <div class="col-span-5 text-ink font-medium">Concreto usinado fck = 25MPa, lançado e adensado...</div>
                  <div class="col-span-1 text-center text-ink-muted font-mono">m³</div>
                  <div class="col-span-2 text-right text-ink-muted font-mono">42,00</div>
                  <div class="col-span-2 text-right text-ink font-mono font-semibold">R$ 18.270,00</div>
                </div>
                <div class="grid grid-cols-12 px-4 py-3 text-xs items-center hover:bg-surface-hover transition-colors">
                  <div class="col-span-2 font-mono text-ink-muted">92760</div>
                  <div class="col-span-5 text-ink font-medium">Armação de aço CA-50 d=10,0mm - montagem e corte...</div>
                  <div class="col-span-1 text-center text-ink-muted font-mono">kg</div>
                  <div class="col-span-2 text-right text-ink-muted font-mono">1.850,00</div>
                  <div class="col-span-2 text-right text-ink font-mono font-semibold">R$ 14.800,00</div>
                </div>
                <div class="grid grid-cols-12 px-4 py-3 text-xs items-center hover:bg-surface-hover transition-colors">
                  <div class="col-span-2 font-mono text-ink-muted">87508</div>
                  <div class="col-span-5 text-ink font-medium">Alvenaria de bloco cerâmico vazado 9x19x19cm...</div>
                  <div class="col-span-1 text-center text-ink-muted font-mono">m²</div>
                  <div class="col-span-2 text-right text-ink-muted font-mono">280,00</div>
                  <div class="col-span-2 text-right text-ink font-mono font-semibold">R$ 16.240,00</div>
                </div>
                <div class="grid grid-cols-12 px-4 py-3 text-xs items-center hover:bg-surface-hover transition-colors">
                  <div class="col-span-2 font-mono text-ink-muted">95310</div>
                  <div class="col-span-5 text-ink font-medium">Argamassa traço 1:3 para contrapiso espessura 3cm...</div>
                  <div class="col-span-1 text-center text-ink-muted font-mono">m³</div>
                  <div class="col-span-2 text-right text-ink-muted font-mono">18,50</div>
                  <div class="col-span-2 text-right text-ink font-mono font-semibold">R$ 9.157,50</div>
                </div>
              </div>
            </div>

            <div class="flex items-center justify-between text-xs text-ink-muted">
              <span>Mostrando 4 de 124 composições ativas</span>
              <button class="text-brand-primary hover:text-brand-hover font-medium flex items-center gap-1 cursor-pointer">
                <span>Visualizar árvore de custos completa</span>
                <ArrowUpRight class="w-3.5 h-3.5" stroke-width="1.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- Tab Content 2: CRONOGRAMA CAIXA -->
        <div v-else-if="activeMockupTab === 'cronograma'" class="animate-fade-in flex flex-col gap-6">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-canvas border border-hairline rounded-lg p-4">
            <div>
              <span class="text-xs text-ink-muted block">Obra Residencial Bella Vista</span>
              <span class="text-base font-semibold text-ink">Cronograma Físico-Financeiro (PCI - Caixa)</span>
            </div>
            <div class="flex items-center gap-6">
              <div class="text-right">
                <span class="text-xs text-ink-muted block">Progresso Físico</span>
                <span class="text-sm font-bold text-semantic-success">64,2%</span>
              </div>
              <div class="text-right">
                <span class="text-xs text-ink-muted block">Financeiro Desembolsado</span>
                <span class="text-sm font-bold text-ink">R$ 340.500,00</span>
              </div>
            </div>
          </div>

          <!-- Gantt / Progress Rows -->
          <div class="border border-hairline rounded-lg bg-canvas divide-y divide-hairline">
            <!-- Phase 1 -->
            <div class="p-4 flex flex-col md:flex-row md:items-center gap-4 hover:bg-surface-hover/50 transition-colors">
              <div class="w-full md:w-1/4">
                <span class="text-xs font-bold text-ink block">1. Serviços Iniciais & Infraestrutura</span>
                <span class="text-[10px] text-ink-muted font-mono">15/01/2026 - 28/02/2026</span>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between text-[11px] text-ink-muted mb-1">
                  <span>Progresso da Fase</span>
                  <span class="font-bold text-ink">100%</span>
                </div>
                <div class="w-full h-2 bg-surface-hover rounded-full overflow-hidden">
                  <div class="h-full bg-semantic-success rounded-full" style="width: 100%"></div>
                </div>
              </div>
              <div class="w-full md:w-32 text-left md:text-right">
                <span class="text-[10px] text-ink-muted block">Custo Medido</span>
                <span class="text-xs font-semibold text-ink font-mono">R$ 96.000,00</span>
              </div>
            </div>

            <!-- Phase 2 -->
            <div class="p-4 flex flex-col md:flex-row md:items-center gap-4 hover:bg-surface-hover/50 transition-colors">
              <div class="w-full md:w-1/4">
                <span class="text-xs font-bold text-ink block">2. Superestrutura e Alvenarias</span>
                <span class="text-[10px] text-ink-muted font-mono">01/03/2026 - 15/05/2026</span>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between text-[11px] text-ink-muted mb-1">
                  <span>Progresso da Fase</span>
                  <span class="font-bold text-brand-primary">85%</span>
                </div>
                <div class="w-full h-2 bg-surface-hover rounded-full overflow-hidden">
                  <div class="h-full bg-brand-primary rounded-full" style="width: 85%"></div>
                </div>
              </div>
              <div class="w-full md:w-32 text-left md:text-right">
                <span class="text-[10px] text-ink-muted block">Custo Medido</span>
                <span class="text-xs font-semibold text-ink font-mono">R$ 244.500,00</span>
              </div>
            </div>

            <!-- Phase 3 -->
            <div class="p-4 flex flex-col md:flex-row md:items-center gap-4 hover:bg-surface-hover/50 transition-colors">
              <div class="w-full md:w-1/4">
                <span class="text-xs font-bold text-ink block">3. Cobertura e Instalações Hidráulicas</span>
                <span class="text-[10px] text-ink-muted font-mono">16/05/2026 - 30/06/2026</span>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between text-[11px] text-ink-muted mb-1">
                  <span>Progresso da Fase</span>
                  <span class="font-bold text-ink-muted animate-pulse">0%</span>
                </div>
                <div class="w-full h-2 bg-surface-hover rounded-full overflow-hidden">
                  <div class="h-full bg-brand-primary rounded-full" style="width: 0%"></div>
                </div>
              </div>
              <div class="w-full md:w-32 text-left md:text-right">
                <span class="text-[10px] text-ink-muted block">Custo Medido</span>
                <span class="text-xs font-semibold text-ink-muted font-mono">R$ 0,00</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab Content 3: PORTAL DO CLIENTE -->
        <div v-else-if="activeMockupTab === 'portal'" class="animate-fade-in grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <!-- Client Welcome Card -->
          <div class="lg:col-span-1 bg-canvas border border-hairline rounded-lg p-5 flex flex-col justify-between">
            <div>
              <span class="text-[10px] text-ink-muted tracking-[0.4px] font-semibold uppercase">Visão do Proprietário</span>
              <h3 class="text-base font-bold text-ink mt-1">Olá, Ana & Bruno!</h3>
              <p class="text-xs text-ink-muted mt-2 leading-[1.4]">
                Acompanhe o cronograma financeiro e envie documentos para a liberação da próxima parcela do seu financiamento de forma direta.
              </p>
            </div>
            
            <div class="mt-8 border-t border-hairline pt-4 flex flex-col gap-2">
              <span class="text-[10px] text-ink-muted uppercase">Construtora Responsável</span>
              <span class="text-xs font-medium text-ink">Engenharia Vértice S/A</span>
            </div>
          </div>

          <!-- Client Progress Overview -->
          <div class="lg:col-span-2 flex flex-col gap-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-canvas border border-hairline rounded-lg p-4">
                <span class="text-[10px] text-ink-muted uppercase block">O que já foi executado</span>
                <span class="text-xl font-bold text-ink mt-1 block font-mono">R$ 340.500,00</span>
                <span class="text-[10px] text-semantic-success mt-1 flex items-center gap-1 font-sans">
                  <CheckCircle2 class="w-3 h-3 text-semantic-success" stroke-width="1.5" />
                  Orçamento de acordo com o plano
                </span>
              </div>
              <div class="bg-canvas border border-hairline rounded-lg p-4">
                <span class="text-[10px] text-ink-muted uppercase block">Próxima Medição Caixa</span>
                <span class="text-xl font-bold text-brand-primary mt-1 block font-mono">R$ 48.200,00</span>
                <span class="text-[10px] text-ink-muted mt-1 block font-sans">Vistoria agendada para 22/05</span>
              </div>
            </div>

            <!-- Client timeline / photo report preview -->
            <div class="bg-canvas border border-hairline rounded-lg p-4">
              <span class="text-xs font-semibold text-ink block mb-3">Diário de Obra e Registro Fotográfico</span>
              <div class="grid grid-cols-3 gap-3">
                <div class="aspect-video bg-surface border border-hairline rounded-md relative flex items-center justify-center overflow-hidden group">
                  <Image class="w-5 h-5 text-ink-muted group-hover:scale-110 transition-transform" stroke-width="1.5" />
                  <div class="absolute bottom-1 left-1.5 bg-surface/80 px-1.5 py-0.5 rounded text-[8px] text-ink">Fundação Concluída</div>
                </div>
                <div class="aspect-video bg-surface border border-hairline rounded-md relative flex items-center justify-center overflow-hidden group">
                  <Image class="w-5 h-5 text-ink-muted group-hover:scale-110 transition-transform" stroke-width="1.5" />
                  <div class="absolute bottom-1 left-1.5 bg-surface/80 px-1.5 py-0.5 rounded text-[8px] text-ink">Alvenaria Térrea</div>
                </div>
                <div class="aspect-video bg-surface border border-hairline rounded-md relative flex items-center justify-center overflow-hidden group">
                  <Image class="w-5 h-5 text-ink-muted group-hover:scale-110 transition-transform" stroke-width="1.5" />
                  <div class="absolute bottom-1 left-1.5 bg-surface/80 px-1.5 py-0.5 rounded text-[8px] text-ink">Laje concretada</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
      </div>
    </section>

    <!-- CUSTOMER MARQUEE / LOGOS -->
    <section class="reveal border-y border-hairline bg-surface py-8 px-6 overflow-hidden">
      <div class="max-w-[1280px] mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <span class="text-[12px] font-medium text-ink-muted tracking-[0.4px] uppercase font-sans whitespace-nowrap">
          CONFIADO POR CONSTRUTORAS INOVADORAS EM TODO O BRASIL
        </span>
        <div class="flex items-center gap-8 md:gap-12 flex-wrap justify-center opacity-45 hover:opacity-75 transition-opacity duration-300">
          <span class="text-sm font-semibold tracking-[-0.5px] font-sans text-ink-muted">BRADESCO OBRA</span>
          <span class="text-sm font-bold tracking-[2px] font-sans text-ink-muted">METROVAL</span>
          <span class="text-sm font-bold tracking-tight font-sans text-ink-muted">CAIXA IMÓVEIS</span>
          <span class="text-sm font-semibold font-sans text-ink-muted">MENDES & CO.</span>
          <span class="text-sm font-semibold font-mono tracking-tighter text-ink-muted">PLAN-ARQ</span>
        </div>
      </div>
    </section>

    <!-- LIVE ESTIMATOR SIMULATOR -->
    <section id="demo" class="reveal py-24 px-6 max-w-[1280px] mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <!-- Text Left -->
        <div class="lg:col-span-5 flex flex-col gap-4 text-left">
          <span class="text-[13px] font-medium text-brand-primary tracking-[0.4px] uppercase font-sans">SIMULADOR DE CUSTO SINAPI/CUB</span>
          <h2 class="text-[32px] md:text-[40px] font-semibold text-ink tracking-[-1.0px] leading-[1.15]">
            Estime seu orçamento em segundos.
          </h2>
          <p class="text-sm text-ink-muted leading-[1.5]">
            Escolha o padrão de construção e a área total da sua obra residencial para calcular uma estimativa física-financeira alinhada com as tabelas de referência regionais.
          </p>
          <div class="mt-4 flex flex-col gap-3">
            <div class="flex items-center gap-3">
              <CheckCircle2 class="w-[18px] h-[18px] text-brand-primary" stroke-width="1.5" />
              <span class="text-xs text-ink-muted">Cálculo baseado no CUB (Custo Unitário Básico)</span>
            </div>
            <div class="flex items-center gap-3">
              <CheckCircle2 class="w-[18px] h-[18px] text-brand-primary" stroke-width="1.5" />
              <span class="text-xs text-ink-muted">Fração de custos distribuída conforme curva ABC clássica</span>
            </div>
          </div>
        </div>

        <!-- Calculator Card Right -->
        <div class="lg:col-span-7 bg-surface border border-hairline rounded-lg p-6 md:p-8 flex flex-col gap-6 text-left relative overflow-hidden">
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Input Area -->
            <div class="flex flex-col gap-2">
              <label class="text-xs font-semibold text-ink-muted uppercase">Área Construída (m²)</label>
              <div class="relative">
                <input 
                  type="number" 
                  v-model.number="calcArea" 
                  min="30" 
                  max="10000"
                  class="w-full bg-canvas border border-hairline text-ink rounded-md py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all font-mono"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-ink-muted font-mono">m²</span>
              </div>
            </div>

            <!-- Select Standard -->
            <div class="flex flex-col gap-2">
              <label class="text-xs font-semibold text-ink-muted uppercase">Padrão da Obra</label>
              <div class="grid grid-cols-3 bg-canvas p-1 rounded-md border border-hairline">
                <button 
                  @click="calcStandard = 'baixo'"
                  :class="calcStandard === 'baixo' ? 'bg-brand-primary text-white' : 'bg-surface-hover text-ink-muted'"
                  class="py-1.5 text-xs font-medium rounded-md transition-all cursor-pointer"
                >
                  Baixo
                </button>
                <button 
                  @click="calcStandard = 'medio'"
                  :class="calcStandard === 'medio' ? 'bg-brand-primary text-white' : 'bg-surface-hover text-ink-muted'"
                  class="py-1.5 text-xs font-medium rounded-md transition-all cursor-pointer"
                >
                  Médio
                </button>
                <button 
                  @click="calcStandard = 'alto'"
                  :class="calcStandard === 'alto' ? 'bg-brand-primary text-white' : 'bg-surface-hover text-ink-muted'"
                  class="py-1.5 text-xs font-medium rounded-md transition-all cursor-pointer"
                >
                  Alto
                </button>
              </div>
            </div>
          </div>

          <!-- Divider -->
          <div class="h-[1px] bg-hairline"></div>

          <!-- Calculations Results -->
          <div class="flex flex-col gap-4">
            <div class="flex justify-between items-end">
              <div>
                <span class="text-xs text-ink-muted uppercase block">Custo Estimado Total</span>
                <span class="text-[28px] font-bold text-ink tracking-tight font-mono">R$ {{ formatNumber(estimatedTotal) }}</span>
              </div>
              <div class="text-right">
                <span class="text-[10px] text-ink-muted uppercase block">Valor Unitário</span>
                <span class="text-xs font-bold text-ink font-mono">R$ {{ formatNumber(unitCostValue) }} / m²</span>
              </div>
            </div>

            <!-- ABC Breakdown -->
            <div class="flex flex-col gap-2 mt-2">
              <span class="text-[10px] text-ink-muted uppercase tracking-wider font-semibold">Distribuição Estimada de Custos (PCI)</span>
              
              <div class="flex flex-col gap-2">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-ink-muted">Infraestrutura & Fundação (12%)</span>
                  <span class="font-mono text-ink font-semibold">R$ {{ formatNumber(estimatedTotal * 0.12) }}</span>
                </div>
                <div class="w-full h-1 bg-canvas rounded-full overflow-hidden">
                  <div class="h-full bg-brand-primary rounded-full" style="width: 12%"></div>
                </div>

                <div class="flex items-center justify-between text-xs">
                  <span class="text-ink-muted">Superestrutura & Alvenarias (40%)</span>
                  <span class="font-mono text-ink font-semibold">R$ {{ formatNumber(estimatedTotal * 0.40) }}</span>
                </div>
                <div class="w-full h-1 bg-canvas rounded-full overflow-hidden">
                  <div class="h-full bg-brand-primary rounded-full" style="width: 40%"></div>
                </div>

                <div class="flex items-center justify-between text-xs">
                  <span class="text-ink-muted">Instalações & Cobertura (18%)</span>
                  <span class="font-mono text-ink font-semibold">R$ {{ formatNumber(estimatedTotal * 0.18) }}</span>
                </div>
                <div class="w-full h-1 bg-canvas rounded-full overflow-hidden">
                  <div class="h-full bg-brand-primary rounded-full" style="width: 18%"></div>
                </div>

                <div class="flex items-center justify-between text-xs">
                  <span class="text-ink-muted">Acabamentos e Pintura (30%)</span>
                  <span class="font-mono text-ink font-semibold">R$ {{ formatNumber(estimatedTotal * 0.30) }}</span>
                </div>
                <div class="w-full h-1 bg-canvas rounded-full overflow-hidden">
                  <div class="h-full bg-brand-primary rounded-full" style="width: 30%"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Action inside Simulator -->
          <router-link to="/auth" class="w-full text-center py-2.5 bg-brand-primary hover:bg-brand-hover text-white rounded-md text-[13px] font-semibold transition-all duration-200 cursor-pointer block mt-2">
            Importar no Gerador de Planilhas
          </router-link>

        </div>
      </div>
    </section>

    <!-- PRODUCT FEATURES GRID -->
    <section id="features" class="reveal py-24 px-6 border-t border-hairline max-w-[1280px] mx-auto text-center">
      
      <!-- Section Header -->
      <div class="flex flex-col items-center gap-4 text-center max-w-[680px] mx-auto mb-16">
        <span class="text-[13px] font-medium text-brand-primary tracking-[0.4px] uppercase font-sans">EFICIÊNCIA TÉCNICA</span>
        <h2 class="text-[32px] md:text-[56px] font-semibold text-ink tracking-[-1.8px] leading-[1.10]">
          Construído para orçamentistas experientes.
        </h2>
        <p class="text-sm md:text-[16px] text-ink-muted leading-[1.5]">
          Deixe de lado planilhas Excel desatualizadas e integrações manuais lentas. O Vértice conecta a inteligência fiscal da engenharia civil a uma plataforma impecável.
        </p>
      </div>

      <!-- Feature Card Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Feature 1 -->
        <div class="bg-surface border border-hairline rounded-lg p-6 text-left flex flex-col gap-4 transition-all duration-200 hover:bg-surface-hover group">
          <div class="w-10 h-10 bg-brand-primary/10 rounded-md flex items-center justify-center border border-brand-primary/20 text-brand-primary group-hover:bg-brand-primary/20 transition-all">
            <RefreshCw class="w-5 h-5" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-semibold text-ink tracking-[-0.4px]">Tabela SINAPI Atualizada</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Sincronização mensal automática das tabelas SINAPI estaduais diretamente do banco de dados oficial da Caixa Econômica, sem downloads de arquivos.
          </p>
        </div>

        <!-- Feature 2 -->
        <div class="bg-surface border border-hairline rounded-lg p-6 text-left flex flex-col gap-4 transition-all duration-200 hover:bg-surface-hover group">
          <div class="w-10 h-10 bg-brand-primary/10 rounded-md flex items-center justify-center border border-brand-primary/20 text-brand-primary group-hover:bg-brand-primary/20 transition-all">
            <Calendar class="w-5 h-5" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-semibold text-ink tracking-[-0.4px]">Cronograma PCI Caixa</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Montagem da planilha de Proposta de Financiamento de forma integrada aos custos orçados, com geração automática do cronograma de parcelas e liberação.
          </p>
        </div>

        <!-- Feature 3 -->
        <div class="bg-surface border border-hairline rounded-lg p-6 text-left flex flex-col gap-4 transition-all duration-200 hover:bg-surface-hover group">
          <div class="w-10 h-10 bg-brand-primary/10 rounded-md flex items-center justify-center border border-brand-primary/20 text-brand-primary group-hover:bg-brand-primary/20 transition-all">
            <Users class="w-5 h-5" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-semibold text-ink tracking-[-0.4px]">Portal de Clientes Isolado</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Dê aos proprietários uma visão clara da evolução física da obra por meio de tokens de acesso dedicados, reduzindo ligações e e-mails de acompanhamento.
          </p>
        </div>

        <!-- Feature 4 -->
        <div class="bg-surface border border-hairline rounded-lg p-6 text-left flex flex-col gap-4 transition-all duration-200 hover:bg-surface-hover group">
          <div class="w-10 h-10 bg-brand-primary/10 rounded-md flex items-center justify-center border border-brand-primary/20 text-brand-primary group-hover:bg-brand-primary/20 transition-all">
            <FileText class="w-5 h-5" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-semibold text-ink tracking-[-0.4px]">Geração de Contratos</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Automatize o processo burocrático gerando propostas comerciais de engenharia civil e contratos jurídicos de prestação de serviços com as cláusulas necessárias.
          </p>
        </div>

        <!-- Feature 5 -->
        <div class="bg-surface border border-hairline rounded-lg p-6 text-left flex flex-col gap-4 transition-all duration-200 hover:bg-surface-hover group">
          <div class="w-10 h-10 bg-brand-primary/10 rounded-md flex items-center justify-center border border-brand-primary/20 text-brand-primary group-hover:bg-brand-primary/20 transition-all">
            <Wallet class="w-5 h-5" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-semibold text-ink tracking-[-0.4px]">Medições Real-Time</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Lance medições diretamente no canteiro de obras, anexe registros fotográficos das vistorias e controle o saldo restante de cada insumo orçado.
          </p>
        </div>

        <!-- Feature 6 -->
        <div class="bg-surface border border-hairline rounded-lg p-6 text-left flex flex-col gap-4 transition-all duration-200 hover:bg-surface-hover group">
          <div class="w-10 h-10 bg-brand-primary/10 rounded-md flex items-center justify-center border border-brand-primary/20 text-brand-primary group-hover:bg-brand-primary/20 transition-all">
            <Shield class="w-5 h-5" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-semibold text-ink tracking-[-0.4px]">Isolamento e Segurança B2B</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Seus orçamentos e dados de construtora totalmente isolados em arquitetura de tenant seguro, em conformidade com as diretrizes do banco de dados local.
          </p>
        </div>
      </div>
    </section>

    <!-- TESTIMONIAL PANEL -->
    <section class="reveal py-24 px-6 border-t border-hairline bg-canvas">
      <div class="max-w-[800px] mx-auto text-center flex flex-col gap-8 items-center">
        <!-- Quote icon -->
        <Quote class="w-10 h-10 text-brand-primary" stroke-width="1.5" />
        
        <p class="text-lg md:text-[20px] font-normal text-ink leading-[1.40] tracking-[-0.2px] italic">
          "A automatização do cronograma físico-financeiro e a integração direta com as planilhas da Caixa nos poupou semanas de retrabalho burocrático. O portal do cliente reduziu as ligações e as cobranças de status a zero. Um luxo de experiência para nossa construtora e clientes."
        </p>

        <!-- Avatar metadata -->
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-brand-primary/20 rounded-full flex items-center justify-center border border-brand-primary/40 font-bold text-xs text-brand-primary font-mono">
            MT
          </div>
          <div class="text-left">
            <span class="text-sm font-semibold text-ink block">Eng. Marcos Toledo</span>
            <span class="text-xs text-ink-muted block">Diretor de Obras — Toledo Incorporadora & Engenharia</span>
          </div>
        </div>
      </div>
    </section>

    <!-- PRICING TIERS SECTION -->
    <section id="pricing" class="reveal py-24 px-6 border-t border-hairline max-w-[1280px] mx-auto text-center">
      
      <!-- Section Header -->
      <div class="flex flex-col items-center gap-4 text-center max-w-[680px] mx-auto mb-16">
        <span class="text-[13px] font-medium text-brand-primary tracking-[0.4px] uppercase font-sans">PRICING TRANSPARENTE</span>
        <h2 class="text-[32px] md:text-[56px] font-semibold text-ink tracking-[-1.8px] leading-[1.10]">
          Planos sob medida para o seu negócio.
        </h2>
        <p class="text-sm text-ink-muted leading-[1.5]">
          Acesso ilimitado ao banco SINAPI estadual, com ferramentas de exportação automatizadas. Sem contratos de longo prazo, mude de plano quando quiser.
        </p>

        <!-- Monthly/Annual Toggle -->
        <div class="flex items-center bg-canvas p-1 rounded-full border border-hairline mt-6">
          <button 
            @click="billingCycle = 'monthly'" 
            :class="billingCycle === 'monthly' ? 'bg-surface text-ink border border-hairline' : 'text-ink-muted'"
            class="px-4 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer"
          >
            Faturamento Mensal
          </button>
          <button 
            @click="billingCycle = 'annual'" 
            :class="billingCycle === 'annual' ? 'bg-surface text-ink border border-hairline' : 'text-ink-muted'"
            class="px-4 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5"
          >
            Anual
            <span class="text-[9px] bg-brand-primary/20 text-brand-primary border border-brand-primary/30 px-1.5 py-0.5 rounded-full font-bold"> Economize 20%</span>
          </button>
        </div>
      </div>

      <!-- 3-Up Pricing Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-left max-w-[1080px] mx-auto">
        <!-- Plan 1: Essencial -->
        <div class="bg-surface border border-hairline rounded-lg p-6 flex flex-col justify-between hover:bg-surface-hover transition-all">
          <div>
            <span class="text-xs font-semibold text-ink-muted uppercase tracking-wider block mb-2">Essencial</span>
            <div class="flex items-baseline gap-1.5 mb-4">
              <span class="text-3xl font-bold text-ink font-mono">R$ {{ billingCycle === 'monthly' ? '149' : '119' }}</span>
              <span class="text-xs text-ink-muted font-sans">/ mês</span>
            </div>
            <p class="text-xs text-ink-muted mb-6 leading-[1.4]">
              Ideal para engenheiros autônomos ou construtores com demandas pontuais de orçamentação.
            </p>
            
            <div class="h-[1px] bg-hairline mb-6"></div>

            <ul class="flex flex-col gap-3 text-xs text-ink-muted">
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Até 3 obras ativas simultâneas
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Acesso total à tabela SINAPI estadual
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Geração de Cronograma Físico-Financeiro
              </li>
              <li class="flex items-center gap-2 opacity-50">
                <X class="w-4 h-4" stroke-width="1.5" />
                Portal do Cliente dedicado
              </li>
              <li class="flex items-center gap-2 opacity-50">
                <X class="w-4 h-4" stroke-width="1.5" />
                Contratos automatizados e propostas
              </li>
            </ul>
          </div>

          <router-link to="/auth" class="w-full text-center py-2.5 bg-canvas hover:bg-surface-hover text-ink border border-hairline rounded-md text-[13px] font-semibold transition-all duration-200 cursor-pointer mt-8 block">
            Começar Agora
          </router-link>
        </div>

        <!-- Plan 2: Profissional (Featured) -->
        <div class="bg-surface border-2 border-brand-primary rounded-lg p-6 flex flex-col justify-between relative overflow-hidden transition-all shadow-[0_0_30px_rgba(94,106,210,0.05)]">
          <div class="absolute top-3 right-3 bg-brand-primary/10 border border-brand-primary/30 px-2 py-0.5 rounded-full">
            <span class="text-[9px] text-brand-primary font-bold uppercase tracking-wider font-sans">RECOMENDADO</span>
          </div>

          <div>
            <span class="text-xs font-semibold text-brand-primary uppercase tracking-wider block mb-2">Profissional</span>
            <div class="flex items-baseline gap-1.5 mb-4">
              <span class="text-3xl font-bold text-ink font-mono">R$ {{ billingCycle === 'monthly' ? '299' : '239' }}</span>
              <span class="text-xs text-ink-muted font-sans">/ mês</span>
            </div>
            <p class="text-xs text-ink-muted mb-6 leading-[1.4]">
              Para construtoras em crescimento que necessitam de integração e transparência com clientes Caixa.
            </p>
            
            <div class="h-[1px] bg-hairline mb-6"></div>

            <ul class="flex flex-col gap-3 text-xs text-ink-muted">
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                <strong>Obras ilimitadas</strong>
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Acesso total às tabelas SINAPI (Todos Estados)
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Cronograma PCI e Físico-Financeiro Caixa
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                <strong>Portal do Cliente ilimitado</strong>
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Contratos automatizados ilimitados
              </li>
            </ul>
          </div>

          <router-link to="/auth" class="w-full text-center py-2.5 bg-brand-primary hover:bg-brand-hover text-white rounded-md text-[13px] font-semibold transition-all duration-200 cursor-pointer mt-8 block">
            Começar Teste Gratuito
          </router-link>
        </div>

        <!-- Plan 3: Corporativo -->
        <div class="bg-surface border border-hairline rounded-lg p-6 flex flex-col justify-between hover:bg-surface-hover transition-all">
          <div>
            <span class="text-xs font-semibold text-ink-muted uppercase tracking-wider block mb-2">Corporativo</span>
            <div class="flex items-baseline gap-1.5 mb-4">
              <span class="text-3xl font-bold text-ink">Sob Consulta</span>
            </div>
            <p class="text-xs text-ink-muted mb-6 leading-[1.4]">
              Ideal para incorporadoras e grandes construtoras com integrações ERP e necessidades customizadas.
            </p>
            
            <div class="h-[1px] bg-hairline mb-6"></div>

            <ul class="flex flex-col gap-3 text-xs text-ink-muted">
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Tudo do plano Profissional
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Múltiplos usuários e permissões de equipe
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Suporte dedicado via WhatsApp e SLA prioritário
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                Integrações via API customizada
              </li>
            </ul>
          </div>

          <a href="mailto:contato@vertice.com.br?subject=Plano Corporativo" class="w-full text-center py-2.5 bg-canvas hover:bg-surface-hover text-ink border border-hairline rounded-md text-[13px] font-semibold transition-all duration-200 cursor-pointer mt-8 block">
            Falar com Vendas
          </a>
        </div>
      </div>
    </section>

    <!-- CLOSING CTA BANNER -->
    <section class="reveal py-16 px-6 max-w-[1280px] mx-auto">
      <div class="bg-surface border border-hairline rounded-lg p-8 md:p-16 text-center flex flex-col items-center gap-6 relative overflow-hidden">
        <span class="text-[13px] font-medium text-brand-primary tracking-[0.4px] uppercase font-sans">COMECE HOJE</span>
        <h2 class="text-2xl md:text-[40px] font-semibold text-ink tracking-[-1.0px] leading-[1.15] max-w-[680px]">
          Simplifique o controle físico-financeiro de suas obras agora.
        </h2>
        <p class="text-xs md:text-sm text-ink-muted max-w-[500px] leading-[1.5]">
          Acesso instantâneo de 14 dias para teste do plano Profissional. Não requer cartão de crédito.
        </p>
        <router-link to="/auth" class="inline-flex items-center justify-center bg-brand-primary hover:bg-brand-hover text-white rounded-md text-[14px] font-medium px-6 py-3 transition-all duration-200 cursor-pointer mt-4">
          Criar Conta B2B
          <ArrowRight class="w-4 h-4 ml-2" stroke-width="1.5" />
        </router-link>
      </div>
    </section>

    <!-- DENSE TECHNICAL FOOTER -->
    <footer class="border-t border-hairline bg-canvas py-16 px-6 lg:px-12 max-w-[1280px] mx-auto text-left text-ink-muted">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
        <!-- Logo Column -->
        <div class="col-span-2 flex flex-col gap-4">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 bg-brand-primary/10 rounded-md border border-brand-primary/30 flex items-center justify-center">
              <Layers class="w-3.5 h-3.5 text-brand-primary" stroke-width="1.5" />
            </div>
            <span class="text-sm font-semibold text-ink">Vértice Engenharia</span>
          </div>
          <p class="text-xs text-ink-muted max-w-[240px] leading-[1.4]">
            Tecnologia focada em estruturação orçamentária e transparência de obras para engenheiros e construtoras civis B2B.
          </p>
        </div>

        <!-- Links Column 1: Produto -->
        <div class="flex flex-col gap-3 text-xs">
          <span class="font-bold text-ink tracking-wider uppercase mb-1">Produto</span>
          <a href="#features" class="hover:text-ink transition-colors">Funcionalidades</a>
          <a href="#demo" class="hover:text-ink transition-colors">Simulador</a>
          <a href="#pricing" class="hover:text-ink transition-colors">Preços</a>
          <span class="text-ink-muted">Changelog <span class="text-[8px] bg-canvas border border-hairline px-1 rounded-sm text-brand-primary font-mono ml-1">v1.0</span></span>
        </div>

        <!-- Links Column 2: Legal -->
        <div class="flex flex-col gap-3 text-xs">
          <span class="font-bold text-ink tracking-wider uppercase mb-1">Legal</span>
          <span class="text-ink-muted opacity-80">Termos de Uso</span>
          <span class="text-ink-muted opacity-80">Privacidade</span>
          <span class="text-ink-muted opacity-80">Segurança B2B</span>
          <span class="text-ink-muted opacity-80">Conformidade Caixa</span>
        </div>

        <!-- Links Column 3: Contato -->
        <div class="flex flex-col gap-3 text-xs">
          <span class="font-bold text-ink tracking-wider uppercase mb-1">Empresa</span>
          <span class="text-ink-muted opacity-80">Sobre Nós</span>
          <a href="mailto:contato@vertice.com.br" class="hover:text-ink transition-colors">Fale Conosco</a>
          <span class="text-ink-muted opacity-80">Suporte Técnico</span>
        </div>
      </div>

      <!-- Bottom Bar -->
      <div class="h-[1px] bg-hairline mb-8"></div>
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-ink-muted opacity-80">
        <span>&copy; 2026 Vértice Engenharia S/A. Todos os direitos reservados.</span>
        <div class="flex items-center gap-4">
          <span>Hospedado no Brasil</span>
          <span>&middot;</span>
          <span>Conexão Segura SSL</span>
        </div>
      </div>
    </footer>

    <!-- CLIENT PORTAL ACCESS MODAL -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="openClientModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
        <div 
          @click.stop 
          class="w-full max-w-md bg-surface border border-hairline rounded-lg p-6 relative overflow-hidden text-left"
        >
          <!-- Close button -->
          <button 
            @click="openClientModal = false" 
            class="absolute top-4 right-4 p-1.5 text-ink-muted hover:text-ink cursor-pointer flex items-center justify-center hover:bg-surface-hover rounded-md transition-all"
          >
            <X class="w-[18px] h-[18px]" stroke-width="1.5" />
          </button>

          <!-- Header -->
          <div class="flex items-center gap-3 mb-4">
            <div class="w-9 h-9 bg-brand-primary/10 rounded-md border border-brand-primary/30 flex items-center justify-center">
              <Users class="w-[18px] h-[18px] text-brand-primary" stroke-width="1.5" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-ink">Acesso ao Portal do Cliente</h3>
              <p class="text-xs text-ink-muted">Insira o código enviado pelo seu construtor.</p>
            </div>
          </div>

          <!-- Input Code Form -->
          <form @submit.prevent="submitClientCode" class="flex flex-col gap-4 mt-6">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-semibold text-ink-muted uppercase">Token da Obra (6+ caracteres)</label>
              <input 
                type="text" 
                v-model="clientToken" 
                placeholder="Ex: OB-8942-X" 
                required
                class="w-full bg-canvas border border-hairline text-ink rounded-md py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all font-mono tracking-widest text-center"
              />
            </div>

            <!-- Error message if needed -->
            <p v-if="clientTokenError" class="text-xs text-red-500 font-medium">
              {{ clientTokenError }}
            </p>

            <button 
              type="submit" 
              class="w-full py-2.5 bg-brand-primary hover:bg-brand-hover text-white rounded-md text-sm font-semibold transition-all duration-200 cursor-pointer flex items-center justify-center gap-2"
            >
              <span>Acessar Portal da Obra</span>
              <ArrowRight class="w-4 h-4" stroke-width="1.5" />
            </button>
          </form>
        </div>
      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../supabase'
import { isDark, toggleTheme } from '../composables/useTheme'
import { Layers, Sun, Moon, Menu, X, ArrowRight, ArrowUpRight, DollarSign, Calendar, Users, CheckCircle2, Image, RefreshCw, FileText, Wallet, Shield, Quote, Check } from 'lucide-vue-next'

const router = useRouter()

// Header states
const hasSession = ref(false)
const mobileMenuOpen = ref(false)

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

// Check session & Setup Scroll reveal observer
onMounted(async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession()
    hasSession.value = !!session
  } catch (error) {
    hasSession.value = false
  }

  // Scroll Reveal Observer
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed')
      }
    })
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' })

  document.querySelectorAll('.reveal').forEach((el) => {
    observer.observe(el)
  })
})

// Interactive Mockup state
const activeMockupTab = ref('orcamento')

// Interactive Calculator state
const calcArea = ref(120)
const calcStandard = ref('medio')

// Prices standard per standard standards
const CUB_PRICES = {
  baixo: 1650,
  medio: 2100,
  alto: 2950
}

const unitCostValue = computed(() => {
  return CUB_PRICES[calcStandard.value] || CUB_PRICES.medio
})

const estimatedTotal = computed(() => {
  const area = typeof calcArea.value === 'number' ? calcArea.value : 0
  return area * unitCostValue.value
})

const formatNumber = (val) => {
  if (isNaN(val)) return '0,00'
  return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val)
}

// Pricing billing cycle
const billingCycle = ref('monthly')

// Client Access Token Modal
const openClientModal = ref(false)
const clientToken = ref('')
const clientTokenError = ref('')

const submitClientCode = () => {
  clientTokenError.value = ''
  const token = clientToken.value.trim()
  
  if (token.length < 4) {
    clientTokenError.value = 'Por favor, insira um token válido com pelo menos 4 caracteres.'
    return
  }

  // Redirect client to portal /portal/:token
  router.push(`/portal/${encodeURIComponent(token)}`)
  openClientModal.value = false
}
</script>

<style scoped>
/* Custom animations & smooth styling fallback */
@keyframes blurInUp {
  from {
    opacity: 0;
    transform: translateY(24px);
    filter: blur(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
}

.animate-blur-in-up {
  animation: blurInUp 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  opacity: 0; /* Pre-animation state */
}

/* Delays for Staggered Animations */
.delay-100 {
  animation-delay: 100ms;
}
.delay-200 {
  animation-delay: 200ms;
}
.delay-300 {
  animation-delay: 300ms;
}
.delay-400 {
  animation-delay: 400ms;
}
.delay-500 {
  animation-delay: 500ms;
}

/* Scroll Reveal animation style */
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.reveal.revealed {
  opacity: 1;
  transform: translateY(0);
}

/* Hide spin-buttons for number inputs */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
</style>
