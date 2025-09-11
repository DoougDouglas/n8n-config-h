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

# --- SCRIPT PRINCIPAL ---

filename = sys.argv[1]
exercise_type = sys.argv[2] if len(sys.argv) > 2 else "sustentacao_vogal"
results = {"status": f"Análise iniciada para: {exercise_type}", "exercise_type": exercise_type}

try:
    sound = parselmouth.Sound(filename)
    
    # --- LÓGICA CONDICIONAL BASEADA NO EXERCÍCIO ---

    if exercise_type == "teste_vogais":
        # Lógica de análise para o teste A-E-I-O-U
        intensity = sound.to_intensity()
        silences = call(intensity, "To TextGrid (silences)", -25, 0.1, 0.1, "silent", "sounding")
        
        num_intervals = call(silences, "Get number of intervals", 1)
        vowel_formants = {}
        vogais = ['a', 'e', 'i', 'o', 'u']
        sound_intervals_count = 0
        
        for i in range(1, num_intervals + 1):
            if call(silences, "Get label of interval", 1, i) == "sounding":
                start_time = call(silences, "Get starting point", 1, i)
                end_time = call(silences, "Get end point", 1, i)
                mid_time = start_time + (end_time - start_time) / 2
                
                formant = sound.to_formant_burg(time_step=mid_time)
                f1 = call(formant, "Get value at time", 1, mid_time, "Hertz", "Linear")
                f2 = call(formant, "Get value at time", 2, mid_time, "Hertz", "Linear")
                
                if sound_intervals_count < len(vogais):
                    vowel_formants[vogais[sound_intervals_count]] = {"f1": f1, "f2": f2}
                
                sound_intervals_count += 1
        
        results["vowel_space_data"] = vowel_formants
        results["summary"] = { "duration_seconds": sound.get_total_duration() }
        results["status"] = "Análise de vogais completa."
        
    else: # Lógica para "sustentacao_vogal" e "resistencia_tmf"
        pitch = sound.to_pitch()
        
        # Dados de Resumo
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
            "pitch_hz": mean_pitch_hz, "stdev_pitch_hz": stdev_pitch_hz,
            "pitch_note": pitch_note, "intensity_db": intensity_db,
            "hnr_db": hnr_db, "duration_seconds": duration,
            "formant1_hz": f1_hz, "formant2_hz": f2_hz
        }
        
        # Dados de Time Series (Contorno)
        pitch_values = pitch.selected_array['frequency']
        pitch_values[pitch_values==0] = np.nan
        times = pitch.xs()
        step = max(1, len(times) // 200)
        pitch_contour_raw = list(zip(times[::step], pitch_values[::step]))
        pitch_contour_clean = [[time, (None if np.isnan(freq) else freq)] for time, freq in pitch_contour_raw]
        results["time_series"] = {"pitch_contour": pitch_contour_clean}
        
        # Análise de Vibrato
        try:
            point_process = call(pitch, "To PointProcess (periodic, cc)")
            avg_period, freq_excursion, _, _, _, _, _, _ = call(
                (sound, point_process, pitch), "Get vibrato", 0, 0, 0.01, 0.0001, 0.05, 0.2, 0.1, 0.9, 0.01, 100)
            results["vibrato"] = {"is_present": True, "rate_hz": 1 / avg_period if avg_period > 0 else 0, "extent_semitones": freq_excursion}
        except Exception:
            results["vibrato"] = {"is_present": False}

        results["status"] = "Análise completa."

except Exception as e:
    results = {"status": "Falha na análise.", "error": str(e), "exercise_type": exercise_type}

print(json.dumps(results))
