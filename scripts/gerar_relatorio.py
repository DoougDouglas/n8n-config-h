from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import sys
import json

# --- DICIONÁRIO COM FAIXAS DE REFERÊNCIA PARA COMPARAÇÃO ---
faixas_referencia = {
    "Baixo": {"pitch_hz": "87 - 147 Hz", "pitch_note": "F2 - D3", "hnr_db": "> 20 dB"},
    "Barítono": {"pitch_hz": "98 - 165 Hz", "pitch_note": "G2 - F3", "hnr_db": "> 20 dB"},
    "Tenor": {"pitch_hz": "131 - 220 Hz", "pitch_note": "C3 - A3", "hnr_db": "> 20 dB"},
    "Contralto": {"pitch_hz": "175 - 294 Hz", "pitch_note": "F3 - D4", "hnr_db": "> 20 dB"},
    "Mezzo-soprano": {"pitch_hz": "196 - 349 Hz", "pitch_note": "G3 - F4", "hnr_db": "> 20 dB"},
    "Soprano": {"pitch_hz": "262 - 523 Hz", "pitch_note": "C4 - C5", "hnr_db": "> 20 dB"},
    "Indefinido": {"pitch_hz": "N/A", "pitch_note": "N/A", "hnr_db": "> 20 dB"}
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
y = height - 120 # Posição vertical inicial

# --- FUNÇÕES DE DESENHO ---
def draw_header():
    c.setFillColor(colors.HexColor("#2E86C1"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height-60, "🎤 Relatório Detalhado da Sua Voz 🎶")
    c.setStrokeColor(colors.HexColor("#2E86C1"))
    c.setLineWidth(2)
    c.line(40, height-80, width-40, height-80)

def draw_table_section(y_start, title, title_color, headers, rows):
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(title_color)
    c.drawString(50, y_start, title)
    y_line = y_start - 25

    # Desenha cabeçalhos da tabela
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.dimgray)
    c.drawString(60, y_line, headers[0])
    c.drawString(250, y_line, headers[1])
    c.drawString(420, y_line, headers[2])
    y_line -= 5
    c.line(50, y_line, width-50, y_line)
    y_line -= 15

    # Desenha linhas da tabela
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    for row_title, user_val, ref_val in rows:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y_line, row_title)
        c.setFont("Helvetica", 11)
        c.drawString(250, y_line, str(user_val))
        c.drawString(420, y_line, str(ref_val))
        y_line -= 20
        
    return y_line

# --- CONSTRUÇÃO DO PDF ---
draw_header()
classificacao = data.get('classificacao', 'Indefinido')
referencia = faixas_referencia.get(classificacao, faixas_referencia["Indefinido"])

# Bloco de Afinação e Qualidade
headers = ["Métrica", "Sua Voz", "Referência"]
pitch_rows = [
    ("Afinação", f"{round(data.get('pitch_hz', 0), 2)} Hz", referencia["pitch_hz"]),
    ("Nota Aprox.", data.get('pitch_note', 'N/A'), referencia["pitch_note"])
]
y = draw_table_section(y, "Afinação (Pitch)", colors.HexColor("#1F618D"), headers, pitch_rows)
y += 10 # Reduz espaço

quality_rows = [
    ("Qualidade (HNR)", f"{round(data.get('hnr_db', 0), 2)} dB", referencia["hnr_db"]),
    ("Intensidade Média", f"{round(data.get('intensity_db', 0), 2)} dB", "70-80 dB (fala)")
]
y = draw_table_section(y, "Qualidade e Intensidade", colors.HexColor("#9B59B6"), headers, quality_rows)


# Bloco de Formantes
formant_rows = [
    ("Formante 1 (F1)", f"{round(data.get('formant1_hz', 0), 2)} Hz", "Varia (vogal)"),
    ("Formante 2 (F2)", f"{round(data.get('formant2_hz', 0), 2)} Hz", "Varia (vogal)")
]
y = draw_table_section(y, "Formantes (Ressonância)", colors.HexColor("#117A65"), headers, formant_rows)


# Bloco de Classificação e Notas Finais
c.setFont("Helvetica-Bold", 16)
c.setFillColor(colors.HexColor("#E67E22"))
c.drawString(50, y-20, f"Classificação Vocal Sugerida: {classificacao}")

c.setFont("Helvetica-Oblique", 11)
c.setFillColor(colors.black)
y -= 60
c.drawString(50, y, "🔎 Este relatório é gerado automaticamente com base no áudio enviado.")
c.drawString(50, y-20, "🎶 Use-o como apoio nos seus estudos de canto.")
c.drawString(50, y-40, "✨ Continue treinando e descubra todo o potencial da sua voz!")

c.save()
print(pdf_file)
