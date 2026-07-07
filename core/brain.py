import os
import sys
import threading
import time
import google.generativeai as genai
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from senses.tts_engine import speak, stop_audio, pause_audio, resume_audio
from tools.web_search import search_the_web
from tools.web_automation import open_website, search_youtube, play_song_on_youtube
from tools.file_locator import locate_file
from tools.pdf_generator import generate_pdf
from tools.image_generator import generate_image
from tools.weather_tool import get_weather
from tools.email_tool import send_email
from tools.pc_maintenance import clean_temp_files, run_malware_scan, detect_unusual_activity, run_self_diagnostics
from tools.app_launcher import open_application, close_application
from tools.vision_tools import analyze_current_screen, analyze_image_file, extract_text_from_image
from tools.system_media import get_clipboard_content, set_clipboard_content, control_system_audio
from tools.network_scanner import ping_network_device
from tools.news_tool import get_tech_news_briefing
from tools.code_debugger import validate_workspace_code
from tools.system_cleaner import optimize_system_storage
from tools.reporter import compile_productivity_report
from tools.todo_manager import add_todo_item, complete_todo_item, get_todo_list
import json
from tools.window_manager import get_active_window_title, execute_system_hotkey, focus_and_control_window, scan_social_notifications
from tools.file_manager import read_project_file, write_project_file, append_project_file, list_project_files, search_files_and_folders, manage_file_system, find_duplicate_files, find_large_files, analyze_folder_storage
from core.system_monitor import (
    get_cpu_usage,
    get_ram_usage,
    get_disk_usage,
    get_battery_status,
    get_gpu_status,
    get_full_system_report,
)
from core.scheduler import add_reminder, get_today_schedule
from core.memory import remember_turn, remember_fact, get_memory_context
from core.query_router import classify_audio_command, build_routing_directive


