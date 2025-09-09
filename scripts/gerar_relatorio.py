from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import sys

# --- INÍCIO DA CORREÇÃO ---
# Removemos a linha antiga e adicionamos este bloco.
# Ele lê os 4 argumentos vindos do n8n e monta o dicionário 'data'.

if len(sys.argv) != 5:
    print("Erro: O script espera 4 argumentos: pitch_hz, formant1, formant2, classificacao")
    sys.exit(1)

data = {
    "pitch_hz": float(sys.argv[1]),
    "formant1": float(sys.argv[2]),
    "formant2": float(sys.argv[3]),
    "classificacao": sys.argv[4]
}
# --- FIM DA CORREÇÃO ---


pdf_file = "/tmp/relatorio_vocal.pdf"
c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4

# Cabeçalho
c.setFillColor(colors.HexColor("#2E86C1"))
c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, height-60, "🎤 Relatório da Sua Voz 🎶")
c.setStrokeColor(colors.HexColor("#2E86C1"))
c.setLineWidth(2)
c.line(40, height-80, width-40, height-80)

y = height - 120

# Pitch
c.setFont("Helvetica-Bold", 14)
c.setFillColor(colors.HexColor("#1F618D"))
c.drawString(50, y, "Frequência Média (Pitch)")
c.setFont("Helvetica", 12)
c.setFillColor(colors.black)
c.drawString(60, y-20, f"{round(data['pitch_hz'],2)} Hz")

# Gráfico de barra
d = Drawing(400, 100)
bc = VerticalBarChart()
bc.x, bc.y, bc.height, bc.width = 50, 10, 80, 300
bc.data = [[data['pitch_hz']]]
bc.valueAxis.valueMin, bc.valueAxis.valueMax, bc.valueAxis.valueStep = 50, 500, 100
bc.categoryAxis.categoryNames = ["Sua Voz"]
bc.bars[0].fillColor = colors.HexColor("#5DADE2")
d.add(bc)
renderPDF.draw(d, c, 100, y-120)
y -= 180

# Formantes
c.setFont("Helvetica-Bold", 14)
c.setFillColor(colors.HexColor("#117A65"))
c.drawString(50, y, "Formantes (Resonância)")
c.setFont("Helvetica", 12)
c.setFillColor(colors.black)
c.drawString(60, y-20, f"Formante 1 (F1): {round(data['formant1'],2)} Hz")
c.drawString(60, y-40, f"Formante 2 (F2): {round(data['formant2'],2)} Hz")
y -= 80

# Classificação Vocal
c.setFont("Helvetica-Bold", 16)
c.setFillColor(colors.HexColor("#E67E22"))
c.drawString(50, y, f"Classificação Vocal: {data['classificacao']}")
y -= 60

# Observações
c.setFont("Helvetica-Oblique", 11)
c.setFillColor(colors.black)
c.drawString(50, y, "🔎 Este relatório é gerado automaticamente com base no áudio enviado.")
c.drawString(50, y-20, "🎶 Use-o como apoio nos seus estudos de canto.")
c.drawString(50, y-40, "✨ Continue treinando e descubra todo o potencial da sua voz!")

c.showPage()
c.save()
print(pdf_file)
