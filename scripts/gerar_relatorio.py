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

# Importa as bibliotecas de análise e gráficos
import parselmouth
import numpy as np
import matplotlib
matplotlib.use('Agg') # Modo não-interativo
import matplotlib.pyplot as plt

# --- FUNÇÕES DE LÓGICA E DESENHO ---

def generate_recommendations(data):
    recomendacoes = []
    summary = data.get("summary", {})
    hnr = summary.get("hnr_db", 0)
    tmf = summary.get("duration_seconds", 0)

    if hnr < 18:
        recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado indica uma voz com bastante soprosidade. Para um som mais 'limpo', foque em exercícios de apoio respiratório e fechamento suave das cordas vocais.")
    elif hnr < 22:
        recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado é bom, mas pode ser melhorado. Para aumentar a clareza e ressonância da sua voz, continue praticando um fluxo de ar constante e bem apoiado em suas notas.")
    else:
        recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado está excelente, indicando uma voz clara e com ótimo apoio. Continue assim!")
    
    if tmf > 5 and tmf < 12: # Só dá feedback de TMF se o áudio for longo o suficiente
        recomendacoes.append("• <b>Eficiência Respiratória (TMF):</b> Seu tempo de fonação está abaixo do esperado. Isso pode indicar falta de apoio respiratório. Pratique exercícios de sustentação de notas para melhorar seu controle do ar e eficiência vocal.")

    return recomendacoes

def draw_pitch_contour_chart(pitch_data):
    times = [p[0] for p in pitch_data if p[1] is not None]
    frequencies = [p[1] for p in pitch_data if p[1] is not None]
    if not times or len(times) < 2: return None
    plt.figure(figsize=(10, 3.5)); plt.plot(times, frequencies, color='#2E86C1', linewidth=2)
    plt.title("Contorno da Afinação ao Longo do Tempo", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
    plt.ylabel("Frequência (Hz)", fontsize=10); plt.grid(True, linestyle='--', alpha=0.6)
    plt.ylim(bottom=max(0, min(frequencies) - 20), top=max(frequencies) + 20); plt.tight_layout()
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
    return buf

def draw_spectrogram(sound):
    try:
        spectrogram = sound.to_spectrogram(); plt.figure(figsize=(10, 3.5))
        sg_db = 10 * np.log10(spectrogram.values)
        plt.imshow(sg_db, cmap='viridis', aspect='auto', origin='lower', extent=[spectrogram.xmin, spectrogram.xmax, spectrogram.ymin, spectrogram.ymax])
        plt.title("Espectrograma (Impressão Digital da Voz)", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
        plt.ylabel("Frequência (Hz)", fontsize=10); plt.ylim(top=4000)
        buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
        return buf
    except Exception: return None

# --- SCRIPT PRINCIPAL DE GERAÇÃO DE PDF (COM LÓGICA MULTI-PÁGINA) ---

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

def check_page_break(y_pos, needed_height):
    """Verifica se há espaço, se não, cria uma nova página e retorna a nova posição Y."""
    if y_pos - needed_height < margin:
        c.showPage(); c.setFont("Helvetica", 11)
        return height - margin
    return y_pos

# --- INÍCIO DA CONSTRUÇÃO DO PDF ---
y = height - 70 # Posição vertical inicial

# 1. Cabeçalho
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, y, "🎤 Relatório de Biofeedback Vocal 🎶"); y -= 20
c.setStrokeColor(colors.HexColor("#2E86C1")); c.setLineWidth(1)
c.line(40, y, width-40, y); y -= 40

# 2. Resumo da Análise
summary = data.get("summary", {}); classificacao = data.get('classificacao', 'Indefinido')
c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
c.drawString(margin, y, "Resumo da Análise"); y -= 15
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
for line in resumo_content:
    p = Paragraph(line, style); w, h = p.wrapOn(c, available_width, height)
    y = check_page_break(y, h); p.drawOn(c, margin, y - h); y -= (h + 5)
y -= 20

# --- INÍCIO DA CORREÇÃO DE TEXTO ---
# 3. Gráfico de Espectrograma e Explicação
height_spectrogram_block = 190 
y = check_page_break(y, height_spectrogram_block)
c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#117A65"))
c.drawString(margin, y, "Análise de Timbre e Projeção"); y -= 15
spectrogram_buffer = draw_spectrogram(sound)
if spectrogram_buffer:
    img = ImageReader(spectrogram_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
    img_h = available_width * aspect
    c.drawImage(img, margin, y - img_h, width=available_width, height=img_h); y -= (img_h + 15)
    
    explanation_style = ParagraphStyle(name='Explicação', parent=styles['BodyText'], fontName='Helvetica-Oblique', fontSize=10, leading=12)
    # SUBSTITUÍDO O TEXTO DO RASCUNHO PELO TEXTO COMPLETO
    explanation_text = """
    O <b>Espectrograma</b> acima é a "impressão digital" da sua voz, mostrando todas as frequências do seu som. Procure por faixas horizontais de energia: a mais baixa é sua nota fundamental, e as de cima são os harmônicos que dão a "cor" ao seu timbre.
    <br/><br/>
    Cantores profissionais desenvolvem o <b>"Formante do Cantor"</b>, uma concentração de energia na faixa de 2500-3500 Hz (uma faixa amarela/brilhante na parte de cima do gráfico). Isso é o que dá brilho e projeção à voz, permitindo que ela seja ouvida sobre uma orquestra.
    """
    p = Paragraph(explanation_text, explanation_style); w, h = p.wrapOn(c, available_width, height)
    p.drawOn(c, margin, y - h); y -= (h + 25)
# --- FIM DA CORREÇÃO DE TEXTO ---

# 4. Gráfico de Contorno de Afinação
height_pitch_block = 170
y = check_page_break(y, height_pitch_block)
c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
c.drawString(margin, y, "Análise de Afinação e Estabilidade"); y -= 15
pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
if pitch_contour_data:
    chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
    if chart_buffer:
        img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
        img_h = available_width * aspect
        c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
        y -= (img_h + 25)

# 5. Recomendações e Dicas
recomendacoes = generate_recommendations(data)
if recomendacoes:
    style = ParagraphStyle(name='Recomendações', parent=styles['BodyText'], fontName='Helvetica', fontSize=11, leading=15)
    # Mede a altura necessária para as recomendações
    p_list = [Paragraph(line, style) for line in recomendacoes]
    total_h = sum([p.wrapOn(c, available_width, height)[1] for p in p_list]) + len(p_list)*10
    y = check_page_break(y, total_h + 40)
    
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#E67E22"))
    c.drawString(margin, y, "Recomendações e Dicas 💡"); y -= 15
    for p in p_list:
        w, h = p.wrapOn(c, available_width, height)
        p.drawOn(c, margin, y - h); y -= (h + 10)

# Finaliza e salva o PDF
c.save()
print(pdf_file)
