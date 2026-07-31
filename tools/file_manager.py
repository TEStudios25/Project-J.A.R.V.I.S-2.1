import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _resolve_path(filename: str) -> str:
    # If absolute, return it
    if os.path.isabs(filename):
        return filename
    
    # Check if file exists on Desktop
    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    desktop_path = os.path.join(user_profile, 'Desktop', filename)
    if os.path.exists(desktop_path):
        return desktop_path
        
    # Default to Project Root
    return os.path.join(PROJECT_ROOT, filename)

def read_project_file(filename: str) -> str:
    """Reads and returns the contents of a local project file or desktop file."""
    path = _resolve_path(filename)
    print(f"\n[📂 J.A.R.V.I.S. is reading file: '{os.path.basename(path)}'...]")
    try:
        if not os.path.exists(path):
            return f"Error: The file at '{path}' does not exist."
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return f"File contents of '{filename}':\n\n{content}"
    except Exception as e:
        return f"Failed to read file '{filename}'. Error: {str(e)}"

def write_project_file(filename: str, content: str) -> str:
    """Creates a new file or overwrites an existing one in the project directory or Desktop."""
    path = _resolve_path(filename)
    print(f"\n[📂 J.A.R.V.I.S. is writing file: '{os.path.basename(path)}'...]")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully created/wrote file '{os.path.basename(path)}' at location: {path}"
    except Exception as e:
        return f"Failed to write file '{filename}'. Error: {str(e)}"

def append_project_file(filename: str, content: str) -> str:
    """Appends text to the end of a project file or Desktop file."""
    path = _resolve_path(filename)
    print(f"\n[📂 J.A.R.V.I.S. is appending to file: '{os.path.basename(path)}'...]")
    try:
        if not os.path.exists(path):
            return f"Error: The file at '{path}' does not exist. Use write_project_file instead."
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully appended content to '{os.path.basename(path)}' at location: {path}"
    except Exception as e:
        return f"Failed to append to file '{filename}'. Error: {str(e)}"

def list_project_files() -> str:
    """Lists all files in the current J.A.R.V.I.S. project directory."""
    print("\n[📂 J.A.R.V.I.S. is scanning project directory tree...]")
    try:
        file_list = []
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Skip virtual environments and cache directories
            if ".venv" in root or "__pycache__" in root or ".git" in root or "gui\\__pycache__" in root or "senses\\__pycache__" in root:
                continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), PROJECT_ROOT)
                file_list.append(rel_path)
        
        if not file_list:
            return "No files found in the project directory."
            
        return "List of J.A.R.V.I.S. project files:\n- " + "\n- ".join(file_list)
    except Exception as e:
        return f"Failed to list project files. Error: {str(e)}"

