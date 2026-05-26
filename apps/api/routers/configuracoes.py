from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel, Field
from supabase import Client
from dependencies import get_authenticated_supabase, get_user_id

_PADRAO_NORMALIZADO = {
    "popular": "popular", "Popular": "popular",
    "medio": "medio", "Médio Padrão": "medio", "Medio Padrao": "medio", "Médio": "medio",
    "alto": "alto", "Alto Padrão": "alto", "Alto Padrao": "alto", "Alto": "alto",
}

router = APIRouter(prefix="/api/configuracoes", tags=["Configurações"])


# ==========================================================================
# MODELS
# ==========================================================================

class TemplateItemPayload(BaseModel):
    codigo_sinapi: str
    fase_obra: str
    fator_area_multiplicador: float = Field(..., gt=0)


class TemplateSavePayload(BaseModel):
    padrao_obra: str = Field(..., pattern="^(popular|medio|alto)$")
    nome: str
    itens: List[TemplateItemPayload]


# ==========================================================================
# ENDPOINTS — TEMPLATES EAP (Configurações)
# ==========================================================================

def _enriquecer_com_sinapi(templates: list, supabase_client: Client) -> list:
    """
    Enriquece os itens de cada template com descricao e unidade ao vivo da
    tabela sinapi_itens. Usado apenas para exibição na tela de Configurações.
    """
    all_codes = list({
        item["codigo_sinapi"]
        for t in templates
        for item in t.get("template_eap_itens", [])
    })
    if not all_codes:
        return templates

    sinapi_res = (
        supabase_client.table("sinapi_itens")
        .select("codigo_item, descricao, unidade")
        .in_("codigo_item", all_codes)
        .execute()
    )
    # Deduplica por código — qualquer ocorrência serve para exibição
    sinapi_map: dict = {}
    for row in sinapi_res.data or []:
        if row["codigo_item"] not in sinapi_map:
            sinapi_map[row["codigo_item"]] = {
                "descricao": row["descricao"],
                "unidade": row["unidade"],
            }

    for template in templates:
        for item in template.get("template_eap_itens", []):
            info = sinapi_map.get(item["codigo_sinapi"], {})
            item["descricao"] = info.get("descricao") or f"[{item['codigo_sinapi']}]"
            item["unidade"] = info.get("unidade") or ""

    return templates


@router.get("/templates")
async def get_templates(
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Retorna os templates EAP do usuário, enriquecidos com descrição/unidade do SINAPI.
    Tenta CUSTOMIZADO primeiro; fallback para SISTEMA se a conta não tiver nenhum.
    """
    custom_res = (
        supabase_client.table("templates_eap")
        .select("*, template_eap_itens(*)")
        .eq("tipo", "CUSTOMIZADO")
        .eq("usuario_id", user_id)
        .execute()
    )

    if custom_res.data:
        data = _enriquecer_com_sinapi(custom_res.data, supabase_client)
        return {"success": True, "source": "customizado", "data": data}

    sistema_res = (
        supabase_client.table("templates_eap")
        .select("*, template_eap_itens(*)")
        .eq("tipo", "SISTEMA")
        .execute()
    )

    data = _enriquecer_com_sinapi(sistema_res.data or [], supabase_client)
    return {"success": True, "source": "sistema", "data": data}


@router.post("/templates", status_code=status.HTTP_200_OK)
async def save_template(
    payload: TemplateSavePayload,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Fork seguro: nunca sobrescreve o template SISTEMA.
    Cria (ou atualiza) a versão CUSTOMIZADO do usuário para o padrão de obra informado.
    """
    existing_res = (
        supabase_client.table("templates_eap")
        .select("id")
        .eq("tipo", "CUSTOMIZADO")
        .eq("usuario_id", user_id)
        .eq("padrao_obra", payload.padrao_obra)
        .execute()
    )

    if existing_res.data:
        template_id = existing_res.data[0]["id"]
        supabase_client.table("template_eap_itens").delete().eq("template_id", template_id).execute()
    else:
        new_template_res = (
            supabase_client.table("templates_eap")
            .insert({
                "nome": payload.nome,
                "tipo": "CUSTOMIZADO",
                "padrao_obra": payload.padrao_obra,
                "usuario_id": user_id,
            })
            .execute()
        )
        if not new_template_res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao criar o template customizado.",
            )
        template_id = new_template_res.data[0]["id"]

    itens_to_insert = [
        {
            "template_id": template_id,
            "codigo_sinapi": item.codigo_sinapi,
            "fase_obra": item.fase_obra,
            "fator_area_multiplicador": item.fator_area_multiplicador,
        }
        for item in payload.itens
    ]

    supabase_client.table("template_eap_itens").insert(itens_to_insert).execute()

    template_final = (
        supabase_client.table("templates_eap")
        .select("*, template_eap_itens(*)")
        .eq("id", template_id)
        .execute()
    )

    data = _enriquecer_com_sinapi(template_final.data or [], supabase_client)
    return {"success": True, "data": data[0] if data else {}}


@router.delete("/templates/{padrao_obra}", status_code=status.HTTP_200_OK)
async def reset_template(
    padrao_obra: str,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Remove o template CUSTOMIZADO do usuário para um padrão de obra,
    fazendo o sistema voltar a usar o template SISTEMA como fallback.
    """
    if padrao_obra not in ("popular", "medio", "alto"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Padrão de obra inválido.")

    supabase_client.table("templates_eap").delete().eq("tipo", "CUSTOMIZADO").eq("usuario_id", user_id).eq("padrao_obra", padrao_obra).execute()

    return {"success": True, "message": f"Template '{padrao_obra}' restaurado para o padrão do sistema."}
