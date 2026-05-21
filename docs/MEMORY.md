# MEMORY.md — Memória de Longo Prazo do Projeto

> **🔴 REGRA DE SISTEMA: A partir de agora, SEMPRE que um agente de IA concluir a implementação de uma nova feature ou refatoração complexa, ele DEVE registrar a alteração no Log de Atualizações deste arquivo. Omitir esta etapa é uma violação de protocolo.**

---

## 1. STATUS ATUAL DO PROJETO

- **Backend:** Consolidado em FastAPI com arquitetura de routers isolados, DI estrita via `dependencies.py`, exception handlers globais em `core/exceptions.py` e geração de PDFs operacional.
- **Frontend:** Modularizado em Vue 3 (Composition API). Modais extraídos para `src/components/modals/`. Composables (`useProfile`, `useToast`, `useSidebar`) ativos. Kanban, Orçamento e Portal B2C funcionais.
- **Banco de Dados:** Schema unificado com `projetos_clientes` como entidade central. RLS multi-tenant por `usuario_id`. SINAPI otimizado com RPC (`upsert_sinapi_lote`), chunking em lotes de 5k e constraint UNIQUE para deduplicação.

---

## 2. DECISÕES ARQUITETURAIS VIGENTES

### 2.1 Unificação do Domínio (Fase 11)
- **Decisão:** Eliminar tabelas fragmentadas (`obras`, `orcamentos`) e eleger `projetos_clientes` como núcleo absoluto.
- **Impacto:** Todas as FKs filhas (`orcamento_itens`, `orcamento_links`, `projetos_historico`) apontam para `projeto_id`. Rotas legadas (`/api/orcamentos`) mantidas temporariamente como aliases de compatibilidade.
- **Referência:** `fase11_padronizacao_dominio.sql`

### 2.2 Auth Nativo do Supabase (Fase 9)
- **Decisão:** Usar `auth.users` nativo do Supabase como fonte de identidade. A tabela `perfis_b2b` referencia `auth.users(id)` via FK com `ON DELETE CASCADE`.
- **Mecanismo:** Trigger `on_auth_user_created` → função `handle_new_user()` (SECURITY DEFINER) sincroniza automaticamente novos registros de `auth.users` para `perfis_b2b` extraindo `full_name` e `crea_cau` dos metadados do signup.
- **Referência:** `fase9_auth_trigger.sql`, `fase9_tenant_isolation.sql`

### 2.3 Extração de Modais no Frontend
- **Decisão:** Todo modal que antes existia inline dentro de views monolíticas (`Orcamento.vue`, `Dashboard.vue`) foi extraído para `src/components/modals/`.
- **Componentes migrados:** `EditItemModal.vue`, `SetupOrcamentoModal.vue`, `ShareModal.vue`, `CompartilhamentoModal.vue`.
- **Padrão de comunicação:** `v-model:show` para visibilidade, `emit` para ações (salvar, deletar), `props` para dados de entrada.

### 2.4 SINAPI: RPC + Chunking (Batch Processing)
- **Decisão:** Abandonar inserções linha-a-linha do SINAPI. Toda importação usa a Stored Procedure `upsert_sinapi_lote` chamada via `supabase_client.rpc()`.
- **Configuração:** Chunks de máx 5.000 registros. `SinapiBot` (pandas) processa planilhas e retorna DataFrames. Persistência é feita pelo router `sinapi.py`.
- **Deduplicação:** Constraint `uq_sinapi_itens_chave_natural` (`codigo_item`, `estado`, `mes_ano`, `desonerado`) impede duplicatas no nível do banco.
- **Referência:** `fix_duplicatas_sinapi.sql`, `sinapi_bot.py`

### 2.5 Exception Handlers com CORS Blindado
- **Decisão:** Todas as exceções não tratadas passam pelo `core/exceptions.py` que injeta headers CORS dinamicamente na resposta de erro.
- **Motivo:** O middleware CORS do Starlette/FastAPI não intercepta respostas geradas por Exception Handlers, fazendo o navegador mascarar erros 500 como falha de CORS.
- **Mapeamento:** Erros de banco (duplicate key, FK violation, RLS, timeout, JWT) são traduzidos em mensagens seguras com `error_code` semântico.

---

## 3. DÍVIDAS TÉCNICAS CONHECIDAS

