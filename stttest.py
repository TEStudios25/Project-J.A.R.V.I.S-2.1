import sys
import os

# --- PATH ENFORCEMENT ---
# Ensures the test script can find the 'senses' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from senses.stt_engine import listen

def run_microphone_diagnostics():
    print("========================================")
    print("🎙️ J.A.R.V.I.S. STT ISOLATED TESTER 🎙️")
    print("========================================")
    print("Loading Faster-Whisper Model into RAM (this takes ~5-10 seconds)...")
    
    while True:
        # Call the listen function from your engine
        transcription = listen()
        
        if transcription:
            print(f"\n[✅ RAW OUTPUT]: {transcription}\n")
            
            # Type or say 'exit' to break the loop
            if transcription in ["stop", "exit", "quit", "shutdown"]:
                print("Diagnostics complete. Shutting down STT.")
                break

if __name__ == "__main__":
    run_microphone_diagnostics()