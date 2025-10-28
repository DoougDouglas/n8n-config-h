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
from reportlab.lib.enums import TA_LEFT

# Configuração do Matplotlib para ambiente de servidor
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- FUNÇÕES DE LÓGICA E DESENHO (MANTIDAS/AJUSTADAS) ---

def generate_recommendations(data):
    """Gera dicas personalizadas e educativas com base nos dados e no tipo de exercício."""
    recomendacoes = []
    summary = data.get("summary", {})
    exercise_type = data.get("exercise_type", "") # Novo tipo: saude_qualidade, extensao_afinacao, etc.
    
    # Adiciona alerta de saúde vocal primeiro
    health_alert = summary.get("vocal_health_alert", "Normal")
    if health_alert != "Normal":
        recomendacoes.append(f"⚠️ <b>ALERTA DE SAÚDE:</b> Identificamos instabilidade ou ruído excessivo na sua voz. Recomendamos descanso, hidratação e, se o problema persistir, procure um fonoaudiólogo. Detalhes: {health_alert}")

    # Lógica para SAÚDE E QUALIDADE & COMUNICAÇÃO E ENTINAÇÃO
    if exercise_type in ["saude_qualidade", "comunicacao_entonação"]:
        
        # 1. Qualidade Vocal (HNR) - Indicador de clareza e apoio
        hnr = summary.get("hnr_db_mean", 0)
        if hnr < 12.0:
            recomendacoes.append("• <b>Clareza da Voz (HNR):</b> Sua voz está com **muito ar/sopro**. Isso reduz a projeção. <b>Dica:</b> Pratique exercícios de apoio respiratório (diafragma) e tente fechar as cordas vocais de forma mais suave.")
        elif hnr < 18:
            recomendacoes.append("• <b>Clareza da Voz (HNR):</b> O resultado é bom, mas há espaço para mais ressonância. <b>Dica:</b> Tente projetar o som para a 'máscara' (nariz e boca) para um timbre mais brilhante e 'limpo'.")
        else:
            recomendacoes.append("• <b>Clareza da Voz (HNR):</b> **Excelente resultado!** Sua voz é clara e bem apoiada. Continue mantendo este controle.")
        
        # 2. Afinação/Estabilidade (Desvio Padrão em Semitons)
        stdev_semitones = summary.get("pitch_stdev_semitones", 10.0)
        if stdev_semitones > 0.5:
            recomendacoes.append(f"• <b>Estabilidade (Afinação):</b> Sua nota principal está **instável** ({round(stdev_semitones, 2)} ST). <b>Dica:</b> Pratique notas longas e retas ('sustentação') para treinar a coordenação da respiração e dos músculos vocais.")
        elif stdev_semitones > 0.3:
            recomendacoes.append("• <b>Estabilidade (Afinação):</b> A estabilidade é boa, mas pode ser mais precisa. <b>Dica:</b> Refine o controle respiratório e use exercícios de *solfejo* lento para 'fixar' a nota na memória muscular.")
        
        # 3. Duração (TMF / Resistência) - APENAS para Saúde/Qualidade
        tmf = summary.get("duration_seconds", 0)
        if exercise_type == "saude_qualidade" and tmf > 0 and tmf < 15:
            recomendacoes.append(f"• <b>Eficiência Respiratória (TMF):</b> O tempo de sustentação ({round(tmf, 1)}s) é baixo. <b>Dica:</b> Priorize exercícios de **respiração diafragmática** para aumentar a capacidade pulmonar e o controle do fluxo de ar.")
        
        # 4. Estabilidade de Micro-Variação (Jitter/Shimmer)
        jitter = summary.get("jitter_percent", "N/A")
        shimmer = summary.get("shimmer_percent", "N/A")

        if jitter == "N/A" or shimmer == "N/A":
             recomendacoes.append("• <b>Micro-Estabilidade:</b> Não foi possível calcular Jitter/Shimmer. <b>Dica:</b> Para uma análise completa, grave em ambiente silencioso e com emissão de voz 'limpa' (sem sopro excessivo).")
        elif isinstance(jitter, (int, float)) and jitter > 1.5:
             recomendacoes.append("• <b>Micro-Estabilidade:</b> Jitter alto detectado. <b>Dica:</b> Isso pode indicar fadiga vocal ou falta de apoio. Descanse a voz e foque no apoio diafragmático para maior firmeza.")
        
        # 5. Vibrato (Positivo)
        vibrato_data = summary.get("vibrato", {})
        if vibrato_data.get("is_present") and vibrato_data.get("extent_semitones", 0) > 0.3:
             recomendacoes.append(f"• <b>Vibrato Natural:</b> Sua voz apresentou um vibrato bonito e natural. Isso demonstra flexibilidade e relaxamento. Continue praticando para refinar essa oscilação controlada.")
    
    # Lógica para EXTENSÃO E AFINAÇÃO
    if exercise_type == "extensao_afinacao":
        # Dicas de Extensão
        range_data = data.get("range_data", {})
        min_note = range_data.get("min_pitch_note", "N/A")
        max_note = range_data.get("max_pitch_note", "N/A")
        
        if min_note != "N/A" and max_note != "N/A":
            recomendacoes.append(f"• <b>Seu Alcance:</b> Você explorou notas desde <b>{min_note}</b> até <b>{max_note}</b>. <b>Dica:</b> O aquecimento vocal é essencial. Para expandir seu alcance, pratique exercícios de escalas que ultrapassem levemente suas notas mais agudas e graves de forma suave.")

        # Dicas de Vogais (baseado na área do triângulo vogal - F1/F2)
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
    
