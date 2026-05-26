# Documento de Produto — Engenharia & Caixa

> **Propósito:** Descrever o funcionamento esperado do sistema, o trajeto completo do usuário (engenheiro e cliente), os problemas identificados e as ideias para evolução. Este é o documento vivo de referência do produto — atualizar sempre que algo mudar ou for decidido.

---

## 1. Visão Geral do Sistema

O sistema tem dois tipos de usuário: o **Engenheiro** (usuário autenticado, paga pelo serviço) e o **Cliente** (acessa links específicos, sem cadastro próprio). Existe também um lado público de descoberta, voltado para B2C (prospects que encontram o engenheiro pela internet).

O produto resolve três problemas centrais:
1. **Qualificação de leads** — o engenheiro cadastra um possível cliente e o sistema conduz esse cliente por uma jornada de auto-qualificação (simulação de financiamento + envio de documentos).
2. **Gestão da obra** — depois do contrato assinado, o cliente acompanha a obra em tempo real por um portal dedicado.
3. **Orçamentação com SINAPI** — o engenheiro monta orçamentos com itens da tabela SINAPI + itens manuais, dentro de um projeto de obra.

---

## 2. Trajeto Completo do Sistema

### 2.1 Jornada do Lead (pré-obra)

```
ENGENHEIRO                                  CLIENTE
──────────                                  ───────

[1] Abre NovoClienteModal
    Preenche:
    • Nome do Cliente (obrigatório)
    • Nome da Obra / Projeto
    • Telefone / WhatsApp (obrigatório)
    • Observações Iniciais
    → POST /api/projetos
    → Projeto criado com status "lead"

[2] Card aparece na EngenhariaList
    Card mostra: nome, obra, status, data
    Botão "Compartilhar" → ShareLinkModal
    ShareLinkModal:
    • Auto-preenche PIN (últimos 4 dígitos do tel.)
    • Gera link seguro → /estimativa/:id
    • Botão: Copiar Link
    • Botão: Enviar pelo WhatsApp
      (mensagem automática com link + PIN)
                                             [3] Recebe link pelo WhatsApp
                                                 Acessa /estimativa/:id
                                                 
                                                 Passo 1 — Padrão da Obra:
                                                 • Popular (R$1.800/m²)
                                                 • Médio Padrão (R$2.800/m²)
                                                 • Alto Padrão (R$4.500/m²)

                                                 Passo 2 — Tamanho Aproximado:
                                                 • Cômodos com campo de área (m²)
                                                 • Para cômodos com múltiplas instâncias
                                                   (quartos, banheiros, vagas de garagem):
                                                   o cliente escolhe a quantidade e pode
                                                   inserir a área de cada um separado
                                                   OU informar a área total somada
                                                 • Sistema soma tudo → metragem total
                                                 • ⚠️ Ver melhoria detalhada na Seção 5.8

                                                 Passo 3 — Valor Estimado:
                                                 • Mostra estimativa (metragem × preço base)
                                                 • Botão "Acessar Simulador da Caixa"
                                                   → abre site da Caixa em nova aba
                                                 • Cliente faz simulação no site da Caixa
                                                 • Volta para o wizard
                                                 • Marca checkbox: "Confirmo que realizei
                                                   a simulação e tenho capacidade de
                                                   financiamento"
                                                 • Clica em "Aprovar"

                                             [4] Tela de Upload de Documentos:
                                                 • Drag & drop ou seleção de arquivos
                                                 • Documentos solicitados: RG, CPF,
                                                   comprovante de renda, etc.
                                                 • Após envio → Sala de Espera
                                                   ("Seus documentos foram enviados.
                                                    Em breve entraremos em contato.")

[5] Engenheiro vê status atualizado na lista
    (hoje: precisa abrir o sistema para ver)
    Status muda para "docs_completos"
    
    ⚠️ PROBLEMA: Engenheiro não é notificado.
       Depende de olhar o sistema manualmente.
```

---

### 2.2 Jornada da Obra (pós-proposta comercial)

