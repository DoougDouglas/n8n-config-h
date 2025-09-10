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
matplotlib.use('Agg') # Modo não-interativo, essencial para rodar no servidor
import matplotlib.pyplot as plt

# --- FUNÇÕES DE LÓGICA E DESENHO ---

def generate_recommendations(data):
    """Gera dicas personalizadas com base nos dados da análise."""
    recomendacoes = []
    summary = data.get("summary", {})
    hnr = summary.get("hnr_db", 0)
    tmf = summary.get("duration_seconds", 0)

    # Apenas dá feedback de HNR para o exercício de sustentação
    if data.get("exercise_type") == "sustentacao_vogal":
        if hnr < 18:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado indica uma voz com bastante soprosidade. Para um som mais 'limpo', foque em exercícios de apoio respiratório e fechamento suave das cordas vocais.")
        elif hnr < 22:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado é bom, mas pode ser melhorado. Para aumentar a clareza e ressonância da sua voz, continue praticando um fluxo de ar constante e bem apoiado em suas notas.")
        else:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado está excelente, indicando uma voz clara e com ótimo apoio. Continue assim!")
    
    # Apenas dá feedback de TMF se o áudio for longo (indicando um teste de resistência)
    if tmf > 10: 
        if tmf < 15:
            recomendacoes.append("• <b>Eficiência Respiratória (TMF):</b> Seu tempo de fonação está um pouco abaixo do esperado para adultos. Pratique exercícios de sustentação para melhorar seu controle do ar.")
        else:
            recomendacoes.append("• <b>Eficiência Respiratória (TMF):</b> Seu tempo de fonação está excelente, demonstrando ótimo controle e apoio respiratório.")

    if not recomendacoes:
        recomendacoes.append("• Análise concluída com sucesso. Continue praticando para acompanhar sua evolução!")
        
    return recomendacoes

def draw_pitch_contour_chart(pitch_data):
    """Cria um gráfico de contorno de afinação."""
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
    """Cria um espectrograma do áudio."""
    try:
        spectrogram = sound.to_spectrogram(); plt.figure(figsize=(10, 3.5))
        sg_db = 10 * np.log10(spectrogram.values)
        plt.imshow(sg_db, cmap='viridis', aspect='auto', origin='lower', extent=[spectrogram.xmin, spectrogram.xmax, spectrogram.ymin, spectrogram.ymax])
        plt.title("Espectrograma (Impressão Digital da Voz)", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
        plt.ylabel("Frequência (Hz)", fontsize=10); plt.ylim(top=4000)
        buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
        return buf
    except Exception: return None

def draw_paragraph(c, y_start, text_list, style):
    """Desenha uma lista de parágrafos e retorna a nova posição Y."""
    y_line = y_start
    for line in text_list:
        p = Paragraph(line, style)
        w, h = p.wrapOn(c, width - 100, height)
        y_line -= (h + 5)
        p.drawOn(c, margin, y_line)
    return y_line

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
y = height - 70

# --- LÓGICA CONDICIONAL ---
exercise_type = data.get('exercise_type', 'sustentacao_vogal')
summary = data.get("summary", {})
classificacao = data.get('classificacao', 'Indefinido')
styles = getSampleStyleSheet()

# CABEÇALHO
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, y, f"🎤 Relatório de Exercício: {exercise_type.replace('_', ' ').title()} 🎶")
y -= 20; c.setStrokeColor(colors.HexColor("#2E86C1")); c.setLineWidth(1)
c.line(40, y, width-40, y); y -= 40

# --- MONTA O PDF DE ACORDO COM O EXERCÍCIO ---
if exercise_type == "escala_5_notas":
    # --- LAYOUT PARA O RELATÓRIO DE ESCALA ---
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Resumo da Análise de Escala"); y -= 15
    style = ParagraphStyle(name='Resumo', fontName='Helvetica', fontSize=11, leading=18)
    resumo_content = [
        f"<b>Extensão Utilizada:</b> De <b>{summary.get('min_pitch_note', 'N/A')}</b> a <b>{summary.get('max_pitch_note', 'N/A')}</b>",
        f"<b>Afinação Média:</b> {round(summary.get('pitch_hz', 0), 2)} Hz",
        f"<b>Estabilidade Média (Desvio Padrão):</b> {round(summary.get('stdev_pitch_hz', 0), 2)} Hz"
    ]
    y = draw_paragraph(c, y, resumo_content, style)
    y -= 20
    
    pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
    if pitch_contour_data:
        chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
        if chart_buffer:
            img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
            img_h = available_width * aspect
            c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
            y -= (img_h + 30)
else: 
    # --- LAYOUT PADRÃO PARA SUSTENTAÇÃO DE VOGAL ---
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Resumo da Análise"); y -= 15
    style = ParagraphStyle(name='Resumo', fontName='Helvetica', fontSize=11, leading=18)
    resumo_content = [
        f"<b>Afinação Média:</b> {round(summary.get('pitch_hz', 0), 2)} Hz (Nota: {summary.get('pitch_note', 'N/A')})",
        f"<b>Estabilidade (Desvio Padrão):</b> {round(summary.get('stdev_pitch_hz', 0), 2)} Hz",
        f"<b>Intensidade Média:</b> {round(summary.get('intensity_db', 0), 2)} dB",
        f"<b>Qualidade (HNR):</b> {round(summary.get('hnr_db', 0), 2)} dB",
        f"<b>Eficiência Respiratória (TMF):</b> {round(summary.get('duration_seconds', 0), 2)} segundos",
        f"<b>Classificação Sugerida:</b> {classificacao}"
    ]
    y = draw_paragraph(c, y, resumo_content, style)
    y -= 20
    
    spectrogram_buffer = draw_spectrogram(sound)
    if spectrogram_buffer:
        img = ImageReader(spectrogram_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
        img_h = available_width * aspect
        c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
        y -= (img_h + 30)

    pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
    if pitch_contour_data:
        chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
        if chart_buffer:
            img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
            img_h = available_width * aspect
            c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
            y -= (img_h + 30)

# Recomendações (comum a todos os relatórios)
recomendacoes = generate_recommendations(data)
if recomendacoes:
    style = ParagraphStyle(name='Recomendacoes', fontName='Helvetica', fontSize=11, leading=15)
    y = draw_paragraph_section(c, y, "Recomendações e Dicas 💡", recomendacoes, colors.HexColor("#E67E22"), style)

c.save()
print(pdf_file)
