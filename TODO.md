# TODO.md — Backlog Priorizado de Micro-Tarefas

> **⚠️ ATENÇÃO AGENTES DE IA: Por limitação de contexto, você DEVE pegar apenas UMA micro-tarefa deste backlog por vez. Nunca tente fazer 2 ou mais tarefas simultaneamente. Marque `[x]` e atualize o arquivo `MEMORY.md` ao concluir.**


## P1 — CRÍTICO: Otimização de Geração de PDF e Contratos

> **Contexto:** A rota `gerar_contrato()` em `integracoes.py` é `async def` e chama `generate_contract_pdf()` (CPU-bound, fpdf2) diretamente. Isso bloqueia o event loop do Uvicorn. A rota `gerar_pdf_comercial()` em `relatorios.py` é `def` (correta — delega para thread pool), MAS ainda referencia a tabela legada `orcamentos`.

### P1.1 — Backend: Corrigir bloqueio de event loop em `integracoes.py`
- [x] **Alterar `gerar_contrato()` de `async def` para `def`** em `routers/integracoes.py:150` ✅ *Concluída em 2026-05-18*
  - Motivo: `generate_contract_pdf()` é sync/CPU-bound → ao rodar dentro de `async def`, bloqueia o event loop
  - FastAPI delega automaticamente funções `def` para thread pool
  - Testar: 2 requisições simultâneas — a segunda não deve esperar a primeira terminar
  - ⚠️ NÃO alterar `enviar_para_zapsign()` — esta é `async def` corretamente (usa `httpx.AsyncClient`)

### P1.2 — Backend: Migrar `relatorios.py` de `orcamentos` para `projetos_clientes`
- [x] **Substituir query `supabase_client.table("orcamentos")` por `supabase_client.table("projetos_clientes")`** em `routers/relatorios.py:38` ✅ *Concluída em 2026-05-18*
  - Trocar campo `orcamento.get("bdi")` → `projeto.get("bdi_padrao")`
  - Trocar campo `orcamento.get("nome_obra")` → `projeto.get("titulo_projeto")`
  - Trocar campo `orcamento.get("cliente_nome")` → `projeto.get("cliente_nome")` (mantém)
  - Ajustar busca de itens: `table("orcamento_itens").eq("orcamento_id")` → `table("orcamento_itens").eq("projeto_id")`
  - Renomear variável interna `orcamento` → `projeto` por clareza semântica
  - Testar: Gerar PDF a partir da tela de orçamento (botão "Gerar Proposta Comercial")

### P1.3 — Frontend: Ajustar rota de PDF no `FinancialSummary.vue`
- [x] **Atualizar URL do axios em `baixarPropostaPDF()`** em `src/components/FinancialSummary.vue:52` ✅ *Concluída em 2026-05-18*
  - Atual: `GET /orcamentos/${activeOrcamento.id}/pdf-comercial`
  - Novo: `GET /projetos/${activeOrcamento.id}/pdf-comercial` (alinhar com novo prefixo)
  - ⚠️ Coordenar com P1.2 — o prefixo do router em `relatorios.py` também precisa mudar de `/api/orcamentos` para `/api/projetos`

---

## P2 — ALTA: Dívidas Técnicas de Backend (MEMORY.md)

### P2.1 — Backend: Migrar `portal_cliente.py` de `orcamentos` para `projetos_clientes`
- [x] **Substituir `service_client.table("orcamentos")` por `service_client.table("projetos_clientes")`** em `routers/portal_cliente.py:85` ✅ *Concluída em 2026-05-18*
  - Ajustar campo `orcamento_id` no insert de `orcamento_links` se necessário
  - Verificar: `orcamento_links.orcamento_id` FK aponta para qual tabela? Se `orcamentos` (legada), criar migration para repontear ou adicionar coluna `projeto_id`
  - Testar: Fluxo B2C completo (Gerar link → Acessar como cliente → Validar PIN → Ver orçamento)

### P2.2 — Backend: Consolidar `extrair_usuario_id_do_token()` com `get_user_id()`
- [x] **Remover** a função `extrair_usuario_id_do_token()` de `routers/projetos.py:13-28`
- [x] **Substituir os 2 usos** por `Depends(get_user_id)` de `dependencies.py`:
  - `routers/projetos.py:122` → `insert_data["usuario_id"] = extrair_usuario_id_do_token(token)` → `user_id` via Depends
  - `routers/projetos.py:298` → `"usuario_id": extrair_usuario_id_do_token(token)` → `user_id` via Depends
- [x] **Remover import `security`** de `projetos.py` se não for mais usado diretamente
- [x] Testar: Criar projeto e registrar histórico — ambas as operações devem funcionar com `get_user_id`

### P2.3 — Backend: Implementar busca de composições SINAPI
- [x] **Adicionar filtro `tipo == "composicao"` no `get_sinapi_items()`** em `routers/sinapi.py`
  - Verificar: Tabela `sinapi_itens` tem coluna `tipo`? Se não, verificar como distinguir insumo de composição (Confirmado: não há coluna tipo; composições são uma tabela distinta)
  - Verificar: `sinapi_bot.py` → `processar_planilha_composicoes()` → qual campo identifica composições? (Persistidas em sinapi_composicoes e itens em sinapi_composicao_itens)
  - Implementar query que retorna composições com seus insumos componentes (se aplicável) (Implementado cálculo batch dinâmico de preços dos insumos)
  - Testar: Busca `GET /api/sinapi?tipo=composicao` retorna itens (Query de relação aninhada testada)

### P2.4 — Backend: Atualizar `supabase_schema.sql`
- [x] **Depreciar** o arquivo `supabase_schema.sql` com aviso no topo ou atualizá-lo com o schema real (Adicionado header de aviso alertando que o schema real e RLS seguros estão direto no Supabase)

---

## P3 — MÉDIA: Dívidas Técnicas de UI (UI_COMPONENTS.md)

