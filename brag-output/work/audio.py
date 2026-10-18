# Original soundtrack for the reel: 128 BPM, D minor, dhol/tabla-flavoured pop beat with SFX in key.
import numpy as np, wave

SR = 44100
DUR = 21.0
N = int(SR * DUR)
BPM = 128
BEAT = 60 / BPM
rng = np.random.default_rng(7)

def hz(midi): return 440 * 2 ** ((midi - 69) / 12)

def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s = (1 - a) * v + a * s; y[i] = s
    return y

def hp(x, fc): return x - onepole_lp(x, fc)

def place(buf, sig, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf): return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig * gain

def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)

# ---------- instruments ----------
def dhol_bass(d=0.35):
    n = int(SR * d); t = np.arange(n) / SR
    f = 52 + 70 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.16)

def dhol_slap(d=0.15):
    n = int(SR * d); t = np.arange(n) / SR
    f = 220 + 160 * np.exp(-t * 60)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.05)
    noise = hp(rng.standard_normal(n), 1500) * env(n, 0.001, 0.025)
    return tone * 0.7 + noise * 0.35

def tabla_na(pitch=hz(74 + 12), d=0.25):  # tuned to D
    n = int(SR * d); t = np.arange(n) / SR
    f = pitch * (1 + 0.04 * np.exp(-t * 40))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)) * env(n, 0.001, 0.07)

def hat(d=0.06):
    n = int(SR * d)
    return hp(rng.standard_normal(n), 7000) * env(n, 0.0005, 0.015)

def pluck(freq, d=0.5, bright=0.5):
    # Karplus-Strong
    n = int(SR * d); L = int(SR / freq)
    buf = rng.uniform(-1, 1, L); out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % L]
        buf[i % L] = 0.5 * (buf[i % L] + buf[(i + 1) % L]) * 0.995
    return out * env(n, 0.002, d / 2.5)

def bass(freq, d):
    n = int(SR * d); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return np.tanh(1.6 * s) * np.minimum(1, t / 0.005) * np.minimum(1, (d - t) / 0.03)

def bell(freq, d=1.0):
    n = int(SR * d); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)) * env(n, 0.002, 0.35)

def whoosh(d=0.45, up=True):
    n = int(SR * d); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    # sweep a crude bandpass by mixing differently filtered copies
    lo = onepole_lp(x, 600); hi = onepole_lp(x, 4000)
    m = t / d if up else 1 - t / d
    shape = np.sin(np.pi * t / d) ** 2
    return ((1 - m) * lo + m * hi) * shape

def riser(d=0.8):
    n = int(SR * d); t = np.arange(n) / SR
    f = hz(62) * 2 ** (t / d * 1.0)  # D up an octave
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    noise = onepole_lp(rng.standard_normal(n), 3000) * 0.4
    return (tone + noise) * (t / d) ** 2

def boom(d=1.2):
    n = int(SR * d); t = np.arange(n) / SR
    f = hz(38) * (1 + 0.5 * np.exp(-t * 8))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.4)

def tick(d=0.05):
    n = int(SR * d)
    return hp(rng.standard_normal(n), 3000) * env(n, 0.0003, 0.008)

# ---------- arrangement ----------
drums = np.zeros(N); perc = np.zeros(N); music = np.zeros(N); sfx = np.zeros(N)

# D minor: Dm - Bb - C - Am (i VI VII v), one chord per bar
chords = [[62, 65, 69], [58, 62, 65], [60, 64, 67], [57, 60, 64]]
roots = [38, 34, 36, 33]
FULL = 2.8  # full groove kicks in on the reveal

