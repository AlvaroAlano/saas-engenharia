-- Tabela de histórico de ações por projeto (auditoria)
CREATE TABLE IF NOT EXISTS public.projetos_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES public.projetos_clientes(id) ON DELETE CASCADE,
    acao TEXT NOT NULL,
    detalhes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

ALTER TABLE public.projetos_historico ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'projetos_historico'
      AND policyname = 'Acesso ao histórico dos meus projetos'
  ) THEN
    CREATE POLICY "Acesso ao histórico dos meus projetos"
    ON public.projetos_historico FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.projetos_clientes
            WHERE projetos_clientes.id = projetos_historico.projeto_id
              AND projetos_clientes.usuario_id = auth.uid()
        )
    );
  END IF;
END $$;
