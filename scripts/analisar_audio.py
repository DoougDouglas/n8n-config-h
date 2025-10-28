import sys
import json
import parselmouth
from parselmouth.praat import call
import math
import numpy as np

# --- FUNÇÕES DE CONVERSÃO E VALIDAÇÃO ---

def frequency_to_note(frequency):
    """Converte frequência em Hertz para a notação musical (ex: A4)."""
    if not isinstance(frequency, (int, float)) or frequency <= 0 or np.isnan(frequency):
        return "N/A"
    A4 = 440
    C0 = A4 * pow(2, -4.75)
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    half_steps = round(12 * math.log2(frequency / C0))
    octave = half_steps // 12
    note_index = half_steps % 12
    return f"{note_names[note_index]}{octave}"

def hz_to_semitones_stdev(valid_pitches, ref_hz=100.0):
    """Calcula o desvio padrão da afinação em Semitons (Variação Semitonal)."""
    if len(valid_pitches) < 2:
        return 0.0
    # Converte Hz para semitons
    semitones = 12 * np.log2(valid_pitches / ref_hz)
    # Retorna o desvio padrão dos semitons
    return np.std(semitones)

def check_vocal_health(jitter, shimmer, hnr):
    """
    Verifica se Jitter, Shimmer e HNR estão dentro das faixas normais.
    Valores de referência comuns (aproximados):
    - Jitter: < 1.04%
    - Shimmer: < 3.81%
    - HNR: > 12.0 dB
    """
    alerts = []
    
    # Jitter (perturbação de frequência)
    if isinstance(jitter, (int, float)) and jitter > 1.04:
        alerts.append("Jitter (instabilidade de frequência) está acima do limite recomendado (Acima de 1.04%).")
    
    # Shimmer (perturbação de amplitude)
    if isinstance(shimmer, (int, float)) and shimmer > 3.81:
        alerts.append("Shimmer (instabilidade de amplitude) está acima do limite recomendado (Acima de 3.81%).")

    # HNR (proporção harmônico-ruído)
    if isinstance(hnr, (int, float)) and hnr < 12.0:
        alerts.append("HNR (Harmônico/Ruído) está baixo (Abaixo de 12.0 dB), indicando uma qualidade de voz 'áspera' ou soprosa.")
    
    if not alerts:
        return "Normal"
    else:
        return " | ".join(alerts)

# --- SCRIPT PRINCIPAL ---

PITCH_FLOOR = 50.0
PITCH_CEILING = 800.0

try:
    filename = sys.argv[1]
    # Argumentos esperados: 'saude_qualidade', 'extensao_afinacao', 'comunicacao_entonação'
    exercise_type = sys.argv[2] if len(sys.argv) > 2 else "saude_qualidade"
except IndexError:
    print(json.dumps({"status": "Falha na inicialização.", "error": "Argumento 'filename' ausente."}))
    sys.exit(1)


results = {
    "status": f"Análise iniciada para: {exercise_type}",
    "exercise_type": exercise_type,
    "vowel_space_data": {},
    "range_data": {},
    "time_series": {}
}

