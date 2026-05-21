import os
import io
import re
import httpx
import base64
from typing import Optional, List, Dict, Any
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

class TemplateUpdate(BaseModel):
    titulo: Optional[str] = None
    conteudo: Optional[str] = None

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
        res = supabase_client.table("templates_contrato").select("id, titulo, created_at").order("created_at").execute()
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
        res = supabase_client.table("templates_contrato").insert({"titulo": template.titulo, "conteudo": template.conteudo, "usuario_id": user_id}).execute()
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
        res_template = supabase_client.table("templates_contrato").select("*").eq("id", template_id).single().execute()
        template_db = res_template.data
        
        valor_num = projeto.get("valor", 0)
        valor_formatado = f"R$ {valor_num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if valor_num else "R$ 0,00"
        
        texto_final = template_db.get("conteudo", "").replace("{{cliente_nome}}", str(projeto.get("cliente_nome", ""))) \
            .replace("{{tamanho}}", str(projeto.get("tamanho", ""))) \
            .replace("{{padrao}}", str(projeto.get("padrao", ""))) \
            .replace("{{valor}}", str(valor_formatado))
        
        pdf_bytes = generate_contract_pdf(texto_final)
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)
        
        supabase_client.table("projetos_clientes").update({"contrato_gerado": True}).eq("id", id).execute()
        supabase_client.table("projetos_historico").insert({
            "projeto_id": id, "acao": "Contrato Gerado", "detalhes": f"Template: {template_db.get('titulo')}"
        }).execute()

        headers = {"Content-Disposition": f'inline; filename="contrato_{id}.pdf"'}
        return StreamingResponse(buffer, media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao gerar o contrato. Tente novamente.")

@router.post("/projetos/{id}/enviar-zapsign")
async def enviar_para_zapsign(id: str, payload: EnviarZapSignRequest, supabase_client: Client = Depends(get_authenticated_supabase), token: HTTPAuthorizationCredentials = Depends(security)):
    zapsign_token = os.environ.get("ZAPSIGN_API_TOKEN")
    if not zapsign_token:
        raise HTTPException(status_code=500, detail="ZAPSIGN_API_TOKEN ausente.")
    
    try:
        res_projeto = supabase_client.table("projetos_clientes").select("*").eq("id", id).single().execute()
        projeto = res_projeto.data
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
        
        supabase_client.table("projetos_clientes").update({
            "contrato_gerado": True, "zapsign_document_token": doc_token,
            "url_assinatura_cliente": signers[0].get("sign_url") if len(signers) > 0 else "",
            "url_assinatura_engenheiro": signers[1].get("sign_url") if len(signers) > 1 else "",
            "status_assinatura": "pendente"
        }).eq("id", id).execute()

        return {"success": True, "data": {"token": doc_token}}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

# --- Webhook ZapSign (Bypass RLS Seguro) ---

@router.post("/zapsign-webhook")
async def zapsign_webhook(request: Request, secret_token: Optional[str] = Query(None)):
    """
    Recebe notificações da ZapSign sobre status de assinatura.
    Utiliza Service Role para atualizar o banco sem necessidade de JWT de usuário.
    Valida a origem através de um token secreto configurado no ambiente.
    """
    expected_token = os.environ.get("ZAPSIGN_WEBHOOK_SECRET")
    if not expected_token or secret_token != expected_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso negado: Token de webhook inválido.")
    
    try:
        data = await request.json()
        event_type = data.get("event_type")
        doc_token = data.get("document", {}).get("token")
        
        if not doc_token:
             return {"status": "ignored", "message": "Nenhum token de documento encontrado."}
             
        service_client = get_service_supabase()
        
        if event_type == "doc_signed":
            # Atualiza status no banco
            service_client.table("projetos_clientes").update({
                "status_assinatura": "assinado",
                "cliente_assinou": True,
                "engenheiro_assinou": True # Simplificação para este exemplo
            }).eq("zapsign_document_token", doc_token).execute()
            
            return {"status": "success", "message": "Status atualizado para assinado."}
            
        return {"status": "received", "message": f"Evento {event_type} recebido."}
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro no webhook: {str(e)}")
