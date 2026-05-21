# TEST_PLAN.md — Agente Validador Estático

> **Este plano define o comportamento esperado das funcionalidades críticas do SaaS. Qualquer implementação ou refatoração que altere o comportamento descrito aqui DEVE atualizar este documento antes do merge.**

---

## MÓDULO 1: GERAÇÃO DE RELATÓRIOS E CONTRATOS EM PDF

### Referências de Código
- `routers/relatorios.py` → `gerar_pdf_comercial()` — `def` (sync, thread pool)
- `routers/integracoes.py` → `gerar_contrato()` — `def` (sync, thread pool)
- `routers/integracoes.py` → `enviar_para_zapsign()` — `async def` (httpx async)
- `utils/pdf_generator.py` → `generate_contract_pdf()` — sync, CPU-bound (fpdf2)
- `FinancialSummary.vue` → `baixarPropostaPDF()` — axios GET com `responseType: 'blob'`

---

### Cenário 1.1: Gerar Proposta Comercial PDF com Sucesso

> **DADO** um projeto com itens no orçamento e BDI configurado  
> **QUANDO** o engenheiro clica em "Gerar Proposta Comercial"

- **Frontend:**
  - `isDownloadingPDF = true` → botão exibe spinner `progress_activity` + texto "Gerando PDF..."
  - Botão fica `disabled` até conclusão
  - Ao receber blob → cria `<a>` temporário, dispara download, revoga `ObjectURL`
  - Toast ou alert em caso de falha (decodifica blob de erro via `.text()` → `JSON.parse`)

- **Backend:**
  - Rota `GET /api/orcamentos/{id}/pdf-comercial` é `def` (não `async def`) → **FastAPI delega automaticamente para thread pool** → event loop NÃO bloqueia
  - Busca dados do orçamento e itens via `supabase_client` autenticado (RLS respeitado)
  - BDI aplicado **apenas no PDF** via `fator_bdi = 1 + (bdi / 100)` → `valor_venda = custo * fator_bdi`
  - Valor unitário persistido no banco **NÃO é alterado** — o BDI é um fator multiplicador efêmero
  - Retorna `StreamingResponse(buffer, media_type="application/pdf")` → HTTP 200
  - Strings longas truncadas em 45 chars para não quebrar layout da tabela

- **Critério de Aceite:**
  - ✅ PDF gerado em ≤ 5s para orçamentos com até 200 itens
  - ✅ Event loop do Uvicorn processa outras requisições simultaneamente durante a geração
  - ✅ Valores no PDF = `valor_unitario * fator_bdi * quantidade` (nunca o custo puro)
  - ✅ Valores no banco permanecem inalterados após download

---

### Cenário 1.2: Gerar Contrato + Enviar para ZapSign

> **DADO** um projeto com template de contrato selecionado  
> **QUANDO** o engenheiro aciona "Enviar para ZapSign"

- **Frontend:**
  - Spinner ativo durante request
  - Toast de sucesso com token do documento

- **Backend:**
  - `gerar_contrato()` é `def` → thread pool (CPU-bound: fpdf2)
  - `enviar_para_zapsign()` é `async def` → usa `httpx.AsyncClient` (I/O-bound)
  - Substituição de placeholders: `{{cliente_nome}}`, `{{tamanho}}`, `{{padrao}}`, `{{valor}}`
  - PDF convertido para `base64` antes do envio
  - ZapSign response salva em `projetos_clientes`: `zapsign_document_token`, `url_assinatura_cliente`, `url_assinatura_engenheiro`, `status_assinatura = 'pendente'`
  - Histórico registrado: `acao = "Contrato Gerado"`

- **Critério de Aceite:**
  - ✅ `httpx.AsyncClient(timeout=30.0)` impede hang indefinido
  - ✅ Se ZapSign retorna status ≠ 200/201 → HTTP 502 com `detail: "Erro ZapSign: {resp.text}"`
  - ✅ `ZAPSIGN_API_TOKEN` ausente → HTTP 500 antes de qualquer processamento

