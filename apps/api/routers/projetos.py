from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from supabase import Client
from dependencies import get_authenticated_supabase, get_user_id

router = APIRouter(tags=["Projetos e Orçamentos Unificados"])

# =========================================================================
# --- DOMÍNIO UNIFICADO: MODELS PYDANTIC ---
# =========================================================================

class ProjetoCreate(BaseModel):
    cliente_nome: str = Field(..., min_length=1, description="Nome completo do cliente ou empresa")
    titulo_projeto: Optional[str] = Field(None, description="Título da obra ou orçamento")
    telefone: str = Field(..., description="Telefone de contato para magic link e validação")
    observacoes: Optional[str] = None

class ProjetoUpdate(BaseModel):
    cliente_nome: Optional[str] = None
    titulo_projeto: Optional[str] = None
    coluna: Optional[str] = None
    valor: Optional[float] = None
    padrao: Optional[str] = None
    tamanho: Optional[str] = None
    status: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None
    documentos: Optional[List[Dict[str, Any]]] = None
    uf_obra: Optional[str] = None
    sinapi_mes_ano: Optional[str] = None
    sinapi_desonerado: Optional[bool] = None
    bdi_padrao: Optional[float] = None

class ProjetoResponse(BaseModel):
    id: str
    usuario_id: Optional[str] = None
    cliente_nome: str
    titulo_projeto: Optional[str] = None
    coluna: Optional[str] = "estimativa_enviada"
    valor: Optional[float] = None
    padrao: Optional[str] = None
    tamanho: Optional[str] = None
    status: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None
    documentos: Optional[List[Dict[str, Any]]] = None
    uf_obra: Optional[str] = None
    sinapi_mes_ano: Optional[str] = None
    sinapi_desonerado: Optional[bool] = False
    bdi_padrao: Optional[float] = None
    contrato_gerado: Optional[bool] = False
    zapsign_document_token: Optional[str] = None
    url_assinatura_cliente: Optional[str] = None
    url_assinatura_engenheiro: Optional[str] = None
    status_assinatura: Optional[str] = 'nao_enviado'
    engenheiro_assinou: Optional[bool] = False
    cliente_assinou: Optional[bool] = False
    created_at: Optional[str] = None

class NovoItemProjeto(BaseModel):
    codigo_sinapi: Optional[str] = Field("MANUAL", description="Código SINAPI ou identificador de item manual")
    descricao: str = Field(..., min_length=1, description="Descrição do serviço ou insumo")
    unidade: str = Field(..., min_length=1, description="Unidade de medida (M², M³, UN, etc.)")
    valor_unitario: float = Field(..., gt=0, description="Custo unitário sem BDI")
    quantidade: float = Field(..., gt=0, description="Quantidade do insumo ou serviço")
    tipo_item: str = Field("insumo", description="Tipo de item: insumo ou composicao")
    etapa_obra: str = Field("servicos_preliminares", description="Etapa da árvore de custos")

class UpdateQuantidadeRequest(BaseModel):
    quantidade: float = Field(..., gt=0, description="Nova quantidade atualizada")

class NotaHistoricoCreate(BaseModel):
    texto: str = Field(..., min_length=1, description="Texto da nota ou observação")


# =========================================================================
# --- ROTAS PRINCIPAIS: PROJETOS (CRM + ENGENHARIA) ---
# =========================================================================

@router.get("/api/dashboard")
async def get_dashboard(supabase_client: Client = Depends(get_authenticated_supabase)):
    """
    Retorna métricas e visões consolidadas de projetos do tenant atual.
    """
    response = supabase_client.table("projetos_clientes").select("*").neq("status", "ARQUIVADO").order("created_at", desc=True).limit(5).execute()
    return response.data

@router.post("/api/projetos", response_model=ProjetoResponse, status_code=status.HTTP_201_CREATED)
async def create_projeto(
    payload: ProjetoCreate, 
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id)
):
    """
    Cria um novo projeto unificado.
    Extraímos o usuario_id localmente a partir do token JWT com latência zero
    para satisfazer a política estrita de RLS (WITH CHECK (auth.uid() = usuario_id)) no Postgres.
    """
    insert_data = payload.model_dump(exclude_unset=True)
    insert_data["usuario_id"] = user_id
    insert_data["coluna"] = "estimativa_enviada"
    insert_data["status"] = "aguardando_cliente"
    
    response = supabase_client.table("projetos_clientes").insert(insert_data).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não foi possível registrar o projeto no banco.")
        
    return response.data[0]

