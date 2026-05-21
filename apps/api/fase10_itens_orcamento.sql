-- =========================================================================
-- FASE 10: MOTOR DE ORÇAMENTAÇÃO (CARRINHO)
-- Tabela: orcamento_itens
-- =========================================================================

-- Dropar a versão antiga (caso exista da Fase 1) que usava obra_id
DROP TABLE IF EXISTS public.orcamento_itens CASCADE;

CREATE TABLE public.orcamento_itens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orcamento_id UUID REFERENCES public.orcamentos(id) ON DELETE CASCADE,
    codigo_sinapi VARCHAR NOT NULL,
    descricao TEXT NOT NULL,
    unidade VARCHAR NOT NULL,
    quantidade DECIMAL(15,2) DEFAULT 1.0,
    valor_unitario DECIMAL(15,2) NOT NULL,
    tipo_item VARCHAR NOT NULL CHECK (tipo_item IN ('insumo', 'composicao')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Habilitar RLS
ALTER TABLE public.orcamento_itens ENABLE ROW LEVEL SECURITY;

-- Política de SELECT: O usuário só vê itens dos orçamentos que ele é dono
CREATE POLICY "Ver itens dos meus orcamentos"
ON public.orcamento_itens FOR SELECT
USING (
    orcamento_id IN (
        SELECT id FROM public.orcamentos WHERE usuario_id = auth.uid()
    )
);

-- Política de INSERT: Só insere em orçamentos que ele é dono
CREATE POLICY "Inserir itens nos meus orcamentos"
ON public.orcamento_itens FOR INSERT
WITH CHECK (
    orcamento_id IN (
        SELECT id FROM public.orcamentos WHERE usuario_id = auth.uid()
    )
);

-- Política de DELETE: Só deleta dos orçamentos que ele é dono
CREATE POLICY "Deletar itens dos meus orcamentos"
ON public.orcamento_itens FOR DELETE
USING (
    orcamento_id IN (
        SELECT id FROM public.orcamentos WHERE usuario_id = auth.uid()
    )
);
