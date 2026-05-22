-- Migration: 006_templates_eap.sql
-- EAP Padrão: Templates Paramétricos Customizáveis por Tenant

-- ==========================================================================
-- 1. TABELAS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS public.templates_eap (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome        TEXT NOT NULL,
    tipo        TEXT NOT NULL CHECK (tipo IN ('SISTEMA', 'CUSTOMIZADO')),
    padrao_obra TEXT NOT NULL CHECK (padrao_obra IN ('popular', 'medio', 'alto')),
    usuario_id  UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    criado_em   TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

CREATE TABLE IF NOT EXISTS public.template_eap_itens (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id             UUID NOT NULL REFERENCES public.templates_eap(id) ON DELETE CASCADE,
    codigo_sinapi           TEXT NOT NULL,
    descricao               TEXT NOT NULL,
    unidade                 TEXT NOT NULL,
    fase_obra               TEXT NOT NULL,
    fator_area_multiplicador NUMERIC(10, 4) NOT NULL CHECK (fator_area_multiplicador > 0)
);

-- ==========================================================================
-- 2. ÍNDICES
-- ==========================================================================

-- Garante um único template SISTEMA por padrão de obra
CREATE UNIQUE INDEX IF NOT EXISTS idx_templates_eap_sistema_padrao
    ON public.templates_eap(padrao_obra)
    WHERE tipo = 'SISTEMA';

-- Garante um único template CUSTOMIZADO por (usuário + padrão)
CREATE UNIQUE INDEX IF NOT EXISTS idx_templates_eap_customizado_padrao
    ON public.templates_eap(usuario_id, padrao_obra)
    WHERE tipo = 'CUSTOMIZADO';

CREATE INDEX IF NOT EXISTS idx_template_eap_itens_template
    ON public.template_eap_itens(template_id);

-- ==========================================================================
-- 3. RLS
-- ==========================================================================

ALTER TABLE public.templates_eap ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.template_eap_itens ENABLE ROW LEVEL SECURITY;

-- templates_eap: qualquer autenticado lê SISTEMA
DROP POLICY IF EXISTS "Leitura dos templates de sistema" ON public.templates_eap;
CREATE POLICY "Leitura dos templates de sistema"
ON public.templates_eap FOR SELECT
TO authenticated
USING (tipo = 'SISTEMA');

-- templates_eap: engenheiro gerencia apenas seus CUSTOMIZADOS
DROP POLICY IF EXISTS "Engenheiro gerencia templates customizados" ON public.templates_eap;
CREATE POLICY "Engenheiro gerencia templates customizados"
ON public.templates_eap FOR ALL
TO authenticated
USING (tipo = 'CUSTOMIZADO' AND auth.uid() = usuario_id)
WITH CHECK (tipo = 'CUSTOMIZADO' AND auth.uid() = usuario_id);

-- template_eap_itens: leitura via template SISTEMA ou próprio CUSTOMIZADO
DROP POLICY IF EXISTS "Leitura dos itens de templates visíveis" ON public.template_eap_itens;
CREATE POLICY "Leitura dos itens de templates visíveis"
ON public.template_eap_itens FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.templates_eap t
        WHERE t.id = template_eap_itens.template_id
          AND (t.tipo = 'SISTEMA' OR (t.tipo = 'CUSTOMIZADO' AND t.usuario_id = auth.uid()))
    )
);

-- template_eap_itens: escrita apenas em templates CUSTOMIZADOS do próprio usuário
DROP POLICY IF EXISTS "Engenheiro gerencia itens dos próprios templates" ON public.template_eap_itens;
CREATE POLICY "Engenheiro gerencia itens dos próprios templates"
ON public.template_eap_itens FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.templates_eap t
        WHERE t.id = template_eap_itens.template_id
          AND t.tipo = 'CUSTOMIZADO'
          AND t.usuario_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.templates_eap t
        WHERE t.id = template_eap_itens.template_id
          AND t.tipo = 'CUSTOMIZADO'
          AND t.usuario_id = auth.uid()
    )
);

-- ==========================================================================
-- 4. SEED — Templates SISTEMA (idempotente via ON CONFLICT DO NOTHING)
-- ==========================================================================

INSERT INTO public.templates_eap (nome, tipo, padrao_obra)
VALUES
    ('Residencial Popular',          'SISTEMA', 'popular'),
    ('Residencial Médio',            'SISTEMA', 'medio'),
    ('Residencial Alto Padrão',      'SISTEMA', 'alto')
ON CONFLICT DO NOTHING;

