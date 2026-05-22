-- Migration: 004_perfil_completo_e_vitrine.sql
-- Descrição: Adiciona colunas faltantes em perfis_b2b, cria tabela dados_empresa
--            e consolida as colunas de vitrine (sobrepõe a 003 com IF NOT EXISTS).

-- =========================================================================
-- 1. Completar perfis_b2b com colunas usadas pelas telas de Configurações
-- =========================================================================
ALTER TABLE public.perfis_b2b
  ADD COLUMN IF NOT EXISTS telefone          TEXT,
  ADD COLUMN IF NOT EXISTS foto_perfil       TEXT,
  ADD COLUMN IF NOT EXISTS updated_at        TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
  -- Colunas de Vitrine Pública (idempotente em relação à migration 003)
  ADD COLUMN IF NOT EXISTS slug_vitrine      TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS descricao_vitrine TEXT,
  ADD COLUMN IF NOT EXISTS fotos_portfolio   TEXT[] DEFAULT '{}'::text[],
  ADD COLUMN IF NOT EXISTS cidades_atuacao   TEXT[] DEFAULT '{}'::text[];

-- Índice para lookup por slug (apenas perfis com slug configurado)
CREATE INDEX IF NOT EXISTS idx_perfis_b2b_slug
  ON public.perfis_b2b(slug_vitrine)
  WHERE slug_vitrine IS NOT NULL;

-- =========================================================================
-- 2. Política pública de leitura da vitrine (idempotente)
-- =========================================================================
DROP POLICY IF EXISTS "Leitura pública de vitrine por slug" ON public.perfis_b2b;
CREATE POLICY "Leitura pública de vitrine por slug"
ON public.perfis_b2b FOR SELECT
TO public
USING (slug_vitrine IS NOT NULL);

-- =========================================================================
-- 3. Tabela dados_empresa (usada pela aba Empresa em Configurações)
-- =========================================================================
CREATE TABLE IF NOT EXISTS public.dados_empresa (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  nome_fantasia   TEXT,
  cnpj            TEXT,
  endereco_completo TEXT,
  logo_url        TEXT,
  updated_at      TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

ALTER TABLE public.dados_empresa ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Empresa: owner lê" ON public.dados_empresa;
CREATE POLICY "Empresa: owner lê"
ON public.dados_empresa FOR SELECT
USING (auth.uid() = usuario_id);

DROP POLICY IF EXISTS "Empresa: owner insere" ON public.dados_empresa;
CREATE POLICY "Empresa: owner insere"
ON public.dados_empresa FOR INSERT
WITH CHECK (auth.uid() = usuario_id);

DROP POLICY IF EXISTS "Empresa: owner atualiza" ON public.dados_empresa;
CREATE POLICY "Empresa: owner atualiza"
ON public.dados_empresa FOR UPDATE
USING (auth.uid() = usuario_id);

-- =========================================================================
-- 4. Bucket de Storage para fotos de perfil, logos e portfólio
--    (executar manualmente no painel caso o bucket não exista)
-- =========================================================================
-- No painel do Supabase > Storage > New Bucket:
--   Nome: identidade
--   Público: SIM (para URLs públicas funcionarem)
--
-- Policies recomendadas para o bucket identidade:
--   SELECT (public): bucket_id = 'identidade'        → qualquer um lê
--   INSERT (authenticated): bucket_id = 'identidade' → apenas logados enviam
