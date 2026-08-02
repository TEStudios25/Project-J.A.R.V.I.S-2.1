import os
import sys
import time
import threading

# Prevent OpenMP runtime conflict crashes (0xC0000005) when loading numpy/ctranslate2 DLLs
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["CT2_FORCE_CPU_ISA"] = "GENERIC"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# Windows terminals often default to cp1252; allow emoji/log output during boot.
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

# --- CRITICAL LOAD ORDER WORKAROUND ---
# Load and initialize Faster-Whisper FIRST to avoid Windows DLL loader lock / memory allocation conflicts
# with PyQt5 / pywebview (Chromium WebView2) libraries.
try:
    print("[System]: Pre-initializing Faster-Whisper model in clean memory space...")
    from senses.stt_engine import get_whisper_model
    get_whisper_model()
except Exception as e:
    print(f"[Warning]: Failed to pre-initialize Faster-Whisper: {e}")

from PyQt5.QtWidgets import QApplication

# --- PATH ENFORCEMENT ---
# Ensures main.py can smoothly read all folders (core, senses, tools)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Graphic Interface, Mouth, and 3D Holographic Core Window
from gui.interface import JarvisGUI
from gui.orb_window import start_orb_thread
from senses.tts_engine import speak

# (Note: If your security.py is inside the 'core' folder, change this to: from core.security import verify_access)
from core.security import verify_access 

def system_boot_sequence(workspace_ref=None):
    """Plays the epic sci-fi startup terminal sequence and verbal greeting."""
    import random
    import datetime

    print("\n=======================================================")
    print("||        PROJECT J.A.R.V.I.S. 2.x INITIATED         ||")
    print("=======================================================")
    time.sleep(0.4)

    # 1. Futuristic Boot Dialogue Pool (Picks 3 random lines on each start!)
    boot_dialogue_pool = [
        ("🧠", "Allocating neural network memory modules and quantum cognitive buffers"),
        ("⚙️", "Calibrating Voice, Vision, and Multimodal Neural interfaces"),
        ("📡", "Establishing encrypted global server telemetry and satellite sync"),
        ("🔋", "Powering up core sub-routines and establishing cybernetic environment radar"),
        ("⚡", "Pre-heating active workspace modules and executing zero-latency system diagnostics")
    ]
    
    # Pick 3 random futuristic lines for lively, non-repeating boot status sequence
    selected_dialogues = random.sample(boot_dialogue_pool, 3)
    for icon, text in selected_dialogues:
        print(f"[{icon} System]: {text}...")
        time.sleep(0.3)
        
    print("[✅ System]: Graphic User Interface locked, loaded, and fully operational.")
    time.sleep(0.3)

    # 2. Spoken Greeting Pool (Randomly selected per start to stay lively and non-repetitive!)
    hour = datetime.datetime.now().hour
    time_greeting = "Good morning" if hour < 12 else ("Good afternoon" if 12 <= hour < 17 else "Good evening")
    
    greeting_pool = [
        f"{time_greeting}, Sir. Systems are online, quantum telemetry is green, and I am locked in for your commands.",
        f"{time_greeting}, Sir. All neural pathways are firing at maximum efficiency. Let's make things happen—no cap.",
        f"Systems locked and loaded, Sir. Dual-chat neural routing is online and ready. What's on the agenda today?",
        f"{time_greeting}, Sir. Active memory buffers are clear, vision and speech engines calibrated. Ready whenever you are.",
        f"J.A.R.V.I.S. 2.2 fully operational, Sir. All security protocols cleared. How can I assist you right now?"
    ]
    
    final_msg = random.choice(greeting_pool)

    print(f"\n[🤖 J.A.R.V.I.S.]: {final_msg}\n")
    speak(final_msg)

    # Start autonomous reminder service ONLY AFTER boot dialogues complete
    if workspace_ref and hasattr(workspace_ref, "reminder_service"):
        time.sleep(1.0)
        workspace_ref.reminder_service.start()

def main():
    # 1. Initialize the QApplication first so graphical windows/dialogs can render
    app = QApplication(sys.argv)
    
    # 2. Run mainframe security verification dialog
    verify_access()
        
    # 3. Launch 3D Holographic Cyan Orb Window concurrently
    start_orb_thread()

    # 4. Launch the Front-Face GUI
    workspace = JarvisGUI()
    workspace.showMaximized()

    # 5. Start the visual boot logs and voice greeting in the background
    threading.Thread(target=system_boot_sequence, args=(workspace,), daemon=True).start()
    
    # 6. Keep the application running flawlessly
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()