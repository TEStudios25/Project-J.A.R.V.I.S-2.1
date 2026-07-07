import ctypes
from ctypes import wintypes

# Win32 Clipboard API constants
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Set explicit argtypes and restypes for Win32 64-bit compatibility
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL

user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL

user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL

user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
user32.IsClipboardFormatAvailable.restype = wintypes.BOOL

user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE

user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HANDLE

kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
kernel32.GlobalLock.restype = ctypes.c_void_p

kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
kernel32.GlobalUnlock.restype = wintypes.BOOL

user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p]
user32.keybd_event.restype = None

def get_clipboard_content() -> str:
    """
    Reads and returns the text currently stored in the Windows clipboard.
    If the clipboard is empty or does not contain text, returns an empty string.
    """
    print("\n[📋 J.A.R.V.I.S. is reading clipboard data stream...]")
    if not user32.OpenClipboard(None):
        return "Error: Could not open Windows clipboard."
    try:
        if user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            h_clip_mem = user32.GetClipboardData(CF_UNICODETEXT)
            if h_clip_mem:
                p_clip_mem = kernel32.GlobalLock(h_clip_mem)
                if p_clip_mem:
                    text = ctypes.c_wchar_p(p_clip_mem).value
                    kernel32.GlobalUnlock(h_clip_mem)
                    return text or ""
    except Exception as e:
        return f"Error while reading clipboard: {str(e)}"
    finally:
        user32.CloseClipboard()
    return "Clipboard is empty or does not contain readable text."

def set_clipboard_content(text: str) -> str:
    """
    Writes the provided text directly to the Windows clipboard.
    This overwrites any previous clipboard contents.
    """
    print(f"\n[📋 J.A.R.V.I.S. is copying text stream to clipboard...]")
    if not user32.OpenClipboard(None):
        return "Error: Could not open Windows clipboard."
    try:
        user32.EmptyClipboard()
        # Allocate movable memory and copy UTF-16 text
        text_bytes = (text + "\0").encode("utf-16le")
        h_global_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
        if h_global_mem:
            p_global_mem = kernel32.GlobalLock(h_global_mem)
            if p_global_mem:
                ctypes.memmove(p_global_mem, text_bytes, len(text_bytes))
                kernel32.GlobalUnlock(h_global_mem)
                user32.SetClipboardData(CF_UNICODETEXT, h_global_mem)
                return "Successfully copied text to clipboard, sir."
    except Exception as e:
        return f"Error writing to clipboard: {str(e)}"
    finally:
        user32.CloseClipboard()
    return "Failed to set clipboard content."

def _send_key(vk_code: int):
    # keybd_event(vk, scan, flags, extra)
    # flag 0: press, flag 2: release
    user32.keybd_event(vk_code, 0, 0, 0)
    user32.keybd_event(vk_code, 0, 2, 0)

def control_system_audio(action: str, percent: int = 10) -> str:
    """
    Controls system volume or media playback.
    action: 'mute', 'volume_up', 'volume_down', 'play_pause', 'next', 'prev'
    percent: The percentage to change volume (default is 10%, which translates to 5 volume steps).
    """
    action = action.lower().strip()
    print(f"\n[🔊 J.A.R.V.I.S. is executing media trigger: '{action}'...]")
    
    try:
        # Convert percent to float then int to handle float strings like "25.0"
        percent_int = int(float(percent))
    except (ValueError, TypeError):
        percent_int = 10
    
    vk_mute = 0xAD
    vk_vol_down = 0xAE
    vk_vol_up = 0xAF
    vk_play_pause = 0xB3
    vk_next = 0xB0
    vk_prev = 0xB1

    if action == "mute":
        _send_key(vk_mute)
        return "Successfully toggled system mute state."
    elif action == "volume_up":
        # Each volume stroke on Windows usually changes volume by 2%
        presses = int(max(1, percent_int // 2))
        for _ in range(presses):
            _send_key(vk_vol_up)
        return f"Increased system volume by approximately {percent_int}%."
    elif action == "volume_down":
        presses = int(max(1, percent_int // 2))
        for _ in range(presses):
            _send_key(vk_vol_down)
        return f"Decreased system volume by approximately {percent_int}%."
    elif action == "play_pause":
        _send_key(vk_play_pause)
        return "Toggled system media playback (Play/Pause)."
    elif action in ["pause", "stop"]:
        # Only send key if currently playing to prevent double toggling
        if is_media_playing():
            _send_key(vk_play_pause)
            return "Successfully paused active system media."
        return "System media is already paused."
    elif action in ["play", "resume"]:
        # Only send key if currently paused to prevent double toggling
        if not is_media_playing():
            _send_key(vk_play_pause)
            return "Successfully resumed system media playback."
        return "System media is already playing."
    elif action == "next":
        _send_key(vk_next)
        return "Skipped to next media track."
    elif action == "prev":
        _send_key(vk_prev)
        return "Returned to previous media track."
    else:
        return f"Unknown system media command: '{action}'. Choose from 'mute', 'volume_up', 'volume_down', 'play_pause', 'pause', 'resume', 'next', 'prev'."

async def _is_media_playing_async() -> bool:
    try:
        from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
        sessions = await MediaManager.request_async()
        current_session = sessions.get_current_session()
        if current_session:
            info = current_session.get_playback_info()
            if info:
                # Playback status: 4 = Playing
                return info.playback_status == 4
    except Exception:
        pass
    return False

def is_media_playing() -> bool:
    """Returns True if any active Windows global media session (Spotify, Chrome YouTube, etc.) is currently playing."""
    import asyncio
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(lambda: asyncio.run(_is_media_playing_async())).result()
        else:
            return asyncio.run(_is_media_playing_async())
    except Exception:
        try:
            return asyncio.run(_is_media_playing_async())
        except Exception:
            return False