---

### Cenário 1.3: Falha na Geração de PDF — Orçamento Não Encontrado

> **DADO** um `orcamento_id` inexistente ou de outro tenant  
> **QUANDO** a rota de PDF é chamada

- **Backend:**
  - Supabase retorna `data: []` por causa do RLS → `orc_res.data` vazio
  - Rota lança `HTTPException(404, "Orçamento não encontrado")`
  - Exception handler injeta CORS headers na resposta de erro

- **Frontend:**
  - Decodifica blob de erro: `error.response.data.text()` → parse JSON → exibe `detail` em alert
  - `isDownloadingPDF = false` no bloco `finally`

---

## MÓDULO 2: MOTOR DE BUSCA SINAPI E APLICAÇÃO DO BDI

### Referências de Código
- `routers/sinapi.py` → `get_sinapi_items()` — validação de `projeto_id` server-side
- `Orcamento.vue` → `buscarItens()`, `fetchProjectData()`
- `ArvoreCustos.vue` → `totalComBdi` (computed), `subtotalEtapa()`
- `SinapiTable.vue` → componente dumb, exibe `item.preco` sem BDI

---

### Cenário 2.1: Busca SINAPI Impõe Parâmetros do Projeto (Server-Side Override)

> **DADO** um projeto com `uf_obra = 'SC'`, `sinapi_desonerado = false`, `sinapi_mes_ano = '03/2026'`  
> **QUANDO** o frontend envia `GET /api/sinapi?projeto_id=xxx&estado=RJ&desonerado=true`

- **Frontend:**
  - Envia `projeto_id` via query param (`params.projeto_id = route.params.id`)
  - Filtros locais (`filterUf`, `filterDesonerado`, `filterMesAno`) são sincronizados com o projeto no `fetchProjectData()` — mas são **decorativos** quando `projeto_id` está presente

- **Backend (Regra Inquebrável):**
  - Se `projeto_id` presente → busca `uf_obra`, `sinapi_desonerado`, `sinapi_mes_ano` direto do banco
  - **SOBRESCREVE** qualquer valor enviado pelo frontend: `estado = proj["uf_obra"]`, etc.
  - Query final ao `sinapi_itens` usa APENAS os valores do banco
  - Paginação: `range(start_idx, end_idx)` com `count="exact"` para total

- **Critério de Aceite:**
  - ✅ Mesmo que o frontend envie `estado=RJ`, a resposta contém APENAS itens de `SC`
  - ✅ Mesmo que `desonerado=true` no query, se o projeto tem `false`, retorna não-desonerado
  - ✅ Nenhuma manipulação de parâmetros no DevTools/Postman altera o resultado da busca vinculada a projeto
  - ✅ Sem `projeto_id`, os filtros do frontend são respeitados normalmente (busca livre)

---

### Cenário 2.2: BDI Aplicado Exclusivamente na Camada de Apresentação

> **DADO** um projeto com `bdi_padrao = 25.00` e itens com `valor_unitario` persistido  
> **QUANDO** o engenheiro visualiza a Árvore de Custos

- **Frontend (ArvoreCustos.vue):**
  - `totalGeral` = `Σ(item.quantidade * item.valor_unitario)` → custo puro, sem BDI
  - `totalComBdi` = `totalGeral * (1 + bdi/100)` → calculado em `computed`, **nunca persistido**
  - Cada item exibe `valor_unitario` original na lista (sem BDI)
  - Footer exibe: Subtotal (sem BDI) | BDI % | Total Final (com BDI)

- **Backend:**
  - `GET /api/projetos/{id}/itens` retorna `valor_unitario` cru do banco
  - `PATCH /api/projetos/{id}/itens/{item_id}` aceita **apenas** `quantidade` e `etapa_obra` — **não permite alterar `valor_unitario`** (whitelist explícita)
  - `POST /api/projetos/{id}/itens` persiste `valor_unitario` conforme enviado (preço SINAPI snapshot)

