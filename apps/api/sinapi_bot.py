import os
import time
import pandas as pd
from typing import Tuple
from database import supabase

class SinapiBot:
    def __init__(self):
        # A URL real da página de downloads da Caixa
        self.base_url = "https://www.caixa.gov.br/site/paginas/downloads.aspx"
        
    def processar_planilha_insumos(self, caminho_arquivo: str, mes_ano: str, desonerado: bool) -> pd.DataFrame:
        print(f"[*] Processando planilha real SINAPI: {caminho_arquivo}")
        
        # Determinar a aba correta baseada no flag desonerado
        sheet_name = 'ISD' if desonerado else 'ISE'
        
        # 1. Encontrar a linha de cabeçalho dinamicamente
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet_name, header=None)
        
        header_idx = -1
        for i, row in df.head(50).iterrows():
            row_str = row.astype(str).str.upper().tolist()
            if any('CODIGO' in str(val) or 'CÓDIGO' in str(val) for val in row_str):
                header_idx = i
                break
                
        if header_idx == -1:
            raise ValueError(f"Não foi possível encontrar o cabeçalho na aba {sheet_name}.")
            
        print(f"[*] Cabeçalho encontrado na linha {header_idx}. Ajustando DataFrame...")
        
        # 2. Redefinir colunas e descartar a sujeira institucional
        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx + 1:].reset_index(drop=True)
        
        # 3. Identificar colunas base
        cols = df.columns.tolist()
        col_codigo = next((c for c in cols if 'CODIGO' in str(c).upper() or 'CÓDIGO' in str(c).upper()), None)
        col_desc = next((c for c in cols if 'DESCRI' in str(c).upper()), None)
        col_unid = next((c for c in cols if 'UNID' in str(c).upper()), None)
        
        if not (col_codigo and col_desc and col_unid):
            raise ValueError("Colunas básicas (Código, Descrição, Unidade) não encontradas.")
            
        # 4. Identificar colunas de estados (tamanho 2, letras maiúsculas)
        estados_cols = [c for c in cols if isinstance(c, str) and len(c.strip()) == 2 and c.strip().upper() == c.strip()]
        
        # 5. Melt!
        print("[*] Aplicando pd.melt para transformar matriz em formato tabular...")
        df_melted = pd.melt(
            df, 
            id_vars=[col_codigo, col_desc, col_unid], 
            value_vars=estados_cols,
            var_name='estado', 
            value_name='preco'
        )
        
        # 6. Renomear para o padrão do banco
        df_melted = df_melted.rename(columns={
            col_codigo: 'codigo_item',
            col_desc: 'descricao',
            col_unid: 'unidade'
        })
        
        # 7. Limpeza e adequação de tipos
        df_melted['preco'] = pd.to_numeric(df_melted['preco'], errors='coerce')
        df_melted = df_melted.dropna(subset=['codigo_item', 'preco'])
        
        # 8. Adicionar metadados
        df_melted['mes_ano'] = mes_ano
        df_melted['desonerado'] = desonerado
        df_melted['codigo_item'] = df_melted['codigo_item'].astype(str).str.strip()
        
        print(f"[*] Processamento concluído. {len(df_melted)} registros gerados pelo Melt.")
        return df_melted

    def processar_planilha_composicoes(self, caminho_arquivo: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print(f"[*] Processando planilha Analítica de Composições: {caminho_arquivo}")
        
        sheet_name = 'Analítico'
        
        # 1. Ler arquivo completo sem header para encontrar cabeçalho dinâmico
        print(f"[*] Lendo arquivo completo da aba {sheet_name}...")
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet_name, header=None)
        
        # 2. Varre as primeiras 50 linhas do DataFrame à procura da string âncora
        header_idx = -1
        for i, row in df.head(50).iterrows():
            row_str = row.astype(str).str.upper().tolist()
            if any('CÓDIGO DA COMPOSIÇÃO' in str(val) or 'CODIGO DA COMPOSICAO' in str(val) or 'DESCRIÇÃO DA COMPOSIÇÃO' in str(val) for val in row_str):
                header_idx = i
                break
                
        if header_idx == -1:
            raise ValueError(f"Não foi possível encontrar o cabeçalho na aba {sheet_name}.")
            
        print(f"[*] Cabeçalho encontrado na linha {header_idx}. Ajustando DataFrame...")
        
        # 3. Redefinir colunas e descartar o cabeçalho institucional
        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx + 1:].reset_index(drop=True)
        
        # 4. Identificar colunas base dinamicamente
        cols = df.columns.tolist()
        col_codigo_comp = next((c for c in cols if pd.notna(c) and ('CÓDIGO DA COMPOSIÇÃO' in str(c).upper() or 'CODIGO DA COMPOSICAO' in str(c).upper())), None)
        col_desc_comp = next((c for c in cols if pd.notna(c) and ('DESCRIÇÃO DA COMPOSIÇÃO' in str(c).upper() or 'DESCRICAO DA COMPOSICAO' in str(c).upper())), None)
        col_unid_comp = next((c for c in cols if pd.notna(c) and ('UNIDADE' in str(c).upper())), None)
        col_tipo_item = next((c for c in cols if pd.notna(c) and ('TIPO ITEM' in str(c).upper())), None)
        col_codigo_item = next((c for c in cols if pd.notna(c) and ('CÓDIGO ITEM' in str(c).upper() or 'CODIGO ITEM' in str(c).upper())), None)
        col_coeficiente = next((c for c in cols if pd.notna(c) and ('COEFICIENTE' in str(c).upper())), None)
        
        if not (col_codigo_comp and col_desc_comp and col_unid_comp and col_tipo_item and col_codigo_item and col_coeficiente):
            raise ValueError("Colunas básicas do Analítico não encontradas.")

        # 5. Drop NA nas linhas base
        df = df.dropna(subset=[col_codigo_comp])
        df = df[df[col_codigo_comp].astype(str).str.strip() != '']

        # Garantir string e limpar espaços, cuidando para não transformar NaN em "nan" onde não queremos
        df[col_codigo_comp] = df[col_codigo_comp].astype(str).str.strip().replace('nan', '')
        df[col_desc_comp] = df[col_desc_comp].astype(str).str.strip()
        df[col_unid_comp] = df[col_unid_comp].astype(str).str.strip()
        df[col_codigo_item] = df[col_codigo_item].astype(str).str.strip().replace('nan', '')

        # 4. Separar em Mães e Filhos
        # Mães: Tipo Item está vazio (NaN ou nulo)
        df_maes_raw = df[df[col_tipo_item].isna()]
        
        # Filhos: Tipo Item preenchido
        df_filhos_raw = df[df[col_tipo_item].notna()]
        
        # ===== Processamento das Mães =====
        df_maes = df_maes_raw[[col_codigo_comp, col_desc_comp, col_unid_comp]].copy()
        df_maes = df_maes.rename(columns={
            col_codigo_comp: 'codigo_composicao',
            col_desc_comp: 'descricao',
            col_unid_comp: 'unidade'
        })
        df_maes = df_maes.drop_duplicates(subset=['codigo_composicao'])
        
        # Substituir NaN do Pandas por None do Python
        df_maes = df_maes.where(pd.notnull(df_maes), None)
        
        # ===== Processamento dos Filhos =====
        df_filhos = df_filhos_raw[[col_codigo_comp, col_codigo_item, col_tipo_item, col_coeficiente]].copy()
        df_filhos = df_filhos.rename(columns={
            col_codigo_comp: 'codigo_composicao',
            col_codigo_item: 'codigo_item',
            col_tipo_item: 'tipo_item',
            col_coeficiente: 'coeficiente'
        })
        
        df_filhos['tipo_item'] = df_filhos['tipo_item'].astype(str).str.strip().str.upper()
        
        # Garantir float no coeficiente
        if df_filhos['coeficiente'].dtype == 'object':
            df_filhos['coeficiente'] = df_filhos['coeficiente'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df_filhos['coeficiente'] = pd.to_numeric(df_filhos['coeficiente'], errors='coerce')
        
        # Remove linhas que não tenham código do item válido ou coeficiente válido
        df_filhos = df_filhos.dropna(subset=['codigo_item', 'coeficiente'])
        
        # Substituir NaN do Pandas por None do Python
        df_filhos = df_filhos.where(pd.notnull(df_filhos), None)
        
        print(f"[*] Extração concluída. Mães: {len(df_maes)} | Filhos: {len(df_filhos)}")
        return df_maes, df_filhos

    def bulk_insert_sinapi(self, df: pd.DataFrame) -> bool:
        """
        Formata o DataFrame lido no padrão esperado pelo Banco e realiza um Bulk Upsert.
        Usa a constraint UNIQUE (codigo_item, estado, mes_ano, desonerado) para evitar duplicatas.
        Se o registro já existir, atualiza o preço e os demais campos.
        """
        if not supabase:
            print("[!] Erro: Cliente Supabase não está configurado.")
            return False
            
        print(f"[*] Preparando registros para upsert em massa (Bulk Upsert)...")
        
        # Converte o df direto para dicionário (as colunas já estão com o nome correto)
        records = df.to_dict('records')
            
        # O cliente Python do Supabase suporta upsert de listas.
        chunk_size = 1000 
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            try:
                # Upsert: se o item já existe para aquele estado/mês/desonerado, atualiza o preço
                response = supabase.table("sinapi_itens").upsert(
                    chunk, 
                    on_conflict="codigo_item,estado,mes_ano,desonerado"
                ).execute()
                print(f"[+] Lote de {len(chunk)} registros sincronizado (upsert) com o banco.")
            except Exception as e:
                print(f"[!] Erro ao realizar bulk upsert do lote: {e}")
                return False
                
        print("[*] Sincronização do catálogo concluída com sucesso no Supabase!")
        return True

    def bulk_insert_composicoes(self, df_maes: pd.DataFrame, df_filhos: pd.DataFrame) -> bool:
        if not supabase:
            print("[!] Erro: Cliente Supabase não está configurado.")
            return False
            
        print("[*] Iniciando persistência do Analítico de Composições...")
        
        # 1. Upsert das Mães (sinapi_composicoes)
        maes_records = df_maes.to_dict('records')
        print(f"[*] Fazendo upsert de {len(maes_records)} composições (Mães)...")
        
        chunk_size = 1000
        todas_maes_inseridas = []
        for i in range(0, len(maes_records), chunk_size):
            chunk = maes_records[i:i + chunk_size]
            try:
                res = supabase.table("sinapi_composicoes").upsert(chunk, on_conflict="codigo_composicao").execute()
                todas_maes_inseridas.extend(res.data)
            except Exception as e:
                print(f"[!] Erro no upsert das composições: {e}")
                return False
                
        print(f"[+] Upsert das Mães concluído. {len(todas_maes_inseridas)} registradas.")
        
        # 2. Mapear UUIDs nos Filhos
        map_codigo_id = {mae['codigo_composicao']: mae['id'] for mae in todas_maes_inseridas}
        df_filhos['composicao_id'] = df_filhos['codigo_composicao'].map(map_codigo_id)
        
        df_filhos_validos = df_filhos.dropna(subset=['composicao_id']).copy()
        
        uuids_maes = df_filhos_validos['composicao_id'].unique().tolist()
        
        # 3. Deletar os itens atuais dessas mães (Integridade Relacional)
        print(f"[*] Limpando itens antigos para {len(uuids_maes)} composições...")
        for i in range(0, len(uuids_maes), 200):
            chunk_uuids = uuids_maes[i:i+200]
            try:
                supabase.table("sinapi_composicao_itens").delete().in_("composicao_id", chunk_uuids).execute()
            except Exception as e:
                print(f"[!] Erro ao limpar filhos antigos: {e}")
                return False
                
        # 4. Inserir os Filhos
        df_filhos_validos = df_filhos_validos.drop(columns=['codigo_composicao'])
        filhos_records = df_filhos_validos.to_dict('records')
        
        print(f"[*] Inserindo {len(filhos_records)} itens (Filhos)...")
        for i in range(0, len(filhos_records), chunk_size):
            chunk = filhos_records[i:i + chunk_size]
            try:
                supabase.table("sinapi_composicao_itens").insert(chunk).execute()
            except Exception as e:
                print(f"[!] Erro no insert dos itens: {e}")
                return False
                
        print("[*] Persistência do Analítico concluída com sucesso!")
        return True

if __name__ == "__main__":
    pass
