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
            _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8", cpu_threads=1)
            print("[🎙️ STT Engine]: Local Faster-Whisper Model Ready.")
        except Exception as e:
            print(f"[🎙️ STT Engine Error]: Failed to load Faster-Whisper: {e}")
    return _whisper_model

def init_whisper_async():
    import threading
    threading.Thread(target=get_whisper_model, daemon=True).start()

# Background initialization will be deferred to post-GUI startup to avoid DLL loader conflicts

def recognize_audio_gemini(audio_path: str) -> str:
    """
    Uploads voice recording to Gemini Cloud for translation/transcription
    using gemini-3.1-flash-lite. Exerts 0% CPU and 0% RAM.
    """
    import google.generativeai as genai
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    model = genai.GenerativeModel(model_name=model_name)
    
    try:
        print(f"[🎙️ STT Engine]: Translating voice sample via Gemini Cloud ({model_name})...")
        audio_file = genai.upload_file(path=audio_path)
        
        # Wait for file processing (instant for short voice clips)
        import time
        for _ in range(15):
            file_status = genai.get_file(audio_file.name)
            if file_status.state.name == "ACTIVE":
                break
            elif file_status.state.name == "FAILED":
                raise ValueError("Gemini cloud audio processing failed.")
            time.sleep(0.3)
            
        prompt = (
            "Listen to this voice recording. Transcribe the speech and translate it directly into English. "
            "Output ONLY the translated English text, verbatim, with no markdown, conversational wrappers, "
            "explanations, or warnings. If there is no speech, output nothing."
        )
        response = model.generate_content([audio_file, prompt])
        
        # Silently delete temp cloud file
        try:
            audio_file.delete()
        except Exception:
            pass
            
        return response.text.strip() if response.text else ""
    except Exception as e:
        print(f"[🎙️ STT Engine]: Gemini Cloud STT Error -> {e}")
        return ""

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
recognizer.pause_threshold = 0.5    # Responsive 0.5-second timeout before auto-submitting

is_calibrated = False # Global flag to ensure calibration runs only once on startup

def get_best_microphone_index():
    import pyaudio
    p = pyaudio.PyAudio()
    try:
        device_count = p.get_device_count()
        
        # 0. User override via environment variables
        env_index = os.getenv("JARVIS_MIC_INDEX")
        if env_index is not None:
            try:
                idx = int(env_index)
                if 0 <= idx < device_count:
                    info = p.get_device_info_by_index(idx)
                    print(f"[🎙️ STT Engine]: Selected Mic Override Index {idx} ({info.get('name')})")
                    return idx
            except Exception:
                pass
                
        env_name = os.getenv("JARVIS_MIC_NAME")
        if env_name:
            env_name_lower = env_name.lower()
            for i in range(device_count):
                try:
                    dev_info = p.get_device_info_by_index(i)
                    if dev_info.get('maxInputChannels', 0) > 0:
                        name = dev_info.get('name', '').lower()
                        if env_name_lower in name:
                            print(f"[🎙️ STT Engine]: Selected Mic Match '{env_name}' at Index {i} ({dev_info.get('name')})")
                            return i
                except Exception:
                    pass

        # Priority 1: Real USB Audio Devices
        for i in range(device_count):
            try:
                dev_info = p.get_device_info_by_index(i)
                if dev_info.get('maxInputChannels', 0) > 0:
                    name = dev_info.get('name', '').lower()
                    if "usb audio device" in name or "usb microphone" in name or "usb mic" in name:
                        print(f"[🎙️ STT Engine]: Auto-detected USB Mic at Index {i} ({dev_info.get('name')})")
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
                        print(f"[🎙️ STT Engine]: Auto-detected Built-in Mic at Index {i} ({dev_info.get('name')})")
                        return i
            except Exception:
                pass
        # Priority 3: Fall back to default
        try:
            default_idx = p.get_default_input_device_info().get('index')
            print(f"[🎙️ STT Engine]: Fallback to Default Mic at Index {default_idx}")
            return default_idx
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
                recognizer.pause_threshold = 0.5
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
            use_local = os.getenv("USE_LOCAL_WHISPER", "false").lower() == "true" # Default to Gemini Cloud STT (highly accurate)
            query = ""
            if use_local:
                try:
                    query = recognize_audio_local(audio)
                except Exception as e:
                    print(f"[System]: Local Whisper error: {e}")
            else:
                # Use Gemini Cloud STT
                try:
                    scratch_dir = r"C:\Users\This Pc\.gemini\antigravity\scratch"
                    os.makedirs(scratch_dir, exist_ok=True)
                    temp_wav_path = os.path.join(scratch_dir, "temp_voice.wav")
                    with open(temp_wav_path, "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    query = recognize_audio_gemini(temp_wav_path)
                    
                    if os.path.exists(temp_wav_path):
                        os.remove(temp_wav_path)
                except Exception as e:
                    print(f"[System]: Gemini Cloud STT error: {e}")
            
            if not query:
                try:
                    query = recognizer.recognize_google(audio).lower()
                except Exception as e:
                    # Reraise or handle to catch UnknownValueError / RequestError
                    raise e

            # Inject acoustic expression markers into the query text based on physical volume (RMS)
            if query.strip():
                if rms > 1600:
                    query = f"[SPOKEN LOUDLY] {query.upper()}!!!"
                    print(f"[System]: Acoustic Expression: Shouting/Loud Voice Detected (RMS: {round(rms, 1)})")
                elif 0 < rms < 110:
                    query = f"[WHISPERED] {query.lower()}"
                    print(f"[System]: Acoustic Expression: Whisper Detected (RMS: {round(rms, 1)})")

            # Set whisper mode state on TTS engine
            import senses.tts_engine
            if (0 < rms < 110) or "whisper" in query.lower() or "[whispered]" in query.lower():
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