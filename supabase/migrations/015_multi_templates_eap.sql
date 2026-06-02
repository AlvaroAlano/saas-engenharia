-- Migration 015: Multi-templates EAP por padrão de obra
-- Permite múltiplos templates CUSTOMIZADO por (usuario_id, padrao_obra).
-- Adiciona is_default para controlar qual template é o ativo por padrão.

-- 1. Remove restrição que limitava 1 CUSTOMIZADO por (usuario, padrao)
DROP INDEX IF EXISTS public.idx_templates_eap_customizado_padrao;

-- 2. Adiciona coluna is_default
ALTER TABLE public.templates_eap
  ADD COLUMN IF NOT EXISTS is_default BOOLEAN NOT NULL DEFAULT FALSE;

-- 3. Templates CUSTOMIZADO existentes tornam-se o padrão ativo automaticamente
UPDATE public.templates_eap
  SET is_default = TRUE
  WHERE tipo = 'CUSTOMIZADO';

-- 4. Garante unicidade: apenas 1 CUSTOMIZADO por (usuario_id, padrao_obra) pode ser is_default
CREATE UNIQUE INDEX IF NOT EXISTS idx_templates_eap_one_default_per_padrao
  ON public.templates_eap(usuario_id, padrao_obra)
  WHERE tipo = 'CUSTOMIZADO' AND is_default = TRUE;