class JarvisBrain:
    def __init__(self):
        print("\n[🧠 Initializing Neural Network and syncing tools...]")
        self.sleep_mode = False
        self.current_user_mood = "Calm"
        
        # Increment total sessions in habit metrics
        try:
            os.makedirs("data", exist_ok=True)
            filepath = os.path.join("data", "habit_metrics.json")
            metrics = {}
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
            metrics["total_sessions"] = metrics.get("total_sessions", 0) + 1
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
        except Exception:
            pass

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            print("\n[ERROR]: GEMINI_API_KEY is missing from the .env file!")
            self.model = None
            self.chat = None
            return

        genai.configure(api_key=api_key)

        self.jarvis_tools = [
            search_the_web,
            get_weather,
            open_website,
            search_youtube,
            play_song_on_youtube,
            open_application,
            close_application,
            locate_file,
            generate_pdf,
            generate_image,
            send_email,
            add_reminder,
            get_today_schedule,
            remember_fact,
            get_cpu_usage,
            get_ram_usage,
            get_disk_usage,
            get_battery_status,
            get_gpu_status,
            get_full_system_report,
            clean_temp_files,
            run_malware_scan,
            run_self_diagnostics,
            detect_unusual_activity,
            analyze_current_screen,
            analyze_image_file,
            extract_text_from_image,
            get_clipboard_content,
            set_clipboard_content,
            control_system_audio,
            get_active_window_title,
            execute_system_hotkey,
            focus_and_control_window,
            scan_social_notifications,
            read_project_file,
            write_project_file,
            append_project_file,
            list_project_files,
            search_files_and_folders,
            manage_file_system,
            find_duplicate_files,
            find_large_files,
            analyze_folder_storage,
            ping_network_device,
            validate_workspace_code,
            optimize_system_storage,
            compile_productivity_report,
            add_todo_item,
            complete_todo_item,
            get_todo_list,
        ]

        memory_context = get_memory_context(limit=6)
        self.model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            tools=self.jarvis_tools,
            system_instruction=(
                "You are J.A.R.V.I.S., a highly advanced personal AI assistant created by Mr. Pranav. "
                "You run on Windows and can control apps, the web, email, files, reminders, system telemetry, "
                "maintenance tasks, image generation, live web search, clipboard contents, audio volume/playback, active window focus tracker, system keyboard hotkey automation, and reading/writing/listing files. "
                "CRITICAL: For current events, prices, news, weather outside wttr, or any live factual data, "
                "you MUST call search_the_web or get_weather instead of guessing from memory. "
                "For PC health, use system monitor and maintenance tools. For running a comprehensive self-diagnostic hardware/software sweep across API keys, memory registries, audio, and phone networks, use run_self_diagnostics. "
                "For reminders, use add_reminder and get_today_schedule. "
                "For email, confirm recipient, subject, and body before calling send_email. "
                "For system volume, mute, or media control, use control_system_audio. "
                "For clipboard tasks (like copying code, writing to or reading text), use get_clipboard_content and set_clipboard_content. "
                "For analyzing what's on screen or image files, use analyze_current_screen or analyze_image_file. "
                "For performing OCR (text extraction) from an image file or current screen, use extract_text_from_image. "
                "For active app title or focus tracking, use get_active_window_title. "
                "For checking if there are any unread notifications or messages on WhatsApp Web, WhatsApp Desktop, or Instagram tabs/apps, use scan_social_notifications. "
                "For hotkeys (like closing windows, Alt+Tab, copy all, lock PC), use execute_system_hotkey. "
                "For targeting a specific open window/application by name (like Chrome, VS Code, Spotify) and minimizing, maximizing, restoring, or switching focus to it, use focus_and_control_window. "
                "CRITICAL: If a user asks you to perform an action (like searching YouTube, searching the web, opening an app, sending an email, focusing/minimizing a window, scanning notifications, or file tools) but leaves out essential details (such as the search query, the app/window name, the website domain, or file name), you MUST ask a clarification question in your response to get the missing parameters before calling the tool. "
                "CRITICAL: Do NOT call execute_system_hotkey or lock the PC when the user asks you to go to sleep, enter standby, or sleep. The system handles sleep mode automatically. "
                "For checking if local Wi-Fi devices (like a phone or tablet) are online by IP address, use ping_network_device. "
                "For working with project or desktop files (reading, writing, appending, or listing files), use read_project_file, write_project_file, append_project_file, or list_project_files. "
                "For recursively searching for files, folders, PDFs, images, or videos, or performing smart searches (like files from yesterday, last week), use search_files_and_folders. "
                "For scanning folders to find duplicate files (content hashing), use find_duplicate_files. "
                "For finding files larger than a certain limit, use find_large_files. "
                "For analyzing storage footprint of folders, use analyze_folder_storage. "
                "For file system operations such as move, copy, rename, delete, compress (zip), or extract (unzip) files or folders, use manage_file_system. "
                "For validating Python scripts for syntax errors in the workspace, use validate_workspace_code. "
                "For cleaning storage (temp directories and recycle bin), use optimize_system_storage. "
                "For compiling a weekly productivity/usage telemetry report, use compile_productivity_report. "
                "For managing your todo checklist, use add_todo_item, complete_todo_item, and get_todo_list. "
                "Keep responses concise, professional, slightly witty, and conversational. "
                "Do NOT use markdown formatting because responses are spoken aloud. "
                f"Persistent memory:\n{memory_context}"
            ),
        )

        self.chat = self.model.start_chat(enable_automatic_function_calling=True)
        print("[✅ Neural Network Online. Tools calibrated.]")

    def process_command(self, user_text: str):
        """Processes incoming user input with routing, memory, and telemetry injection."""
        if not self.model or not self.chat:
            error_msg = "Neural network is offline. Please set GEMINI_API_KEY in your .env file."
            print(f"\n[JARVIS]: {error_msg}")
            threading.Thread(target=speak, args=(error_msg,), daemon=True).start()
            return error_msg

        # Standby / Sleep mode command checks
        clean_cmd = user_text.lower().strip().replace(".", "").replace(",", "").strip()
        
        # If J.A.R.V.I.S. is asleep, only listen for wake up words
        if self.sleep_mode:
            if any(wake in clean_cmd for wake in ["wake up", "jarvis wake up", "activate"]):
                self.sleep_mode = False
                wake_msg = "All systems online. Welcome back, Mr. Pranav."
                print(f"\n[🤖 J.A.R.V.I.S.]: {wake_msg}")
                threading.Thread(target=speak, args=(wake_msg,), daemon=True).start()
                return wake_msg
            else:
                # Silently ignore everything else
                return ""
                
        # If J.A.R.V.I.S. is active, check if user commanded sleep
        sleep_triggers = ["go to sleep", "enter standby", "sleep mode", "standby mode", "system standby"]
        if any(trigger in clean_cmd for trigger in sleep_triggers) or clean_cmd == "sleep" or clean_cmd == "standby":
            self.sleep_mode = True
            sleep_msg = "Entering standby mode. Say 'wake up' to activate core modules, sir."
            print(f"\n[🤖 J.A.R.V.I.S.]: {sleep_msg}")
            threading.Thread(target=speak, args=(sleep_msg,), daemon=True).start()
            return sleep_msg

        # Update User Cognitive Sentiment Mood and Habit Analytics Logger
        self.current_user_mood = self.analyze_sentiment(user_text)
        self.log_habit_metric(user_text)

        try:
            audio_action = classify_audio_command(user_text)
            if audio_action == "stop":
                stop_audio()
                return ""
            if audio_action == "pause":
                pause_audio()
                return ""
            if audio_action == "resume":
                resume_audio()
                return ""

            live_time = time.strftime("%A, %B %d, %Y at %I:%M %p")
            routing = build_routing_directive(user_text)
            memory_context = get_memory_context(limit=4)

            # Check if user query explicitly requests a daily briefing routine
            import re
            briefing_match = re.search(
                r"\b(run briefing|daily briefing|morning routine|wake up)\b",
                user_text.lower()
            )
            
            briefing_info = ""
            if briefing_match:
                print("\n[🧠 J.A.R.V.I.S. is compiling your daily briefing segment...]")
                try:
                    weather = get_weather()
                except Exception:
                    weather = "Weather telemetry offline."
                    
                try:
                    schedule = get_today_schedule()
                except Exception:
                    schedule = "Schedule database offline."
                    
                try:
                    cpu_perc = get_cpu_usage()
                    ram_perc = get_ram_usage()
                    battery_status = get_battery_status()
                    sys_health = f"CPU usage is {cpu_perc}%, RAM usage is {ram_perc}%, and {battery_status}"
                except Exception:
                    sys_health = "System health telemetry offline."
                    
                try:
                    news = get_tech_news_briefing()
                except Exception:
                    news = "Tech news feed offline."
                
                briefing_info = (
                    f"\n\n[SYSTEM DAILY BRIEFING INITIATED]\n"
                    f"CRITICAL: Welcome Mr. Pranav and present the daily briefing parameters in a highly concise, snappy, and clear manner. "
                    f"Combine weather, schedule, and system stats into 1-2 brief sentences, then list the key news headlines concisely in 1-2 snappy sentences. "
                    f"Do NOT elaborate, keep it quick so he doesn't have to wait. "
                    f"Parameters:\n"
                    f"- Weather Report: {weather}\n"
                    f"- Today's Schedule: {schedule}\n"
                    f"- System Health: {sys_health}\n"
                    f"- News Headlines: {news}\n"
                )

            stealth_payload = (
                f"[System Clock: {live_time}]\n"
                f"[Memory Snapshot]\n{memory_context}\n"
                f"[User Mood Context: {self.current_user_mood}]\n"
                f"[{routing}]\n"
                f"User: {user_text}\n"
                f"(Directive: Use tools whenever they can complete the task more accurately than memory. If the user's mood is rushed, keep your response extremely short and snappy. If they are fatigued or tired, be encouraging and supportive.){briefing_info}"
            )

            response = self.chat.send_message(stealth_payload)
            reply_text = response.text or "Task completed, sir."

            print(f"\n[JARVIS]: {reply_text}")
            remember_turn(user_text, reply_text)
            threading.Thread(target=speak, args=(reply_text,), daemon=True).start()
            return reply_text

        except Exception as e:
            error_msg = f"Neural network error: {str(e)}"
            print(f"\n[JARVIS]: {error_msg}")
            threading.Thread(target=speak, args=(error_msg,), daemon=True).start()
            return error_msg

    def analyze_sentiment(self, text: str) -> str:
        text = text.lower()
        fatigued = ["tired", "exhausted", "sleepy", "headache", "stress", "slow", "hard", "difficult"]
        excited = ["awesome", "great", "wow", "amazing", "cool", "working", "happy", "yes", "lets go"]
        rushed = ["fast", "quick", "hurry", "rush", "now", "immediately", "brief", "compact"]
        
        if any(w in text for w in fatigued):
            return "Fatigued"
        elif any(w in text for w in excited):
            return "Excited"
        elif any(w in text for w in rushed):
            return "Rushed"
        return "Calm"

    def log_habit_metric(self, command_text: str):
        try:
            filepath = os.path.join("data", "habit_metrics.json")
            os.makedirs("data", exist_ok=True)
            metrics = {"total_queries": 0, "total_sessions": 0, "tools_invoked": {}, "last_active_timestamp": ""}
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
            
            # Record total queries and sessions
            metrics["total_queries"] = metrics.get("total_queries", 0) + 1
            metrics["last_active_timestamp"] = time.strftime("%Y-%m-%d %I:%M %p")
            
            # If total_sessions is 0 or not set, initialize it
            if metrics.get("total_sessions", 0) == 0:
                metrics["total_sessions"] = 1
                
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
        except Exception:
            pass


if __name__ == "__main__":
    brain = JarvisBrain()
    print("\n--- J.A.R.V.I.S. Interactive Core Diagnostics ---")
    print("Type 'exit' or 'shutdown' to terminate session.\n")

    while True:
        user_input = input("💬 Ask me anything → ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "shutdown"]:
            stop_audio()
            print("\n[System shutting down. Goodbye, Commander.]")
            break
        brain.process_command(user_input)
