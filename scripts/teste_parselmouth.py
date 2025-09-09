# teste_parselmouth.py
import parselmouth
from parselmouth.praat import call
import sys

# Vamos usar o mesmo arquivo de áudio que o n8n está usando
audio_file = "/tmp/cursoTutoLMS/py/audio-aluno.wav"

print("--- Iniciando teste_parselmouth.py ---")
print(f"Versão do Parselmouth instalada: {parselmouth.__version__}")
print(f"Analisando arquivo de áudio: {audio_file}")

try:
    sound = parselmouth.Sound(audio_file)
    print("1. Arquivo de áudio carregado com sucesso.")

    pitch = sound.to_pitch()
    print("2. Objeto Pitch criado com sucesso.")
    
    voiced_frames = pitch.count_voiced_frames()
    print(f"   - Quadros de voz (voiced frames) encontrados: {voiced_frames}")

    if voiced_frames == 0:
        raise ValueError("Nenhum quadro de voz foi encontrado no áudio. A análise não pode continuar.")

    # A LINHA CRÍTICA - Vamos tentar o comando problemático em isolamento
    print("3. Tentando criar PointProcess com o comando 'To PointProcess (periodic, cc)'...")
    point_process = call(pitch, "To PointProcess (periodic, cc)")
    print("4. SUCESSO! Objeto PointProcess criado.")
    print(f"   - Tipo do objeto criado: {type(point_process)}")
    print(f"   - Conteúdo: {point_process}")

except Exception as e:
    print("\n!!!!!!!!!!!!!!!!!! ERRO !!!!!!!!!!!!!!!!!!")
    print(f"A execução falhou com a seguinte exceção: {e}")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")

print("--- Teste concluído ---")
