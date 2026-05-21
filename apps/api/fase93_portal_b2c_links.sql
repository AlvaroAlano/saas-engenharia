-- =========================================================================
-- FASE 9.3: PORTAL DO CLIENTE B2C (ZERO-LOGIN) — MAGIC LINKS
-- =========================================================================
-- Objetivo: Permitir que o Engenheiro (B2B) gere um link público e
-- temporário para que o Cliente Final (B2C) visualize um orçamento
-- específico e faça upload de arquivos — sem precisar de senha.
--
-- Arquitetura de Segurança:
--   • O Engenheiro autenticado (JWT) gerencia os links via CRUD.
--   • O Cliente anônimo (role: anon) só consegue ler o registro do
--     link se ele estiver ativo — obtendo apenas o token_acesso e o
--     orcamento_id associado.
--   • Os dados reais do orçamento continuam protegidos pelo RLS da
--     tabela "orcamentos". O backend usará uma Service Key pontual
--     para buscar os dados quando um token_acesso válido for apresentado.
-- =========================================================================


-- =========================================================================
-- 1. TABELA: orcamento_links (Magic Links)
-- =========================================================================

CREATE TABLE IF NOT EXISTS public.orcamento_links (
    -- Chave primária
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- FK para o orçamento protegido (cascade ao deletar orçamento)
    orcamento_id UUID NOT NULL REFERENCES public.orcamentos(id) ON DELETE CASCADE,

    -- Token público do Magic Link — será a hash na URL compartilhada
    -- UNIQUE garante que cada token é irrepetível no sistema inteiro
    token_acesso UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    -- Flag de ativação — permite revogar o link sem deletá-lo
    ativo BOOLEAN NOT NULL DEFAULT true,

    -- Metadados de auditoria
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),

    -- Expiração opcional — NULL significa "sem expiração"
    -- O backend pode checar: WHERE expires_at IS NULL OR expires_at > now()
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
);

-- Índice para busca rápida por token (o cliente B2C sempre consulta por aqui)
CREATE INDEX IF NOT EXISTS idx_orcamento_links_token
    ON public.orcamento_links(token_acesso)
    WHERE ativo = true;

-- Índice para o engenheiro listar os links dos seus orçamentos
CREATE INDEX IF NOT EXISTS idx_orcamento_links_orcamento
    ON public.orcamento_links(orcamento_id);


-- =========================================================================
-- 2. ROW LEVEL SECURITY (RLS)
-- =========================================================================

ALTER TABLE public.orcamento_links ENABLE ROW LEVEL SECURITY;


-- -------------------------------------------------------------------------
-- 2.1 POLÍTICAS DO ENGENHEIRO (Autenticado — role: authenticated)
-- -------------------------------------------------------------------------
-- O engenheiro só pode operar nos links cujo orcamento_id pertence a ele.
-- A verificação é feita via subquery na tabela "orcamentos".
-- -------------------------------------------------------------------------

-- SELECT: Engenheiro vê apenas links dos seus próprios orçamentos
CREATE POLICY "Engenheiro visualiza links dos próprios orçamentos"
ON public.orcamento_links
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.orcamentos
        WHERE orcamentos.id = orcamento_links.orcamento_id
          AND orcamentos.usuario_id = auth.uid()
    )
);

-- INSERT: Engenheiro cria links apenas para seus próprios orçamentos
CREATE POLICY "Engenheiro cria links para próprios orçamentos"
ON public.orcamento_links
FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.orcamentos
        WHERE orcamentos.id = orcamento_links.orcamento_id
          AND orcamentos.usuario_id = auth.uid()
    )
);

-- UPDATE: Engenheiro edita (ativar/desativar) links dos seus orçamentos
CREATE POLICY "Engenheiro atualiza links dos próprios orçamentos"
ON public.orcamento_links
FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.orcamentos
        WHERE orcamentos.id = orcamento_links.orcamento_id
          AND orcamentos.usuario_id = auth.uid()
    )
);

-- DELETE: Engenheiro remove links dos seus próprios orçamentos
CREATE POLICY "Engenheiro deleta links dos próprios orçamentos"
ON public.orcamento_links
FOR DELETE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.orcamentos
        WHERE orcamentos.id = orcamento_links.orcamento_id
          AND orcamentos.usuario_id = auth.uid()
    )
);


-- -------------------------------------------------------------------------
-- 2.2 POLÍTICA DO CLIENTE B2C (Anônimo — role: anon)
-- -------------------------------------------------------------------------
-- O cliente sem login acessa a URL pública com o token_acesso.
-- Esta política permite que o papel "anon" leia APENAS registros
-- que estejam ativos e não expirados.
--
-- IMPORTANTE: Isso dá acesso somente ao REGISTRO DO LINK (token, 
-- orcamento_id, ativo). Os dados reais do orçamento continuam 
-- blindados pelo RLS da tabela "orcamentos" (que exige auth.uid()).
-- O backend resolverá isso com a Service Key na rota B2C.
-- -------------------------------------------------------------------------

CREATE POLICY "Cliente B2C acessa links ativos via token"
ON public.orcamento_links
FOR SELECT
TO anon
USING (
    ativo = true
    AND (expires_at IS NULL OR expires_at > now())
);


-- =========================================================================
-- 3. ATUALIZAÇÃO: COLUNA PIN DE ACESSO (Fase 9.3 - Passo 2)
-- =========================================================================
-- O PIN é uma camada extra de segurança (4 últimos dígitos do telefone
-- do cliente). Impede acesso indevido caso o link seja compartilhado
-- acidentalmente, sem exigir CPF ou documentos formais.
-- =========================================================================

-- Se a tabela já foi criada sem o campo, use este ALTER TABLE:
ALTER TABLE public.orcamento_links
    ADD COLUMN IF NOT EXISTS pin_acesso VARCHAR(4) NOT NULL DEFAULT '0000'
    CONSTRAINT pin_acesso_4_digitos CHECK (pin_acesso ~ '^\d{4}$');

-- Remover o default após migração (forçar envio explícito nas novas inserções)
-- ALTER TABLE public.orcamento_links ALTER COLUMN pin_acesso DROP DEFAULT;


-- =========================================================================
-- 4. COMENTÁRIOS DE DOCUMENTAÇÃO
-- =========================================================================

COMMENT ON TABLE public.orcamento_links IS
    'Magic Links para o Portal B2C. Permite que clientes anônimos acessem orçamentos via token único + PIN de 4 dígitos.';

COMMENT ON COLUMN public.orcamento_links.token_acesso IS
    'UUID único usado na URL pública: /portal/{token_acesso}. Gerado automaticamente.';

COMMENT ON COLUMN public.orcamento_links.ativo IS
    'Flag de revogação. O engenheiro pode desativar o link sem deletá-lo, mantendo o histórico.';

COMMENT ON COLUMN public.orcamento_links.expires_at IS
    'Expiração opcional do link. NULL = sem expiração. O RLS e o backend devem checar este campo.';

COMMENT ON COLUMN public.orcamento_links.pin_acesso IS
    'PIN de 4 dígitos numéricos (últimos 4 dígitos do telefone/WhatsApp do cliente). Camada de segurança contra vazamento de link.';
