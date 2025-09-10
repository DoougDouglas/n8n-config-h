from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
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
    """Gera dicas personalizadas com base nos dados e no tipo de exercício."""
    recomendacoes = []
    summary = data.get("summary", {})
    exercise_type = data.get("exercise_type", "")
    
    if exercise_type == "sustentacao_vogal":
        hnr = summary.get("hnr_db", 0)
        if hnr < 18:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado indica uma voz com bastante soprosidade. Para um som mais 'limpo', foque em exercícios de apoio respiratório e fechamento suave das cordas vocais.")
        elif hnr < 22:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado é bom, mas pode ser melhorado. Para aumentar a clareza, continue praticando um fluxo de ar constante e bem apoiado.")
        else:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado está excelente, indicando uma voz clara e com ótimo apoio!")

    if exercise_type == "resistencia_tmf":
        tmf = summary.get("duration_seconds", 0)
        if tmf < 15:
            recomendacoes.append("• <b>Eficiência Respiratória (TMF):</b> Seu tempo de fonação está abaixo da média para adultos (15-25s). Pratique exercícios de respiração diafragmática e sustentação de notas para melhorar seu controle do ar.")
        else:
            recomendacoes.append("• <b>Eficiência Respiratória (TMF):</b> Seu tempo de fonação está excelente, demonstrando ótimo controle e apoio respiratório.")

    if exercise_type == "teste_vogais":
        recomendacoes.append("• <b>Clareza da Dicção:</b> Observe no gráfico se suas vogais estão bem definidas e separadas. Um 'triângulo vocálico' (entre A, I, U) amplo indica uma articulação clara e ressonante.")

    if not recomendacoes:
        recomendacoes.append("• Análise concluída com sucesso. Continue praticando para acompanhar sua evolução!")
        
    return recomendacoes

def draw_pitch_contour_chart(pitch_data):
    # (Função do gráfico sem alterações)
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
    # (Função do espectrograma sem alterações)
    try:
        spectrogram = sound.to_spectrogram(); plt.figure(figsize=(10, 3.5))
        sg_db = 10 * np.log10(spectrogram.values)
        plt.imshow(sg_db, cmap='viridis', aspect='auto', origin='lower', extent=[spectrogram.xmin, spectrogram.xmax, spectrogram.ymin, spectrogram.ymax])
        plt.title("Espectrograma (Impressão Digital da Voz)", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
        plt.ylabel("Frequência (Hz)", fontsize=10); plt.ylim(top=4000)
        buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
        return buf
    except Exception: return None

def draw_vowel_space_chart(vowel_data):
    """Cria um gráfico F1 vs F2 do espaço vocálico."""
    vogais = ['a', 'e', 'i', 'o', 'u']
    f1_vals = [vowel_data.get(v, {}).get('f1') for v in vogais]
    f2_vals = [vowel_data.get(v, {}).get('f2') for v in vogais]
    
    # Verifica se temos dados para todas as vogais
    if any(v is None for v in f1_vals) or any(v is None for v in f2_vals): return None

    plt.figure(figsize=(6, 6))
    plt.scatter(f2_vals, f1_vals, s=100, c='#2E86C1', zorder=10)
    for i, txt in enumerate(vogais):
        plt.annotate(txt.upper(), (f2_vals[i] + 30, f1_vals[i] + 10), fontsize=12, fontweight='bold')
        
    # Desenha o triângulo vocálico (A-I-U)
    triangle_f2 = [f2_vals[0], f2_vals[2], f2_vals[4], f2_vals[0]]
    triangle_f1 = [f1_vals[0], f1_vals[2], f1_vals[4], f1_vals[0]]
    plt.plot(triangle_f2, triangle_f1, color='lightgray', linestyle='--', zorder=5)

    plt.xlabel("Formante 2 (F2) - Anterioridade da Língua →"); plt.ylabel("Formante 1 (F1) - Altura da Língua →")
    plt.title("Mapa do Seu Espaço Vocálico", fontsize=14); plt.grid(True, linestyle='--', alpha=0.5)
    
    # Inverte os eixos para corresponder à convenção fonética (importante!)
    plt.gca().invert_xaxis(); plt.gca().invert_yaxis()
    
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150); buf.seek(0); plt.close()
    return buf

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

