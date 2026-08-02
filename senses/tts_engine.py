import asyncio
import edge_tts
import pygame
import os
import re
import io
import numpy as np

# Initialize the audio mixer safely once when the module loads
try:
    pygame.mixer.init()
except Exception:
    pass

def _ensure_mixer_init():
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except Exception:
            pass

# Global state to keep the script alive while paused
is_paused = False
media_was_paused = False
whisper_mode = False
speaking_state = {"is_speaking": False}
current_channel = None

def _apply_jarvis_dsp_filter(sound) -> pygame.mixer.Sound:
    """Applies a custom real-time neural DSP filter to make the voice deep, futuristic, and metallic."""
    try:
        # Extract raw array from Pygame Sound object
        arr = pygame.sndarray.array(sound)
        if len(arr) == 0:
            return sound
            
        # 1. Pitch Shift Down: nearest-neighbor resampling by 1.10x (Deepens the voice)
        num_samples = len(arr)
        indices = np.round(np.linspace(0, num_samples - 1, int(num_samples * 1.10))).astype(np.int32)
        indices = np.clip(indices, 0, num_samples - 1)
        arr_deep = arr[indices]
        
        # 2. Metallic Ring Modulator: 45Hz LFO (futuristic carrier buzz)
        sample_rate = 44100
        mixer_settings = pygame.mixer.get_init()
        if mixer_settings:
            sample_rate = mixer_settings[0]
            
        new_len = len(arr_deep)
        t = np.linspace(0, new_len / sample_rate, new_len, endpoint=False)
        # LFO carrier wave (combines deep pitch and metallic frequency)
        carrier = 0.82 + 0.18 * np.sin(2 * np.pi * 45 * t)
        
        if len(arr_deep.shape) == 2:
            arr_modulated = (arr_deep * carrier[:, np.newaxis]).astype(np.int16)
        else:
            arr_modulated = (arr_deep * carrier).astype(np.int16)
            
        return pygame.sndarray.make_sound(arr_modulated)
    except Exception as e:
        print(f"[DSP Filter Error]: {e}")
        return sound

def stop_audio():
    """Instantly kills the audio and dumps it from memory."""
    global is_paused, media_was_paused, current_channel
    _ensure_mixer_init()
    is_paused = False  # Reset pause state
    try:
        if current_channel:
            current_channel.stop()
            current_channel = None
            print("\n[System]: J.A.R.V.I.S. audio terminated.")
    except Exception:
        pass
        
    # Restore background media if it was paused
    if media_was_paused:
        try:
            from tools.system_media import _send_key
            print("[System]: J.A.R.V.I.S. is resuming background playback...")
            _send_key(0xB3) # VK_MEDIA_PLAY_PAUSE
        except Exception:
            pass
        media_was_paused = False

def pause_audio():
    """Pauses the current TTS playback."""
    global is_paused, current_channel
    _ensure_mixer_init()
    is_paused = True
    try:
        if current_channel:
            current_channel.pause()
            print("\n[System]: J.A.R.V.I.S. audio paused.")
    except Exception:
        pass

def resume_audio():
    """Resumes the paused TTS playback."""
    global is_paused, current_channel
    _ensure_mixer_init()
    is_paused = False
    try:
        if current_channel:
            current_channel.unpause()
            print("\n[System]: J.A.R.V.I.S. audio resumed.")
    except Exception:
        pass