```
ENGENHEIRO                                  CLIENTE
──────────                                  ───────

[6] Acessa projeto na EngenhariaList
    Abre orçamento (Orcamento.vue)
    Monta a planilha SINAPI:
    • Setup da Obra (UF, desoneração, mês, BDI)
    • Itens SINAPI (busca por código ou descrição)
    • Itens manuais (nome + valor direto)
    • Árvore de custos / resumo financeiro

[7] Exporta planilha SINAPI finalizada
    • Botão "Exportar" ao concluir os itens
    • Formatos: PDF e/ou Excel (.xlsx)
    • Arquivo contém: todos os itens, códigos,
      unidades, quantidades, preços unitários,
      BDI, total geral
    • ⚠️ Portal do Cliente BLOQUEADO até aqui —
      nenhum link de acesso à obra deve existir
      antes desta etapa estar concluída

[8] Submete planilha à Caixa Econômica
    (fora do sistema — processo da Caixa)
    • Engenheiro usa o arquivo exportado
    • Caixa analisa e aprova a obra

    ⚠️ FORA DO SISTEMA: essa etapa acontece
       externamente. O sistema pode oferecer
       um campo de "Marcar como aprovado pela
       Caixa" para avançar o status do projeto.

[9] Gera Contrato de Construção (pós-SINAPI)
    • Motor de Contratos → template tipo
      "Contrato de Construção"
    • Variáveis preenchidas com valores reais
      do SINAPI: {{valor_total_sinapi}},
      {{mes_referencia_sinapi}}, {{bdi}}, etc.
    • Envia para ZapSign (assinatura digital)
    → Ambas as partes assinam
    → Webhook atualiza status: contrato_assinado

[10] Portal do Cliente é DESBLOQUEADO
     Apenas após webhook confirmar assinatura
     ShareLinkModal → /portal/:token
     Envia link + PIN para o cliente pelo WhatsApp
                                             [11] Acessa /portal/:token
                                                  Insere PIN (últimos 4 dígitos do tel.)

                                                  Aba 1 — Diário de Obra:
                                                  • Feed cronológico de fotos e textos
                                                    publicados pelo engenheiro

                                                  Aba 2 — Evolução Caixa:
                                                  • Caixômetro com PCI/PFUI
                                                  • Medições e liberações da Caixa

                                                  Aba 3 — Documentos:
                                                  • Plantas, memoriais, contratos
                                                  • Download dos arquivos

                                                  Aba 4 — Dados da Obra:
                                                  • Informações gerais do projeto
                                                  • Observações do engenheiro

[Paralelo] Engenheiro alimenta o portal:
    • Publica fotos e textos no diário
    • Sobe documentos oficiais
    • Registra medições da Caixa
```

---

## 3. Tela de Configurações

### 3.0 Motor de Contratos — Separação entre Proposta e Contrato

Como definido na Seção 7, o sistema precisa de **dois tipos de documento** com momentos e variáveis distintos. A aba "Motor de Contratos" em Configurações deve refletir isso visualmente.

**O que precisa mudar na UI do Motor de Contratos:**

A lista lateral de templates deve ter uma separação clara em dois grupos:

```
┌─────────────────────────────────┐
│ PROPOSTAS COMERCIAIS            │  ← geradas com valores do CUB
│  + Nova proposta                │
│  • Proposta Padrão MCMV         │
│  • Proposta Alto Padrão         │
├─────────────────────────────────┤
│ CONTRATOS DE CONSTRUÇÃO         │  ← gerados com valores do SINAPI
│  + Novo contrato                │
│  • Contrato MCMV v1             │
│  • Contrato Particular          │
└─────────────────────────────────┘
```

**Por que separar:**
- Cada tipo usa variáveis diferentes. Proposta usa `{{valor_estimado}}` (CUB). Contrato usa `{{valor_total_sinapi}}` (SINAPI). O editor deve mostrar apenas as variáveis disponíveis para aquele tipo.
- O sistema precisa saber qual template usar em cada etapa do fluxo — não pode deixar o engenheiro escolher um contrato SINAPI antes de ter o orçamento pronto, nem uma proposta depois que o SINAPI já está fechado.
- O engenheiro sabe exatamente onde criar cada documento, sem precisar lembrar qual template é de qual tipo.

**Variáveis disponíveis por tipo:**

| Variável | Proposta Comercial | Contrato de Construção |
|----------|:-----------------:|:---------------------:|
| `{{cliente_nome}}` | ✅ | ✅ |
| `{{engenheiro_nome}}` | ✅ | ✅ |
| `{{crea_cau}}` | ✅ | ✅ |
| `{{uf_obra}}` | ✅ | ✅ |
| `{{metragem}}` | ✅ | ✅ |
| `{{padrao_obra}}` | ✅ | ✅ |
| `{{valor_estimado}}` | ✅ | — |
| `{{valor_total_sinapi}}` | — | ✅ |
| `{{valor_por_m2_sinapi}}` | — | ✅ |
| `{{mes_referencia_sinapi}}` | — | ✅ |
| `{{bdi}}` | — | ✅ |
| `{{data_hoje}}` | ✅ | ✅ |

---

### 3.1 O que existe hoje (5 abas)

| Aba | Conteúdo Atual |
|-----|---------------|
| **Perfil** | Nome, e-mail, telefone, CREA/CAU, foto de perfil |
| **Empresa** | Nome fantasia, CNPJ, endereço, logo |
| **Preferências** | Configurações gerais do usuário |
| **Vitrine** | Slug da URL pública, bio, fotos do portfólio, cidades de atuação |
| **Motor de Contratos** | Templates de contrato com variáveis dinâmicas |