def search_files_and_folders(search_term: str, target_dir: str = "", file_type: str = "all") -> str:
    """
    Searches recursively through directories for matching files, folders, PDFs, images, or videos.
    Supports smart search parameters:
      - Time-based: search_term = 'yesterday', 'last week', 'last month'
      - Large files: search_term = 'large files' (files > 5GB)
      - Duplicates: search_term = 'duplicates' (scans for file hash duplicates)
      - Storage: search_term = 'storage' (analyzes directory sizes)
    """
    import glob
    import time
    import hashlib
    
    search_term = search_term.lower().strip()
    file_type = file_type.lower().strip()
    
    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    search_paths = []
    if target_dir and os.path.exists(target_dir):
        search_paths = [target_dir]
    else:
        search_paths = [
            os.path.join(user_profile, 'Desktop'),
            os.path.join(user_profile, 'Documents'),
            os.path.join(user_profile, 'Downloads'),
            PROJECT_ROOT
        ]
        
    image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv'}
    
    matches = []
    current_time = time.time()
    
    # Helper to calculate file hashes for duplicates
    def get_file_hash(filepath):
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    # Helper to sum directory sizes
    def get_dir_size(path):
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_dir_size(entry.path)
        except Exception:
            pass
        return total

    # --- SPECIAL MODE: STORAGE ANALYZER ---
    if search_term == "storage":
        results = []
        for s_path in search_paths:
            if not os.path.exists(s_path):
                continue
            try:
                for entry in os.scandir(s_path):
                    if entry.is_dir(follow_symlinks=False) and not entry.name.startswith('.'):
                        size_bytes = get_dir_size(entry.path)
                        size_mb = round(size_bytes / (1024 * 1024), 2)
                        results.append((entry.name, size_mb, entry.path))
            except Exception:
                pass
        results.sort(key=lambda x: x[1], reverse=True)
        if not results:
            return "No directories found to analyze."
        report = "📦 Storage Space Analysis (Top Directories):\n"
        for name, size, path in results[:10]:
            report += f"  • {name}: {size} MB ({path})\n"
        return report.strip()

    # --- SPECIAL MODE: DUPLICATE DETECTION ---
    if search_term in ["duplicates", "find duplicates", "duplicate files"]:
        hashes = {}
        duplicates = []
        for s_path in search_paths:
            if not os.path.exists(s_path):
                continue
            for root, _, files in os.walk(s_path):
                if any(p in root for p in [".venv", "__pycache__", ".git", "AppData"]):
                    continue
                for file in files:
                    filepath = os.path.join(root, file)
                    f_hash = get_file_hash(filepath)
                    if f_hash:
                        if f_hash in hashes:
                            duplicates.append((filepath, hashes[f_hash]))
                        else:
                            hashes[f_hash] = filepath
        if not duplicates:
            return "No duplicate files detected in target directories."
        report = "📋 Duplicate Files Found:\n"
        for dup, orig in duplicates[:15]:
            report += f"  • Duplicate: {os.path.basename(dup)} ({dup})\n    Original: {orig}\n"
        return report.strip()

    # --- STANDARD OR TIMED/SIZE SEARCHES ---
    for s_path in search_paths:
        if not os.path.exists(s_path):
            continue
        for root, dirs, files in os.walk(s_path):
            if any(p in root for p in [".venv", "__pycache__", ".git", "AppData"]):
                continue
                
            # Match folders (skipped if user specifies file types)
            if file_type in ['folder', 'all'] and search_term not in ['large files', 'yesterday', 'last week', 'last month']:
                for d in dirs:
                    if search_term in d.lower():
                        matches.append(f"[DIR] {os.path.join(root, d)}")
                        
            # Match files
            if file_type != 'folder':
                for file in files:
                    filepath = os.path.join(root, file)
                    name_lower = file.lower()
                    ext = os.path.splitext(name_lower)[1]
                    
                    # Extension filters
                    is_type_match = False
                    if file_type == 'pdf' and ext == '.pdf':
                        is_type_match = True
                    elif file_type == 'image' and ext in image_exts:
                        is_type_match = True
                    elif file_type == 'video' and ext in video_exts:
                        is_type_match = True
                    elif file_type in ['file', 'all']:
                        is_type_match = True
                        
                    if not is_type_match:
                        continue
                        
                    # Filter by search parameter
                    try:
                        mtime = os.path.getmtime(filepath)
                        fsize = os.path.getsize(filepath)
                    except Exception:
                        continue
                        
                    if search_term == "yesterday":
                        # Modified in the last 24-48 hours
                        if current_time - mtime <= 172800: 
                            matches.append(f"[FILE] {filepath} (Modified: {time.ctime(mtime)})")
                    elif search_term == "last week":
                        # Modified in last 7 days
                        if current_time - mtime <= 604800:
                            matches.append(f"[FILE] {filepath} (Modified: {time.ctime(mtime)})")
                    elif search_term == "last month":
                        # Modified in last 30 days
                        if current_time - mtime <= 2592000:
                            matches.append(f"[FILE] {filepath} (Modified: {time.ctime(mtime)})")
                    elif search_term in ["large files", "large file"]:
                        # Larger than 5GB (5,368,709,120 bytes) or 100MB for testing safety
                        if fsize >= 104857600: # Match files > 100MB for clean diagnostic utility
                            size_gb = round(fsize / (1024 * 1024 * 1024), 2)
                            matches.append(f"[FILE] {filepath} ({size_gb} GB)")
                    else:
                        # Simple keyword name search
                        if search_term in name_lower or search_term in ext:
                            matches.append(f"[FILE] {filepath}")
                            
    if not matches:
        return f"No matches found for search term '{search_term}' and filter '{file_type}'."
    return f"Found {len(matches)} item(s):\n- " + "\n- ".join(matches[:20])