### P3.1 — Frontend: Unificar `ShareModal` e `CompartilhamentoModal`
- [x] **Criar componente único** `src/components/modals/ShareLinkModal.vue`
  - Props: `isOpen: Boolean`, `resourceId: String | Number`, `resourceLabel: String` (default: 'Orçamento')
  - Emits: `'close'`
  - Lógica: Idêntica ao atual — PIN → Gerar link → Copiar/WhatsApp
  - Usar `<Teleport to="body">` (padrão de todos os modais)
- [x] **Substituir uso em `Orcamento.vue`** → trocar `<ShareModal>` por `<ShareLinkModal :resourceId="...">` ✅ *Concluída em 2026-05-19*
- [x] **Substituir uso em `Dashboard.vue`/`ProjectCard.vue`** → trocar `<CompartilhamentoModal>` por `<ShareLinkModal>` ✅ *Concluída em 2026-05-19*
- [x] **Deletar** `src/components/modals/ShareModal.vue` e `src/components/modals/CompartilhamentoModal.vue` ✅ *Concluída em 2026-05-19*
- [x] Atualizar `UI_COMPONENTS.md` com o novo componente ✅ *Concluída em 2026-05-19*

### P3.2 — Frontend: Extrair `formatCurrency()` para utilitário compartilhado
- [x] **Criar** `src/utils/formatters.js` ✅ *Concluída em 2026-05-19*
- [x] **Substituir** em todos os componentes (`ArvoreCustos.vue`, `FinancialSummary.vue`, `EstimativaWizard.vue`, `ProjectCard.vue`, `SinapiTable.vue`, `PortalCliente.vue`, `EngenhariaList.vue`) ✅ *Concluída em 2026-05-19*
- [x] Testar: Valores monetários renderizam corretamente em todas as telas e compilam com sucesso ✅ *Concluída em 2026-05-19*

### P3.3 — Frontend: Extrair constante `etapas[]` para módulo compartilhado
- [x] **Criar** `src/constants/etapas.js` ✅ *Concluída em 2026-05-19*
- [x] **Substituir** em: `ArvoreCustos.vue`, `modals/EditItemModal.vue`, `ManualItemModal.vue` ✅ *Concluída em 2026-05-19*
- [x] Testar: Accordion de etapas e selects de etapa continuam funcionando e compilando com sucesso ✅ *Concluída em 2026-05-19*

### P3.4 — Frontend: Remover modal de item manual inline do `FinancialSummary.vue`
- [x] **Remover** o HTML do modal manual e a lógica `salvarItemManual()` em `FinancialSummary.vue` ✅ *Concluída em 2026-05-19*
- [x] **Importar e usar** o `ManualItemModal.vue` existente como sub-componente ✅ *Concluída em 2026-05-19*
- [x] Conectar o emit `'confirm'` do `ManualItemModal` ao handler de salvamento via API ✅ *Concluída em 2026-05-19*
- [x] Testar: Botão "+ Item Manual" no Resumo Financeiro abre o modal correto e salva ✅ *Concluída em 2026-05-19*

---

## P4 — FEATURE: Matchmaking / Simulador Avançado B2C

> **Contexto:** O `EstimativaWizard.vue` já possui um wizard de 3 steps (Padrão → Metragem → Resultado) com simulação Caixa. A feature de matchmaking conectaria clientes a engenheiros com base em localização, especialidade e disponibilidade.

### P4.1 — Backend: Criar endpoint de simulação paramétrica
- [x] **Criar** `routers/simulador.py` com rota `POST /api/simulador/calcular` ✅ *Concluída em 2026-05-19*
  - Input: `{ padrao: str, metragem: float, uf: str }`
  - Lógica: Busca preço base do SINAPI para a UF (média dos itens mais comuns por padrão)
  - Output: `{ valor_estimado, custo_m2, margem_financiamento }`
  - ⚠️ Rota pública (sem JWT) — é para prospects não autenticados

### P4.2 — Backend: Criar modelo de dados para matchmaking
- [x] **Criar migration** com tabela `engenheiros_disponiveis` ✅ *Concluída em 2026-05-19*
- [x] **Criar endpoint** `GET /api/matchmaking?uf=SC&padrao=popular` ✅ *Concluída em 2026-05-19*

### P4.3 — Frontend: Evolução do EstimativaWizard
- [x] **Adicionar Step 4** no `EstimativaWizard.vue`: "Encontre seu Engenheiro" ✅ *Concluída em 2026-05-20*
  - Exibir cards de engenheiros retornados pelo matchmaking (`GET /api/matchmaking?uf=...`)
  - Card com: avatar, nome, CREA/CAU, especialidades e botão "Solicitar Orçamento"
  - Usar padrão visual do `UI_COMPONENTS.md` (cards com fundo `bg-surface`, bordas `border-hairline` e botões de destaque)
- [x] **Implementar endpoint de criação de Lead** `POST /api/matchmaking/solicitar` ✅ *Concluída em 2026-05-20*:
  - Como o usuário B2C é anônimo, o backend usa a `service_role` (ignora RLS) para criar de forma segura o projeto na base do engenheiro com status de 'Lead' e gerar a notificação inicial
- [x] **Conectar** o clique do botão "Solicitar Orçamento" ao endpoint de solicitação e exibir tela de sucesso/confirmação ✅ *Concluída em 2026-05-20*

### P4.4 — Frontend: Landing Page B2C (Funil de Vendas)
- [x] **Criar** `src/components/LandingSimulador.vue` ✅ *Concluída em 2026-05-20*
  - Hero com CTA de impacto: "Descubra o custo estimado da sua obra em 60 segundos"
  - Inputs semânticos e integrados ao endpoint público `/api/simulador/calcular`
  - Direcionar o prospect para o `EstimativaWizard` com os dados da simulação pré-preenchidos para escolha do engenheiro

---

## P5 — FEATURE: Portal do Cliente Avançado & Evolução de Obra (MCMV)

