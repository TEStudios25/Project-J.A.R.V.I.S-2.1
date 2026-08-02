import os
import sys
import time
import socket
import threading
import subprocess
import webview
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

ORB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "orb"))

is_paused = False

class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ORB_DIR, **kwargs)

    def log_message(self, format, *args):
        pass # Suppress HTTP access log noise

    def do_GET(self):
        global is_paused
        if self.path == "/pause":
            is_paused = True
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"paused")
        elif self.path == "/resume":
            is_paused = False
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"resumed")
        elif self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            status_json = '{"paused": ' + ('true' if is_paused else 'false') + '}'
            self.wfile.write(status_json.encode('utf-8'))
        else:
            super().do_GET()

class QuietThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        pass # Silence harmless socket abort/reset traceback noise

def start_local_http_server(port=54321):
    try:
        server = QuietThreadingHTTPServer(('127.0.0.1', port), QuietHTTPRequestHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        print(f"[🌐 Local HTTP Server active on http://127.0.0.1:{port}]")
        return server
    except Exception as e:
        print(f"[Warning HTTP Server]: {e}")
        return None

def launch_orb_window():
    """Launches the 3D Holographic Cyan Orb WebGL Window using pywebview over local HTTP."""
    if not os.path.exists(ORB_DIR):
        print(f"[ERROR]: Orb directory not found at {ORB_DIR}")
        return

    # Start local HTTP server to grant secure origin context for DroidCam / WebCam
    port = 54321
    start_local_http_server(port)

    print("\n[🌌 Launching 3D Holographic Cyan Orb Core Window...]")
    try:
        url = f"http://127.0.0.1:{port}/orb.html?v={int(time.time())}"
        cache_dir = os.path.abspath(os.path.join("data", "webview_cache"))
        os.makedirs(cache_dir, exist_ok=True)

        window = webview.create_window(
            title="J.A.R.V.I.S. 3D Holographic Core",
            url=url,
            width=1000,
            height=800,
            resizable=True,
            maximized=True,
            frameless=False,
            easy_drag=True,
            background_color="#020610"
        )
        webview.start(debug=False, storage_path=cache_dir)

        # When 3D Orb Window is closed by user, shutdown J.A.R.V.I.S. completely
        print("\n[System]: 3D Orb Core Window closed. Initiating complete J.A.R.V.I.S. shutdown...")
        try:
            import subprocess
            subprocess.run('taskkill /f /im python.exe /fi "COMMANDLINE eq *main.py*"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        os._exit(0)
    except Exception as e:
        print(f"[⚠️ 3D Orb Window Launch Warning]: {e}")

def start_orb_thread():
    """Launches the 3D Orb Window as a separate background process for Dual-GUI operation."""
    cmd = [sys.executable, os.path.abspath(__file__)]
    try:
        subprocess.Popen(cmd)
    except Exception as e:
        print(f"[ERROR launching Orb process]: {e}")

if __name__ == "__main__":
    launch_orb_window()