- [ ] `routers/relatorios.py` ainda referencia a tabela legada `orcamentos` na rota de PDF comercial. Precisa migrar para `projetos_clientes`.
- [x] `routers/portal_cliente.py` referencia `orcamentos` no acesso B2C via Service Role. Precisa migrar para `projetos_clientes`. → **Resolvido:** Coluna `orcamento_id` renomeada para `projeto_id` no banco + `pin_acesso` adicionada.
- [x] A função `extrair_usuario_id_do_token()` em `routers/projetos.py` é duplicata de `get_user_id()` em `dependencies.py`. Consolidar.
- [ ] Composições SINAPI (`tipo == "composicao"`) retornam `data: []` no router. Implementação pendente.
- [ ] `supabase_schema.sql` contém o schema inicial legado com políticas permissivas `USING (true)`. Não reflete o estado atual do banco. Considerar atualizar ou depreciar.

---

## 4. LOG DE ATUALIZAÇÕES

> Formato: `[AAAA-MM-DD] — [Módulo] — Descrição resumida`

| Data | Módulo | Descrição |
|---|---|---|
| 2026-05-20 | Full-Stack | **P10 Jornada de Acesso Concluída:** Separada a jornada do lead (matchmaking B2C no wizard público) do portal do cliente ativo. O link e PIN do portal foram removidos da tela final do EstimativaWizard e agora são exibidos na Sala de Espera pós-upload de documentos. O CTA do Kanban em `engenharia_caixa` foi atualizado para "Enviar Acesso à Obra", integrando envio via WhatsApp e movendo "Abrir SINAPI" para o dropdown. Adicionados endpoints públicos GET/PATCH seguros por ID aleatório do projeto no `matchmaking.py`. |
| 2026-05-20 | Frontend | **P5.5 Fase 5 Concluída:** Criado componente premium reusável `Caixometro.vue` para progresso físico-financeiro da Caixa (PCI/PFUI) com tooltips explicativas sobre juros de evolução de obra e integrado na aba "Evolução Caixa" do portal do cliente. |
| 2026-05-20 | Testes | **P5.5 Fase 5 Concluída:** Criada suite de testes integrados e automatizados `test_portal_avancado.py` validando matchmaking, PIN parsing, rotas de feed/documentos/caixa e RLS (100% de sucesso/OK). Corrigido relacionamento da FK em `orcamento_links` no Supabase para apontar para `projetos_clientes`. |
| 2026-05-20 | Frontend | **P5.4 Fase 4 Concluída:** Linha do tempo vertical integrada no `PortalCliente.vue` consumindo dados reais de canteiro. Wizard (`EstimativaWizard.vue`) atualizado para exibir card com link do portal e PIN de segurança com botão de cópia rápida e atalho de navegação no encerramento do matchmaking B2C. |
| 2026-05-20 | Frontend | **P5.3 Fase 3 Concluída:** Portal do Cliente (`PortalCliente.vue`) refatorado com abas responsivas (Timeline, Evolução Caixa, Documentos). Modal de Compartilhamento (`ShareLinkModal.vue`) atualizado para pré-carregar e preencher o PIN com os últimos 4 dígitos do telefone do cliente. |
| 2026-05-20 | Backend | **P5.2 Fase 2 Concluída:** Criadas as rotas públicas sob `/api/portal/projetos/{hash_link}` para feed, documentos e caixa (Caixômetro físico-financeiro com cálculo simulado de juros de obra). |
| 2026-05-20 | Banco de Dados | **P5.1 Fase 1 Concluída:** Migration 002 aplicada — tabelas `obras_feed` e `projetos_documentos` criadas com RLS. Tabela `orcamento_links` corrigida: `orcamento_id` → `projeto_id`, coluna `pin_acesso` adicionada. |
| 2026-05-20 | Backend | **P5.1 Fase 1 Concluída:** Endpoint `POST /api/matchmaking/solicitar` agora gera automaticamente o link do portal e o PIN (4 últimos dígitos do telefone) na criação do Lead. |
| 2026-05-20 | Frontend | **P4.4 Concluída:** Criada Landing Page B2C (/simulador) integrada com endpoint de cálculo e redirecionamento parametrizado para o Wizard. |
| 2026-05-20 | Full-Stack | **P4.3 Concluída:** Fluxo de Matchmaking B2C operacional (Step 4 no Wizard, endpoint seguro de Lead via service_role bypass RLS, finalização anônima opcional). |
| 2026-05-19 | Backend | **P4.2 Concluída:** Criada migration SQL e endpoint público de matchmaking (/api/matchmaking) integrado com perfis_b2b. |
| 2026-05-19 | Backend | **P4.1 Concluída:** Criado endpoint público de simulação paramétrica (/api/simulador/calcular) e registrado no main.py. |
| 2026-05-19 | Frontend | **P3.4 Concluída:** Modal inline de item manual removido de FinancialSummary.vue, substituído pelo componente reutilizável ManualItemModal.vue. |
| 2026-05-19 | Frontend | **P3.3 Concluída:** Constante ETAPAS_OBRA extraída para src/constants/etapas.js e importada nos componentes ArvoreCustos.vue, EditItemModal.vue e ManualItemModal.vue. |
| 2026-05-19 | Frontend | **P3.2 Concluída:** Função formatCurrency extraída para src/utils/formatters.js e importada em todos os componentes. |
| 2026-05-19 | Banco de Dados | **P2.4 Concluída:** supabase_schema.sql depreciado com aviso de segurança. |
| 2026-05-19 | Backend | **P2.3 Concluída:** Endpoint de busca SINAPI atualizado para suportar o filtro tipo=composicao. |
| 2026-05-19 | Frontend | **P3.1 Concluída:** ShareModal e CompartilhamentoModal unificados no novo componente ShareLinkModal.vue. |
| 2026-05-19 | Backend | **P2.2 Concluída:** extrair_usuario_id_do_token consolidada com get_user_id em projetos.py usando Depends. |
| 2026-05-18 | Backend+Frontend | **P2.1 Concluída:** `portal_cliente.py` migrado de `orcamentos` → `projetos_clientes`. Model `orcamento_id`→`projeto_id`. Response key `orcamento`→`projeto`. Frontend: `ShareModal`, `CompartilhamentoModal` e `PortalCliente.vue` atualizados (payload+campos). Erros sanitizados. |
| 2026-05-18 | Frontend | **P1.3 Concluída:** URL em `FinancialSummary.vue:52` atualizada de `/orcamentos/` → `/projetos/` para alinhar com novo prefixo do backend. Bloco P1 100% completo. |
| 2026-05-18 | Backend | **P1.2 Concluída:** `relatorios.py` migrado de `orcamentos` → `projetos_clientes`. Prefixo `/api/orcamentos` → `/api/projetos`. Campos: `bdi`→`bdi_padrao`, `nome_obra`→`titulo_projeto`. Busca itens por `projeto_id`. Erro sanitizado. |
| 2026-05-18 | Backend | **P1.1 Concluída:** `gerar_contrato()` em `integracoes.py` alterada de `async def` → `def` (thread pool). Erro sanitizado conforme RULES.md §2.3. `enviar_para_zapsign()` mantida `async def`. |
| 2026-05-18 | Produto | Criação do `TODO.md` — backlog priorizado com 16 micro-tarefas (P1-P4), mapa de dependências e estimativa de esforço. |
| 2026-05-18 | Frontend | Criação do `UI_COMPONENTS.md` — catálogo de 14 componentes com props/emits, 3 composables, paleta de cores, padrões de modal/input e dívidas técnicas de UI. |
| 2026-05-18 | QA | Criação do `TEST_PLAN.md` — cenários BDD para PDF, SINAPI+BDI e Upload em Lote com critérios de aceite e matriz de riscos. |
| 2026-05-18 | Governança | Criação do `RULES.md` — fonte da verdade com regras de backend, frontend, segurança, RLS e instruções para IA. |
| 2026-05-18 | Governança | Criação do `MEMORY.md` — memória de longo prazo com decisões arquiteturais, status e log de atualizações. |
| 2026-05-18 | Banco de Dados | Consolidação documentada: unificação de domínio (Fase 11), RLS multi-tenant, RPC SINAPI com chunking, constraint de deduplicação. |
| 2026-05-14 | Backend | Correção de políticas RLS e injeção de `usuario_id` no fluxo de criação de projetos. Ajuste de prefixos de rotas (`/api/admin`, `/api/sinapi`). |
| 2026-05-14 | Backend | Refatoração do sync SINAPI: migração de inserts linha-a-linha para batch processing via Stored Procedure `upsert_sinapi_lote`. |
| 2026-05-13 | Frontend | Extração de modais do `Orcamento.vue` para `src/components/modals/` (EditItemModal, SetupOrcamentoModal, ShareModal). |
| 2026-05-13 | Banco de Dados | Implementação de RLS policies em `orcamento_itens`, `orcamento_links` e `projetos_historico` com isolamento via JOIN. |
| 2026-05-12 | Frontend | Modularização do componente Kanban (`ProjectCard.vue`). Implementação de gaveta de projetos arquivados e modal de edição. |
| 2026-05-11 | Full-Stack | Feature "Histórico e Notas": modal reativo, endpoints `GET/POST /api/projetos/{id}/historico`, tabela `projetos_historico`. |
| 2026-05-07 | Frontend | Módulo "Engenharia": `EngenhariaList.vue` com busca, filtros por status e navegação para orçamento por projeto. |
| 2026-05-06 | Infraestrutura | Deploy produção: sanitização de URLs hardcoded, `vercel.json` para SPA routing, sincronização Vercel (frontend) + Render (backend). |
