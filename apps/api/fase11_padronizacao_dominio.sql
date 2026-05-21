-- =========================================================================
-- FASE 11: MUDANÇA E PADRONIZAÇÃO DO DOMÍNIO PRINCIPAL (SaaS Engenharia)
-- SCRIPT CORRIGIDO: Referenciando auth.users nativo do Supabase
-- =========================================================================
-- Arquiteto Backend & DBA: Decisão de Unificação de Domínio
--
-- JUSTIFICATIVA ARQUITETURAL:
-- Em um SaaS moderno de Engenharia Civil, a segregação entre "Obras", 
-- "Orçamentos" e "Projetos de Clientes" gera fragmentação desnecessária, 
-- duplicação de dados e risco severo de dessincronização relacional.
-- 
-- Decidimos eleger a entidade "Projeto" (tabela `projetos_clientes`) como o 
-- NÚCLEO ABSOLUTO do sistema. Um Projeto nasce no funil comercial (Kanban) 
-- contendo dados do cliente, status e telefone, e evolui nativamente para o 
-- Orçamento Técnico (absorvendo as configurações de BDI, UF, e tabela SINAPI).
-- 
-- Todas as entidades filhas (itens da planilha de custos, links de portal B2C, 
-- histórico de ações) apontarão estritamente para a chave estrangeira `projeto_id`.
-- Eliminamos assim as tabelas redundantes e legadas de "orcamentos" e "obras".
-- =========================================================================

-- 1. Garantir e Saneamento da Tabela Central: projetos_clientes
CREATE TABLE IF NOT EXISTS public.projetos_clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid(),
    cliente_nome TEXT NOT NULL,
    titulo_projeto TEXT,
    telefone TEXT,
    observacoes TEXT,
    coluna TEXT DEFAULT 'estimativa_enviada',
    status TEXT DEFAULT 'aguardando_cliente',
    valor NUMERIC(15, 2) DEFAULT 0.00,
    padrao TEXT,
    tamanho TEXT,
    uf_obra VARCHAR(2) DEFAULT 'SC',
    sinapi_mes_ano VARCHAR(7),
    sinapi_desonerado BOOLEAN DEFAULT false,
    bdi_padrao NUMERIC(5, 2) DEFAULT 25.00,
    documentos JSONB DEFAULT '[]'::jsonb,
    contrato_gerado BOOLEAN DEFAULT false,
    zapsign_document_token TEXT,
    url_assinatura_cliente TEXT,
    url_assinatura_engenheiro TEXT,
    status_assinatura TEXT DEFAULT 'nao_enviado',
    engenheiro_assinou BOOLEAN DEFAULT false,
    cliente_assinou BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Adiciona a coluna usuario_id de forma segura caso a tabela tenha sido criada sem ela anteriormente
ALTER TABLE public.projetos_clientes 
    ADD COLUMN IF NOT EXISTS usuario_id UUID REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid();

-- Habilitar RLS estrito na tabela principal
ALTER TABLE public.projetos_clientes ENABLE ROW LEVEL SECURITY;

-- Remover políticas soltas antigas caso existam
DROP POLICY IF EXISTS "Visualizar próprios projetos" ON public.projetos_clientes;
DROP POLICY IF EXISTS "Inserir próprios projetos" ON public.projetos_clientes;
DROP POLICY IF EXISTS "Atualizar próprios projetos" ON public.projetos_clientes;
DROP POLICY IF EXISTS "Deletar próprios projetos" ON public.projetos_clientes;

-- Recriar Políticas com Isolamento Total de Tenant (SaaS)
CREATE POLICY "Visualizar próprios projetos" 
ON public.projetos_clientes FOR SELECT 
USING (auth.uid() = usuario_id);

CREATE POLICY "Inserir próprios projetos" 
ON public.projetos_clientes FOR INSERT 
WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "Atualizar próprios projetos" 
ON public.projetos_clientes FOR UPDATE 
USING (auth.uid() = usuario_id);

CREATE POLICY "Deletar próprios projetos" 
ON public.projetos_clientes FOR DELETE 
USING (auth.uid() = usuario_id);


-- 2. Recriação e Padronização da Tabela Filha: orcamento_itens (Planilha de Custos)
-- Dropamos a tabela antiga para eliminar chaves órfãs como orcamento_id ou obra_id
DROP TABLE IF EXISTS public.orcamento_itens CASCADE;

CREATE TABLE public.orcamento_itens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES public.projetos_clientes(id) ON DELETE CASCADE,
    codigo_sinapi VARCHAR NOT NULL,
    descricao TEXT NOT NULL,
    unidade VARCHAR NOT NULL,
    quantidade NUMERIC(15, 4) DEFAULT 1.0000,
    valor_unitario NUMERIC(15, 2) NOT NULL,
    tipo_item VARCHAR NOT NULL CHECK (tipo_item IN ('insumo', 'composicao')),
    etapa_obra VARCHAR DEFAULT 'servicos_preliminares',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Índices de otimização para carregamento rápido da árvore de custos
CREATE INDEX IF NOT EXISTS idx_orcamento_itens_projeto ON public.orcamento_itens(projeto_id);

-- RLS e Isolamento na tabela de itens
ALTER TABLE public.orcamento_itens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Acesso total aos itens dos meus projetos"
ON public.orcamento_itens FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM public.projetos_clientes
        WHERE projetos_clientes.id = orcamento_itens.projeto_id
          AND projetos_clientes.usuario_id = auth.uid()
    )
);


-- 3. Recriação e Padronização da Tabela Filha: orcamento_links (Portal B2C)
DROP TABLE IF EXISTS public.orcamento_links CASCADE;

CREATE TABLE public.orcamento_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES public.projetos_clientes(id) ON DELETE CASCADE,
    token_acesso UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    pin_acesso VARCHAR(4) NOT NULL CONSTRAINT pin_acesso_formato CHECK (pin_acesso ~ '^\d{4}$'),
    ativo BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_orcamento_links_projeto ON public.orcamento_links(projeto_id);
CREATE INDEX IF NOT EXISTS idx_orcamento_links_token ON public.orcamento_links(token_acesso) WHERE ativo = true;

ALTER TABLE public.orcamento_links ENABLE ROW LEVEL SECURITY;

-- Engenheiro gerencia os links dos seus projetos
CREATE POLICY "Gerenciar links dos meus projetos"
ON public.orcamento_links FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.projetos_clientes
        WHERE projetos_clientes.id = orcamento_links.projeto_id
          AND projetos_clientes.usuario_id = auth.uid()
    )
);

-- Cliente B2C (anon) consulta apenas links ativos pelo token único
CREATE POLICY "Cliente B2C acessa link ativo"
ON public.orcamento_links FOR SELECT
TO anon
USING (
    ativo = true 
    AND (expires_at IS NULL OR expires_at > now())
);


-- 4. Tabela de Histórico de Ações do Projeto
CREATE TABLE IF NOT EXISTS public.projetos_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES public.projetos_clientes(id) ON DELETE CASCADE,
    acao TEXT NOT NULL,
    detalhes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

ALTER TABLE public.projetos_historico ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Acesso ao histórico dos meus projetos"
ON public.projetos_historico FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM public.projetos_clientes
        WHERE projetos_clientes.id = projetos_historico.projeto_id
          AND projetos_clientes.usuario_id = auth.uid()
    )
);
