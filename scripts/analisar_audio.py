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

# --- SCRIPT PRINCIPAL COM LOGGING ---

# Estrutura final da nossa saída
results = {
    "log": [],
    "data": {
        "pitch_hz": None, "pitch_note": None, "jitter_percent": None,
        "shimmer_percent": None, "hnr_db": None, "formant1_hz": None,
        "formant2_hz": None
    },
    "status": ""
}

# Inicia o processo
filename = sys.argv[1]
results["log"].append(f"INFO: Script iniciado para o arquivo: {filename}")

try:
    # ETAPA 1: Carregar o áudio
    try:
        sound = parselmouth.Sound(filename)
        results["log"].append("INFO: Arquivo de áudio carregado com sucesso.")
    except Exception as e:
        raise Exception(f"Falha ao carregar o arquivo de áudio: {e}")

    # ETAPA 2: Análise de Pitch
    try:
        pitch = sound.to_pitch(time_step=0.01, pitch_floor=75.0, pitch_ceiling=600.0)
        mean_pitch_hz = call(pitch, "Get mean", 0, 0, "Hertz")
        pitch_note = frequency_to_note(mean_pitch_hz)
        results["data"]["pitch_hz"] = mean_pitch_hz
        results["data"]["pitch_note"] = pitch_note
        results["log"].append(f"INFO: Análise de Pitch concluída. Média: {round(mean_pitch_hz, 2)} Hz ({pitch_note})")
    except Exception as e:
        results["log"].append(f"ERRO: Falha na análise de Pitch: {e}")
        pitch = None # Define pitch como None se falhar

    # ETAPA 3: Análise de Estabilidade (Jitter e Shimmer)
    if pitch and pitch.count_voiced_frames() > 1:
        try:
            point_process = call(pitch, "To PointProcess (periodic, cc)")
            results["log"].append("INFO: PointProcess para estabilidade criado com sucesso.")
            
            jitter_percent = call((point_process, sound), "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3) * 100
            results["data"]["jitter_percent"] = jitter_percent
            results["log"].append(f"INFO: Cálculo de Jitter concluído: {round(jitter_percent, 3)}%")
            
            shimmer_percent = call((point_process, sound), "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100
            results["data"]["shimmer_percent"] = shimmer_percent
            results["log"].append(f"INFO: Cálculo de Shimmer concluído: {round(shimmer_percent, 3)}%")

        except Exception as e:
            results["log"].append(f"ERRO: Falha no cálculo de Jitter/Shimmer: {e}")
    else:
        results["log"].append("AVISO: Análise de Jitter/Shimmer pulada (sem voz suficiente ou falha no Pitch).")

    # ETAPA 4: Análise de HNR
    try:
        harmonicity = sound.to_harmonicity()
        hnr_db = call(harmonicity, "Get mean", 0, 0)
        results["data"]["hnr_db"] = hnr_db
        results["log"].append(f"INFO: Análise de HNR concluída: {round(hnr_db, 2)} dB")
    except Exception as e:
        results["log"].append(f"ERRO: Falha no cálculo de HNR: {e}")

    # ETAPA 5: Análise de Formantes
    try:
        duration = sound.get_total_duration()
        formant = sound.to_formant_burg(time_step=0.01)
        f1_hz = call(formant, "Get value at time", 1, duration / 2, "Hertz", "Linear")
        f2_hz = call(formant, "Get value at time", 2, duration / 2, "Hertz", "Linear")
        results["data"]["formant1_hz"] = f1_hz
        results["data"]["formant2_hz"] = f2_hz
        results["log"].append(f"INFO: Análise de Formantes concluída (F1: {round(f1_hz,2)}, F2: {round(f2_hz,2)}).")
    except Exception as e:
        results["log"].append(f"ERRO: Falha no cálculo de Formantes: {e}")

    # Define o status final com base nos logs
    if any("ERRO" in log for log in results["log"]):
        results["status"] = "Análise concluída com erros."
    else:
        results["status"] = "Análise completa com sucesso."

except Exception as e:
    # Captura erros graves que impeçam a execução (ex: arquivo não encontrado)
    results["log"].append(f"ERRO CRÍTICO: {e}")
    results["status"] = "Falha geral na execução do script."

# Imprime o resultado final completo
print(json.dumps(results, indent=4))
