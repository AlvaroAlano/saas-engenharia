import os
import base64
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

# Dependência do FastAPI para extrair o Bearer Token do header Authorization
security = HTTPBearer()

def get_authenticated_supabase(token: HTTPAuthorizationCredentials = Depends(security)) -> Client:
    """
    Retorna um Client do Supabase autenticado para a requisição atual.
    O Client é criado usando a ANON_KEY e o JWT do usuário para que o RLS seja respeitado.
    """
    url: str = os.environ.get("SUPABASE_URL", "")
    key: str = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY", "")
    
    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Configuração do Supabase (URL/KEY) ausente no backend."
        )
    
    if not token or not token.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT ausente ou formato inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        # Injetando o token do usuário nos headers para acionar o RLS do Postgres
        options = ClientOptions(headers={"Authorization": f"Bearer {token.credentials}"})
        client: Client = create_client(url, key, options=options)
        
        return client
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Falha ao gerar client Supabase autenticado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extrai o ID do usuário (sub) decodificando o JWT localmente sem chamadas de rede.
    Garante latência zero e total robustez na injeção do usuario_id para conformidade com RLS.
    """
    if not token or not token.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT ausente para extração de identidade.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        parts = token.credentials.split(".")
        if len(parts) < 2:
            raise ValueError("Token JWT em formato inválido.")
            
        payload_b64 = parts[1]
        # Adiciona o padding correto para decodificação base64
        padded = payload_b64 + "=" * ((4 - len(payload_b64) % 4) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        
        user_id = claims.get("sub")
        if not user_id:
            raise ValueError("Claim 'sub' não encontrada no payload do token.")
            
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Não foi possível validar a identidade no token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
