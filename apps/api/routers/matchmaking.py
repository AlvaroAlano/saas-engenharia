import os
import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from database import supabase
from supabase import create_client, Client

router = APIRouter(prefix="/api/matchmaking", tags=["Matchmaking"])


class SolicitarMatchmakingRequest(BaseModel):
    usuario_id: str
    cliente_nome: str
    telefone: str
    valor: float
    padrao: str
    tamanho: str
    uf_obra: str


def get_service_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not service_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_SERVICE_ROLE_KEY não configurada no backend."
        )
    return create_client(url, service_key)



class EngenheiroMatchResponse(BaseModel):
    id: str
    usuario_id: str
    ufs_atuacao: List[str]
    especialidades: List[str]
    raio_km: int
    ativo: bool
    nome_completo: str
    registro_crea_cau: Optional[str] = None
    foto_perfil: Optional[str] = None


@router.get("", response_model=List[EngenheiroMatchResponse])
async def get_matchmaking(
    uf: str = Query(..., min_length=2, max_length=2, description="Sigla da UF (ex: SC)"),
    padrao: Optional[str] = Query(None, description="Padrão de acabamento (ex: popular, alto, etc.)")
):
    """
    Endpoint público para matchmaking. Busca engenheiros disponíveis na UF informada,
    trazendo dados cadastrais como nome, registro profissional (CREA/CAU) e foto de perfil.
    """
    try:
        uf_upper = uf.upper().strip()

        # Realiza query no Supabase com join aninhado na tabela perfis_b2b
        res = (
            supabase.table("engenheiros_disponiveis")
            .select("*, perfis_b2b(*)")
            .eq("ativo", True)
            .contains("ufs_atuacao", [uf_upper])
            .execute()
        )

        if not res.data:
            return []

        resultado = []
        for item in res.data:
            perfil = item.get("perfis_b2b")
            if not perfil:
                # Ignora caso não tenha perfil correspondente (ex: integridade)
                continue

            resultado.append(
                EngenheiroMatchResponse(
                    id=str(item["id"]),
                    usuario_id=str(item["usuario_id"]),
                    ufs_atuacao=item["ufs_atuacao"],
                    especialidades=item["especialidades"],
                    raio_km=int(item["raio_km"]),
                    ativo=bool(item["ativo"]),
                    nome_completo=perfil.get("nome_completo", ""),
                    registro_crea_cau=perfil.get("registro_crea_cau"),
                    foto_perfil=perfil.get("foto_perfil"),
                )
            )

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao realizar matchmaking: {str(e)}",
        )


def _extrair_pin_do_telefone(telefone: str) -> str:
    """Extrai os 4 últimos dígitos numéricos do telefone para usar como PIN."""
    apenas_digitos = re.sub(r'\D', '', telefone)
    if len(apenas_digitos) < 4:
        # Fallback: preenche com zeros à esquerda
        return apenas_digitos.zfill(4)[-4:]
    return apenas_digitos[-4:]


