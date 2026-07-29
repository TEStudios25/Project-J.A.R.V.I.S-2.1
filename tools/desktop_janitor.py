import os
import shutil
import sys

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

def organize_folder(folder_name: str = "Desktop") -> str:
    """
    Scans a local directory (e.g., 'Desktop' or 'Downloads'), creates subfolders 
    by file type, and moves files into them. Also empties the Recycle Bin.
    """
    print(f"\n[🧹 Desktop Janitor]: Organizing folder: '{folder_name}'...")
    
    # 1. Resolve Path
    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    if folder_name.lower().strip() == "desktop":
        target_dir = os.path.join(user_profile, 'Desktop')
    elif folder_name.lower().strip() == "downloads":
        target_dir = os.path.join(user_profile, 'Downloads')
    else:
        # Check absolute or relative workspace path
        if os.path.isabs(folder_name):
            target_dir = folder_name
        else:
            target_dir = os.path.abspath(folder_name)
            
    if not os.path.exists(target_dir):
        return f"Error: Target directory does not exist at '{target_dir}'."

    # 2. Categories mapping
    categories = {
        "Organized_Images": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg", ".ico"],
        "Organized_Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".csv"],
        "Organized_Installers": [".exe", ".msi"],
        "Organized_Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Organized_Media": [".mp4", ".mp3", ".wav", ".mkv", ".avi", ".flac", ".mov"]
    }

    # 3. Create categories subfolders
    for category in categories.keys():
        os.makedirs(os.path.join(target_dir, category), exist_ok=True)

    # 4. Scan and move files
    moved_counts = {cat: 0 for cat in categories.keys()}
    other_moved = 0
    errors = []

    try:
        for filename in os.listdir(target_dir):
            file_path = os.path.join(target_dir, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Find category
            moved = False
            for category, extensions in categories.items():
                if file_ext in extensions:
                    dest_path = os.path.join(target_dir, category, filename)
                    try:
                        shutil.move(file_path, dest_path)
                        moved_counts[category] += 1
                        moved = True
                    except Exception as e:
                        errors.append(f"Could not move {filename}: {e}")
                    break
            
            # If not in specified categories, we don't touch it or move to Miscellaneous
            if not moved and file_ext:
                misc_dir = os.path.join(target_dir, "Organized_Misc")
                os.makedirs(misc_dir, exist_ok=True)
                try:
                    shutil.move(file_path, os.path.join(misc_dir, filename))
                    other_moved += 1
                except Exception as e:
                    errors.append(f"Could not move misc {filename}: {e}")

        # 5. Clear Recycle Bin (Trash)
        trash_cleared = "Recycle bin not emptied."
        try:
            from tools.system_cleaner import optimize_system_storage
            trash_cleared = optimize_system_storage()
        except Exception as e:
            trash_cleared = f"Failed to empty Recycle Bin: {e}"

        # 6. Build report
        report = f"Folder '{os.path.basename(target_dir)}' has been organized successfully!\n\n"
        report += "Files Moved:\n"
        for cat, count in moved_counts.items():
            report += f"- {cat.replace('Organized_', '')}: {count} files\n"
        if other_moved > 0:
            report += f"- Miscellaneous: {other_moved} files\n"
        
        report += f"\nTrash Status: {trash_cleared}"
        if errors:
            report += f"\n\nMinor Warnings:\n" + "\n".join(errors[:5])
            
        return report

    except Exception as e:
        return f"Failed to organize folder '{folder_name}'. Error: {str(e)}"

if __name__ == "__main__":
    # Test organizer on a dummy scratch folder
    test_dir = r"C:\Users\This Pc\.gemini\antigravity\scratch\organizer_test"
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "test.txt"), "w") as f:
        f.write("test")
    print(organize_folder(test_dir))