nbeats = int(DUR / BEAT) + 1
for b in range(nbeats):
    t0 = b * BEAT
    bar = b // 4; pos = b % 4
    full = t0 >= FULL - 1e-6
    # dhol pattern: boom on 1 and 3, boom on the "and" of 2, slaps on 2 and 4
    if pos in (0, 2): place(drums, dhol_bass(), t0, 1.0 if full else 0.6)
    if pos == 1: place(drums, dhol_bass(), t0 + BEAT / 2, 0.55 if full else 0.3)
    if pos in (1, 3): place(drums, dhol_slap(), t0, 0.55 if full else 0.35)
    # 8th hats, 16th tabla accents once full
    for k in range(2): place(perc, hat(), t0 + k * BEAT / 2, 0.12 if full else 0.06)
    if full:
        for k, g in ((1, 0.18), (3, 0.12)):
            place(perc, tabla_na(hz(86 if k == 1 else 81)), t0 + k * BEAT / 4, g)
    # harmony
    if full:
        ch = chords[bar % 4]
        if pos == 0: place(music, bass(hz(roots[bar % 4]), BEAT * 1.5), t0, 0.32)
        if pos == 2: place(music, bass(hz(roots[bar % 4]), BEAT * 0.9), t0, 0.26)
        if pos == 3: place(music, bass(hz(roots[bar % 4] + 12), BEAT * 0.45), t0 + BEAT / 2, 0.18)
        for k in range(4):  # arpeggiated plucks in 8ths
            note = ch[(pos * 2 + k) % 3] + (12 if (pos * 2 + k) % 4 == 3 else 0)
            if k < 2: place(music, pluck(hz(note), 0.45), t0 + k * BEAT / 2, 0.16)
    else:
        # hook: sustained low drone on D
        pass

# hook drone (0 - 2.8s): D fifth pad
t = np.arange(int(SR * FULL)) / SR
pad = (np.sin(2 * np.pi * hz(50) * t) + 0.5 * np.sin(2 * np.pi * hz(57) * t) + 0.3 * np.sin(2 * np.pi * hz(62) * t))
pad *= np.minimum(1, t / 0.05) * np.minimum(1, (FULL - t) / 0.1) * 0.12
place(music, pad, 0)

# ---------- SFX (in D, mixed under) ----------
place(sfx, boom(), 0.0, 0.5)
place(sfx, whoosh(0.5), 0.62, 0.22)              # red bar slide
place(sfx, whoosh(0.45), FULL - 0.4, 0.22)
place(sfx, boom(), FULL, 0.55)                   # reveal
place(sfx, bell(hz(74), 1.2), 3.25, 0.12)        # title
for tc in (5.6, 9.4, 12.4, 16.2):
    place(sfx, whoosh(0.4), tc - 0.3, 0.16)
for k in range(12):                              # soft typing ticks
    place(sfx, tick(), 5.85 + k * 0.085, 0.05)
for k in range(9):
    place(sfx, tick(), 9.6 + k * 0.085, 0.05)
place(sfx, tick(0.06) * 3, 7.05, 0.12)           # shutter
place(sfx, tick(0.05) * 2, 7.12, 0.1)
place(sfx, bell(hz(81), 0.8), 7.3, 0.08)         # saved toast
place(sfx, bell(hz(74), 0.9), 10.5, 0.1)         # notification: D then A
place(sfx, bell(hz(81), 0.9), 10.62, 0.08)
for tc, m in ((12.7, 74), (13.4, 77), (14.1, 81)):  # spec cards: D F A
    place(sfx, pluck(hz(m), 0.5), tc, 0.18)
place(sfx, tick(0.08), 16.75, 0.08)              # strike
place(sfx, bell(hz(86), 1.0), 17.3, 0.1)         # price lands
place(sfx, riser(0.75), 17.65, 0.28)
place(sfx, boom(), 18.4, 0.45)
place(sfx, dhol_bass(), 18.95, 0.4); place(sfx, dhol_slap(), 18.95, 0.3)  # stamp
place(sfx, bell(hz(74), 1.6), 19.5, 0.1)

# ---------- mix ----------
mix = drums * 0.55 + perc * 0.7 + music * 0.8 + sfx * 0.7
fade = np.ones(N); fl = int(SR * 0.7); fade[-fl:] = np.linspace(1, 0, fl)
mix *= fade
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix /= np.max(np.abs(mix)) / 0.89

stereo = np.stack([mix, mix], axis=1)
pcm = (stereo * 32767).astype(np.int16)
with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', len(mix) / SR)
