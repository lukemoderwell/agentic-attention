#!/usr/bin/env python3
"""Generate Mario-melodic × Apple-smooth sound effects for Claude Code hooks.

Mario: major key intervals, bouncy pentatonic patterns, coin/1-up DNA
Apple: sine waves, soft attack/release, warm reverb, never harsh
"""

import wave, struct, math, os

SAMPLE_RATE = 44100
DIR = os.path.dirname(os.path.abspath(__file__))


def write_wav(filename, samples):
    path = os.path.join(DIR, filename)
    peak = max(abs(s) for s in samples) if samples else 1
    scale = 28000 / peak if peak > 28000 else 1.0
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        for s in samples:
            w.writeframes(struct.pack("<h", max(-32767, min(32767, int(s * scale)))))
    print(f"  {filename} ({len(samples)/SAMPLE_RATE:.2f}s)")


def sine_tone(freq, duration, volume=0.3):
    """Pure sine — Apple-clean, no harmonics."""
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        val = math.sin(2 * math.pi * freq * t)
        # Smooth raised-cosine envelope — no clicks, ever
        attack = 0.5 * (1 - math.cos(math.pi * min(i / 400, 1.0)))
        release = 0.5 * (1 - math.cos(math.pi * min((n - i) / 600, 1.0)))
        samples.append(val * volume * attack * release * 32767)
    return samples


def bell_tone(freq, duration, volume=0.3):
    """Sine + soft overtones — warm, bell-like. Apple notification character."""
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        # Fundamental + gentle 2nd and 3rd partials
        val = math.sin(2 * math.pi * freq * t)
        val += 0.3 * math.sin(2 * math.pi * freq * 2 * t) * math.exp(-t * 8)
        val += 0.1 * math.sin(2 * math.pi * freq * 3 * t) * math.exp(-t * 14)
        # Smooth envelope with natural decay
        attack = 0.5 * (1 - math.cos(math.pi * min(i / 300, 1.0)))
        decay = math.exp(-t * 2.5)
        release = min((n - i) / 800, 1.0)
        samples.append(val * volume * attack * decay * release * 32767)
    return samples


def pitch_glide(start_freq, end_freq, duration, volume=0.3):
    """Smooth sine glide — like a Mario coin but softer."""
    samples = []
    n = int(SAMPLE_RATE * duration)
    phase = 0.0
    for i in range(n):
        progress = i / n
        # Ease-out curve for natural-feeling glide
        eased = 1 - (1 - progress) ** 2
        freq = start_freq + (end_freq - start_freq) * eased
        phase += freq / SAMPLE_RATE
        val = math.sin(2 * math.pi * phase)
        attack = 0.5 * (1 - math.cos(math.pi * min(i / 200, 1.0)))
        release = 0.5 * (1 - math.cos(math.pi * min((n - i) / 400, 1.0)))
        samples.append(val * volume * attack * release * 32767)
    return samples


def silence(duration):
    return [0] * int(SAMPLE_RATE * duration)


def reverb(samples, decay=0.3, mix=0.4):
    """Warm multi-tap reverb — longer, smoother than before."""
    taps = [
        (29, 0.35),
        (47, 0.28),
        (73, 0.20),
        (97, 0.14),
        (127, 0.09),
        (163, 0.05),
        (199, 0.03),
    ]
    tap_samples = [(int(ms * SAMPLE_RATE / 1000), gain * decay) for ms, gain in taps]
    out_len = len(samples) + int(SAMPLE_RATE * 0.5)
    out = [0.0] * out_len

    for i, s in enumerate(samples):
        out[i] = s
    for i in range(len(samples)):
        for delay, gain in tap_samples:
            if i + delay < out_len:
                out[i + delay] += out[i] * gain

    result = []
    for i in range(out_len):
        dry = samples[i] if i < len(samples) else 0
        wet = out[i]
        result.append(dry * (1 - mix) + wet * mix)
    return result


def mix_channels(*channels):
    max_len = max(len(ch) for ch in channels)
    mixed = [0.0] * max_len
    for ch in channels:
        for i, s in enumerate(ch):
            mixed[i] += s
    return mixed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Notification: Mario coin × Apple alert
# The coin sound is a B5→E6 (major interval, upward).
# We keep that interval but render it as warm bell tones
# with a soft sine glide connecting them.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Generating notification.wav...")

# Warm glide up (coin-inspired interval)
coin = pitch_glide(988, 1319, 0.08, volume=0.28)   # B5 → E6
# Bell ring on the landing note
ring = bell_tone(1319, 0.30, volume=0.22)            # E6 bell sustain

# Subtle octave-below pad
pad = sine_tone(659, 0.35, volume=0.08)              # E5 underneath

samples = mix_channels(coin + ring, pad)
samples = reverb(samples, decay=0.32, mix=0.45)
write_wav("notification.wav", samples)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Task Complete: 1-Up melody × Apple completion
# The 1-Up is: E5 G5 E6 C6 D6 G6 — a bright ascending phrase.
# We take that melodic contour, render as bell tones,
# and let the final note bloom in reverb.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Generating task_complete.wav...")

# Melody — 1-Up inspired intervals, bell timbre
melody_notes = [
    (659, 0.075),   # E5
    (784, 0.075),   # G5
    (1319, 0.075),  # E6
    (1047, 0.075),  # C6
    (1175, 0.075),  # D6
    (1568, 0.25),   # G6 — held, blooms in reverb
]
melody = []
for freq, dur in melody_notes:
    melody += bell_tone(freq, dur, volume=0.22)
    melody += silence(0.008)

# Warm harmonic bed — gentle sine pads
bed = sine_tone(330, 0.25, volume=0.06)    # E4
bed += sine_tone(392, 0.20, volume=0.06)   # G4
bed += sine_tone(523, 0.30, volume=0.07)   # C5

samples = mix_channels(melody, bed)
samples = reverb(samples, decay=0.35, mix=0.48)
write_wav("task_complete.wav", samples)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Error: Pipe/warp zone feel × Apple's gentle alert
# Mario's pipe sound descends. We use a soft downward glide
# landing on a low bell tone — clearly "something happened"
# but pleasant, not punishing.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Generating error.wav...")

glide = pitch_glide(880, 440, 0.10, volume=0.22)    # A5 → A4 soft glide down
land = bell_tone(440, 0.28, volume=0.18)             # A4 bell — warm, low
pad = sine_tone(220, 0.30, volume=0.06)              # A3 sub

samples = mix_channels(glide + land, pad)
samples = reverb(samples, decay=0.28, mix=0.40)
write_wav("error.wav", samples)

print("\nDone — Mario melody, Apple polish.")