# Funções draw_spectrogram, draw_vowel_space_chart, draw_vocal_range_chart 
# (Devem estar presentes no seu arquivo final)

# --- FUNÇÕES AUXILIARES DE PDF (MANTIDAS) ---
def draw_paragraph(c, y_start, text_list, style, available_width):
    # ... (manter o corpo da função draw_paragraph) ...
    y_line = y_start
    for line in text_list:
        p = Paragraph(line, style)
        w, h = p.wrapOn(c, available_width, height)
        y_line -= h
        p.drawOn(c, margin, y_line)
        y_line -= 10
    return y_line

def check_page_break(y_pos, needed_height):
    # ... (manter o corpo da função check_page_break) ...
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
    # Assumindo que draw_spectrogram precisa de parselmouth.Sound
    sound = parselmouth.Sound(audio_file_path) 
except Exception as e:
    print(f"Erro ao ler os arquivos: {e}", file=sys.stderr); sys.exit(1)

c = canvas.Canvas(pdf_file, pagesize=A4)
width, height = A4; margin = 50; available_width = width - (2 * margin)
styles = getSampleStyleSheet()
y = height - 70

# Cabeçalho (Ajuste no Mapeamento de Título)
exercise_type = data.get('exercise_type', 'saude_qualidade')
title_map = {
    "saude_qualidade": "Saúde, Qualidade e Resistência Vocal",
    "extensao_afinacao": "Extensão, Afinação e Articulação",
    "comunicacao_entonação": "Projeção e Entonação na Comunicação"
}
# O título é o nome da categoria que veio do HTML
title = title_map.get(exercise_type, "Relatório de Análise Vocal") 

c.setFillColor(colors.HexColor("#2E86C1")); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width/2, y, f"🎤 Relatório de Desempenho Vocal: {title} 🎶")
y -= 20; c.line(40, y, width-40, y); y -= 40
summary = data.get("summary", {})

# --- 1. SEÇÃO RESUMO PRINCIPAL (MANTIDA, pois já foi ajustada e é genérica) ---
y = check_page_break(y, 150)
c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
c.drawString(margin, y, "Seu Perfil Vocal em Números Fáceis"); y -= 15
style = ParagraphStyle(name='Resumo', fontName='Helvetica', fontSize=11, leading=18)

# Variáveis para a nova análise (MANTIDAS)
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

# --- 2. LÓGICA DE GRÁFICOS POR GRUPO (AJUSTADA) ---

# GRUPO A: SAÚDE, QUALIDADE E COMUNICAÇÃO (Pitch Contour e Espectrograma são essenciais)
if exercise_type in ["saude_qualidade", "comunicacao_entonação"]:
    
    # Espectrograma (Timbre e Projeção)
    y = check_page_break(y, 190)
    # Assumindo a função draw_spectrogram está definida
    # spectrogram_buffer = draw_spectrogram(sound) 
    spectrogram_buffer = None # <--- Substituir pela chamada real da função
    
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
        is_falada = (exercise_type == "comunicacao_entonação") # Apenas comunicaçao/palestrante é "fala"
        chart_buffer = draw_pitch_contour_chart(pitch_contour_data, is_falada=is_falada) 
        if chart_buffer:
            c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D")); c.drawString(margin, y, "Mapa da Afinação/Entonação"); y -= 15
            img = ImageReader(chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
            img_h = available_width * aspect
            c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
            y -= (img_h + 30)

# GRUPO B: EXTENSÃO E AFINAÇÃO (Alcance e Espaço Vocálico)
elif exercise_type == "extensao_afinacao":
    
    # 1. Gráfico de Extensão (Range)
    y = check_page_break(y, 170)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#117A65"))
    c.drawString(margin, y, "Seu Alcance Vocal Completo"); y -= 15
    range_data = data.get("range_data", {})
    
    # Assumindo a função draw_vocal_range_chart está definida
    # vocal_range_chart_buffer = draw_vocal_range_chart(range_data) 
    vocal_range_chart_buffer = None # <--- Substituir pela chamada real da função
    
    if vocal_range_chart_buffer:
        img = ImageReader(vocal_range_chart_buffer); img_width, img_height = img.getSize(); aspect = img_height / float(img_width)
        img_h = available_width * aspect
        y = check_page_break(y, img_h); c.drawImage(img, margin, y - img_h, width=available_width, height=img_h)
        y -= (img_h + 30)

    # 2. Espaço Vocálico (Formantes A-E-I-O-U)
    y = check_page_break(y, 40)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#1F618D"))
    c.drawString(margin, y, "Mapa do Seu Espaço Vocálico (Clareza e Articulação)"); y -= 15
    
    # Assumindo a função draw_vowel_space_chart está definida
    # vowel_chart_buffer = draw_vowel_space_chart(data.get("vowel_space_data", {}))
    vowel_chart_buffer = None # <--- Substituir pela chamada real da função
    
    if vowel_chart_buffer:
        img_h = available_width * 0.95 
        y = check_page_break(y, img_h); c.drawImage(ImageReader(vowel_chart_buffer), margin, y - img_h, width=available_width, height=img_h, preserveAspectRatio=True, anchor='n')
        y -= (img_h + 15)
        
# --- 3. SEÇÃO DE RECOMENDAÇÕES (MANTIDA) ---
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