### 3.1.1 Templates de Obra — Nova Aba em Configurações

O mesmo raciocínio do **Motor de Contratos** aplicado a orçamentos SINAPI. O engenheiro configura uma vez e o sistema usa em todos os projetos futuros.

**Conceito:** Uma aba "Templates de Obra" em Configurações onde o engenheiro define quais composições SINAPI compõem o esqueleto padrão dos seus projetos. Ao criar um novo projeto e fazer o Setup da Obra, aparece um seletor "Qual template usar como base?" — o sistema carrega automaticamente as composições com os preços do UF e mês configurados, sem o engenheiro precisar buscar item por item.

**Três opções de implementação (em ordem de complexidade):**

**Opção A — Kit global fixo (MVP, menor esforço)**
A plataforma mantém um template curado com as composições mais comuns da construção civil. O engenheiro não configura nada — ao criar o projeto as composições já aparecem. Pode remover ou adicionar depois.
- Vantagem: zero configuração, funciona desde o primeiro projeto
- Limitação: o kit será genérico demais para engenheiros especializados

**Opção B — Templates por padrão de obra (equilíbrio recomendado)**
Em Configurações, o engenheiro personaliza três listas: uma para Popular, uma para Médio Padrão, uma para Alto Padrão. O sistema usa a lista correspondente ao padrão do projeto.
- Vantagem: simples de entender, cobre a maioria dos casos práticos
- Limitação: engenheiros com mais de três perfis de obra precisam comprimir

**Opção C — Templates livres com nome (mais flexível, futuro)**
O engenheiro cria quantos templates quiser com nomes livres: "MCMV Lote Pequeno", "Sobrado Duplex", "Galpão Industrial". Mesmo modelo visual do Motor de Contratos — lista à esquerda, composições à direita. No Setup da Obra, seletor de qual template aplicar.
- Vantagem: máxima flexibilidade, engenheiro reconhece o padrão visual que já usa
- Complexidade: maior esforço de implementação

**Estratégia de evolução recomendada:**
```
MVP: Opção A (kit padrão da plataforma, fallback automático)
     ↓ engenheiro pede personalização
V2:  Opção B (personalização por padrão de obra nas Configurações)
     ↓ engenheiros avançados pedem mais
V3:  Opção C (templates livres com nome, igual ao Motor de Contratos)
```
A Opção A e B coexistem: se o engenheiro não configurou nenhum template, usa o kit da plataforma. Se configurou, usa o dele.

**Impacto esperado:**
Essa feature resolve o principal problema de usabilidade do orçamento hoje — o engenheiro precisar buscar composição por composição do zero a cada novo projeto. Com o template, 80% do orçamento aparece pronto; ele só ajusta quantidades e adiciona os itens específicos da obra.

---

### 3.2 O que avaliar adicionar

A ideia central é fazer o engenheiro **sentir que o sistema é dele** — personalização e identidade são fundamentais para isso.

**Personalização de marca:**
- Cor primária do portal do cliente (hoje é sempre a cor padrão do sistema)
- Logo própria exibida no portal — o cliente vê a marca do engenheiro, não a do sistema
- Mensagem de boas-vindas personalizada no portal ("Olá, sou o Eng. João. Seu projeto está em boas mãos.")
- Nome personalizado para o portal ("Portal da Construtora X" ao invés de "Portal do Cliente")

**Configurações de documentos solicitados:**
- O engenheiro deveria poder configurar quais documentos ele pede no upload (etapa 4 do lead)
- Hoje a lista é fixa no sistema — o ideal é o engenheiro configurar sua própria lista (RG, CPF, IR, FGTS, etc.)

**Notificações (quando existirem):**
- Configurar por qual canal quer ser avisado (e-mail, WhatsApp, push no sistema)
- Horário de silêncio

**Padrões do orçamento:**
- BDI padrão da empresa (hoje configurado projeto a projeto)
- Estado de atuação padrão (para não precisar selecionar toda vez)
- Desoneração padrão (definir o default uma vez, aplicar em todos os projetos novos)

---

## 4. Problemas Identificados

> **Como usar esta seção:** Aqui ficam os problemas com contexto completo (o porquê, o impacto, o comportamento esperado). Quando um problema vira tarefa executável, recebe a marcação `→ Tarefa criada: TODO.md Pxx.x` mas **não é removido daqui** — o contexto permanece para referência. Itens sem marcação ainda estão em análise ou aguardam decisão antes de virar tarefa.

### 4.1 Sistema sem saída ("rua sem saída")

**Problema:** O fluxo de orçamentação não tem um fim claro. O engenheiro monta a planilha SINAPI, mas depois disso não há uma ação de "concluir" ou "próximo passo" — o sistema simplesmente para. Cada etapa é uma ilha: o orçamento não leva ao contrato, o contrato não ativa o portal.

