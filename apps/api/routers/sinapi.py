import os
import shutil
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from supabase import Client
from dependencies import get_authenticated_supabase
from sinapi_bot import SinapiBot
from core.scheduler import scheduler

router = APIRouter(prefix="/api/sinapi", tags=["SINAPI"])
admin_router = APIRouter(prefix="/api/admin", tags=["SINAPI Admin"])

def job_processar_composicoes(file_path: str):
    print(f"[*] Executando job agendado de SINAPI: {file_path}")
    bot = SinapiBot()
    try:
        df_maes, df_filhos = bot.processar_planilha_composicoes(file_path)
        success = bot.bulk_insert_composicoes(df_maes, df_filhos)
        if success:
            print(f"[+] Job concluído: {len(df_maes)} mães e {len(df_filhos)} filhos.")
        else:
            print("[-] Falha no job de persistência.")
    except Exception as e:
        print(f"[!] Erro crítico no job: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[*] Arquivo persistente {file_path} removido após conclusão do job.")

@admin_router.post("/sync-sinapi")
async def sync_sinapi(
    file: UploadFile = File(...),
    mes_ano: str = Form(...),
    desonerado: bool = Form(False),
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    bot = SinapiBot()
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1]
    temp_file_path = os.path.join(temp_dir, f"sinapi_upload_{uuid.uuid4().hex}{file_ext}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Extrai os dados da planilha usando o processamento otimizado do SinapiBot
        df = bot.processar_planilha_insumos(temp_file_path, mes_ano, desonerado)
        records = df.to_dict('records')
        
        total_records = len(records)
        chunk_size = 5000
        lotes_processados = 0
        
        # Envia os dados fatiados (chunks) para a RPC no Supabase
        for i in range(0, total_records, chunk_size):
            lote = records[i:i + chunk_size]
            try:
                supabase_client.rpc("upsert_sinapi_lote", {"payload": lote}).execute()
                lotes_processados += 1
            except Exception as e:
                # Captura e relata especificamente em qual lote a falha ocorreu
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Falha ao processar o lote {lotes_processados + 1} (registros {i} a {i + len(lote)}): {str(e)}"
                )
        
        return {
            "success": True, 
            "message": f"Processados {total_records} registros com sucesso em {lotes_processados} lotes via RPC."
        }
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@admin_router.post("/sync-composicoes")
async def sync_composicoes(
    file: UploadFile = File(...),
    data_ativacao: Optional[str] = Form(None),
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    file_ext = os.path.splitext(file.filename)[1]
    
    if data_ativacao:
        uploads_dir = "uploads/sinapi_schedules"
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, f"sinapi_comp_{uuid.uuid4().hex}{file_ext}")
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            try:
                run_date = datetime.fromisoformat(data_ativacao.replace("Z", "+00:00"))
            except ValueError:
                run_date = datetime.strptime(data_ativacao, "%Y-%m-%d %H:%M:%S")

            scheduler.add_job(job_processar_composicoes, 'date', run_date=run_date, args=[file_path])
            
            return {
                "success": True,
                "message": f"Processamento agendado com sucesso para {run_date.strftime('%d/%m/%Y %H:%M')}."
            }
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro no agendamento: {str(e)}")
            
    else:
        bot = SinapiBot()
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"sinapi_comp_{uuid.uuid4().hex}{file_ext}")
        
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            df_maes, df_filhos = bot.processar_planilha_composicoes(temp_file_path)
            success = bot.bulk_insert_composicoes(df_maes, df_filhos)
            
            if success:
                return {
                    "success": True, 
                    "total_maes": len(df_maes),
                    "total_filhos": len(df_filhos),
                    "message": "Composições sincronizadas com sucesso."
                }
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha na sincronização das composições.")
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

