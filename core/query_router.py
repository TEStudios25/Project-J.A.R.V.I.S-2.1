import re
from typing import Optional

AUDIO_STOP = {"stop", "shut up", "jarvis stop", "clear audio", "quiet", "cancel"}
AUDIO_PAUSE = {"pause", "jarvis pause", "hold on"}
AUDIO_RESUME = {"continue", "resume", "jarvis continue", "go ahead"}

WEATHER_PATTERNS = r"\b(weather|temperature|forecast|rain|humidity|how hot|how cold)\b"
SYSTEM_PATTERNS = r"\b(cpu|ram|memory usage|disk space|battery|gpu|system status|system report|performance)\b"
SCHEDULE_PATTERNS = r"\b(schedule|reminder|calendar|what do i have today|my tasks)\b"
SEARCH_PATTERNS = r"\b(latest|current|today|now|news|price|who is|what is happening|search for|look up)\b"
CLIPBOARD_PATTERNS = r"\b(clipboard|copy to|read copy|what's copied|write to clipboard)\b"
VISION_PATTERNS = r"\b(look at screen|analyze screen|ocr|read my screen|scan screen|analyze image|ocr image|look at this image)\b"
VOLUME_PATTERNS = r"\b(volume|mute|unmute|play_pause|play/pause|next track|previous track|skip song)\b"
FOCUS_PATTERNS = r"\b(active window|focused window|foreground window|what app|what am i looking at)\b"
HOTKEY_PATTERNS = r"\b(close window|copy all|lock pc|lock computer|switch app|search macro)\b"
FILE_PATTERNS = r"\b(read file|write file|create file|append file|list files|project files|code file)\b"


def normalize(text: str) -> str:
    return text.lower().strip()


def classify_audio_command(text: str) -> Optional[str]:
    clean = normalize(text)
    if clean in AUDIO_STOP:
        return "stop"
    if clean in AUDIO_PAUSE:
        return "pause"
    if clean in AUDIO_RESUME:
        return "resume"
    return None


def build_routing_directive(user_text: str) -> str:
    """Adds lightweight intent hints so Gemini picks the right tool more reliably."""
    clean = normalize(user_text)
    hints = []

    if re.search(WEATHER_PATTERNS, clean):
        hints.append("Use get_weather for weather or temperature questions.")
    if re.search(SYSTEM_PATTERNS, clean):
        hints.append("Use get_full_system_report or related system telemetry tools.")
    if re.search(SCHEDULE_PATTERNS, clean):
        hints.append("Use get_today_schedule or add_reminder as appropriate.")
    if re.search(r"\b(play|song|music|youtube)\b", clean):
        hints.append("Use play_song_on_youtube or search_youtube for music requests.")
    if re.search(r"\b(open|launch|start)\b", clean):
        hints.append("Use open_application or open_website for launch requests.")
    if re.search(r"\b(email|mail|send a message to)\b", clean):
        hints.append("Use send_email for outbound mail.")
    if re.search(r"\b(image|picture|draw|generate art)\b", clean):
        hints.append("Use generate_image for visual generation.")
    if re.search(r"\b(clean|cleanup|temp files|malware|virus scan|defender)\b", clean):
        hints.append("Use clean_temp_files or run_malware_scan for maintenance.")
    if re.search(CLIPBOARD_PATTERNS, clean):
        hints.append("Use get_clipboard_content or set_clipboard_content for clipboard tasks.")
    if re.search(VISION_PATTERNS, clean):
        hints.append("Use analyze_current_screen or analyze_image_file for screen and image analysis.")
    if re.search(VOLUME_PATTERNS, clean):
        hints.append("Use control_system_audio for system volume, mute, or media control action.")
    if re.search(FOCUS_PATTERNS, clean):
        hints.append("Use get_active_window_title for querying active or foreground focused windows.")
    if re.search(HOTKEY_PATTERNS, clean):
        hints.append("Use execute_system_hotkey for Alt+F4, Alt+Tab, Ctrl+C copy, or Lock Workstation shortcuts.")
    if re.search(FILE_PATTERNS, clean):
        hints.append("Use read_project_file, write_project_file, append_project_file, or list_project_files for file system operations.")
    if re.search(SEARCH_PATTERNS, clean) or re.search(r"\?$", user_text.strip()):
        hints.append("Use search_the_web before answering factual or live-data questions.")

    if not hints:
        hints.append("Choose the best tool automatically. Prefer tools over guessing.")

    return "Routing hints: " + " ".join(hints)
