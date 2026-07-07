import os
import sys
import time
import threading

# Windows terminals often default to cp1252; allow emoji/log output during boot.
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
from PyQt5.QtWidgets import QApplication

# --- PATH ENFORCEMENT ---
# Ensures main.py can smoothly read all folders (core, senses, tools)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import the Graphic Interface and the Mouth
from gui.interface import JarvisGUI
from senses.tts_engine import speak

# (Note: If your security.py is inside the 'core' folder, change this to: from core.security import verify_access)
from core.security import verify_access 

def system_boot_sequence():
    """Plays the epic sci-fi startup terminal sequence and verbal greeting."""
    print("\n=======================================================")
    print("||        PROJECT J.A.R.V.I.S. 2.x INITIATED         ||")
    print("=======================================================")
    time.sleep(0.5)

    # Boot Dialog 1
    msg1 = "Powering up the Systems"
    print(f"[🔋 System]: {msg1}...")
    speak(msg1)
    
    # Boot Dialog 2
    msg2 = "Allocating neural network memory modules"
    print(f"[🧠 System]: {msg2}...")
    speak(msg2)
    
    # Boot Dialog 3
    msg3 = "Establishing secure connection to global servers"
    print(f"[📡 System]: {msg3}...")
    speak(msg3)
    
    # Boot Dialog 4
    msg4 = "Calibrating Voice and Vision interfaces"
    print(f"[⚙️ System]: {msg4}...")
    speak(msg4)
    
    # Boot Dialog 5
    msg5 = "Graphic User Interface locked and loaded"
    print(f"[✅ System]: {msg5}.")
    speak(msg5)
    
    # The iconic startup phrase (Officially addressing Mr. Pranav!)
    final_msg = "All systems online. Good to see you, Mr. Pranav. I am ready for your orders."
    print(f"\n[🤖 J.A.R.V.I.S.]: {final_msg}\n")
    speak(final_msg)

def main():
    # 1. Initialize the QApplication first so graphical windows/dialogs can render
    app = QApplication(sys.argv)
    
    # 2. Run mainframe security verification dialog
    verify_access()
        
    # 3. Start the visual boot logs and voice greeting in the background
    threading.Thread(target=system_boot_sequence, daemon=True).start()
    
    # 4. Launch the Front-Face GUI
    workspace = JarvisGUI()
    workspace.show()
    
    # 5. Keep the application running flawlessly
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()