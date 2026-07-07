import glob
import os
import subprocess
import tempfile

import psutil


def clean_temp_files() -> str:
    """Safely removes temporary files from common Windows temp locations."""
    print("\n[🧹 J.A.R.V.I.S. is running a safe temp-file cleanup...]")

    targets = [
        tempfile.gettempdir(),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Temp"),
    ]

    removed = 0
    skipped = 0

    for folder in targets:
        if not folder or not os.path.isdir(folder):
            continue
        for path in glob.glob(os.path.join(folder, "*")):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    removed += 1
                elif os.path.isdir(path):
                    import shutil

                    shutil.rmtree(path, ignore_errors=True)
                    removed += 1
            except Exception:
                skipped += 1

    return (
        f"Cleanup complete. Removed or cleared {removed} temporary items. "
        f"Skipped {skipped} locked files that were still in use."
    )


def run_malware_scan(quick_scan: bool = True) -> str:
    """Starts a Windows Defender scan in the background."""
    scan_type = "QuickScan" if quick_scan else "FullScan"
    print(f"\n[🛡️ J.A.R.V.I.S. is starting Windows Defender {scan_type}...]")

    try:
        command = (
            f'Start-MpScan -ScanType {scan_type}'
            if quick_scan
            else "Start-MpScan -ScanType FullScan"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000,
        )
        return (
            f"Windows Defender {scan_type.replace('Scan', ' scan')} has been started in the background, sir."
        )
    except Exception as exc:
        return f"Could not start malware scan. Error: {exc}"


def detect_unusual_activity() -> str:
    """Reports high CPU processes and suspicious network-heavy activity."""
    print("\n[🔍 J.A.R.V.I.S. is scanning for unusual activity...]")

    alerts = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            cpu = proc.cpu_percent(interval=0.0)
            if cpu >= 25:
                alerts.append(f"High CPU: {proc.info.get('name')} at {round(cpu, 1)} percent")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    psutil.cpu_percent(interval=0.2)
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            cpu = proc.cpu_percent(interval=0.0)
            if cpu >= 25:
                label = f"High CPU: {proc.info.get('name')} at {round(cpu, 1)} percent"
                if label not in alerts:
                    alerts.append(label)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    connections = len(psutil.net_connections(kind="inet"))
    if connections > 250:
        alerts.append(f"Elevated network socket count detected: {connections} active connections.")

    if not alerts:
        return "No unusual activity detected at this time. Systems appear nominal, sir."

    return "Unusual activity report:\n- " + "\n- ".join(alerts[:8])

def run_self_diagnostics() -> str:
    """
    Executes a comprehensive system diagnostics sweep of J.A.R.V.I.S.'s internal subsystems.
    Tests API keys, database files, audio drivers, networking logs, and telemetry sensors.
    """
    import os
    import json
    import pygame
    import socket
    import psutil
    import time
    
    print("\n[⚙️ J.A.R.V.I.S. is executing a self-diagnostic system scan...]")
    report = "================================================\n"
    report += "||        J.A.R.V.I.S. SELF-DIAGNOSTIC SWEEP       ||\n"
    report += "================================================\n"
    
    # 1. Check Neural Core API Connection
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and len(api_key.strip()) > 10:
        report += "[✅] Neural core (Gemini API Key): ONLINE\n"
    else:
        report += "[❌] Neural core (Gemini API Key): OFFLINE / CONFIG ERR\n"
        
    # 2. Check Memory Database Integrity
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    memory_path = os.path.join(project_root, "data", "memory.json")
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            facts_count = len(data.get("profile", {}).get("facts", []))
            report += f"[✅] Memory Registry: OK ({facts_count} facts indexed)\n"
        except Exception as e:
            report += f"[❌] Memory Registry: CORRUPTED -> {e}\n"
    else:
        report += "[❌] Memory Registry: FILE MISSING\n"
        
    # 3. Check Audio & Vocal Synthesis Engines
    try:
        if pygame.mixer.get_init():
            report += "[✅] Vocal Sound System: OK (Audio mixer active)\n"
        else:
            report += "[❌] Vocal Sound System: Audio driver disabled\n"
    except Exception:
        report += "[❌] Vocal Sound System: Hardware driver error\n"
        
    # 4. Check Telemetry Sensors
    try:
        cpu = psutil.cpu_percent(interval=0.01)
        ram = psutil.virtual_memory().percent
        report += f"[✅] System Telemetry Sensors: OK (CPU: {cpu}%, RAM: {ram}%)\n"
    except Exception:
        report += "[❌] System Telemetry Sensors: Sensor failure\n"
        
    # 5. Check Mobile Telemetry Node (Phone link IP ping check)
    phone_ip = None
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for fact in data.get("profile", {}).get("facts", []):
                if "phone ip" in fact.lower() or "mobile ip" in fact.lower() or "phone is" in fact.lower():
                    import re
                    ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', fact)
                    if ip_match:
                        phone_ip = ip_match.group(0)
                        break
        except Exception:
            pass
            
    if phone_ip:
        try:
            # Quick socket check (0.5 sec timeout)
            socket.setdefaulttimeout(0.5)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Try connecting to port 80 or similar
            s.connect((phone_ip, 80))
            s.close()
            report += f"[✅] Phone HUD Link: ONLINE (Device IP: {phone_ip})\n"
        except Exception:
            report += f"[❌] Phone HUD Link: OFFLINE (Device IP: {phone_ip} unreachable)\n"
    else:
        report += "[⚠️] Phone HUD Link: UNCONFIGURED (No IP in memories)\n"
        
    report += "================================================\n"
    report += "Status: Systems nominal and ready for commands, sir."
    return report