try:
    sound = parselmouth.Sound(filename)
    duration = sound.get_total_duration()
    
    # 1. DETECÇÃO ROBUSTA DE PITCH (F0)
    pitch = sound.to_pitch_ac(pitch_floor=PITCH_FLOOR, pitch_ceiling=PITCH_CEILING, time_step=0.01)
    
    pitch_values_all = pitch.selected_array['frequency']
    valid_pitches = pitch_values_all[pitch_values_all > 0]

    if len(valid_pitches) == 0:
        raise ValueError("Não foi possível detectar nenhuma frequência vocal válida. O áudio pode estar vazio ou muito ruidoso.")

    # --- 2. DADOS DE RESUMO FUNDAMENTAIS ---
    mean_pitch_hz = np.mean(valid_pitches)
    stdev_pitch_semitones = hz_to_semitones_stdev(valid_pitches)
    pitch_note = frequency_to_note(mean_pitch_hz)
    
    intensity_db = call(sound.to_intensity(), "Get mean", 0, 0, "dB")
    hnr_db = call(sound.to_harmonicity(), "Get mean", 0, 0)
    
    formant = sound.to_formant_burg()
    mid_time = duration / 2
    f1_hz = call(formant, "Get value at time", 1, mid_time, "Hertz", "Linear")
    f2_hz = call(formant, "Get value at time", 2, mid_time, "Hertz", "Linear")

    summary_data = {
        "pitch_hz_mean": mean_pitch_hz,
        "pitch_note_mean": pitch_note,
        "pitch_stdev_semitones": stdev_pitch_semitones,
        "intensity_db_mean": intensity_db,
        "hnr_db_mean": hnr_db,
        "duration_seconds": duration,
        "formant1_hz": f1_hz,
        "formant2_hz": f2_hz
    }
    
    # --- 3. JITTER, SHIMMER, VIBRATO (ROBUSTEZ APRIMORADA) ---
    jitter_local, shimmer_local, vibrato_data = "N/A", "N/A", {"is_present": False, "error": "Não calculado."}
    
    try:
        # Tenta criar PointProcess (pode falhar em voz muito irregular/ruído)
        point_process = call([sound, pitch], "To PointProcess (cc)") 

        # Se PointProcess for criado, calcula as métricas:
        jitter_local = call([sound, point_process], "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3) * 100 
        shimmer_local = call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3) * 100

        # Vibrato
        avg_period, freq_excursion, _, _, _, _, _, _ = call(
            [sound, point_process, pitch], "Get vibrato", 0, 0, 0.01, 0.0001, 0.05, 0.2, 0.1, 0.9, 0.01, 100
        )
        
        vibrato_data = {
            "is_present": (freq_excursion > 0.05),
            "rate_hz": 1 / avg_period if avg_period > 0 else 0,
            "extent_semitones": freq_excursion
        }

    except parselmouth.PraatError as e:
        print(f"Aviso: Falha ao calcular Jitter/Shimmer/Vibrato devido a voz não periódica. {e}", file=sys.stderr)
        vibrato_data["error"] = "Falha de cálculo: voz muito instável/ruidosa ou não vozeada."
    except Exception as e:
        print(f"Aviso: Falha desconhecida ao calcular Jitter/Shimmer/Vibrato. {e}", file=sys.stderr)
        vibrato_data["error"] = f"Erro inesperado: {str(e)}"
        
    summary_data["jitter_percent"] = jitter_local
    summary_data["shimmer_percent"] = shimmer_local
    summary_data["vibrato"] = vibrato_data
    
    # --- 4. VERIFICAÇÃO DE SAÚDE VOCAL ---
    if jitter_local != "N/A" and shimmer_local != "N/A":
        saude_vocal_alert = check_vocal_health(jitter_local, shimmer_local, hnr_db)
    else:
        saude_vocal_alert = "Falha no Alerta (Jitter/Shimmer N/A)"
        
    summary_data["vocal_health_alert"] = saude_vocal_alert
    
    results["summary"] = summary_data

    # --- 5. LÓGICA CONDICIONAL PARA AS NOVAS CATEGORIAS ---
    
    if exercise_type == "extensao_afinacao":
        # Combina "analise_extensao" e "teste_vogais"
        
        # A. Análise de Extensão (pitch range)
        min_pitch_hz = np.min(valid_pitches)
        max_pitch_hz = np.max(valid_pitches)

        results["range_data"] = {
            "min_pitch_hz": min_pitch_hz,
            "max_pitch_hz": max_pitch_hz,
            "min_pitch_note": frequency_to_note(min_pitch_hz),
            "max_pitch_note": frequency_to_note(max_pitch_hz)
        }
        
        # B. Análise de Vogais (Formantes no "A-E-I-O-U" - usando 5 intervalos)
        vogais = ['a', 'e', 'i', 'o', 'u']
        vowel_formants = {}
        interval_duration = duration / len(vogais)
        
        for i, vogal in enumerate(vogais):
            start_time = i * interval_duration
            end_time = (i + 1) * interval_duration
            mid_time = start_time + interval_duration / 2
            
            if mid_time > sound.get_total_duration(): continue
            
            formant_vowel = sound.to_formant_burg() 
            try:
                f1 = call(formant_vowel, "Get value at time", 1, mid_time, "Hertz", "Linear")
                f2 = call(formant_vowel, "Get value at time", 2, mid_time, "Hertz", "Linear")
                vowel_formants[vogal] = {"f1": f1, "f2": f2}
            except Exception as e:
                vowel_formants[vogal] = {"f1": "N/A", "f2": "N/A", "error": str(e)}

        results["vowel_space_data"] = vowel_formants
        results["status"] = "Análise de Extensão e Afinação completa."
        
    
    elif exercise_type in ["saude_qualidade", "comunicacao_entonação"]:
        # Contorno de Pitch
        
        # INÍCIO DA CORREÇÃO: VERIFICAR SE PITCH É VÁLIDO ANTES DE USAR as_matrix()
        if pitch is not None and hasattr(pitch, 'as_matrix'): 
            pitch_contour_raw = pitch.as_matrix()
            times = pitch.xs()
            
            pitch_contour_clean = [
                [time, (None if freq <= 0 else freq)]
                for time, freq in zip(times, pitch_contour_raw[0, :])
            ]

            results["time_series"] = {"pitch_contour": pitch_contour_clean}
            
        else:
            # Se pitch é inválido, registra um warning em vez de quebrar o JSON
            results["time_series"] = {"pitch_contour": [], "warning": "Contorno não gerado: objeto Pitch inválido ou erro de detecção de frequência."}
        # FIM DA CORREÇÃO

        if exercise_type == "saude_qualidade":
             results["tmf_seconds"] = duration
             results["status"] = "Análise de Saúde e Qualidade completa."
        
        if exercise_type == "comunicacao_entonação":
            results["status"] = "Análise de Comunicação e Entonação completa."


    if "status" not in results or results["status"].startswith("Análise iniciada"):
        results["status"] = "Análise completa."

except Exception as e:
    # Captura qualquer erro de alto nível que possa ter sido lançado (ex: ValueError do len(valid_pitches))
    results = {"status": "Falha na análise.", "error": str(e), "exercise_type": exercise_type, "details": str(e)}

print(json.dumps(results, indent=2))
