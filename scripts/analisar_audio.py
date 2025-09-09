import sys
import json
import parselmouth
from parselmouth.praat import call
import math
import numpy as np

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

filename = sys.argv[1]
results = {"status": "Análise iniciada."}

try:
    sound = parselmouth.Sound(filename)
    pitch = sound.to_pitch()
    
    # --- DADOS DE RESUMO (PARA OS MEDIDORES) ---
    mean_pitch_hz = call(pitch, "Get mean", 0, 0, "Hertz")
    pitch_note = frequency_to_note(mean_pitch_hz)
    intensity_db = sound.get_intensity()
    hnr_db = call(sound.to_harmonicity(), "Get mean", 0, 0)
    
    duration = sound.get_total_duration()
    formant = sound.to_formant_burg()
    f1_hz = call(formant, "Get value at time", 1, duration / 2, "Hertz", "Linear")
    f2_hz = call(formant, "Get value at time", 2, duration / 2, "Hertz", "Linear")

    results["summary"] = {
        "pitch_hz": mean_pitch_hz,
        "pitch_note": pitch_note,
        "intensity_db": intensity_db,
        "hnr_db": hnr_db,
        "formant1_hz": f1_hz,
        "formant2_hz": f2_hz
    }

    # --- DADOS PARA O GRÁFICO DE CONTORNO DE AFINAÇÃO ---
    pitch_values = pitch.selected_array['frequency']
    pitch_values[pitch_values==0] = np.nan # Substitui 0s por NaN (ainda necessário para numpy)
    times = pitch.xs()
    
    # Pega no máximo 200 pontos para não sobrecarregar o JSON
    step = max(1, len(times) // 200)
    pitch_contour_raw = list(zip(times[::step], pitch_values[::step]))
    
    # --- INÍCIO DA CORREÇÃO ---
    # Substitui os valores numpy.nan pelo None do Python, que se torna 'null' no JSON
    pitch_contour_clean = [
        [time, (None if np.isnan(freq) else freq)] 
        for time, freq in pitch_contour_raw
    ]
    # --- FIM DA CORREÇÃO ---

    results["time_series"] = {
        "pitch_contour": pitch_contour_clean
    }
    
    # --- ANÁLISE DE VIBRATO ---
    try:
        point_process = call(pitch, "To PointProcess (periodic, cc)")
        avg_period, freq_excursion, _, _, _, _, _, _ = call(
            (sound, point_process, pitch), "Get vibrato", 0, 0, 0.01, 0.0001, 0.05, 0.2, 0.1, 0.9, 0.01, 100
        )
        results["vibrato"] = {
            "is_present": True,
            "rate_hz": 1 / avg_period if avg_period > 0 else 0,
            "extent_semitones": freq_excursion
        }
    except Exception:
        results["vibrato"] = {"is_present": False}

    results["status"] = "Análise completa."

except Exception as e:
    results["status"] = "Falha na análise."
    # Limpa dados parciais em caso de erro grave para não enviar JSON malformado
    results.pop("summary", None)
    results.pop("time_series", None)
    results.pop("vibrato", None)
    results["error"] = str(e)

print(json.dumps(results))