@router.get("/api/projetos", response_model=List[ProjetoResponse])
async def get_projetos(supabase_client: Client = Depends(get_authenticated_supabase)):
    """Listagem limpa de todos os projetos do tenant logado, respeitando estritamente o RLS."""
    response = supabase_client.table("projetos_clientes").select("*").neq("status", "ARQUIVADO").order("created_at", desc=False).execute()
    return response.data

@router.get("/api/projetos/{id}", response_model=ProjetoResponse)
async def get_projeto(id: str, supabase_client: Client = Depends(get_authenticated_supabase)):
    """Busca os detalhes de um projeto específico unificado."""
    response = supabase_client.table("projetos_clientes").select("*").eq("id", id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto ou Orçamento não encontrado.")
    return response.data[0]

@router.patch("/api/projetos/{id}")
async def update_projeto(
    id: str, 
    payload: ProjetoUpdate, 
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Atualiza configurações técnicas, status ou dados comerciais do projeto."""
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return {"success": True, "message": "Nenhum dado fornecido para atualização."}
        
    response = supabase_client.table("projetos_clientes").update(update_data).eq("id", id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    
    projeto_atualizado = response.data[0]
    
    # Gravação do histórico rastreável do projeto
    detalhes = []
    if "coluna" in update_data: detalhes.append(f"Coluna de funil alterada para: {update_data['coluna']}")
    if "status" in update_data: detalhes.append(f"Status técnico alterado para: {update_data['status']}")
    if "bdi_padrao" in update_data: detalhes.append(f"BDI ajustado para: {update_data['bdi_padrao']}%")
    
    if detalhes:
        supabase_client.table("projetos_historico").insert({
            "projeto_id": id,
            "acao": "Atualização Técnica/Comercial",
            "detalhes": "; ".join(detalhes)
        }).execute()

    return {"success": True, "data": projeto_atualizado}


# =========================================================================
# --- ROTAS DE ITENS DO PROJETO (CARRINHO E PLANILHA DE CUSTOS) ---
# =========================================================================

@router.post("/api/projetos/{projeto_id}/itens", status_code=status.HTTP_201_CREATED)
async def add_item_projeto(
    projeto_id: str, 
    payload: NovoItemProjeto, 
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """
    Adiciona um insumo ou composição à árvore de custos do projeto.
    A chave estrangeira padronizada é estritamente `projeto_id`.
    """
    insert_data = {
        "projeto_id": projeto_id,
        "codigo_sinapi": payload.codigo_sinapi,
        "descricao": payload.descricao,
        "unidade": payload.unidade,
        "quantidade": payload.quantidade,
        "valor_unitario": payload.valor_unitario,
        "tipo_item": payload.tipo_item,
        "etapa_obra": payload.etapa_obra
    }
    res = supabase_client.table("orcamento_itens").insert(insert_data).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falha ao inserir item no orçamento.")
    return {"success": True, "data": res.data[0]}

@router.post("/api/projetos/{projeto_id}/itens/bulk", status_code=status.HTTP_201_CREATED)
async def add_items_bulk(
    projeto_id: str, 
    payload: List[NovoItemProjeto], 
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Inserção em massa otimizada para importação de templates paramétricos."""
    insert_list = [{
        "projeto_id": projeto_id,
        "codigo_sinapi": item.codigo_sinapi,
        "descricao": item.descricao,
        "unidade": item.unidade,
        "quantidade": item.quantidade,
        "valor_unitario": item.valor_unitario,
        "tipo_item": item.tipo_item,
        "etapa_obra": item.etapa_obra
    } for item in payload]
    
    res = supabase_client.table("orcamento_itens").insert(insert_list).execute()
    return {"success": True, "data": res.data}

@router.get("/api/projetos/{projeto_id}/itens")
async def listar_itens_projeto(
    projeto_id: str, 
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Retorna todos os itens orçados de um determinado projeto."""
    res = supabase_client.table("orcamento_itens").select("*").eq("projeto_id", projeto_id).order("created_at", desc=False).execute()
    return {"success": True, "data": res.data}

@router.patch("/api/projetos/{projeto_id}/itens/{item_id}")
async def atualizar_item_projeto(
    projeto_id: str, 
    item_id: str, 
    payload: dict, 
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Atualiza a quantidade ou a etapa de um item da árvore de custos."""
    update_data = {k: v for k, v in payload.items() if k in ["quantidade", "etapa_obra"]}
    if not update_data:
        return {"success": True, "message": "Nenhum atributo modificável enviado."}
        
    res = supabase_client.table("orcamento_itens").update(update_data).eq("id", item_id).eq("projeto_id", projeto_id).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não localizado neste projeto.")
    return {"success": True, "data": res.data[0]}

@router.delete("/api/projetos/{projeto_id}/itens/{item_id}")
async def remover_item_projeto(
    projeto_id: str,
    item_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """Exclui um insumo ou composição do projeto."""
    res = supabase_client.table("orcamento_itens").delete().eq("id", item_id).eq("projeto_id", projeto_id).execute()
    return {"success": True}


class AplicarTemplateRequest(BaseModel):
    modo: str = Field("mesclar", description="'substituir' apaga os itens atuais e insere o template; 'mesclar' insere apenas os códigos que ainda não estão na árvore")
    template_id: Optional[str] = Field(None, description="ID do template a usar. Se None, usa o is_default do padrão do projeto (ou SISTEMA como fallback)")


@router.post("/api/projetos/{projeto_id}/aplicar-template-padrao", status_code=status.HTTP_201_CREATED)
async def aplicar_template_padrao(
    projeto_id: str,
    payload: AplicarTemplateRequest = AplicarTemplateRequest(),
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id),
):
    """
    Popula a árvore de custos com os itens padrão do template SINAPI para o padrão de obra configurado.
    Itens são inseridos com quantidade=0 para preenchimento posterior pelo engenheiro.
    Usa o template CUSTOMIZADO do usuário se existir, senão fallback para o template SISTEMA.
    modo='substituir': apaga todos os itens existentes antes de inserir.
    modo='mesclar': insere apenas códigos que ainda não estão na árvore.
    """
    res_projeto = (
        supabase_client.table("projetos_clientes")
        .select("padrao, uf_obra, sinapi_mes_ano, sinapi_desonerado")
        .eq("id", projeto_id)
        .single()
        .execute()
    )
    if not res_projeto.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")

    projeto = res_projeto.data
    padrao = projeto.get("padrao")
    if not padrao:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configure o padrão de obra no Setup antes de aplicar o template.")

    uf_obra = projeto.get("uf_obra") or "SC"
    sinapi_mes_ano = projeto.get("sinapi_mes_ano")
    sinapi_desonerado = projeto.get("sinapi_desonerado") or False

    # Resolução do template a usar:
    # 1. template_id explícito no payload (escolha do usuário no Orçamento)
    # 2. CUSTOMIZADO com is_default=true para o padrão
    # 3. Qualquer CUSTOMIZADO do usuário para o padrão
    # 4. SISTEMA como fallback imutável
    if payload.template_id:
        template_res = (
            supabase_client.table("templates_eap")
            .select("id, tipo, usuario_id, template_eap_itens(*)")
            .eq("id", payload.template_id)
            .execute()
        )
        if template_res.data:
            t = template_res.data[0]
            if t["tipo"] == "CUSTOMIZADO" and t["usuario_id"] != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado ao template informado.")
    else:
        template_res = (
            supabase_client.table("templates_eap")
            .select("id, template_eap_itens(*)")
            .eq("padrao_obra", padrao)
            .eq("tipo", "CUSTOMIZADO")
            .eq("usuario_id", user_id)
            .eq("is_default", True)
            .execute()
        )
        if not template_res.data:
            template_res = (
                supabase_client.table("templates_eap")
                .select("id, template_eap_itens(*)")
                .eq("padrao_obra", padrao)
                .eq("tipo", "CUSTOMIZADO")
                .eq("usuario_id", user_id)
                .execute()
            )
        if not template_res.data:
            template_res = (
                supabase_client.table("templates_eap")
                .select("id, template_eap_itens(*)")
                .eq("padrao_obra", padrao)
                .eq("tipo", "SISTEMA")
                .execute()
            )

    if not template_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Nenhum template encontrado para o padrão '{padrao}'.")

    template_itens = template_res.data[0].get("template_eap_itens", [])
    if not template_itens:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template configurado não possui itens.")

    # Busca preços ao vivo no SINAPI para todos os códigos do template
    all_codes = [item["codigo_sinapi"] for item in template_itens]
    sinapi_query = (
        supabase_client.table("sinapi_itens")
        .select("codigo_item, descricao, unidade, preco")
        .in_("codigo_item", all_codes)
        .eq("estado", uf_obra)
        .eq("desonerado", sinapi_desonerado)
    )
    if sinapi_mes_ano:
        sinapi_query = sinapi_query.eq("mes_ano", sinapi_mes_ano)

    sinapi_res = sinapi_query.execute()
    sinapi_map: dict = {}
    for row in sinapi_res.data or []:
        if row["codigo_item"] not in sinapi_map:
            sinapi_map[row["codigo_item"]] = {
                "descricao": row["descricao"],
                "unidade": row["unidade"],
                "preco": float(row["preco"] or 0),
            }

    nao_encontrados = [t["codigo_sinapi"] for t in template_itens if t["codigo_sinapi"] not in sinapi_map]
    if nao_encontrados:
        print(f"[WARN] aplicar_template_padrao: {len(nao_encontrados)} código(s) não encontrados no SINAPI "
              f"({uf_obra}/{sinapi_mes_ano}/desonerado={sinapi_desonerado}): {nao_encontrados}")

    # --- modo: substituir ---
    if payload.modo == "substituir":
        supabase_client.table("orcamento_itens").delete().eq("projeto_id", projeto_id).execute()
        pares_ja_presentes: set = set()
    # --- modo: mesclar (padrão) ---
    else:
        existentes_res = (
            supabase_client.table("orcamento_itens")
            .select("codigo_sinapi, etapa_obra")
            .eq("projeto_id", projeto_id)
            .execute()
        )
        # Deduplicação por (código, fase) — o mesmo código pode existir em fases distintas
        pares_ja_presentes = {
            (row["codigo_sinapi"], row["etapa_obra"])
            for row in (existentes_res.data or [])
        }

    itens_para_inserir = [
        {
            "projeto_id": projeto_id,
            "codigo_sinapi": t["codigo_sinapi"],
            "descricao": sinapi_map.get(t["codigo_sinapi"], {}).get("descricao") or f"Cód. SINAPI {t['codigo_sinapi']}",
            "unidade": sinapi_map.get(t["codigo_sinapi"], {}).get("unidade") or "UN",
            "quantidade": 0,
            "valor_unitario": sinapi_map.get(t["codigo_sinapi"], {}).get("preco", 0.0),
            "tipo_item": "insumo",
            "etapa_obra": t["fase_obra"],
        }
        for t in template_itens
        if (t["codigo_sinapi"], t["fase_obra"]) not in pares_ja_presentes
    ]

    if itens_para_inserir:
        supabase_client.table("orcamento_itens").insert(itens_para_inserir).execute()

    return {
        "success": True,
        "modo": payload.modo,
        "inserted": len(itens_para_inserir),
        "ignorados": len(template_itens) - len(itens_para_inserir),
        "sem_preco": nao_encontrados,
    }


# =========================================================================
# --- ROTAS DE COMPATIBILIDADE / TRANSIÇÃO SUAVE PARA O FRONTEND ---
# =========================================================================

@router.get("/api/orcamentos")
async def listar_orcamentos_legacy_compat(supabase_client: Client = Depends(get_authenticated_supabase)):
    """
    Rota de compatibilidade: Redireciona de forma transparente a listagem 
    de orçamentos legados para consumir a tabela unificada de projetos.
    """
    response = supabase_client.table("projetos_clientes").select("*").neq("status", "ARQUIVADO").order("created_at", desc=True).execute()
    projetos = response.data
    
    # Formata a saída para o formato que a tabela/menu antigo de orçamentos espera
    for p in projetos:
        p["nome_obra"] = p.get("titulo_projeto") or p.get("cliente_nome") or "Obra sem título"
        p["bdi"] = p.get("bdi_padrao") or 0.0
        p["valor_total"] = p.get("valor") or 0.0
        
    return {"success": True, "data": projetos}

@router.post("/api/orcamentos", status_code=status.HTTP_201_CREATED)
async def criar_orcamento_legacy_compat(
    payload: dict,
    supabase_client: Client = Depends(get_authenticated_supabase),
    user_id: str = Depends(get_user_id)
):
    """Alias compatível para criação rápida de orçamento a partir de modais antigos."""
    nome_obra = payload.get("nome_obra", "Nova Obra")
    cliente_nome = payload.get("cliente_nome", "Cliente Padrão")
    
    insert_data = {
        "usuario_id": user_id,
        "cliente_nome": cliente_nome,
        "titulo_projeto": nome_obra,
        "telefone": payload.get("telefone", "00000000000"),
        "observacoes": payload.get("observacoes"),
        "bdi_padrao": payload.get("bdi", 25.0),
        "coluna": "estimativa_enviada",
        "status": "aguardando_cliente"
    }
    
    response = supabase_client.table("projetos_clientes").insert(insert_data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Erro ao inicializar o orçamento.")
        
    criado = response.data[0]
    criado["nome_obra"] = criado.get("titulo_projeto")
    return {"success": True, "data": criado}


# =========================================================================
# --- ROTAS DE HISTÓRICO E NOTAS & PROJETOS ARQUIVADOS ---
# =========================================================================

_STATUS_RESTAURACAO = {
    "contrato_pendente": "docs_validados",
    "engenharia_caixa":  "em_analise_caixa",
    "obra_liberada":     "liberada",
}

@router.get("/api/projetos-arquivados")
async def listar_projetos_arquivados(supabase_client: Client = Depends(get_authenticated_supabase)):
    """Retorna todos os projetos arquivados do tenant, ordenados pela data de arquivamento."""
    res = supabase_client.table("projetos_clientes") \
        .select("*") \
        .eq("status", "ARQUIVADO") \
        .order("archived_at", desc=True) \
        .execute()
    projetos = res.data
    for p in projetos:
        p["nome"]    = p.get("titulo_projeto") or p.get("cliente_nome") or "Obra sem título"
        p["cliente"] = p.get("cliente_nome") or "Cliente não informado"
        p["archived_at"] = p.get("archived_at") or p.get("created_at")
    return {"success": True, "data": projetos}

@router.post("/api/projetos/{id}/restaurar")
async def restaurar_projeto(id: str, supabase_client: Client = Depends(get_authenticated_supabase)):
    """Restaura um projeto arquivado para a fase de funil em que estava."""
    check = supabase_client.table("projetos_clientes") \
        .select("id,coluna") \
        .eq("id", id).eq("status", "ARQUIVADO") \
        .execute()
    if not check.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto arquivado não encontrado.")
    coluna = check.data[0].get("coluna") or "estimativa_enviada"
    novo_status = _STATUS_RESTAURACAO.get(coluna, "aguardando_cliente")
    res = supabase_client.table("projetos_clientes") \
        .update({"status": novo_status, "coluna": coluna}) \
        .eq("id", id) \
        .execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao restaurar projeto.")
    supabase_client.table("projetos_historico").insert({
        "projeto_id": id,
        "acao": "Projeto Restaurado",
        "detalhes": f"Restaurado da lixeira para a coluna '{coluna}' com status '{novo_status}'."
    }).execute()
    return {"success": True, "data": res.data[0]}

@router.delete("/api/projetos/{id}")
async def excluir_projeto_definitivamente(id: str, supabase_client: Client = Depends(get_authenticated_supabase)):
    """Exclui permanentemente um projeto do banco de dados. Restringe a projetos arquivados."""
    check = supabase_client.table("projetos_clientes").select("id").eq("id", id).eq("status", "ARQUIVADO").execute()
    if not check.data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas projetos arquivados podem ser excluídos permanentemente.")
    supabase_client.table("projetos_clientes").delete().eq("id", id).execute()
    return {"success": True, "message": "Projeto excluído definitivamente."}

@router.get("/api/projetos/{id}/historico")
async def get_historico_projeto(id: str, supabase_client: Client = Depends(get_authenticated_supabase)):
    """Consulta todas as entradas de histórico e notas de um projeto específico."""
    res = supabase_client.table("projetos_historico").select("*").eq("projeto_id", id).order("created_at", desc=True).execute()
    notas = res.data
    for n in notas:
        created = n.get("created_at", "")
        n["data"] = created.replace("T", " ").split(".")[0] if created else ""
        n["autor"] = "Você" if n.get("acao") in ("Nota Manual", "Observação") else "Sistema"
        n["texto"] = n.get("detalhes") or n.get("acao")
    return {"success": True, "data": notas}

@router.post("/api/projetos/{id}/historico", status_code=status.HTTP_201_CREATED)
async def criar_nota_historico(id: str, payload: NotaHistoricoCreate, supabase_client: Client = Depends(get_authenticated_supabase)):
    """Adiciona uma nova observação ou nota manual ao histórico do projeto."""
    insert_data = {
        "projeto_id": id,
        "acao": "Nota Manual",
        "detalhes": payload.texto
    }
    res = supabase_client.table("projetos_historico").insert(insert_data).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Não foi possível inserir a nota.")
    
    nota = res.data[0]
    created = nota.get("created_at", "")
    nota["data"] = created.replace("T", " ").split(".")[0] if created else ""
    nota["autor"] = "Você"
    nota["texto"] = nota.get("detalhes")
    return {"success": True, "data": nota}