- **Critério de Aceite:**
  - ✅ O campo `valor_unitario` no banco é SEMPRE o preço de custo SINAPI, nunca o preço de venda
  - ✅ O BDI nunca aparece como coluna/campo na tabela `orcamento_itens`
  - ✅ O PDF comercial aplica BDI via `fator_bdi` em memória — o banco NÃO é tocado
  - ✅ Alterar `bdi_padrao` do projeto reflete IMEDIATAMENTE na Árvore de Custos (reatividade Vue)

---

### Cenário 2.3: Busca por Código SINAPI com Zeros à Esquerda

> **DADO** a busca `q = "00938"` no campo de pesquisa  
> **QUANDO** o backend processa a query

- **Backend:**
  - Detecta que `q` é numérico via `q_str.isdigit()`
  - Gera `q_clean = q_str.lstrip('0')` → `"938"`
  - Filtra com `OR`: `descricao ILIKE %00938%` OU `codigo_item ILIKE %00938%` OU `codigo_item ILIKE %938%`
  - Se `q_clean` ficar vazio (ex: `"000"`), usa `"0"` como fallback

- **Critério de Aceite:**
  - ✅ Buscar `"938"` e `"00938"` retorna os mesmos resultados
  - ✅ Busca textual (`"CONCRETO"`) funciona normalmente via `ilike`
  - ✅ Debounce de 300ms no frontend evita queries desnecessárias

---

## MÓDULO 3: UPLOAD EM LOTE DA PLANILHA SINAPI (SYNC)

### Referências de Código
- `routers/sinapi.py` → `sync_sinapi()` (insumos) + `sync_composicoes()` (composições)
- `sinapi_bot.py` → `processar_planilha_insumos()`, `processar_planilha_composicoes()`, `bulk_insert_composicoes()`
- `AdminSync.vue` → formulário de upload com overlay de loading
- SQL: `upsert_sinapi_lote` (RPC), `uq_sinapi_itens_chave_natural` (constraint)

---

### Cenário 3.1: Upload de Insumos com Chunking via RPC

> **DADO** uma planilha `.xlsx` com 18.000 registros SINAPI  
> **QUANDO** o admin clica em "Sincronizar Insumos"

- **Frontend (AdminSync.vue):**
  - Valida presença de arquivo (`file.value != null`) antes do submit
  - `isUploading = true` → overlay com spinner `sync` + "Processando dados da Caixa..."
  - Overlay cobre todo o formulário (`absolute inset-0 z-50`) → impede double-submit
  - Sucesso → `alertType = 'success'` + mensagem do backend + `file.value = null`
  - Erro → `alertType = 'error'` + mensagem genérica ou do servidor

- **Backend:**
  - Recebe `multipart/form-data` (file + mes_ano + desonerado)
  - Salva arquivo temporário em `temp/sinapi_upload_{uuid}.xlsx`
  - `SinapiBot.processar_planilha_insumos()` → retorna DataFrame pandas
  - Converte DataFrame para `list[dict]` via `.to_dict('records')`
  - **Chunking:** `chunk_size = 5000` → loop `range(0, total, 5000)` → cada lote enviado via `supabase_client.rpc("upsert_sinapi_lote", {"payload": lote})`
  - Stored Procedure faz `UPSERT` (insert ou update) → constraint `uq_sinapi_itens_chave_natural` impede duplicatas
  - Arquivo temp removido no `finally` (mesmo em caso de erro)

- **Critério de Aceite:**
  - ✅ 18.000 registros = 4 lotes (5000 + 5000 + 5000 + 3000)
  - ✅ Se o lote 3 falha → HTTP 500 com mensagem: `"Falha ao processar o lote 3 (registros 10000 a 15000): {erro}"`
  - ✅ Lotes 1 e 2 já persistidos NÃO são revertidos (sem transação global) — operação idempotente via UPSERT
  - ✅ Arquivo temporário é removido mesmo em caso de exceção
  - ✅ O event loop do Uvicorn continua responsivo durante o processamento (rota é `async def` mas operações de I/O são await)

