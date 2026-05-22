-- Migration: 003_vitrine_perfil_publico.sql
-- Descrição: Adiciona colunas de vitrine pública à tabela perfis_b2b e cria política de leitura pública por slug.

-- 1. Adiciona colunas de portfólio à tabela existente
ALTER TABLE public.perfis_b2b
  ADD COLUMN IF NOT EXISTS slug_vitrine TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS descricao_vitrine TEXT,
  ADD COLUMN IF NOT EXISTS fotos_portfolio TEXT[] DEFAULT '{}'::text[],
  ADD COLUMN IF NOT EXISTS cidades_atuacao TEXT[] DEFAULT '{}'::text[];

-- 2. Índice para lookup rápido por slug (apenas onde slug não é nulo)
CREATE INDEX IF NOT EXISTS idx_perfis_b2b_slug
  ON public.perfis_b2b(slug_vitrine)
  WHERE slug_vitrine IS NOT NULL;

-- 3. Política pública de leitura da vitrine (só expõe perfis com slug configurado)
DROP POLICY IF EXISTS "Leitura pública de vitrine por slug" ON public.perfis_b2b;
CREATE POLICY "Leitura pública de vitrine por slug"
ON public.perfis_b2b FOR SELECT
TO public
USING (slug_vitrine IS NOT NULL);
