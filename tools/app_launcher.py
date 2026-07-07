import os
import subprocess

def open_application(app_name: str) -> str:
    """
    Takes the name of an application and commands Windows to launch it.
    Returns a success or failure message for the AI Brain instantly.
    """
    app_name = app_name.lower().strip()
    
    # 🧠 The Smart Dictionary
    app_commands = {
        "chrome": "chrome",
        "google": "chrome",
        "notepad": "notepad",
        "calculator": "calc",
        "calc": "calc",
        "file explorer": "explorer",
        "files": "explorer",
        "vs code": "code",
        "visual studio": "code",
        "command prompt": "cmd",
        "roblox": "roblox:" 
    }
    
    try:
        print(f"\n[⚙️ Attempting to launch '{app_name}'...]")
        
        # subprocess.Popen with shell=True runs it in the background instantly
        if app_name in app_commands:
            subprocess.Popen(f"start {app_commands[app_name]}", shell=True)
            return f"Successfully opened {app_name}."
            
        else:
            subprocess.Popen(f"start {app_name}", shell=True)
            return f"Successfully opened {app_name}."
                
    except Exception as e:
        return f"System error while trying to open {app_name}: {str(e)}"

def close_application(app_name: str) -> str:
    """Forces an application to close instantly."""
    app_name = app_name.lower().strip()
    
    exe_names = {
        "chrome": "chrome.exe",
        "google": "chrome.exe",
        "google chrome": "chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "vs code": "code.exe",
        "visual studio": "code.exe",
        "vscode": "code.exe",
        "code": "code.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "command prompt": "cmd.exe",
        "cmd": "cmd.exe",
        "roblox": "RobloxPlayerBeta.exe"
    }
    
    target_exe = exe_names.get(app_name, f"{app_name}.exe")
    
    try:
        print(f"\n[⚙️ Terminating '{target_exe}'...]")
        # subprocess.run waits just long enough to ensure it actually closed
        subprocess.run(f"taskkill /f /im {target_exe}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Successfully closed {app_name}."
    except Exception as e:
        return f"Failed to close {app_name}. Error: {str(e)}"

# ===============================================================
# 🧪 ISOLATED TESTING BLOCK
# ===============================================================
if __name__ == "__main__":
    import time
    print("\nInitiating High-Speed Automation Protocol...")
    
    # Test 1: Open an app
    open_response = open_application("notepad")
    print(f"Result: {open_response}")
    
    # Test 2: Wait 3 seconds, then close it
    time.sleep(3)
    
    close_response = close_application("notepad")
    print(f"Result: {close_response}")