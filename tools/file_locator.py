import os
import subprocess
import time

def locate_file(filename: str) -> str:
    """
    Searches for a specific file in the user's main directories.
    If found, it commands Windows to open File Explorer and highlight the file.
    Returns the result to the AI Brain.
    """
    filename = filename.lower().strip()
    print(f"\n[🔎 J.A.R.V.I.S. is scanning the file system for '{filename}'...]")

    # Grab the current Windows user profile path (e.g., C:\Users\Pranav)
    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    
    # We target the most common folders for maximum speed.
    # You can easily add "D:\\" or specific project folders to this list later!
    search_dirs = [
        os.path.join(user_profile, 'Desktop'),
        os.path.join(user_profile, 'Documents'),
        os.path.join(user_profile, 'Downloads')
    ]

    found_path = None

    # The high-speed search loop
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue

        for root, _, files in os.walk(directory):
            for file in files:
                # We use 'in' so you don't have to guess the exact extension
                # e.g., searching "taxes" will find "taxes_2026.pdf"
                if filename in file.lower():
                    found_path = os.path.join(root, file)
                    break 
            if found_path:
                break 
        if found_path:
            break 

    # The Action
    if found_path:
        try:
            print(f"[⚙️ File located. Opening Explorer...]")
            # This specific command opens the folder AND highlights the exact file
            subprocess.run(f'explorer /select,"{found_path}"', shell=True)
            return f"Successfully located '{filename}' and opened File Explorer to its location: {found_path}"
        except Exception as e:
            return f"Located the file at {found_path}, but failed to open Windows Explorer. Error: {str(e)}"
    else:
        return f"Could not find any file matching '{filename}' in the primary directories."

# ===============================================================
# 🧪 ISOLATED TESTING BLOCK
# ===============================================================
if __name__ == "__main__":
    print("\nInitiating Deep Directory Scan Protocol...")
    
    # Create a quick dummy file on your desktop to test it!
    desktop_path = os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'Desktop', 'jarvis_test_target.txt')
    with open(desktop_path, 'w') as f:
        f.write("You found me.")
        
    print("\n[Target File Created on Desktop]")
    
    # Run the locator
    response = locate_file("jarvis_test_target")
    print(f"\nResult: {response}")
    
    # Clean up the dummy file so we don't leave trash on your PC
    time.sleep(2) # Wait a moment so you can see it highlight in Explorer
    try:
        os.remove(desktop_path)
    except:
        pass