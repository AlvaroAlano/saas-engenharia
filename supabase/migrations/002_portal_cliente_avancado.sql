-- Migration: 002_portal_cliente_avancado.sql
-- Descrição: Criação das tabelas de diário de obras (feed) e documentos vinculados com RLS.

-- 1. Tabela obras_feed
CREATE TABLE IF NOT EXISTS public.obras_feed (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES public.projetos_clientes(id) ON DELETE CASCADE,
    descricao TEXT NOT NULL,
    imagens TEXT[] DEFAULT '{}'::text[], -- Array de URLs das fotos
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    usuario_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid()
);

-- Habilitar RLS em obras_feed
ALTER TABLE public.obras_feed ENABLE ROW LEVEL SECURITY;

-- 2. Tabela projetos_documentos
CREATE TABLE IF NOT EXISTS public.projetos_documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES public.projetos_clientes(id) ON DELETE CASCADE,
    nome_documento TEXT NOT NULL,
    arquivo_url TEXT NOT NULL,
    categoria TEXT NOT NULL, -- ex: 'Planta', 'Contrato', 'Habite-se', 'Outros'
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    usuario_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid()
);

-- Habilitar RLS em projetos_documentos
ALTER TABLE public.projetos_documentos ENABLE ROW LEVEL SECURITY;

-- 3. Índices de Otimização
CREATE INDEX IF NOT EXISTS idx_obras_feed_projeto ON public.obras_feed(projeto_id);
CREATE INDEX IF NOT EXISTS idx_projetos_documentos_projeto ON public.projetos_documentos(projeto_id);

-- 4. Políticas de RLS para obras_feed
DROP POLICY IF EXISTS "Engenheiro gerencia feed do projeto" ON public.obras_feed;
CREATE POLICY "Engenheiro gerencia feed do projeto"
ON public.obras_feed FOR ALL
TO authenticated
USING (auth.uid() = usuario_id)
WITH CHECK (auth.uid() = usuario_id);

DROP POLICY IF EXISTS "Leitura publica do feed via token ativo" ON public.obras_feed;
CREATE POLICY "Leitura publica do feed via token ativo"
ON public.obras_feed FOR SELECT
TO public
USING (
    EXISTS (
        SELECT 1 FROM public.orcamento_links
        WHERE orcamento_links.projeto_id = obras_feed.projeto_id
          AND orcamento_links.ativo = true
    )
);

-- 5. Políticas de RLS para projetos_documentos
DROP POLICY IF EXISTS "Engenheiro gerencia documentos do projeto" ON public.projetos_documentos;
CREATE POLICY "Engenheiro gerencia documentos do projeto"
ON public.projetos_documentos FOR ALL
TO authenticated
USING (auth.uid() = usuario_id)
WITH CHECK (auth.uid() = usuario_id);

DROP POLICY IF EXISTS "Leitura publica de documentos via token ativo" ON public.projetos_documentos;
CREATE POLICY "Leitura publica de documentos via token ativo"
ON public.projetos_documentos FOR SELECT
TO public
USING (
    EXISTS (
        SELECT 1 FROM public.orcamento_links
        WHERE orcamento_links.projeto_id = projetos_documentos.projeto_id
          AND orcamento_links.ativo = true
    )
);
