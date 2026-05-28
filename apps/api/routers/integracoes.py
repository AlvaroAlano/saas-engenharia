import os
import io
import re
import httpx
import base64
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import Client, create_client
from dependencies import get_authenticated_supabase, security, get_user_id
from fastapi.security import HTTPAuthorizationCredentials
from utils.pdf_generator import generate_contract_pdf
from database import supabase as supabase_admin

router = APIRouter(prefix="/api", tags=["Integracoes"])

# --- Models ---

class TransformarTemplateRequest(BaseModel):
    nome: str
    area_referencia_m2: float

class ImportarTemplateRequest(BaseModel):
    nova_area: Optional[float] = None

class TemplateCreate(BaseModel):
    titulo: str
    conteudo: str
    tipo: str = "proposta"

class TemplateUpdate(BaseModel):
    titulo: Optional[str] = None
    conteudo: Optional[str] = None
    tipo: Optional[str] = None

class EnviarZapSignRequest(BaseModel):
    template_id: str

# --- Helper ---

def get_service_supabase() -> Client:
    """Retorna um Client Supabase com a Service Role Key (Admin) para bypass de RLS."""
    url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not service_key:
        raise HTTPException(status_code=500, detail="SUPABASE_SERVICE_ROLE_KEY não configurada.")
    return create_client(url, service_key)

# --- Routes: Templates Paramétricos ---

