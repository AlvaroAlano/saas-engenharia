import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel, Field
from supabase import Client
from dependencies import get_authenticated_supabase, get_user_id

router = APIRouter(prefix="/api/configuracoes", tags=["Configurações"])

_PADROES_ORDEM = ["popular", "medio", "alto"]


# ==========================================================================
# MODELS
# ==========================================================================

class TemplateItemPayload(BaseModel):
    codigo_sinapi: str
    fase_obra: str
    fator_area_multiplicador: float = Field(..., gt=0)


class CreateTemplatePayload(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    padrao_obra: str = Field(..., pattern="^(popular|medio|alto)$")
    base_template_id: Optional[str] = None  # Se informado, copia itens deste template


class UpdateTemplatePayload(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    padrao_obra: Optional[str] = Field(None, pattern="^(popular|medio|alto)$")
    itens: Optional[List[TemplateItemPayload]] = None


# ==========================================================================
# HELPERS
# ==========================================================================

def _enriquecer_com_sinapi(templates: list, supabase_client: Client) -> list:
    """Enriquece os itens de cada template com descrição e unidade do SINAPI."""
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


def _compute_active_per_padrao(sistema: list, customizado: list) -> dict:
    """Retorna {padrao_obra: template_id} com o template ativo por padrão de obra."""
    active: dict = {}
    for t in customizado:
        if t.get("is_default") and t["padrao_obra"] not in active:
            active[t["padrao_obra"]] = t["id"]
    for t in sistema:
        if t["padrao_obra"] not in active:
            active[t["padrao_obra"]] = t["id"]
    return active


def _annotate_templates(templates: list, active_per_padrao: dict) -> list:
    for t in templates:
        t["is_active"] = active_per_padrao.get(t["padrao_obra"]) == t["id"]
        t["total_itens"] = len(t.get("template_eap_itens", []))
    return templates


# ==========================================================================
# ENDPOINTS — TEMPLATES EAP
# ==========================================================================

@router.get("/templates")
async def get_templates(
    padrao_obra: Optional[str] = Query(None),
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Retorna todos os templates: SISTEMA (3 fixos) + todos os CUSTOMIZADO do usuário.
    Aceita filtro opcional por padrao_obra para o seletor no Orçamento.
    """
    sistema_res = (
        supabase_client.table("templates_eap")
        .select("*, template_eap_itens(*)")
        .eq("tipo", "SISTEMA")
        .execute()
    )

    custom_query = (
        supabase_client.table("templates_eap")
        .select("*, template_eap_itens(*)")
        .eq("tipo", "CUSTOMIZADO")
        .eq("usuario_id", user_id)
    )
    if padrao_obra:
        custom_query = custom_query.eq("padrao_obra", padrao_obra)
    custom_res = custom_query.execute()

    sistema = sorted(
        sistema_res.data or [],
        key=lambda t: _PADROES_ORDEM.index(t["padrao_obra"])
    )
    customizado = custom_res.data or []

    all_templates = sistema + customizado
    all_templates = _enriquecer_com_sinapi(all_templates, supabase_client)

    active_per_padrao = _compute_active_per_padrao(sistema, customizado)
    _annotate_templates(all_templates, active_per_padrao)

    return {
        "success": True,
        "sistema": [t for t in all_templates if t["tipo"] == "SISTEMA"],
        "customizado": [t for t in all_templates if t["tipo"] == "CUSTOMIZADO"],
        "active_per_padrao": active_per_padrao,
    }


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: CreateTemplatePayload,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Cria um novo template CUSTOMIZADO.
    Se base_template_id for informado, copia os itens deste template (pode ser SISTEMA ou CUSTOMIZADO do usuário).
    O primeiro CUSTOMIZADO criado para um padrão vira is_default automaticamente.
    """
    existing_res = (
        supabase_client.table("templates_eap")
        .select("id")
        .eq("tipo", "CUSTOMIZADO")
        .eq("usuario_id", user_id)
        .eq("padrao_obra", payload.padrao_obra)
        .execute()
    )
    is_first = len(existing_res.data or []) == 0

    new_res = (
        supabase_client.table("templates_eap")
        .insert({
            "nome": payload.nome,
            "tipo": "CUSTOMIZADO",
            "padrao_obra": payload.padrao_obra,
            "usuario_id": user_id,
            "is_default": is_first,
        })
        .execute()
    )
    if not new_res.data:
        raise HTTPException(status_code=500, detail="Falha ao criar o template.")

    template_id = new_res.data[0]["id"]

    if payload.base_template_id:
        base_res = (
            supabase_client.table("template_eap_itens")
            .select("codigo_sinapi, fase_obra, fator_area_multiplicador")
            .eq("template_id", payload.base_template_id)
            .execute()
        )
        if base_res.data:
            supabase_client.table("template_eap_itens").insert([
                {
                    "template_id": template_id,
                    "codigo_sinapi": item["codigo_sinapi"],
                    "fase_obra": item["fase_obra"],
                    "fator_area_multiplicador": item["fator_area_multiplicador"],
                }
                for item in base_res.data
            ]).execute()

    final_res = (
        supabase_client.table("templates_eap")
        .select("*, template_eap_itens(*)")
        .eq("id", template_id)
        .execute()
    )
    data = _enriquecer_com_sinapi(final_res.data or [], supabase_client)
    result = data[0] if data else {}
    result["total_itens"] = len(result.get("template_eap_itens", []))
    result["is_active"] = is_first

    return {"success": True, "data": result, "auto_set_default": is_first}


@router.put("/templates/{template_id}", status_code=status.HTTP_200_OK)
async def update_template(
    template_id: str,
    payload: UpdateTemplatePayload,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """Atualiza nome, padrao_obra e/ou itens de um template CUSTOMIZADO do usuário."""
    template_res = (
        supabase_client.table("templates_eap")
        .select("*")
        .eq("id", template_id)
        .eq("tipo", "CUSTOMIZADO")
        .eq("usuario_id", user_id)
        .execute()
    )
    if not template_res.data:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    current = template_res.data[0]
    updates: dict = {}

    if payload.nome is not None:
        updates["nome"] = payload.nome

    old_padrao = current["padrao_obra"]
    changing_padrao = payload.padrao_obra is not None and payload.padrao_obra != old_padrao

    if changing_padrao:
        updates["padrao_obra"] = payload.padrao_obra
        # Se era default do padrão antigo, perde o status ao mudar de padrão
        if current.get("is_default"):
            updates["is_default"] = False

    if updates:
        supabase_client.table("templates_eap").update(updates).eq("id", template_id).execute()

    # Se mudou de padrão e era default, promove o próximo CUSTOMIZADO do padrão antigo
    if changing_padrao and current.get("is_default"):
        remaining = (
            supabase_client.table("templates_eap")
            .select("id")
            .eq("tipo", "CUSTOMIZADO")
            .eq("usuario_id", user_id)
            .eq("padrao_obra", old_padrao)
            .order("criado_em", desc=False)
            .limit(1)
            .execute()
        )
        if remaining.data:
            supabase_client.table("templates_eap").update({"is_default": True}).eq("id", remaining.data[0]["id"]).execute()

    if payload.itens is not None:
        supabase_client.table("template_eap_itens").delete().eq("template_id", template_id).execute()
        if payload.itens:
            supabase_client.table("template_eap_itens").insert([
                {
                    "template_id": template_id,
                    "codigo_sinapi": item.codigo_sinapi,
                    "fase_obra": item.fase_obra,
                    "fator_area_multiplicador": item.fator_area_multiplicador,
                }
                for item in payload.itens
            ]).execute()

    final_res = (
        supabase_client.table("templates_eap")
        .select("*, template_eap_itens(*)")
        .eq("id", template_id)
        .execute()
    )
    data = _enriquecer_com_sinapi(final_res.data or [], supabase_client)
    result = data[0] if data else {}
    result["total_itens"] = len(result.get("template_eap_itens", []))

    return {"success": True, "data": result}


@router.post("/templates/{template_id}/set-default", status_code=status.HTTP_200_OK)
async def set_template_default(
    template_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Define qual template é o ativo para o padrão de obra.

    - Template CUSTOMIZADO do usuário → marca is_default=true nele e false nos demais.
    - Template SISTEMA → remove is_default de todos os CUSTOMIZADO daquele padrão,
      fazendo o sistema voltar a usar o SISTEMA como ativo (fallback natural).
    """
    template_res = (
        supabase_client.table("templates_eap")
        .select("id, tipo, usuario_id, padrao_obra, is_default")
        .eq("id", template_id)
        .execute()
    )
    if not template_res.data:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    template = template_res.data[0]

    # ── Caso SISTEMA: limpa is_default de todos os CUSTOMIZADO do padrão ──
    if template["tipo"] == "SISTEMA":
        (
            supabase_client.table("templates_eap")
            .update({"is_default": False})
            .eq("tipo", "CUSTOMIZADO")
            .eq("usuario_id", user_id)
            .eq("padrao_obra", template["padrao_obra"])
            .execute()
        )
        return {"success": True, "message": "Template do sistema definido como ativo."}

    # ── Caso CUSTOMIZADO: valida ownership ──
    if template["usuario_id"] != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if template.get("is_default"):
        return {"success": True, "message": "Este template já é o padrão ativo."}

    # Zera is_default de todos os CUSTOMIZADO do mesmo padrao_obra
    (
        supabase_client.table("templates_eap")
        .update({"is_default": False})
        .eq("tipo", "CUSTOMIZADO")
        .eq("usuario_id", user_id)
        .eq("padrao_obra", template["padrao_obra"])
        .execute()
    )
    # Define este como default
    (
        supabase_client.table("templates_eap")
        .update({"is_default": True})
        .eq("id", template_id)
        .execute()
    )

    return {"success": True, "message": "Template definido como padrão ativo."}


@router.delete("/templates/{template_id}", status_code=status.HTTP_200_OK)
async def delete_template(
    template_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Remove um template CUSTOMIZADO.
    Se era o is_default, promove automaticamente o próximo CUSTOMIZADO disponível.
    """
    template_res = (
        supabase_client.table("templates_eap")
        .select("id, padrao_obra, is_default")
        .eq("id", template_id)
        .eq("tipo", "CUSTOMIZADO")
        .eq("usuario_id", user_id)
        .execute()
    )
    if not template_res.data:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    template = template_res.data[0]
    was_default = template.get("is_default", False)
    padrao_obra = template["padrao_obra"]

    # CASCADE deleta template_eap_itens via FK
    supabase_client.table("templates_eap").delete().eq("id", template_id).execute()

    promoted_id = None
    if was_default:
        remaining_res = (
            supabase_client.table("templates_eap")
            .select("id")
            .eq("tipo", "CUSTOMIZADO")
            .eq("usuario_id", user_id)
            .eq("padrao_obra", padrao_obra)
            .order("criado_em", desc=False)
            .limit(1)
            .execute()
        )
        if remaining_res.data:
            promoted_id = remaining_res.data[0]["id"]
            supabase_client.table("templates_eap").update({"is_default": True}).eq("id", promoted_id).execute()

    return {
        "success": True,
        "was_default": was_default,
        "promoted_id": promoted_id,
        "fallback_to_sistema": was_default and promoted_id is None,
    }


# ==========================================================================
# ENDPOINT — SINAPI SEARCH (para adicionar itens ao template)
# ==========================================================================

@router.get("/sinapi-search")
async def search_sinapi_for_template(
    q: str = Query(..., min_length=2),
    supabase_client: Client = Depends(get_authenticated_supabase),
    _: str = Depends(get_user_id),
):
    """
    Busca itens SINAPI por código ou descrição para uso nos templates EAP.
    Retorna código, descrição e unidade — sem vínculo a preço/estado.
    """
    q_str = q.strip()
    q_clean = q_str.lstrip("0") if q_str.isdigit() else q_str
    if not q_clean:
        q_clean = "0"

    res = (
        supabase_client.table("sinapi_itens")
        .select("codigo_item, descricao, unidade")
        .or_(f"descricao.ilike.%{q_str}%,codigo_item.ilike.%{q_str}%,codigo_item.ilike.%{q_clean}%")
        .limit(50)
        .execute()
    )

    seen: set = set()
    unique_items = []
    for row in res.data or []:
        code = row["codigo_item"]
        if code not in seen:
            seen.add(code)
            unique_items.append({
                "codigo_item": code,
                "descricao": row["descricao"],
                "unidade": row["unidade"],
            })
        if len(unique_items) >= 10:
            break

    return {"success": True, "data": unique_items}


# ==========================================================================
# ENDPOINTS — FASES DE OBRA
# ==========================================================================

_ICONS_VALIDOS = {
    "engineering", "foundation", "domain", "electric_bolt", "format_paint",
    "wrench", "home", "package", "settings", "grid",
}
_CORES_VALIDAS = {
    "amber", "orange", "blue", "violet", "emerald",
    "red", "slate", "cyan", "indigo", "green", "yellow", "pink",
}


def _slugify(text: str) -> str:
    text = text.lower().strip()
    for src, dst in [('à','a'),('á','a'),('â','a'),('ã','a'),('ä','a'),
                     ('è','e'),('é','e'),('ê','e'),('ë','e'),
                     ('ì','i'),('í','i'),('î','i'),('ï','i'),
                     ('ò','o'),('ó','o'),('ô','o'),('õ','o'),('ö','o'),
                     ('ù','u'),('ú','u'),('û','u'),('ü','u'),('ç','c')]:
        text = text.replace(src, dst)
    text = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    return text or "fase"


class CreateFasePayload(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    icon:  str = Field("engineering")
    color: str = Field("blue")


class UpdateFasePayload(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=80)
    icon:  Optional[str] = None
    color: Optional[str] = None
    ordem: Optional[int] = None


class FasesOrdemPayload(BaseModel):
    valores: List[str] = Field(..., description="Array de slugs (value) na ordem desejada")


@router.get("/fases")
async def get_fases(
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Retorna todas as fases de obra ordenadas.
    Se o usuário tiver uma ordem personalizada (tabela fases_obra_user_ordem),
    ela é aplicada; caso contrário usa a ordem padrão (campo ordem das tabelas).
    """
    sistema_res = (
        supabase_client.table("fases_obra")
        .select("*")
        .eq("tipo", "SISTEMA")
        .order("ordem")
        .execute()
    )
    custom_res = (
        supabase_client.table("fases_obra")
        .select("*")
        .eq("tipo", "CUSTOMIZADO")
        .eq("usuario_id", user_id)
        .order("ordem")
        .execute()
    )

    all_fases = (sistema_res.data or []) + (custom_res.data or [])

    # Aplica ordem personalizada do usuário, se existir
    try:
        ordem_res = (
            supabase_client.table("fases_obra_user_ordem")
            .select("valores_ordem")
            .eq("usuario_id", user_id)
            .execute()
        )
        if ordem_res.data and ordem_res.data[0].get("valores_ordem"):
            user_order = ordem_res.data[0]["valores_ordem"]
            ordem_map = {v: i for i, v in enumerate(user_order)}
            # Fases com slug na preferência do usuário → usa o índice salvo
            # Fases novas (ainda não na preferência) → ficam no final
            all_fases.sort(key=lambda f: ordem_map.get(f["value"], 9999))
        else:
            all_fases.sort(key=lambda f: f.get("ordem", 99))
    except Exception:
        all_fases.sort(key=lambda f: f.get("ordem", 99))

    return {"success": True, "data": all_fases}


@router.put("/fases/ordem", status_code=status.HTTP_200_OK)
async def save_fases_ordem(
    payload: FasesOrdemPayload,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """Salva a ordem personalizada das fases para o usuário (upsert)."""
    supabase_client.table("fases_obra_user_ordem").upsert({
        "usuario_id":    user_id,
        "valores_ordem": payload.valores,
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return {"success": True}


@router.post("/fases", status_code=status.HTTP_201_CREATED)
async def create_fase(
    payload: CreateFasePayload,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """Cria uma fase customizada. O slug (value) é gerado automaticamente a partir do label."""
    if payload.icon not in _ICONS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Ícone inválido. Opções: {sorted(_ICONS_VALIDOS)}")
    if payload.color not in _CORES_VALIDAS:
        raise HTTPException(status_code=400, detail=f"Cor inválida. Opções: {sorted(_CORES_VALIDAS)}")

    base_slug = _slugify(payload.label)
    slug = base_slug

    # Garante unicidade do slug para este usuário
    attempt = 0
    while True:
        existing = (
            supabase_client.table("fases_obra")
            .select("id")
            .eq("tipo", "CUSTOMIZADO")
            .eq("usuario_id", user_id)
            .eq("value", slug)
            .execute()
        )
        if not existing.data:
            break
        attempt += 1
        slug = f"{base_slug}_{attempt}"

    # Ordem: próxima após o maior valor existente
    max_ordem_res = (
        supabase_client.table("fases_obra")
        .select("ordem")
        .or_(f"tipo.eq.SISTEMA,and(tipo.eq.CUSTOMIZADO,usuario_id.eq.{user_id})")
        .order("ordem", desc=True)
        .limit(1)
        .execute()
    )
    next_ordem = (max_ordem_res.data[0]["ordem"] + 1) if max_ordem_res.data else 10

    res = (
        supabase_client.table("fases_obra")
        .insert({
            "usuario_id": user_id,
            "value":      slug,
            "label":      payload.label,
            "icon":       payload.icon,
            "color":      payload.color,
            "ordem":      next_ordem,
            "tipo":       "CUSTOMIZADO",
        })
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=500, detail="Falha ao criar fase.")
    return {"success": True, "data": res.data[0]}


@router.put("/fases/{fase_id}", status_code=status.HTTP_200_OK)
async def update_fase(
    fase_id: str,
    payload: UpdateFasePayload,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Atualiza label, icon, color e/ou ordem de uma fase.
    Fases SISTEMA: apenas label/icon/color/ordem são editáveis (sem excluir).
    Fases CUSTOMIZADO: somente do próprio usuário.
    """
    fase_res = (
        supabase_client.table("fases_obra")
        .select("*")
        .eq("id", fase_id)
        .execute()
    )
    if not fase_res.data:
        raise HTTPException(status_code=404, detail="Fase não encontrada.")

    fase = fase_res.data[0]
    if fase["tipo"] == "CUSTOMIZADO" and fase["usuario_id"] != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if payload.icon and payload.icon not in _ICONS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Ícone inválido. Opções: {sorted(_ICONS_VALIDOS)}")
    if payload.color and payload.color not in _CORES_VALIDAS:
        raise HTTPException(status_code=400, detail=f"Cor inválida. Opções: {sorted(_CORES_VALIDAS)}")

    updates: dict = {}
    if payload.label is not None: updates["label"] = payload.label
    if payload.icon  is not None: updates["icon"]  = payload.icon
    if payload.color is not None: updates["color"] = payload.color
    if payload.ordem is not None: updates["ordem"] = payload.ordem

    if not updates:
        return {"success": True, "data": fase}

    res = supabase_client.table("fases_obra").update(updates).eq("id", fase_id).execute()
    return {"success": True, "data": res.data[0] if res.data else fase}


@router.delete("/fases/{fase_id}", status_code=status.HTTP_200_OK)
async def delete_fase(
    fase_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Remove uma fase CUSTOMIZADO do usuário.
    Bloqueia se houver itens de template ou orçamento referenciando o slug da fase.
    """
    fase_res = (
        supabase_client.table("fases_obra")
        .select("id, tipo, usuario_id, value")
        .eq("id", fase_id)
        .execute()
    )
    if not fase_res.data:
        raise HTTPException(status_code=404, detail="Fase não encontrada.")

    fase = fase_res.data[0]
    if fase["tipo"] == "SISTEMA":
        raise HTTPException(status_code=400, detail="Fases do sistema não podem ser excluídas.")
    if fase["usuario_id"] != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    slug = fase["value"]

    # Verifica referências em template_eap_itens
    refs_tpl = (
        supabase_client.table("template_eap_itens")
        .select("id")
        .eq("fase_obra", slug)
        .limit(1)
        .execute()
    )
    if refs_tpl.data:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir: existem itens de template vinculados à fase '{slug}'."
        )

    # Verifica referências em orcamento_itens
    refs_orc = (
        supabase_client.table("orcamento_itens")
        .select("id")
        .eq("etapa_obra", slug)
        .limit(1)
        .execute()
    )
    if refs_orc.data:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir: existem itens de orçamento vinculados à fase '{slug}'."
        )

    supabase_client.table("fases_obra").delete().eq("id", fase_id).execute()
    return {"success": True}
