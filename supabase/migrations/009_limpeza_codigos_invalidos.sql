-- Migration: 009_limpeza_codigos_invalidos.sql
-- Remove do template e dos projetos todos os códigos que não existem em sinapi_itens:
--   • Códigos de composição (antigos, migration 006/007): 98546, 98522, 93358, 94970,
--     92767, 87251, 95959, 89707, 91926, 87250, 88489
--   • Insumos não encontrados na base importada: 3365 (Serra), 42306 (Pintor)

-- ==========================================================================
-- 1. REMOVE OS CÓDIGOS INVÁLIDOS DOS TEMPLATES SISTEMA
-- ==========================================================================

DELETE FROM public.template_eap_itens
WHERE codigo_sinapi IN (
    '98546', '98522',
    '93358', '94970', '92767',
    '87251', '95959',
    '89707', '91926',
    '87250', '88489',
    '3365',  '42306'
)
AND template_id IN (
    SELECT id FROM public.templates_eap WHERE tipo = 'SISTEMA'
);

-- ==========================================================================
-- 2. REMOVE OS ITENS JÁ INSERIDOS NOS PROJETOS COM ESSES CÓDIGOS
--    (inseridos com valor_unitario=0 e descrição "Cód. SINAPI XXXXX" pelo fallback)
-- ==========================================================================

DELETE FROM public.orcamento_itens
WHERE codigo_sinapi IN (
    '98546', '98522',
    '93358', '94970', '92767',
    '87251', '95959',
    '89707', '91926',
    '87250', '88489',
    '3365',  '42306'
);
