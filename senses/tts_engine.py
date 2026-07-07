import asyncio
import edge_tts
import pygame
import os
import re
import io

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

def stop_audio():
    """Instantly kills the audio and dumps it from memory."""
    global is_paused, media_was_paused
    _ensure_mixer_init()
    is_paused = False  # Reset pause state
    try:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            print("\n[🔇 J.A.R.V.I.S. audio terminated.]")
    except Exception:
        pass
        
    # Restore background media if it was paused
    if media_was_paused:
        try:
            from tools.system_media import _send_key
            print("[🔊 J.A.R.V.I.S. is resuming background playback...]")
            _send_key(0xB3) # VK_MEDIA_PLAY_PAUSE
        except Exception:
            pass
        media_was_paused = False

def pause_audio():
    """Pauses the current TTS playback."""
    global is_paused
    _ensure_mixer_init()
    is_paused = True
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.pause()
            print("\n[⏸️ J.A.R.V.I.S. audio paused.]")
    except Exception:
        pass

def resume_audio():
    """Resumes the paused TTS playback."""
    global is_paused
    _ensure_mixer_init()
    is_paused = False
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.unpause()
            print("\n[▶️ J.A.R.V.I.S. audio resumed.]")
    except Exception:
        pass

async def _stream_fast_audio(text: str, voice: str = "en-GB-RyanNeural"):
    """Generates audio in RAM and plays it instantly without saving to disk."""
    global is_paused, whisper_mode
    
    # If whisper mode is active, choose a softer, whispering voice
    if whisper_mode:
        voice = "en-US-JennyNeural"
        
    communicate = edge_tts.Communicate(text, voice)
    
    # Stream chunks directly into system memory (Bypassing Hard Drive completely!)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
            
    # Load the audio directly from Random Access Memory (RAM)
    audio_stream = io.BytesIO(audio_data)
    _ensure_mixer_init()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.load(audio_stream)
    except Exception as e:
        print(f"[Mixer Error]: Load failed -> {e}")
        return
    
    # Lower output volume for whisper mode focus
    if whisper_mode:
        pygame.mixer.music.set_volume(0.32)
    else:
        pygame.mixer.music.set_volume(1.0)
        
    pygame.mixer.music.play()
    
    # THE MAGIC LOOP: Stays alive if playing OR if paused!
    while pygame.mixer.music.get_busy() or is_paused:
        pygame.time.Clock().tick(10)
        
    pygame.mixer.music.unload()

def speak(text: str) -> str:
    """Reads text aloud using Neural TTS. Strips markdown and emojis for speed."""
    global media_was_paused
    media_was_paused = False
    
    # Check if media is currently playing
    try:
        from tools.system_media import is_media_playing, _send_key
        if is_media_playing():
            print("\n[🔊 J.A.R.V.I.S. is pausing background playback for focus...]")
            _send_key(0xB3) # Send VK_MEDIA_PLAY_PAUSE to pause
            media_was_paused = True
            # Small delay to ensure Windows media controller registers pause state before J.A.R.V.I.S. speaks
            time.sleep(0.3)
    except Exception:
        pass
    
    # 1. Strip out markdown symbols (*, #, _, etc.) 
    clean_text = re.sub(r'[*#_~`]', '', text)
    
    # 2. Strip emojis (forces standard text only)
    # This stops the TTS from awkwardly pausing to read things like "Smiling face emoji"
    clean_text = clean_text.encode('ascii', 'ignore').decode('ascii')
    
    try:
        import time
        asyncio.run(_stream_fast_audio(clean_text))
        
        # Resume background media if we paused it
        if media_was_paused:
            try:
                from tools.system_media import _send_key
                print("[🔊 J.A.R.V.I.S. is resuming background playback...]")
                _send_key(0xB3) # VK_MEDIA_PLAY_PAUSE
            except Exception:
                pass
            media_was_paused = False
            
        return "Audio finished."
    except Exception as e:
        print(f"\n[ERROR]: Fast TTS Engine failed -> {e}")
        # Clean up on error
        if media_was_paused:
            try:
                from tools.system_media import _send_key
                _send_key(0xB3)
            except Exception:
                pass
            media_was_paused = False
        return f"Error: {str(e)}"