### P5.1 — Backend: Tabelas de Diário de Obra e Documentos (Migration)
- [x] **Criar migration** `supabase/migrations/002_portal_cliente_avancado.sql`: ✅ *Concluída em 2026-05-21*
  - Tabela `obras_feed` (`id`, `projeto_id`, `descricao`, `imagens[]`, `criado_em`, `usuario_id`)
  - Tabela `projetos_documentos` (`id`, `projeto_id`, `nome_documento`, `arquivo_url`, `categoria`, `criado_em`)
  - RLS: Select público via token do projeto, insert/update/delete restrito ao engenheiro dono (`auth.uid() = usuario_id`).

### P5.2 — Backend: Endpoints de Acesso e Consumo
- [x] **Criar rotas** públicas sob `routers/portal_cliente.py` (validadas por hash/PIN do link): ✅ *Concluída em 2026-05-21*
  - `GET /api/portal/projetos/{hash_link}/feed` -> retorna posts da timeline
  - `GET /api/portal/projetos/{hash_link}/documentos` -> retorna documentos do vault
  - `GET /api/portal/projetos/{hash_link}/caixa` -> retorna progresso físico/financeiro e juros de obra estimados

### P5.3 — Frontend: Linha do Tempo e Medição Caixa no Portal B2C
- [x] **Criar Timeline Visual** no `PortalCliente.vue` para exibir fotos da obra com legendas ordenadas cronologicamente ✅ *Concluída em 2026-05-21*
- [x] **Criar componente** `Caixometro.vue` mostrando o progresso da obra (etapas de medição da Caixa Econômica) e tooltip educacional explicando a taxa de evolução de obra (juros de obra) ✅ *Concluída em 2026-05-21*
- [x] **Aba "Cofre de Documentos"** no `PortalCliente.vue` para listagem e download de PDFs (plantas, contratos, Habite-se) ✅ *Concluída em 2026-05-21*

### P5.4 — Frontend/Backend: Diário de Obra Mobile-First para o Engenheiro
- [x] **Criar aba rápido "Diário de Obra"** no painel do engenheiro: ✅ *Concluída em 2026-05-21*
  - Focado em mobile/campo, permitindo tirar foto na hora e digitar descrição rápida
  - Implementar compressão de imagem em JS antes de salvar no Storage para otimização de custos de hospedagem

---

## P6 — FEATURE: Vitrine Pública do Construtor B2B2C

### P6.1 — Backend: Modelo de Vitrine e Perfil Público
- [x] **Criar migration** para adicionar colunas à tabela `perfis_b2b`: ✅ *Concluída em 2026-05-21*
  - `slug_vitrine` (text unique), `descricao_vitrine` (text), `fotos_portfolio` (text[]), `cidades_atuacao` (text[])
- [x] **Criar endpoints** em `routers/vitrine.py`: ✅ *Concluída em 2026-05-21*
  - `GET /api/vitrine/{slug}` (público) -> retorna dados públicos do engenheiro
  - `POST /api/vitrine/configurar` (privado com JWT) -> atualiza dados de portfólio

### P6.2 — Frontend: Reestruturação do Layout de Configurações (Padrão Vercel/Stripe)
- [x] **Refatorar `Configuracoes.vue` (Casca):** ✅ *Concluída em 2026-05-21*
  - Removido cabeçalho redundante; nav horizontal `shrink-0` entre TopHeader e conteúdo (sem sticky hack).
  - Tabs com indicador de linha inferior ativa; tab ativa muda componente via `markRaw` + `computed`.
- [x] **Padronizar UI dos Formulários (Cards Isolados):** ✅ *Concluída em 2026-05-21*
  - Padrão consistente: card com header (título + descrição), body (inputs grid) e footer isolado com botão "Salvar".
  - Substituídos `alert()` por `showToast()` em todos os novos tabs.
- [x] **Criar as Abas Base:** ✅ *Concluída em 2026-05-21*
  - **`TabPerfil.vue`:** Avatar, Informações Profissionais, Alterar Senha, Danger Zone.
  - **`TabEmpresa.vue`:** Logo da Construtora, Dados Jurídicos (Nome Fantasia, CNPJ, Endereço).
  - **`TabPreferencias.vue`:** Seletor visual Light/Dark (preview de UI), BDI Padrão Global (localStorage).
- [x] **Migrar o `ConfiguracoesContratos.vue`** para aba dinâmica; layout fill-height preservado via wrapper condicional. ✅ *Concluída em 2026-05-21*

### P6.3 — Frontend: Configuração de Vitrine pelo Engenheiro
- [x] **Criar aba `TabVitrine.vue`:** Para edição de biografia, galeria de fotos de obras concluídas e definição da URL personalizada (`slug_vitrine`). Usar o mesmo padrão de Cards Isolados do P6.2. ✅ *Concluída em 2026-05-21*

### P6.4 — Frontend: Landing Page Pública do Engenheiro (`vertice.app/p/:slug`)
- [x] **Criar rota pública dinâmica** `/p/:slug` no `router.js` com layout premium: ✅ *Concluída em 2026-05-21*
  - Exibe foto de perfil, registro CREA/CAU, cidades de atuação e galeria de portfólio com thumbnails clicáveis
  - Simulador paramétrico embutido (UF + metragem + padrão) chamando `POST /simulador/calcular`
  - Após resultado: formulário de contato (nome + WhatsApp) + CTA "Solicitar Orçamento para [Nome]"
  - Solicita via `POST /matchmaking/solicitar` com `usuario_id` do engenheiro da vitrine (sem matchmaking genérico)
  - Redireciona para `/estimativa/:projeto_id` para envio de documentos
  - Botão "Visualizar Vitrine" no `TabVitrine.vue` abre `/p/:slug` em nova aba

---

## P7 — FEATURE: Sincronização em Tempo Real (Realtime Kanban)

> **Contexto:** Quando o cliente B2C aprova a simulação ou faz upload de documentos, o card no Kanban do engenheiro deve se mover/atualizar instantaneamente sem necessidade de `F5`.

