import sys
import json
import parselmouth
from parselmouth.praat import call
import math

# --- FUNÇÃO AUXILIAR PARA CONVERTER HERTZ EM NOTA MUSICAL ---
def frequency_to_note(frequency):
    if not frequency or not isinstance(frequency, (int, float)) or frequency <= 0:
        return "N/A"
    A4 = 440
    C0 = A4 * pow(2, -4.75)
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    half_steps = round(12 * math.log2(frequency / C0))
    octave = half_steps // 12
    note_index = half_steps % 12
    return f"{note_names[note_index]}{octave}"

# --- SCRIPT PRINCIPAL ---

filename = sys.argv[1]

try:
    sound = parselmouth.Sound(filename)
    
    pitch = sound.to_pitch(time_step=0.01, pitch_floor=75.0, pitch_ceiling=600.0)
    mean_pitch_hz = call(pitch, "Get mean", 0, 0, "Hertz")
    pitch_note = frequency_to_note(mean_pitch_hz)

    # --- INÍCIO DA CORREÇÃO DEFINITIVA ---
    # Usamos o comando correto para criar o PointProcess para análise de periodicidade
    point_process = call(pitch, "To PointProcess (periodic, cc)")
    # --- FIM DA CORREÇÃO DEFINITIVA ---

    # Com o PointProcess correto, os cálculos de Jitter e Shimmer funcionarão
    jitter_percent = call((point_process, sound), "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3) * 100
    shimmer_percent = call((point_process, sound), "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100
    
    harmonicity = sound.to_harmonicity()
    hnr_db = call(harmonicity, "Get mean", 0, 0)

    duration = sound.get_total_duration()
    formant = sound.to_formant_burg(time_step=0.01)
    f1_hz = call(formant, "Get value at time", 1, duration / 2, "Hertz", "Linear")
    f2_hz = call(formant, "Get value at time", 2, duration / 2, "Hertz", "Linear")

    output_data = {
        "status": "Análise completa.",
        "pitch_hz": mean_pitch_hz,
        "pitch_note": pitch_note,
        "jitter_percent": jitter_percent,
        "shimmer_percent": shimmer_percent,
        "hnr_db": hnr_db,
        "formant1_hz": f1_hz,
        "formant2_hz": f2_hz
    }

except Exception as e:
    output_data = {"error": str(e), "status": "Falha na análise."}

print(json.dumps(output_data))
