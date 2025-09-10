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
    # (Função de recomendações sem alterações)
    recomendacoes = []
    summary = data.get("summary", {})
    hnr = summary.get("hnr_db", 0)
    if hnr < 18:
        recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado indica uma voz com bastante soprosidade. Para um som mais 'limpo', foque em exercícios de apoio respiratório e fechamento suave das cordas vocais.")
    elif hnr < 22:
        recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado é bom, mas pode ser melhorado. Para aumentar a clareza e ressonância da sua voz, continue praticando um fluxo de ar constante e bem apoiado em suas notas.")
    else:
        recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado está excelente, indicando uma voz clara, 'limpa' e com ótimo apoio. Continue assim!")
    return recomendacoes

def draw_pitch_contour_chart(pitch_data):
    # (Função de gráfico sem alterações)
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
    # (Função de espectrograma sem alterações)
    try:
        spectrogram = sound.to_spectrogram(); plt.figure(figsize=(10, 3.5))
        sg_db = 10 * np.log10(spectrogram.values)
        plt.imshow(sg_db, cmap='viridis', aspect='auto', origin='lower', extent=[spectrogram.xmin, spectrogram.xmax, spectrogram.ymin, spectrogram.ymax])
        plt.title("Espectrograma (Impressão Digital da Voz)", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
        plt.ylabel("Frequência (Hz)", fontsize=10); plt.ylim(top=4000)
        buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
        return buf
    except Exception: return None

# --- SCRIPT PRINCIPAL DE GERAÇÃO DE PDF ---
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

# --- PÁGINA 1: DADOS PRINCIPAIS E GRÁFICOS ---

y = height - 70 # Posição vertical inicial

# Cabeçalho
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, y, "🎤 Relatório de Biofeedback Vocal 🎶"); y -= 20
c.setStrokeColor(colors.HexColor("#2E86C1")); c.setLineWidth(1)
c.line(40, y, width-40, y); y -= 40

# Resumo da Análise
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
    p.drawOn(c, margin, y - h); y -= (h + 5)
y -= 20

# Gráfico de Espectrograma e Explicação
c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#117A65"))
c.drawString(margin, y, "Análise de Timbre e Projeção"); y -= 15
spectrogram_buffer = draw_spectrogram(sound)
if spectrogram_buffer:
    img = ImageReader(spectrogram_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
    img_h = available_width * aspect
    c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
    y -= (img_h + 15)
    
    # --- TEXTO EXPLICATIVO DO ESPECTROGRAMA (REINSERIDO) ---
    explanation_style = ParagraphStyle(name='Explicação', parent=styles['BodyText'], fontName='Helvetica-Oblique', fontSize=10, leading=12)
    explanation_text = """O <b>Espectrograma</b> acima é a "impressão digital" da sua voz. Procure por faixas de energia horizontais: a mais baixa é sua nota, e as de cima são os harmônicos que dão "cor" ao seu timbre. Cantores profissionais desenvolvem o <b>"Formante do Cantor"</b>, uma concentração de energia na faixa de 2500-3500 Hz (uma faixa amarela/brilhante), que dá brilho e projeção à voz."""
    p = Paragraph(explanation_text, explanation_style); w, h = p.wrapOn(c, available_width, height)
    p.drawOn(c, margin, y - h); y -= (h + 25)

# Gráfico de Contorno de Afinação
c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
c.drawString(margin, y, "Análise de Afinação e Estabilidade"); y -= 15
pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
if pitch_contour_data:
    chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
    if chart_buffer:
        img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
        img_h = available_width * aspect
        c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
        y -= (img_h + 15)
        
        # --- NOVA EXPLICAÇÃO DO GRÁFICO DE CONTORNO ---
        explanation_style.fontName = 'Helvetica-Oblique'
        explanation_text = """Este gráfico mostra sua afinação segundo a segundo. Uma linha <b>mais reta</b> indica uma nota muito estável. Ondulações suaves e regulares podem indicar um <b>vibrato</b> controlado. Linhas muito irregulares sugerem instabilidade na sustentação."""
        p = Paragraph(explanation_text, explanation_style); w, h = p.wrapOn(c, available_width, height)
        p.drawOn(c, margin, y - h); y -= (h + 25)

c.showPage() # Finaliza a primeira página

# --- PÁGINA 2: RECOMENDAÇÕES E GLOSSÁRIO ---
y = height - 70

# Recomendações
recomendacoes = generate_recommendations(data)
if recomendacoes:
    style = ParagraphStyle(name='Recomendacoes', parent=styles['BodyText'], fontName='Helvetica', fontSize=11, leading=15)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#E67E22"))
    c.drawString(margin, y, "Recomendações e Dicas 💡"); y -= 15
    for text_line in recomendacoes:
        p = Paragraph(text_line, style); w, h = p.wrapOn(c, available_width, height)
        p.drawOn(c, margin, y - h); y -= (h + 10)
    y -= 25

# --- NOVO GLOSSÁRIO DE MÉTRICAS ---
c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.darkslategray)
c.drawString(margin, y, "Glossário: Entendendo Suas Métricas"); y -= 15
style = ParagraphStyle(name='Glossario', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=14)
glossario_content = [
    "<b>Afinação Média (Hz):</b> A nota musical central que você cantou, medida em Hertz.",
    "<b>Estabilidade (Desvio Padrão):</b> Mede o quanto sua afinação variou. Quanto menor o número, mais estável e firme foi sua nota.",
    "<b>Intensidade Média (dB):</b> O volume médio da sua voz. Ajuda a medir a projeção e energia.",
    "<b>Qualidade (HNR):</b> 'Harmonics-to-Noise Ratio'. Mede a 'pureza' do som. Valores altos indicam uma voz 'limpa', com pouco ruído ou soprosidade.",
    "<b>Eficiência Respiratória (TMF):</b> 'Tempo Máximo de Fonação'. Mede por quantos segundos você sustentou o som, indicando seu controle do fluxo de ar.",
    "<b>Formantes (F1, F2):</b> Picos de ressonância que definem o som das vogais. São essenciais para a clareza da dicção."
]
for line in glossario_content:
    p = Paragraph(line, style); w, h = p.wrapOn(c, available_width, height)
    p.drawOn(c, margin, y - h); y -= (h + 8)

c.save()
print(pdf_file)
