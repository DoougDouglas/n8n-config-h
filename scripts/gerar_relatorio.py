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
    """Gera dicas personalizadas com base nos dados e no tipo de exercício."""
    recomendacoes = []
    summary = data.get("summary", {})
    exercise_type = data.get("exercise_type", "")
    
    if exercise_type == "sustentacao_vogal":
        hnr = summary.get("hnr_db", 0)
        if hnr < 18:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado indica uma voz com bastante soprosidade. Para um som mais 'limpo', foque em exercícios de apoio respiratório e fechamento suave das cordas vocais.")
        elif hnr < 22:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado é bom, mas pode ser melhorado. Para aumentar a clareza e ressonância, continue praticando um fluxo de ar constante e bem apoiado.")
        else:
            recomendacoes.append("• <b>Qualidade Vocal (HNR):</b> Seu resultado está excelente, indicando uma voz clara e com ótimo apoio!")

    if exercise_type == "resistencia_tmf":
        tmf = summary.get("duration_seconds", 0)
        if tmf < 15:
            recomendacoes.append("• <b>Eficiência Respiratória (TMF):</b> Seu tempo de fonação está abaixo da média. Pratique exercícios de respiração para melhorar seu controle do ar.")
        else:
            recomendacoes.append("• <b>Eficiência Respiratória (TMF):</b> Seu tempo de fonação está excelente, demonstrando ótimo controle do fluxo de ar.")

    if exercise_type == "teste_vogais":
        recomendacoes.append("• <b>Clareza da Dicção:</b> Observe no gráfico se suas vogais estão bem definidas. Um 'triângulo vocálico' (entre A, I, U) amplo indica uma articulação clara.")

    if not recomendacoes:
        recomendacoes.append("• Análise concluída com sucesso. Continue praticando!")
        
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

def draw_vowel_space_chart(vowel_data):
    """Cria um gráfico F1 vs F2 do espaço vocálico, com o triângulo."""
    vogais = ['a', 'e', 'i', 'o', 'u']
    f1_vals = [vowel_data.get(v, {}).get('f1') for v in vogais]
    f2_vals = [vowel_data.get(v, {}).get('f2') for v in vogais]
    
    if any(v is None for v in f1_vals) or any(v is None for v in f2_vals): return None

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(f2_vals, f1_vals, s=100, c='#2E86C1', zorder=10)
    for i, txt in enumerate(vogais):
        ax.annotate(txt.upper(), (f2_vals[i] + 30, f1_vals[i] + 10), fontsize=12, fontweight='bold')
        
    if all(v is not None for v in [f1_vals[0], f1_vals[2], f1_vals[4], f2_vals[0], f2_vals[2], f2_vals[4]]):
        triangle_f2 = [f2_vals[0], f2_vals[2], f2_vals[4], f2_vals[0]]
        triangle_f1 = [f1_vals[0], f1_vals[2], f1_vals[4], f1_vals[0]]
        ax.plot(triangle_f2, triangle_f1, color='gray', linestyle='--', zorder=5, linewidth=2)

    ax.set_xlabel("Formante 2 (F2) - Anterioridade da Língua →"); ax.set_ylabel("Formante 1 (F1) - Altura da Língua →")
    ax.set_title("Mapa do Seu Espaço Vocálico", fontsize=14); ax.grid(True, linestyle='--', alpha=0.5)
    
    ax.invert_xaxis(); ax.invert_yaxis()
    plt.tight_layout()
    
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150); buf.seek(0); plt.close(fig)
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

# --- FUNÇÃO PARA GERENCIAR QUEBRA DE PÁGINA ---
def check_page_break(y_pos, needed_height):
    """Verifica se há espaço, se não, cria uma nova página e retorna a nova posição Y."""
    if y_pos - needed_height < margin:
        c.showPage()
        c.setFont("Helvetica", 11)
        return height - margin
    return y_pos

# --- INÍCIO DA CONSTRUÇÃO DO PDF ---
y = height - 70

# Cabeçalho
exercise_type = data.get('exercise_type', 'sustentacao_vogal')
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, y, f"🎤 Relatório de Exercício: {exercise_type.replace('_', ' ').title()} 🎶")
y -= 20; c.line(40, y, width-40, y); y -= 40
summary = data.get("summary", {})
classificacao = data.get('classificacao', 'Indefinido')
styles = getSampleStyleSheet()

# --- LÓGICA PARA MONTAR O PDF CORRETO ---
if exercise_type == "teste_vogais":
    # --- LAYOUT PARA O RELATÓRIO DE VOGAIS ---
    y = check_page_break(y, 40)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Análise da Clareza e Dicção"); y -= 15
    
    vowel_chart_buffer = draw_vowel_space_chart(data.get("vowel_space_data", {}))
    if vowel_chart_buffer:
        img_h = available_width * 0.95
        y = check_page_break(y, img_h); c.drawImage(ImageReader(vowel_chart_buffer), margin, y - img_h, width=available_width, height=img_h, preserveAspectRatio=True, anchor='n')
        y -= (img_h + 15)
    
elif exercise_type == "resistencia_tmf":
    # --- LAYOUT PARA O RELATÓRIO DE RESISTÊNCIA ---
    y = check_page_break(y, 100)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Resumo da Análise de Resistência"); y -= 15
    # (código para desenhar o resumo de resistência...)
    
    y = check_page_break(y, 170)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#117A65"))
    c.drawString(margin, y, "Estabilidade da Afinação Durante o Exercício"); y -= 15
    # (código para desenhar o gráfico de contorno...)

else: # PADRÃO: SUSTENTAÇÃO DE VOGAL
    # --- LAYOUT COMPLETO ---
    y = check_page_break(y, 150)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Resumo da Análise"); y -= 15
    # (código para desenhar o resumo completo...)

    y = check_page_break(y, 190)
    # (código para desenhar o espectrograma...)

    y = check_page_break(y, 170)
    # (código para desenhar o contorno de afinação...)

# Recomendações
recomendacoes = generate_recommendations(data)
if recomendacoes:
    # (código para medir e desenhar as recomendações...)

c.save()
print(pdf_file)
