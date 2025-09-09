import sys
import json
import parselmouth
from parselmouth.praat import call

filename = sys.argv[1]
debug_info = {}

try:
    # Tenta carregar o arquivo e obter informações básicas
    sound = parselmouth.Sound(filename)
    debug_info["arquivo_carregado"] = True
    debug_info["duracao_segundos"] = sound.get_total_duration()
    debug_info["n_canais"] = sound.get_number_of_channels()

    # Tenta extrair o objeto de Pitch
    pitch = sound.to_pitch(time_step=0.01, pitch_floor=75.0, pitch_ceiling=600.0)
    debug_info["objeto_pitch_criado"] = True

    # Extrai informações detalhadas do Pitch
    total_frames = pitch.get_number_of_frames()
    voiced_frames = pitch.count_voiced_frames()
    debug_info["total_de_frames"] = total_frames
    debug_info["frames_com_voz_encontrados"] = voiced_frames
    
    # Se encontrou voz, tenta calcular as estatísticas
    if voiced_frames > 0:
        mean_pitch = call(pitch, "Get mean", 0, 0, "Hertz")
        min_pitch = call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")
        max_pitch = call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")
        debug_info["pitch_medio_hz"] = mean_pitch
        debug_info["pitch_minimo_hz"] = min_pitch
        debug_info["pitch_maximo_hz"] = max_pitch
        
        # Tenta criar o PointProcess, que é usado para Jitter
        point_process = call(pitch, "To PointProcess")
        debug_info["point_process_criado"] = True
        debug_info["pontos_no_process"] = point_process.get_number_of_points()
    else:
        debug_info["pitch_stats"] = "Nenhuma voz encontrada para calcular estatísticas."

    debug_info["status_depuracao"] = "Script de depuração executado com sucesso."

except Exception as e:
    # Se um erro acontecer em qualquer etapa, ele será capturado aqui
    debug_info["ERRO_OCORRIDO"] = str(e)
    debug_info["status_depuracao"] = "Uma exceção ocorreu durante a depuração."

# Imprime o dicionário de depuração formatado como um texto JSON
print(json.dumps(debug_info, indent=4))