@router.post("/projetos/{projeto_id}/transformar-template")
async def transformar_em_template(projeto_id: str, payload: TransformarTemplateRequest, supabase_client: Client = Depends(get_authenticated_supabase)):
    try:
        template_data = {"nome": payload.nome, "area_referencia_m2": payload.area_referencia_m2}
        res_template = supabase_client.table("templates").insert(template_data).execute()
        template_id = res_template.data[0]["id"]
        
        res_itens = supabase_client.table("orcamento_itens").select("*").eq("projeto_id", projeto_id).execute()
        if res_itens.data:
            novos_itens = [{
                "template_id": template_id,
                "codigo_sinapi": item.get("codigo_sinapi"),
                "descricao": item.get("descricao"),
                "unidade": item.get("unidade"),
                "quantidade": item.get("quantidade"),
                "valor_unitario_snapshot": item.get("valor_unitario"),
                "scale_behavior": "LINEAR"
            } for item in res_itens.data]
            supabase_client.table("template_itens").insert(novos_itens).execute()

        return {"success": True, "data": res_template.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates-orcamento")
async def listar_templates(supabase_client: Client = Depends(get_authenticated_supabase)):
    try:
        res = supabase_client.table("templates").select("*").order("criado_em", desc=True).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projetos/{projeto_id}/importar-template/{template_id}")
async def importar_template(projeto_id: str, template_id: str, payload: ImportarTemplateRequest, supabase_client: Client = Depends(get_authenticated_supabase)):
    try:
        res_template = supabase_client.table("templates").select("*").eq("id", template_id).single().execute()
        template = res_template.data
        fator = float(payload.nova_area) / float(template["area_referencia_m2"]) if payload.nova_area and template["area_referencia_m2"] > 0 else 1.0
        
        res_itens = supabase_client.table("template_itens").select("*").eq("template_id", template_id).execute()
        if res_itens.data:
            novos_itens = [{
                "projeto_id": projeto_id,
                "codigo_sinapi": item.get("codigo_sinapi"),
                "descricao": item.get("descricao"),
                "unidade": item.get("unidade"),
                "quantidade": float(item.get("quantidade", 0)) * (fator if item.get("scale_behavior") == "LINEAR" else 1.0),
                "valor_unitario": item.get("valor_unitario_snapshot", 0),
                "tipo_item": "insumo"
            } for item in res_itens.data]
            supabase_client.table("orcamento_itens").insert(novos_itens).execute()
        return {"success": True, "message": "Template importado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Routes: Templates Contrato ---

@router.get("/contratos-templates")
async def listar_templates_contrato(supabase_client: Client = Depends(get_authenticated_supabase)):
    try:
        res = supabase_client.table("templates_contrato").select("id, titulo, tipo, created_at").order("created_at").execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contratos-templates/{id}")
async def buscar_template_contrato(id: str, supabase_client: Client = Depends(get_authenticated_supabase)):
    try:
        res = supabase_client.table("templates_contrato").select("*").eq("id", id).single().execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

@router.post("/contratos-templates")
async def criar_template_contrato(template: TemplateCreate, supabase_client: Client = Depends(get_authenticated_supabase), user_id: str = Depends(get_user_id)):
    try:
        res = supabase_client.table("templates_contrato").insert({"titulo": template.titulo, "conteudo": template.conteudo, "tipo": template.tipo, "usuario_id": user_id}).execute()
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/contratos-templates/{id}")
async def atualizar_template_contrato(id: str, template: TemplateUpdate, supabase_client: Client = Depends(get_authenticated_supabase)):
    try:
        update_data = {k: v for k, v in template.dict(exclude_unset=True).items()}
        res = supabase_client.table("templates_contrato").update(update_data).eq("id", id).execute()
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/contratos-templates/{id}")
async def deletar_template_contrato(id: str, supabase_client: Client = Depends(get_authenticated_supabase)):
    try:
        supabase_client.table("templates_contrato").delete().eq("id", id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Routes: Contratos & ZapSign ---

@router.get("/projetos/{id}/contrato")
def gerar_contrato(id: str, template_id: str = Query(...), supabase_client: Client = Depends(get_authenticated_supabase)):
    """
    Gera o PDF do contrato a partir de um template. Roda como `def` (sync) para que o FastAPI
    delegue automaticamente para uma thread pool separada, liberando o event loop do Uvicorn
    durante a geração CPU-bound do PDF (fpdf2). REF: TODO.md P1.1
    """
    try:
        res_projeto = supabase_client.table("projetos_clientes").select("*").eq("id", id).single().execute()
        projeto = res_projeto.data

        documentos = projeto.get("documentos") or []
        categorias_obrigatorias = {'identidade', 'residencia', 'estado_civil'}
        docs_aprovados = {d.get('categoria') for d in documentos if d.get('status') == 'aprovado'}
        if not categorias_obrigatorias.issubset(docs_aprovados):
            raise HTTPException(
                status_code=403,
                detail="Todos os 3 documentos obrigatórios devem estar com status 'aprovado' para gerar o contrato."
            )

        res_template = supabase_client.table("templates_contrato").select("*").eq("id", template_id).single().execute()
        template_db = res_template.data

        valor_num = projeto.get("valor", 0)
        valor_formatado = f"R$ {valor_num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if valor_num else "R$ 0,00"

        # Variáveis SINAPI — calculadas a partir dos itens do orçamento
        res_itens = supabase_client.table("orcamento_itens").select("valor_unitario, quantidade").eq("projeto_id", id).execute()
        itens = res_itens.data or []
        bdi_perc = float(projeto.get("bdi_padrao") or 0.0)
        fator_bdi = 1 + (bdi_perc / 100)
        valor_total_sinapi = sum(
            float(item.get("valor_unitario") or 0) * float(item.get("quantidade") or 0) * fator_bdi
            for item in itens
        )
        _tamanho_raw = re.sub(r"[^\d.,]", "", str(projeto.get("tamanho") or "0")).replace(",", ".")
        tamanho = float(_tamanho_raw) if _tamanho_raw else 0.0
        valor_por_m2_sinapi = valor_total_sinapi / tamanho if tamanho > 0 else 0.0

        def fmt_brl(v: float) -> str:
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        texto_final = template_db.get("conteudo", "") \
            .replace("{{cliente_nome}}", str(projeto.get("cliente_nome", ""))) \
            .replace("{{tamanho}}", str(projeto.get("tamanho", ""))) \
            .replace("{{padrao}}", str(projeto.get("padrao", ""))) \
            .replace("{{valor}}", str(valor_formatado)) \
            .replace("{{valor_total_sinapi}}", fmt_brl(valor_total_sinapi)) \
            .replace("{{mes_referencia_sinapi}}", str(projeto.get("sinapi_mes_ano") or "-")) \
            .replace("{{bdi}}", f"{bdi_perc:.1f}%") \
            .replace("{{valor_por_m2_sinapi}}", fmt_brl(valor_por_m2_sinapi))

        pdf_bytes = generate_contract_pdf(texto_final)
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        try:
            supabase_client.table("projetos_clientes").update({"contrato_gerado": True}).eq("id", id).execute()
            supabase_client.table("projetos_historico").insert({
                "projeto_id": id, "acao": "Contrato Gerado", "detalhes": f"Template: {template_db.get('titulo')}"
            }).execute()
        except Exception as audit_err:
            logger.warning("Falha ao registrar auditoria do contrato (não fatal): %s", audit_err)

        headers = {"Content-Disposition": f'inline; filename="contrato_{id}.pdf"'}
        return StreamingResponse(buffer, media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao gerar contrato para projeto %s", id)
        raise HTTPException(status_code=500, detail="Erro ao gerar o contrato. Tente novamente.")

@router.post("/projetos/{id}/enviar-zapsign")
async def enviar_para_zapsign(id: str, payload: EnviarZapSignRequest, supabase_client: Client = Depends(get_authenticated_supabase), token: HTTPAuthorizationCredentials = Depends(security)):
    zapsign_token = os.environ.get("ZAPSIGN_API_TOKEN")
    if not zapsign_token:
        raise HTTPException(status_code=500, detail="ZAPSIGN_API_TOKEN ausente.")
    
    try:
        res_projeto = supabase_client.table("projetos_clientes").select("*").eq("id", id).single().execute()
        projeto = res_projeto.data

        documentos = projeto.get("documentos") or []
        categorias_obrigatorias = {'identidade', 'residencia', 'estado_civil'}
        docs_aprovados = {d.get('categoria') for d in documentos if d.get('status') == 'aprovado'}
        if not categorias_obrigatorias.issubset(docs_aprovados):
            raise HTTPException(
                status_code=403,
                detail="Todos os 3 documentos obrigatórios devem estar com status 'aprovado' para enviar o contrato."
            )

        res_template = supabase_client.table("templates_contrato").select("*").eq("id", payload.template_id).single().execute()
        template_db = res_template.data

        valor_num = projeto.get("valor", 0)
        valor_formatado = f"R$ {valor_num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if valor_num else "R$ 0,00"
        
        texto_final = template_db.get("conteudo", "").replace("{{cliente_nome}}", str(projeto.get("cliente_nome", ""))) \
            .replace("{{tamanho}}", str(projeto.get("tamanho", ""))) \
            .replace("{{padrao}}", str(projeto.get("padrao", ""))) \
            .replace("{{valor}}", str(valor_formatado))
        
        pdf_bytes = generate_contract_pdf(texto_final)
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Fallback seguro e de altíssimo desempenho sem requisição extra de rede ou tabelas inexistentes
        nome_eng = "Engenheiro Responsável"
        
        zapsign_payload = {
            "name": f"Contrato - {projeto.get('cliente_nome')} - {projeto.get('titulo_projeto', 'Obra')}",
            "base64_pdf": pdf_base64,
            "signers": [{"name": projeto.get("cliente_nome")}, {"name": nome_eng}],
            "lang": "pt-br"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.zapsign.com.br/api/v1/docs/", json=zapsign_payload, headers={"Authorization": f"Bearer {zapsign_token}", "Content-Type": "application/json"})
        
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Erro ZapSign: {resp.text}")
        
        data = resp.json()
        doc_token = data["token"]
        signers = data["signers"]

        cliente_signer  = signers[0] if len(signers) > 0 else {}
        eng_signer      = signers[1] if len(signers) > 1 else {}

        base_update = {
            "contrato_gerado":           True,
            "zapsign_document_token":    doc_token,
            "url_assinatura_cliente":    cliente_signer.get("sign_url", ""),
            "url_assinatura_engenheiro": eng_signer.get("sign_url", ""),
            "status_assinatura":         "pendente",
            "cliente_assinou":           False,
            "engenheiro_assinou":        False,
        }

        # Tenta incluir os tokens de signatários (requer migration 012)
        try:
            supabase_client.table("projetos_clientes").update({
                **base_update,
                "zapsign_signer_token_cliente":    cliente_signer.get("token", ""),
                "zapsign_signer_token_engenheiro": eng_signer.get("token", ""),
            }).eq("id", id).execute()
        except Exception:
            logger.warning("Colunas de signer_token indisponíveis — aplicar migration 012. Salvando sem elas.")
            supabase_client.table("projetos_clientes").update(base_update).eq("id", id).execute()

        logger.info("Contrato enviado ao ZapSign. doc_token=%s projeto=%s", doc_token, id)
        return {"success": True, "data": {"token": doc_token}}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

# --- Webhook ZapSign (Bypass RLS Seguro) ---

@router.post("/zapsign-webhook")
async def zapsign_webhook(request: Request, secret_token: Optional[str] = Query(None)):
    """
    Recebe notificações da ZapSign sobre eventos de assinatura.
    - signer_signed: um signatário específico assinou — atualiza cliente_assinou ou engenheiro_assinou.
    - doc_signed: todos assinaram — fecha o contrato e salva o PDF final.
    Usa Service Role para bypass de RLS; valida origem pelo ZAPSIGN_WEBHOOK_SECRET.
    """
    expected_token = os.environ.get("ZAPSIGN_WEBHOOK_SECRET")
    if not expected_token or secret_token != expected_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso negado: token de webhook inválido.")

    try:
        data = await request.json()
        event_type = data.get("event_type")
        document   = data.get("document", {})
        doc_token  = document.get("token")

        logger.info("Webhook ZapSign recebido: event=%s doc_token=%s", event_type, doc_token)

        if not doc_token:
            return {"status": "ignored", "message": "Token de documento ausente."}

        service_client = get_service_supabase()

        # --- Assinatura individual de um signatário ---
        if event_type == "signer_signed":
            signer       = data.get("signer", {})
            signer_token = signer.get("token", "")

            if not signer_token:
                return {"status": "ignored", "message": "Token do signatário ausente."}

            # Busca o projeto para comparar tokens dos signatários
            try:
                res = service_client.table("projetos_clientes") \
                    .select("id, zapsign_document_token, zapsign_signer_token_cliente, zapsign_signer_token_engenheiro") \
                    .eq("zapsign_document_token", doc_token) \
                    .execute()
            except Exception as sel_err:
                # Colunas de token ainda não existem no banco (migration 012 pendente):
                # identifica o projeto só pelo doc_token e registra quem assinou pelo nome.
                logger.warning("signer_signed SELECT falhou (%s). Aguardando migration 012.", sel_err)
                res_id = service_client.table("projetos_clientes") \
                    .select("id") \
                    .eq("zapsign_document_token", doc_token) \
                    .execute()
                if not res_id.data:
                    return {"status": "ignored", "message": "Projeto não encontrado."}
                logger.info("signer_signed registrado sem token comparison. projeto=%s", res_id.data[0]["id"])
                return {"status": "received", "message": "Assinatura recebida (tokens pendentes de migration)."}

            if not res.data:
                logger.warning("Webhook signer_signed: nenhum projeto encontrado para doc_token=%s", doc_token)
                return {"status": "ignored", "message": "Projeto não encontrado."}

            projeto = res.data[0]
            update  = {}

            if signer_token == projeto.get("zapsign_signer_token_cliente"):
                update["cliente_assinou"] = True
                logger.info("Cliente assinou o contrato. projeto=%s", projeto["id"])
            elif signer_token == projeto.get("zapsign_signer_token_engenheiro"):
                update["engenheiro_assinou"] = True
                logger.info("Engenheiro assinou o contrato. projeto=%s", projeto["id"])
            else:
                logger.warning(
                    "Token de signatário desconhecido=%s para projeto=%s — ignorando.",
                    signer_token, projeto["id"]
                )
                return {"status": "ignored", "message": "Signatário não reconhecido."}

            service_client.table("projetos_clientes").update(update) \
                .eq("id", projeto["id"]).execute()

            return {"status": "success", "message": "Assinatura individual registrada."}

        # --- Documento totalmente assinado por todos ---
        if event_type == "doc_signed":
            pdf_url = document.get("pdf_file", "")

            update_payload: Dict[str, Any] = {
                "status_assinatura":  "assinado",
                "cliente_assinou":    True,
                "engenheiro_assinou": True,
            }

            # Tenta salvar a URL do PDF assinado; ignora se a coluna ainda não existir no banco
            if pdf_url:
                try:
                    service_client.table("projetos_clientes").update(
                        {**update_payload, "url_contrato_assinado": pdf_url}
                    ).eq("zapsign_document_token", doc_token).execute()
                except Exception:
                    logger.warning("Coluna url_contrato_assinado indisponível — aplicar migration 012. Atualizando sem ela.")
                    service_client.table("projetos_clientes").update(update_payload) \
                        .eq("zapsign_document_token", doc_token).execute()
            else:
                service_client.table("projetos_clientes").update(update_payload) \
                    .eq("zapsign_document_token", doc_token).execute()

            logger.info("Contrato totalmente assinado. doc_token=%s pdf_url=%s", doc_token, pdf_url)
            return {"status": "success", "message": "Contrato marcado como assinado."}

        return {"status": "received", "message": f"Evento '{event_type}' recebido e ignorado."}

    except Exception as e:
        logger.exception("Erro no webhook ZapSign: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro no webhook: {str(e)}")
