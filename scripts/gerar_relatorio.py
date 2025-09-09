from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import sys
import json

# --- INÍCIO DA CORREÇÃO ---
# Agora, o script espera um ÚNICO argumento, que é o texto JSON completo.
if len(sys.argv) != 2:
    print("Erro: O script espera um único argumento contendo os dados em formato JSON.")
    sys.exit(1)

# Carrega todos os dados a partir do texto JSON
data = json.loads(sys.argv[1])
# --- FIM DA CORREÇÃO ---


pdf_file = "/tmp/relatorio_vocal.pdf"
c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4

# --- FUNÇÃO AUXILIAR PARA CRIAR SEÇÕES E NÃO REPETIR CÓDIGO ---
def draw_section(y_start, title, title_color, content_list):
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(title_color)
    c.drawString(50, y_start, title)
    
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    
    y_line = y_start - 20
    for line in content_list:
        c.drawString(60, y_line, line)
        y_line -= 20 # Espaçamento entre linhas
    
    # Retorna a nova posição Y para a próxima seção
    return y_line - 20 # Espaço extra após a seção

# --- ESTRUTURA DO PDF ---

# 1. Cabeçalho
c.setFillColor(colors.HexColor("#2E86C1"))
c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, height-60, "🎤 Relatório Detalhado da Sua Voz 🎶")
c.setStrokeColor(colors.HexColor("#2E86C1"))
c.setLineWidth(2)
c.line(40, height-80, width-40, height-80)

y = height - 120

# 2. Bloco de Afinação (Pitch)
pitch_hz = data.get('pitch_hz', 0)
pitch_note = data.get('pitch_note', 'N/A')
pitch_content = [f"Frequência Média: {round(pitch_hz, 2)} Hz", f"Nota Musical Aproximada: {pitch_note}"]
y = draw_section(y, "Afinação (Pitch)", colors.HexColor("#1F618D"), pitch_content)

# 3. Bloco de Qualidade e Estabilidade Vocal (NOVO!)
jitter = data.get('jitter_percent', 0)
shimmer = data.get('shimmer_percent', 0)
hnr = data.get('hnr_db', 0)
quality_content = [
    f"Jitter (Estabilidade da Afinação): {round(jitter, 3)} %",
    f"Shimmer (Estabilidade do Volume): {round(shimmer, 3)} %",
    f"Relação Harmônico-Ruído (HNR): {round(hnr, 2)} dB"
]
y = draw_section(y, "Qualidade e Estabilidade Vocal", colors.HexColor("#9B59B6"), quality_content)

# Adiciona uma breve explicação para as novas métricas
c.setFont("Helvetica-Oblique", 9)
c.setFillColor(colors.dimgray)
c.drawString(60, y + 5, "Valores baixos de Jitter/Shimmer e altos de HNR geralmente indicam uma voz mais estável e 'limpa'.")
y -= 20

# 4. Bloco de Formantes (Resonância)
f1 = data.get('formant1_hz', 0)
f2 = data.get('formant2_hz', 0)
formant_content = [
    f"Formante 1 (F1): {round(f1, 2)} Hz",
    f"Formante 2 (F2): {round(f2, 2)} Hz"
]
y = draw_section(y, "Formantes (Ressonância)", colors.HexColor("#117A65"), formant_content)


# 5. Classificação Vocal (se ainda for relevante)
# classificacao = data.get('classificacao', 'Não determinada') # Se você ainda for calcular isso
# y = draw_section(y, "Classificação Vocal", colors.HexColor("#E67E22"), [classificacao])


# 6. Observações Finais
c.setFont("Helvetica-Oblique", 11)
c.setFillColor(colors.black)
c.drawString(50, y, "🔎 Este relatório é gerado automaticamente com base no áudio enviado.")
c.drawString(50, y-20, "🎶 Use-o como apoio nos seus estudos de canto.")
c.drawString(50, y-40, "✨ Continue treinando e descubra todo o potencial da sua voz!")

c.showPage()
c.save()
print(pdf_file)
