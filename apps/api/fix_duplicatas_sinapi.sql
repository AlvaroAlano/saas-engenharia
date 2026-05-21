-- ============================================================
-- SCRIPT DE CORREÇÃO: Duplicatas na tabela sinapi_itens
-- Executar no SQL Editor do Supabase (painel web)
-- ============================================================

-- PASSO 1: Remover as linhas duplicadas, mantendo apenas a mais recente (maior id)
-- Esta CTE identifica todas as linhas que NÃO são a "melhor" (mais recente) para
-- cada combinação de chave natural (codigo_item + estado + mes_ano + desonerado)
DELETE FROM sinapi_itens
WHERE id NOT IN (
    SELECT DISTINCT ON (codigo_item, estado, mes_ano, desonerado) id
    FROM sinapi_itens
    ORDER BY codigo_item, estado, mes_ano, desonerado, id DESC
);

-- PASSO 2: Criar a constraint UNIQUE composta que impede futuras duplicatas
-- Se a constraint já existir, este comando não fará nada (usa IF NOT EXISTS implicitamente via DO)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_sinapi_itens_chave_natural'
    ) THEN
        ALTER TABLE sinapi_itens
        ADD CONSTRAINT uq_sinapi_itens_chave_natural
        UNIQUE (codigo_item, estado, mes_ano, desonerado);
    END IF;
END $$;

-- VERIFICAÇÃO: Após rodar, execute esta query para confirmar que não há mais duplicatas
-- SELECT codigo_item, estado, mes_ano, desonerado, COUNT(*)
-- FROM sinapi_itens
-- GROUP BY codigo_item, estado, mes_ano, desonerado
-- HAVING COUNT(*) > 1;
