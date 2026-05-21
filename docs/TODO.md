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
- [ ] **Criar migration** `supabase/migrations/002_portal_cliente_avancado.sql`:
  - Tabela `obras_feed` (`id`, `projeto_id`, `descricao`, `imagens[]`, `criado_em`, `usuario_id`)
  - Tabela `projetos_documentos` (`id`, `projeto_id`, `nome_documento`, `arquivo_url`, `categoria`, `criado_em`)
  - RLS: Select público via token do projeto, insert/update/delete restrito ao engenheiro dono (`auth.uid() = usuario_id`).

### P5.2 — Backend: Endpoints de Acesso e Consumo
- [ ] **Criar rotas** públicas sob `routers/portal_cliente.py` (validadas por hash/PIN do link):
  - `GET /api/portal/projetos/{hash_link}/feed` -> retorna posts da timeline
  - `GET /api/portal/projetos/{hash_link}/documentos` -> retorna documentos do vault
  - `GET /api/portal/projetos/{hash_link}/caixa` -> retorna progresso físico/financeiro e juros de obra estimados

### P5.3 — Frontend: Linha do Tempo e Medição Caixa no Portal B2C
- [ ] **Criar Timeline Visual** no `PortalCliente.vue` para exibir fotos da obra com legendas ordenadas cronologicamente
- [ ] **Criar componente** `Caixometro.vue` mostrando o progresso da obra (etapas de medição da Caixa Econômica) e tooltip educacional explicando a taxa de evolução de obra (juros de obra)
- [ ] **Aba "Cofre de Documentos"** no `PortalCliente.vue` para listagem e download de PDFs (plantas, contratos, Habite-se)

### P5.4 — Frontend/Backend: Diário de Obra Mobile-First para o Engenheiro
- [ ] **Criar aba rápido "Diário de Obra"** no painel do engenheiro:
  - Focado em mobile/campo, permitindo tirar foto na hora e digitar descrição rápida
  - Implementar compressão de imagem em JS antes de salvar no Storage para otimização de custos de hospedagem

---

## P6 — FEATURE: Vitrine Pública do Construtor B2B2C

### P6.1 — Backend: Modelo de Vitrine e Perfil Público
- [ ] **Criar migration** para adicionar colunas à tabela `perfis_b2b`:
  - `slug_vitrine` (text unique), `descricao_vitrine` (text), `fotos_portfolio` (text[]), `cidades_atuacao` (text[])
- [ ] **Criar endpoints** em `routers/vitrine.py`:
  - `GET /api/vitrine/{slug}` (público) -> retorna dados públicos do engenheiro
  - `POST /api/vitrine/configurar` (privado com JWT) -> atualiza dados de portfólio

### P6.2 — Frontend: Configuração de Vitrine pelo Engenheiro
- [ ] **Criar painel** em `Configuracoes.vue` para edição de biografia, galeria de fotos de obras concluídas e definição da URL personalizada

### P6.3 — Frontend: Landing Page Pública do Engenheiro (`vertice.app/p/:slug`)
- [ ] **Criar rota pública dinâmica** `/p/:slug` no `router.js` com layout premium:
  - Exibir foto de perfil, registro CREA/CAU, cidades de atuação e fotos de portfólio
  - CTA destacado "Simular Custos e Solicitar Orçamento" que redireciona para o `EstimativaWizard` pré-selecionando o engenheiro para matchmaking direto

---

## P7 — FEATURE: Sincronização em Tempo Real (Realtime Kanban)

> **Contexto:** Quando o cliente B2C aprova a simulação ou faz upload de documentos, o card no Kanban do engenheiro deve se mover/atualizar instantaneamente sem necessidade de `F5`.

### P7.1 — Frontend: Escuta de Eventos via Supabase Realtime
- [ ] **Dashboard/Kanban:** Implementar inscrição (`supabase.channel('projetos').on('postgres_changes', ...).subscribe()`) para escutar `UPDATE` e `INSERT` na tabela `projetos_clientes`.
- [ ] **Reatividade:** Ao receber o payload do WebSocket, atualizar o array local do Vue para refletir as mudanças (mover coluna, alterar status) com transições visuais suaves.

---

## P8 — FEATURE: Upload Granular de Documentos B2C

> **Contexto:** Em vez de um botão de upload em lote, o cliente deve enviar cada documento exigido separadamente, facilitando a auditoria.

### P8.1 — Frontend: Modificar `EstimativaWizard.vue` (Step de Upload)
- [ ] **Separar Dropzones:** Criar 3 campos distintos para upload: 1. Identidade (RG/CNH), 2. Comprovante de Residência, 3. Certidão de Estado Civil.
- [ ] **Lógica de Upload:** Modificar o método `uploadFiles` para enviar os arquivos categorizados de forma que a API saiba qual documento é qual.

### P8.2 — Frontend/Backend: Auditoria no `ProjectCard.vue`
- [ ] **Backend:** Atualizar o schema/endpoint de recepção de documentos para armazenar a `categoria` do documento atrelada ao arquivo.
- [ ] **Frontend:** No card do Kanban, exibir os documentos com suas respectivas etiquetas (RG, Comprovante, etc.) em vez de apenas nomes genéricos de arquivo.

---

## P9 — FEATURE: Histórico de Auditoria e Rejeição de Documentos

> **Contexto:** Cada card deve ter uma "linha do tempo" real que registre ações automáticas e manuais. Além disso, o engenheiro deve poder rejeitar um documento específico, notificando o cliente.

### P9.1 — Backend/Frontend: Linha do Tempo Real do Projeto
- [ ] **Backend:** Criar a tabela `projetos_historico` (projeto_id, acao, detalhes JSONB, usuario_id, criado_em) caso não exista.
- [ ] **Backend:** Criar rotinas automáticas (triggers ou via API) para inserir registros no histórico quando: projeto criado, link gerado, documentos enviados, contrato gerado, contrato assinado.
- [ ] **Frontend (`ProjectCard.vue`):** Conectar o modal de "Histórico e Notas" (atualmente com dados estáticos) ao endpoint `GET /api/projetos/{id}/historico`.

### P9.2 — Backend/Frontend: Rejeição de Documentos e Correção B2C
- [ ] **Backend:** Criar endpoint `POST /api/projetos/{id}/documentos/rejeitar` que aceita o `id` do documento e um `motivo`. Este endpoint deve deletar o arquivo inválido, mudar o status do projeto para `docs_pendentes` (ou similar) e registrar a recusa no histórico.
- [ ] **Frontend (`ProjectCard.vue`):** Adicionar um botão de ação "Recusar" ao lado de cada documento no cofre do Kanban. Ao clicar, abrir modal pedindo o "Motivo".
- [ ] **Frontend (`PortalCliente.vue`):** Exibir alerta caso existam documentos rejeitados (com o motivo visível) e liberar o botão de upload apenas para o documento faltante/rejeitado.

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
P6.1 ──→ P6.2 ──→ P6.3
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
