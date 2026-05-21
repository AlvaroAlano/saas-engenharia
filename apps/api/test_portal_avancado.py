import os
import sys
import unittest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Adiciona o diretório atual ao path para importação do main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from routers.portal_cliente import get_service_supabase

class TestPortalClienteAvancado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.supabase = get_service_supabase()
        
        # Busca um engenheiro disponível para realizar o matchmaking
        res = cls.supabase.table("engenheiros_disponiveis").select("usuario_id, ufs_atuacao").limit(1).execute()
        if not res.data:
            raise Exception("Nenhum engenheiro encontrado na tabela 'engenheiros_disponiveis'. Rode as migrações primeiro.")
        
        cls.eng_id = res.data[0]["usuario_id"]
        cls.eng_uf = res.data[0]["ufs_atuacao"][0] if res.data[0].get("ufs_atuacao") else "SC"
        cls.created_project_id = None
        cls.created_link_token = None

    def test_01_matchmaking_solicitar_sucesso(self):
        """Teste de solicitação de matchmaking com geração de PIN e link público"""
        payload = {
            "usuario_id": self.eng_id,
            "cliente_nome": "Cliente Teste Portal Avançado",
            "telefone": "(99) 99999-1234",
            "valor": 250000.0,
            "padrao": "Médio Padrão",
            "tamanho": "120m²",
            "uf_obra": self.eng_uf
        }
        
        response = self.client.post("/api/matchmaking/solicitar", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("projeto_id", data)
        self.assertIn("url_publica", data)
        self.assertIn("pin_acesso", data)
        
        # O PIN deve ser os últimos 4 dígitos do telefone
        self.assertEqual(data["pin_acesso"], "1234")
        
        # Guarda para os próximos testes
        self.__class__.created_project_id = data["projeto_id"]
        
        # Extrai o token_acesso da url_publica (formato: .../portal/{token})
        url = data["url_publica"]
        token = url.split("/portal/")[-1]
        self.__class__.created_link_token = token

    def test_02_acesso_portal_sucesso(self):
        """Validação de acesso ao portal do cliente com PIN correto"""
        self.assertIsNotNone(self.created_link_token, "Token de acesso não gerado")
        
        payload = {
            "token_acesso": self.created_link_token,
            "pin_acesso": "1234"
        }
        
        response = self.client.post("/api/portal/acessar-orcamento", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"]["projeto"]["id"], self.created_project_id)

    def test_03_acesso_portal_pin_incorreto(self):
        """Tentativa de acesso ao portal do cliente com PIN incorreto (deve falhar)"""
        self.assertIsNotNone(self.created_link_token, "Token de acesso não gerado")
        
        payload = {
            "token_acesso": self.created_link_token,
            "pin_acesso": "9999" # PIN Errado
        }
        
        response = self.client.post("/api/portal/acessar-orcamento", json=payload)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "PIN incorreto.")

    def test_04_get_feed_obras(self):
        """Busca do feed de obras do portal público"""
        self.assertIsNotNone(self.created_link_token, "Token de acesso não gerado")
        
        response = self.client.get(f"/api/portal/projetos/{self.created_link_token}/feed")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("data"), list)

    def test_05_get_documentos_obras(self):
        """Busca de documentos (Vault) do portal público"""
        self.assertIsNotNone(self.created_link_token, "Token de acesso não gerado")
        
        response = self.client.get(f"/api/portal/projetos/{self.created_link_token}/documentos")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("data"), list)

    def test_06_get_caixometro(self):
        """Busca do caixômetro e juros de obra simulados"""
        self.assertIsNotNone(self.created_link_token, "Token de acesso não gerado")
        
        response = self.client.get(f"/api/portal/projetos/{self.created_link_token}/caixa")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get("success"))
        
        caixa = data.get("data")
        self.assertIn("progresso_geral", caixa)
        self.assertIn("juros_mensal_atual", caixa)
        self.assertIn("juros_acumulado_estimado", caixa)
        self.assertIn("etapas", caixa)
        self.assertEqual(len(caixa["etapas"]), 5) # Deve conter exatamente as 5 etapas da Caixa

    @classmethod
    def tearDownClass(cls):
        # Limpa o projeto de teste criado para não poluir o banco de dados
        if cls.created_project_id:
            print(f"\n[*] Limpando registros de teste (projeto_id: {cls.created_project_id})...")
            # O link é cascateado ou deletado manualmente
            cls.supabase.table("orcamento_links").delete().eq("projeto_id", cls.created_project_id).execute()
            cls.supabase.table("projetos_clientes").delete().eq("id", cls.created_project_id).execute()

if __name__ == "__main__":
    unittest.main()