**O fluxo correto com os "fins" definidos:**

```
Setup da Obra
    ↓
Planilha SINAPI (adicionar itens, ajustar quantidades)
    ↓
[EXPORTAR] → PDF e/ou Excel com todos os itens,
              códigos SINAPI, unidades, quantidades,
              preços unitários, BDI e total geral
    ↓
Engenheiro submete arquivo à Caixa (fora do sistema)
    ↓
[MARCAR CAIXA APROVADA] → muda status do projeto
    ↓
Gerar Contrato de Construção (Motor de Contratos,
template tipo "Contrato", valores do SINAPI)
    ↓
Enviar para ZapSign → cliente assina
    ↓
[Webhook ZapSign confirma assinatura]
    ↓
Portal do Cliente desbloqueado automaticamente
```

**O que precisa ser construído:**
1. **Botão "Exportar Planilha"** na tela de orçamento — gera PDF e/ou Excel com todos os dados
2. **Botão "Marcar como Aprovado pela Caixa"** — avanço manual de status já que a Caixa é fora do sistema
3. **Portal bloqueado por padrão** — o botão de compartilhar portal só aparece após `status = contrato_assinado`
4. **Indicador visual de progresso** — barra de etapas no topo da tela de orçamento mostrando em qual fase o projeto está
---

### 4.2 Valor do SINAPI não bate com o simulador

**Problema:** Um projeto que saiu R$ 1.012.500 no simulador, ao abrir no SINAPI exibe R$ 54.194,40 — um valor completamente fora do esperado.

**Contexto:** O simulador usa preço base por padrão (Popular, Médio, Alto) multiplicado pela metragem. O SINAPI trabalha com itens unitários — cada item tem um código, uma unidade e um preço por unidade. Se a lista de itens está incompleta ou as quantidades são pequenas, o total será muito baixo.

**Perguntas a responder:**
- O SINAPI tem uma lista padrão de itens para uma obra de alto padrão? Ou o engenheiro monta do zero?
- Existe uma "memória de itens" — um template de orçamento que o engenheiro já montou e pode reusar?
- O sistema deveria mostrar ao engenheiro: "Seu orçamento está R$ 958.305 abaixo da estimativa do simulador. Verifique se todos os itens foram adicionados."

---

### 4.3 Setup da Obra não avança após salvar
> → Tarefa criada: **TODO.md P11.1**

**Problema:** Na tela de Setup da Obra, o engenheiro preenche UF, desoneração, mês de referência e BDI, clica em "Salvar Configurações" e nada acontece — o sistema não avança para a tela de Engenharia do projeto, mas se eu der um f5 ele atualiza a página e se eu clicar no SINAPI ele vai para a tela de engenharia.


**Contexto:** Antes de uma modificação recente, isso estava funcionando. Provavelmente o emit de evento `salvar` ou a navegação após o save foi quebrada.

**Comportamento esperado:** Após clicar em "Salvar Configurações" → fechar o modal → abrir automaticamente a tela `Orcamento.vue` do projeto.

---

### 4.4 Pre-seleções incorretas no Setup da Obra
> → Tarefa criada: **TODO.md P11.2** (UF) e **TODO.md P11.5** (mês de referência)

**Problemas encontrados:**

| Campo | Comportamento Atual | Comportamento Esperado |
|-------|--------------------|-----------------------|
| Estado (UF) | Vem pré-selecionado como SC | Vir vazio — engenheiro escolhe |
| Desonerado | Vem como "Não desonerado" | A definir (ver dúvida abaixo) |
| Mês de Referência | Não atualiza automaticamente | Sempre o mês mais recente disponível |
| BDI | Vem como null | Deixar para o engenheiro preencher OU usar o padrão das Configurações |

**Dúvida em aberto — Desoneração:**
Não sabemos qual é o percentual de obras que usa desonerado vs. não desonerado. Se ~90% das obras são não desoneradas, faz sentido deixar pré-selecionado como padrão e o engenheiro altera quando necessário. Se a divisão for equilibrada, melhor deixar vazio e forçar a escolha consciente. **Decisão pendente.**

---

### 4.5 Botões de voltar ausentes
> → Tarefa criada: **TODO.md P11.3**

**Problema:** Diversas telas não têm botão de voltar ou o caminho de retorno não é óbvio. Usuário fica preso ou usa o botão do navegador.

**Telas que precisam de botão de voltar:**
- `Orcamento.vue` → voltar para `EngenhariaList`
- `EstimativaWizard` (cada passo) → voltar para o passo anterior
- `PortalCliente` → não se aplica (é uma tela standalone para o cliente)
- `Configuracoes` → voltar para o Dashboard

---