### P7.1 — Frontend: Escuta de Eventos via Supabase Realtime
- [x] **Dashboard/Kanban:** Implementar inscrição (`supabase.channel('kanban-projetos').on('postgres_changes', ...).subscribe()`) para escutar `UPDATE`, `INSERT` e `DELETE` na tabela `projetos_clientes`. ✅ *Concluída em 2026-05-21*
- [x] **Reatividade:** Ao receber o payload do WebSocket, atualizar o array local do Vue para refletir as mudanças (mover coluna, alterar status) com transições visuais suaves (`<TransitionGroup name="kanban-card">`). ✅ *Concluída em 2026-05-21*
- [x] **Toast de notificação:** Exibe mensagem ao engenheiro quando um lead avança de coluna ou envia documentos (`docs_completos`). ✅ *Concluída em 2026-05-21*
- [x] **Migration:** `005_realtime_projetos_clientes.sql` — habilita `REPLICA IDENTITY FULL` e adiciona tabela à publicação `supabase_realtime`. ✅ *Concluída em 2026-05-21*
- [x] **Cleanup:** `onUnmounted` remove o canal para evitar memory leak. ✅ *Concluída em 2026-05-21*

---

## P8 — FEATURE: Upload Granular de Documentos B2C

> **Contexto:** Em vez de um botão de upload em lote, o cliente deve enviar cada documento exigido separadamente, facilitando a auditoria.

### P8.1 — Frontend: Modificar `EstimativaWizard.vue` (Step de Upload)
- [x] **Separar Dropzones:** Criar 3 campos distintos para upload: 1. Identidade (RG/CNH), 2. Comprovante de Residência, 3. Certidão de Estado Civil. ✅ *Concluído em 2026-05-22*
- [x] **Lógica de Upload:** Modificar o método `uploadFiles` para enviar os arquivos categorizados de forma que a API saiba qual documento é qual. ✅ *Concluído em 2026-05-22*
  - Cada arquivo salvo em `{projeto_id}/{categoria}/{arquivo}` no Storage
  - Payload inclui campo `categoria` por documento
  - Botão "Finalizar Envio" desabilitado até os 3 slots estarem preenchidos (`allDocsReady`)

### P8.2 — Frontend/Backend: Auditoria no `ProjectCard.vue`
- [x] **Backend:** Atualizar o schema/endpoint de recepção de documentos para armazenar a `categoria` do documento atrelada ao arquivo. ✅ *Concluído em 2026-05-22*
  - `List[dict]` já era flexível — nenhuma migration necessária
  - Histórico agora registra as categorias: `"Documentos recebidos: identidade, residencia, estado_civil"`
- [x] **Frontend:** No card do Kanban, exibir os documentos com suas respectivas etiquetas (RG, Comprovante, etc.) em vez de apenas nomes genéricos de arquivo. ✅ *Concluído em 2026-05-22*
  - Ícone contextual por categoria (`badge`, `home_work`, `family_restroom`)
  - Label principal: "Identidade" / "Residência" / "Estado Civil"
  - Nome do arquivo exibido como subtexto
  - Badge colorido com tipo abreviado (RG/CNH, Comprovante, Certidão)
  - Fallback gracioso para documentos antigos sem campo `categoria`

---

## P9 — FEATURE: Histórico de Auditoria e Rejeição de Documentos

> **Contexto:** Cada card deve ter uma "linha do tempo" real que registre ações automáticas e manuais. Além disso, o engenheiro deve poder rejeitar um documento específico, notificando o cliente.

### P9.1 — Backend/Frontend: Linha do Tempo Real do Projeto
- [x] **Backend:** Criar a tabela `projetos_historico` (projeto_id, acao, detalhes JSONB, usuario_id, criado_em) caso não exista. ✅ *Concluído em 2026-05-22*
- [x] **Backend:** Criar rotinas automáticas (triggers ou via API) para inserir registros no histórico quando: projeto criado, link gerado, documentos enviados, contrato gerado, contrato assinado. ✅ *Concluído em 2026-05-22*
- [x] **Frontend (`ProjectCard.vue`):** Conectar o modal de "Histórico e Notas" (atualmente com dados estáticos) ao endpoint `GET /api/projetos/{id}/historico`. ✅ *Concluído em 2026-05-22*

### P9.2 — Backend/Frontend: Rejeição de Documentos e Correção B2C
- [x] **Backend:** Criar endpoint `POST /api/projetos/{id}/documentos/rejeitar` que aceita o `id` do documento e um `motivo`. Este endpoint deve deletar o arquivo inválido, mudar o status do projeto para `docs_pendentes` (ou similar) e registrar a recusa no histórico. ✅ *Concluído em 2026-05-22*
- [x] **Frontend (`ProjectCard.vue`):** Adicionar um botão de ação "Recusar" ao lado de cada documento no cofre do Kanban. Ao clicar, abrir modal pedindo o "Motivo". ✅ *Concluído em 2026-05-22*
- [x] **Frontend (`PortalCliente.vue`):** Exibir alerta caso existam documentos rejeitados (com o motivo visível) e liberar o botão de upload apenas para o documento faltante/rejeitado. ✅ *Concluído em 2026-05-22*

---

## P10 — FEATURE: Jornada de Acesso (Estimativa vs Portal da Obra)

> **Contexto:** Separar claramente o ambiente de "Venda/Burocracia" (Wizard) do ambiente de "Entrega/Obra" (Portal). O Portal só deve ser apresentado ao cliente após o contrato ser assinado.

### P10.1 — Frontend: Esconder Portal na Captação (`EstimativaWizard.vue`)
- [x] **Remover Acesso Antecipado:** Remover a exibição do link e PIN do Portal do Cliente na tela final do matchmaking. ✅ *Concluído em 2026-05-20*
- [x] **Estado de Espera (Sala de Espera):** Quando os documentos forem enviados (`status = 'docs_completos'`), a tela do Estimativa deve exibir apenas uma mensagem: *"Documentos em análise! Aguarde o contato do engenheiro para assinatura do contrato"*. Se o cliente acessar esse link novamente, ele só verá essa mensagem (o link encerra sua vida útil aqui). ✅ *Concluído em 2026-05-20*

