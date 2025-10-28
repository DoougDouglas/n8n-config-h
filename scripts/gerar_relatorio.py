import sys
import json
import io
import os
import parselmouth
import numpy as np
import matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER # Importado para centralizar o título

# Configuração do Matplotlib para ambiente de servidor
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- FUNÇÕES DE LÓGICA E DESENHO (CORPO COMPLETO) ---

def generate_recommendations(data):
    """Gera dicas personalizadas e educativas com base nos dados e no tipo de exercício."""
    recomendacoes = []
    summary = data.get("summary", {})
    exercise_type = data.get("exercise_type", "")
    
    health_alert = summary.get("vocal_health_alert", "Normal")
    if health_alert != "Normal":
        recomendacoes.append(f"⚠️ <b>ALERTA DE SAÚDE:</b> Identificamos instabilidade ou ruído excessivo na sua voz. Recomendamos descanso, hidratação e, se o problema persistir, procure um fonoaudiólogo. Detalhes: {health_alert}")

    if exercise_type in ["saude_qualidade", "comunicacao_entonação"]:
        
        hnr = summary.get("hnr_db_mean", 0)
        if hnr < 12.0:
            recomendacoes.append("• <b>Clareza da Voz (HNR):</b> Sua voz está com **muito ar/sopro**. Isso reduz a projeção. <b>Dica:</b> Pratique exercícios de apoio respiratório (diafragma) e tente fechar as cordas vocais de forma mais suave.")
        elif hnr < 18:
            recomendacoes.append("• <b>Clareza da Voz (HNR):</b> O resultado é bom, mas há espaço para mais ressonância. <b>Dica:</b> Tente projetar o som para a 'máscara' (nariz e boca) para um timbre mais brilhante e 'limpo'.")
        else:
            recomendacoes.append("• <b>Clareza da Voz (HNR):</b> **Excelente resultado!** Sua voz é clara e bem apoiada. Continue mantendo este controle.")
        
        stdev_semitones = summary.get("pitch_stdev_semitones", 10.0)
        if stdev_semitones > 0.5:
            recomendacoes.append(f"• <b>Estabilidade (Afinação):</b> Sua nota principal está **instável** ({round(stdev_semitones, 2)} ST). <b>Dica:</b> Pratique notas longas e retas ('sustentação') para treinar a coordenação da respiração e dos músculos vocais.")
        elif stdev_semitones > 0.3:
            recomendacoes.append("• <b>Estabilidade (Afinação):</b> A estabilidade é boa, mas pode ser mais precisa. <b>Dica:</b> Refine o controle respiratório e use exercícios de *solfejo* lento para 'fixar' a nota na memória muscular.")
        
        tmf = summary.get("duration_seconds", 0)
        if exercise_type == "saude_qualidade" and tmf > 0 and tmf < 15:
            recomendacoes.append(f"• <b>Eficiência Respiratória (TMF):</b> O tempo de sustentação ({round(tmf, 1)}s) é baixo. <b>Dica:</b> Priorize exercícios de **respiração diafragmática** para aumentar a capacidade pulmonar e o controle do fluxo de ar.")
        
        jitter = summary.get("jitter_percent", "N/A")
        shimmer = summary.get("shimmer_percent", "N/A")

        if jitter == "N/A" or shimmer == "N/A":
             recomendacoes.append("• <b>Micro-Estabilidade:</b> Não foi possível calcular Jitter/Shimmer. <b>Dica:</b> Para uma análise completa, grave em ambiente silencioso e com emissão de voz 'limpa' (sem sopro excessivo).")
        elif isinstance(jitter, (int, float)) and jitter > 1.5:
             recomendacoes.append("• <b>Micro-Estabilidade:</b> Jitter alto detectado. <b>Dica:</b> Isso pode indicar fadiga vocal ou falta de apoio. Descanse a voz e foque no apoio diafragmático para maior firmeza.")
        
        vibrato_data = summary.get("vibrato", {})
        if vibrato_data.get("is_present") and vibrato_data.get("extent_semitones", 0) > 0.3:
             recomendacoes.append(f"• <b>Vibrato Natural:</b> Sua voz apresentou um vibrato bonito e natural. Isso demonstra flexibilidade e relaxamento. Continue praticando para refinar essa oscilação controlada.")
    
    if exercise_type == "extensao_afinacao":
        range_data = data.get("range_data", {})
        min_note = range_data.get("min_pitch_note", "N/A")
        max_note = range_data.get("max_pitch_note", "N/A")
        
        if min_note != "N/A" and max_note != "N/A":
            recomendacoes.append(f"• <b>Seu Alcance:</b> Você explorou notas desde <b>{min_note}</b> até <b>{max_note}</b>. <b>Dica:</b> O aquecimento vocal é essencial. Para expandir seu alcance, pratique exercícios de escalas que ultrapassem levemente suas notas mais agudas e graves de forma suave.")

        vowel_data = data.get("vowel_space_data", {})
        if len(vowel_data) >= 3 and vowel_data.get('a', {}).get('f1') != 'N/A':
            recomendacoes.append("• <b>Clareza de Vogais:</b> O seu 'triângulo vocálico' (mapa F1/F2) mostra a distinção entre suas vogais. <b>Dica:</b> Para melhorar a dicção, tente exagerar a forma das vogais para aumentar o contraste entre elas.")


    if not recomendacoes or recomendacoes[0].startswith("• Análise concluída"):
        recomendacoes.append("• Análise concluída com sucesso. Continue praticando para acompanhar sua evolução!")
            
    return recomendacoes

