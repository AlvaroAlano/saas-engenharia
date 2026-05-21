import io
from fpdf import FPDF

class PDFContrato(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Contrato de Prestacao de Servicos', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

def generate_contract_pdf(texto_final: str) -> bytes:
    """
    Gera um PDF a partir de um texto formatado e retorna os bytes do documento.
    """
    pdf = PDFContrato()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 10, txt=texto_final)
    
    # Retorna os bytes do PDF
    return pdf.output()
