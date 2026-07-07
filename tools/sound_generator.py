import wave
import math
import struct
import os

def write_wav(filename, samples, sample_rate=22050):
    filepath = os.path.join("Frontend/Sounds", filename)
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setparams((1, 2, sample_rate, len(samples), 'NONE', 'not compressed'))
        for s in samples:
            val = int(s * 32767)
            val = max(-32767, min(32767, val))
            data = struct.pack('<h', val)
            wav_file.writeframes(data)
    print(f"[Audio Synthesis]: Synthesized Sci-Fi SFX: {filename}")

def make_boot_sound():
    sample_rate = 22050
    duration = 1.2
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        freq = 220 + 580 * (t / duration)**2
        val = math.sin(2 * math.pi * freq * t)
        if t > 0.4:
            val += 0.5 * math.sin(2 * math.pi * (freq * 1.5) * t)
            val += 0.3 * math.sin(2 * math.pi * (freq * 2.0) * t)
            val /= 1.8
        if t > duration - 0.2:
            val *= (duration - t) / 0.2
        if t < 0.1:
            val *= t / 0.1
        samples.append(val)
    write_wav("boot.wav", samples, sample_rate)

def make_success_sound():
    sample_rate = 22050
    duration = 0.4
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        if t < 0.15:
            freq = 650
            val = math.sin(2 * math.pi * freq * t)
            if t > 0.12:
                val *= (0.15 - t) / 0.03
        else:
            freq = 950
            val = math.sin(2 * math.pi * freq * t)
            if t > duration - 0.1:
                val *= (duration - t) / 0.1
        if t < 0.05:
            val *= t / 0.05
        samples.append(val * 0.8)
    write_wav("success.wav", samples, sample_rate)

def make_warning_sound():
    sample_rate = 22050
    duration = 0.6
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        if (0 <= t < 0.2) or (0.3 <= t < 0.5):
            freq = 280
            val = math.sin(2 * math.pi * freq * t)
            if 0 <= t < 0.05:
                val *= t / 0.05
            elif 0.15 <= t < 0.2:
                val *= (0.2 - t) / 0.05
            elif 0.3 <= t < 0.35:
                val *= (t - 0.3) / 0.05
            elif 0.45 <= t < 0.5:
                val *= (0.5 - t) / 0.05
        else:
            val = 0.0
        samples.append(val * 0.7)
    write_wav("warning.wav", samples, sample_rate)

def make_shutdown_sound():
    sample_rate = 22050
    duration = 1.0
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        freq = 700 - 580 * (t / duration)
        val = math.sin(2 * math.pi * freq * t)
        if t > duration - 0.3:
            val *= (duration - t) / 0.3
        if t < 0.1:
            val *= t / 0.1
        samples.append(val * 0.75)
    write_wav("shutdown.wav", samples, sample_rate)

def ensure_sfx_exist():
    try:
        os.makedirs("Frontend/Sounds", exist_ok=True)
        if not os.path.exists("Frontend/Sounds/boot.wav"):
            make_boot_sound()
        if not os.path.exists("Frontend/Sounds/success.wav"):
            make_success_sound()
        if not os.path.exists("Frontend/Sounds/warning.wav"):
            make_warning_sound()
        if not os.path.exists("Frontend/Sounds/shutdown.wav"):
            make_shutdown_sound()
    except Exception as e:
        print(f"[Sound FX Error]: Procedural compilation failed -> {e}")

if __name__ == "__main__":
    ensure_sfx_exist()
