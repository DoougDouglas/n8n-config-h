import sys
import json
import parselmouth
from parselmouth.praat import call
import math
import numpy as np

def frequency_to_note(frequency):
    if not frequency or not isinstance(frequency, (int, float)) or frequency <= 0:
        return "N/A"
    A4 = 440; C0 = A4 * pow(2, -4.75)
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    half_steps = round(12 * math.log2(frequency / C0))
    octave = half_steps // 12; note_index = half_steps % 12
    return f"{note_names[note_index]}{octave}"

filename = sys.argv[1]
exercise_type = sys.argv[2] if len(sys.argv) > 2 else "sustentacao_vogal"
results = {"status": f"Análise iniciada para o exercício: {exercise_type}"}

try:
    sound = parselmouth.Sound(filename)
    pitch = sound.to_pitch()
    
    pitch_values = pitch.selected_array['frequency']
    pitch_values[pitch_values==0] = np.nan
    times = pitch.xs()
    step = max(1, len(times) // 200)
    pitch_contour_raw = list(zip(times[::step], pitch_values[::step]))
    pitch_contour_clean = [[time, (None if np.isnan(freq) else freq)] for time, freq in pitch_contour_raw]
    results["time_series"] = {"pitch_contour": pitch_contour_clean}
    results['exercise_type'] = exercise_type # <-- ADICIONADO AQUI

    if exercise_type == "escala_5_notas":
        mean_pitch_hz = call(pitch, "Get mean", 0, 0, "Hertz")
        min_pitch_hz = call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")
        max_pitch_hz = call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")
        stdev_pitch_hz = call(pitch, "Get standard deviation", 0, 0, "Hertz")
        results["summary"] = {
            "pitch_hz": mean_pitch_hz, "stdev_pitch_hz": stdev_pitch_hz,
            "min_pitch_note": frequency_to_note(min_pitch_hz),
            "max_pitch_note": frequency_to_note(max_pitch_hz),
            "intensity_db": sound.get_intensity(),
            "hnr_db": call(sound.to_harmonicity(), "Get mean", 0, 0),
            "duration_seconds": sound.get_total_duration()
        }
        results["vibrato"] = {"is_present": False}
        results["status"] = "Análise de Escala completa."
    else: 
        mean_pitch_hz = call(pitch, "Get mean", 0, 0, "Hertz")
        stdev_pitch_hz = call(pitch, "Get standard deviation", 0, 0, "Hertz")
        pitch_note = frequency_to_note(mean_pitch_hz)
        intensity_db = sound.get_intensity()
        hnr_db = call(sound.to_harmonicity(), "Get mean", 0, 0)
        duration = sound.get_total_duration()
        formant = sound.to_formant_burg()
        f1_hz = call(formant, "Get value at time", 1, duration / 2, "Hertz", "Linear")
        f2_hz = call(formant, "Get value at time", 2, duration / 2, "Hertz", "Linear")
        results["summary"] = {
            "pitch_hz": mean_pitch_hz, "stdev_pitch_hz": stdev_pitch_hz, "pitch_note": pitch_note,
            "intensity_db": intensity_db, "hnr_db": hnr_db, "duration_seconds": duration,
            "formant1_hz": f1_hz, "formant2_hz": f2_hz
        }
        try:
            point_process = call(pitch, "To PointProcess (periodic, cc)")
            avg_period, freq_excursion, _, _, _, _, _, _ = call(
                (sound, point_process, pitch), "Get vibrato", 0, 0, 0.01, 0.0001, 0.05, 0.2, 0.1, 0.9, 0.01, 100)
            results["vibrato"] = {"is_present": True, "rate_hz": 1 / avg_period if avg_period > 0 else 0, "extent_semitones": freq_excursion}
        except Exception:
            results["vibrato"] = {"is_present": False}
        results["status"] = "Análise de Sustentação completa."
except Exception as e:
    results = {"status": "Falha na análise.", "error": str(e)}

print(json.dumps(results))
