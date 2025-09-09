from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
import sys
import json
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import parselmouth
import numpy as np

def generate_recommendations(data):
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

def draw_paragraph_section(c, y_start, title, content_list, title_color=colors.black):
    c.setFont("Helvetica-Bold", 14); c.setFillColor(title_color); c.drawString(50, y_start, title)
    styles = getSampleStyleSheet(); style = styles['BodyText']
    style.fontName = 'Helvetica'; style.fontSize = 11; style.leading = 15
    y_line = y_start - 20
    for text_line in content_list:
        p = Paragraph(text_line, style); w, h = p.wrapOn(c, width - 100, height)
        p.drawOn(c, 50, y_line - h); y_line -= (h + 10)
    return y_line - 15

# --- SCRIPT PRINCIPAL DE GERAÇÃO DE PDF ---
json_file_path = "/tmp/cursoTutoLMS/py/data_for_report.json"
audio_file_path = "/tmp/cursoTutoLMS/py/audio-aluno.wav"

try:
    with open(json_file_path, 'r', encoding='utf-8') as f: data = json.load(f)
    sound = parselmouth.Sound(audio_file_path)
except Exception as e:
    print(f"Erro ao ler os arquivos de dados ou áudio: {e}", file=sys.stderr); sys.exit(1)

pdf_file = "/tmp/cursoTutoLMS/py/relatorio_vocal.pdf"
c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4
y = height - 110; margin = 50; available_width = width - (2 * margin)

# Cabeçalho
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, height-60, "🎤 Relatório de Biofeedback Vocal 🎶")
c.line(40, height-80, width-40, height-80)

# --- SEÇÃO DE RESUMO COM NOVA FORMATAÇÃO E MÉTRICA ---
summary = data.get("summary", {})
classificacao = data.get('classificacao', 'Indefinido')

c.setFont("Helvetica-Bold", 14)
c.setFillColor(colors.HexColor("#1F618D"))
c.drawString(50, y, "Resumo da Análise")

styles = getSampleStyleSheet()
style = styles['BodyText']
style.fontName = 'Helvetica'
style.fontSize = 11
style.leading = 18

resumo_content = [
    f"<b>Afinação Média:</b> {round(summary.get('pitch_hz', 0), 2)} Hz (Nota: {summary.get('pitch_note', 'N/A')})",
    f"<b>Estabilidade da Afinação (Desvio Padrão):</b> {round(summary.get('stdev_pitch_hz', 0), 2)} Hz",
    f"<b>Intensidade Média:</b> {round(summary.get('intensity_db', 0), 2)} dB",
    f"<b>Qualidade (HNR):</b> {round(summary.get('hnr_db', 0), 2)} dB",
    f"<b>Classificação Sugerida:</b> {classificacao}"
]
y_line = y - 20
for line in resumo_content:
    p = Paragraph(line, style)
    w, h = p.wrapOn(c, available_width, height)
    p.drawOn(c, margin, y_line - h)
    y_line -= h + 5
y = y_line - 25

# Gráficos 
spectrogram_buffer = draw_spectrogram(sound)
if spectrogram_buffer:
    img = ImageReader(spectrogram_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
    c.drawImage(img, margin, y - (available_width * aspect), width=available_width, height=(available_width * aspect), preserveAspectRatio=True, anchor='c')
    y -= (available_width * aspect) + 30

pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
if pitch_contour_data:
    chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
    if chart_buffer:
        img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
        c.drawImage(img, margin, y - (available_width * aspect), width=available_width, height=(available_width * aspect), preserveAspectRatio=True, anchor='c')
        y -= (available_width * aspect) + 30

recomendacoes = generate_recommendations(data)
if recomendacoes:
    y = draw_paragraph_section(c, y, "Recomendações e Dicas 💡", recomendacoes, colors.HexColor("#E67E22"))

# Notas Finais
c.setFont("Helvetica-Oblique", 10); c.setFillColor(colors.dimgray)
c.drawCentredString(width/2, 60, "Este é um relatório de biofeedback gerado por computador.")
c.drawCentredString(width/2, 45, "Use-o como uma ferramenta para guiar sua percepção e seus estudos.")

c.save()
print(pdf_file)
