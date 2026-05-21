-- =========================================================================
-- FASE 9.2 (Passo 4): Sincronização Automática de Perfis B2B
-- =========================================================================

-- 1. Função de Sincronização de Usuário
-- O SECURITY DEFINER garante que esta função execute com privilégios de criador (bypass RLS/Roles)
-- O SET search_path = public é uma prática de segurança recomendada para funções SECURITY DEFINER
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.perfis_b2b (id, email, nome_completo, registro_crea_cau)
  VALUES (
    NEW.id,
    NEW.email,
    -- Extraindo os metadados repassados pelo Frontend via options.data no signUp
    -- Usamos COALESCE para garantir que um valor default seja salvo caso falhe
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'Engenheiro B2B'),
    NEW.raw_user_meta_data->>'crea_cau'
  );
  
  RETURN NEW;
END;
$$;

-- 2. Gatilho (Trigger) de Monitoramento
-- Drop preventivo caso você vá atualizar a função futuramente
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Associa a função de sincronização à tabela auth.users sempre que um INSERT ocorrer
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user();