@router.post("/solicitar")
async def solicitar_matchmaking(payload: SolicitarMatchmakingRequest):
    """
    Cria de forma segura um novo projeto na base do engenheiro com status de 'Lead'.
    Gera automaticamente um link de acesso ao Portal do Cliente com PIN baseado
    nos 4 últimos dígitos do telefone informado.
    Utiliza service_role bypass RLS.
    """
    try:
        service_client = get_service_supabase()
        
        # 1. Cria o projeto com status Lead
        projeto_data = {
            "usuario_id": payload.usuario_id,
            "cliente_nome": payload.cliente_nome,
            "telefone": payload.telefone,
            "titulo_projeto": f"Lead - {payload.cliente_nome}",
            "valor": payload.valor,
            "padrao": payload.padrao,
            "tamanho": payload.tamanho,
            "uf_obra": payload.uf_obra.upper().strip(),
            "coluna": "estimativa_enviada",
            "status": "Lead",
            "bdi_padrao": 25.00
        }
        
        res_projeto = service_client.table("projetos_clientes").insert(projeto_data).execute()
        if not res_projeto.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível criar o lead do projeto."
            )
            
        projeto_criado = res_projeto.data[0]
        projeto_id = projeto_criado["id"]
        
        # 2. Gera automaticamente o link do Portal com PIN (últimos 4 dígitos do telefone)
        pin_acesso = _extrair_pin_do_telefone(payload.telefone)
        link_data = {
            "projeto_id": projeto_id,
            "pin_acesso": pin_acesso,
            "ativo": True
        }
        res_link = service_client.table("orcamento_links").insert(link_data).execute()
        
        url_publica = None
        token_acesso = None
        if res_link.data:
            token_acesso = res_link.data[0]["token_acesso"]
            frontend_base = os.environ.get("FRONTEND_URL", "http://localhost:5173")
            url_publica = f"{frontend_base}/portal/{token_acesso}"
        
        # 3. Cria a notificação/histórico inicial
        historico_data = {
            "projeto_id": projeto_id,
            "acao": "Matchmaking B2C",
            "detalhes": f"Lead criado via matchmaking. Cliente: {payload.cliente_nome}. Telefone: {payload.telefone}. Portal gerado automaticamente."
        }
        service_client.table("projetos_historico").insert(historico_data).execute()
        
        return {
            "success": True,
            "projeto_id": projeto_id,
            "url_publica": url_publica,
            "pin_acesso": pin_acesso,
            "message": "Solicitação de orçamento enviada com sucesso!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar solicitação de lead: {str(e)}"
        )


class PublicProjetoResponse(BaseModel):
    id: str
    cliente_nome: str
    status: Optional[str] = None
    coluna: Optional[str] = None
    valor: Optional[float] = None
    padrao: Optional[str] = None
    tamanho: Optional[str] = None
    telefone: Optional[str] = None
    documentos: Optional[List[dict]] = None


class PublicProjetoUpdate(BaseModel):
    valor: Optional[float] = None
    padrao: Optional[str] = None
    tamanho: Optional[str] = None
    coluna: Optional[str] = None
    status: Optional[str] = None
    documentos: Optional[List[dict]] = None


@router.get("/projetos/{id}", response_model=PublicProjetoResponse)
async def get_projeto_publico(id: str):
    """
    Busca de forma pública (sem JWT de engenheiro) dados básicos do projeto usando service role.
    Utilizado na jornada B2C (Sala de Espera e Validação de Documentos).
    """
    try:
        service_client = get_service_supabase()
        res = service_client.table("projetos_clientes").select("id, cliente_nome, status, coluna, valor, padrao, tamanho, telefone, documentos").eq("id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Projeto não encontrado.")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar projeto público: {str(e)}"
        )


@router.patch("/projetos/{id}")
async def update_projeto_publico(id: str, payload: PublicProjetoUpdate):
    """
    Atualiza de forma pública (sem JWT de engenheiro) status ou documentos do projeto.
    Utilizado na aprovação de estimativa e upload de documentos pelo cliente.
    """
    try:
        service_client = get_service_supabase()
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return {"success": True, "message": "Nenhum dado para atualizar."}

        if update_data.get("status") == "docs_completos":
            update_data["coluna"] = "contrato_pendente"

        res = service_client.table("projetos_clientes").update(update_data).eq("id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Projeto não encontrado.")
            
        # Registra no histórico do projeto
        historico_msg = f"Atualizado via Portal Público B2C: {', '.join([f'{k}={v}' for k, v in update_data.items() if k != 'documentos'])}"
        if "documentos" in update_data:
            historico_msg += f" (Enviados {len(update_data['documentos'])} documentos)"
            
        service_client.table("projetos_historico").insert({
            "projeto_id": id,
            "acao": "Portal Público B2C",
            "detalhes": historico_msg
        }).execute()
        
        return {"success": True, "data": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar projeto público: {str(e)}"
        )