async def _stream_fast_audio(text: str, voice: str = None):
    """Generates ultra-realistic 24kHz Neural AI audio in RAM with dynamic emotional prosody."""
    global is_paused, whisper_mode, current_channel
    
    if not voice:
        voice = os.getenv("JARVIS_VOICE", "en-US-ChristopherNeural")
        
    # Analyze text ending for dynamic emotional prosody (rate & pitch)
    rate = "+0%"
    pitch = "+0Hz"
    
    clean_strip = text.strip()
    if clean_strip.endswith("!"):
        rate = "+3%"
        pitch = "+3Hz"   # Energetic, expressive, emphatic
    elif clean_strip.endswith("..."):
        rate = "-8%"
        pitch = "-2Hz"   # Thoughtful, reflective, calm
    elif clean_strip.endswith("?"):
        pitch = "+2Hz"   # Inquisitive intonation
        
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    
    # Stream chunks directly into RAM
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
            
    if not audio_data:
        return
        
    audio_stream = io.BytesIO(audio_data)
    _ensure_mixer_init()
    
    try:
        # High-Fidelity 24kHz Stereo Neural Audio (Pure, uncompressed, expressive human quality)
        processed_sound = pygame.mixer.Sound(audio_stream)
        current_channel = processed_sound.play()
        
        # Adjust volume for whisper mode focus
        if whisper_mode:
            current_channel.set_volume(0.35)
        else:
            current_channel.set_volume(1.0)
            
        # The main play loop: remains alive if playing or paused
        while (current_channel and current_channel.get_busy()) or is_paused:
            await asyncio.sleep(0.04)
            
    except Exception as e:
        print(f"[Mixer Error]: Playback failed -> {e}")
        return
    finally:
        current_channel = None

def normalize_speech_text(text: str) -> str:
    """Transforms raw text into natural, fluid human spoken English with realistic pause phrasing."""
    if not text:
        return ""

    # Strip markdown symbols (*, #, _, ~, `, >, |)
    clean = re.sub(r'[*#_~`>|]', '', text)
    # Strip bracketed logs like [System: ...] or [TONE: ...]
    clean = re.sub(r'\[.*?\]', '', clean)

    # Expand technical symbols into natural spoken words
    clean = re.sub(r'°C', ' degrees Celsius', clean)
    clean = re.sub(r'°F', ' degrees Fahrenheit', clean)
    clean = re.sub(r'%', ' percent', clean)
    clean = re.sub(r'\be\.g\.\b', 'for example', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\bi\.e\.\b', 'that is', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\betc\.\b', 'et cetera', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\bvs\.\b|\bvs\b', 'versus', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(&)\b', 'and', clean)
    clean = re.sub(r'\b(@)\b', 'at', clean)

    # Replace em-dashes, double hyphens, and colons with natural pause commas
    clean = re.sub(r'—|--', ', ', clean)
    clean = re.sub(r':', ', ', clean)
    clean = re.sub(r'\s+-\s+', ', ', clean)

    # Strip emojis / non-ascii characters
    clean = clean.encode('ascii', 'ignore').decode('ascii')

    # Ensure spaces after commas and periods for natural speech pause pacing
    clean = re.sub(r',([^\s])', r', \1', clean)
    clean = re.sub(r'\.([^\s\.\?\!])', r'. \1', clean)

    return clean.strip()

def speak(text: str) -> str:
    """Reads text aloud using Neural TTS with natural human spoken sentence phrasing."""
    global media_was_paused
    media_was_paused = False
    speaking_state["is_speaking"] = True

    # Check if media is currently playing
    try:
        from tools.system_media import is_media_playing, _send_key
        if is_media_playing():
            print("\n[System]: J.A.R.V.I.S. is pausing background playback for focus...")
            _send_key(0xB3) # Send VK_MEDIA_PLAY_PAUSE to pause
            media_was_paused = True
            import time
            time.sleep(0.3)
    except Exception:
        pass

    clean_text = normalize_speech_text(text)
    
    try:
        asyncio.run(_stream_fast_audio(clean_text))
        
        # Resume background media if we paused it
        if media_was_paused:
            try:
                from tools.system_media import _send_key
                print("[System]: J.A.R.V.I.S. is resuming background playback...")
                _send_key(0xB3) # VK_MEDIA_PLAY_PAUSE
            except Exception:
                pass
            media_was_paused = False
            
        return "Audio finished."
    except Exception as e:
        print(f"\n[ERROR]: Fast TTS Engine failed -> {e}")
        if media_was_paused:
            try:
                from tools.system_media import _send_key
                _send_key(0xB3)
            except Exception:
                pass
            media_was_paused = False
        return f"Error: {str(e)}"
    finally:
        speaking_state["is_speaking"] = False