### P10.2 — Frontend: Onboarding Pós-Venda (`ProjectCard.vue`)
- [x] Atualizar as lógicas de `ctaInfo` e ações do Kanban. Quando o projeto avançar para `engenharia_caixa` (após contrato assinado), exibir o CTA de destaque: "Enviar Acesso à Obra". ✅ *Concluído em 2026-05-20*
- [x] Ao clicar no CTA, abrir a comunicação no WhatsApp entregando o link oficial do Portal (`/portal/{token}`) junto com o PIN, oficializando o início dos trabalhos. ✅ *Concluído em 2026-05-20*

---

## P11 — BUGS: Correções Identificadas no PRODUTO.md

> **Contexto:** Bugs e problemas de UX levantados durante análise do produto. Todos impactam diretamente o uso diário do engenheiro. Executar na ordem abaixo: 11.1 desbloqueia o acesso ao SINAPI, os demais são independentes.

### P11.1 — Frontend: Bug Setup da Obra não navega após salvar
- [x] **Corrigir evento errado no `ProjectCard.vue:922`**
  - Atual: `@success="onSetupSuccess"`
  - Correto: `@salvar="onSetupSuccess"`
  - **Causa:** `SetupOrcamentoModal` emite `'salvar'` (`SetupOrcamentoModal.vue:77`) mas `ProjectCard` escuta `@success` — o handler `onSetupSuccess` existe e está correto (linha 214-217), simplesmente nunca é chamado
  - Testar: Abrir Setup → preencher UF + mês + BDI → Salvar → deve fechar modal e navegar para `/orcamento/:id`

### P11.2 — Frontend: Pre-seleções incorretas no Setup da Obra
- [x] **Remover fallback `'SC'` no `SetupOrcamentoModal.vue:44`** ✅ *Concluído em 2026-05-22*
  - Atual: `form.value.uf_obra = props.project.uf_obra || 'SC'`
  - Correto: `form.value.uf_obra = props.project.uf_obra || ''`
  - O select já tem `<option value="" disabled selected>Selecione...</option>` — com o fallback removido, o placeholder aparece corretamente
  - Encargos Sociais: `sinapi_desonerado` agora inicia como `null` com placeholder "Selecione..."
  - BDI: valor padrão alterado de `null` para `20`
  - Testar: Abrir Setup em um projeto novo → campo UF deve mostrar "Selecione..." sem pré-seleção. O campo ENCARGOS SOCIAIS não deve vir setado também, deve ter um Selecione.

### P11.3 — Frontend: Botão de voltar ausente nas telas principais
- [x] **Adicionar botão "Voltar" no `Orcamento.vue`** (header da tela) ✅ *Concluído em 2026-05-22*
  - Ação: `router.push('/engenharia')`
  - Posição: canto superior esquerdo do header, antes do título da obra
  - Estilo: ícone `arrow_back` + texto "Obras" — padrão já usado em outros lugares do sistema
- [x] **Adicionar botão "Voltar" no `Configuracoes.vue`** (header da tela) ✅ *Concluído em 2026-05-22*
  - Ação: `router.push('/dashboard')`
  - Posição: canto superior esquerdo, antes do título "Configurações"
  - Testar: Ambas as telas devem ter caminho de retorno sem depender do botão do navegador

### P11.4 — Frontend: Portal do Cliente acessível antes da hora
- [x] **Restringir botões de acesso ao portal no `ProjectCard.vue`** ✅ *Concluído em 2026-05-22*
  - Linhas 616 e 631 (dropdown menu) e linhas 786-812 (botões fixos): mudar condição de `project.coluna === 'engenharia_caixa' || project.coluna === 'obra_liberada'` para apenas `project.coluna === 'obra_liberada'`
  - **Motivo:** O portal só deve ser acessível após a Caixa aprovar e o contrato ser assinado. A coluna `engenharia_caixa` é pré-aprovação — liberar o portal nessa fase é prematuro (ver PRODUTO.md seção 4.7)
  - Testar: Card na coluna `engenharia_caixa` NÃO deve mostrar botão "Portal" nem "Copiar Link do Portal". Card em `obra_liberada` deve continuar mostrando normalmente

### P11.5 — Frontend: Mês de referência sempre mais recente no Setup
- [x] **Garantir que o mês mais recente seja selecionado automaticamente no `SetupOrcamentoModal.vue`** ✅ *Concluído em 2026-05-22*
  - Verificar: `carregarReferencias()` já seta `form.value.sinapi_mes_ano = res.data.data[0]` quando o campo está vazio — confirmar que `res.data.data[0]` retorna o mês mais recente (ordenação na API)
  - Verificar em `routers/sinapi.py`: endpoint `/sinapi/referencias` — confirmar que os meses estão ordenados DESC (mais recente primeiro)
  - Se não estiver ordenado: adicionar `.order('mes_ano', desc=True)` na query
  - Testar: Abrir Setup em qualquer projeto → campo Mês deve mostrar automaticamente o mês mais recente disponível

---

## P12 — UX: Card Expansível e Visão Detalhada do Projeto

> **Contexto:** O engenheiro precisa navegar para `/orcamento/:id` para ver qualquer detalhe além do card do Kanban. A proposta é um painel "quick-look" que mostre informações críticas sem sair da esteira — reduzindo fricção no dia a dia. **Ler as dúvidas abaixo antes de iniciar qualquer subtarefa.**

### Dúvidas a resolver antes de implementar

