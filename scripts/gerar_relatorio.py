from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import sys
import json
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import parselmouth
import numpy as np

# --- FUNÇÕES DE LÓGICA E DESENHO (sem alterações) ---
def generate_recommendations(data):
    # ... (código da função) ...
def draw_pitch_contour_chart(pitch_data):
    # ... (código da função) ...
def draw_spectrogram(sound):
    # ... (código da função) ...

# --- SCRIPT PRINCIPAL DE GERAÇÃO DE PDF (COM LÓGICA CONDICIONAL) ---

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
y = height - 70

# --- INÍCIO DA LÓGICA CONDICIONAL ---
exercise_type = data.get('exercise_type', 'sustentacao_vogal')
summary = data.get("summary", {})
classificacao = data.get('classificacao', 'Indefinido')

# CABEÇALHO (comum a todos os relatórios)
c.setFillColor(colors.HexColor("#2E8C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, y, f"🎤 Relatório de Exercício: {exercise_type.replace('_', ' ').title()} 🎶")
y -= 20; c.setStrokeColor(colors.HexColor("#2E8C1")); c.setLineWidth(1)
c.line(40, y, width-40, y); y -= 40

# MONTA O PDF DE ACORDO COM O EXERCÍCIO
if exercise_type == "escala_5_notas":
    # --- LAYOUT PARA O RELATÓRIO DE ESCALA ---
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Resumo da Análise de Escala")
    y -= 15
    style = ParagraphStyle(name='Resumo', fontName='Helvetica', fontSize=11, leading=18)
    resumo_content = [
        f"<b>Extensão Utilizada:</b> De <b>{summary.get('min_pitch_note', 'N/A')}</b> a <b>{summary.get('max_pitch_note', 'N/A')}</b>",
        f"<b>Afinação Média:</b> {round(summary.get('pitch_hz', 0), 2)} Hz",
        f"<b>Estabilidade Média (Desvio Padrão):</b> {round(summary.get('stdev_pitch_hz', 0), 2)} Hz"
    ]
    for line in resumo_content:
        p = Paragraph(line, style); w, h = p.wrapOn(c, available_width, height)
        y -= (h + 5); p.drawOn(c, margin, y)
    y -= 30
    
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#117A65"))
    c.drawString(margin, y, "Gráfico de Contorno da Afinação")
    y -= 15
    pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
    if pitch_contour_data:
        chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
        if chart_buffer:
            img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
            img_h = available_width * aspect
            c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
            y -= (img_h + 15)
            
else: # PADRÃO: LAYOUT PARA SUSTENTAÇÃO DE VOGAL
    # --- LAYOUT COMPLETO QUE JÁ TEMOS ---
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Resumo da Análise"); y -= 15
    style = ParagraphStyle(name='Resumo', fontName='Helvetica', fontSize=11, leading=18)
    resumo_content = [
        f"<b>Afinação Média:</b> {round(summary.get('pitch_hz', 0), 2)} Hz (Nota: {summary.get('pitch_note', 'N/A')})",
        # ... (resto do resumo da análise de sustentação) ...
    ]
    # ... (resto do código para desenhar o relatório de sustentação) ...
    # (Gráfico de Espectrograma, Contorno, Recomendações, etc.)

c.save()
print(pdf_file)
