import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from supabase import Client
from database import supabase
from dependencies import get_authenticated_supabase, get_user_id

router = APIRouter(prefix="/api/vitrine", tags=["Vitrine Pública"])


class VitrineResponse(BaseModel):
    id: str
    nome_completo: str
    registro_crea_cau: Optional[str] = None
    foto_perfil: Optional[str] = None
    slug_vitrine: str
    descricao_vitrine: Optional[str] = None
    fotos_portfolio: Optional[List[str]] = None
    cidades_atuacao: Optional[List[str]] = None


class VitrineConfigRequest(BaseModel):
    slug_vitrine: Optional[str] = None
    descricao_vitrine: Optional[str] = None
    fotos_portfolio: Optional[List[str]] = None
    cidades_atuacao: Optional[List[str]] = None

    @field_validator("slug_vitrine")
    @classmethod
    def validate_slug(cls, v):
        if v is not None and not re.match(r"^[a-z0-9][a-z0-9-]{2,49}$", v):
            raise ValueError("Slug deve ter 3-50 caracteres: letras minúsculas, números e hífens.")
        return v


@router.post("/configurar")
async def configurar_vitrine(
    payload: VitrineConfigRequest,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """Atualiza os dados de portfólio e slug da vitrine pública do engenheiro autenticado."""
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return {"success": True, "message": "Nenhum dado para atualizar."}

    if "slug_vitrine" in update_data and update_data["slug_vitrine"]:
        update_data["slug_vitrine"] = update_data["slug_vitrine"].lower()
        # Garante unicidade do slug excluindo o próprio engenheiro
        conflict = supabase_client.table("perfis_b2b") \
            .select("id") \
            .eq("slug_vitrine", update_data["slug_vitrine"]) \
            .neq("id", user_id) \
            .execute()
        if conflict.data:
            raise HTTPException(status_code=409, detail="Este slug já está em uso. Escolha outro.")

    try:
        res = supabase_client.table("perfis_b2b") \
            .update(update_data) \
            .eq("id", user_id) \
            .execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Perfil não encontrado.")

        return {"success": True, "data": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao configurar vitrine: {str(e)}")


@router.get("/{slug}", response_model=VitrineResponse)
async def get_vitrine_publica(slug: str):
    """Endpoint público. Retorna os dados da vitrine de um engenheiro pelo slug."""
    try:
        res = supabase.table("perfis_b2b") \
            .select("id, nome_completo, registro_crea_cau, foto_perfil, slug_vitrine, descricao_vitrine, fotos_portfolio, cidades_atuacao") \
            .eq("slug_vitrine", slug.lower()) \
            .execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Vitrine não encontrada.")

        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar vitrine: {str(e)}")