- **Escopo vs. duplicação com `Orcamento.vue`:** O card expansível é complementar (quick-look rápido) ou substitui parte da navegação? Se for rico demais, criamos dois lugares para a mesma informação. Sugestão: o drawer mostra *status* e *histórico*, nunca edição — edição sempre vai para `Orcamento.vue`.
- **Trigger de abertura:** Clicar em qualquer parte do card? Um ícone dedicado `open_in_full` no canto superior direito? Um item "Ver detalhes" no dropdown? Ícone é mais previsível, clique-geral tem risco de conflito com outros cliques do card.
- **Apresentação:** Painel lateral deslizante (drawer, ~40% da tela) — mais confortável para leitura. Modal centralizado — mais simples de implementar. Expansão inline do card — quebra o layout do Kanban. **Recomendação: drawer lateral.**
- **Mobile:** Drawer lateral não funciona bem em telas pequenas. Opções: bottom sheet, modal full-screen, ou desabilitar o recurso em mobile (≤ 640px) e só exibir no desktop.
- **Conteúdo mínimo viável:** O que o engenheiro consulta frequentemente que não está visível no card? Sugestão: documentos com status por categoria (✅ Identidade, ❌ Residência reprovada, ⏳ Estado Civil pendente), contrato (gerado/assinado/link), dados de contato do cliente (telefone, e-mail), últimas 5 entradas do histórico.
- **Carregamento dos dados:** Lazy (busca ao abrir o drawer, com loading spinner) ou eager (já embarcados no card via Realtime)? Lazy é mais simples, eager é mais rápido mas exige que o Dashboard já carregue esses dados.
- **Dependência de P9.1:** O histórico da linha do tempo (tab de `projetos_historico`) não está conectado ao frontend ainda. O drawer vai mostrar placeholder até P9.1 ser implementado — isso é aceitável?
- **Dependência de P8.2/P8.3:** O status individual de cada documento (aprovado/reprovado/pendente) só existe após P8.2 (backend) e P8.3 (fluxo de rejeição). O drawer pode mostrar a lista de documentos sem status detalhado até lá.

### P12.1 — Frontend: Botão "Expandir" no `ProjectCard.vue`
- [x] Adicionar ícone `open_in_full` no header do card, ao lado do menu dropdown (três pontos) ✅ *Concluído*
- [x] `v-on:click.stop` para não propagar para outros handlers do card ✅ *Concluído*
- [x] Controlar visibilidade com `isDrawerOpen = ref(false)` ✅ *Concluído*

### P12.2 — Frontend: Criar `DrawerDetalheProjeto.vue`
- [x] **Props:** `isOpen: Boolean`, `project: Object` ✅ *Concluído*
- [x] **Emits:** `'close'`, `'update'` ✅ *Concluído*
- [x] **Estrutura do drawer:** painel fixo à direita, overlay escuro atrás ✅ *Concluído*
- [x] **Seção 1 — Identificação:** nome da obra, cliente, coluna atual (badge colorido por estágio), UF, BDI, mês SINAPI ✅ *Concluído*
- [x] **Seção 2 — Documentos:** lista das 3 categorias com ícone de status ✅ *Concluído*
- [x] **Seção 3 — Contrato:** status do contrato, link para download/visualização ✅ *Concluído*
- [x] **Seção 4 — Histórico:** últimas entradas de `GET /projetos/{id}/historico` ✅ *Concluído*
- [x] **Seção 5 — Ações rápidas:** "Abrir Orçamento", "Enviar Portal", "Copiar Link Portal" ✅ *Concluído*

### P12.3 — Frontend: Sincronização de estado após ações no drawer
- [x] Após ação no drawer, o card no Kanban reflete a mudança via `@update="emit('update')"` → `Dashboard.fetchProjetos` ✅ *Concluído*
- [x] `Dashboard.vue` usa Realtime (`supabase.channel('kanban-projetos')`): mudanças via API se propagam automaticamente ✅ *Confirmado*

---

## P13 — CRÍTICO: Exportar Planilha SINAPI

> **Contexto:** O engenheiro monta a planilha no `Orcamento.vue` mas não tem como extrair o arquivo para submeter à Caixa Econômica. Sem esse botão, o fluxo da obra trava nesta etapa — é o maior gargalo do produto hoje.

### P13.1 — Backend: Endpoint de geração de planilha SINAPI (PDF e Excel)
- [x] **Criar rota** `GET /api/projetos/{id}/exportar-sinapi?formato=pdf|xlsx` em `routers/relatorios.py` ✅ *Concluída em 2026-05-25*
  - Parâmetro `formato` aceita `pdf` (padrão) ou `xlsx`
  - Dados comuns: busca projeto + itens, agrupa por etapa (5 fases EAP + fallback "Outros")
  - **PDF:** A4 paisagem, cabeçalho com dados da obra, tabela por etapa, subtotais, total geral destacado
  - **Excel:** `openpyxl` com estilos, larguras de coluna definidas, células numéricas (não texto), cabeçalho congelado, subtotais por etapa, total geral formatado como moeda
  - Retorna `StreamingResponse` com `Content-Disposition: attachment` e nome de arquivo dinâmico
  - Rejeita com 422 se o projeto não tiver itens

### P13.2 — Frontend: Botões "Exportar" no `Orcamento.vue`
- [x] **Adicionar dois botões** "Exportar PDF" e "Exportar Excel" no header da tela de orçamento ✅ *Concluída em 2026-05-25*
  - Ficam abaixo do botão "Configurações da Obra", lado a lado, visíveis apenas quando `activeOrcamentoId` existe
  - Chamam `GET /api/projetos/{id}/exportar-sinapi?formato=pdf|xlsx` via `axios` com `responseType: 'blob'`
  - Download automático pelo browser com nome dinâmico baseado no nome da obra
  - Estado de loading individual por formato: ícone `sync` animado + texto "Gerando..." enquanto processa
  - Botão PDF com hover vermelho; botão Excel com hover verde — diferenciação visual clara
  - Se projeto sem itens (422), exibe toast: "Adicione itens ao orçamento antes de exportar."

---

## P14 — ALTA: Motor de Contratos — Separação por Tipo

> **Contexto:** O sistema tem dois documentos distintos: **Proposta Comercial** (valores do CUB, gerada logo após aceitar o lead) e **Contrato de Construção** (valores reais do SINAPI, gerado após planilha pronta). Hoje os templates são genéricos sem distinção, o que pode causar geração do documento errado na hora errada.

