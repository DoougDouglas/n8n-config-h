from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import sys
import json
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import parselmouth
import numpy as np

# --- FUNÇÕES DE LÓGICA E DESENHO ---

def generate_recommendations(data):
    recomendacoes = []
    summary = data.get("summary", {})
    hnr = summary.get("hnr_db", 0)
    tmf = summary.get("duration_seconds", 0)

    if hnr < 18:
        recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado indica uma voz com bastante soprosidade. Para um som mais 'limpo', foque em exercícios de apoio respiratório e fechamento suave das cordas vocais.")
    else:
        recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado está excelente, indicando uma voz clara e com bom apoio. Continue o ótimo trabalho!")
    
    if tmf < 12:
        recomendacoes.append("• <b>Eficiência Respiratória (TMF):</b> Seu tempo de fonação está abaixo do esperado. Isso pode indicar falta de apoio respiratório. Pratique exercícios de sustentação de notas para melhorar seu controle do ar.")

    return recomendacoes

def draw_pitch_contour_chart(pitch_data):
    times = [p[0] for p in pitch_data if p[1] is not None]
    frequencies = [p[1] for p in pitch_data if p[1] is not None]
    if not times: return None
    plt.figure(figsize=(10, 3.5)); plt.plot(times, frequencies, color='#2E86C1', linewidth=2)
    plt.title("Contorno da Afinação ao Longo do Tempo", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
    plt.ylabel("Frequência (Hz)", fontsize=10); plt.grid(True, linestyle='--', alpha=0.6)
    plt.ylim(bottom=max(0, min(frequencies) - 20), top=max(frequencies) + 20); plt.tight_layout()
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
    return buf

def draw_spectrogram(sound):
    try:
        spectrogram = sound.to_spectrogram()
        plt.figure(figsize=(10, 3.5))
        sg_db = 10 * np.log10(spectrogram.values)
        plt.imshow(sg_db, cmap='viridis', aspect='auto', origin='lower', extent=[spectrogram.xmin, spectrogram.xmax, spectrogram.ymin, spectrogram.ymax])
        plt.title("Espectrograma (Impressão Digital da Voz)", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
        plt.ylabel("Frequência (Hz)", fontsize=10); plt.ylim(top=4000)
        buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
        return buf
    except Exception: return None

def draw_paragraph_section(c, y_start, title, content_list, title_color=colors.black, style=None):
    c.setFont("Helvetica-Bold", 14); c.setFillColor(title_color); c.drawString(50, y_start, title)
    if not style:
        styles = getSampleStyleSheet(); style = styles['BodyText']
        style.fontName = 'Helvetica'; style.fontSize = 11; style.leading = 15
    y_line = y_start - 20
    for text_line in content_list:
        p = Paragraph(text_line, style); w, h = p.wrapOn(c, width - 100, height)
        p.drawOn(c, 50, y_line - h); y_line -= (h + 10)
    return y_line - 15

# --- SCRIPT PRINCIPAL ---
json_file_path = "/tmp/cursoTutoLMS/py/data_for_report.json"
audio_file_path = "/tmp/cursoTutoLMS/py/audio-aluno.wav"
try:
    with open(json_file_path, 'r', encoding='utf-8') as f: data = json.load(f)
    sound = parselmouth.Sound(audio_file_path)
except Exception as e:
    print(f"Erro ao ler os arquivos: {e}", file=sys.stderr); sys.exit(1)

pdf_file = "/tmp/cursoTutoLMS/py/relatorio_vocal.pdf"
c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4; margin = 50; available_width = width - (2 * margin)
y = height - 110

# Cabeçalho
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, height-60, "🎤 Relatório de Biofeedback Vocal 🎶")
c.line(40, height-80, width-40, height-80)

# Resumo da Análise
summary = data.get("summary", {})
classificacao = data.get('classificacao', 'Indefinido')
styles = getSampleStyleSheet()
style = ParagraphStyle(name='Resumo', parent=styles['BodyText'], fontName='Helvetica', fontSize=11, leading=18)
resumo_content = [
    f"<b>Afinação Média:</b> {round(summary.get('pitch_hz', 0), 2)} Hz (Nota: {summary.get('pitch_note', 'N/A')})",
    f"<b>Estabilidade (Desvio Padrão):</b> {round(summary.get('stdev_pitch_hz', 0), 2)} Hz",
    f"<b>Intensidade Média:</b> {round(summary.get('intensity_db', 0), 2)} dB",
    f"<b>Qualidade (HNR):</b> {round(summary.get('hnr_db', 0), 2)} dB",
    f"<b>Eficiência Respiratória (TMF):</b> {round(summary.get('duration_seconds', 0), 2)} segundos",
    f"<b>Classificação Sugerida:</b> {classificacao}"
]
y = draw_paragraph_section(c, y, "Resumo da Análise", resumo_content, colors.HexColor("#1F618D"), style)

# Gráficos e Explicações
c.showPage(); c.save() # Cria a primeira página
c = canvas.Canvas(pdf_file, pagesize=A4); y = height - 110
c.setFillColor(colors.HexColor("#117A65")); c.setFont("Helvetica-Bold", 14)
c.drawString(50, y, "Análise de Timbre e Projeção")
spectrogram_buffer = draw_spectrogram(sound)
if spectrogram_buffer:
    img = ImageReader(spectrogram_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
    c.drawImage(img, margin, y - 20 - (available_width * aspect), width=available_width, height=(available_width * aspect))
    y -= (available_width * aspect) + 30
    
    explanation_style = ParagraphStyle(name='Explicação', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=12)
    explanation_text = """
    O <b>Espectrograma</b> acima é a "impressão digital" da sua voz, mostrando todas as frequências do seu som. Procure por faixas horizontais de energia: a mais baixa é sua nota fundamental, e as de cima são os harmônicos que dão a "cor" ao seu timbre.
    <br/><br/>
    Cantores profissionais desenvolvem o <b>"Formante do Cantor"</b>, uma concentração de energia na faixa de 2500-3500 Hz (uma faixa amarela/brilhante na parte de cima do gráfico). Isso é o que dá brilho e projeção à voz, permitindo que ela seja ouvida sobre uma orquestra.
    """
    p = Paragraph(explanation_text, explanation_style)
    w, h = p.wrapOn(c, available_width, height)
    p.drawOn(c, margin, y - h); y -= (h + 30)

c.setFillColor(colors.HexColor("#1F618D")); c.setFont("Helvetica-Bold", 14)
c.drawString(50, y, "Análise de Afinação e Estabilidade")
pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
if pitch_contour_data:
    chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
    if chart_buffer:
        img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
        c.drawImage(img, margin, y - 20 - (available_width * aspect), width=available_width, height=(available_width * aspect))
        y -= (available_width * aspect) + 30

# Recomendações
recomendacoes = generate_recommendations(data)
if recomendacoes:
    y = draw_paragraph_section(c, height - 110, "Recomendações e Dicas 💡", recomendacoes, colors.HexColor("#E67E22"))

c.showPage(); c.save()
print(pdf_file)
