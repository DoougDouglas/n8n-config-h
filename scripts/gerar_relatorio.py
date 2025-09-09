from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import sys
import json
import io

# Importa a biblioteca de gráficos
import matplotlib
matplotlib.use('Agg') # Modo não-interativo, essencial para rodar no servidor
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
        recomendacoes.append("• Seu HNR indica uma voz com bastante soprosidade. Para um som mais 'limpo', foque em exercícios de apoio respiratório e fechamento das cordas vocais.")
    elif hnr < 22:
        recomendacoes.append("• Seu HNR é bom, mas pode ser melhorado. Para aumentar a clareza e ressonância, continue praticando um fluxo de ar constante e bem apoiado.")
    else:
        recomendacoes.append("• Seu HNR está excelente, indicando uma voz clara, 'limpa' e com ótimo apoio. Continue assim!")
    
    # Adicione mais lógicas if/else aqui para outras métricas no futuro
    return recomendacoes

def draw_pitch_contour_chart(pitch_data):
    """Cria um gráfico de contorno de afinação com matplotlib e retorna como uma imagem em memória."""
    times = [p[0] for p in pitch_data if p[1] is not None]
    frequencies = [p[1] for p in pitch_data if p[1] is not None]
    
    if not times: return None

    plt.figure(figsize=(7, 2.5))
    plt.plot(times, frequencies, color='#2E86C1', linewidth=2)
    plt.title("Contorno da Afinação ao Longo do Tempo", fontsize=12)
    plt.xlabel("Tempo (segundos)", fontsize=10)
    plt.ylabel("Frequência (Hz)", fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.ylim(bottom=max(0, min(frequencies) - 20), top=max(frequencies) + 20)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close()
    return buf

def draw_text_section(c, y_start, title, content_list, title_color=colors.black):
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(title_color)
    c.drawString(50, y_start, title)
    y_line = y_start - 10
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    for line in content_list:
        y_line -= 18
        c.drawString(60, y_line, line)
    return y_line - 25


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
referencia = faixas_referencia.get(classificacao, {"pitch_min": 75, "pitch_max": 600})
resumo_content = [
    f"Afinação Média: {round(summary.get('pitch_hz', 0), 2)} Hz (Nota: {summary.get('pitch_note', 'N/A')})",
    f"Intensidade Média: {round(summary.get('intensity_db', 0), 2)} dB",
    f"Qualidade (HNR): {round(summary.get('hnr_db', 0), 2)} dB",
    f"Classificação Sugerida: {classificacao}"
]
y = draw_text_section(c, y, "Resumo da Análise", colors.HexColor("#1F618D"), resumo_content)

# Gráfico de Contorno de Afinação
pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
if pitch_contour_data:
    chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
    if chart_buffer:
        c.drawImage(ImageReader(chart_buffer), 50, y - 100, width=7*cm, height=2.5*cm)
        y -= 130

# Análise de Vibrato
vibrato_info = data.get("vibrato", {})
if vibrato_info.get("is_present"):
    vibrato_content = [
        f"Taxa de Modulação: {round(vibrato_info.get('rate_hz', 0), 2)} Hz (ideal: 5-7 Hz)",
        f"Extensão da Variação: {round(vibrato_info.get('extent_semitones', 0), 2)} semitons"
    ]
    y = draw_text_section(c, y, "Análise de Vibrato", colors.HexColor("#9B59B6"), vibrato_content)

# Recomendações Personalizadas
recomendacoes = generate_recommendations(data)
if recomendacoes:
    y = draw_text_section(c, y, "Recomendações e Dicas 💡", colors.HexColor("#E67E22"), recomendacoes)

# Notas Finais
c.setFont("Helvetica-Oblique", 10); c.setFillColor(colors.dimgray)
c.drawCentredString(width/2, 60, "Este é um relatório de biofeedback gerado por computador.")
c.drawCentredString(width/2, 45, "Use-o como uma ferramenta para guiar sua percepção e seus estudos.")

c.save()
print(pdf_file)
