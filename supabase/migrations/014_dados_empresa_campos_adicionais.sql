-- Migration 014: Campos adicionais em dados_empresa
-- Adiciona informações de contato e web da empresa, usadas nos contratos e portal.

ALTER TABLE public.dados_empresa
  ADD COLUMN IF NOT EXISTS site_url         TEXT,
  ADD COLUMN IF NOT EXISTS email_empresa    TEXT,
  ADD COLUMN IF NOT EXISTS telefone_empresa TEXT;
