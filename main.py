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
    print("\n=======================================================")
    print("||        PROJECT J.A.R.V.I.S. 2.x INITIATED         ||")
    print("=======================================================")
    time.sleep(0.5)

    # Boot Dialog 1
    msg1 = "Powering up the Systems"
    print(f"[🔋 System]: {msg1}...")
    
    # Boot Dialog 2
    msg2 = "Allocating neural network memory modules"
    print(f"[🧠 System]: {msg2}...")
    
    # Boot Dialog 3
    msg3 = "Establishing secure connection to global servers"
    print(f"[📡 System]: {msg3}...")
    
    # Boot Dialog 4
    msg4 = "Calibrating Voice and Vision interfaces"
    print(f"[⚙️ System]: {msg4}...")
    
    # Boot Dialog 5
    msg5 = "Graphic User Interface locked and loaded"
    print(f"[✅ System]: {msg5}.")
    
    # The iconic startup phrase (Officially addressing Mr. Pranav!)
    import datetime
    hour = datetime.datetime.now().hour
    if hour < 12:
        final_msg = "Good morning, Sir. J.A.R.V.I.S. is online, caffeinated, and ready for your orders. No cap."
    elif 12 <= hour < 17:
        final_msg = "Good afternoon, Sir. System is online, green across the board. What are we cooking today?"
    else:
        final_msg = "Good evening, Sir. Systems are online and fully optimized. Let's make things happen."

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