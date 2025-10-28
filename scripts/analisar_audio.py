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

# Define os valores de piso e teto para a detecção de pitch (mais abrangente para canto)
PITCH_FLOOR = 50.0
PITCH_CEILING = 800.0

# Obtendo argumentos
try:
    filename = sys.argv[1]
    # Usado para customizar o output (ex: "sustentacao_vogal", "analise_extensao", "palestrante_leitura")
    exercise_type = sys.argv[2] if len(sys.argv) > 2 else "sustentacao_vogal"
except IndexError:
    print(json.dumps({"status": "Falha na inicialização.", "error": "Argumento 'filename' ausente."}))
    sys.exit(1)


results = {
    "status": f"Análise iniciada para: {exercise_type}",
    "exercise_type": exercise_type
}

try:
    sound = parselmouth.Sound(filename)
    
    # 1. DETECÇÃO ROBUSTA DE PITCH (F0)
    # Time step menor melhora o contorno para análise de vibrato/afinação
    pitch = sound.to_pitch_ac(
        pitch_floor=PITCH_FLOOR, 
        pitch_ceiling=PITCH_CEILING,
        time_step=0.01 
    )
    
    # Filtra valores de pitch válidos (> 0 Hz)
    pitch_values_all = pitch.selected_array['frequency']
    valid_pitches = pitch_values_all[pitch_values_all > 0]

    # Garante que há dados válidos
    if len(valid_pitches) == 0:
        raise ValueError("Não foi possível detectar nenhuma frequência vocal válida.")

    # --- 2. DADOS DE RESUMO FUNDAMENTAIS ---
    mean_pitch_hz = np.mean(valid_pitches)
    stdev_pitch_semitones = hz_to_semitones_stdev(valid_pitches)
    pitch_note = frequency_to_note(mean_pitch_hz)
    
    intensity_db = call(sound.to_intensity(), "Get mean", 0, 0, "dB")
    hnr_db = call(sound.to_harmonicity(), "Get mean", 0, 0)
    duration = sound.get_total_duration()
    
    # Formantes (Análise no ponto médio da gravação)
    formant = sound.to_formant_burg()
    mid_time = duration / 2
    f1_hz = call(formant, "Get value at time", 1, mid_time, "Hertz", "Linear")
    f2_hz = call(formant, "Get value at time", 2, mid_time, "Hertz", "Linear")

    summary_data = {
        "pitch_hz_mean": mean_pitch_hz,
        "pitch_note_mean": pitch_note,
        "pitch_stdev_semitones": stdev_pitch_semitones, # MUITO MELHOR que stdev em Hz
        "intensity_db_mean": intensity_db,
        "hnr_db_mean": hnr_db,
        "duration_seconds": duration,
        "formant1_hz": f1_hz,
        "formant2_hz": f2_hz
    }
    
    # --- 3. JITTER, SHIMMER, VIBRATO (COM TRATAMENTO DE ERRO) ---
    jitter_local, shimmer_local, vibrato_data = "N/A", "N/A", {"is_present": False}
    
    try:
        # Cria o PointProcess (ciclos glóticos) que é necessário para Jitter/Shimmer
        point_process = call([sound, pitch], "To PointProcess (cc)")

        # Jitter Local (em % para melhor visualização)
        jitter_local = call(
            [sound, point_process], "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3
        ) * 100 

        # Shimmer Local (em % para melhor visualização)
        shimmer_local = call(
            [sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3
        ) * 100

        # Vibrato (Retorna 8 valores)
        avg_period, freq_excursion, _, _, _, _, _, _ = call(
            [sound, point_process, pitch], "Get vibrato", 0, 0, 0.01, 0.0001, 0.05, 0.2, 0.1, 0.9, 0.01, 100
        )
        
        vibrato_data = {
            "is_present": (freq_excursion > 0.05), # Excursão de 0.05 semitons como limite
            "rate_hz": 1 / avg_period if avg_period > 0 else 0,
            "extent_semitones": freq_excursion
        }

    except Exception as e:
        # O PointProcess pode falhar em vozes muito irregulares.
        print(f"Aviso: Falha ao calcular jitter/shimmer/vibrato. {e}", file=sys.stderr)
        
    summary_data["jitter_percent"] = jitter_local
    summary_data["shimmer_percent"] = shimmer_local
    summary_data["vibrato"] = vibrato_data
    
    # --- 4. VERIFICAÇÃO DE SAÚDE VOCAL ---
    saude_vocal_alert = check_vocal_health(jitter_local, shimmer_local, hnr_db)
    summary_data["vocal_health_alert"] = saude_vocal_alert
    
    results["summary"] = summary_data

    # --- 5. DADOS ESPECÍFICOS POR EXERCÍCIO (Mantidos e Refinados) ---
    
    if exercise_type == "analise_extensao":
        # Pitch values já filtrados anteriormente
        min_pitch_hz = np.min(valid_pitches)
        max_pitch_hz = np.max(valid_pitches)

        results["range_data"] = {
            "min_pitch_hz": min_pitch_hz,
            "max_pitch_hz": max_pitch_hz,
            "min_pitch_note": frequency_to_note(min_pitch_hz),
            "max_pitch_note": frequency_to_note(max_pitch_hz)
        }
        results["status"] = "Análise de extensão vocal completa."
        
    elif exercise_type in ["sustentacao_vogal", "palestrante_leitura"]:
        # Contorno de Pitch (Série temporal para visualização de estabilidade)
        pitch_contour_raw = pitch.as_matrix() # Usa a matriz para pegar todos os dados de pitch
        times = pitch.xs()
        
        # Filtra o contorno para incluir apenas valores válidos (não 0 Hz)
        pitch_contour_clean = [
            [time, (None if freq <= 0 else freq)]
            for time, freq in zip(times, pitch_contour_raw[0, :])
        ]

        results["time_series"] = {"pitch_contour": pitch_contour_clean}
        results["status"] = f"Análise de {exercise_type} completa."


    if "status" not in results or results["status"].startswith("Análise iniciada"):
        results["status"] = "Análise completa."

except Exception as e:
    results = {"status": "Falha na análise.", "error": str(e), "exercise_type": exercise_type}

print(json.dumps(results, indent=2))
