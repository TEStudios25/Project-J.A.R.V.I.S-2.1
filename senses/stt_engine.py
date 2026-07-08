import speech_recognition as sr
import pygame

# 1. Create the recognizer globally so it remembers its settings
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = False
recognizer.energy_threshold = 280   # Lowered to 280 to easily catch whispers, low voices, and fillers!
recognizer.pause_threshold = 0.8    # Responsive 0.8-second timeout before auto-submitting

is_calibrated = False # Global flag to ensure calibration runs only once on startup

def listen(check_active_func=None) -> str:
    """
    Listens to the microphone with an advanced 'Barge-In' Intercept Mode.
    Normal Mode uses simple pause-based auto-submission with a 0.8-second timeout.
    """
    global is_calibrated
    with sr.Microphone() as source:
        # Check if J.A.R.V.I.S. is currently speaking out loud
        is_speaking = False
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            is_speaking = True
            
        # 🔥 THE FIX: Calibrate noise ONLY once on boot, never on every turn!
        # This speeds up listening start by 0.5s per turn.
        if not is_calibrated and not is_speaking:
            print("\n[🎙️ J.A.R.V.I.S. is calibrating mic for ambient noise...]")
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            is_calibrated = True
            print("[✓] Calibration complete. Standby.")
        
        if not is_speaking:
            print("\n[🎙️ J.A.R.V.I.S. is listening (0.8s pause standby)...]")
        
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
                # NORMAL MODE: Single listen call with 0.8-second pause threshold
                recognizer.pause_threshold = 0.8
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                print("[⚙️ Processing...]")
            
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

            # Translate the audio
            query = recognizer.recognize_google(audio).lower()
            
            # Set whisper mode state on TTS engine
            import senses.tts_engine
            if (0 < rms < 380) or "whisper" in query:
                senses.tts_engine.whisper_mode = True
                print(f"[⚙️ Whisper Mode Active (RMS: {round(rms, 1)})]")
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