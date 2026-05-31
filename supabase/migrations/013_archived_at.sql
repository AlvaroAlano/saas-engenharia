-- Migration 013: Campo archived_at em projetos_clientes
-- Registra o momento exato em que um projeto foi arquivado,
-- em vez de usar created_at como proxy (que é a data de criação).

ALTER TABLE projetos_clientes
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

-- Trigger: define/limpa archived_at automaticamente na mudança de status
CREATE OR REPLACE FUNCTION set_archived_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'ARQUIVADO' AND (OLD.status IS DISTINCT FROM 'ARQUIVADO') THEN
        NEW.archived_at = NOW();
    ELSIF NEW.status != 'ARQUIVADO' AND OLD.status = 'ARQUIVADO' THEN
        NEW.archived_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_archived_at ON projetos_clientes;
CREATE TRIGGER trg_set_archived_at
    BEFORE UPDATE ON projetos_clientes
    FOR EACH ROW EXECUTE FUNCTION set_archived_at();
