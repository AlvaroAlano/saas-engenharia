-- Migration: 001_engenheiros_disponiveis.sql
-- Descrição: Tabela para controle de engenheiros disponíveis para matchmaking B2C.

CREATE TABLE IF NOT EXISTS public.engenheiros_disponiveis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES public.perfis_b2b(id) ON DELETE CASCADE UNIQUE,
    ufs_atuacao TEXT[] NOT NULL,
    especialidades TEXT[] NOT NULL,
    raio_km INTEGER NOT NULL DEFAULT 50,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Habilitar RLS
ALTER TABLE public.engenheiros_disponiveis ENABLE ROW LEVEL SECURITY;

-- Política de SELECT público: qualquer prospect (mesmo não autenticado) pode ver
CREATE POLICY "Leitura pública de engenheiros disponíveis"
ON public.engenheiros_disponiveis FOR SELECT
USING (true);

-- Política de ALL restrita ao próprio engenheiro
CREATE POLICY "Engenheiro gerencia apenas a própria disponibilidade"
ON public.engenheiros_disponiveis FOR ALL
USING (auth.uid() = usuario_id)
WITH CHECK (auth.uid() = usuario_id);