### P14.1 — Backend: Adicionar campo `tipo` nos templates de contrato
- [ ] **Criar migration** `006_tipo_template_contrato.sql`: adicionar coluna `tipo text DEFAULT 'proposta' CHECK (tipo IN ('proposta', 'contrato'))` na tabela `templates_contrato`
- [ ] **Atualizar endpoints** em `routers/integracoes.py`:
  - `POST /contratos-templates` — aceitar campo `tipo` no payload
  - `GET /contratos-templates` — retornar `tipo` em cada template
  - `GET /contratos-templates/{id}` — retornar `tipo`
- [ ] **Injetar variáveis SINAPI** no `gerar_contrato()`: buscar `orcamento_itens` do projeto e injetar `{{valor_total_sinapi}}`, `{{mes_referencia_sinapi}}`, `{{bdi}}`, `{{valor_por_m2_sinapi}}` no template antes de gerar o PDF

### P14.2 — Frontend: Separar lista de templates em `ConfiguracoesContratos.vue`
- [ ] **Dividir a lista lateral** em dois grupos com separador visual:
  - Grupo "PROPOSTAS COMERCIAIS" — templates com `tipo === 'proposta'`
  - Grupo "CONTRATOS DE CONSTRUÇÃO" — templates com `tipo === 'contrato'`
  - Botão "+ Nova proposta" e "+ Novo contrato" separados
- [ ] **Editor de template**: ao criar/editar, mostrar apenas as variáveis disponíveis para o tipo selecionado (ver tabela no PRODUTO.md Seção 3.0)
- [ ] Testar: Criar uma proposta e um contrato — cada um deve aparecer no grupo correto; variáveis disponíveis devem ser as do tipo

### P14.3 — Frontend: Restringir geração de contrato por fase no `ProjectCard.vue`
- [ ] **Botão "Gerar Proposta Comercial"**: visível a partir de `contrato_pendente` (lead aceitou, docs analisados)
  - Usa template do tipo `proposta`; injeta variáveis do CUB
- [ ] **Botão "Gerar Contrato de Construção"**: visível apenas quando `coluna === 'engenharia_caixa'` **e** `total_sinapi > 0` (planilha tem itens)
  - Usa template do tipo `contrato`; injeta variáveis reais do SINAPI
- [ ] Testar: Projeto em `estimativa_enviada` não deve ter nenhum botão de geração de documento; projeto em `engenharia_caixa` sem itens SINAPI deve ter o botão desabilitado com tooltip explicativo

---

## P15 — MÉDIA: EstimativaWizard — CUB Real por UF

> **Contexto:** O Passo 3 do wizard usa preços fixos hardcoded (R$1.800/2.800/4.500 por m²) em vez de usar o endpoint `/api/simulador/calcular` que já existe e retorna o CUB real por estado. Um cliente do Pará recebe estimativa com custo de SC — cria expectativa errada na primeira interação.

### P15.1 — Frontend: Conectar wizard ao simulador real
- [ ] **Substituir o cálculo local** `metragem_total * padraoSelecionado.precoBase` pela chamada `POST /api/simulador/calcular` com `{ padrao, metragem, uf: ufObra }`
  - O estado `ufObra` já existe no wizard (linha 20 do `EstimativaWizard.vue`)
  - Exibir skeleton/loading enquanto a API responde
  - Fallback para preço fixo se a API falhar (para não quebrar o fluxo)
- [ ] **Garantir que a UF está preenchida antes do Passo 3**: se `ufObra` ainda for o default `'SC'` e o projeto vier de uma vitrine (que já sabe a UF do engenheiro), passar a UF via query param automaticamente
- [ ] Testar: Selecionar "Alto Padrão" + 100m² + UF = PA → valor deve vir do CUB do Pará, diferente do valor anterior fixo

---

## P16 — MÉDIA: Substituir `alert()` por `showToast()` no `ProjectCard.vue`

> **Contexto:** O sistema usa `showToast()` como padrão visual de feedback ao usuário. O `ProjectCard.vue` ainda tem 14 ocorrências de `alert()` nativo do browser que quebram a UX (janela modal bloqueante, sem estilo, fora do contexto visual).

### P16.1 — Frontend: Migrar todos os `alert()` para `showToast()`
- [ ] **Importar** `useToast` em `ProjectCard.vue` (padrão: `import { useToast } from '../composables/useToast'`)
- [ ] **Substituir** as 14 ocorrências de `alert(mensagem)` por `showToast(mensagem, 'error')` — linhas 198, 202, 226, 230, 269, 295, 313, 358, 419, 456, 520, 582, 607, 688
- [ ] Mensagens de sucesso que usem `alert` devem usar `showToast(msg, 'success')`
- [ ] Testar: Simular um erro de rede em cada ação do card — feedback deve aparecer como toast, não como popup do browser

---

## P17 — BAIXA: Sub-status visual nos cards do Kanban

> **Contexto:** A coluna `estimativa_enviada` comprime 4 estados do lead em uma única visão. O engenheiro não sabe, olhando para o card, se o cliente ainda não acessou o wizard, se está no meio, ou se enviou os documentos. O campo `project.status` já existe no banco com esse detalhe — falta renderizá-lo.

### P17.1 — Frontend: Badge de sub-status no `ProjectCard.vue`
- [ ] **Adicionar badge** abaixo do nome da obra no card exibindo o sub-status legível:
  - `aguardando_cliente` → badge cinza "Aguardando cliente"
  - `em_qualificacao` → badge amarelo "Wizard em andamento"
  - `docs_completos` → badge verde "Docs enviados ✓"
  - `docs_validados` → badge azul "Docs validados ✓"
  - Para outras colunas, não exibir badge (o nome da coluna já é suficiente)
- [ ] Testar: Card em `estimativa_enviada` com `status = 'docs_completos'` deve mostrar badge verde; card com `status = 'aguardando_cliente'` deve mostrar badge cinza

---

