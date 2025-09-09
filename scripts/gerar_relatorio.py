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

# Importa as bibliotecas de análise e gráficos
import parselmouth
import numpy as np
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
    # (Função de recomendações)
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
    # (Função do gráfico de contorno)
    times = [p[0] for p in pitch_data if p[1] is not None]
    frequencies = [p[1] for p in pitch_data if p[1] is not None]
    if not times: return None
    # Aumentamos a qualidade da imagem gerada
    plt.figure(figsize=(10, 3.5)); plt.plot(times, frequencies, color='#2E86C1', linewidth=2)
    plt.title("Contorno da Afinação ao Longo do Tempo", fontsize=12); plt.xlabel("Tempo (segundos)", fontsize=10)
    plt.ylabel("Frequência (Hz)", fontsize=10); plt.grid(True, linestyle='--', alpha=0.6)
    plt.ylim(bottom=max(0, min(frequencies) - 20), top=max(frequencies) + 20); plt.tight_layout()
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
    return buf

def draw_spectrogram(sound):
    # (Função do espectrograma)
    try:
        spectrogram = sound.to_spectrogram()
        # Aumentamos a qualidade da imagem gerada
        plt.figure(figsize=(10, 3.5))
        
        X, Y = spectrogram.x_grid(), spectrogram.y_grid()
        sg_db = 10 * np.log10(spectrogram.values)
        
        plt.imshow(sg_db, cmap='viridis', aspect='auto', origin='lower', 
                   extent=[spectrogram.xmin, spectrogram.xmax, spectrogram.ymin, spectrogram.ymax])
        
        plt.title("Espectrograma (Impressão Digital da Voz)", fontsize=12)
        plt.xlabel("Tempo (segundos)", fontsize=10)
        plt.ylabel("Frequência (Hz)", fontsize=10)
        plt.ylim(top=4000) # Aumenta um pouco o teto para vozes mais agudas
        
        buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200); buf.seek(0); plt.close()
        return buf
    except Exception as e:
        print(f"DEBUG: Erro ao gerar o espectrograma: {e}", file=sys.stderr)
        return None

def draw_paragraph_section(c, y_start, title, content_list, title_color=colors.black):
    # (Função de parágrafo)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(title_color); c.drawString(50, y_start, title)
    styles = getSampleStyleSheet(); style = styles['BodyText']
    style.fontName = 'Helvetica'; style.fontSize = 11; style.leading = 15
    y_line = y_start - 20
    for text_line in content_list:
        p = Paragraph(text_line, style); w, h = p.wrapOn(c, width - 100, height) # Margem de 50 de cada lado
        p.drawOn(c, 50, y_line - h); y_line -= (h + 10)
    return y_line - 15

# --- SCRIPT PRINCIPAL DE GERAÇÃO DE PDF ---
json_file_path = "/tmp/cursoTutoLMS/py/data_for_report.json"
audio_file_path = "/tmp/cursoTutoLMS/py/audio-aluno.wav"

try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    sound = parselmouth.Sound(audio_file_path)
except Exception as e:
    print(f"Erro ao ler os arquivos de dados ou áudio: {e}", file=sys.stderr)
    sys.exit(1)

pdf_file = "/tmp/cursoTutoLMS/py/relatorio_vocal.pdf"
c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4
y = height - 110
margin = 50
available_width = width - (2 * margin) # Largura total - margens

# Cabeçalho
c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, height-60, "🎤 Relatório de Biofeedback Vocal 🎶")
c.line(40, height-80, width-40, height-80)

# Resumo e Classificação
summary = data.get("summary", {})
classificacao = data.get('classificacao', 'Indefinido')
c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "Resumo da Análise")
c.setFont("Helvetica", 11)
c.drawString(60, y-20, f"• Afinação Média: {round(summary.get('pitch_hz', 0), 2)} Hz (Nota: {summary.get('pitch_note', 'N/A')})")
c.drawString(60, y-40, f"• Intensidade Média: {round(summary.get('intensity_db', 0), 2)} dB")
c.drawString(60, y-60, f"• Qualidade (HNR): {round(summary.get('hnr_db', 0), 2)} dB")
c.drawString(60, y-80, f"• Classificação Sugerida: {classificacao}")
y -= 110

# --- ADIÇÃO DOS GRÁFICOS MAIORES ---
spectrogram_buffer = draw_spectrogram(sound)
if spectrogram_buffer:
    # Desenha a imagem com a largura disponível, mantendo a proporção da altura
    img = ImageReader(spectrogram_buffer)
    img_width, img_height = img.getSize()
    aspect = img_height / float(img_width)
    c.drawImage(img, margin, y - (available_width * aspect), width=available_width, height=(available_width * aspect), preserveAspectRatio=True, anchor='c')
    y -= (available_width * aspect) + 30 # Ajusta o Y baseado na altura proporcional + margem

pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
if pitch_contour_data:
    chart_buffer = draw_pitch_contour_chart(pitch_contour_data)
    if chart_buffer:
        img = ImageReader(chart_buffer)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        c.drawImage(img, margin, y - (available_width * aspect), width=available_width, height=(available_width * aspect), preserveAspectRatio=True, anchor='c')
        y -= (available_width * aspect) + 30

# Recomendações Personalizadas
recomendacoes = generate_recommendations(data)
if recomendacoes:
    y = draw_paragraph_section(c, y, "Recomendações e Dicas 💡", recomendacoes, colors.HexColor("#E67E22"))

# Notas Finais
c.setFont("Helvetica-Oblique", 10); c.setFillColor(colors.dimgray)
c.drawCentredString(width/2, 60, "Este é um relatório de biofeedback gerado por computador.")
c.drawCentredString(width/2, 45, "Use-o como uma ferramenta para guiar sua percepção e seus estudos.")

c.save()
print(pdf_file)