exercise_type = data.get('exercise_type', 'sustentacao_vogal')
summary = data.get("summary", {})
classificacao = data.get('classificacao', 'Indefinido')
styles = getSampleStyleSheet()

# --- CABEÇALHO DINÂMICO ---
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, y, f"🎤 Relatório de Exercício: {exercise_type.replace('_', ' ').title()} 🎶")
y -= 20; c.line(40, y, width-40, y); y -= 40

# --- LÓGICA PARA MONTAR O PDF CORRETO ---
if exercise_type == "teste_vogais":
    # --- LAYOUT PARA O RELATÓRIO DE VOGAIS ---
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Análise de Clareza e Dicção")
    y -= 15
    
    vowel_chart_buffer = draw_vowel_space_chart(data.get("vowel_space_data", {}))
    if vowel_chart_buffer:
        img_h = available_width * 0.9 # Gráfico quase quadrado
        c.drawImage(ImageReader(vowel_chart_buffer), margin, y - img_h, width=available_width, height=img_h, preserveAspectRatio=True, anchor='n')
        y -= (img_h + 15)
    
    style = ParagraphStyle(name='Explicação', parent=styles['BodyText'], fontName='Helvetica-Oblique', fontSize=10, leading=12)
    explanation_text = "Este gráfico é o 'mapa' das suas vogais. Quanto mais distantes os pontos A, I e U estiverem (maior a área do triângulo), mais clara e distinta é a sua articulação."
    p = Paragraph(explanation_text, style); w, h = p.wrapOn(c, available_width, height)
    p.drawOn(c, margin, y - h); y -= (h + 30)

elif exercise_type == "resistencia_tmf":
    # --- LAYOUT PARA O RELATÓRIO DE RESISTÊNCIA ---
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Resumo da Análise de Resistência")
    y -= 15
    style = ParagraphStyle(name='Resumo', fontName='Helvetica', fontSize=12, leading=20)
    resumo_content = [
        f"<b>Tempo Máximo de Fonação (TMF):</b> {round(summary.get('duration_seconds', 0), 2)} segundos",
        f"<b>Estabilidade Média (Desvio Padrão):</b> {round(summary.get('stdev_pitch_hz', 0), 2)} Hz (quanto menor, mais estável)"
    ]
    for line in resumo_content:
        p = Paragraph(line, style); w, h = p.wrapOn(c, available_width, height)
        y -= (h + 5); p.drawOn(c, margin, y)
    y -= 30
    
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#117A65"))
    c.drawString(margin, y, "Estabilidade da Afinação Durante o Exercício")
    y -= 15
    pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
    if pitch_contour_data:
        # ... (código para desenhar o gráfico de contorno) ...

else: # PADRÃO: LAYOUT PARA SUSTENTAÇÃO DE VOGAL (QUALIDADE)
    # --- LAYOUT COMPLETO QUE JÁ TEMOS ---
    # ... (código completo do relatório de qualidade, com resumo, espectrograma, contorno e recomendações) ...

# Recomendações (comum a todos os relatórios)
recomendacoes = generate_recommendations(data)
if recomendacoes:
    y -= 20
    style = ParagraphStyle(name='Recomendacoes', parent=styles['BodyText'], fontName='Helvetica', fontSize=11, leading=15)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#E67E22"))
    c.drawString(margin, y, "Recomendações e Dicas 💡"); y -= 15
    for text_line in recomendacoes:
        p = Paragraph(text_line, style); w, h = p.wrapOn(c, available_width, height)
        p.drawOn(c, margin, y - h); y -= (h + 10)

c.save()
print(pdf_file)