### 4.6 Link errado no ShareLinkModal para leads novos

**Problema:** O `ShareLinkModal` gera links para `/portal/:token` (Portal de Acompanhamento de Obra). Para um lead novo — que ainda não passou pelo wizard e não tem contrato — o link correto seria `/estimativa/:id` (o wizard de qualificação).

**Dois tipos de link precisam existir:**
1. **Link de Qualificação** — para leads. Leva para o wizard (padrão → tamanho → simulador → docs). Gerado logo após o cadastro do cliente.
2. **Link do Portal** — para clientes com obra em andamento. Leva para o portal com PIN. Gerado **apenas após** `status = contrato_assinado`.

---

### 4.7 Portal do Cliente acessível antes da hora
> → Tarefa criada: **TODO.md P11.4**

**Problema:** Hoje o engenheiro consegue gerar e enviar o link do Portal de Acompanhamento (`/portal/:token`) a qualquer momento, inclusive antes de a planilha SINAPI estar pronta e antes do contrato ser assinado. Isso é um problema sério: o cliente entra no portal e não encontra nada — ou pior, encontra dados incompletos de uma obra que ainda nem foi aprovada pela Caixa.

**Regra que precisa ser aplicada:**

| Status do projeto | Portal do Cliente |
|-------------------|-------------------|
| `lead_novo` até `sinapi_montado` | ❌ Bloqueado — botão de compartilhar portal não aparece |
| `caixa_aprovada` ou `contrato_assinado` | ✅ Liberado — botão aparece no card do projeto |
| `obra_ativa` | ✅ Liberado e ativo |

**O que muda na UI:**
- No `ProjectCard.vue`: o botão "Enviar Acesso à Obra" / `ShareLinkModal` só renderiza quando `project.coluna === 'obra_liberada'` ou `project.status === 'contrato_assinado'`
- Antes disso, no lugar do botão pode aparecer uma indicação do próximo passo: "Aguardando assinatura do contrato"
- O desbloqueio automático pode acontecer via webhook do ZapSign que já existe no sistema

---

## 5. Sacadas / Ideias para o Futuro

> Itens que não devem ser feitos agora, mas que valem registrar. Quando uma ideia for aprovada e priorizada, vira tarefa no TODO.md e recebe a marcação `→ Tarefa criada: TODO.md Pxx.x`.

### 5.1 Notificação ao engenheiro
Quando o cliente enviar os documentos, o engenheiro deveria ser notificado sem precisar abrir o sistema. Supabase tem Realtime nativo — bastaria um listener na tabela `projetos_clientes` filtrando `status = 'docs_completos'`. Canais possíveis:
- Badge no Sidebar com contador de leads prontos
- Toast automático se o engenheiro estiver logado
- Notificação push no celular (futuramente)
- Mensagem de WhatsApp automática ("Novo cliente enviou documentos: João Silva")

### 5.2 Fluxo guiado de conversão de lead → obra
Hoje não existe um botão claro de "Converter em Projeto". O engenheiro precisa fazer isso manualmente. O ideal seria uma ação visível no card do lead que dispara uma sequência:
1. Marca como lead qualificado
2. Abre o orçamento
3. Gera o contrato
4. Ativa o portal

### 5.3 Estimativa usando CUB por estado
Hoje o Passo 3 do wizard usa preço base fixo (R$1.800 / R$2.800 / R$4.500 por m²). O sistema já tem `/api/simulador/calcular` que usa a tabela CUB por UF. Usar o CUB do estado do cliente no wizard tornaria o valor estimado mais preciso e profissional.

### 5.4 Sala de Espera mais rica para o cliente
Após enviar os documentos, o cliente cai em uma tela simples. Poderia mostrar:
- Lista dos documentos enviados com data/hora
- Status de "em análise"
- Expectativa de retorno ("Você receberá uma resposta em até 48h úteis")
- Contato direto com o engenheiro (WhatsApp, telefone)

### 5.5 Aba "Solicitar" no Portal de Acompanhamento
Hoje o cliente só lê o portal. Uma aba simples onde o cliente pode enviar uma mensagem ao engenheiro (visita, dúvida, problema no canteiro) manteria a comunicação dentro do sistema ao invés de se perder no WhatsApp.

### 5.6 Templates de orçamento reutilizáveis
O engenheiro que monta um orçamento de casa popular de 60m² vai montar o mesmo tipo de obra 10 vezes. A capacidade de salvar um orçamento como template e aplicar em projetos futuros economizaria muito tempo. O sistema já tem estrutura básica para isso (`/api/projetos/{id}/transformar-template`), mas ainda não está exposto de forma clara na UI.

### 5.9 EAP Padrão — O que já existe e o que falta

O sistema já tem a estrutura técnica para isso. O que falta é o conteúdo e o fluxo de aplicação.

