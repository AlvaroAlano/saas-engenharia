-- Migration: 005_realtime_projetos_clientes.sql
-- Descrição: Habilita Supabase Realtime para a tabela projetos_clientes,
--            permitindo que o Kanban receba atualizações em tempo real via WebSocket.

-- REPLICA IDENTITY FULL garante que eventos UPDATE enviem o registro completo
-- (antigo e novo), essencial para o handler do Kanban identificar a coluna de origem.
ALTER TABLE public.projetos_clientes REPLICA IDENTITY FULL;

-- Adiciona a tabela à publicação padrão do Supabase Realtime.
-- Sem isso, nenhum evento é enviado ao cliente, mesmo com o subscribe() ativo.
ALTER PUBLICATION supabase_realtime ADD TABLE public.projetos_clientes;