def draw_pitch_contour_chart(pitch_data, is_falada=False):
    """Cria um gráfico de contorno de afinação com rótulos amigáveis."""
    times = [p[0] for p in pitch_data if p[1] is not None]
    frequencies = [p[1] for p in pitch_data if p[1] is not None]
    if not times or len(times) < 2: return None
    
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(times, frequencies, color='#2E86C1', linewidth=2)
    
    if is_falada:
        title = "Contorno da ENTROÇÃO (Fala)"
        ylabel = "Frequência (Entonação)"
    else:
        title = "Contorno da AFINAÇÃO (Sustentação)"
        ylabel = "Frequência (Hz)"
        
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel("Tempo (segundos)", fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    if frequencies:
        ax.set_ylim(bottom=max(0, min(frequencies) - 20), top=max(frequencies) + 20)
    
    plt.tight_layout(pad=1.0)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200)
    buf.seek(0)
    plt.close(fig)
    return buf

def draw_spectrogram(sound):
    """Cria um espectrograma do áudio."""
    try:
        spectrogram = sound.to_spectrogram()
        fig, ax = plt.subplots(figsize=(10, 3.5))
        
        sg_db = 10 * np.log10(spectrogram.values)
        
        im = ax.imshow(sg_db, cmap='viridis', aspect='auto', origin='lower', 
                        extent=[spectrogram.xmin, spectrogram.xmax, spectrogram.ymin, spectrogram.ymax])
        
        ax.set_title("Espectrograma (Impressão Digital da Voz)", fontsize=12, fontweight='bold')
        ax.set_xlabel("Tempo (segundos)", fontsize=10)
        ax.set_ylabel("Frequência (Hz)", fontsize=10)
        ax.set_ylim(top=4000)
        
        plt.tight_layout(pad=1.0)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200)
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception: return None