**O que já existe:**
- Tabelas `sinapi_composicoes` e `sinapi_composicao_itens` com relação pai-filho e coeficientes
- `ArvoreCustos.vue` com accordion por fase e edição inline só na quantidade do pai (read-only nos filhos)
- Fases da obra definidas em `ETAPAS_OBRA`
- Busca em batch de preços por UF/mês/desonerado

**O que falta:**
1. **Conteúdo do template** — definir quais 40-60 composições SINAPI compõem um projeto residencial típico por padrão (popular/médio/alto). Isso é decisão de produto/conteúdo, não de código.
2. **Fluxo de pré-carga** — ao concluir o Setup da Obra, o sistema insere automaticamente as composições do template no projeto com as quantidades sugeridas.
3. **Trava de edição na API** — confirmar que o endpoint `PATCH /api/projetos/{id}/itens/{item_id}` rejeita alterações de coeficientes internos (hoje só o frontend respeita essa regra).
4. **Quantidades sugeridas por metragem** — composições como alvenaria são proporcionais à área. O template deveria sugerir uma quantidade inicial baseada na metragem informada no wizard (ex: 370m² → alvenaria ≈ 185m²).

### 5.8 Passo 2 do Wizard — Cômodos com múltiplas instâncias

Hoje o Passo 2 tem um campo de área para cada tipo de cômodo (sala, cozinha, quartos, banheiros). O problema é que uma casa com 3 quartos de tamanhos diferentes — ou 2 banheiros com áreas distintas — não consegue ser representada com um único número.

**O que melhorar:**

Alguns cômodos de uma casa têm sempre uma única instância (sala de estar, cozinha, área de serviço). Outros podem ter várias (quartos, banheiros, suítes, vagas de garagem, escritórios). Para os que podem ter múltiplos, o cliente deve poder:

- **Opção 1 — Área Total:** Digitar diretamente a soma. Exemplo: "3 quartos = 36m²". Rápido, para quem já sabe o total.
- **Opção 2 — Por Unidade:** Escolher a quantidade (ex: 3 quartos) e o sistema expande campos individuais. Exemplo: Quarto 1: 12m², Quarto 2: 10m², Quarto 3: 14m².

A UI deve oferecer as duas formas sem forçar uma só.

**Cômodos que se beneficiam disso:**

| Cômodo | Múltiplos? | Como apresentar |
|--------|-----------|----------------|
| Sala de estar | Não | Campo único de área |
| Cozinha | Não | Campo único de área |
| Área de serviço | Não | Campo único de área |
| Quartos | Sim | Qtd. + área individual ou total |
| Suítes | Sim | Qtd. + área individual ou total |
| Banheiros | Sim | Qtd. + área individual ou total |
| Vagas de garagem | Sim | Qtd. + área individual ou total |
| Escritório / Home office | Sim | Qtd. + área individual ou total |

**Impacto na estimativa:**
A metragem total continua sendo a soma de tudo — o que muda é a granularidade com que o cliente informa. Uma estimativa baseada em "3 quartos de 12m² cada" é mais confiável do que "quartos: 36m²" que pode estar errado. Além disso, esses dados ficam salvos no projeto e o engenheiro pode usar para dimensionar o projeto técnico mais rápido.

**Dado adicional interessante:**
A combinação de quantidades (ex: "3 quartos, 2 banheiros") é um excelente qualificador de lead — uma casa com 4 quartos + 3 suítes já sinaliza alto padrão antes mesmo de o cliente responder o Passo 1.

### 5.7 Histórico de status do lead
Uma linha do tempo simples no card de cada projeto: "Lead cadastrado → Link enviado → Wizard concluído → Documentos enviados → Contrato assinado → Obra ativa". Daria visibilidade total sem precisar abrir o projeto.

### 5.10 Tela de Sugestões — Fórum de Ideias dos Engenheiros

Uma seção dentro do sistema onde os próprios engenheiros submetem e votam em melhorias. Funciona como um canal de feedback estruturado e um roadmap público parcial.

**Entrada:** Botão "Sugestões" no Sidebar (provavelmente embaixo, área secundária). Ícone de lâmpada ou balão de fala.

**Como funciona:**

```
[Engenheiro envia sugestão]
    ↓
Admin do sistema recebe notificação
    ↓
Admin aprova → sugestão entra no mural público
Admin rejeita → sugestão não aparece (evita spam/duplicatas)
    ↓
Todos os engenheiros logados podem votar na sugestão
    ↓
Sugestões com mais votos sobem no ranking
    ↓
[Admin atualiza o status da sugestão conforme evolui]
```

**Layout da tela:**
- Área superior: campo de texto + botão "Enviar Sugestão"
- Área principal: lista de sugestões aprovadas ordenadas por votos
- Cada card de sugestão mostra: texto, autor (ou anônimo), data, contagem de votos e status atual

