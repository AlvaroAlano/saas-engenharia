-- Migration: 010_tipo_template_contrato.sql
-- Adiciona coluna `tipo` na tabela templates_contrato para distinguir
-- Proposta Comercial (valores CUB) de Contrato de Construção (valores SINAPI).

ALTER TABLE templates_contrato
  ADD COLUMN IF NOT EXISTS tipo text DEFAULT 'proposta'
    CHECK (tipo IN ('proposta', 'contrato'));
