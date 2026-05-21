-- ⚠️ DEPRECADO: Este arquivo contém apenas a modelagem inicial de rascunho. O schema real e as políticas RLS seguras estão ativas diretamente no Supabase Dashboard.
-- Não rode este script para evitar sobrescrever a produção com permissões inseguras.

-- Passo 1: Habilitar a extensão pgcrypto se não estiver (para usar UUID)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Passo 2: Criação da Tabela Obras
CREATE TABLE obras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    valor_total NUMERIC(15, 2) DEFAULT 0.00,
    status_geral TEXT DEFAULT 'pendente',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Passo 3: Criação da Tabela Clientes
CREATE TABLE clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    telefone TEXT,
    status_caixa TEXT DEFAULT 'analise',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Passo 4: Criação da Tabela Documentos
CREATE TABLE documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    tipo_documento TEXT NOT NULL,
    status TEXT CHECK (status IN ('pendente', 'em_verificacao', 'aprovado', 'rejeitado')) DEFAULT 'pendente',
    url_arquivo TEXT,
    feedback_rejeicao TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Passo 5: Habilitar RLS nas tabelas
ALTER TABLE obras ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos ENABLE ROW LEVEL SECURITY;

-- Passo 6: Criar políticas permissivas (apenas para ambiente de desenvolvimento/teste)
-- ATENÇÃO: NÃO USE ESTAS POLÍTICAS EM PRODUÇÃO

CREATE POLICY "Permitir leitura anonima obras" ON obras FOR SELECT USING (true);
CREATE POLICY "Permitir insercao anonima obras" ON obras FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir atualizacao anonima obras" ON obras FOR UPDATE USING (true);
CREATE POLICY "Permitir delecao anonima obras" ON obras FOR DELETE USING (true);

CREATE POLICY "Permitir leitura anonima clientes" ON clientes FOR SELECT USING (true);
CREATE POLICY "Permitir insercao anonima clientes" ON clientes FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir atualizacao anonima clientes" ON clientes FOR UPDATE USING (true);
CREATE POLICY "Permitir delecao anonima clientes" ON clientes FOR DELETE USING (true);

CREATE POLICY "Permitir leitura anonima documentos" ON documentos FOR SELECT USING (true);
CREATE POLICY "Permitir insercao anonima documentos" ON documentos FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir atualizacao anonima documentos" ON documentos FOR UPDATE USING (true);
CREATE POLICY "Permitir delecao anonima documentos" ON documentos FOR DELETE USING (true);

-- Passo 7: Criação da Tabela SINAPI (Catálogo de Itens)
CREATE TABLE sinapi_itens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estado VARCHAR(2) NOT NULL,
    mes_ano VARCHAR(7) NOT NULL,
    desonerado BOOLEAN NOT NULL DEFAULT false,
    codigo_item VARCHAR(50) NOT NULL,
    descricao TEXT,
    unidade VARCHAR(20),
    preco NUMERIC(15, 2) NOT NULL
);

-- Índice composto para acelerar buscas no Orçamentador
CREATE INDEX IF NOT EXISTS idx_sinapi_busca_rapida 
ON sinapi_itens (estado, mes_ano, desonerado, codigo_item);

ALTER TABLE sinapi_itens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir leitura anonima sinapi" ON sinapi_itens FOR SELECT USING (true);
CREATE POLICY "Permitir insercao anonima sinapi" ON sinapi_itens FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir atualizacao anonima sinapi" ON sinapi_itens FOR UPDATE USING (true);
CREATE POLICY "Permitir delecao anonima sinapi" ON sinapi_itens FOR DELETE USING (true);

-- Passo 8: Criação da Tabela Orçamento Itens (Carrinho)
CREATE TABLE orcamento_itens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
    sinapi_item_id UUID REFERENCES sinapi_itens(id) ON DELETE RESTRICT,
    quantidade NUMERIC(15, 2) NOT NULL,
    preco_congelado NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

ALTER TABLE orcamento_itens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir leitura anonima orcamento_itens" ON orcamento_itens FOR SELECT USING (true);
CREATE POLICY "Permitir insercao anonima orcamento_itens" ON orcamento_itens FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir atualizacao anonima orcamento_itens" ON orcamento_itens FOR UPDATE USING (true);
CREATE POLICY "Permitir delecao anonima orcamento_itens" ON orcamento_itens FOR DELETE USING (true);

-- Passo 9: Criação da Tabela Composições (Cabeçalho do serviço)
CREATE TABLE public.sinapi_composicoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_composicao VARCHAR UNIQUE NOT NULL,
    descricao TEXT NOT NULL,
    unidade VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Passo 10: Criação da Tabela Itens da Composição (A Receita do Bolo)
CREATE TABLE public.sinapi_composicao_itens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composicao_id UUID REFERENCES public.sinapi_composicoes(id) ON DELETE CASCADE,
    codigo_item VARCHAR NOT NULL,
    tipo_item VARCHAR NOT NULL CHECK (tipo_item IN ('INSUMO', 'COMPOSICAO')),
    coeficiente NUMERIC(15,7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

ALTER TABLE public.sinapi_composicoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sinapi_composicao_itens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir leitura anonima composicoes" 
ON public.sinapi_composicoes FOR SELECT USING (true);

CREATE POLICY "Permitir insercao anonima composicoes" 
ON public.sinapi_composicoes FOR INSERT WITH CHECK (true);

CREATE POLICY "Permitir leitura anonima itens composicao" 
ON public.sinapi_composicao_itens FOR SELECT USING (true);

CREATE POLICY "Permitir insercao anonima itens composicao" 
ON public.sinapi_composicao_itens FOR INSERT WITH CHECK (true);

-- Passo 11: Criação da View de Referências SINAPI
CREATE OR REPLACE VIEW vw_sinapi_referencias AS
SELECT mes_ano
FROM sinapi_itens
GROUP BY mes_ano
ORDER BY substring(mes_ano, 4, 4) DESC, substring(mes_ano, 1, 2) DESC;