**Sistema de votos — recomendação:**
Usar apenas **upvote** (sem downvote). O downvote público pode desestimular participação — um engenheiro que vê a própria ideia sendo derrubada provavelmente não volta a participar. O que se perde em sinal é pouco; o que se ganha em ambiente mais saudável e participação contínua é muito.

Se quiser capturar o sinal negativo sem expor publicamente: um botão discreto "Não preciso disso" que registra o dado internamente mas não aparece no card.

**Status das sugestões — o diferencial:**

| Status | Descrição |
|--------|-----------|
| `Aguardando votos` | Aprovada pelo admin, em votação pública |
| `Em análise` | Equipe está avaliando viabilidade |
| `Planejado` | Confirmado que vai ser feito |
| `Em desenvolvimento` | Está sendo construído agora |
| `Implementado` | Feature entregue — sugestão encerrada com link para o changelog |
| `Não planejado` | Não será feito (com motivo opcional) |

Quando uma sugestão de um engenheiro muda para `Implementado`, ele recebe uma notificação: *"Sua ideia foi implementada! Acesse [funcionalidade]."* Isso fecha o ciclo e é o que transforma um fórum em comunidade ativa — as pessoas voltam porque veem que o sistema ouve.

**Regras básicas:**
- Engenheiro não pode votar na própria sugestão
- Um voto por usuário por sugestão
- Engenheiro pode editar/deletar a própria sugestão enquanto ela não for aprovada
- Sugestões aprovadas não podem ser editadas (voto já aconteceu sobre aquele texto)

**Por que isso é um diferencial:**
Poucos SaaS de construção civil no Brasil têm isso. Cria senso de comunidade, reduz churn (o usuário sente que o produto evolui com ele), e entrega um roadmap naturalmente priorizado sem precisar de pesquisas caras. O custo de implementação é baixo; o impacto em retenção e percepção de valor é alto.

**Banco de dados necessário (simples):**
- `sugestoes` — id, usuario_id, texto, status, criado_em
- `sugestoes_votos` — sugestao_id, usuario_id, criado_em (único por par)

---

## 6. Perguntas em Aberto

Decisões que precisam ser tomadas antes de implementar.

| # | Pergunta | Impacta |
|---|----------|---------|
| 1 | Qual o percentual de obras desoneradas vs. não desoneradas? | Pre-seleção do Setup da Obra |
| 2 | O SINAPI deve ter uma lista padrão de itens por tipo de obra (popular, médio, alto)? | Experiência de orçamentação |
| 3 | O engenheiro deve poder personalizar quais documentos pede ao cliente? | Etapa de upload + Configurações |
| 4 | O "Link de Qualificação" e o "Link do Portal" devem ser dois botões separados no card, ou um fluxo único que muda conforme o status do projeto? | UX da EngenhariaList e ShareLinkModal |
| 5 | O portal do cliente deve ter a marca do engenheiro (logo + cor personalizada)? | Configurações + PortalCliente |
| 6 | Qual o critério para um projeto "virar obra" — assinatura do contrato, confirmação manual, ou outra ação? | Fluxo de conversão lead → obra |

---

## 7. Contratos — Quando Gerar e Qual Documento

Esta é uma das decisões mais importantes do fluxo e precisa estar clara antes de qualquer implementação.

### 7.1 O problema

Existem **dois documentos distintos** que o sistema (e o usuário) tendem a chamar de "contrato", e eles têm momentos, valores e finalidades completamente diferentes. Misturá-los causa problemas legais e operacionais.

---

### 7.2 Documento 1 — Proposta Comercial (pré-SINAPI)

| | |
|--|--|
| **Quando é gerado** | Após o engenheiro aceitar o lead qualificado (documentos recebidos e analisados) |
| **Valores usados** | Estimativa pelo CUB do estado × metragem × padrão — ainda não é o valor definitivo |
| **Finalidade** | Formalizar o compromisso entre as partes. Cliente confirma que escolheu aquele engenheiro. Engenheiro confirma que vai montar o orçamento. Nenhum dos dois perde tempo sem garantia. |
| **Submetido à Caixa?** | Não. É um documento interno entre cliente e engenheiro. |
| **Assinatura digital** | Pode passar pelo ZapSign nesta fase se o engenheiro quiser |
| **Variáveis dinâmicas** | `{{cliente_nome}}`, `{{valor_estimado}}`, `{{padrao}}`, `{{metragem}}`, `{{uf_obra}}`, `{{engenheiro_nome}}` |

---

### 7.3 Documento 2 — Contrato de Construção (pós-SINAPI)

