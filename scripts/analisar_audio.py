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

results = {
    "status": f"Análise iniciada para: {exercise_type}",
    "exercise_type": exercise_type
}

try:
    sound = parselmouth.Sound(filename)
    pitch = sound.to_pitch()
    
    # --- DADOS DE RESUMO (AGORA CALCULADOS PARA TODOS OS EXERCÍCIOS) ---
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

    # --- ADIÇÃO DE JITTER, SHIMMER E VIBRATO PARA ANÁLISE DETALHADA ---
    try:
        # Aumentamos a faixa de pitch para detecção do ponto de processo
        point_process = call(pitch, "To PointProcess (periodic, cc)", 75, 500)
        
        # Ajustamos os parâmetros de jitter e shimmer para serem mais tolerantes
        # O 4º parâmetro (teto de variação de frequência) foi ajustado de 0.02 para 0.05
        # O 5º parâmetro (fator do período máximo) foi ajustado de 1.3 para 1.1
        jitter_local = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.05, 1.1) * 100
        shimmer_local = call(point_process, "Get shimmer (local)", 0, 0, 0.0001, 0.05, 1.1) * 100
        
        # Vibrato
        avg_period, freq_excursion, _, _, _, _, _, _ = call(
            (sound, point_process, pitch), "Get vibrato", 0, 0, 0.01, 0.0001, 0.05, 0.2, 0.1, 0.9, 0.01, 100)
            
        results["summary"]["jitter_percent"] = jitter_local
        results["summary"]["shimmer_percent"] = shimmer_local
        results["summary"]["vibrato"] = {
            "is_present": True,
            "rate_hz": 1 / avg_period if avg_period > 0 else 0,
            "extent_semitones": freq_excursion
        }

    except Exception as e:
        # Define valores "N/A" se a análise detalhada falhar
        results["summary"]["jitter_percent"] = "N/A"
        results["summary"]["shimmer_percent"] = "N/A"
        results["summary"]["vibrato"] = {"is_present": False}
        print(f"Aviso: Falha ao calcular métricas detalhadas (Jitter, Shimmer, Vibrato). {e}", file=sys.stderr)

    # --- DADOS ESPECÍFICOS DE CADA EXERCÍCIO ---
    
    if exercise_type == "teste_vogais":
        intensity_obj = sound.to_intensity()
        silences = call(intensity_obj, "To TextGrid (silences)", -25, 0.1, 0.1, "silent", "sounding")
        num_intervals = call(silences, "Get number of intervals", 1)
        vowel_formants = {}
        vogais = ['a', 'e', 'i', 'o', 'u']
        sound_intervals_count = 0
        
        for i in range(1, num_intervals + 1):
            if call(silences, "Get label of interval", 1, i) == "sounding":
                start_time = call(silences, "Get starting point", 1, i)
                end_time = call(silences, "Get end point", 1, i)
                mid_time = start_time + (end_time - start_time) / 2
                
                formant_vowel = sound.to_formant_burg(time_step=mid_time)
                f1 = call(formant_vowel, "Get value at time", 1, mid_time, "Hertz", "Linear")
                f2 = call(formant_vowel, "Get value at time", 2, mid_time, "Hertz", "Linear")
                
                if sound_intervals_count < len(vogais):
                    vowel_formants[vogais[sound_intervals_count]] = {"f1": f1, "f2": f2}
                sound_intervals_count += 1
        
        results["vowel_space_data"] = vowel_formants
        results["status"] = "Análise de vogais completa."

    # Seção para o novo teste de extensão vocal
    elif exercise_type == "analise_extensao":
        pitch_values = pitch.selected_array['frequency']
        valid_pitches = pitch_values[pitch_values > 0]
        
        if len(valid_pitches) > 0:
            min_pitch_hz = np.min(valid_pitches)
            max_pitch_hz = np.max(valid_pitches)
            
            results["range_data"] = {
                "min_pitch_hz": min_pitch_hz,
                "max_pitch_hz": max_pitch_hz,
                "min_pitch_note": frequency_to_note(min_pitch_hz),
                "max_pitch_note": frequency_to_note(max_pitch_hz)
            }
            results["status"] = "Análise de extensão vocal completa."
        else:
            results["status"] = "Não foi possível detectar notas para análise de extensão."

    # Time Series é relevante para sustentação e resistência
    elif exercise_type in ["sustentacao_vogal", "resistencia_tmf"]:
        pitch_values = pitch.selected_array['frequency']
        pitch_values[pitch_values==0] = np.nan
        times = pitch.xs()
        step = max(1, len(times) // 200)
        pitch_contour_raw = list(zip(times[::step], pitch_values[::step]))
        pitch_contour_clean = [[time, (None if np.isnan(freq) else freq)] for time, freq in pitch_contour_raw]
        results["time_series"] = {"pitch_contour": pitch_contour_clean}
        
        # O vibrato já foi movido para o bloco de resumo, então não precisa ser recalculado aqui.
    
    if "status" not in results or results["status"].startswith("Análise iniciada"):
        results["status"] = "Análise completa."

except Exception as e:
    results = {"status": "Falha na análise.", "error": str(e), "exercise_type": exercise_type}

print(json.dumps(results))