---

### Cenário 3.2: Upload de Composições com Agendamento

> **DADO** que o toggle "Processamento Agendado" está ativo  
> **QUANDO** o admin define data `2026-05-20 03:00` e clica "Agendar Sincronização"

- **Frontend:**
  - `isScheduled = true` → exibe campo `datetime-local`
  - Valida que `activationDate` não está vazio antes do submit
  - Botão muda visual: fundo `indigo-600` + texto "Agendar Sincronização" + ícone `event_upcoming`
  - `isLoadingComp = true` → overlay de loading idêntico ao cenário 3.1

- **Backend:**
  - Arquivo salvo em `uploads/sinapi_schedules/` (diretório permanente, não temp)
  - Data parseada: `datetime.fromisoformat()` com fallback `strptime("%Y-%m-%d %H:%M:%S")`
  - Job adicionado ao `APScheduler`: `scheduler.add_job(job_processar_composicoes, 'date', run_date=..., args=[file_path])`
  - Response imediata: `{"success": true, "message": "Processamento agendado para 20/05/2026 03:00"}`
  - O job roda no futuro → chama `SinapiBot` → `bulk_insert_composicoes()` → remove arquivo após conclusão

- **Critério de Aceite:**
  - ✅ Response HTTP 200 retorna em < 2s (apenas agendou, não processou)
  - ✅ Arquivo NÃO é removido na resposta — só após execução do job
  - ✅ Se erro no agendamento → arquivo temp é removido imediatamente + HTTP 400
  - ✅ `ENABLE_SCHEDULER=true` é pré-requisito — scheduler inicia no lifespan

---

### Cenário 3.3: Upload sem Arquivo Selecionado

> **DADO** que o campo de arquivo está vazio  
> **QUANDO** o admin clica em "Sincronizar"

- **Frontend:**
  - Validação local: `if (!file.value)` → seta `alertType = 'error'` + `alertMessage = 'Por favor, selecione um arquivo Excel.'`
  - **Nenhuma requisição HTTP é disparada**
  - `isUploading` permanece `false`

- **Critério de Aceite:**
  - ✅ Zero tráfego de rede
  - ✅ Alerta visual vermelho com ícone `error` visível imediatamente

---

### Cenário 3.4: Constraint de Deduplicação (Idempotência)

> **DADO** que a mesma planilha SINAPI (mesmo mês/ano/estado/desonerado) já foi importada  
> **QUANDO** o admin faz upload novamente

- **Backend:**
  - RPC `upsert_sinapi_lote` executa `INSERT ... ON CONFLICT ... DO UPDATE`
  - Constraint `uq_sinapi_itens_chave_natural` (`codigo_item`, `estado`, `mes_ano`, `desonerado`)
  - Registros existentes são **atualizados** (preço atualizado), não duplicados

- **Critério de Aceite:**
  - ✅ `SELECT COUNT(*) FROM sinapi_itens WHERE mes_ano = 'XX/XXXX'` retorna o mesmo total antes e depois do re-upload
  - ✅ Preços podem mudar se a planilha trouxer valores diferentes (update)
  - ✅ Nenhum erro de constraint é propagado ao frontend

---

## MÓDULO 4: FUNIL DE LEADS B2C E MATCHMAKING

### Referências de Código
- `routers/matchmaking.py` → `get_engenheiros()` — `GET /api/matchmaking` (público, sem JWT)
- `routers/matchmaking.py` → `solicitar_matchmaking()` — `POST /api/matchmaking/solicitar` (público, sem JWT, bypass RLS via `service_role`)
- `routers/simulador.py` → `calcular_simulacao()` — `POST /api/simulador/calcular` (público, sem JWT)
- `EstimativaWizard.vue` → Passo 4 ("Encontre seu Engenheiro")
- `LandingSimulador.vue` → `/simulador` (Landing Page)

---

### Cenário 4.1: Simulação Rápida (Custo CUB/SINAPI por UF)

