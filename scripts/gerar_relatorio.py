from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
import sys
import json

# --- DICIONÁRIO COM FAIXAS DE REFERÊNCIA NUMÉRICAS PARA OS GRÁFICOS ---
faixas_referencia_grafico = {
    "Baixo": {"pitch_min": 87, "pitch_max": 147},
    "Barítono": {"pitch_min": 98, "pitch_max": 165},
    "Tenor": {"pitch_min": 131, "pitch_max": 220},
    "Contralto": {"pitch_min": 175, "pitch_max": 294},
    "Mezzo-soprano": {"pitch_min": 196, "pitch_max": 349},
    "Soprano": {"pitch_min": 262, "pitch_max": 523},
}

# --- SCRIPT DE GERAÇÃO DE PDF ---

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

# --- FUNÇÕES DE DESENHO CORRIGIDAS ---

def draw_header():
    c.setFillColor(colors.HexColor("#2E86C1"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height-60, "🎤 Relatório Detalhado da Sua Voz 🎶")
    c.setStrokeColor(colors.HexColor("#2E86C1"))
    c.setLineWidth(2)
    c.line(40, height-80, width-40, height-80)

def draw_gauge_chart(y_start, label, value, min_val, max_val, ideal_min, ideal_max, unit=""):
    """Desenha um gráfico de medidor horizontal com alinhamento corrigido."""
    chart_width = width - 250  # Diminui um pouco a largura para mais margem
    chart_x_start = 200
    chart_x_end = chart_x_start + chart_width
    chart_y = y_start

    def normalize(val, min_v, max_v):
        # Garante que o valor não saia dos limites do gráfico
        val = max(min_v, min(val, max_v))
        return chart_x_start + ((val - min_v) / (max_v - min_v)) * chart_width

    # Desenha a barra de fundo
    c.setFillColor(colors.lightgrey)
    c.rect(chart_x_start, chart_y, chart_width, 15, stroke=0, fill=1)

    # Desenha a barra da faixa ideal
    ideal_x_start = normalize(ideal_min, min_val, max_val)
    ideal_x_end = normalize(ideal_max, min_val, max_val)
    c.setFillColor(colors.HexColor("#A9DFBF")) # Verde claro
    c.rect(ideal_x_start, chart_y, ideal_x_end - ideal_x_start, 15, stroke=0, fill=1)
    
    # Desenha o marcador do valor do usuário
    marker_x = normalize(value, min_val, max_val)
    c.setFillColor(colors.HexColor("#2E86C1")) # Azul para o marcador
    c.rect(marker_x - 1.5, chart_y - 4, 3, 23, stroke=0, fill=1) # Marcador mais grosso
    
    # Escreve os textos com alinhamento corrigido
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawString(50, chart_y + 3, label)
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.dimgray)
    c.drawString(chart_x_start, chart_y - 12, str(min_val))
    c.drawRightString(chart_x_end, chart_y - 12, str(max_val))
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#1F618D"))
    c.drawCentredString(marker_x, chart_y - 25, f"{round(value, 2)} {unit}")
    
    return y_start - 60 # Retorna a nova posição Y com mais espaçamento

# --- CONSTRUÇÃO DO PDF ---
draw_header()
y = height - 120
classificacao = data.get('classificacao', 'Indefinido')
referencia = faixas_referencia_grafico.get(classificacao, {"pitch_min": 75, "pitch_max": 600})

# Bloco de Afinação
c.setFont("Helvetica-Bold", 14)
c.setFillColor(colors.HexColor("#1F618D"))
c.drawString(50, y, "Afinação (Pitch)")
c.setFont("Helvetica", 12)
c.setFillColor(colors.black)
c.drawString(60, y-20, f"Nota Musical Aproximada: {data.get('pitch_note', 'N/A')}")
y -= 45
y = draw_gauge_chart(y, "Frequência (Hz):", data.get('pitch_hz', 0), 
                     referencia["pitch_min"] - 20, referencia["pitch_max"] + 20, 
                     referencia["pitch_min"], referencia["pitch_max"])

# Bloco de Qualidade e Intensidade
c.setFont("Helvetica-Bold", 14)
c.setFillColor(colors.HexColor("#9B59B6"))
c.drawString(50, y, "Qualidade e Intensidade Vocal")
y -= 25
y = draw_gauge_chart(y, "Qualidade (HNR):", data.get('hnr_db', 0), 0, 40, 20, 40, "dB")
y = draw_gauge_chart(y, "Intensidade Média:", data.get('intensity_db', 0), 50, 100, 70, 85, "dB")
y -= 10 # Espaço extra

# Bloco de Formantes
c.setFont("Helvetica-Bold", 14)
c.setFillColor(colors.HexColor("#117A65"))
c.drawString(50, y, "Formantes (Ressonância)")
c.setFont("Helvetica", 12)
c.setFillColor(colors.black)
c.drawString(60, y-20, f"Formante 1 (F1): {round(data.get('formant1_hz', 0), 2)} Hz")
c.drawString(60, y-40, f"Formante 2 (F2): {round(data.get('formant2_hz', 0), 2)} Hz")
y -= 60

# Bloco de Classificação e Notas Finais
c.setFont("Helvetica-Bold", 16)
c.setFillColor(colors.HexColor("#E67E22"))
c.drawString(50, y, f"Classificação Vocal Sugerida: {classificacao}")
y -= 40
c.setFont("Helvetica-Oblique", 11)
c.setFillColor(colors.black)
c.drawString(50, y, "🔎 Este relatório é gerado automaticamente com base no áudio enviado.")
c.drawString(50, y-20, "🎶 Use-o como apoio nos seus estudos de canto.")
c.drawString(50, y-40, "✨ Continue treinando e descubra todo o potencial da sua voz!")

c.save()
print(pdf_file)