## P18 — BAIXA: UF padrão do engenheiro nas Configurações

> **Contexto:** O `SetupOrcamentoModal` tem fallback hardcoded para `'SC'` quando o campo UF está vazio (corrigido para `''` em P11.2, mas ainda sem um padrão inteligente). O engenheiro que atua em SP vai selecionar SP em cada novo projeto. A solução é uma UF padrão salva no perfil.

### P18.1 — Backend/Frontend: Campo "UF de atuação padrão" no perfil
- [ ] **Adicionar campo** `uf_atuacao_padrao text` na tabela `perfis_b2b` (ou reutilizar campo existente se houver)
- [ ] **Adicionar input** de UF no `TabPerfil.vue` (select com todas as UFs, salva via `PATCH /configuracoes/perfil`)
- [ ] **Consultar o padrão** no `SetupOrcamentoModal.vue`: ao abrir, se `project.uf_obra` estiver vazio, pré-selecionar `perfil.uf_atuacao_padrao` (se configurado)
- [ ] **Consultar o padrão** no `EstimativaWizard.vue`: se vier sem `uf` na query, usar `uf_atuacao_padrao` do engenheiro da vitrine como sugestão inicial
- [ ] Testar: Configurar UF padrão como "RJ" → abrir Setup em novo projeto → campo UF deve vir pré-selecionado como "RJ"

---

## MAPA DE DEPENDÊNCIAS

```
P1.2 ──→ P1.3  (Backend muda prefixo → Frontend atualiza URL)
P1.1          (Independente)
P2.1          (Independente, mas testar após P1.2)
P2.2          (Independente)
P2.3          (Independente)
P3.1          (Independente)
P3.2          (Independente)
P3.3          (Independente)
P3.4          (Independente, mas idealmente após P3.2)
P4.1 ──→ P4.3 (Backend cria API → Frontend consome)
P4.2 ──→ P4.3 (Backend cria matchmaking → Frontend exibe)
P4.4          (Depende de P4.1)
P5.1 ──→ P5.2 ──→ P5.3
P6.1 ──→ P6.2 ──→ P6.3 ──→ P6.4
P13.1 ──→ P13.2 (Backend cria endpoint → Frontend adiciona botão)
P14.1 ──→ P14.2 ──→ P14.3 (Migration → UI separada → Restrição por fase)
P15.1         (Independente — mas idealmente após P18.1 para UF padrão estar disponível)
P16.1         (Independente — sem dependências)
P17.1         (Independente — sem dependências)
P18.1         (Independente — sem dependências)
```

---

## ESTIMATIVA DE ESFORÇO

| ID | Tarefa | Complexidade | Arquivos Afetados |
|---|---|---|---|
| P1.1 | Corrigir `async def` → `def` | 🟢 Trivial | 1 (`integracoes.py`) |
| P1.2 | Migrar relatorios para `projetos_clientes` | 🟡 Média | 1 (`relatorios.py`) |
| P1.3 | Ajustar URL do PDF no frontend | 🟢 Trivial | 1 (`FinancialSummary.vue`) |
| P2.1 | Migrar portal_cliente | 🟡 Média | 1-2 (`portal_cliente.py` + migration) |
| P2.2 | Consolidar `extrair_usuario_id` | 🟢 Simples | 1 (`projetos.py`) |
| P2.3 | Composições SINAPI | 🔴 Complexa | 2 (`sinapi.py`, `sinapi_bot.py`) |
| P2.4 | Depreciar schema SQL | 🟢 Trivial | 1 (`supabase_schema.sql`) |
| P3.1 | Unificar modais Share | 🟡 Média | 4 (criar 1, editar 2, deletar 2) |
| P3.2 | Extrair `formatCurrency` | 🟢 Simples | 6 (criar 1, editar 5) |
| P3.3 | Extrair `etapas[]` | 🟢 Simples | 4 (criar 1, editar 3) |
| P3.4 | Remover modal inline | 🟡 Média | 1 (`FinancialSummary.vue`) |
| P4.1 | Simulação paramétrica | 🟢 Simples | 2 (`simulador.py`, `main.py`) |
| P4.2 | Banco Matchmaking | 🟡 Média | 3 (`001_engenheiros.sql`, `matchmaking.py`, `main.py`) |
| P4.3 | Matchmaking no Wizard | 🟡 Média | 2-3 (`EstimativaWizard.vue`, `matchmaking.py`) |
| P4.4 | Landing Page B2C | 🟡 Média | 2 (`LandingSimulador.vue`, `router.js`) |
| P5.x | Portal do Cliente Avançado | 🔴 Épico | Timeline, Caixômetro, Doc Vault, Upload Mobile |
| P6.x | Vitrine Pública B2B2C | 🔴 Épico | Colunas perfil, Configuração, Rota `/p/:slug` |
| P13.1 | Endpoint exportar SINAPI (PDF) | 🟡 Média | 1 (`relatorios.py`) |
| P13.2 | Botão exportar no `Orcamento.vue` | 🟢 Simples | 1 (`Orcamento.vue`) |
| P14.1 | Migration + campo `tipo` nos templates | 🟢 Simples | 2 (`migration`, `integracoes.py`) |
| P14.2 | UI separada por tipo em ConfiguracoesContratos | 🟡 Média | 1 (`ConfiguracoesContratos.vue`) |
| P14.3 | Restringir geração de doc por fase no ProjectCard | 🟡 Média | 1 (`ProjectCard.vue`) |
| P15.1 | Wizard usando CUB real por UF | 🟡 Média | 1 (`EstimativaWizard.vue`) |
| P16.1 | Substituir `alert()` por `showToast()` | 🟢 Trivial | 1 (`ProjectCard.vue`) |
| P17.1 | Badge de sub-status nos cards | 🟢 Simples | 1 (`ProjectCard.vue`) |
| P18.1 | UF padrão do engenheiro no perfil | 🟡 Média | 3 (`perfis_b2b`, `TabPerfil.vue`, `SetupOrcamentoModal.vue`) |
