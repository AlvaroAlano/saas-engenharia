-- Migration: 007_refactor_template_eap_itens.sql
-- Remove colunas redundantes de template_eap_itens (Single Source of Truth via SINAPI)
-- Substitui seed pelos códigos corretos da planilha SINAPI importada

-- ==========================================================================
-- 1. REMOVE COLUNAS REDUNDANTES
-- ==========================================================================

ALTER TABLE public.template_eap_itens DROP COLUMN IF EXISTS descricao;
ALTER TABLE public.template_eap_itens DROP COLUMN IF EXISTS unidade;

-- ==========================================================================
-- 2. SUBSTITUI SEED (códigos antigos → códigos corretos da base SINAPI)
-- ==========================================================================

DELETE FROM public.template_eap_itens
WHERE template_id IN (
    SELECT id FROM public.templates_eap WHERE tipo = 'SISTEMA'
);

-- Template Popular
INSERT INTO public.template_eap_itens (template_id, codigo_sinapi, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    ('98546', 'servicos_preliminares', 0.50),
    ('98522', 'servicos_preliminares', 0.01),
    ('93358', 'infraestrutura',        0.25),
    ('94964', 'infraestrutura',        0.12),
    ('92767', 'infraestrutura',        2.50),
    ('87256', 'superestrutura',        2.20),
    ('95959', 'superestrutura',        1.05),
    ('89707', 'instalacoes',           0.12),
    ('91926', 'instalacoes',           0.80),
    ('87248', 'acabamentos',           0.40),
    ('88489', 'acabamentos',           1.80)
) AS v(codigo_sinapi, fase_obra, fator)
ON (t.padrao_obra = 'popular' AND t.tipo = 'SISTEMA');

-- Template Médio
INSERT INTO public.template_eap_itens (template_id, codigo_sinapi, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    ('98546', 'servicos_preliminares', 0.60),
    ('98522', 'servicos_preliminares', 0.01),
    ('93358', 'infraestrutura',        0.30),
    ('94970', 'infraestrutura',        0.15),
    ('92767', 'infraestrutura',        3.00),
    ('87251', 'superestrutura',        2.50),
    ('95959', 'superestrutura',        1.05),
    ('89707', 'instalacoes',           0.15),
    ('91926', 'instalacoes',           1.00),
    ('87250', 'acabamentos',           0.50),
    ('88489', 'acabamentos',           2.20)
) AS v(codigo_sinapi, fase_obra, fator)
ON (t.padrao_obra = 'medio' AND t.tipo = 'SISTEMA');

-- Template Alto
INSERT INTO public.template_eap_itens (template_id, codigo_sinapi, fase_obra, fator_area_multiplicador)
SELECT t.id, v.codigo_sinapi, v.fase_obra, v.fator
FROM public.templates_eap t
JOIN (VALUES
    ('98546', 'servicos_preliminares', 0.70),
    ('98522', 'servicos_preliminares', 0.01),
    ('93358', 'infraestrutura',        0.40),
    ('94971', 'infraestrutura',        0.20),
    ('92767', 'infraestrutura',        4.00),
    ('87251', 'superestrutura',        2.80),
    ('95959', 'superestrutura',        1.10),
    ('89707', 'instalacoes',           0.20),
    ('91926', 'instalacoes',           1.30),
    ('87250', 'acabamentos',           0.65),
    ('100746','acabamentos',           2.50)
) AS v(codigo_sinapi, fase_obra, fator)
ON (t.padrao_obra = 'alto' AND t.tipo = 'SISTEMA');
