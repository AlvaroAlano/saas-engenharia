import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import datetime

# Routers
from routers import relatorios, projetos, sinapi, integracoes, portal_cliente, simulador, matchmaking, configuracoes, vitrine
# Core
from core.scheduler import scheduler
from core.exceptions import setup_exception_handlers


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    enable_scheduler = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
    if enable_scheduler:
        print("[*] Iniciando APScheduler (Motor de Agendamento)...")
        scheduler.start()
    else:
        print("[*] APScheduler desativado (ENABLE_SCHEDULER=false).")
    yield
    if enable_scheduler:
        print("[*] Desligando APScheduler de forma segura...")
        scheduler.shutdown()

app = FastAPI(title="Engenharia SaaS API", lifespan=lifespan)

# =========================================================================
# 1. SETUP CORS (DEVE SER O PRIMEIRO MIDDLEWARE PARA INTERCEPTAR TUDO)
# =========================================================================
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    os.environ.get("FRONTEND_URL", "https://saas-engenharia-web.vercel.app")
]
print(f"[*] CORS: Origins permitidas: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================================
# 2. SETUP TRATADORES GLOBAIS DE EXCEÇÕES (INJETAM CORS EM ERROS INTERNOS)
# =========================================================================
setup_exception_handlers(app)

# =========================================================================
# 3. REGISTRO DE ROTAS
# =========================================================================
app.include_router(relatorios.router)
app.include_router(projetos.router)
app.include_router(sinapi.router)
app.include_router(sinapi.admin_router)
app.include_router(integracoes.router)
app.include_router(portal_cliente.router)
app.include_router(simulador.router)
app.include_router(matchmaking.router)
app.include_router(configuracoes.router)
app.include_router(vitrine.router)

@app.get("/api/health")
async def health_check():
    return {"status": "online", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    is_dev = os.environ.get("ENVIRONMENT", "production") == "development"
    print(f"[*] Iniciando servidor na porta {port} (Modo: {'Desenvolvimento' if is_dev else 'Produção'})")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_dev)
