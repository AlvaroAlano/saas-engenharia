-- Migration: 008_classificacao_sinapi_e_templates_insumos.sql
-- 1. Adiciona coluna classificacao em sinapi_itens (Material / Mão de Obra / Equipamento / Serviço)
-- 2. Recria RPC upsert_sinapi_lote para incluir a nova coluna
-- 3. Re-seed dos templates SISTEMA com códigos corretos de insumos puros (ISD/ISE)

-- ==========================================================================
-- 1. COLUNA classificacao em sinapi_itens
-- ==========================================================================

ALTER TABLE public.sinapi_itens
    ADD COLUMN IF NOT EXISTS classificacao VARCHAR(50);

-- ==========================================================================
-- 2. RPC upsert_sinapi_lote (recria com suporte à classificacao)
-- ==========================================================================

CREATE OR REPLACE FUNCTION public.upsert_sinapi_lote(payload JSONB)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO public.sinapi_itens
        (codigo_item, descricao, unidade, preco, estado, mes_ano, desonerado, classificacao)
    SELECT
        (elem->>'codigo_item')::varchar,
        elem->>'descricao',
        elem->>'unidade',
        (elem->>'preco')::numeric,
        (elem->>'estado')::varchar,
        (elem->>'mes_ano')::varchar,
        (elem->>'desonerado')::boolean,
        elem->>'classificacao'
    FROM jsonb_array_elements(payload) AS elem
    ON CONFLICT (codigo_item, estado, mes_ano, desonerado)
    DO UPDATE SET
        descricao      = EXCLUDED.descricao,
        unidade        = EXCLUDED.unidade,
        preco          = EXCLUDED.preco,
        classificacao  = COALESCE(EXCLUDED.classificacao, public.sinapi_itens.classificacao);
END;
$$;

-- ==========================================================================
-- 3. RE-SEED DOS TEMPLATES SISTEMA
--    Substitui códigos de composição pelos insumos puros do catálogo ISD/ISE.
--    Fase/Categoria  →  código SINAPI (insumo)
--    fator = 1.0 (quantidade=0 no novo fluxo; engenheiro preenche)
-- ==========================================================================

DELETE FROM public.template_eap_itens
WHERE template_id IN (
    SELECT id FROM public.templates_eap WHERE tipo = 'SISTEMA'
);

-- --------------------------------------------------------------------------
-- TEMPLATE POPULAR
-- Foco: materiais e mão de obra essenciais, acabamentos básicos
-- --------------------------------------------------------------------------
INSERT INTO public.template_eap_itens (template_id, codigo_sinapi, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    -- Serviços Preliminares: encarregado + servente + betoneira
    ('4083',  'servicos_preliminares', 1.0),
    ('6111',  'servicos_preliminares', 1.0),
    ('10535', 'servicos_preliminares', 1.0),

    -- Infraestrutura: armação, estrutura, forma
    ('378',   'infraestrutura', 1.0),  -- ARMADOR
    ('4750',  'infraestrutura', 1.0),  -- PEDREIRO
    ('1379',  'infraestrutura', 1.0),  -- CIMENTO CP II-32
    ('370',   'infraestrutura', 1.0),  -- AREIA MEDIA
    ('4721',  'infraestrutura', 1.0),  -- PEDRA BRITADA N.1
    ('43059', 'infraestrutura', 1.0),  -- ACO CA-50
    ('43132', 'infraestrutura', 1.0),  -- ARAME RECOZIDO
    ('6189',  'infraestrutura', 1.0),  -- TABUA PINUS
    ('5061',  'infraestrutura', 1.0),  -- PREGO

    -- Superestrutura: alvenaria
    ('7258',  'superestrutura', 1.0),  -- TIJOLO CERAMICO

    -- Instalações: hidráulica e elétrica básica
    ('2696',  'instalacoes', 1.0),  -- ENCANADOR
    ('2436',  'instalacoes', 1.0),  -- ELETRICISTA
    ('9868',  'instalacoes', 1.0),  -- TUBO PVC ESGOTO DN100
    ('9838',  'instalacoes', 1.0),  -- TUBO PVC AGUA DN25
    ('39389', 'instalacoes', 1.0),  -- CABO COBRE 2,5MM
    ('12042', 'instalacoes', 1.0),  -- ELETRODUTO PVC 25MM
    ('38083', 'instalacoes', 1.0),  -- CAIXA DE LUZ 4X2

    -- Acabamentos: revestimento e pintura básica
    ('37329', 'acabamentos', 1.0),  -- PISO CERAMICO
    ('1381',  'acabamentos', 1.0),  -- ARGAMASSA COLANTE AC I
    ('7356',  'acabamentos', 1.0),  -- TINTA ACRILICA
    ('4056',  'acabamentos', 1.0)   -- MASSA CORRIDA
) AS v(codigo_sinapi, fase_obra, fator)
ON (t.padrao_obra = 'popular' AND t.tipo = 'SISTEMA');