-- Itens do template Popular
INSERT INTO public.template_eap_itens
    (template_id, codigo_sinapi, descricao, unidade, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.descricao, v.unidade, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    ('98544', 'Tapume em chapa de madeira compensada 6mm',     'M²',  'servicos_preliminares', 0.50),
    ('98459', 'Instalação provisória de água e esgoto',        'UN',  'servicos_preliminares', 0.01),
    ('93358', 'Escavação manual em solo de 1ª categoria',       'M³',  'infraestrutura',        0.25),
    ('94970', 'Concreto estrutural fck=20MPa, usinado',         'M³',  'infraestrutura',        0.12),
    ('92767', 'Armação passiva CA-50 diam. 10,0mm',            'KG',  'infraestrutura',        2.50),
    ('87503', 'Alvenaria de vedação bloco cerâmico 9x19x19cm', 'M²',  'superestrutura',        2.20),
    ('92414', 'Laje pré-moldada treliçada para piso',          'M²',  'superestrutura',        1.05),
    ('89707', 'Tubo PVC, série normal, esgoto predial DN=100', 'M',   'instalacoes',           0.12),
    ('91926', 'Cabo de cobre flexível 2,5mm², 750V',           'M',   'instalacoes',           0.80),
    ('88489', 'Revestimento cerâmico p/ paredes, PEI-3',       'M²',  'acabamentos',           0.40),
    ('88411', 'Pintura látex acrílica, 2 demãos, em paredes',  'M²',  'acabamentos',           1.80)
) AS v(codigo_sinapi, descricao, unidade, fase_obra, fator)
ON (t.padrao_obra = 'popular' AND t.tipo = 'SISTEMA')
WHERE NOT EXISTS (
    SELECT 1 FROM public.template_eap_itens WHERE template_id = t.id
);

-- Itens do template Médio
INSERT INTO public.template_eap_itens
    (template_id, codigo_sinapi, descricao, unidade, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.descricao, v.unidade, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    ('98544', 'Tapume em chapa de madeira compensada 6mm',     'M²',  'servicos_preliminares', 0.60),
    ('98459', 'Instalação provisória de água e esgoto',        'UN',  'servicos_preliminares', 0.01),
    ('93358', 'Escavação manual em solo de 1ª categoria',       'M³',  'infraestrutura',        0.30),
    ('94970', 'Concreto estrutural fck=25MPa, usinado',         'M³',  'infraestrutura',        0.15),
    ('92767', 'Armação passiva CA-50 diam. 10,0mm',            'KG',  'infraestrutura',        3.00),
    ('87503', 'Alvenaria de vedação bloco cerâmico 9x19x19cm', 'M²',  'superestrutura',        2.50),
    ('92414', 'Laje pré-moldada treliçada para piso',          'M²',  'superestrutura',        1.05),
    ('89707', 'Tubo PVC, série normal, esgoto predial DN=100', 'M',   'instalacoes',           0.15),
    ('91926', 'Cabo de cobre flexível 2,5mm², 750V',           'M',   'instalacoes',           1.00),
    ('88489', 'Revestimento cerâmico p/ paredes, PEI-3',       'M²',  'acabamentos',           0.50),
    ('88411', 'Pintura látex acrílica, 2 demãos, em paredes',  'M²',  'acabamentos',           2.20)
) AS v(codigo_sinapi, descricao, unidade, fase_obra, fator)
ON (t.padrao_obra = 'medio' AND t.tipo = 'SISTEMA')
WHERE NOT EXISTS (
    SELECT 1 FROM public.template_eap_itens WHERE template_id = t.id
);

-- Itens do template Alto
INSERT INTO public.template_eap_itens
    (template_id, codigo_sinapi, descricao, unidade, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.descricao, v.unidade, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    ('98544', 'Tapume em chapa de madeira compensada 6mm',     'M²',  'servicos_preliminares', 0.70),
    ('98459', 'Instalação provisória de água e esgoto',        'UN',  'servicos_preliminares', 0.01),
    ('93358', 'Escavação manual em solo de 1ª categoria',       'M³',  'infraestrutura',        0.40),
    ('94970', 'Concreto estrutural fck=30MPa, usinado',         'M³',  'infraestrutura',        0.20),
    ('92767', 'Armação passiva CA-50 diam. 10,0mm',            'KG',  'infraestrutura',        4.00),
    ('87503', 'Alvenaria de vedação bloco cerâmico 9x19x19cm', 'M²',  'superestrutura',        2.80),
    ('92414', 'Laje pré-moldada treliçada para piso',          'M²',  'superestrutura',        1.10),
    ('89707', 'Tubo PVC, série normal, esgoto predial DN=100', 'M',   'instalacoes',           0.20),
    ('91926', 'Cabo de cobre flexível 2,5mm², 750V',           'M',   'instalacoes',           1.30),
    ('88489', 'Revestimento cerâmico p/ paredes, PEI-3',       'M²',  'acabamentos',           0.65),
    ('88411', 'Pintura látex acrílica, 2 demãos, em paredes',  'M²',  'acabamentos',           2.50)
) AS v(codigo_sinapi, descricao, unidade, fase_obra, fator)
ON (t.padrao_obra = 'alto' AND t.tipo = 'SISTEMA')
WHERE NOT EXISTS (
    SELECT 1 FROM public.template_eap_itens WHERE template_id = t.id
);
