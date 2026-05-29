import io
from typing import Optional
from fpdf import FPDF

class PDFContrato(FPDF):
    def __init__(self, logo_url: Optional[str] = None, nome_fantasia: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_url = logo_url
        self.nome_fantasia = nome_fantasia

    def header(self):
        has_header_brand = False
        
        if self.logo_url:
            try:
                # Renderiza a logo no canto superior esquerdo (x=10, y=10, h=15 mm)
                self.image(self.logo_url, x=10, y=10, h=15)
                has_header_brand = True
            except Exception as e:
                # Se falhar ao carregar/baixar a imagem, o fallback será o nome fantasia
                pass
                
        if not has_header_brand and self.nome_fantasia:
            # Fallback para Nome Fantasia
            self.set_font('helvetica', 'B', 10)
            self.set_text_color(100, 100, 100) # Cinza sutil institucional
            self.cell(0, 10, self.nome_fantasia.upper(), ln=True, align='L')
            has_header_brand = True

        # Ajusta a posição vertical após a logo ou nome da empresa
        if has_header_brand:
            self.set_y(28)
        else:
            self.set_y(15)

        # Adiciona uma linha divisória elegante (Vercel Aesthetic)
        self.set_draw_color(229, 229, 229) # #e5e5e5
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

def generate_contract_pdf(texto_final: str, logo_url: Optional[str] = None, nome_fantasia: Optional[str] = None) -> bytes:
    """
    Gera um PDF a partir de um texto formatado e retorna os bytes do documento.
    Injeta a logo da empresa ou nome fantasia no cabeçalho como papel timbrado institucional (White-label).
    """
    pdf = PDFContrato(logo_url=logo_url, nome_fantasia=nome_fantasia)
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    pdf.set_text_color(30, 30, 30) # Cinza escuro para melhor legibilidade
    
    # Substituir quebras de linha ou caracteres não-latin1 que possam quebrar a geração
    texto_seguro = texto_final.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 7, txt=texto_seguro)
    
    # Retorna os bytes do PDF
    return pdf.output()
