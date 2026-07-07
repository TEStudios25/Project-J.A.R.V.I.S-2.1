import os
import shutil
import ctypes

def empty_recycle_bin() -> bool:
    """Empties the Windows Recycle Bin silently without popups or confirmation dialogs."""
    try:
        # Flags: SHERB_NOCONFIRMATION (0x00000001) | SHERB_NOPROGRESSUI (0x00000002) | SHERB_NOSOUND (0x00000004)
        flags = 7
        res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        return res == 0
    except Exception:
        return False

def optimize_system_storage() -> str:
    """
    Cleans system temporary files, caches, and empties the Recycle Bin.
    Returns a status report summarizing the total storage space reclaimed in Megabytes.
    """
    # Verbal confirmation gate
    from senses.tts_engine import speak
    from senses.stt_engine import listen
    speak("Confirming authorization, sir. Are you sure you want to clean and optimize the system storage?")
    reply = listen(check_active_func=lambda: True)
    if not reply or not any(w in reply.lower() for w in ["yes", "confirm", "proceed", "sure", "do it"]):
        return "System optimization cancelled by user request."
        
    print("\n[🧹 J.A.R.V.I.S. is executing system storage optimization...]")
    
    bytes_freed = 0
    recycle_bin_success = empty_recycle_bin()
    
    # Target temp folders
    temp_dirs = []
    
    user_temp = os.environ.get("TEMP")
    if user_temp and os.path.exists(user_temp):
        temp_dirs.append(user_temp)
        
    system_temp = "C:\\Windows\\Temp"
    if os.path.exists(system_temp):
        temp_dirs.append(system_temp)
        
    files_deleted = 0
    errors_encountered = 0
    
    for t_dir in temp_dirs:
        for root, dirs, files in os.walk(t_dir, topdown=False):
            # Try to delete files
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    # Record file size
                    f_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    bytes_freed += f_size
                    files_deleted += 1
                except Exception:
                    # Standard behavior: ignore files currently locked/in use by running Windows processes
                    errors_encountered += 1
                    
            # Try to delete empty directories
            for d in dirs:
                dirpath = os.path.join(root, d)
                try:
                    os.rmdir(dirpath)
                except Exception:
                    pass
                    
    mb_reclaimed = round(bytes_freed / (1024 * 1024), 2)
    
    report = (
        f"Storage optimization completed successfully, Mr. Pranav. "
        f"I have cleared {files_deleted} temporary files, reclaiming {mb_reclaimed} Megabytes of disk space. "
    )
    if recycle_bin_success:
        report += "The Windows Recycle Bin has also been emptied."
    else:
        report += "Note that the Recycle Bin was already clean or bypassed."
        
    return report
