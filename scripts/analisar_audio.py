import sys
import json
import parselmouth
from parselmouth.praat import call
import math

# --- FUNÇÃO AUXILIAR PARA CONVERTER HERTZ EM NOTA MUSICAL ---
def frequency_to_note(frequency):
    """Converte uma frequência em Hz para a nota musical mais próxima (ex: A4)."""
    if not frequency or not isinstance(frequency, (int, float)) or frequency <= 0:
        return "N/A"
    
    # Frequências de referência
    A4 = 440
    C0 = A4 * pow(2, -4.75)
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    # Calcula o número de semitons a partir de C0
    half_steps = round(12 * math.log2(frequency / C0))
    octave = half_steps // 12
    note_index = half_steps % 12
    
    return f"{note_names[note_index]}{octave}"

# --- SCRIPT PRINCIPAL ---

# Pega o nome do arquivo enviado pelo n8n
filename = sys.argv[1]

try:
    # Carrega o áudio UMA ÚNICA VEZ com parselmouth
    sound = parselmouth.Sound(filename)

    # 1. ANÁLISE DE PITCH (AFINAÇÃO)
    pitch = sound.to_pitch()
    mean_pitch_hz = call(pitch, "Get mean", 0, 0, "Hertz")
    pitch_note = frequency_to_note(mean_pitch_hz)

    # Cria um PointProcess para calcular Jitter e Shimmer
    point_process = call(sound, "To PointProcess (periodic, cc)", pitch)

    # 2. JITTER (ESTABILIDADE DA AFINAÇÃO) - em porcentagem
    jitter_percent = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3) * 100

    # 3. SHIMMER (ESTABILIDADE DA INTENSIDADE/VOLUME) - em porcentagem
    shimmer_percent = call(point_process, "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100

    # 4. HARMONICS-TO-NOISE RATIO (HNR - "LIMPEZA" DA VOZ) - em dB
    harmonicity = sound.to_harmonicity()
    hnr_db = call(harmonicity, "Get mean", 0, 0)

    # 5. FORMANTES (RESONÂNCIA)
    # Analisa os formantes no meio do arquivo de áudio para mais precisão
    duration = sound.get_total_duration()
    formant = sound.to_formant_burg(time_step=0.01)
    f1_hz = call(formant, "Get value at time", 1, duration / 2, "Hertz", "Linear")
    f2_hz = call(formant, "Get value at time", 2, duration / 2, "Hertz", "Linear")

    # Monta o dicionário com todos os dados
    output_data = {
        "pitch_hz": mean_pitch_hz,
        "pitch_note": pitch_note,
        "jitter_percent": jitter_percent,
        "shimmer_percent": shimmer_percent,
        "hnr_db": hnr_db,
        "formant1_hz": f1_hz,
        "formant2_hz": f2_hz
    }

except Exception as e:
    # Em caso de erro (ex: arquivo de áudio inválido), retorna um erro claro
    output_data = {"error": str(e)}

# Imprime o resultado final como um texto JSON, que o n8n vai receber
print(json.dumps(output_data))
