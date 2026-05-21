-- =========================================================================
-- FASE 9.2: ARQUITETURA MULTI-TENANT (SAAS) E ISOLAMENTO DE DADOS
-- =========================================================================

-- 1. Criação da Tabela de Perfis/Tenants (Engenheiros Assinantes)
CREATE TABLE IF NOT EXISTS public.perfis_b2b (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome_completo TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    registro_crea_cau VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Habilitar RLS na tabela de perfis
ALTER TABLE public.perfis_b2b ENABLE ROW LEVEL SECURITY;

-- Políticas para perfis_b2b (O usuário só pode ver/editar o próprio perfil)
CREATE POLICY "Usuário pode visualizar o próprio perfil" 
ON public.perfis_b2b FOR SELECT 
USING (auth.uid() = id);

CREATE POLICY "Usuário pode atualizar o próprio perfil" 
ON public.perfis_b2b FOR UPDATE 
USING (auth.uid() = id);


-- 2. Criação da Tabela Orçamentos (Caso não exista) e Relacionamento
CREATE TABLE IF NOT EXISTS public.orcamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES public.perfis_b2b(id) ON DELETE CASCADE,
    nome_obra TEXT NOT NULL,
    cliente_nome TEXT,
    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Caso a tabela já existisse no seu banco, o comando abaixo faria a adição da coluna.
-- Como criamos via IF NOT EXISTS com o campo junto, deixamos apenas documentado para caso de alteração em uma tabela de nome diferente (como "obras"):
-- ALTER TABLE public.orcamentos ADD COLUMN usuario_id UUID REFERENCES public.perfis_b2b(id) ON DELETE CASCADE;


-- 3. Políticas de RLS (Row Level Security) para Isolamento Total na Tabela orcamentos
ALTER TABLE public.orcamentos ENABLE ROW LEVEL SECURITY;

-- SELECT: O engenheiro só visualiza os orçamentos onde ele é o dono
CREATE POLICY "Visualizar apenas os próprios orçamentos" 
ON public.orcamentos FOR SELECT 
USING (auth.uid() = usuario_id);

-- INSERT: O engenheiro só pode criar um orçamento vinculado ao seu próprio ID
CREATE POLICY "Inserir orçamentos apenas para si mesmo" 
ON public.orcamentos FOR INSERT 
WITH CHECK (auth.uid() = usuario_id);

-- UPDATE: O engenheiro só pode editar seus próprios orçamentos
CREATE POLICY "Atualizar apenas os próprios orçamentos" 
ON public.orcamentos FOR UPDATE 
USING (auth.uid() = usuario_id);

-- DELETE: O engenheiro só pode excluir seus próprios orçamentos
CREATE POLICY "Deletar apenas os próprios orçamentos" 
ON public.orcamentos FOR DELETE 
USING (auth.uid() = usuario_id);

-- IMPORTANTE:
-- As tabelas sinapi_composicoes e sinapi_composicao_itens e sinapi_itens 
-- continuam com políticas de SELECT USING (true) para que todos os engenheiros 
-- autenticados consigam ler a base universal da Caixa Econômica, mas não alterá-la.
