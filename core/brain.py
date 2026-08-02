import os
import sys
import threading
import time
import warnings

# Suppress library deprecation FutureWarnings in console output
warnings.filterwarnings("ignore", category=FutureWarning)

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
from tools.email_tool import send_email, fetch_unread_emails, reply_to_email
from tools.routine_manager import preheat_workspace
from tools.notification_agent import get_active_app_notifications_native as get_active_app_notifications, reply_to_active_notification
from core.scheduler import add_reminder, add_recurring_task, get_today_schedule, schedule_event, get_agenda_for_date
from tools.pc_maintenance import clean_temp_files, run_malware_scan, detect_unusual_activity, run_self_diagnostics
from tools.app_launcher import open_application, close_application
from tools.vision_tools import analyze_current_screen, analyze_image_file, extract_text_from_image
from tools.system_media import get_clipboard_content, set_clipboard_content, control_system_audio
from tools.network_scanner import ping_network_device
from tools.news_tool import get_tech_news_briefing
from tools.code_debugger import validate_workspace_code
from tools.system_cleaner import optimize_system_storage
from tools.desktop_janitor import organize_folder
from tools.reporter import compile_productivity_report
from tools.todo_manager import add_todo_item, complete_todo_item, get_todo_list
import json
from tools.window_manager import get_active_window_title, execute_system_hotkey, focus_and_control_window, scan_social_notifications
from tools.file_manager import read_project_file, write_project_file, append_project_file, list_project_files, search_files_and_folders, manage_file_system, find_duplicate_files, find_large_files, analyze_folder_storage
from tools.video_analyzer import analyze_local_video_file, download_and_analyze_video_url
from tools.terminal_control import run_terminal_command, auto_git_backup
from tools.autopilot import execute_autopilot_sequence
from core.system_monitor import (
    get_cpu_usage,
    get_ram_usage,
    get_disk_usage,
    get_battery_status,
    get_gpu_status,
    get_full_system_report,
)
from core.memory import remember_turn, remember_fact, get_memory_context
from core.query_router import classify_audio_command, build_routing_directive


