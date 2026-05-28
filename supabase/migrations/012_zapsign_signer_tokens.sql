-- Migration 012: Rastreamento individual de assinaturas ZapSign
-- Adiciona tokens dos signatários para identificar quem assinou no webhook,
-- e URL do contrato assinado (PDF final fornecido pela ZapSign no doc_signed).

ALTER TABLE projetos_clientes
    ADD COLUMN IF NOT EXISTS zapsign_signer_token_cliente     TEXT,
    ADD COLUMN IF NOT EXISTS zapsign_signer_token_engenheiro  TEXT,
    ADD COLUMN IF NOT EXISTS url_contrato_assinado            TEXT;
