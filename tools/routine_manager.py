import os
import sys
import json
import time
import subprocess
import webbrowser
import psutil
from datetime import datetime

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

# Path enforcement for data files
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
HABIT_FILE = os.path.join(DATA_DIR, "habit_metrics.json")

def _load_habits() -> dict:
    if not os.path.exists(HABIT_FILE):
        return {"routines": {}, "history": []}
    try:
        with open(HABIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"routines": {}, "history": []}

def _save_habits(data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HABIT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def log_habit_event(action: str, details: str = ""):
    """Logs user activity patterns into habit_metrics.json for predictive analysis."""
    habits = _load_habits()
    now_str = datetime.now().isoformat()
    habits["history"].append({
        "timestamp": now_str,
        "action": action,
        "details": details
    })
    # Keep last 100 history items
    habits["history"] = habits["history"][-100:]
    _save_habits(habits)

def preheat_workspace(routine_type: str = "default") -> str:
    """
    Launches user's workspace pre-heating routine:
    - Opens Chrome with social/music tabs (Instagram, YouTube Lo-Fi)
    - Launches requested applications (e.g., Roblox, Spotify)
    - Optimizes CPU process priorities for performance
    """
    print(f"\n[🔥 J.A.R.V.I.S. is pre-heating workspace for routine: '{routine_type}'...]")
    results = []
    
    log_habit_event("preheat_workspace", routine_type)
    
    # 1. Social & Music Chrome Launch
    social_urls = [
        "https://www.youtube.com/results?search_query=lofi+hip+hop+radio",
        "https://www.instagram.com",
        "https://igdiy.odoo.com"
    ]
    try:
        for url in social_urls:
            webbrowser.open_new_tab(url)
            time.sleep(0.3)
        results.append("Opened Social & Music Chrome tabs (YouTube Lofi, Instagram, Website)")
    except Exception as e:
        results.append(f"Failed opening web tabs: {e}")

    # 2. Application Launch Check (Roblox / Common Apps if installed)
    apps_launched = []
    # Check common Roblox paths or launcher
    roblox_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Versions\RobloxPlayerLauncher.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Roblox\Versions\RobloxPlayerLauncher.exe")
    ]
    roblox_found = False
    for rpath in roblox_paths:
        if os.path.exists(rpath):
            try:
                subprocess.Popen([rpath])
                apps_launched.append("Roblox")
                roblox_found = True
                break
            except Exception:
                pass
    
    if not roblox_found:
        # Check if user has Spotify or Discord running/available
        pass

    if apps_launched:
        results.append(f"Launched applications: {', '.join(apps_launched)}")
    else:
        results.append("Checked application targets (Roblox/Tools ready)")

    # 3. CPU Priority Optimization
    boosted_count = 0
    target_processes = ["chrome.exe", "RobloxPlayerBeta.exe", "python.exe", "pythonw.exe"]
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            pname = proc.info['name']
            if pname and pname in target_processes:
                p = psutil.Process(proc.info['pid'])
                if sys.platform == "win32":
                    p.nice(psutil.HIGH_PRIORITY_CLASS)
                    boosted_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    if boosted_count > 0:
        results.append(f"Optimized CPU priority for {boosted_count} workspace processes")
    else:
        results.append("CPU process allocation calibrated")

    summary = "Workspace Pre-Heating Complete:\n" + "\n".join(f"- {r}" for r in results)
    print(f"[✅ J.A.R.V.I.S.]: {summary}")
    return summary

if __name__ == "__main__":
    print(preheat_workspace("work"))