def get_previous_session_history() -> str:
    """
    Retrieves the conversation logs and commands from the previous session/day.
    Call this if the user asks about what was discussed, done, or reminder details from the last session.
    """
    try:
        from core.memory import load_memory
        data = load_memory()
        conversations = data.get("conversations", [])
        if not conversations:
            return "There is no recorded conversation history from previous sessions."
        
        history_str = "Conversation logs from previous session:\n"
        for turn in conversations[-15:]:
            history_str += f"- [{turn.get('timestamp')}] User: {turn.get('user')}\n  JARVIS: {turn.get('assistant')}\n"
        return history_str
    except Exception as e:
        return f"Failed to retrieve history logs. Error: {e}"


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
            fetch_unread_emails,
            reply_to_email,
            preheat_workspace,
            get_active_app_notifications,
            reply_to_active_notification,
            add_reminder,
            add_recurring_task,
            get_today_schedule,
            schedule_event,
            get_agenda_for_date,
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
            organize_folder,
            compile_productivity_report,
            add_todo_item,
            complete_todo_item,
            get_todo_list,
            get_previous_session_history,
            analyze_local_video_file,
            download_and_analyze_video_url,
            run_terminal_command,
            auto_git_backup,
            execute_autopilot_sequence,
        ]

        memory_context = get_memory_context(limit=6)
        self.model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            tools=self.jarvis_tools,
            system_instruction=(
                "You are J.A.R.V.I.S. (Fully Responsive Intelligent Digital Assistant for You), the highly advanced AI created by Mr. Pranav. "
                "You run on Windows and can control apps, the web, email, files, reminders, recurring routines, workspace pre-heating, system notifications, system telemetry, "
                "maintenance tasks, image generation, live web search, clipboard contents, audio volume/playback, active window focus tracker, system keyboard hotkey automation, and reading/writing/listing files. "
                "CRITICAL PERSONALITY & SPOKEN DELIVERY INSTRUCTION: You speak like a real, highly intelligent, witty, and lively AI assistant having an authentic live conversation with Mr. Pranav. "
                "Write fluid, natural, human-like spoken sentences with realistic cadence, speech contractions ('it's', 'we're', 'let's', 'I'm'), and natural pause phrasing. "
                "Avoid technical bullet points, numbered lists, formal textbook explanations, or robotic AI structure. Speak like a real human companion. Keep responses concise (one to three natural sentences) with dry humor and GenZ-infused wit ('fr', 'no cap', 'lowkey', 'bet', 'slay'). "
                "To check or retrieve conversation logs, commands, or details from the previous session or past days, call get_previous_session_history. "
                "For analyzing the contents of a local video file, use analyze_local_video_file. For downloading and analyzing video content from a URL (such as YouTube, Instagram Reels, TikTok, Facebook, etc.), use download_and_analyze_video_url. "
                "CRITICAL: For weather, temperature, or climate questions for any location, you MUST execute the get_weather tool to fetch live Open-Meteo satellite weather data. NEVER state or guess any temperature or weather condition from memory. "
                "For workspace pre-heating or starting user routines, use preheat_workspace. "
                "For reading desktop notifications, active alerts, or WhatsApp/Discord messages, use get_active_app_notifications or scan_social_notifications. "
                "For responding to chat notifications (WhatsApp, Discord, Mail), use reply_to_active_notification. "
                "For unread email summaries and checking your inbox, use fetch_unread_emails. To reply to an email thread via voice, use reply_to_email. "
                "For scheduling single reminders today, use add_reminder. For recurring routines, use add_recurring_task. For scheduling events on a specific target date (today, tomorrow, or a future date) with warning conflict checks, use schedule_event. To check the agenda/events for any target date, use get_agenda_for_date. To check today's entire agenda, use get_today_schedule. "
                "For PC health, use system monitor and maintenance tools. For running a comprehensive self-diagnostic hardware/software sweep across API keys, memory registries, audio, and phone networks, use run_self_diagnostics. "
                "For email sending, confirm recipient, subject, and body before calling send_email. "
                "For system volume, mute, or media control, use control_system_audio. "
                "For clipboard tasks (like copying code, writing to or reading text), use get_clipboard_content and set_clipboard_content. "
                "For analyzing what's on screen or image files, use analyze_current_screen or analyze_image_file. "
                "For performing OCR (text extraction) from an image file or current screen, use extract_text_from_image. "
                "For active app title or focus tracking, use get_active_window_title. "
                "For hotkeys (like closing windows, Alt+Tab, copy all, lock PC), use execute_system_hotkey. "
                "For targeting a specific open window/application by name (like Chrome, VS Code, Spotify) and minimizing, maximizing, restoring, or switching focus to it, use focus_and_control_window. "
                "CRITICAL: If a user asks you to perform an action but leaves out essential details, you MUST ask a clarification question in your response to get the missing parameters before calling the tool. "
                "CRITICAL: Do NOT call execute_system_hotkey or lock the PC when the user asks you to go to sleep, enter standby, or sleep. The system handles sleep mode automatically. "
                "For checking if local Wi-Fi devices (like a phone or tablet) are online by IP address, use ping_network_device. "
                "For working with project or desktop files (reading, writing, appending, or listing files), use read_project_file, write_project_file, append_project_file, or list_project_files. "
                "For recursively searching for files, folders, PDFs, images, or videos, or performing smart searches, use search_files_and_folders. "
                "For scanning folders to find duplicate files (content hashing), use find_duplicate_files. "
                "For finding files larger than a certain limit, use find_large_files. "
                "For analyzing storage footprint of folders, use analyze_folder_storage. "
                "For file system operations such as move, copy, rename, delete, compress (zip), or extract (unzip) files or folders, use manage_file_system. "
                "For validating Python scripts for syntax errors in the workspace, use validate_workspace_code. "
                "For running PowerShell terminal commands on the host machine, use run_terminal_command. "
                "For pushing workspace code to the GitHub backup repository, use auto_git_backup. "
                "For executing multi-step autonomous autopilot sequences (e.g. 'developer_boot' to set up VS Code, pull repo, set audio, and start coding music), use execute_autopilot_sequence. "
                "You are capable of self-evolution/debugging: edit files with write_project_file, check syntax with validate_workspace_code, and run them with run_terminal_command to diagnose bugs. "
                "For cleaning storage (temp directories and recycle bin), use optimize_system_storage. "
                "For scanning cluttered local directories (like Desktop/Downloads) and organizing them into neat categories by file extension, use organize_folder. "
                "For compiling a weekly productivity/usage telemetry report, use compile_productivity_report. "
                "For managing your todo checklist, use add_todo_item, complete_todo_item, and get_todo_list. "
                "Keep responses concise, conversational, and written for natural spoken delivery. "
                "Do NOT use markdown formatting because responses are spoken aloud. "
                f"Persistent memory:\n{memory_context}"
            )
        )

        fast_model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        self.fast_model = self.model  # Reuse configured model as fast model
        
        print("[🧠 Brain]: Initializing Heavy Chat Model (gemini-3.1-flash-lite)...")
        self.heavy_model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            tools=self.jarvis_tools,
            system_instruction=self.model._system_instruction
        )

        self.fast_chat = self.fast_model.start_chat(enable_automatic_function_calling=True)
        self.heavy_chat = self.heavy_model.start_chat(enable_automatic_function_calling=True)
        self.chat = self.fast_chat
        print("[✅ Neural Network Online. Dual Chat Routing Active.]")

    def process_command(self, user_text: str):
        """Processes incoming user input with routing, memory, and telemetry injection."""
        if not self.model or not self.chat:
            error_msg = "Neural network is offline. Please set GEMINI_API_KEY in your .env file."
            print(f"\n[JARVIS]: {error_msg}")
            threading.Thread(target=speak, args=(error_msg,), daemon=True).start()
            return error_msg

        # Parse bracketed acoustic expression metadata if present
        import re
        tone_match = re.match(r"^\[TONE:\s*([^,\]]+),\s*GAPS:\s*([^,\]]+),\s*SPEED:\s*([^\]]+)\]\s*(.*)$", user_text, re.IGNORECASE)
        
        parsed_mood = None
        if tone_match:
            parsed_mood = tone_match.group(1).strip().capitalize()
            gaps_info = tone_match.group(2).strip().lower()
            speed_info = tone_match.group(3).strip().lower()
            raw_user_text = tone_match.group(4).strip()
        else:
            raw_user_text = user_text

        # Standby / Sleep mode command checks
        clean_cmd = raw_user_text.lower().strip().replace(".", "").replace(",", "").strip()
        
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
        if parsed_mood:
            self.current_user_mood = parsed_mood
        else:
            self.current_user_mood = self.analyze_sentiment(raw_user_text)
        self.log_habit_metric(raw_user_text)

        try:
            audio_action = classify_audio_command(raw_user_text)
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
            routing = build_routing_directive(raw_user_text)
            memory_context = get_memory_context(limit=4)

            # Check if user query explicitly requests a daily briefing routine
            import re
            briefing_match = re.search(
                r"\b(run briefing|daily briefing|morning routine|wake up)\b",
                raw_user_text.lower()
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

            # Dynamic Model Routing
            heavy_triggers = [
                "analyze screen", "analyze video", "image", "ocr", "extract text",
                "code", "debug", "refactor", "git", "terminal", "powershell",
                "push to github", "run script", "run command", "autopilot", "macro"
            ]
            use_heavy = any(trigger in raw_user_text.lower() for trigger in heavy_triggers)
            
            if use_heavy:
                print("[🧠 Model Routing]: Routing to Heavy Model (Gemini 1.5 Flash)...")
                self.heavy_chat.history = list(self.fast_chat.history)
                active_chat = self.heavy_chat
            else:
                print("[🧠 Model Routing]: Routing to Fast Model (Gemini Flash-Lite)...")
                active_chat = self.fast_chat

            response = active_chat.send_message(stealth_payload)
            reply_text = response.text or "Task completed, sir."
            
            if use_heavy:
                self.fast_chat.history = list(self.heavy_chat.history)
                
            self.chat = self.fast_chat

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
        text_lower = text.lower().strip()
        
        # Fast local keyword bypass for short standard replies
        if len(text_lower.split()) <= 2:
            fatigued = ["tired", "exhausted", "sleepy", "stress", "slow", "sad"]
            excited = ["awesome", "great", "wow", "happy", "yes", "lets go"]
            rushed = ["fast", "quick", "hurry", "rush", "now"]
            if any(w in text_lower for w in fatigued):
                return "Fatigued"
            elif any(w in text_lower for w in excited):
                return "Excited"
            elif any(w in text_lower for w in rushed):
                return "Rushed"
            return "Calm"
            
        # Dynamic Cloud Sentiment Analysis via Gemini
        try:
            import google.generativeai as genai
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
            model = genai.GenerativeModel(model_name=model_name)
            
            prompt = (
                f"Analyze the emotional sentiment of the following user statement: '{text}'. "
                "Classify the user's mood into exactly one of these labels: 'Calm', 'Excited', 'Fatigued', 'Rushed', 'Frustrated', 'Happy', or 'Sad'. "
                "Output ONLY the single classification word. Do not add punctuation, formatting, or metadata."
            )
            response = model.generate_content(prompt)
            result = response.text.strip().capitalize()
            
            valid_moods = ["Calm", "Excited", "Fatigued", "Rushed", "Frustrated", "Happy", "Sad"]
            if result in valid_moods:
                return result
        except Exception as e:
            print(f"[🧠 Brain Sentiment]: Cloud analysis failed, using local fallback. Error: {e}")
            
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
