import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "")
# O cliente padrão do backend deve usar a ANON_KEY para respeitar o RLS.
# Se precisar de bypass, use explicitamente a SERVICE_ROLE_KEY em funções específicas.
key: str = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY", "")

if not url or not key:
    print("AVISO: SUPABASE_URL ou SUPABASE_ANON_KEY não estão configuradas no .env")

supabase: Client = create_client(url, key) if url and key else None
