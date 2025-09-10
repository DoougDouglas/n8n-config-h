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
    
    # --- DADOS DE RESUMO ---
    mean_pitch_hz = call(pitch, "Get mean", 0, 0, "Hertz")
    stdev_pitch_hz = call(pitch, "Get standard deviation", 0, 0, "Hertz")
    pitch_note = frequency_to_note(mean_pitch_hz)
    intensity_db = sound.get_intensity()
    hnr_db = call(sound.to_harmonicity(), "Get mean", 0, 0)
    
    duration = sound.get_total_duration() # <-- DURAÇÃO TOTAL DO ÁUDIO (TMF)
    
    formant = sound.to_formant_burg()
    f1_hz = call(formant, "Get value at time", 1, duration / 2, "Hertz", "Linear")
    f2_hz = call(formant, "Get value at time", 2, duration / 2, "Hertz", "Linear")

    results["summary"] = {
        "pitch_hz": mean_pitch_hz,
        "stdev_pitch_hz": stdev_pitch_hz,
        "pitch_note": pitch_note,
        "intensity_db": intensity_db,
        "hnr_db": hnr_db,
        "duration_seconds": duration, # <-- Adicionado ao resultado
        "formant1_hz": f1_hz,
        "formant2_hz": f2_hz
    }

    # (Restante do código para time_series e vibrato permanece igual)
    pitch_values = pitch.selected_array['frequency']
    pitch_values[pitch_values==0] = np.nan
    times = pitch.xs()
    step = max(1, len(times) // 200)
    pitch_contour_raw = list(zip(times[::step], pitch_values[::step]))
    pitch_contour_clean = [[time, (None if np.isnan(freq) else freq)] for time, freq in pitch_contour_raw]
    results["time_series"] = {"pitch_contour": pitch_contour_clean}
    
    try:
        point_process = call(pitch, "To PointProcess (periodic, cc)")
        avg_period, freq_excursion, _, _, _, _, _, _ = call(
            (sound, point_process, pitch), "Get vibrato", 0, 0, 0.01, 0.0001, 0.05, 0.2, 0.1, 0.9, 0.01, 100)
        results["vibrato"] = {"is_present": True, "rate_hz": 1 / avg_period if avg_period > 0 else 0, "extent_semitones": freq_excursion}
    except Exception:
        results["vibrato"] = {"is_present": False}
    results["status"] = "Análise completa."

except Exception as e:
    results["status": "Falha na análise.", "error": str(e)}

print(json.dumps(results))