def draw_vowel_space_chart(vowel_data):
    """Cria um gráfico F1 vs F2 do espaço vocálico, com o triângulo."""
    vogais = ['a', 'e', 'i', 'o', 'u']
    f1_vals = [vowel_data.get(v, {}).get('f1') for v in vogais]
    f2_vals = [vowel_data.get(v, {}).get('f2') for v in vogais]
    
    f1_clean = [v for v in f1_vals if isinstance(v, (int, float))]
    f2_clean = [v for v in f2_vals if isinstance(v, (int, float))]
    
    if len(f1_clean) < 3 or len(f2_clean) < 3: return None

    fig, ax = plt.subplots(figsize=(6, 6))
    
    ax.scatter(f2_clean, f1_clean, s=100, c='#2E86C1', zorder=10)
    
    valid_vogais = [(f2_vals[i], f1_vals[i], vogais[i]) for i in range(len(vogais)) if isinstance(f1_vals[i], (int, float))]

    for f2, f1, txt in valid_vogais:
        ax.annotate(txt.upper(), (f2, f1), xytext=(5, 12), textcoords='offset points', fontsize=12, fontweight='bold')
    
    vowels_for_triangle = {v: data for v, data in zip(vogais, valid_vogais) if v in ['a', 'i', 'u']}
    if len(vowels_for_triangle) == 3:
        triangle_coords = [vowels_for_triangle[v][:2] for v in ['a', 'i', 'u']]
        triangle_coords.append(triangle_coords[0]) 
        
        triangle_f2 = [c[0] for c in triangle_coords]
        triangle_f1 = [c[1] for c in triangle_coords]
        ax.plot(triangle_f2, triangle_f1, color='gray', linestyle='--', zorder=5, linewidth=2)

    ax.set_xlabel("Formante 2 (F2) - Anterioridade da Língua →")
    ax.set_ylabel("Formante 1 (F1) - Altura da Língua →")
    ax.set_title("Mapa do Seu Espaço Vocálico", fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    ax.invert_xaxis(); ax.invert_yaxis()
    plt.tight_layout(pad=1.0)
    
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150); buf.seek(0); plt.close(fig)
    return buf

def draw_vocal_range_chart(range_data):
    """Cria um gráfico de barra horizontal para a extensão vocal."""
    min_note = range_data.get("min_pitch_note", "N/A")
    max_note = range_data.get("max_pitch_note", "N/A")
    
    if min_note == "N/A" or max_note == "N/A": return None
    
    notes = ["G2", "G#2", "A2", "A#2", "B2", "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3", "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4", "C5", "C#5", "D5"]
    
    try:
        y_min = notes.index(min_note)
        y_max = notes.index(max_note)
    except ValueError:
        return None

    fig, ax = plt.subplots(figsize=(8, 3))
    
    ax.barh("Sua Extensão", width=y_max - y_min, left=y_min, color='#2E86C1', height=0.5)
    
    ax.set_title("Seu Alcance Vocal", fontsize=14, fontweight='bold')
    ax.set_xlabel("Notas Musicais", fontsize=10)
    ax.set_yticks([]) 
    ax.set_xticks(range(len(notes)))
    ax.set_xticklabels(notes, rotation=45, ha='right', fontsize=8)
    ax.set_xlim(-0.5, len(notes) - 0.5)
    
    ax.text(y_min, "Sua Extensão", min_note, ha='center', va='bottom', color='#2E86C1', fontweight='bold', fontsize=10, transform=ax.transData)
    ax.text(y_max, "Sua Extensão", max_note, ha='center', va='bottom', color='#2E86C1', fontweight='bold', fontsize=10, transform=ax.transData)
    
    plt.tight_layout(pad=1.0)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200)
    buf.seek(0)
    plt.close(fig)
    return buf


# --- FUNÇÕES AUXILIARES DE PDF ---
def draw_paragraph(c, y_start, text_list, style, available_width):
    y_line = y_start
    for line in text_list:
        p = Paragraph(line, style)
        w, h = p.wrapOn(c, available_width, height)
        y_line -= h
        p.drawOn(c, margin, y_line)
        y_line -= 10
    return y_line

def check_page_break(y_pos, needed_height):
    if y_pos - needed_height < margin:
        c.showPage()
        c.setFont("Helvetica", 11)
        return height - margin
    return y_pos

# --- SCRIPT PRINCIPAL DE GERAÇÃO DE PDF ---

if len(sys.argv) < 2:
    print("Uso: python seu_script.py <nome_da_pasta_do_cliente_email>", file=sys.stderr)
    sys.exit(1)

