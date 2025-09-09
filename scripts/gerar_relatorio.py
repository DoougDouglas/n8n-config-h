from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
# --- NOVAS BIBLIOTECAS PARA QUEBRA DE LINHA ---
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT

import sys
import json
import io

# Importa a biblioteca de gráficos
import matplotlib
matplotlib.use('Agg') # Modo não-interativo
import matplotlib.pyplot as plt

# --- DICIONÁRIO DE REFERÊNCIAS ---
faixas_referencia = {
    "Baixo": {"pitch_min": 87, "pitch_max": 147}, "Barítono": {"pitch_min": 98, "pitch_max": 165},
    "Tenor": {"pitch_min": 131, "pitch_max": 220}, "Contralto": {"pitch_min": 175, "pitch_max": 294},
    "Mezzo-soprano": {"pitch_min": 196, "pitch_max": 349}, "Soprano": {"pitch_min": 262, "pitch_max": 523},
}

# --- FUNÇÕES DE LÓGICA E DESENHO ---

def generate_recommendations(data):
    """Gera dicas personalizadas com base nos dados da análise."""
    recomendacoes = []
    summary = data.get("summary", {})
    hnr = summary.get("hnr_db", 0)
    
    if hnr < 18:
        recomendacoes.append("• Seu HNR (Qualidade Vocal) indica uma voz com bastante soprosidade. Para um som mais 'limpo', foque em exercícios de apoio respiratório e fechamento suave das cordas vocais.")
    elif hnr < 22:
        recomendacoes.append("• Seu HNR (Qualidade Vocal) é bom, mas pode ser melhorado. Para aumentar a clareza e ressonância da sua voz, continue praticando um fluxo de ar constante e bem apoiado em suas notas.")
    else:
        recomendacoes.append("• Seu HNR (Qualidade Vocal) está excelente, indicando uma voz clara, 'limpa' e com ótimo apoio. Continue assim!")
    
    return recomendacoes

def draw_pitch_contour_chart(pitch_data):
    """Cria um gráfico de contorno de afinação."""
    times = [p[0] for p in pitch_data if p[1] is not None]
    frequencies = [p[1] for p in pitch_data if p[1] is not None]
    if not times: return None
    plt.figure(figsize=(7, 2.5)); plt.plot(times, frequencies, color='#2E86C1', linewidth=2)
    plt.title("Contorno da Afinação ao Longo do Tempo", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
    plt.ylabel("Frequência (Hz)", fontsize=10); plt.grid(True, linestyle='--', alpha=0.6)
    plt.ylim(bottom=max(0, min(frequencies) - 20), top=max(frequencies) + 20); plt.tight_layout()
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150); buf.seek(0); plt.close()
    return buf

# --- NOVA FUNÇÃO PARA DESENHAR PARÁGRAFOS COM QUEBRA DE LINHA ---
def draw_paragraph_section(c, y_start, title, content_list, title_color=colors.black):
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(title_color)
    c.drawString(50, y_start, title)
    
    # Prepara o estilo do parágrafo
    styles = getSampleStyleSheet()
    style = styles['BodyText']
    style.fontName = 'Helvetica'
    style.fontSize = 11
    style.leading = 15 # Espaçamento entre linhas
    
    y_line = y_start - 20
    for text_line in content_list:
        p = Paragraph(text_line, style)
        # Calcula a altura necessária e desenha o parágrafo
        w, h = p.wrapOn(c, width - 110, height) # Largura máxima = página - margens
        p.drawOn(c, 60, y_line - h)
        y_line -= (h + 10) # Move a posição Y para baixo
        
    return y_line - 15

# --- SCRIPT PRINCIPAL DE GERAÇÃO DE PDF ---
json_file_path = "/tmp/cursoTutoLMS/py/data_for_report.json"
try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f"Erro ao ler o arquivo de dados: {e}")
    sys.exit(1)

pdf_file = "/tmp/cursoTutoLMS/py/relatorio_vocal.pdf"
c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4
y = height - 110

# Cabeçalho
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, height-60, "🎤 Relatório de Biofeedback Vocal 🎶")
c.line(40, height-80, width-40, height-80)

# Resumo e Classificação
summary = data.get("summary", {})
classificacao = data.get('classificacao', 'Indefinido')
c.setFont("Helvetica-Bold", 12)
c.drawString(50, y, "Resumo da Análise")
c.setFont("Helvetica", 11)
c.drawString(60, y-20, f"• Afinação Média: {round(summary.get('pitch_hz', 0), 2)} Hz (Nota: {summary.get('pitch_note', 'N/A')})")
c.drawString(60, y-40, f"• Intensidade Média: {round(summary.get('intensity_db', 0), 2)} dB")
c.drawString(60, y-60, f"• Qualidade (HNR): {round(summary.get('hnr_db', 0), 2)} dB")
c.drawString(60, y-80, f"• Classificação Sugerida: {classificacao}")
y -= 110

# Gráfico de Contorno de Afinação
pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
if pitch_contour_data:
    chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
    if chart_buffer:
        c.drawImage(ImageReader(chart_buffer), 50, y - 100, width=7*cm, height=2.5*cm)
        y -= 130

# Recomendações Personalizadas
recomendacoes = generate_recommendations(data)
if recomendacoes:
    # Usamos a nova função para desenhar as recomendações, que quebra a linha
    y = draw_paragraph_section(c, y, "Recomendações e Dicas 💡", recomendacoes, colors.HexColor("#E67E22"))

# Notas Finais
c.setFont("Helvetica-Oblique", 10); c.setFillColor(colors.dimgray)
y = 80 # Posição fixa para o rodapé
c.drawCentredString(width/2, y, "Este é um relatório de biofeedback gerado por computador.")
c.drawCentredString(width/2, y-15, "Use-o como uma ferramenta para guiar sua percepção e seus estudos.")

c.save()
print(pdf_file)
