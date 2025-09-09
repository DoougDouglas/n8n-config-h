from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import sys
import json

# --- INÍCIO DA CORREÇÃO ---
# Corrigimos o caminho para corresponder exatamente onde o arquivo foi salvo
json_file_path = "/tmp/cursoTutoLMS/py/data_for_report.json"
# --- FIM DA CORREÇÃO ---

try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"Erro: O arquivo de dados {json_file_path} não foi encontrado.")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Erro: O arquivo {json_file_path} não contém um JSON válido.")
    sys.exit(1)

pdf_file = "/tmp/cursoTutoLMS/py/relatorio_vocal.pdf"
c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4

def draw_section(y_start, title, title_color, content_list):
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(title_color)
    c.drawString(50, y_start, title)
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    y_line = y_start - 20
    for line in content_list:
        c.drawString(60, y_line, line)
        y_line -= 20
    return y_line - 20

c.setFillColor(colors.HexColor("#2E86C1"))
c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, height-60, "🎤 Relatório Detalhado da Sua Voz 🎶")
c.setStrokeColor(colors.HexColor("#2E86C1"))
c.setLineWidth(2)
c.line(40, height-80, width-40, height-80)

y = height - 120

pitch_hz = data.get('pitch_hz', 0)
pitch_note = data.get('pitch_note', 'N/A')
pitch_content = [f"Frequência Média: {round(pitch_hz, 2)} Hz", f"Nota Musical Aproximada: {pitch_note}"]
y = draw_section(y, "Afinação (Pitch)", colors.HexColor("#1F618D"), pitch_content)

hnr = data.get('hnr_db', 0)
quality_content = [f"Relação Harmônico-Ruído (HNR): {round(hnr, 2)} dB"]
y = draw_section(y, "Qualidade Vocal", colors.HexColor("#9B59B6"), quality_content)
c.setFont("Helvetica-Oblique", 9)
c.setFillColor(colors.dimgray)
c.drawString(60, y + 5, "Valores altos (geralmente > 20 dB) indicam uma voz mais 'limpa', clara e ressonante.")
y -= 20

f1 = data.get('formant1_hz', 0)
f2 = data.get('formant2_hz', 0)
formant_content = [f"Formante 1 (F1): {round(f1, 2)} Hz", f"Formante 2 (F2): {round(f2, 2)} Hz"]
y = draw_section(y, "Formantes (Ressonância)", colors.HexColor("#117A65"), formant_content)

classificacao = data.get('classificacao', 'Não determinada')
y = draw_section(y, "Classificação Vocal", colors.HexColor("#E67E22"), [classificacao])

c.setFont("Helvetica-Oblique", 11)
c.setFillColor(colors.black)
c.drawString(50, y, "🔎 Este relatório é gerado automaticamente com base no áudio enviado.")
c.drawString(50, y-20, "🎶 Use-o como apoio nos seus estudos de canto.")
c.drawString(50, y-40, "✨ Continue treinando e descubra todo o potencial da sua voz!")

c.showPage()
c.save()
print(pdf_file)
