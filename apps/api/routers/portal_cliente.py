import os
import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client, create_client
from dependencies import get_authenticated_supabase

router = APIRouter(prefix="/api/portal", tags=["Portal Cliente"])

# --- Models ---

class LinkCreateRequest(BaseModel):
    projeto_id: str
    pin_acesso: str

class LinkAcessoRequest(BaseModel):
    token_acesso: str
    pin_acesso: str

# --- Helper ---

def get_service_supabase() -> Client:
    """Retorna um Client Supabase com a Service Role Key (Admin)."""
    url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not service_key:
        raise HTTPException(status_code=500, detail="SUPABASE_SERVICE_ROLE_KEY não configurada.")
    return create_client(url, service_key)

# --- Routes ---

@router.post("/links", status_code=201)
async def gerar_link_b2c(payload: LinkCreateRequest, supabase_client: Client = Depends(get_authenticated_supabase)):
    """
    Gera um link de acesso público (Portal do Cliente) para um projeto específico.
    Protegido por PIN. Chamado pelo Engenheiro. REF: TODO.md P2.1
    """
    if not re.match(r'^\d{4}$', payload.pin_acesso):
        raise HTTPException(status_code=422, detail="O PIN deve conter exatamente 4 dígitos numéricos.")
    
    try:
        insert_data = {"projeto_id": payload.projeto_id, "pin_acesso": payload.pin_acesso, "ativo": True}
        response = supabase_client.table("orcamento_links").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(status_code=403, detail="Não foi possível criar o link.")
        
        link_data = response.data[0]
        frontend_base = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        return {
            "success": True,
            "data": {
                "id": link_data["id"],
                "token_acesso": link_data["token_acesso"],
                "url_publica": f"{frontend_base}/portal/{link_data['token_acesso']}",
                "pin_acesso": payload.pin_acesso,
                "ativo": True
            }
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Erro ao gerar link de compartilhamento.")

@router.post("/acessar-orcamento")
async def acessar_orcamento_b2c(payload: LinkAcessoRequest):
    """
    Valida o token + PIN do cliente B2C e retorna os dados do projeto.
    Usa service role para ambas as queries — o PIN é validado em Python antes de retornar dados.
    """
    try:
        service_client = get_service_supabase()

        link_res = service_client.table("orcamento_links").select("*").eq("token_acesso", payload.token_acesso).eq("ativo", True).execute()
        if not link_res.data:
            raise HTTPException(status_code=404, detail="Link inválido ou expirado.")

        link = link_res.data[0]
        if link.get("pin_acesso") != payload.pin_acesso:
            raise HTTPException(status_code=403, detail="PIN incorreto.")

        proj_res = service_client.table("projetos_clientes").select("*").eq("id", link["projeto_id"]).single().execute()

        return {
            "success": True,
            "data": {
                "projeto": proj_res.data,
                "link_id": link["id"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO PORTAL /acessar-orcamento] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao acessar o portal do cliente. Tente novamente.")


from datetime import datetime

@router.get("/projetos/{hash_link}/feed")
async def get_portal_feed(hash_link: str):
    """
    Retorna os posts da timeline do canteiro de obras para o link público.
    """
    try:
        service_client = get_service_supabase()
        
        # 1. Valida o token do link
        link_res = service_client.table("orcamento_links").select("projeto_id").eq("token_acesso", hash_link).eq("ativo", True).execute()
        if not link_res.data:
            raise HTTPException(status_code=404, detail="Link do portal inválido ou inativo.")
            
        projeto_id = link_res.data[0]["projeto_id"]
        
        # 2. Busca o feed do canteiro
        feed_res = service_client.table("obras_feed").select("*").eq("projeto_id", projeto_id).order("criado_em", desc=True).execute()
        
        return {
            "success": True,
            "data": feed_res.data or []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar feed da obra: {str(e)}")


@router.get("/projetos/{hash_link}/documentos")
async def get_portal_documentos(hash_link: str):
    """
    Retorna os documentos vinculados ao projeto para visualização do cliente.
    """
    try:
        service_client = get_service_supabase()
        
        # 1. Valida o token do link
        link_res = service_client.table("orcamento_links").select("projeto_id").eq("token_acesso", hash_link).eq("ativo", True).execute()
        if not link_res.data:
            raise HTTPException(status_code=404, detail="Link do portal inválido ou inativo.")
            
        projeto_id = link_res.data[0]["projeto_id"]
        
        # 2. Busca os documentos
        doc_res = service_client.table("projetos_documentos").select("*").eq("projeto_id", projeto_id).order("criado_em", desc=True).execute()
        
        return {
            "success": True,
            "data": doc_res.data or []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar documentos do projeto: {str(e)}")


@router.get("/projetos/{hash_link}/caixa")
async def get_portal_caixa(hash_link: str):
    """
    Calcula e retorna o progresso físico-financeiro (Caixômetro) e estimativa de juros de obra (MCMV).
    """
    try:
        service_client = get_service_supabase()
        
        # 1. Valida o token do link
        link_res = service_client.table("orcamento_links").select("projeto_id").eq("token_acesso", hash_link).eq("ativo", True).execute()
        if not link_res.data:
            raise HTTPException(status_code=404, detail="Link do portal inválido ou inativo.")
            
        projeto_id = link_res.data[0]["projeto_id"]
        
        # 2. Busca os dados do projeto
        proj_res = service_client.table("projetos_clientes").select("valor, status, created_at").eq("id", projeto_id).single().execute()
        if not proj_res.data:
            raise HTTPException(status_code=404, detail="Projeto não encontrado.")
            
        projeto = proj_res.data
        valor_total = float(projeto.get("valor") or 0.0)
        status_projeto = projeto.get("status", "Lead")
        created_at_str = projeto.get("created_at")
        
        # 3. Determina o progresso geral
        progresso_geral = 0.0
        if status_projeto == "Lead":
            progresso_geral = 0.0
        elif status_projeto == "concluido":
            progresso_geral = 100.0
        elif status_projeto == "em_andamento":
            # Simula progresso reativo com base no tempo de criação
            if created_at_str:
                try:
                    # Suporta formatos com ou sem fuso horário
                    clean_date = created_at_str.replace("Z", "+00:00")
                    created_at = datetime.fromisoformat(clean_date)
                    dias_decorridos = (datetime.now(created_at.tzinfo) - created_at).days
                    # 1.5% ao dia, mínimo 15% (já que está em andamento), máximo 90%
                    progresso_geral = min(90.0, max(15.0, float(dias_decorridos) * 1.5))
                except Exception:
                    progresso_geral = 40.0
            else:
                progresso_geral = 40.0
        else: # Ex: aguardando_cliente
            progresso_geral = 15.0
            
        # 4. Distribui o progresso geral entre as 5 etapas da Caixa
        etapas_config = [
            {"chave": "servicos_preliminares", "nome": "1. Serviços Preliminares & Fundações", "peso": 0.15},
            {"chave": "superestrutura", "nome": "2. Superestrutura & Alvenarias", "peso": 0.25},
            {"chave": "cobertura_instalacoes", "nome": "3. Cobertura & Instalações", "peso": 0.20},
            {"chave": "acabamento", "nome": "4. Acabamento & Revestimento", "peso": 0.30},
            {"chave": "pintura_finais", "nome": "5. Pintura & Entregas Finais", "peso": 0.10}
        ]
        
        etapas_calculadas = []
        progresso_restante = progresso_geral / 100.0
        
        for e in etapas_config:
            peso = e["peso"]
            valor_etapa = valor_total * peso
            
            # Calcula o progresso específico desta etapa
            if progresso_restante >= peso:
                progresso_etapa = 100.0
                progresso_restante -= peso
            elif progresso_restante > 0:
                progresso_etapa = (progresso_restante / peso) * 100.0
                progresso_restante = 0.0
            else:
                progresso_etapa = 0.0
                
            valor_medido = valor_etapa * (progresso_etapa / 100.0)
            
            etapas_calculadas.append({
                "nome": e["nome"],
                "peso_percentual": peso * 100.0,
                "progresso": round(progresso_etapa, 1),
                "valor_total": round(valor_etapa, 2),
                "valor_medido": round(valor_medido, 2)
            })
            
        # 5. Calcula os juros de obra
        valor_disbursado = valor_total * (progresso_geral / 100.0)
        valor_a_liberar = valor_total - valor_disbursado
        taxa_anual = 8.0
        taxa_mensal = (taxa_anual / 100.0) / 12.0
        
        juros_mensal_atual = valor_disbursado * taxa_mensal
        
        # Estima os juros acumulados com base no tempo decorrido
        meses_decorridos = 1.0
        if created_at_str:
            try:
                clean_date = created_at_str.replace("Z", "+00:00")
                created_at = datetime.fromisoformat(clean_date)
                dias = (datetime.now(created_at.tzinfo) - created_at).days
                meses_decorridos = max(1.0, float(dias) / 30.0)
            except Exception:
                pass
        
        juros_acumulado_estimado = (valor_disbursado / 2.0) * taxa_mensal * meses_decorridos
        
        return {
            "success": True,
            "data": {
                "progresso_geral": round(progresso_geral, 1),
                "valor_total": round(valor_total, 2),
                "valor_disbursado": round(valor_disbursado, 2),
                "valor_a_liberar": round(valor_a_liberar, 2),
                "taxa_juros_anual": taxa_anual,
                "juros_mensal_atual": round(juros_mensal_atual, 2),
                "juros_acumulado_estimado": round(juros_acumulado_estimado, 2),
                "etapas": etapas_calculadas
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular progresso de caixa: {str(e)}")


def _extrair_pin_do_telefone(telefone: str) -> str:
    apenas_digitos = re.sub(r'\D', '', telefone)
    if len(apenas_digitos) < 4:
        return apenas_digitos.zfill(4)[-4:]
    return apenas_digitos[-4:]


@router.get("/projetos/{projeto_id}/link")
async def obter_ou_criar_link_portal(
    projeto_id: str, 
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """
    Recupera o link do portal do cliente ativo. Se não existir, gera um novo link 
    e PIN usando os 4 últimos dígitos do telefone cadastrado no projeto.
    Requer autenticação do Engenheiro.
    """
    try:
        # 1. Verifica se já existe um link ativo para o projeto
        res = supabase_client.table("orcamento_links").select("*").eq("projeto_id", projeto_id).eq("ativo", True).execute()
        
        if res.data:
            link = res.data[0]
            frontend_base = os.environ.get("FRONTEND_URL", "http://localhost:5173")
            return {
                "success": True,
                "url_publica": f"{frontend_base}/portal/{link['token_acesso']}",
                "pin_acesso": link["pin_acesso"]
            }
            
        # 2. Se não existir, busca o projeto para obter o telefone
        proj_res = supabase_client.table("projetos_clientes").select("telefone").eq("id", projeto_id).single().execute()
        if not proj_res.data:
            raise HTTPException(status_code=404, detail="Projeto não encontrado.")
            
        telefone = proj_res.data.get("telefone") or "0000"
        pin_acesso = _extrair_pin_do_telefone(telefone)
        
        # 3. Insere novo link
        insert_res = supabase_client.table("orcamento_links").insert({
            "projeto_id": projeto_id,
            "pin_acesso": pin_acesso,
            "ativo": True
        }).execute()
        
        if not insert_res.data:
            raise HTTPException(status_code=400, detail="Não foi possível criar o link de acesso ao portal.")
            
        new_link = insert_res.data[0]
        frontend_base = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        return {
            "success": True,
            "url_publica": f"{frontend_base}/portal/{new_link['token_acesso']}",
            "pin_acesso": pin_acesso
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter ou criar link do portal: {str(e)}"
        )


# =========================================================================
# ENDPOINTS AUTENTICADOS — Diário de Obra (obras_feed)
# =========================================================================

class FeedPostRequest(BaseModel):
    projeto_id: str
    descricao: str
    imagens: list[str] = []


@router.get("/feed/{projeto_id}")
async def listar_feed_engenheiro(
    projeto_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Lista os posts do diário de obra de um projeto (autenticado)."""
    try:
        res = supabase_client.table("obras_feed") \
            .select("*") \
            .eq("projeto_id", projeto_id) \
            .order("criado_em", desc=True) \
            .execute()
        return {"success": True, "data": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar feed: {str(e)}")


@router.post("/feed", status_code=201)
async def criar_post_feed(
    payload: FeedPostRequest,
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Cria um novo post no diário de obra (autenticado)."""
    try:
        insert_data = {
            "projeto_id": payload.projeto_id,
            "descricao": payload.descricao,
            "imagens": payload.imagens
        }
        res = supabase_client.table("obras_feed").insert(insert_data).execute()
        if not res.data:
            raise HTTPException(status_code=400, detail="Não foi possível criar o post.")
        return {"success": True, "data": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar post: {str(e)}")


@router.delete("/feed/{post_id}")
async def deletar_post_feed(
    post_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Exclui um post do diário de obra (RLS garante que só o dono deleta)."""
    try:
        res = supabase_client.table("obras_feed").delete().eq("id", post_id).execute()
        return {"success": True, "deleted": len(res.data or [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar post: {str(e)}")


# =========================================================================
# ENDPOINTS AUTENTICADOS — Cofre de Documentos (projetos_documentos)
# =========================================================================

class DocumentoRequest(BaseModel):
    projeto_id: str
    nome_documento: str
    arquivo_url: str
    categoria: str = "Outros"


@router.get("/documentos/{projeto_id}")
async def listar_documentos_engenheiro(
    projeto_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Lista os documentos de um projeto (autenticado)."""
    try:
        res = supabase_client.table("projetos_documentos") \
            .select("*") \
            .eq("projeto_id", projeto_id) \
            .order("criado_em", desc=True) \
            .execute()
        return {"success": True, "data": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {str(e)}")


@router.post("/documentos", status_code=201)
async def criar_documento(
    payload: DocumentoRequest,
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Adiciona um documento ao cofre do projeto (autenticado)."""
    try:
        insert_data = {
            "projeto_id": payload.projeto_id,
            "nome_documento": payload.nome_documento,
            "arquivo_url": payload.arquivo_url,
            "categoria": payload.categoria
        }
        res = supabase_client.table("projetos_documentos").insert(insert_data).execute()
        if not res.data:
            raise HTTPException(status_code=400, detail="Não foi possível adicionar o documento.")
        return {"success": True, "data": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar documento: {str(e)}")


@router.delete("/documentos/item/{doc_id}")
async def deletar_documento(
    doc_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Exclui um documento do cofre (RLS garante que só o dono deleta)."""
    try:
        res = supabase_client.table("projetos_documentos").delete().eq("id", doc_id).execute()
        return {"success": True, "deleted": len(res.data or [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar documento: {str(e)}")
