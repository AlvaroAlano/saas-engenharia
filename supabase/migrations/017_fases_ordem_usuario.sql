-- Migration 017: Ordem de fases de obra por usuário
-- Armazena a sequência personalizada de fases por usuário,
-- permitindo reordenar fases SISTEMA e CUSTOMIZADO livremente.

CREATE TABLE IF NOT EXISTS public.fases_obra_user_ordem (
    usuario_id   UUID  PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    valores_ordem TEXT[] NOT NULL DEFAULT '{}',
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

ALTER TABLE public.fases_obra_user_ordem ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Usuário gerencia sua própria ordem de fases" ON public.fases_obra_user_ordem;
CREATE POLICY "Usuário gerencia sua própria ordem de fases"
ON public.fases_obra_user_ordem FOR ALL TO authenticated
USING  (auth.uid() = usuario_id)
WITH CHECK (auth.uid() = usuario_id);