client_folder_name = sys.argv[1]

base_dir = os.path.join("/tmp/cursoTutoLMS/py", client_folder_name)
json_file_path = os.path.join(base_dir, "data_for_report.json")
audio_file_path = os.path.join(base_dir, "audio-aluno.wav")
pdf_file = os.path.join(base_dir, "relatorio_vocal.pdf")


try:
    with open(json_file_path, 'r', encoding='utf-8') as f: data = json.load(f)
    sound = parselmouth.Sound(audio_file_path) 
except Exception as e:
    print(f"Erro ao ler os arquivos: {e}", file=sys.stderr); sys.exit(1)

c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4; margin = 50; available_width = width - (2 * margin)
styles = getSampleStyleSheet()
y = height - 70

# Cabeçalho (AJUSTADO PARA QUEBRA DE LINHA)
exercise_type = data.get('exercise_type', 'saude_qualidade')
title_map = {
    "saude_qualidade": "Saúde, Qualidade e Resistência Vocal",
    "extensao_afinacao": "Extensão, Afinação e Articulação",
    "comunicacao_entonação": "Projeção e Entonação na Comunicação"
}
title_text = f"🎤 Relatório de Desempenho Vocal: {title_map.get(exercise_type, 'Análise Geral')} 🎶"

# 1. Cria um estilo para o título (centralizado e com quebra de linha)
header_style = ParagraphStyle(
    name='HeaderStyle', 
    fontName='Helvetica-Bold', 
    fontSize=20, 
    leading=24, 
    alignment=TA_CENTER
)
p_header = Paragraph(title_text, header_style)
w_header, h_header = p_header.wrapOn(c, available_width, height)

# 2. Desenha o título quebrando linha
y -= h_header 
p_header.drawOn(c, margin, y)

# 3. Desenha a linha e ajusta o Y
y -= 20; c.line(40, y, width-40, y); y -= 40
summary = data.get("summary", {})

# --- 1. SEÇÃO RESUMO PRINCIPAL ---
y = check_page_break(y, 150)
c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
c.drawString(margin, y, "Seu Perfil Vocal em Números Fáceis"); y -= 15
style = ParagraphStyle(name='Resumo', fontName='Helvetica', fontSize=11, leading=18)

# Variáveis
jitter_val = round(summary.get('jitter_percent', 0), 2) if isinstance(summary.get('jitter_percent', 0), (int, float)) else summary.get('jitter_percent', 'N/A')
shimmer_val = round(summary.get('shimmer_percent', 0), 2) if isinstance(summary.get('shimmer_percent', 0), (int, float)) else summary.get('shimmer_percent', 'N/A')
estabilidade_st = round(summary.get('pitch_stdev_semitones', 0), 2)
hnr_val = round(summary.get('hnr_db_mean', 0), 2)
duracao_val = round(summary.get('duration_seconds', 0), 2)
intensidade_val = round(summary.get('intensity_db_mean', 0), 2)

resumo_content = [
    f"<b>Afinação Média:</b> {summary.get('pitch_note_mean', 'N/A')} ({round(summary.get('pitch_hz_mean', 0), 2)} Hz).",
    f"<b>Estabilidade da Afinação:</b> {estabilidade_st} semitons. <br/> <i>(Mede o 'balanço' da nota. Menor que 0.5 ST é considerado estável.)</i>",
    f"<b>Clareza Vocal (HNR):</b> {hnr_val} dB. <br/> <i>(Indica o quão 'limpa' a voz está. Valores acima de 18 dB são excelentes.)</i>",
    f"<b>Projeção/Volume Médio:</b> {intensidade_val} dB.",
    f"<b>Resistência (Duração):</b> {duracao_val} segundos. <br/> <i>(Seu Tempo Máximo de Fonação. Essencial para controle respiratório.)</i>",
    f"<b>Instabilidade (Jitter/Shimmer):</b> Jitter: {jitter_val}%; Shimmer: {shimmer_val}%. <br/> <i>(Micro-variações. Valores baixos indicam saúde e firmeza vocal.)</i>",
]

