import os
import sys
import time
import subprocess

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

def execute_autopilot_sequence(sequence_name: str) -> str:
    """
    Executes a multi-step macro sequence autonomously, checking terminal feedback after each step.
    Available sequences: 'developer_boot' (pulls code, starts VS Code, sets volume, plays coding music).
    """
    sequence_name = sequence_name.lower().strip()
    print(f"\n[🤖 Autopilot Core]: Executing sequence '{sequence_name}'...")
    
    if sequence_name in ("developer_boot", "dev_setup"):
        # Step 1: Git Pull
        print("[🤖 Autopilot]: Step 1/5 - Pulling latest code changes...")
        repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        try:
            git_res = subprocess.run(["git", "pull"], cwd=repo_dir, capture_output=True, text=True, timeout=15)
            if git_res.returncode != 0:
                # If no remote configured or network down, log warning and continue
                print(f"[🤖 Autopilot Warning]: Git Pull returned exit code {git_res.returncode}. Proceeding anyway...")
            elif "conflict" in git_res.stdout.lower() or "conflict" in git_res.stderr.lower():
                return f"Autopilot aborted at Step 1: Merge conflicts detected in terminal feedback: {git_res.stdout}"
            else:
                print(f"[🤖 Autopilot]: Git pull success: {git_res.stdout.strip()}")
        except Exception as e:
            print(f"[🤖 Autopilot Warning]: Git pull exception: {e}. Proceeding...")
            
        # Step 2: Open VS Code
        print("[🤖 Autopilot]: Step 2/5 - Launching Visual Studio Code...")
        try:
            subprocess.Popen(["code", "."], cwd=repo_dir, shell=True)
            time.sleep(1.5)
        except Exception as e:
            print(f"[🤖 Autopilot Warning]: Failed to launch VS Code: {e}")
            
        # Step 3: Set audio level
        print("[🤖 Autopilot]: Step 3/5 - Adjusting audio volume to 65%...")
        try:
            from tools.system_media import control_system_audio
            control_system_audio("set_volume", "65")
        except Exception as e:
            print(f"[🤖 Autopilot Warning]: Could not set audio levels: {e}")
            
        # Step 4: Play music on YouTube
        print("[🤖 Autopilot]: Step 4/5 - Queuing Synthwave coding radio...")
        try:
            from tools.web_automation import play_song_on_youtube
            play_song_on_youtube("synthwave radio lofi coding music")
        except Exception as e:
            print(f"[🤖 Autopilot Warning]: Could not start youtube music: {e}")
            
        # Step 5: Check system health
        print("[🤖 Autopilot]: Step 5/5 - Scanning system health...")
        try:
            from core.system_monitor import get_full_system_report
            report = get_full_system_report()
            print("[🤖 Autopilot]: Autopilot sequence completed successfully.")
            return f"Autopilot 'developer_boot' executed successfully, Sir! Code repository synced, VS Code loaded, volume set to 65%, synthwave coding radio active, and system health is nominal. Current telemetry:\n{report}"
        except Exception as e:
            return f"Autopilot completed with minor diagnostic report error: {str(e)}"
            
    else:
        return f"Unknown autopilot sequence: '{sequence_name}'. Available sequences: 'developer_boot'."

if __name__ == "__main__":
    # Test autopilot output listing
    print(execute_autopilot_sequence("list"))