| | |
|--|--|
| **Quando é gerado** | Após o engenheiro montar a planilha SINAPI completa com todos os itens e quantidades |
| **Valores usados** | Valor real da planilha SINAPI — preciso ao centavo |
| **Finalidade** | Contrato definitivo e legal da obra. Este é o documento que a **Caixa Econômica exige** para aprovar o financiamento. Sem ele com os valores do SINAPI, o banco não libera. |
| **Submetido à Caixa?** | **Sim.** Junto com o projeto técnico e a planilha orçamentária. |
| **Assinatura digital** | ZapSign nesta fase é obrigatório (ambas as partes) |
| **Variáveis dinâmicas** | `{{cliente_nome}}`, `{{valor_total_sinapi}}`, `{{valor_por_m2}}`, `{{metragem}}`, `{{uf_obra}}`, `{{mes_referencia_sinapi}}`, `{{bdi}}`, `{{engenheiro_nome}}`, `{{crea_cau}}` |

---

### 7.4 Fluxo correto dos dois documentos

```
Lead cadastrado
    ↓
Wizard: estado + padrão + metragem → CUB do estado → estimativa
    ↓
Cliente simula na Caixa → aprova → envia documentos
    ↓
Engenheiro analisa docs e aceita o lead
    ↓
┌─────────────────────────────────────────────────────────────┐
│  PROPOSTA COMERCIAL (valores estimados via CUB)             │
│  Gerada pelo Motor de Contratos com template de proposta    │
│  Assinada pelas duas partes → compromisso formal            │
└─────────────────────────────────────────────────────────────┘
    ↓
Engenheiro monta planilha SINAPI detalhada
(itens, quantidades, unidades, preços por código SINAPI)
    ↓
┌─────────────────────────────────────────────────────────────┐
│  CONTRATO DE CONSTRUÇÃO (valores reais do SINAPI)           │
│  Gerado pelo Motor de Contratos com template de contrato    │
│  Assinado pelas duas partes via ZapSign                     │
│  Submetido à Caixa junto com o projeto técnico              │
└─────────────────────────────────────────────────────────────┘
    ↓
Caixa aprova a obra
    ↓
Portal de Acompanhamento é ativado para o cliente
```

---

### 7.5 Implicações para o sistema

1. **O Motor de Contratos precisa de dois tipos de template distintos:** um de "Proposta Comercial" e um de "Contrato de Construção". Hoje tem templates genéricos — precisaria de uma categorização ou indicador de qual tipo é.

2. **O template de Contrato de Construção precisa de novas variáveis** que só existem depois do SINAPI: `{{valor_total_sinapi}}`, `{{mes_referencia_sinapi}}`, `{{bdi}}`. Hoje essas variáveis não estão disponíveis no motor.

3. **A ação "Gerar Contrato" na tela de Orçamento** só deveria estar disponível depois que o SINAPI estiver montado (alguma validação de que a planilha tem itens e um total > 0).

4. **A ação "Enviar Proposta"** deveria estar disponível mais cedo, logo após o engenheiro aceitar o lead — sem precisar ter o SINAPI pronto.

5. **O estado do projeto precisa refletir isso:** `proposta_enviada` e `contrato_assinado` são dois estados diferentes e bem separados no tempo.

---

### 7.6 Sobre o estado no wizard (CUB correto)

O estado do cliente é **obrigatório** para a estimativa ser útil. O CUB varia significativamente entre estados — uma obra no RS sai diferente de SP ou PA. Mostrar um valor de CUB de SC para um cliente do Pará cria expectativas erradas logo na primeira interação.

**O que precisa mudar no wizard:**
- Adicionar seleção de estado antes (ou no Passo 2, junto com metragem)
- O Passo 3 usa `/api/simulador/calcular` passando o `uf` correto, ao invés do preço base fixo atual
- O estado selecionado pelo cliente fica salvo no projeto para o engenheiro visualizar

---

## 8. Mapa de Status dos Projetos

Fluxo completo de status que um projeto percorre no sistema:

```
lead_novo
  ↓ cliente acessa wizard e preenche os dados
lead_em_qualificacao
  ↓ cliente aprova simulador da Caixa
lead_aprovado
  ↓ cliente envia documentos pessoais
docs_completos
  ↓ engenheiro analisa e aceita o lead
em_negociacao
  ↓ proposta comercial (CUB) enviada e assinada
proposta_assinada
  ↓ engenheiro monta planilha SINAPI
sinapi_montado
  ↓ contrato de construção (SINAPI) enviado e assinado
contrato_assinado
  ↓ Caixa aprova o financiamento
caixa_aprovada
  ↓ obra iniciada → portal de acompanhamento ativo
obra_ativa
  ↓ obra concluída
obra_concluida
  ↓ (opcional)
arquivado
```

Hoje o sistema não deixa explícito todos esses estados na UI — alguns existem no banco mas não têm representação visual clara no dashboard.

---

*Última atualização: 21/05/2026*