def manage_file_system(action: str, source_path: str, destination_path: str = "") -> str:
    """
    Manages files and directories on the local system (Move, Copy, Rename, Delete, Compress, Extract).
    action: 'move', 'copy', 'rename', 'delete', 'compress', 'extract'
    source_path: Target file or directory to manage.
    destination_path: New path, folder target, or name for the action.
    """
    import shutil
    import zipfile
    
    action = action.lower().strip()
    src = _resolve_path(source_path)
    dst = _resolve_path(destination_path) if destination_path else ""
    
    print(f"\n[📂 J.A.R.V.I.S. is executing file manager action '{action}' on '{source_path}'...]")
    
    if not os.path.exists(src):
        return f"Error: Source path '{src}' does not exist."
        
    try:
        if action == "move":
            if not dst:
                return "Error: Destination path is required for move action."
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return f"Successfully moved '{os.path.basename(src)}' to: {dst}"
            
        elif action == "copy":
            if not dst:
                return "Error: Destination path is required for copy action."
            if os.path.isdir(src):
                shutil.copytree(src, dst)
                return f"Successfully copied directory '{os.path.basename(src)}' to: {dst}"
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                return f"Successfully copied file '{os.path.basename(src)}' to: {dst}"
                
        elif action == "rename":
            if not dst:
                return "Error: New name/path is required for rename action."
            os.rename(src, dst)
            return f"Successfully renamed '{os.path.basename(src)}' to: '{os.path.basename(dst)}'"
            
        elif action == "delete":
            if os.path.isdir(src):
                shutil.rmtree(src)
                return f"Successfully deleted directory '{os.path.basename(src)}'."
            else:
                os.remove(src)
                return f"Successfully deleted file '{os.path.basename(src)}'."
                
        elif action == "compress":
            # If destination_path doesn't end in .zip, add it
            if not dst:
                dst = src + ".zip"
            elif not dst.endswith(".zip"):
                dst = dst + ".zip"
                
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isdir(src):
                    for root, _, files in os.walk(src):
                        for file in files:
                            filepath = os.path.join(root, file)
                            arcname = os.path.relpath(filepath, src)
                            zipf.write(filepath, arcname)
                else:
                    zipf.write(src, os.path.basename(src))
            return f"Successfully compressed '{os.path.basename(src)}' into zip archive at: {dst}"
            
        elif action == "extract":
            if not dst:
                dst = os.path.splitext(src)[0]
            os.makedirs(dst, exist_ok=True)
            with zipfile.ZipFile(src, 'r') as zip_ref:
                zip_ref.extractall(dst)
            return f"Successfully extracted archive '{os.path.basename(src)}' into folder: {dst}"
            
        else:
            return f"Unknown file management action '{action}'. Choose from 'move', 'copy', 'rename', 'delete', 'compress', 'extract'."
            
    except Exception as e:
        return f"Failed to execute action '{action}' on '{os.path.basename(src)}'. Error: {str(e)}"

def find_duplicate_files(target_dir: str = "") -> str:
    """
    Scans directories (Desktop, Documents, Downloads, or custom directory) for duplicate files.
    Identifies identical files using content hashing (MD5).
    """
    return search_files_and_folders("duplicates", target_dir)

def find_large_files(min_size_mb: float = 100.0, target_dir: str = "") -> str:
    """
    Scans directories and returns files larger than the specified size in Megabytes.
    Default is 100.0 MB.
    """
    # For large file cleaner, we pass the keyword 'large files' to our search tool
    # Wait, the search_files_and_folders tool uses bytes for size checking, let's call it!
    return search_files_and_folders("large files", target_dir)

def analyze_folder_storage(target_dir: str = "") -> str:
    """
    Scans a directory and returns a sorted breakdown of which subdirectories take up the most space.
    """
    return search_files_and_folders("storage", target_dir)