@router.get("/referencias")
async def get_sinapi_referencias(supabase_client: Client = Depends(get_authenticated_supabase)):
    try:
        response = supabase_client.table("vw_sinapi_referencias").select("mes_ano").execute()
        return {"success": True, "data": [row["mes_ano"] for row in response.data]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar referências SINAPI: {str(e)}")

@router.get("")
async def get_sinapi_items(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    estado: Optional[str] = Query(None),
    mes_ano: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    desonerado: Optional[bool] = Query(None),
    tipo: Optional[str] = Query(None),
    projeto_id: Optional[str] = Query(None),
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    try:
        # Validação Inquebrável de Regra de Negócio: Se atrelado a um projeto,
        # o backend impõe o estado, desoneração e mês/ano persistidos no banco.
        if projeto_id:
            res_proj = supabase_client.table("projetos_clientes").select("uf_obra, sinapi_desonerado, sinapi_mes_ano").eq("id", projeto_id).execute()
            if res_proj and res_proj.data:
                proj = res_proj.data[0]
                if proj.get("uf_obra"): estado = proj["uf_obra"]
                if proj.get("sinapi_desonerado") is not None: desonerado = proj["sinapi_desonerado"]
                if proj.get("sinapi_mes_ano"): mes_ano = proj["sinapi_mes_ano"]

        if tipo == "composicao":
            query = supabase_client.table("sinapi_composicoes").select("*, sinapi_composicao_itens(*)", count="exact")
            
            if q:
                q_str = str(q).strip()
                q_clean = q_str.lstrip('0') if q_str.isdigit() else q_str
                if not q_clean: q_clean = "0"
                query = query.or_(f"descricao.ilike.%{q_str}%,codigo_composicao.ilike.%{q_str}%,codigo_composicao.ilike.%{q_clean}%")

            start_idx = (page - 1) * limit
            end_idx = start_idx + limit - 1
            query = query.range(start_idx, end_idx)
                
            response = query.execute()
            
            total_items = response.count if response.count is not None else 0
            total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
            
            raw_composicoes = response.data or []
            
            # Gather all item codes to fetch their prices in one batch
            child_codes = set()
            for comp in raw_composicoes:
                for child in comp.get("sinapi_composicao_itens", []):
                    if child.get("codigo_item"):
                        child_codes.add(child["codigo_item"])
            
            # Fetch prices for these codes from sinapi_itens
            prices_map = {}
            if child_codes:
                price_query = supabase_client.table("sinapi_itens").select("codigo_item, preco")
                if estado:
                    price_query = price_query.eq("estado", estado)
                if mes_ano:
                    price_query = price_query.eq("mes_ano", mes_ano)
                if desonerado is not None:
                    price_query = price_query.eq("desonerado", desonerado)
                
                price_query = price_query.in_("codigo_item", list(child_codes))
                price_res = price_query.execute()
                
                for item in (price_res.data or []):
                    prices_map[item["codigo_item"]] = float(item["preco"])
            
            # Assemble mapped compositions with computed prices
            data = []
            for comp in raw_composicoes:
                comp_price = 0.0
                children_list = comp.get("sinapi_composicao_itens", [])
                
                for child in children_list:
                    code = child.get("codigo_item")
                    coef = float(child.get("coeficiente", 0.0))
                    item_price = prices_map.get(code, 0.0)
                    comp_price += coef * item_price
                
                data.append({
                    "id": comp["id"],
                    "codigo_item": comp["codigo_composicao"],
                    "descricao": comp["descricao"],
                    "unidade": comp["unidade"],
                    "preco": round(comp_price, 2),
                    "tipo": "composicao",
                    "estado": estado,
                    "mes_ano": mes_ano,
                    "desonerado": desonerado,
                    "itens": children_list
                })
            
            return {
                "success": True, 
                "data": data,
                "total_items": total_items,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
            
        else:
            # Query standard insumos (default behavior)
            query = supabase_client.table("sinapi_itens").select("*", count="exact")
            
            if estado: query = query.eq("estado", estado)
            if mes_ano: query = query.eq("mes_ano", mes_ano)
            if desonerado is not None: query = query.eq("desonerado", desonerado)
            
            if q:
                q_str = str(q).strip()
                q_clean = q_str.lstrip('0') if q_str.isdigit() else q_str
                if not q_clean: q_clean = "0"
                query = query.or_(f"descricao.ilike.%{q_str}%,codigo_item.ilike.%{q_str}%,codigo_item.ilike.%{q_clean}%")

            start_idx = (page - 1) * limit
            end_idx = start_idx + limit - 1
            query = query.range(start_idx, end_idx)
                
            response = query.execute()
            
            total_items = response.count if response.count is not None else 0
            total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
            
            # Add tipo: "insumo" for clarity/uniformity
            data = [
                {**item, "tipo": "insumo"} for item in (response.data or [])
            ]
            
            return {
                "success": True, 
                "data": data,
                "total_items": total_items,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
            
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
