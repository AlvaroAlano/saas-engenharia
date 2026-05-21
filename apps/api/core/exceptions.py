import sys
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def get_cors_headers(request: Request, extra_headers: dict = None) -> dict:
    """
    Constrói e injeta os cabeçalhos de CORS dinamicamente na resposta de erro.
    Isso contorna uma limitação arquitetural nativa do Starlette/FastAPI, 
    onde exceções capturadas por Exception Handlers não passam de volta pelo 
    fluxo padrão do CORSMiddleware, fazendo o navegador mascarar a falha como erro de CORS.
    """
    headers = {}
    origin = request.headers.get("origin")
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    else:
        headers["Access-Control-Allow-Origin"] = "*"
        
    if extra_headers:
        headers.update(extra_headers)
    return headers

def setup_exception_handlers(app: FastAPI):
    """
    Registra os tratadores globais de exceções da aplicação para evitar o 
    vazamento de strings cruas do banco de dados (Postgres/Supabase) para o cliente,
    assegurando a injeção estrita de cabeçalhos de CORS.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Se for um erro 500 interno disparado manualmente, aplicamos o filtro de segurança
        if exc.status_code >= 500:
            print(f"[ERRO INTERNO HTTP 500] URL: {request.url} | Detalhe original: {exc.detail}")
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "message": "Erro interno do servidor ao processar a requisição.",
                    "error_code": "INTERNAL_SERVER_ERROR"
                },
                headers=get_cors_headers(request, getattr(exc, "headers", None))
            )
            
        # Repassa 400, 401, 403, 404 normalmente com os headers de CORS blindados
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "detail": exc.detail},
            headers=get_cors_headers(request, getattr(exc, "headers", None))
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        print(f"[ERRO VALIDAÇÃO PYDANTIC] URL: {request.url} | Corpo Inválido: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Dados enviados em formato inválido ou ausentes.",
                "detail": exc.errors()
            },
            headers=get_cors_headers(request)
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Extrai a string crua e o traceback completo para os logs do servidor
        err_str = str(exc)
        print(f"\n[ERRO CRÍTICO NÃO TRATADO] Falha na rota: {request.method} {request.url}")
        print(f"Tipo: {type(exc).__name__}")
        print(f"Mensagem Interna: {err_str}")
        traceback.print_exc(file=sys.stdout)
        print("-" * 80)

        # Mapeamento heurístico para dar um retorno seguro e elegante sem expor o schema
        err_lower = err_str.lower()
        mensagem_segura = "Ocorreu um erro inesperado nos nossos servidores."
        error_code = "UNKNOWN_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        if "duplicate key value" in err_lower or "unique constraint" in err_lower:
            mensagem_segura = "Este registro já existe ou colide com um identificador único no sistema."
            error_code = "DUPLICATE_RECORD"
            status_code = status.HTTP_409_CONFLICT
        elif "violates foreign key constraint" in err_lower or "foreign key" in err_lower:
            mensagem_segura = "A operação falhou porque faz referência a um item ou projeto que não existe mais."
            error_code = "RELATION_NOT_FOUND"
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif "row level security" in err_lower or "rls policy" in err_lower:
            mensagem_segura = "Acesso negado pelas políticas de segurança ou o item não pertence ao seu usuário."
            error_code = "ACCESS_DENIED_RLS"
            status_code = status.HTTP_403_FORBIDDEN
        elif "connection refused" in err_lower or "timeout" in err_lower:
            mensagem_segura = "Tempo limite de conexão com o banco de dados excedido. Tente novamente em instantes."
            error_code = "DATABASE_TIMEOUT"
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        elif "jwt" in err_lower or "unauthorized" in err_lower:
            mensagem_segura = "Sua sessão expirou ou o token de acesso é inválido."
            error_code = "UNAUTHORIZED"
            status_code = status.HTTP_401_UNAUTHORIZED
        elif "invalid api key" in err_lower or "api key" in err_lower:
            mensagem_segura = "A chave de autenticação da API configurada no servidor é inválida ou expirou."
            error_code = "INVALID_API_KEY"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": mensagem_segura,
                "error_code": error_code
            },
            headers=get_cors_headers(request)
        )
