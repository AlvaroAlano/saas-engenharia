-- Migration 016: Fases de Obra gerenciáveis por tenant
-- Permite criar, renomear, reordenar e excluir fases além das 5 do sistema.

-- ==========================================================================
-- 1. TABELA
-- ==========================================================================

CREATE TABLE IF NOT EXISTS public.fases_obra (
    id         UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID      REFERENCES auth.users(id) ON DELETE CASCADE,
    value      TEXT      NOT NULL,   -- slug imutável (usado em fase_obra / etapa_obra)
    label      TEXT      NOT NULL,
    icon       TEXT      NOT NULL DEFAULT 'engineering',
    color      TEXT      NOT NULL DEFAULT 'blue',
    ordem      SMALLINT  NOT NULL DEFAULT 99,
    tipo       TEXT      NOT NULL CHECK (tipo IN ('SISTEMA', 'CUSTOMIZADO')),
    criado_em  TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Slug único por contexto
CREATE UNIQUE INDEX IF NOT EXISTS idx_fases_obra_sistema_value
    ON public.fases_obra(value) WHERE tipo = 'SISTEMA';

CREATE UNIQUE INDEX IF NOT EXISTS idx_fases_obra_custom_value
    ON public.fases_obra(usuario_id, value) WHERE tipo = 'CUSTOMIZADO';

-- ==========================================================================
-- 2. RLS
-- ==========================================================================

ALTER TABLE public.fases_obra ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Leitura das fases de sistema" ON public.fases_obra;
CREATE POLICY "Leitura das fases de sistema"
ON public.fases_obra FOR SELECT TO authenticated
USING (tipo = 'SISTEMA');

DROP POLICY IF EXISTS "Engenheiro gerencia suas fases customizadas" ON public.fases_obra;
CREATE POLICY "Engenheiro gerencia suas fases customizadas"
ON public.fases_obra FOR ALL TO authenticated
USING  (tipo = 'CUSTOMIZADO' AND auth.uid() = usuario_id)
WITH CHECK (tipo = 'CUSTOMIZADO' AND auth.uid() = usuario_id);

-- ==========================================================================
-- 3. SEED — 5 fases padrão do sistema (idempotente)
-- ==========================================================================

INSERT INTO public.fases_obra (value, label, icon, color, ordem, tipo)
VALUES
    ('servicos_preliminares', 'Serviços Preliminares',          'engineering',   'amber',   1, 'SISTEMA'),
    ('infraestrutura',        'Infraestrutura (Fundação)',       'foundation',    'orange',  2, 'SISTEMA'),
    ('superestrutura',        'Superestrutura (Alvenaria/Lajes)','domain',        'blue',    3, 'SISTEMA'),
    ('instalacoes',           'Instalações (Hidráulica/Elétrica)','electric_bolt','violet',  4, 'SISTEMA'),
    ('acabamentos',           'Acabamentos',                    'format_paint',  'emerald', 5, 'SISTEMA')
ON CONFLICT DO NOTHING;
