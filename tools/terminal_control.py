import subprocess
import os
import sys

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

def run_terminal_command(command: str) -> str:
    """
    Executes a shell command in Windows PowerShell and returns stdout/stderr.
    Use this to run local scripts, start servers, or manage processes autonomously.
    """
    print(f"\n[💻 Terminal Control]: Executing command: {command}")
    try:
        # Run PowerShell command
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        output = proc.stdout
        error = proc.stderr
        
        result = ""
        if output:
            result += f"Output:\n{output}\n"
        if error:
            result += f"Errors:\n{error}\n"
        if not result:
            result = "Command executed successfully with no console output."
            
        return result
    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out after 30 seconds."
    except Exception as e:
        return f"Error executing terminal command: {str(e)}"

def auto_git_backup(commit_message: str = "J.A.R.V.I.S. Auto-Backup") -> str:
    """
    Runs git status, add, commit, and push in the project repository to back up your code to GitHub.
    Use this when the user asks to save, back up, or push their project changes.
    """
    print("\n[🛠️ Auto-Git Pipeline]: Starting repository backup...")
    try:
        repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # Git status
        status_res = subprocess.run(["git", "status"], cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if "nothing to commit, working tree clean" in status_res.stdout:
            return "Git status shows working tree is clean. No backup needed, sir."
            
        # Git add
        add_res = subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        # Git commit
        commit_res = subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        # Git push
        push_res = subprocess.run(["git", "push"], cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        report = (
            f"Backup process completed successfully!\n\n"
            f"Commit Status:\n{commit_res.stdout}\n"
            f"Push Status:\n{push_res.stdout or push_res.stderr}\n"
        )
        return report
    except Exception as e:
        return f"Failed to complete Git auto-backup. Error: {str(e)}"

if __name__ == "__main__":
    print(run_terminal_command("Get-Location"))
