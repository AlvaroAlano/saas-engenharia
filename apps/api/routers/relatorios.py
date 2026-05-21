import io
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fpdf import FPDF

# Importa o cliente do Supabase seguro (o mesmo usado no main.py)
from supabase import Client
from dependencies import get_authenticated_supabase

router = APIRouter(prefix="/api/projetos", tags=["Relatorios"])

class PDFProposta(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'Proposta Comercial - Orcamento de Obra', ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-30)
        self.set_font('helvetica', 'I', 10)
        
        # Linha para assinatura centralizada
        largura_linha = 80
        margem_esq = (self.w - largura_linha) / 2
        self.line(margem_esq, self.get_y(), margem_esq + largura_linha, self.get_y())
        
        self.cell(0, 10, 'Engenheiro Responsavel', ln=True, align='C')
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

@router.get("/{projeto_id}/pdf-comercial")
def gerar_pdf_comercial(
    projeto_id: str,
    supabase_client: Client = Depends(get_authenticated_supabase)
):
    """
    Gera PDF de proposta comercial com BDI embutido (cliente não vê custo base).
    Roda como `def` (sync) para delegação automática ao thread pool. REF: TODO.md P1.2
    """
    try:
        # 1. Busca os dados do Projeto na tabela unificada
        proj_res = supabase_client.table("projetos_clientes").select("*").eq("id", projeto_id).single().execute()
        if not proj_res.data:
            raise HTTPException(status_code=404, detail="Projeto não encontrado.")
        projeto = proj_res.data

        # 2. Busca a lista de itens vinculados a este Projeto
        itens_res = supabase_client.table("orcamento_itens").select("*").eq("projeto_id", projeto_id).execute()
        itens = itens_res.data or []

        # 3. Lógica Matemática do BDI invisível
        bdi_percentual = float(projeto.get("bdi_padrao") or 0.0)
        fator_bdi = 1 + (bdi_percentual / 100)

        # 4. Desenha o PDF
        pdf = PDFProposta()
        pdf.add_page()

        # Cabeçalho de Informações
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, txt=f"Obra: {projeto.get('titulo_projeto', 'Não informada')}", ln=True)
        cliente_nome = projeto.get('cliente_nome')
        pdf.cell(0, 8, txt=f"Cliente: {cliente_nome if cliente_nome else 'Não informado'}", ln=True)
        data_atual = datetime.now().strftime("%d/%m/%Y")
        pdf.cell(0, 8, txt=f"Data: {data_atual}", ln=True)
        pdf.ln(10)

        # Cabeçalho da Tabela
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(85, 8, "Item/Descricao", border=1)
        pdf.cell(15, 8, "Unid.", border=1, align='C')
        pdf.cell(15, 8, "Qtd.", border=1, align='C')
        pdf.cell(35, 8, "Valor Unit. (R$)", border=1, align='C')
        pdf.cell(35, 8, "Total (R$)", border=1, align='C')
        pdf.ln()

        # Corpo da Tabela
        pdf.set_font("helvetica", '', 10)
        valor_total_proposta = 0

        for item in itens:
            descricao = item.get("descricao", "Item sem nome")
            unidade = item.get("unidade", "un")
            quantidade = float(item.get("quantidade", 0))
            valor_custo = float(item.get("valor_unitario", 0))

            # Aplica o BDI na venda: Regra Ouro (Cliente final não vê o custo puro nem a sigla BDI)
            valor_venda_unitario = valor_custo * fator_bdi
            valor_venda_total = valor_venda_unitario * quantidade
            valor_total_proposta += valor_venda_total

            # Corta strings muito longas para não quebrar o layout da tabela (máx ~45 caracteres)
            pdf.cell(85, 8, descricao[:45], border=1)
            pdf.cell(15, 8, unidade, border=1, align='C')
            pdf.cell(15, 8, f"{quantidade:.2f}", border=1, align='C')
            pdf.cell(35, 8, f"{valor_venda_unitario:.2f}", border=1, align='R')
            pdf.cell(35, 8, f"{valor_venda_total:.2f}", border=1, align='R')
            pdf.ln()

        pdf.ln(5)

        # Valor Total da Proposta (Rodapé da Tabela)
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(150, 10, "Valor Total da Proposta:", border=0, align='R')
        pdf.cell(35, 10, f"R$ {valor_total_proposta:.2f}", border=0, align='R')

        # Output para Byte String em Memória (Não salva no disco)
        pdf_bytes = pdf.output()
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        # Retorna o arquivo binário anexado
        headers = {
            "Content-Disposition": f'attachment; filename="proposta_comercial_{projeto_id}.pdf"'
        }
        return StreamingResponse(buffer, media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao gerar a proposta comercial. Tente novamente.")