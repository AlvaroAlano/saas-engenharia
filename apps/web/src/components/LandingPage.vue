<template>
  <div class="min-h-screen bg-canvas text-ink font-sans antialiased overflow-x-hidden selection:bg-brand-blue/30 selection:text-white transition-colors duration-200">
    
    <!-- HEADER / NAVIGATION (Adaptive Minimalist) -->
    <header class="sticky top-0 z-50 w-full h-[56px] bg-surface/80 backdrop-blur-md border-b border-hairline transition-all duration-300 flex items-center">
      <div class="w-full max-w-[1280px] mx-auto px-6 flex items-center justify-between">
        <!-- Left: Logo & Wordmark -->
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-brand-blue/10 rounded-md border border-brand-blue/35 flex items-center justify-center text-brand-blue">
            <Layers class="w-5 h-5" stroke-width="1.5" />
          </div>
          <span class="text-[18px] font-bold text-ink tracking-[-0.4px]">Vértice</span>
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
              class="p-2 min-h-[44px] min-w-[44px] text-ink-muted hover:text-ink hover:bg-surface-hover rounded-md transition-all cursor-pointer flex items-center justify-center focus:outline-none"
              title="Alternar Tema"
            >
              <Sun v-if="isDark" class="w-5 h-5" stroke-width="1.5" />
              <Moon v-else class="w-5 h-5" stroke-width="1.5" />
            </button>

            <!-- Client Portal Access -->
            <button 
              @click="openClientModal = true" 
              class="hidden md:inline-flex items-center justify-center bg-surface hover:bg-surface-hover text-ink border border-hairline rounded-md text-[13px] font-medium px-4 py-2 transition-all duration-200 cursor-pointer"
            >
              Acesso Cliente
            </button>
            
            <!-- Builder Access -->
            <router-link 
              v-if="hasSession" 
              to="/dashboard" 
              class="hidden md:inline-flex items-center justify-center bg-brand-blue hover:bg-brand-blue-hover text-white rounded-md text-[13px] font-bold px-4 py-2 transition-all duration-200 cursor-pointer focus:outline-none border-none"
            >
              Entrar no Painel
            </router-link>
            <router-link 
              v-else 
              to="/auth" 
              class="hidden md:inline-flex items-center justify-center bg-brand-blue hover:bg-brand-blue-hover text-white rounded-md text-[13px] font-bold px-4 py-2 transition-all duration-200 cursor-pointer focus:outline-none border-none"
            >
              Acesso Construtor
            </router-link>

            <!-- Mobile Menu Trigger -->
            <button @click="toggleMobileMenu" class="md:hidden p-2 min-h-[44px] min-w-[44px] text-ink-muted hover:text-ink cursor-pointer flex items-center justify-center focus:outline-none">
              <transition mode="out-in" name="rotate-fade">
                <X v-if="mobileMenuOpen" class="w-5 h-5" stroke-width="1.5" />
                <Menu v-else class="w-5 h-5" stroke-width="1.5" />
              </transition>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- BACKDROP PARA MENU MOBILE (Fundo Fosco) -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div 
        v-if="mobileMenuOpen" 
        @click="mobileMenuOpen = false" 
        class="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
      ></div>
    </transition>

    <!-- MOBILE MENU OVERLAY (Card Flutuante Centralizado) -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 scale-95 translate-y-[-8px]"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 translate-y-[-8px]"
    >
      <div v-if="mobileMenuOpen" class="fixed top-20 inset-x-4 max-w-sm mx-auto bg-surface border border-hairline rounded-2xl shadow-2xl p-6 z-50 md:hidden flex flex-col gap-4">
        <a href="#features" @click="mobileMenuOpen = false" class="text-ink-muted hover:text-ink py-2.5 min-h-[44px] flex items-center text-sm font-medium border-b border-hairline/60">Funcionalidades</a>
        <a href="#demo" @click="mobileMenuOpen = false" class="text-ink-muted hover:text-ink py-2.5 min-h-[44px] flex items-center text-sm font-medium border-b border-hairline/60">Simulador</a>
        <a href="#workflow" @click="mobileMenuOpen = false" class="text-ink-muted hover:text-ink py-2.5 min-h-[44px] flex items-center text-sm font-medium border-b border-hairline/60">Como Funciona</a>
        <a href="#pricing" @click="mobileMenuOpen = false" class="text-ink-muted hover:text-ink py-2.5 min-h-[44px] flex items-center text-sm font-medium">Preços</a>
        <div class="h-[1px] bg-hairline my-1"></div>
        <button 
          @click="openClientModal = true; mobileMenuOpen = false" 
          class="w-full text-center py-3 min-h-[44px] flex items-center justify-center bg-canvas border border-hairline text-ink hover:bg-surface-hover rounded-md text-sm font-medium cursor-pointer"
        >
          Acesso Cliente
        </button>
        <router-link 
          v-if="hasSession" 
          to="/dashboard" 
          @click="mobileMenuOpen = false" 
          class="w-full text-center py-3 min-h-[44px] flex items-center justify-center bg-brand-blue hover:bg-brand-blue-hover text-white rounded-md text-sm font-bold cursor-pointer block border-none"
        >
          Entrar no Painel
        </router-link>
        <router-link 
          v-else 
          to="/auth" 
          @click="mobileMenuOpen = false" 
          class="w-full text-center py-3 min-h-[44px] flex items-center justify-center bg-brand-orange hover:bg-brand-orange-hover text-neutral-950 rounded-md text-sm font-bold cursor-pointer block border-none"
        >
          Acesso Construtor
        </router-link>
      </div>
    </transition>

    <!-- HERO SECTION (Matte & Solid aesthetics without neon glows) -->
    <section class="w-full bg-gradient-to-b from-canvas via-canvas to-surface/40 relative overflow-hidden pt-20 pb-16 md:pt-32 md:pb-24 border-b border-hairline">
      
      <div class="relative z-10 flex flex-col px-6 max-w-[1280px] mx-auto">
        
        <!-- Hero Content: Text & CTA -->
        <div class="flex flex-col lg:flex-row lg:items-end justify-between gap-8 mb-16">
          
          <!-- Left: Headline and description -->
          <div class="flex flex-col items-start text-left max-w-[720px]">
            <!-- Announcement Chip -->
            <div class="inline-flex items-center gap-2 px-3 py-1 bg-brand-blue/[0.03] border border-brand-blue/15 rounded-full mb-6 animate-blur-in-up">
              <span class="w-1.5 h-1.5 bg-brand-orange rounded-full animate-pulse"></span>
              <span class="text-[11px] font-bold text-ink-muted tracking-wider font-mono uppercase">VÉRTICE 1.0 — O MOTOR DE CRESCIMENTO B2B2C PARA SUA CONSTRUTORA</span>
            </div>

            <!-- Main Headline -->
            <h1 class="text-[28px] sm:text-[36px] md:text-[64px] font-black text-ink leading-[1.05] tracking-[-1.5px] md:tracking-[-2.5px] mb-6 animate-blur-in-up delay-100">
              Da Captação de Clientes ao Canteiro de Obras.
            </h1>

            <!-- Subheadline -->
            <p class="text-[15px] md:text-[17px] text-ink-muted leading-[1.6] font-sans animate-blur-in-up delay-200 max-w-[650px]">
              O Vértice é o marketplace e motor de gestão B2B2C definitivo para construtoras e engenheiros Caixa. Permita que clientes finais encontrem seu perfil por estado na Vitrine do Construtor, gere e assine contratos automatizados via ZapSign, monte orçamentos SINAPI em minutos e garanta transparência absoluta com o Portal do Cliente B2C.
            </p>
          </div>

          <!-- Right: CTA Buttons -->
          <div class="flex flex-col sm:flex-row items-center gap-4 animate-blur-in-up delay-300 shrink-0">
            <a href="#demo" class="w-full sm:w-auto min-h-[44px] inline-flex items-center justify-center bg-surface hover:bg-surface-hover dark:bg-transparent text-ink border border-hairline rounded-md text-[14px] font-medium px-6 py-3 transition-all duration-200 cursor-pointer">
              Simular Custos
            </a>
            <router-link to="/auth" class="w-full sm:w-auto min-h-[44px] inline-flex items-center justify-center bg-brand-orange hover:bg-brand-orange-hover text-neutral-950 border border-transparent rounded-md text-[14px] font-bold px-6 py-3 transition-all duration-200 cursor-pointer focus:outline-none">
              Começar Grátis
              <ArrowRight class="w-4 h-4 ml-2" stroke-width="2" />
            </router-link>
          </div>

        </div>

        <!-- Interactive Product UI Panel (Screenshot Mockup) -->
        <div class="w-full bg-gradient-to-b from-surface to-brand-blue/[0.015] border border-hairline/80 shadow-md rounded-xl p-4 md:p-6 text-left relative overflow-hidden transition-all duration-300 animate-blur-in-up delay-400">
        
          <!-- Chrome Navigation / Tabs -->
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-hairline pb-4 mb-6">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-neutral-300"></span>
              <span class="w-2.5 h-2.5 rounded-full bg-neutral-300"></span>
              <span class="w-2.5 h-2.5 rounded-full bg-neutral-300"></span>
              <span class="text-xs text-ink-muted ml-2 font-mono">vertice.app/dashboard/bella-vista</span>
            </div>

            <!-- Tabs Toggles -->
            <div class="flex items-center bg-canvas p-1 rounded-lg border border-hairline self-start md:self-auto flex-wrap gap-1">
              <button 
                @click="activeMockupTab = 'kanban'" 
                :class="activeMockupTab === 'kanban' ? 'bg-surface text-ink border border-hairline ' : 'text-ink-muted hover:text-ink border border-transparent'"
                class="min-h-[44px] md:min-h-0 px-3 py-2 md:py-1.5 rounded-md text-xs font-semibold transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
              >
                <Layers class="w-3.5 h-3.5 text-brand-blue" stroke-width="2" />
                CRM & Vitrine
              </button>
              <button 
                @click="activeMockupTab = 'contrato'" 
                :class="activeMockupTab === 'contrato' ? 'bg-surface text-ink border border-hairline ' : 'text-ink-muted hover:text-ink border border-transparent'"
                class="min-h-[44px] md:min-h-0 px-3 py-2 md:py-1.5 rounded-md text-xs font-semibold transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
              >
                <FileText class="w-3.5 h-3.5 text-brand-orange" stroke-width="2" />
                Contratos
              </button>
              <button 
                @click="activeMockupTab = 'portal'" 
                :class="activeMockupTab === 'portal' ? 'bg-surface text-ink border border-hairline ' : 'text-ink-muted hover:text-ink border border-transparent'"
                class="min-h-[44px] md:min-h-0 px-3 py-2 md:py-1.5 rounded-md text-xs font-semibold transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
              >
                <Users class="w-3.5 h-3.5 text-brand-blue" stroke-width="2" />
                Portal do Cliente
              </button>
            </div>
          </div>

          <!-- Tab Content 1: KANBAN & LEADS (Visão do Engenheiro) -->
          <div v-if="activeMockupTab === 'kanban'" class="animate-fade-in flex flex-row overflow-x-auto md:grid md:grid-cols-3 gap-6 snap-x snap-mandatory pb-4 scrollbar-none">
            <!-- Coluna 1: Leads do Marketplace -->
            <div class="bg-canvas border border-hairline rounded-lg p-4 flex flex-col gap-4 w-[280px] shrink-0 snap-align-start md:w-auto">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Leads do Marketplace</span>
                <span class="w-2 h-2 rounded-full bg-brand-orange animate-pulse"></span>
              </div>
              
              <!-- Card de Lead MCMV -->
              <div class="bg-surface border border-hairline rounded-lg p-3.5 flex flex-col gap-3 shadow-sm hover:border-brand-orange/30 transition-all">
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <h4 class="text-xs font-bold text-ink">Ana Souza</h4>
                    <span class="text-[10px] text-ink-muted flex items-center gap-1 mt-0.5">
                      <MapPin class="w-3 h-3 text-brand-orange" />
                      Campinas, SP
                    </span>
                  </div>
                  <span class="text-[9px] bg-brand-orange/10 text-brand-orange border border-brand-orange/20 px-2 py-0.5 rounded font-bold font-mono">NOVO LEAD</span>
                </div>
                <p class="text-[11px] text-ink-muted leading-relaxed">
                  Busca construtor homologado Caixa para projeto MCMV de 110m² no terreno próprio.
                </p>
                <div class="h-[1px] bg-hairline"></div>
                <div class="flex items-center justify-between text-[10px]">
                  <span class="text-ink-muted">Orçamento preliminar</span>
                  <span class="font-bold text-brand-orange font-mono">R$ 231.000,00</span>
                </div>
                <button class="w-full min-h-[44px] flex items-center justify-center text-center py-2.5 bg-brand-orange hover:bg-brand-orange-hover text-neutral-950 text-xs font-bold rounded transition-colors cursor-pointer border-none">
                  Aceitar & Iniciar Obra
                </button>
              </div>
            </div>

            <!-- Coluna 2: Orçamento SINAPI -->
            <div class="bg-canvas border border-hairline rounded-lg p-4 flex flex-col gap-4 w-[280px] shrink-0 snap-align-start md:w-auto">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Orçamento SINAPI</span>
                <span class="w-2 h-2 rounded-full bg-brand-blue"></span>
              </div>
              
              <!-- Card de Orçamento -->
              <div class="bg-surface border border-hairline rounded-lg p-3.5 flex flex-col gap-3 shadow-sm hover:border-brand-blue/30 transition-all">
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <h4 class="text-xs font-bold text-ink">Residencial Bella Vista</h4>
                    <span class="text-[10px] text-ink-muted flex items-center gap-1 mt-0.5">
                      <Calendar class="w-3 h-3 text-brand-blue" />
                      Médio Padrão - 120m²
                    </span>
                  </div>
                  <span class="text-[9px] bg-brand-blue/10 text-brand-blue border border-brand-blue/20 px-2 py-0.5 rounded font-bold font-mono">SP / MAIO</span>
                </div>
                <div class="flex items-center gap-1.5 bg-canvas border border-hairline p-2 rounded text-[10px] text-brand-blue font-mono font-semibold">
                  <RefreshCw class="w-3.5 h-3.5 animate-spin" />
                  SINAPI sincronizado com desoneração
                </div>
                <div class="h-[1px] bg-hairline"></div>
                <div class="flex items-center justify-between text-[10px]">
                  <span class="text-ink-muted">Custo Total de Insumos</span>
                  <span class="font-bold text-brand-blue font-mono">R$ 252.000,00</span>
                </div>
              </div>
            </div>

            <!-- Coluna 3: Contrato ZapSign -->
            <div class="bg-canvas border border-hairline rounded-lg p-4 flex flex-col gap-4 w-[280px] shrink-0 snap-align-start md:w-auto">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Contrato ZapSign</span>
                <span class="w-2 h-2 rounded-full bg-green-500"></span>
              </div>
              
              <!-- Card de Contrato -->
              <div class="bg-surface border border-hairline rounded-lg p-3.5 flex flex-col gap-3 shadow-sm hover:border-green-500/30 transition-all">
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <h4 class="text-xs font-bold text-ink">Contrato - Bella Vista</h4>
                    <span class="text-[10px] text-ink-muted flex items-center gap-1 mt-0.5">
                      <FileText class="w-3 h-3 text-green-500" />
                      PDF assinado digitalmente
                    </span>
                  </div>
                  <span class="text-[9px] bg-green-500/10 text-green-600 border border-green-500/20 px-2 py-0.5 rounded font-bold font-mono">ZAPSIGN</span>
                </div>
                <p class="text-[11px] text-ink-muted leading-relaxed">
                  Contrato de serviço e cronograma físico-financeiro assinados e homologados Caixa.
                </p>
                <div class="h-[1px] bg-hairline"></div>
                <div class="flex items-center justify-between text-[10px]">
                  <span class="text-ink-muted">Status do Contrato</span>
                  <span class="font-bold text-green-600 flex items-center gap-1">
                    <CheckCircle2 class="w-3.5 h-3.5" />
                    Concluído
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab Content 2: CONTRATOS & ASSINATURAS (Automação) -->
          <div v-if="activeMockupTab === 'contrato'" class="animate-fade-in grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- PDF Preview -->
            <div class="lg:col-span-8 bg-canvas border border-hairline rounded-lg p-5 flex flex-col justify-between min-h-[320px] relative overflow-hidden">
              <div class="flex flex-col gap-3">
                <div class="flex items-center justify-between border-b border-hairline pb-3">
                  <span class="text-[10px] font-bold text-brand-blue uppercase tracking-wider font-mono">Visualizador de Documentos Vértice</span>
                  <span class="text-[9px] bg-brand-orange/10 text-brand-orange px-2 py-0.5 rounded font-mono font-bold">PDF WHITE-LABEL</span>
                </div>
                
                <div class="space-y-3 mt-2">
                  <h3 class="text-xs font-bold text-ink uppercase tracking-wide">CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE ENGENHARIA CIVIL B2B2C</h3>
                  <p class="text-[10px] text-ink-muted leading-relaxed font-sans max-h-[140px] overflow-y-auto font-mono">
                    <strong>Cláusula Primeira:</strong> O presente instrumento tem por objeto a prestação de serviços de engenharia civil para a execução da obra residencial com base nas diretrizes físicas e financeiras da planilha PCI da Caixa Econômica Federal.
                    <br/><br/>
                    <strong>Cláusula Segunda:</strong> A construtora obriga-se a disponibilizar canal de transparência e vistoria periódica fotográfica por meio do Portal do Cliente do Vértice...
                  </p>
                </div>
              </div>
              
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-6 pt-3 border-t border-hairline">
                <div class="flex items-center gap-2">
                  <span class="w-2.5 h-2.5 rounded-full bg-brand-orange animate-pulse"></span>
                  <span class="text-[10px] text-ink-muted">Aguardando assinatura do cliente</span>
                </div>
                <button class="bg-brand-orange hover:bg-brand-orange-hover text-neutral-950 font-bold min-h-[44px] py-2.5 px-4 rounded text-xs transition-all cursor-pointer border-none flex items-center justify-center gap-1.5 shadow-sm">
                  <FileText class="w-3.5 h-3.5" />
                  Assinar via ZapSign
                </button>
              </div>
            </div>

            <!-- Webhook status panel -->
            <div class="lg:col-span-4 bg-canvas border border-hairline rounded-lg p-5 flex flex-col gap-5 text-left justify-between">
              <div class="flex flex-col gap-4">
                <span class="text-[10px] font-bold text-ink-muted uppercase tracking-wider block">Fluxo da Automação Legal</span>
                
                <div class="flex flex-col gap-4">
                  <!-- Status 1 -->
                  <div class="flex gap-3">
                    <div class="w-5 h-5 rounded-full bg-brand-blue/15 border border-brand-blue/35 text-brand-blue flex items-center justify-center font-mono font-bold text-[10px] shrink-0">
                      ✓
                    </div>
                    <div>
                      <h4 class="text-xs font-bold text-brand-blue">Contrato Configurado</h4>
                      <p class="text-[10px] text-ink-muted mt-0.5">
                        Variáveis dinâmicas de valores SINAPI e dados do cliente integradas automaticamente.
                      </p>
                    </div>
                  </div>

                  <!-- Status 2 -->
                  <div class="flex gap-3">
                    <div class="w-5 h-5 rounded-full bg-brand-orange/15 border border-brand-orange/35 text-brand-orange flex items-center justify-center font-mono font-bold text-[10px] shrink-0">
                      !
                    </div>
                    <div>
                      <h4 class="text-xs font-bold text-brand-orange">Aguardando Assinatura</h4>
                      <p class="text-[10px] text-ink-muted mt-0.5">
                        Link de assinatura enviado via WhatsApp automático para o proprietário.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="border-t border-hairline pt-3 mt-2 text-[10px] text-ink-muted font-mono leading-relaxed">
                ⚡ Webhook ZapSign integrado: status sincronizado em tempo real.
              </div>
            </div>
          </div>

          <!-- Tab Content 3: PORTAL DO CLIENTE (Visão do Proprietário) -->
          <div v-if="activeMockupTab === 'portal'" class="animate-fade-in grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Portal Content Left -->
            <div class="lg:col-span-8 flex flex-col gap-5">
              <!-- Caixômetro panel -->
              <div class="bg-canvas border border-hairline rounded-lg p-5 flex flex-col gap-3">
                <div class="flex justify-between items-center text-[11px] text-ink-muted">
                  <span class="font-bold flex items-center gap-1">
                    <Building2 class="w-3.5 h-3.5 text-brand-blue" />
                    Liberação de Recursos (Caixa Econômica) - Caixômetro
                  </span>
                  <span class="font-mono font-semibold text-brand-blue">64,2% Liberado</span>
                </div>
                
                <!-- Progress bar -->
                <div class="w-full h-3 bg-surface-hover rounded-full overflow-hidden border border-hairline">
                  <div class="h-full bg-brand-blue rounded-full transition-all duration-500" style="width: 64.2%"></div>
                </div>
                
                <p class="text-[10px] text-ink-muted leading-relaxed">
                  Etapa 3 de 5 concluída. Próxima medição física agendada para liberação de mais R$ 48.200,00.
                </p>
              </div>

              <!-- Gallery of recent construction photos -->
              <div class="bg-canvas border border-hairline rounded-lg p-4 flex flex-col gap-3 text-xs">
                <span class="font-bold text-ink block">Vistorias Fotográficas Recentes</span>
                <div class="grid grid-cols-3 gap-3">
                  <div class="aspect-video bg-surface rounded border border-hairline flex flex-col items-center justify-center p-2 text-center group hover:border-brand-blue/30 transition-all">
                    <span class="text-[9px] text-brand-blue font-bold uppercase block tracking-wider">Etapa 1: Fundação</span>
                    <span class="text-[8px] text-ink-muted mt-1 font-mono">100% Concluído</span>
                  </div>
                  <div class="aspect-video bg-surface rounded border border-hairline flex flex-col items-center justify-center p-2 text-center group hover:border-brand-blue/30 transition-all">
                    <span class="text-[9px] text-brand-blue font-bold uppercase block tracking-wider">Etapa 2: Lajes</span>
                    <span class="text-[8px] text-ink-muted mt-1 font-mono">100% Concluído</span>
                  </div>
                  <div class="aspect-video bg-surface rounded border border-hairline flex flex-col items-center justify-center p-2 text-center group hover:border-brand-orange/30 transition-all">
                    <span class="text-[9px] text-brand-orange font-bold uppercase block tracking-wider">Etapa 3: Alvenaria</span>
                    <span class="text-[8px] text-ink-muted mt-1 font-mono">Em Andamento</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Profile right (Vitrine) -->
            <div class="lg:col-span-4 bg-canvas border border-hairline rounded-lg p-5 flex flex-col items-center justify-between text-center min-h-[300px]">
              <div class="flex flex-col items-center gap-3">
                <!-- Profile image placeholder -->
                <div class="w-14 h-14 bg-brand-blue/10 rounded-full border border-brand-blue/20 flex items-center justify-center text-brand-blue text-lg font-bold font-mono">
                  MT
                </div>
                <div>
                  <h4 class="text-sm font-bold text-ink">Eng. Marcos Toledo</h4>
                  <span class="text-[10px] text-ink-muted block mt-0.5">Toledo Construtora Ltda</span>
                </div>
                
                <!-- Rating badge -->
                <span class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-brand-orange/10 text-brand-orange border border-brand-orange/20 rounded-full text-[9px] font-bold font-mono uppercase tracking-wider">
                  <Star class="w-3 h-3 fill-brand-orange" />
                  Construtor Premium 5.0
                </span>
              </div>

              <div class="w-full flex flex-col gap-2 mt-4">
                <p class="text-[10px] text-ink-muted leading-relaxed">
                  15 obras concluídas e 4 ativas no estado de SP.
                </p>
                <button class="w-full min-h-[44px] flex items-center justify-center text-center py-2.5 bg-brand-blue hover:bg-brand-blue-hover text-white text-xs font-bold rounded transition-colors cursor-pointer border-none flex items-center gap-1 shadow-sm">
                  Visualizar Vitrine Pública
                  <ArrowUpRight class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- PROVA SOCIAL / INSTITUCIONAL -->
    <section class="border-y border-hairline bg-surface py-8 px-6 overflow-hidden">
      <div class="max-w-[1280px] mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <span class="text-[12px] font-bold text-ink-muted tracking-wider uppercase font-mono">
          ✓ Homologação e Conformidade Técnica
        </span>
        <div class="flex items-center gap-8 md:gap-12 flex-wrap justify-center text-xs text-ink-muted font-black tracking-widest font-mono">
          <span>CAIXA ECONÔMICA</span>
          <span>SINAPI INTEGRADO</span>
          <span>PCI & PFUI PADRÃO</span>
          <span>MODELO MULTI-TENANT</span>
        </div>
      </div>
    </section>

    <!-- LIVE ESTIMATOR SIMULATOR -->
    <section id="demo" class="reveal py-24 px-6 max-w-[1280px] mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <!-- Text Left -->
        <div class="lg:col-span-5 flex flex-col gap-4 text-left">
          <span class="text-[13px] font-bold text-brand-blue tracking-wider uppercase font-mono">SIMULADOR COMO LEAD MAGNET</span>
          <h2 class="text-[24px] sm:text-[32px] md:text-[40px] font-black text-ink tracking-[-1.0px] leading-[1.15]">
            Capture leads quentes com o seu próprio Simulador na sua Vitrine.
          </h2>
          <p class="text-sm text-ink-muted leading-[1.6]">
            Ofereça uma estimativa instantânea no seu perfil do Marketplace. O cliente simula o custo base da obra, e você recebe o lead pré-qualificado com metragem e padrão direto no seu Kanban.
          </p>
          <div class="mt-4 flex flex-col gap-3">
            <div class="flex items-center gap-3">
              <CheckCircle2 class="w-5 h-5 text-brand-blue" stroke-width="2" />
              <span class="text-xs text-ink">Cálculo paramétrico de alta precisão regional</span>
            </div>
            <div class="flex items-center gap-3">
              <CheckCircle2 class="w-5 h-5 text-brand-blue" stroke-width="2" />
              <span class="text-xs text-ink">Insumos orçamentários prontos para exportação</span>
            </div>
          </div>
        </div>

        <!-- Calculator Card Right (Matte) -->
        <div class="lg:col-span-7 bg-gradient-to-br from-surface to-brand-blue/[0.02] border border-hairline/90 shadow-md rounded-xl p-6 md:p-8 flex flex-col gap-6 text-left relative overflow-hidden">
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Input Area -->
            <div class="flex flex-col gap-2">
              <label class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Área Privativa (m²)</label>
              <div class="relative">
                <input 
                  type="number" 
                  v-model.number="calcArea" 
                  min="30" 
                  max="10000"
                  class="w-full bg-canvas border border-hairline dark:border-transparent text-ink rounded-md py-2.5 px-3 text-sm focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all font-mono font-medium"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-ink-muted font-mono font-medium">m²</span>
              </div>
            </div>

            <!-- Select Standard -->
            <div class="flex flex-col gap-2">
              <label class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Padrão de Acabamento</label>
              <div class="grid grid-cols-3 bg-canvas p-1 rounded-md border border-hairline">
                <button 
                  @click="calcStandard = 'baixo'"
                  :class="calcStandard === 'baixo' ? 'bg-brand-blue text-white font-bold' : 'text-ink-muted hover:text-ink'"
                  class="min-h-[44px] md:min-h-0 py-2 md:py-1.5 text-xs font-semibold rounded-md transition-all cursor-pointer border-none flex items-center justify-center"
                >
                  Baixo
                </button>
                <button 
                  @click="calcStandard = 'medio'"
                  :class="calcStandard === 'medio' ? 'bg-brand-blue text-white font-bold' : 'text-ink-muted hover:text-ink'"
                  class="min-h-[44px] md:min-h-0 py-2 md:py-1.5 text-xs font-semibold rounded-md transition-all cursor-pointer border-none flex items-center justify-center"
                >
                  Médio
                </button>
                <button 
                  @click="calcStandard = 'alto'"
                  :class="calcStandard === 'alto' ? 'bg-brand-blue text-white font-bold' : 'text-ink-muted hover:text-ink'"
                  class="min-h-[44px] md:min-h-0 py-2 md:py-1.5 text-xs font-semibold rounded-md transition-all cursor-pointer border-none flex items-center justify-center"
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
                <span class="text-[9px] text-ink-muted font-bold uppercase block">Custo Estimado de Obra</span>
                <span class="text-[28px] font-black text-ink tracking-tight font-mono font-medium">R$ {{ formatNumber(estimatedTotal) }}</span>
              </div>
              <div class="text-right">
                <span class="text-[9px] text-ink-muted font-bold uppercase block">Fator Médio</span>
                <span class="text-xs font-bold text-ink font-mono font-medium">R$ {{ formatNumber(unitCostValue) }} / m²</span>
              </div>
            </div>

            <!-- PCI ABC Breakdown -->
            <div class="flex flex-col gap-3.5 mt-2">
              <span class="text-[10px] text-ink-muted uppercase tracking-wider font-bold block">Fração Estimada por Etapa PCI</span>
              
              <div class="flex flex-col gap-3">
                <div class="space-y-1">
                  <div class="flex items-center justify-between text-xs text-ink-muted">
                    <span>Infraestrutura & Fundação (12%)</span>
                    <span class="font-mono text-ink font-bold font-medium font-medium">R$ {{ formatNumber(estimatedTotal * 0.12) }}</span>
                  </div>
                  <div class="w-full h-1.5 bg-canvas rounded-full overflow-hidden">
                    <div class="h-full bg-brand-blue" style="width: 12%"></div>
                  </div>
                </div>

                <div class="space-y-1">
                  <div class="flex items-center justify-between text-xs text-ink-muted">
                    <span>Superestrutura & Alvenarias (40%)</span>
                    <span class="font-mono text-ink font-bold font-medium font-medium">R$ {{ formatNumber(estimatedTotal * 0.40) }}</span>
                  </div>
                  <div class="w-full h-1.5 bg-canvas rounded-full overflow-hidden">
                    <div class="h-full bg-brand-blue" style="width: 40%"></div>
                  </div>
                </div>

                <div class="space-y-1">
                  <div class="flex items-center justify-between text-xs text-ink-muted">
                    <span>Instalações & Coberturas (18%)</span>
                    <span class="font-mono text-ink font-bold font-medium font-medium">R$ {{ formatNumber(estimatedTotal * 0.18) }}</span>
                  </div>
                  <div class="w-full h-1.5 bg-canvas rounded-full overflow-hidden">
                    <div class="h-full bg-brand-blue" style="width: 18%"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <router-link to="/auth" class="w-full min-h-[44px] flex items-center justify-center text-center py-2.5 bg-brand-blue hover:bg-brand-blue-hover text-white rounded-md text-[13px] font-bold transition-all duration-200 cursor-pointer mt-2 border-none">
            Importar no Gerador de Planilhas SINAPI
          </router-link>

        </div>
      </div>
    </section>

    <!-- PRODUCT FEATURES GRID -->
    <section id="features" class="reveal py-24 px-6 border-t border-hairline max-w-[1280px] mx-auto text-center">
      
      <!-- Section Header -->
      <div class="flex flex-col items-center gap-4 text-center max-w-[700px] mx-auto mb-16">
        <span class="text-[13px] font-bold text-brand-blue tracking-wider uppercase font-mono">DIFERENCIAIS TÉCNICOS</span>
        <h2 class="text-[24px] sm:text-[32px] md:text-[56px] font-black text-ink tracking-[-1.8px] leading-[1.10]">
          Sua engenharia livre de planilhas bagunçadas.
        </h2>
        <p class="text-sm md:text-[16px] text-ink-muted leading-[1.6]">
          Conecte a inteligência fiscal do SINAPI a uma ferramenta robusta e centralizada de orçamentos, contratos e portal do cliente de alto padrão.
        </p>
      </div>

      <!-- Feature Card Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Feature 1 -->
        <div class="bg-surface border border-hairline/80 rounded-xl p-6 text-left flex flex-col gap-4 transition-all duration-300 hover:bg-gradient-to-br hover:from-surface hover:to-brand-blue/[0.02] hover:-translate-y-1 hover:shadow-md hover:border-brand-blue/30 group">
          <div class="w-10 h-10 bg-brand-blue/10 rounded-md flex items-center justify-center border border-brand-blue/20 text-brand-blue group-hover:bg-brand-blue/20 transition-all">
            <RefreshCw class="w-5 h-5 transition-transform duration-300 group-hover:scale-110" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-bold text-ink tracking-[-0.4px]">Vitrine do Construtor</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            A "Vitrine do Construtor" permite que clientes de todo o país busquem profissionais e construtoras por estado. Seja encontrado facilmente pelo cliente final e receba leads pré-qualificados prontos para fechar contrato.
          </p>
        </div>

        <!-- Feature 2 -->
        <div class="bg-surface border border-hairline/80 rounded-xl p-6 text-left flex flex-col gap-4 transition-all duration-300 hover:bg-gradient-to-br hover:from-surface hover:to-brand-blue/[0.02] hover:-translate-y-1 hover:shadow-md hover:border-brand-blue/30 group">
          <div class="w-10 h-10 bg-brand-blue/10 rounded-md flex items-center justify-center border border-brand-blue/20 text-brand-blue group-hover:bg-brand-blue/20 transition-all">
            <Calendar class="w-5 h-5 transition-transform duration-300 group-hover:scale-110" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-bold text-ink tracking-[-0.4px]">SINAPI Nativa & Custos</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Sincronização automática e mensal de insumos e composições locais da Caixa. Monte orçamentos detalhados ou paramétricos em minutos, sem planilhas soltas.
          </p>
        </div>

        <!-- Feature 3 -->
        <div class="bg-surface border border-hairline/80 rounded-xl p-6 text-left flex flex-col gap-4 transition-all duration-300 hover:bg-gradient-to-br hover:from-surface hover:to-brand-blue/[0.02] hover:-translate-y-1 hover:shadow-md hover:border-brand-blue/30 group">
          <div class="w-10 h-10 bg-brand-blue/10 rounded-md flex items-center justify-center border border-brand-blue/20 text-brand-blue group-hover:bg-brand-blue/20 transition-all">
            <Users class="w-5 h-5 transition-transform duration-300 group-hover:scale-110" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-bold text-ink tracking-[-0.4px]">Contratos & Automação Legal</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Gere contratos robustos de forma automatizada e envie para assinatura digital via ZapSign direto no WhatsApp do cliente final, reduzindo a burocracia a zero.
          </p>
        </div>

        <!-- Feature 4 -->
        <div class="bg-surface border border-hairline/80 rounded-xl p-6 text-left flex flex-col gap-4 transition-all duration-300 hover:bg-gradient-to-br hover:from-surface hover:to-brand-blue/[0.02] hover:-translate-y-1 hover:shadow-md hover:border-brand-blue/30 group">
          <div class="w-10 h-10 bg-brand-blue/10 rounded-md flex items-center justify-center border border-brand-blue/20 text-brand-blue group-hover:bg-brand-blue/20 transition-all">
            <FileText class="w-5 h-5 transition-transform duration-300 group-hover:scale-110" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-bold text-ink tracking-[-0.4px]">Portal do Cliente B2C</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Destrave transparência total da obra para o cliente final B2C. Um portal interativo onde o proprietário acompanha diários, fotos de vistorias e o cronograma financeiro sem precisar mandar mensagens.
          </p>
        </div>

        <!-- Feature 5 -->
        <div class="bg-surface border border-hairline/80 rounded-xl p-6 text-left flex flex-col gap-4 transition-all duration-300 hover:bg-gradient-to-br hover:from-surface hover:to-brand-blue/[0.02] hover:-translate-y-1 hover:shadow-md hover:border-brand-blue/30 group">
          <div class="w-10 h-10 bg-brand-blue/10 rounded-md flex items-center justify-center border border-brand-blue/20 text-brand-blue group-hover:bg-brand-blue/20 transition-all">
            <Wallet class="w-5 h-5 transition-transform duration-300 group-hover:scale-110" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-bold text-ink tracking-[-0.4px]">O Caixômetro</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            O controle visual do cronograma de liberação da Caixa Econômica (PCI/PFUI). Visualize o progresso das etapas medidas e planeje as vistorias técnicas sem surpresas.
          </p>
        </div>

        <!-- Feature 6 -->
        <div class="bg-surface border border-hairline/80 rounded-xl p-6 text-left flex flex-col gap-4 transition-all duration-300 hover:bg-gradient-to-br hover:from-surface hover:to-brand-blue/[0.02] hover:-translate-y-1 hover:shadow-md hover:border-brand-blue/30 group">
          <div class="w-10 h-10 bg-brand-blue/10 rounded-md flex items-center justify-center border border-brand-blue/20 text-brand-blue group-hover:bg-brand-blue/20 transition-all">
            <Shield class="w-5 h-5 transition-transform duration-300 group-hover:scale-110" stroke-width="1.5" />
          </div>
          <h3 class="text-lg font-bold text-ink tracking-[-0.4px]">Segurança & RLS</h3>
          <p class="text-xs md:text-sm text-ink-muted leading-[1.5]">
            Seus dados protegidos por padrão. Leads, orçamentos e contratos protegidos pelo isolamento de segurança Postgres RLS de nível corporativo.
          </p>
        </div>
      </div>
    </section>

    <!-- TESTIMONIAL PANEL -->
    <section class="reveal py-16 px-6 border-t border-hairline bg-gradient-to-b from-canvas via-surface to-canvas">
      <div class="max-w-[800px] mx-auto text-center flex flex-col gap-8 items-center">
        <Quote class="w-10 h-10 text-brand-blue" stroke-width="1.5" />
        
        <p class="text-lg md:text-[20px] font-normal text-ink leading-[1.45] tracking-[-0.2px] italic">
          "A automatização das planilhas Caixa nos economizou semanas de retrabalho técnico. Com o Portal do Cliente, centralizamos as fotos do diário de obra e eliminamos as mensagens de status pelo WhatsApp. A experiência é de altíssimo padrão."
        </p>

        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-brand-blue/20 rounded-full flex items-center justify-center border border-brand-blue/35 font-bold text-xs text-brand-blue font-mono">
            MT
          </div>
          <div class="text-left">
            <span class="text-sm font-bold text-ink block">Eng. Marcos Toledo</span>
            <span class="text-xs text-ink-muted block font-sans">Diretor de Engenharia — Toledo Incorporadora</span>
          </div>
        </div>
      </div>
    </section>

    <!-- HOW IT WORKS (WORKFLOW) SECTION -->
    <section id="workflow" class="reveal py-16 px-6 border-t border-hairline bg-surface max-w-[1280px] mx-auto text-center">
      <div class="flex flex-col items-center gap-4 text-center max-w-[700px] mx-auto mb-16">
        <span class="text-[13px] font-bold text-brand-blue tracking-wider uppercase font-mono">FLUXO OPERACIONAL</span>
        <h2 class="text-[24px] sm:text-[32px] md:text-[56px] font-black text-ink tracking-[-1.8px] leading-[1.10]">
          Esteira de Produção da Obra.
        </h2>
        <p class="text-sm md:text-[16px] text-ink-muted leading-[1.6]">
          Desde a captação do lead no nosso marketplace até o canteiro de obras e a prestação de contas à Caixa Econômica, o Vértice centraliza cada etapa.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-8 max-w-[1100px] mx-auto text-left relative">
        <!-- Step 1 -->
        <div class="flex flex-col gap-4 relative">
          <div class="w-8 h-8 rounded-full bg-brand-blue/15 border border-brand-blue/35 text-brand-blue flex items-center justify-center font-mono font-bold text-sm">
            1
          </div>
          <h4 class="text-base font-bold text-ink">Vitrine & Leads</h4>
          <p class="text-xs text-ink-muted leading-[1.5]">
            O proprietário encontra seu perfil na Vitrine do Construtor, simula custos online e envia a documentação direto.
          </p>
        </div>

        <!-- Step 2 -->
        <div class="flex flex-col gap-4 relative">
          <div class="w-8 h-8 rounded-full bg-brand-blue/15 border border-brand-blue/35 text-brand-blue flex items-center justify-center font-mono font-bold text-sm">
            2
          </div>
          <h4 class="text-base font-bold text-ink">Orçamento SINAPI</h4>
          <p class="text-xs text-ink-muted leading-[1.5]">
            O engenheiro monta a EAP, sincroniza insumos mensais locais do SINAPI e exporta a planilha PCI oficial Caixa.
          </p>
        </div>

        <!-- Step 3 -->
        <div class="flex flex-col gap-4 relative">
          <div class="w-8 h-8 rounded-full bg-brand-blue/15 border border-brand-blue/35 text-brand-blue flex items-center justify-center font-mono font-bold text-sm">
            3
          </div>
          <h4 class="text-base font-bold text-ink">Automação de Contrato</h4>
          <p class="text-xs text-ink-muted leading-[1.5]">
            Gerador automático de propostas de serviço e minutas contratuais enviadas por ZapSign para assinatura digital instantânea.
          </p>
        </div>

        <!-- Step 4 -->
        <div class="flex flex-col gap-4 relative">
          <div class="w-8 h-8 rounded-full bg-brand-blue/15 border border-brand-blue/35 text-brand-blue flex items-center justify-center font-mono font-bold text-sm">
            4
          </div>
          <h4 class="text-base font-bold text-ink">Medição & Portal B2C</h4>
          <p class="text-xs text-ink-muted leading-[1.5]">
            Lançamento de diários fotográficos em tempo real e total transparência para o proprietário com o monitor do Caixômetro.
          </p>
        </div>
      </div>
    </section>

    <!-- PRICING TIERS SECTION -->
    <section id="pricing" class="reveal py-24 px-6 border-t border-hairline max-w-[1280px] mx-auto text-center">
      
      <!-- Section Header -->
      <div class="flex flex-col items-center gap-4 text-center max-w-[680px] mx-auto mb-12">
        <span class="text-[13px] font-bold text-brand-blue tracking-wider uppercase font-mono">PRICING TRANSPARENTE</span>
        <h2 class="text-[24px] sm:text-[32px] md:text-[56px] font-black text-ink tracking-[-1.8px] leading-[1.10]">
          Licenciamento B2B escalável.
        </h2>
        <p class="text-sm md:text-[16px] text-ink-muted leading-[1.5]">
          Acesso imediato de 14 dias para teste sem cartões ou compromisso. Cancele quando desejar.
        </p>
      </div>

      <!-- Billing Cycle Toggle -->
      <div class="flex items-center justify-center gap-3 mb-16">
        <span :class="billingCycle === 'monthly' ? 'text-ink font-bold' : 'text-ink-muted'" class="text-xs font-semibold tracking-wide uppercase transition-colors">Mensal</span>
        <button 
          @click="billingCycle = billingCycle === 'monthly' ? 'annual' : 'monthly'" 
          class="relative w-10 h-6 bg-canvas border border-hairline rounded-full p-0.5 cursor-pointer focus:outline-none transition-colors duration-200"
        >
          <div 
            :class="billingCycle === 'annual' ? 'translate-x-4 bg-brand-orange' : 'translate-x-0 bg-ink-muted'" 
            class="w-4 h-4 rounded-full transition-transform duration-200"
          ></div>
        </button>
        <span :class="billingCycle === 'annual' ? 'text-ink font-bold' : 'text-ink-muted'" class="text-xs font-semibold tracking-wide uppercase transition-colors flex items-center gap-1.5">
          Anual
          <span class="text-[9px] bg-brand-orange/10 border border-brand-orange/30 text-brand-orange px-1.5 py-0.5 rounded-md font-mono font-bold tracking-tight">Economize 20%</span>
        </span>
      </div>

      <!-- Pricing cards grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-[1100px] mx-auto text-left">
        <!-- Plan 1: Básico -->
        <div class="bg-surface border border-hairline/80 rounded-xl p-6 flex flex-col justify-between hover:bg-gradient-to-br hover:from-surface hover:to-brand-blue/[0.02] hover:-translate-y-1 hover:shadow-md hover:border-brand-blue/30 duration-300 group">
          <div>
            <span class="text-xs font-bold text-ink-muted uppercase tracking-wider block mb-2">Engenheiro Autônomo</span>
            <div class="flex items-baseline gap-1.5 mb-4">
              <span class="text-3xl font-bold text-ink font-mono">R$ {{ billingCycle === 'monthly' ? '149' : '119' }}</span>
              <span class="text-xs text-ink-muted">/ mês</span>
            </div>
            <p class="text-xs text-ink-muted mb-6 leading-[1.40]">
              Perfeito para engenheiros autônomos que realizam orçamentos pontuais e vistorias.
            </p>
            
            <div class="h-[1px] bg-hairline mb-6"></div>

            <ul class="flex flex-col gap-3 text-xs text-ink-muted">
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-blue" stroke-width="2" />
                Até 3 obras simultâneas
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-blue" stroke-width="2" />
                Tabela SINAPI (Seu Estado)
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-blue" stroke-width="2" />
                Cronogramas físico-financeiros Caixa
              </li>
            </ul>
          </div>

          <router-link to="/auth" class="w-full min-h-[44px] flex items-center justify-center text-center py-2.5 border border-hairline bg-transparent hover:bg-surface-hover text-ink rounded-md text-[13px] font-bold transition-all duration-200 cursor-pointer mt-8">
            Começar Agora
          </router-link>
        </div>

        <!-- Plan 2: Profissional (Destaque Laranja) -->
        <div class="bg-surface border border-brand-orange rounded-xl p-6 flex flex-col justify-between relative overflow-hidden">
          <div class="absolute top-0 right-0 bg-brand-orange text-neutral-950 text-[9px] font-black tracking-widest px-3 py-1 uppercase rounded-bl">Recomendado</div>
          <div>
            <span class="text-xs font-bold text-brand-orange uppercase tracking-wider block mb-2">Plano Construtora</span>
            <div class="flex items-baseline gap-1.5 mb-4">
              <span class="text-3xl font-bold text-ink font-mono">R$ {{ billingCycle === 'monthly' ? '299' : '239' }}</span>
              <span class="text-xs text-ink-muted">/ mês</span>
            </div>
            <p class="text-xs text-ink-muted mb-6 leading-[1.40]">
              Para equipes de construtoras que exigem automação, relatórios Caixa e portal do cliente completo.
            </p>
            
            <div class="h-[1px] bg-hairline mb-6"></div>

            <ul class="flex flex-col gap-3 text-xs text-ink-muted">
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-orange" stroke-width="2" />
                <strong>Obras ilimitadas</strong>
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-orange" stroke-width="2" />
                SINAPI de todos os estados do Brasil
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-orange" stroke-width="2" />
                <strong>Portal do Cliente ilimitado</strong>
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-orange" stroke-width="2" />
                Contratos e propostas automáticas
              </li>
            </ul>
          </div>

          <router-link to="/auth" class="w-full min-h-[44px] flex items-center justify-center text-center py-2.5 bg-brand-blue hover:bg-brand-blue-hover text-white rounded-md text-[13px] font-bold transition-all duration-200 cursor-pointer mt-8 border-none">
            Começar Grátis B2B
          </router-link>
        </div>

        <!-- Plan 3: Corporativo -->
        <div class="bg-surface border border-hairline/80 rounded-xl p-6 flex flex-col justify-between hover:bg-gradient-to-br hover:from-surface hover:to-brand-blue/[0.02] hover:-translate-y-1 hover:shadow-md hover:border-brand-blue/30 duration-300 group">
          <div>
            <span class="text-xs font-bold text-ink-muted uppercase tracking-wider block mb-2">Enterprise</span>
            <div class="flex items-baseline gap-1.5 mb-4">
              <span class="text-3xl font-bold text-ink">Sob Consulta</span>
            </div>
            <p class="text-xs text-ink-muted mb-6 leading-[1.40]">
              Para incorporadoras com demandas de integrações ERP e customização sob demanda.
            </p>
            
            <div class="h-[1px] bg-hairline mb-6"></div>

            <ul class="flex flex-col gap-3 text-xs text-ink-muted">
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-blue" stroke-width="2" />
                Tudo do plano Construtora
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-blue" stroke-width="2" />
                Múltiplos usuários de equipe
              </li>
              <li class="flex items-center gap-2">
                <Check class="w-4 h-4 text-brand-blue" stroke-width="2" />
                Suporte prioritário via SLA WhatsApp
              </li>
            </ul>
          </div>

          <a href="mailto:contato@vertice.com.br?subject=Plano Corporativo" class="w-full min-h-[44px] flex items-center justify-center text-center py-2.5 border border-hairline bg-transparent hover:bg-surface-hover text-ink rounded-md text-[13px] font-bold transition-all duration-200 cursor-pointer mt-8">
            Contatar Vendas
          </a>
        </div>
      </div>
    </section>

    <!-- CLOSING CTA BANNER -->
    <section class="reveal py-16 px-6 max-w-[1280px] mx-auto">
      <div class="bg-gradient-to-br from-surface via-surface to-brand-blue/[0.03] border border-hairline shadow-md rounded-xl p-8 md:p-16 text-center flex flex-col items-center gap-6 relative overflow-hidden">
        <span class="text-[13px] font-bold text-brand-orange tracking-wider uppercase font-mono">TESTE SEM COMPROMISSO</span>
        <h2 class="text-[22px] sm:text-2xl md:text-[40px] font-black text-ink leading-[1.15] max-w-[680px]">
          Centralize e simplifique o controle das suas obras Caixa hoje.
        </h2>
        <p class="text-xs md:text-sm text-ink-muted max-w-[500px] leading-[1.5]">
          Acesso instantâneo sem cartão de crédito. Teste todas as ferramentas e tabelas SINAPI livres.
        </p>
        <router-link to="/auth" class="w-full sm:w-auto min-h-[44px] inline-flex items-center justify-center bg-brand-orange hover:bg-brand-orange-hover text-neutral-950 rounded-md text-[14px] font-bold px-6 py-3 transition-all duration-200 cursor-pointer mt-4 border-none">
          Criar Conta Gratuita B2B
          <ArrowRight class="w-4 h-4 ml-2" stroke-width="2" />
        </router-link>
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="border-t border-hairline bg-canvas py-16 px-6 lg:px-12 max-w-[1280px] mx-auto text-left text-ink-muted">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
        <!-- Logo Column -->
        <div class="col-span-2 flex flex-col gap-4">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 bg-brand-blue/10 rounded-md border border-brand-blue/35 flex items-center justify-center text-brand-blue">
              <Layers class="w-3.5 h-3.5" stroke-width="1.5" />
            </div>
            <span class="text-sm font-bold text-ink">Vértice Engenharia</span>
          </div>
          <p class="text-xs text-ink-muted max-w-[240px] leading-[1.5]">
            Tecnologia focada em inteligência orçamentária e transparência de obras para construtoras e engenheiros B2B.
          </p>
        </div>

        <!-- Links Column 1: Produto -->
        <div class="flex flex-col gap-3 text-xs">
          <span class="font-bold text-ink tracking-wider uppercase mb-1">Produto</span>
          <a href="#features" class="hover:text-white transition-colors">Funcionalidades</a>
          <a href="#demo" class="hover:text-white transition-colors">Simulador</a>
          <a href="#pricing" class="hover:text-white transition-colors">Preços</a>
        </div>

        <!-- Links Column 2: Legal -->
        <div class="flex flex-col gap-3 text-xs">
          <span class="font-bold text-ink tracking-wider uppercase mb-1">Legal</span>
          <span class="hover:text-ink transition-colors cursor-pointer">Termos de Uso</span>
          <span class="hover:text-ink transition-colors cursor-pointer">Privacidade</span>
          <span class="hover:text-ink transition-colors cursor-pointer">Conformidade Caixa</span>
        </div>

        <!-- Links Column 3: Contato -->
        <div class="flex flex-col gap-3 text-xs">
          <span class="font-bold text-ink tracking-wider uppercase mb-1">Empresa</span>
          <a href="mailto:contato@vertice.com.br" class="hover:text-ink transition-colors">Fale Conosco</a>
          <span class="hover:text-ink transition-colors cursor-pointer">Suporte B2B</span>
        </div>
      </div>

      <!-- Bottom Bar -->
      <div class="h-[1px] bg-hairline mb-8"></div>
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-ink-muted font-medium">
        <span>&copy; 2026 Vértice Engenharia S/A. Todos os direitos reservados.</span>
        <div class="flex items-center gap-4">
          <span>Hospedado no Brasil</span>
          <span>&middot;</span>
          <span>Conexão Criptografada SSL</span>
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
      <div v-if="openClientModal" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div 
          @click.stop 
          class="w-full max-w-md bg-surface border border-hairline rounded-xl p-6 relative overflow-hidden text-left"
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
            <div class="w-9 h-9 bg-brand-blue/10 rounded-md border border-brand-blue/35 flex items-center justify-center text-brand-blue">
              <Users class="w-[18px] h-[18px]" stroke-width="1.5" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-ink">Acesso ao Portal do Cliente</h3>
              <p class="text-xs text-ink-muted">Insira o código fornecido pelo seu construtor.</p>
            </div>
          </div>

          <!-- Input Code Form -->
          <form @submit.prevent="submitClientCode" class="flex flex-col gap-4 mt-6">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Código de Acesso da Obra</label>
              <input 
                type="text" 
                v-model="clientToken" 
                placeholder="Ex: OB-8942-X" 
                required
                class="w-full bg-canvas border border-hairline dark:border-transparent text-ink rounded-md py-2.5 px-3 text-sm focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all font-mono tracking-widest text-center"
              />
            </div>

            <!-- Error message -->
            <p v-if="clientTokenError" class="text-xs text-red-500 font-medium">
              {{ clientTokenError }}
            </p>

            <button 
              type="submit" 
              class="w-full min-h-[44px] py-2.5 bg-brand-blue hover:bg-brand-blue-hover text-white rounded-md text-sm font-bold transition-all duration-200 cursor-pointer flex items-center justify-center gap-2 border-none"
            >
              <span>Acessar Portal da Obra</span>
              <ArrowRight class="w-4 h-4" stroke-width="2" />
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
import { Layers, Sun, Moon, Menu, X, ArrowRight, ArrowUpRight, DollarSign, Calendar, Users, CheckCircle2, Image, RefreshCw, FileText, Wallet, Shield, Quote, Check, Building2, MapPin, Star } from 'lucide-vue-next'

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
const activeMockupTab = ref('kanban')

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

/* Transition for Mobile Hamburger and Close Icons */
.rotate-fade-enter-active,
.rotate-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.rotate-fade-enter-from {
  opacity: 0;
  transform: rotate(-45deg) scale(0.85);
}
.rotate-fade-leave-to {
  opacity: 0;
  transform: rotate(45deg) scale(0.85);
}
</style>
