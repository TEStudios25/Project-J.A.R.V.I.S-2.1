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
    """Generates audio in RAM, applies real-time metallic DSP filter, and plays it instantly."""
    global is_paused, whisper_mode, current_channel
    
    if not voice:
        voice = os.getenv("JARVIS_VOICE", "en-GB-RyanNeural")
        
    # If whisper mode is active, choose a softer, whispering voice (always male RyanNeural)
    if whisper_mode:
        voice = os.getenv("JARVIS_VOICE", "en-GB-RyanNeural")
        
    communicate = edge_tts.Communicate(text, voice)
    
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
        raw_sound = pygame.mixer.Sound(audio_stream)
        
        # Apply deep, robotic, futuristic vocoder DSP filter!
        # (Skip DSP filter for whisper mode to preserve whisper soft texture)
        if not whisper_mode:
            processed_sound = _apply_jarvis_dsp_filter(raw_sound)
        else:
            processed_sound = raw_sound
            
        current_channel = processed_sound.play()
        
        # Adjust volume for whisper mode focus
        if whisper_mode:
            current_channel.set_volume(0.32)
        else:
            current_channel.set_volume(1.0)
            
        # The main play loop: remains alive if playing or paused
        while (current_channel and current_channel.get_busy()) or is_paused:
            await asyncio.sleep(0.05)
            
    except Exception as e:
        print(f"[Mixer Error]: Playback failed -> {e}")
        return
    finally:
        current_channel = None

def speak(text: str) -> str:
    """Reads text aloud using Neural TTS. Strips markdown and emojis for speed."""
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
    
    # 1. Strip out markdown symbols (*, #, _, etc.) 
    clean_text = re.sub(r'[*#_~`]', '', text)
    
    # Force a natural TTS pause/break by replacing em-dashes, double hyphens, and clause hyphens with a semicolon
    clean_text = re.sub(r'—|--', '; ', clean_text)
    clean_text = re.sub(r'\s+-\s+', '; ', clean_text)
    
    # 2. Strip emojis
    clean_text = clean_text.encode('ascii', 'ignore').decode('ascii')
    
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