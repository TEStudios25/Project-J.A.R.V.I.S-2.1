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
            
        segments, info = model.transcribe(temp_wav_path, task="transcribe")
        text = "".join([segment.text for segment in segments]).strip()
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

# Create the recognizer globally so it remembers its settings
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300   # Default responsive 300 threshold for standard USB mic sensitivity
recognizer.pause_threshold = 0.5    # Responsive timeout before auto-submitting

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

def format_punctuation_with_voice_prosody(query: str, audio=None) -> str:
    """
    Analyzes raw speech audio (energy, peak spikes, trailing pauses) to add acoustic expressions:
    - Exclamation Marks (!) for high volume / excited / emphatic speech
    - Ellipses (...) for hesitations, trailing pauses, and slow speech
    - Question Marks (?) for questions or rising pitch intonation
    - Commas (,) for mid-speech pauses
    """
    if not query:
        return ""

    query = query.strip()
    if not query:
        return ""

    # Capitalize first letter
    query = query[0].upper() + query[1:]

    # Calculate acoustic features from audio frame data if available
    peak_rms = 0
    mean_rms = 0
    trailing_pause = False
    mid_pauses = 0

    if audio and hasattr(audio, "frame_data") and audio.frame_data:
        try:
            import struct
            import math
            frame_data = audio.frame_data
            sample_count = len(frame_data) // 2
            if sample_count > 0:
                shorts = struct.unpack(f"<{sample_count}h", frame_data)
                
                # Peak and Mean RMS
                abs_samples = [abs(s) for s in shorts]
                peak_rms = max(abs_samples)
                mean_rms = math.sqrt(sum(s*s for s in shorts) / sample_count)
                
                # Frame chunking (50ms chunks at 16kHz = 800 samples)
                chunk_size = 800
                chunks = [shorts[i:i+chunk_size] for i in range(0, len(shorts), chunk_size) if len(shorts[i:i+chunk_size]) == chunk_size]
                if chunks:
                    chunk_rms = [math.sqrt(sum(s*s for s in c) / len(c)) for c in chunks]
                    
                    # Mid-sentence pauses (chunks below 50 RMS in middle of speech)
                    if len(chunk_rms) > 4:
                        mid_chunks = chunk_rms[1:-2]
                        mid_pauses = sum(1 for r in mid_chunks if r < 50)
                        
                    # Trailing pause / trail off (last 2 chunks are quiet < 40 RMS)
                    if len(chunk_rms) >= 3 and chunk_rms[-1] < 40 and chunk_rms[-2] < 40:
                        trailing_pause = True
        except Exception:
            pass

    # 1. Check for Exclamation / High Energy Spikes (!)
    is_emphatic_word = any(w in query.lower().split() for w in ["stop", "wait", "no", "yes", "hey", "hurry", "quick", "wow", "jarvis", "help", "system", "shut up"])
    is_high_volume = (peak_rms > 5500 or mean_rms > 350)
    
    if is_high_volume or (is_emphatic_word and mean_rms > 200):
        query = query.rstrip('.?!') + "!"
        return query

    # 2. Check for Hesitation / Trailing Off / Pauses (...)
    hesitation_words = ("umm", "uh", "err", "well", "maybe", "i think", "let me see", "like", "so")
    has_hesitation_word = any(query.lower().startswith(hw) or query.lower().endswith(hw) for hw in hesitation_words)
    
    if trailing_pause or has_hesitation_word or mid_pauses >= 3:
        query = query.rstrip('.?!') + "..."
        return query

    # 3. Check for Question Words / Structure (?)
    question_words = (
        "what", "why", "how", "when", "where", "who", "which", 
        "can", "could", "would", "should", "is", "are", "do", 
        "does", "did", "am", "was", "were", "will", "shall", "tell", "show"
    )
    first_word = query.split()[0].lower() if query.split() else ""
    if not query.endswith(('.', '?', '!', ';', ':', '...')):
        if first_word in question_words:
            query += "?"
        else:
            query += "."

    return query

def listen(check_active_func=None) -> str:
    """
    Listens to the microphone with classic 2.1 instant SpeechRecognition.
    """
    global is_calibrated, chosen_mic_index
    with sr.Microphone(device_index=chosen_mic_index) as source:
        # Check if J.A.R.V.I.S. is currently speaking out loud
        is_speaking = False
        import senses.tts_engine
        if senses.tts_engine.speaking_state.get("is_speaking", False):
            is_speaking = True
            
        # Calibrate noise ONCE on startup
        if not is_calibrated and not is_speaking:
            print("\n[System]: Calibrating microphone for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            recognizer.energy_threshold = max(150, min(800, recognizer.energy_threshold))
            is_calibrated = True
            print(f"[System]: Calibration complete. Energy threshold set to: {int(recognizer.energy_threshold)}")
        
        if not is_speaking:
            print("\n[System]: Listening...")
        
        try:
            # Dynamic Listening Logic
            if is_speaking:
                old_pt = recognizer.pause_threshold
                recognizer.pause_threshold = 0.3
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                finally:
                    recognizer.pause_threshold = old_pt
            else:
                recognizer.pause_threshold = 0.5
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
                print("[System]: Processing voice...")
        except sr.WaitTimeoutError:
            # Silence timeout when no one spoke. Quiet return, NO ERROR LOG!
            return ""
        except Exception:
            return ""

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

        # Noise Gate: Filter out zero/extreme low audio
        if rms < 30:
            return ""

        # Pure Direct English STT (Classic 2.1 Engine with Punctuation)
        query = ""
        try:
            query = recognizer.recognize_google(audio).strip()
            if query:
                print(f"[🎙️ Google STT]: Recognized speech: '{query}'")
        except sr.UnknownValueError:
            # Ambient noise / silence. Silently return empty string.
            return ""
        except Exception as e:
            try:
                query = recognize_audio_local(audio)
                if query:
                    print(f"[🎙️ Local Whisper STT]: Recognized speech: '{query}'")
            except Exception:
                return ""

        import re
        query = re.sub(r"\[.*?\]", "", query).strip()
        query = format_punctuation_with_voice_prosody(query, audio)

        # 🚨 REAL-TIME SPEECH BARGE-IN INTERRUPT 🚨
        # If user speaks while J.A.R.V.I.S. is talking out loud, INSTANTLY cut off TTS playback!
        import senses.tts_engine
        if query and senses.tts_engine.speaking_state.get("is_speaking", False):
            print("\n[⚡ Barge-In]: User spoke mid-speech! Cutting off J.A.R.V.I.S. audio playback...")
            senses.tts_engine.stop_audio()

        # Set whisper mode state on TTS engine
        import senses.tts_engine
        if (0 < rms < 110) or "whisper" in query.lower():
            senses.tts_engine.whisper_mode = True
            print(f"[System]: Whisper Mode Active (RMS: {round(rms, 1)})")
        else:
            senses.tts_engine.whisper_mode = False
        
        # Echo-Cancellation & Override Filtering
        if is_speaking:
            override_triggers = ["stop", "shut up", "pause", "quiet", "cancel", "resume"]
            for trigger in override_triggers:
                if trigger in query.lower():
                    print(f"\n[Mr. Pranav (Interrupt)]: {query}")
                    return trigger 
            return ""
        else:
            print(f"[Mr. Pranav]: {query}")
            return query