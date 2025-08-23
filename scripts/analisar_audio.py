import aubio, sys, numpy as np, parselmouth, json

filename = sys.argv[1]
win_s, hop_s, samplerate = 4096, 512, 0
s = aubio.source(filename, samplerate, hop_s)
pitch_o = aubio.pitch("yin", win_s, hop_s, samplerate)
pitch_o.set_unit("Hz"); pitch_o.set_silence(-40)

pitches = []
while True:
    samples, read = s()
    pitch = pitch_o(samples)[0]
    if pitch > 0: pitches.append(pitch)
    if read < hop_s: break

mean_pitch = float(np.mean(pitches)) if pitches else 0.0

snd = parselmouth.Sound(filename)
formant = snd.to_formant_burg()
f1, f2 = formant.get_value_at_time(1, 0.5), formant.get_value_at_time(2, 0.5)

print(json.dumps({"pitch_hz": mean_pitch, "formant1": f1, "formant2": f2}))