> **DADO** o preenchimento de metragem, UF e padrão de acabamento na Landing Page B2C  
> **QUANDO** o cliente final solicita o cálculo da simulação

- **Frontend (LandingSimulador.vue):**
  - Botão de cálculo desabilitado e com spinner ativo durante a requisição
  - Sucesso → Exibe painel reativo com custo total, custo unitário por m² e a margem de financiamento da Caixa (80%)
  - Clique em "Personalizar & Encontrar Engenheiro" → Redireciona com query params para o Wizard

- **Backend:**
  - Rota `POST /api/simulador/calcular` é pública (sem JWT)
  - Calcula o custo estimado buscando no banco o valor de referência CUB para a UF especificada
  - Retorna o JSON estruturado contendo a simulação

- **Critério de Aceite:**
  - ✅ Retorno dos cálculos matemáticos de forma instantânea (≤ 1s)
  - ✅ Valores de referência por UF e padrão batem com a tabela de coeficientes cadastrada

---

### Cenário 4.2: Matchmaking com Engenheiros Disponíveis por UF

> **DADO** a seleção de estado (UF) e padrão de acabamento no Wizard B2C  
> **QUANDO** o cliente avança para o Step 4 ("Encontre seu Engenheiro")

- **Frontend (EstimativaWizard.vue):**
  - Dispara requisição reativa `GET /api/matchmaking?uf=XX&padrao=YY`
  - Exibe cards de profissionais cadastrados com avatar, nome, CREA/CAU e especialidades
  - Permite preenchimento do formulário de contato do lead

- **Backend:**
  - Rota `GET /api/matchmaking` busca engenheiros que atendem àquela UF
  - Retorna lista pública sanitizada (sem dados sensíveis ou informações privadas)

- **Critério de Aceite:**
  - ✅ Apenas engenheiros que atendem ao estado especificado são retornados
  - ✅ A lista reage imediatamente caso o usuário altere a UF nas etapas anteriores do Wizard

---

### Cenário 4.3: Criação de Lead com Bypass RLS

> **DADO** a escolha de um engenheiro e o preenchimento do formulário de contato  
> **QUANDO** o cliente final clica em "Solicitar Orçamento"

- **Backend:**
  - Recebe o payload do lead (nome, e-mail, telefone, padrão, metragem, uf, engenheiro_id)
  - Como não há sessão de usuário autenticado (B2C), instancia o cliente via `get_service_supabase()`
  - Cria o registro do projeto na tabela `projetos_clientes` com status `'Lead'` e associado ao `usuario_id` do engenheiro escolhido
  - Registra histórico de auditoria do lead

- **Critério de Aceite:**
  - ✅ Criação do projeto com sucesso mesmo sem cabeçalho `Authorization` JWT do cliente final
  - ✅ O lead fica visível apenas no painel do engenheiro selecionado (RLS ativo na visão do engenheiro)
  - ✅ Exibição de tela de sucesso customizada para o cliente final após resposta da API

---

## MATRIZ DE RISCOS

| Risco | Severidade | Mitigação Atual |
|---|---|---|
| PDF bloqueia event loop | 🔴 Crítica | `def` (sync) delega para thread pool automaticamente |
| Frontend manipula BDI no banco | 🔴 Crítica | PATCH whitelist aceita só `quantidade`/`etapa_obra` |
| Frontend altera filtro SINAPI de outro estado | 🟡 Alta | Backend sobrescreve com dados do projeto |
| Upload SINAPI de 50k+ registros causa timeout | 🟡 Alta | Chunking 5k + RPC |
| Duplicata SINAPI no re-upload | 🟢 Baixa | Constraint UNIQUE + UPSERT via RPC |
| Arquivo temp não removido após crash | 🟡 Alta | `finally` block no router |
| Scheduler desligado em produção | 🟡 Alta | `ENABLE_SCHEDULER` env var (default: false) |
| Inserção maliciosa/spam de Leads B2C | 🟡 Alta | Validação rígida com Pydantic Schema + Vinculação obrigatória a um engenheiro ativo |
