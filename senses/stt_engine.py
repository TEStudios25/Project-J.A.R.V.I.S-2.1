import speech_recognition as sr
import pygame
import os
import sys

# Prevent OpenMP runtime duplicate initialization crash
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["CT2_FORCE_CPU_ISA"] = "GENERIC"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            print("\n[🎙️ STT Engine]: Initializing Local Faster-Whisper (tiny, int8 CPU)...")
            _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            print("[🎙️ STT Engine]: Local Faster-Whisper Model Ready.")
        except Exception as e:
            print(f"[🎙️ STT Engine Error]: Failed to load Faster-Whisper: {e}")
    return _whisper_model

def init_whisper_async():
    import threading
    threading.Thread(target=get_whisper_model, daemon=True).start()

# Initialize Whisper model in parallel on boot to eliminate lag
init_whisper_async()

def recognize_audio_local(audio) -> str:
    model = get_whisper_model()
    if model is None:
        return ""
    
    scratch_dir = r"C:\Users\This Pc\.gemini\antigravity\scratch"
    os.makedirs(scratch_dir, exist_ok=True)
    temp_wav_path = os.path.join(scratch_dir, "temp_voice.wav")
    
    try:
        with open(temp_wav_path, "wb") as f:
            f.write(audio.get_wav_data())
            
        segments, info = model.transcribe(temp_wav_path, task="translate")
        text = "".join([segment.text for segment in segments]).strip().lower()
        return text
    except Exception as e:
        print(f"[🎙️ STT Engine]: Local transcription error -> {e}")
        return ""
    finally:
        try:
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
        except Exception:
            pass


# 1. Create the recognizer globally so it remembers its settings
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = False
recognizer.energy_threshold = 280   # Lowered to 280 to easily catch whispers, low voices, and fillers!
recognizer.pause_threshold = 0.8    # Responsive 0.8-second timeout before auto-submitting

is_calibrated = False # Global flag to ensure calibration runs only once on startup

def get_best_microphone_index():
    import pyaudio
    p = pyaudio.PyAudio()
    try:
        device_count = p.get_device_count()
        # Priority 1: Real USB Audio Devices
        for i in range(device_count):
            try:
                dev_info = p.get_device_info_by_index(i)
                if dev_info.get('maxInputChannels', 0) > 0:
                    name = dev_info.get('name', '').lower()
                    if "usb audio device" in name or "usb microphone" in name or "usb mic" in name:
                        return i
            except Exception:
                pass
        # Priority 2: Standard built-in mics (excluding DroidCam and mapper)
        for i in range(device_count):
            try:
                dev_info = p.get_device_info_by_index(i)
                if dev_info.get('maxInputChannels', 0) > 0:
                    name = dev_info.get('name', '').lower()
                    if "sound mapper" not in name and "droidcam" not in name:
                        return i
            except Exception:
                pass
        # Priority 3: Fall back to default
        try:
            return p.get_default_input_device_info().get('index')
        except Exception:
            return None
    except Exception:
        return None
    finally:
        try:
            p.terminate()
        except Exception:
            pass

chosen_mic_index = get_best_microphone_index()

def listen(check_active_func=None) -> str:
    """
    Listens to the microphone with an advanced 'Barge-In' Intercept Mode.
    Normal Mode uses simple pause-based auto-submission with a 0.8-second timeout.
    """
    global is_calibrated, chosen_mic_index
    with sr.Microphone(device_index=chosen_mic_index) as source:
        # Check if J.A.R.V.I.S. is currently speaking out loud
        is_speaking = False
        import senses.tts_engine
        if senses.tts_engine.speaking_state.get("is_speaking", False):
            is_speaking = True
            
        # THE FIX: Calibrate noise ONLY once on boot, never on every turn!
        # This speeds up listening start by 0.5s per turn.
        if not is_calibrated and not is_speaking:
            print("\n[System]: Calibrating microphone for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            # Increase sensitivity slightly to catch whispers, clamp max to 600 to prevent fan noise locks
            recognizer.energy_threshold = min(600, max(90, recognizer.energy_threshold * 0.80))
            is_calibrated = True
            print(f"[System]: Calibration complete. Energy threshold set to: {int(recognizer.energy_threshold)}")
        
        if not is_speaking:
            print("\n[System]: Listening...")
        
        try:
            # Dynamic Listening Logic
            if is_speaking:
                # BARGE-IN MODE: Listen in short bursts without recalibrating
                # Use small pause threshold for quick barge-in overrides
                old_pt = recognizer.pause_threshold
                recognizer.pause_threshold = 0.4
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                finally:
                    recognizer.pause_threshold = old_pt
            else:
                # NORMAL MODE: Stable long-timeout to keep stream active
                recognizer.pause_threshold = 0.8
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=12)
                print("[System]: Processing voice...")
            
            # Calculate RMS energy of the recorded audio
            import struct
            import math
            try:
                frame_data = audio.frame_data
                count = len(frame_data) // 2
                if count > 0:
                    shorts = struct.unpack(f"<{count}h", frame_data)
                    rms = math.sqrt(sum(s*s for s in shorts) / count)
                else:
                    rms = 0
            except Exception:
                rms = 0

            # Translate the audio (Telugu/others to English)
            use_local = os.getenv("USE_LOCAL_WHISPER", "true").lower() == "true"
            query = ""
            if use_local:
                try:
                    query = recognize_audio_local(audio)
                except Exception as e:
                    print(f"[System]: Local Whisper error: {e}")
            
            if not query:
                try:
                    query = recognizer.recognize_google(audio).lower()
                except Exception as e:
                    # Reraise or handle to catch UnknownValueError / RequestError
                    raise e

            
            # Set whisper mode state on TTS engine
            import senses.tts_engine
            if (0 < rms < 120) or "whisper" in query:
                senses.tts_engine.whisper_mode = True
                print(f"[System]: Whisper Mode Active (RMS: {round(rms, 1)})")
            else:
                senses.tts_engine.whisper_mode = False
            
            # Echo-Cancellation & Override Filtering
            if is_speaking:
                # We search the messy overlapping audio for your command
                override_triggers = ["stop", "shut up", "pause", "quiet", "cancel", "resume"]
                
                for trigger in override_triggers:
                    if trigger in query:
                        print(f"\n[Mr. Pranav (Interrupt)]: {query}")
                        # Return exactly what you said ('stop', 'pause', etc.)
                        return trigger 
                
                # If no command is found, it was just his own echo. Delete it!
                return ""
            else:
                # Normal speech when the room was quiet
                print(f"[Mr. Pranav]: {query}")
                return query
            
        except sr.WaitTimeoutError:
            # The short burst timed out without hearing anyone. Keep looping quietly.
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"[System]: Network error -> {e}")
            return ""
        except Exception as e:
            print(f"[System]: STT Error -> {e}")
            return ""

# ===============================================================
# 🧪 ISOLATED TESTING BLOCK
# ===============================================================
if __name__ == "__main__":
    print("\nInitiating STT Intercept diagnostics...")
    while True:
        result = listen()
        if result:
            print(f"✅ Captured: {result}")
            if result in ["exit", "stop", "quit"]:
                break