vibrato_data = summary.get("vibrato", {})
if vibrato_data.get("is_present"):
    vibrato_rate = round(vibrato_data["rate_hz"], 2)
    vibrato_extent = round(vibrato_data["extent_semitones"], 2)
    resumo_content.append(f"<b>Vibrato:</b> Presente (Taxa: {vibrato_rate} Hz, Extensão: {vibrato_extent} ST). <br/> <i>(Oscilação natural. Indica flexibilidade e relaxamento vocal.)</i>")

y = draw_paragraph(c, y, resumo_content, style, available_width)
y -= 20

# --- 2. LÓGICA DE GRÁFICOS POR GRUPO ---

# GRUPO A: SAÚDE, QUALIDADE E COMUNICAÇÃO
if exercise_type in ["saude_qualidade", "comunicacao_entonação"]:
    
    # Espectrograma (Timbre e Projeção)
    y = check_page_break(y, 190)
    spectrogram_buffer = draw_spectrogram(sound)
    
    if spectrogram_buffer:
        c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#117A65")); c.drawString(margin, y, "Impressão Digital da Voz (Timbre e Projeção)"); y -= 15
        img = ImageReader(spectrogram_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
        img_h = available_width * aspect
        c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
        y -= (img_h + 30)

    # Contorno de Pitch (Afinação/Entonação)
    y = check_page_break(y, 170)
    pitch_contour_data = data.get("time_series", {}).get("pitch_contour", [])
    if pitch_contour_data:
        is_falada = (exercise_type == "comunicacao_entonação")
        chart_buffer = draw_pitch_contour_chart(pitch_contour_data, is_falada=is_falada) 
        if chart_buffer:
            c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D")); c.drawString(margin, y, "Mapa da Afinação/Entonação"); y -= 15
            img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
            img_h = available_width * aspect
            c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
            y -= (img_h + 30)

# GRUPO B: EXTENSÃO E AFINAÇÃO
elif exercise_type == "extensao_afinacao":
    
    # 1. Gráfico de Extensão (Range)
    y = check_page_break(y, 170)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#117A65"))
    c.drawString(margin, y, "Seu Alcance Vocal Completo"); y -= 15
    range_data = data.get("range_data", {})
    
    vocal_range_chart_buffer = draw_vocal_range_chart(range_data)
    
    if vocal_range_chart_buffer:
        img = ImageReader(vocal_range_chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
        img_h = available_width * aspect
        y = check_page_break(y, img_h); c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
        y -= (img_h + 30)

    # 2. Espaço Vocálico (Formantes A-E-I-O-U)
    y = check_page_break(y, 40)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Mapa do Seu Espaço Vocálico (Clareza e Articulação)"); y -= 15
    
    vowel_chart_buffer = draw_vowel_space_chart(data.get("vowel_space_data", {}))
    
    if vowel_chart_buffer:
        img_h = available_width * 0.95 
        y = check_page_break(y, img_h); c.drawImage(ImageReader(vowel_chart_buffer), margin, y - img_h, width=available_width, height=img_h, preserveAspectRatio=True, anchor='n')
        y -= (img_h + 15)
        
# --- 3. SEÇÃO DE RECOMENDAÇÕES ---
recomendacoes = generate_recommendations(data)
if recomendacoes:
    style = ParagraphStyle(name='Recomendacoes', parent=styles['BodyText'], fontName='Helvetica', fontSize=11, leading=18)
    p_list = [Paragraph(line, style) for line in recomendacoes]
    total_h = sum([p.wrapOn(c, available_width, height)[1] for p in p_list]) + len(p_list)*10
    y = check_page_break(y, total_h + 40)
    
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#E67E22"))
    c.drawString(margin, y, "Recomendações Personalizadas e Dicas de Exercícios 💡"); y -= 15
    y = draw_paragraph(c, y, recomendacoes, style, available_width)

c.save()
print(pdf_file)