-- --------------------------------------------------------------------------
-- TEMPLATE MÉDIO
-- Adiciona: carpinteiro de formas, vibrador, serra, disjuntor, gesso
-- --------------------------------------------------------------------------
INSERT INTO public.template_eap_itens (template_id, codigo_sinapi, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    -- Serviços Preliminares
    ('4083',  'servicos_preliminares', 1.0),
    ('6111',  'servicos_preliminares', 1.0),
    ('10535', 'servicos_preliminares', 1.0),
    ('10642', 'servicos_preliminares', 1.0),  -- VIBRADOR DE IMERSAO

    -- Infraestrutura
    ('378',   'infraestrutura', 1.0),
    ('4750',  'infraestrutura', 1.0),
    ('1213',  'infraestrutura', 1.0),  -- CARPINTEIRO DE FORMAS
    ('1379',  'infraestrutura', 1.0),
    ('370',   'infraestrutura', 1.0),
    ('4721',  'infraestrutura', 1.0),
    ('43059', 'infraestrutura', 1.0),
    ('43132', 'infraestrutura', 1.0),
    ('6189',  'infraestrutura', 1.0),
    ('5061',  'infraestrutura', 1.0),

    -- Superestrutura
    ('7258',  'superestrutura', 1.0),

    -- Instalações
    ('2696',  'instalacoes', 1.0),
    ('2436',  'instalacoes', 1.0),
    ('9868',  'instalacoes', 1.0),
    ('9838',  'instalacoes', 1.0),
    ('39389', 'instalacoes', 1.0),
    ('12042', 'instalacoes', 1.0),
    ('39443', 'instalacoes', 1.0),  -- DISJUNTOR 20A
    ('38083', 'instalacoes', 1.0),

    -- Acabamentos
    ('1332',  'acabamentos', 1.0),  -- GESSO ACARTONADO
    ('37329', 'acabamentos', 1.0),
    ('1381',  'acabamentos', 1.0),
    ('7356',  'acabamentos', 1.0),
    ('4056',  'acabamentos', 1.0)
) AS v(codigo_sinapi, fase_obra, fator)
ON (t.padrao_obra = 'medio' AND t.tipo = 'SISTEMA');

-- --------------------------------------------------------------------------
-- TEMPLATE ALTO PADRÃO
-- Mesmo conjunto do Médio — distinção fica nas quantidades que o engenheiro define
-- --------------------------------------------------------------------------
INSERT INTO public.template_eap_itens (template_id, codigo_sinapi, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    ('4083',  'servicos_preliminares', 1.0),
    ('6111',  'servicos_preliminares', 1.0),
    ('10535', 'servicos_preliminares', 1.0),
    ('10642', 'servicos_preliminares', 1.0),

    ('378',   'infraestrutura', 1.0),
    ('4750',  'infraestrutura', 1.0),
    ('1213',  'infraestrutura', 1.0),
    ('1379',  'infraestrutura', 1.0),
    ('370',   'infraestrutura', 1.0),
    ('4721',  'infraestrutura', 1.0),
    ('43059', 'infraestrutura', 1.0),
    ('43132', 'infraestrutura', 1.0),
    ('6189',  'infraestrutura', 1.0),
    ('5061',  'infraestrutura', 1.0),

    ('7258',  'superestrutura', 1.0),

    ('2696',  'instalacoes', 1.0),
    ('2436',  'instalacoes', 1.0),
    ('9868',  'instalacoes', 1.0),
    ('9838',  'instalacoes', 1.0),
    ('39389', 'instalacoes', 1.0),
    ('12042', 'instalacoes', 1.0),
    ('39443', 'instalacoes', 1.0),
    ('38083', 'instalacoes', 1.0),

    ('1332',  'acabamentos', 1.0),
    ('37329', 'acabamentos', 1.0),
    ('1381',  'acabamentos', 1.0),
    ('7356',  'acabamentos', 1.0),
    ('4056',  'acabamentos', 1.0)
) AS v(codigo_sinapi, fase_obra, fator)
ON (t.padrao_obra = 'alto' AND t.tipo = 'SISTEMA');
