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
    
    # 1. ANÁLISE DE PITCH (Funciona)
    pitch = sound.to_pitch()
    mean_pitch_hz = call(pitch, "Get mean", 0, 0, "Hertz")
    pitch_note = frequency_to_note(mean_pitch_hz)

    # 2. HARMONICS-TO-NOISE RATIO (HNR) (Funciona)
    harmonicity = sound.to_harmonicity()
    hnr_db = call(harmonicity, "Get mean", 0, 0)

    # 3. FORMANTES (Funciona)
    duration = sound.get_total_duration()
    formant = sound.to_formant_burg(time_step=0.01)
    f1_hz = call(formant, "Get value at time", 1, duration / 2, "Hertz", "Linear")
    f2_hz = call(formant, "Get value at time", 2, duration / 2, "Hertz", "Linear")

    output_data = {
        "status": "Análise concluída.",
        "pitch_hz": mean_pitch_hz,
        "pitch_note": pitch_note,
        "hnr_db": hnr_db,
        "formant1_hz": f1_hz,
        "formant2_hz": f2_hz
    }

except Exception as e:
    output_data = {"error": str(e), "status": "Falha na análise."}

print(json.dumps(output_data))
