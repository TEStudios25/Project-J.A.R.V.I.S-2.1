import os
import sys
import threading
import time
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTextEdit, 
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QStackedWidget, QFrame, QScrollArea
)
from PyQt5.QtGui import QFont, QMovie, QColor, QPainter, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QThread, QPoint

# --- PATH ENFORCEMENT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the system modules safely
from core.brain import JarvisBrain
from core.reminder_service import ReminderService
from senses.stt_engine import listen
from senses.tts_engine import speak

class TelemetryWorker(QThread):
    """Background worker thread to fetch CPU, RAM, Disk, GPU, Battery, and Mobile connection status."""
    stats_updated = pyqtSignal(dict)

    def __init__(self, brain):
        super().__init__()
        self.brain = brain

    def run(self):
        import psutil
        import subprocess
        import re
        from core.system_monitor import get_disk_usage, get_battery_status, get_gpu_status
        from core.memory import load_memory
        
        while True:
            try:
                # Non-blocking CPU reading
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # RAM calculations
                ram = psutil.virtual_memory()
                ram_percent = ram.percent
                ram_str = f"RAM: {ram_percent}% ({round(ram.available / (1024 ** 3), 2)}GB free)"
                
                # Get other telemetry data
                disk_str = get_disk_usage()
                gpu_str = get_gpu_status()
                battery_str = get_battery_status()
                
                # Retrieve phone IP from memory facts dynamically
                phone_ip = None
                try:
                    mem = load_memory()
                    profile = mem.get("profile", {})
                    # 1. Search profile
                    for k, v in profile.items():
                        if "phone" in k or "mobile" in k:
                            ips = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", str(v))
                            if ips:
                                phone_ip = ips[0]
                                break
                    # 2. Search conversations if not in profile
                    if not phone_ip:
                        for conv in reversed(mem.get("conversations", [])):
                            user_txt = conv.get("user", "").lower()
                            if "phone ip" in user_txt or "mobile ip" in user_txt:
                                ips = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", conv.get("user", ""))
                                if ips:
                                    phone_ip = ips[0]
                                    # Dynamically save to profile
                                    try:
                                        from core.memory import remember_fact
                                        remember_fact("phone ip", phone_ip)
                                    except Exception:
                                        pass
                                    break
                except Exception:
                    pass
                
                phone_online = False
                if phone_ip:
                    try:
                        res = subprocess.run(
                            f"ping -n 1 -w 500 {phone_ip}",
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            creationflags=0x08000000
                        )
                        phone_online = (res.returncode == 0)
                    except Exception:
                        pass
                
                # Send back payload to GUI thread
                self.stats_updated.emit({
                    "cpu_percent": int(cpu_percent),
                    "cpu_str": f"CPU: {cpu_percent}%",
                    "ram_percent": int(ram_percent),
                    "ram_str": ram_str,
                    "disk_str": disk_str,
                    "gpu_str": gpu_str,
                    "battery_str": battery_str,
                    "phone_online": phone_online,
                    "phone_ip": phone_ip or "Not Registered"
                })
            except Exception:
                pass
            time.sleep(2.0) # Poll stats every 2.0 seconds in background thread

class WeatherWorker(QThread):
    """Background thread to poll wttr.in coordinates every 15 minutes to update HUD Radar."""
    weather_updated = pyqtSignal(dict)

    def run(self):
        while True:
            try:
                from tools.weather_tool import get_weather_dict
                w_data = get_weather_dict()
                self.weather_updated.emit(w_data)
            except Exception:
                pass
            time.sleep(900) # Every 15 minutes

class WaveVisualizer(QWidget):
    """Futuristic, interactive vector-drawn dual sine wave visualizer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)  # Compact space below GIF
        self.setMinimumWidth(300)
        self.phase = 0.0
        self.is_active = False

        # Animation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_wave)
        self.anim_timer.start(33) # ~30 FPS

    def animate_wave(self):
        # Shift phase for animation movement
        self.phase += 0.12 if self.is_active else 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        mid_y = height // 2

        # Adjust height amplitude based on J.A.R.V.I.S. activity
        amplitude = 14.0 if self.is_active else 1.8
        frequency = 0.025

        # Draw Main Wave (Electric Blue)
        pen1 = QPen(QColor("#007AFF"), 2)
        painter.setPen(pen1)
        
        points1 = []
        for x in range(0, width, 2):
            y = mid_y + math.sin(x * frequency + self.phase) * amplitude
            points1.append(QPoint(x, int(y)))
            
        for i in range(len(points1) - 1):
            painter.drawLine(points1[i], points1[i+1])

        # Draw Secondary Out-of-Phase Wave (Glowing Neon Cyan)
        pen2 = QPen(QColor("#66FCF1"), 1, Qt.DashLine)
        painter.setPen(pen2)
        
        points2 = []
        amplitude2 = amplitude * 0.55
        frequency2 = 0.035
        for x in range(0, width, 2):
            y = mid_y + math.cos(x * frequency2 - self.phase) * amplitude2
            points2.append(QPoint(x, int(y)))
            
        for i in range(len(points2) - 1):
            painter.drawLine(points2[i], points2[i+1])

class JarvisGUI(QMainWindow):
    append_text_signal = pyqtSignal(str, str)  # (Sender Name, Message Content)
    update_status_signal = pyqtSignal(str)     # (Status Bar Message)
    add_notif_signal = pyqtSignal(str)          # (Notification Log Entry)
    update_task_status_signal = pyqtSignal(str) # (Task Workspace Status)
    update_bio_signal = pyqtSignal(int)         # (Bio memory link count updates)

    def __init__(self):
        super().__init__()
        print("\n[🖥️ Activating Advanced Blue-HUD Command Suite Layout...]")
        
        # Initialize J.A.R.V.I.S. Brain
        self.brain = JarvisBrain()

        # Operational State Matrix
        self.mic_active = False  
        self.pending_confirmation_action = None
        
        # Autonomous reminder daemon
        self.reminder_service = ReminderService(on_reminder=self.handle_autonomous_reminder)
        self.reminder_service.start()
        
        self.initUI()
        
        # Link signals to safe execution slots
        self.append_text_signal.connect(self.safe_append_chat)
        self.update_status_signal.connect(self.safe_update_status)
        self.add_notif_signal.connect(self.safe_add_notification)
        self.update_task_status_signal.connect(self.safe_update_task_status)
        self.update_bio_signal.connect(self.safe_update_bio)
        
        # Start QTimer for Clock (12h format updates)
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        
        # Start background telemetry thread worker to prevent GUI lagging
        self.telemetry_worker = TelemetryWorker(self.brain)
        self.telemetry_worker.stats_updated.connect(self.handle_telemetry_update)
        self.telemetry_worker.start()

        # Start weather monitor thread
        self.weather_worker = WeatherWorker()
        self.weather_worker.weather_updated.connect(self.handle_weather_update)
        self.weather_worker.start()
        
        # Update user facts
        self.update_bio_from_memory()
        
        # Play Boot Sound
        self.play_sfx("boot.wav")
        
        # Log system boot logs
        self.add_notif_signal.emit("J.A.R.V.I.S Core online.")
        self.add_notif_signal.emit("Telemetry sensors synchronized.")
        self.add_notif_signal.emit("Auto-submit STT listener standby.")
        self.add_notif_signal.emit("System audio sessions mapped.")
        
        # Fire up background listening worker thread
        threading.Thread(target=self.voice_listening_worker, daemon=True).start()

    def play_sfx(self, sound_name: str):
        """Plays custom synthesized Sci-Fi audio chimes safely via pygame soundboard mixer."""
        try:
            import pygame
            sound_path = os.path.join("Frontend", "Sounds", sound_name)
            if os.path.exists(sound_path):
                pygame.mixer.Sound(sound_path).play()
        except Exception:
            pass

    def initUI(self):
        # Frameless window configuration with an absolute J.A.R.V.I.S. theme
        self.setWindowTitle("Project J.A.R.V.I.S. 2.0 Command Center")
        self.resize(1250, 820)
        
        # Main stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #07090D;
            }
            QLabel {
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
                color: #E1E2E6;
            }
            QPushButton {
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
            }
            QProgressBar {
                background-color: #0C0F15;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 4px;
            }
        """)

        # Central widget layout split into 3 columns
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ===============================================================
        # 📊 LEFT COLUMN: LOGO, BIO, WEATHER, SPECS & NOTIF LOGS (FULL HEIGHT)
        # ===============================================================
        left_column = QVBoxLayout()
        left_column.setSpacing(15)
        
        # 1. App Header Title Box (Highlight 1 - Brahma Logo Block Style)
        header_frame = QFrame()
        header_frame.setFixedWidth(290)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #1C2735;
                border-radius: 12px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(10)
        
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(40, 40)
        logo_lbl.setStyleSheet("""
            QLabel {
                background-color: #0B0C10;
                border: 2px solid #66FCF1;
                border-radius: 20px;
            }
        """)
        logo_lbl.setText("⚙️")
        logo_lbl.setFont(QFont("Segoe UI Emoji", 12))
        logo_lbl.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(logo_lbl)
        
        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(2)
        
        title_lbl = QLabel("J.A.R.V.I.S. 2.0")
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_lbl.setStyleSheet("color: #66FCF1; border: none; font-weight: bold;")
        title_text_layout.addWidget(title_lbl)
        
        subtitle_lbl = QLabel("Your Personal Assistant")
        subtitle_lbl.setFont(QFont("Segoe UI", 8))
        subtitle_lbl.setStyleSheet("color: #8A8F98; border: none;")
        title_text_layout.addWidget(subtitle_lbl)
        
        header_layout.addLayout(title_text_layout)
        header_layout.addStretch()
        left_column.addWidget(header_frame)
        
        # 2. Personal Bio Card Box (Highlight 11 - Top Sidebar)
        bio_frame = QFrame()
        bio_frame.setFixedWidth(290)
        bio_frame.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #1C2735;
                border-radius: 12px;
            }
        """)
        bio_layout = QVBoxLayout(bio_frame)
        bio_layout.setContentsMargins(15, 12, 15, 12)
        bio_layout.setSpacing(6)
        
        bio_header = QLabel("COGNITIVE USER BIO")
        bio_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        bio_header.setStyleSheet("color: #66FCF1; border: none; letter-spacing: 1px;")
        bio_layout.addWidget(bio_header)
        
        self.bio_name = QLabel("User: Mr. Pranav")
        self.bio_name.setFont(QFont("Segoe UI", 9))
        self.bio_name.setStyleSheet("color: #E1E2E6; border: none;")
        bio_layout.addWidget(self.bio_name)
        
        self.bio_role = QLabel("Role: Developer")
        self.bio_role.setFont(QFont("Segoe UI", 9))
        self.bio_role.setStyleSheet("color: #E1E2E6; border: none;")
        bio_layout.addWidget(self.bio_role)
        
        self.bio_lang = QLabel("Focus: Personal AI Assistant")
        self.bio_lang.setFont(QFont("Segoe UI", 9))
        self.bio_lang.setStyleSheet("color: #45A29E; border: none;")
        bio_layout.addWidget(self.bio_lang)
        
        # Highlight 31: Cognitive User Mood Gauge display
        self.bio_mood = QLabel("Mood: Calm")
        self.bio_mood.setFont(QFont("Segoe UI", 9))
        self.bio_mood.setStyleSheet("color: #45A29E; border: none;")
        bio_layout.addWidget(self.bio_mood)
        
        # Highlight 1 (Adapted): Mobile Connection Node HUD indicator (Button Box Style)
        self.phone_node_lbl = QLabel("PHONE LINK: OFFLINE")
        self.phone_node_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.phone_node_lbl.setAlignment(Qt.AlignCenter)
        self.phone_node_lbl.setFixedHeight(28)
        self.phone_node_lbl.setFixedWidth(200)
        self.phone_node_lbl.setStyleSheet("""
            QLabel {
                background-color: #200A0A;
                border: 1px solid #FF453A;
                color: #FF453A;
                border-radius: 6px;
            }
        """)
        bio_layout.addWidget(self.phone_node_lbl, 0, Qt.AlignCenter)
        
        self.bio_memory = QLabel("Core Sync: Memory calibrated")
        self.bio_memory.setFont(QFont("Segoe UI", 9))
        self.bio_memory.setStyleSheet("color: #8A8F98; border: none;")
        bio_layout.addWidget(self.bio_memory)
        
        left_column.addWidget(bio_frame, stretch=1)
        
        # 3. Weather HUD Radar Card (Highlight 4)
        weather_frame = QFrame()
        weather_frame.setFixedWidth(290)
        weather_frame.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #1C2735;
                border-radius: 12px;
            }
        """)
        weather_layout = QVBoxLayout(weather_frame)
        weather_layout.setContentsMargins(15, 12, 15, 12)
        weather_layout.setSpacing(6)
        
        weather_header = QLabel("ENVIRONMENT RADAR")
        weather_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        weather_header.setStyleSheet("color: #66FCF1; border: none; letter-spacing: 1px;")
        weather_layout.addWidget(weather_header)
        
        self.weather_lbl = QLabel("Weather: Syncing wttr...")
        self.weather_lbl.setFont(QFont("Segoe UI", 9))
        self.weather_lbl.setStyleSheet("color: #E1E2E6; border: none;")
        self.weather_lbl.setWordWrap(True)
        weather_layout.addWidget(self.weather_lbl)
        
        left_column.addWidget(weather_frame, stretch=1)
        
        # 4. Telemetry Container (Highlight 11 - Moved to Middle)
        telemetry_frame = QFrame()
        telemetry_frame.setFixedWidth(290)
        telemetry_frame.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #1C2735;
                border-radius: 12px;
            }
        """)
        telemetry_layout = QVBoxLayout(telemetry_frame)
        telemetry_layout.setContentsMargins(15, 15, 15, 15)
        telemetry_layout.setSpacing(12)
        
        telemetry_header = QLabel("SYSTEM TELEMETRY")
        telemetry_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        telemetry_header.setStyleSheet("color: #66FCF1; border: none; letter-spacing: 1px;")
        telemetry_layout.addWidget(telemetry_header)
        
        # CPU Monitor Widget
        self.cpu_lbl = QLabel("CPU: Fetching...")
        self.cpu_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.cpu_lbl.setStyleSheet("color: #E1E2E6; border: none;")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setFixedHeight(6)
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setStyleSheet("""
            QProgressBar { background-color: #080A0E; border: none; border-radius: 3px; }
            QProgressBar::chunk { background-color: #007AFF; border-radius: 3px; }
        """)
        telemetry_layout.addWidget(self.cpu_lbl)
        telemetry_layout.addWidget(self.cpu_bar)
        
        # RAM Monitor Widget
        self.ram_lbl = QLabel("RAM: Fetching...")
        self.ram_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.ram_lbl.setStyleSheet("color: #E1E2E6; border: none;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setFixedHeight(6)
        self.ram_bar.setTextVisible(False)
        self.ram_bar.setStyleSheet("""
            QProgressBar { background-color: #080A0E; border: none; border-radius: 3px; }
            QProgressBar::chunk { background-color: #66FCF1; border-radius: 3px; }
        """)
        telemetry_layout.addWidget(self.ram_lbl)
        telemetry_layout.addWidget(self.ram_bar)
        
        # Disk Monitor Label
        self.disk_lbl = QLabel("Disk: Checking OS...")
        self.disk_lbl.setWordWrap(True)
        self.disk_lbl.setFont(QFont("Segoe UI", 9))
        self.disk_lbl.setStyleSheet("color: #8A8F98; border: none; line-height: 1.3;")
        telemetry_layout.addWidget(self.disk_lbl)
        
        # GPU Monitor Label
        self.gpu_lbl = QLabel("GPU: Querying Controller...")
        self.gpu_lbl.setWordWrap(True)
        self.gpu_lbl.setFont(QFont("Segoe UI", 9))
        self.gpu_lbl.setStyleSheet("color: #8A8F98; border: none; line-height: 1.3;")
        telemetry_layout.addWidget(self.gpu_lbl)
        
        # Battery Monitor Label
        self.battery_lbl = QLabel("Battery: Reading DC/AC...")
        self.battery_lbl.setFont(QFont("Segoe UI", 9))
        self.battery_lbl.setStyleSheet("color: #8A8F98; border: none;")
        telemetry_layout.addWidget(self.battery_lbl)
        
        left_column.addWidget(telemetry_frame, stretch=2)
        
        # 5. System Notifications Log Container (Highlight 11 - Moved to Bottom)
        notif_frame = QFrame()
        notif_frame.setFixedWidth(290)
        notif_frame.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #1C2735;
                border-radius: 12px;
            }
        """)
        notif_layout = QVBoxLayout(notif_frame)
        notif_layout.setContentsMargins(15, 15, 15, 15)
        notif_layout.setSpacing(10)
        
        notif_header = QLabel("SYSTEM STATUS LOG")
        notif_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        notif_header.setStyleSheet("color: #66FCF1; border: none; letter-spacing: 1px;")
        notif_layout.addWidget(notif_header)
        
        self.notif_display = QTextEdit()
        self.notif_display.setReadOnly(True)
        self.notif_display.setFont(QFont("Consolas", 9))
        self.notif_display.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #8A8F98;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 5px;
            }
            QScrollBar::handle:vertical {
                background: #1C2735;
                border-radius: 2px;
            }
        """)
        notif_layout.addWidget(self.notif_display)
        
        left_column.addWidget(notif_frame, stretch=3)
        
        # Online indicator
        self.online_status_lbl = QLabel("● SYSTEM ACTIVE // WORKSTATION STABLE")
        self.online_status_lbl.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.online_status_lbl.setStyleSheet("color: #66FCF1; padding-left: 5px; letter-spacing: 1px;") 
        left_column.addWidget(self.online_status_lbl)
        
        main_layout.addLayout(left_column)

        # ===============================================================
        # 🎯 CENTER COLUMN: HEADER BAR & TARGET VISUALIZER CORE
        # ===============================================================
        center_column = QVBoxLayout()
        center_column.setSpacing(15)
        
        # Header bar (Highlight 3 - Title on Left, Clock on Right)
        hud_header_frame = QFrame()
        hud_header_frame.setStyleSheet("background-color: transparent; border: none;")
        hud_header_layout = QHBoxLayout(hud_header_frame)
        hud_header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left title
        hud_title_lbl = QLabel("PROJECT J.A.R.V.I.S. 2.0")
        hud_title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        hud_title_lbl.setStyleSheet("color: #FFFFFF; font-weight: bold; letter-spacing: 1px;")
        hud_header_layout.addWidget(hud_title_lbl)
        
        hud_header_layout.addStretch()
        
        # Right clock
        hud_clock_layout = QVBoxLayout()
        hud_clock_layout.setSpacing(2)
        hud_clock_layout.setAlignment(Qt.AlignRight)
        
        self.clock_time_lbl = QLabel("00:00:00 AM")
        self.clock_time_lbl.setAlignment(Qt.AlignRight)
        self.clock_time_lbl.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.clock_time_lbl.setStyleSheet("color: #66FCF1; font-weight: bold; letter-spacing: 1px;")
        hud_clock_layout.addWidget(self.clock_time_lbl)
        
        self.clock_date_lbl = QLabel("MON 01 JAN 2026")
        self.clock_date_lbl.setAlignment(Qt.AlignRight)
        self.clock_date_lbl.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.clock_date_lbl.setStyleSheet("color: #45A29E; text-transform: uppercase; letter-spacing: 2px;")
        hud_clock_layout.addWidget(self.clock_date_lbl)
        
        hud_header_layout.addLayout(hud_clock_layout)
        center_column.addWidget(hud_header_frame)
        
        # Widescreen target frame (Highlight 2 - 16:9 widescreen layout)
        visualizer_frame = QFrame()
        visualizer_frame.setStyleSheet("""
            QFrame {
                background-color: #080A0E;
                border: 1px solid #1C2735;
                border-radius: 12px;
            }
        """)
        visualizer_layout = QVBoxLayout(visualizer_frame)
        visualizer_layout.setContentsMargins(5, 5, 5, 5) 
        visualizer_layout.setAlignment(Qt.AlignCenter)
        
        self.gif_display = QLabel()
        self.gif_display.setAlignment(Qt.AlignCenter)
        self.gif_display.setStyleSheet("background-color: transparent; border: none;")
        
        gif_path = os.path.join("Frontend", "Graphics", "Jarvis.gif")
        if not os.path.exists(gif_path):
            gif_path = "Jarvis.gif"

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.movie.setScaledSize(QSize(600, 338))  # 16:9 ratio
            self.gif_display.setMovie(self.movie)
            self.movie.start()
        else:
            self.gif_display.setText("[ HOLOGRAPHIC AUDIO CORE OFFLINE ]")
            self.gif_display.setStyleSheet("color: #66FCF1; font-size: 13px; font-weight: bold; font-family: Consolas;")
        visualizer_layout.addWidget(self.gif_display)
        
        # Highlight 1: Vector Wave visualizer directly below the GIF
        self.wave_widget = WaveVisualizer()
        visualizer_layout.addWidget(self.wave_widget)
        
        center_column.addWidget(visualizer_frame, stretch=1)

        # Status capsule Display
        self.status_display = QLabel("SYSTEM STATUS: STANDBY // MICROPHONE MUTED")
        self.status_display.setAlignment(Qt.AlignCenter)
        self.status_display.setStyleSheet("""
            QLabel {
                background-color: #121620;
                color: #45A29E;
                border: 1px solid #1C2735;
                border-radius: 14px;
                padding: 6px 14px;
                font-family: 'Segoe UI', Arial;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        center_column.addWidget(self.status_display)

        # Bottom Command Input Panel
        input_panel = QFrame()
        input_panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #1C2735;
                border-radius: 12px;
            }
        """)
        input_layout = QHBoxLayout(input_panel)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)
        
        # Input Textbox
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter system command parameter...")
        self.text_input.setFont(QFont("Segoe UI", 10))
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                padding: 6px;
            }
        """)
        self.text_input.returnPressed.connect(self.submit_text_command)
        input_layout.addWidget(self.text_input)
        
        # Mic Activation Button
        self.mic_btn = QPushButton("🎙️")
        self.mic_btn.setFixedSize(38, 38)
        self.mic_btn.setFont(QFont("Segoe UI Emoji", 11))
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #07090D;
                color: #45A29E;
                border: 1px solid #1C2735;
                border-radius: 8px;
            }
            QPushButton:hover {
                border-color: #66FCF1;
                color: #FFFFFF;
            }
        """)
        self.mic_btn.clicked.connect(self.toggle_microphone_state)
        input_layout.addWidget(self.mic_btn)
        
        # Send Button
        self.send_btn = QPushButton("➔")
        self.send_btn.setFixedSize(38, 38)
        self.send_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: #FFFFFF;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #66FCF1;
                color: #07090D;
            }
        """)
        self.send_btn.clicked.connect(self.submit_text_command)
        input_layout.addWidget(self.send_btn)

        center_column.addWidget(input_panel)
        main_layout.addLayout(center_column, stretch=2)

        # ===============================================================
        # 💬 RIGHT COLUMN: BUBBLY CHAT WORKSPACE (FULL HEIGHT)
        # ===============================================================
        right_column = QVBoxLayout()
        right_column.setSpacing(15)
        
        workspace_frame = QFrame()
        workspace_frame.setMinimumWidth(400)
        workspace_frame.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #1C2735;
                border-radius: 12px;
            }
        """)
        workspace_layout = QVBoxLayout(workspace_frame)
        workspace_layout.setContentsMargins(15, 18, 15, 18)
        workspace_layout.setSpacing(15)
        
        workspace_header = QLabel("COMMAND WORKSPACE")
        workspace_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        workspace_header.setStyleSheet("color: #66FCF1; border: none; letter-spacing: 1px;")
        workspace_layout.addWidget(workspace_header)
        
        # Tabs selectors
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(10)
        
        self.chat_tab_btn = QPushButton("CHAT")
        self.chat_tab_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.chat_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #66FCF1;
                color: #07090D;
                border-radius: 6px;
                border: none;
                padding: 8px;
            }
        """)
        self.chat_tab_btn.clicked.connect(lambda: self.switch_tab(0))
        tabs_layout.addWidget(self.chat_tab_btn)
        
        self.hist_tab_btn = QPushButton("HISTORY")
        self.hist_tab_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.hist_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #080A0E;
                color: #45A29E;
                border-radius: 6px;
                border: 1px solid #1C2735;
                padding: 8px;
            }
            QPushButton:hover {
                border-color: #66FCF1;
                color: #FFFFFF;
            }
        """)
        self.hist_tab_btn.clicked.connect(lambda: self.switch_tab(1))
        tabs_layout.addWidget(self.hist_tab_btn)
        
        workspace_layout.addLayout(tabs_layout)
        
        # Stacked widget for Chat and History
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("border: none; background-color: transparent;")
        
        # Container widget for Chat tab (Highlight 13 - Card Workspace + Chat display)
        chat_container = QWidget()
        chat_container_layout = QVBoxLayout(chat_container)
        chat_container_layout.setContentsMargins(0, 0, 0, 0)
        chat_container_layout.setSpacing(12)
        
        # Task & Schedule Workspace Card (Brahma Style)
        task_workspace_card = QFrame()
        task_workspace_card.setStyleSheet("""
            QFrame {
                background-color: #0B0D13;
                border: 1px solid #1C2735;
                border-radius: 10px;
            }
        """)
        task_layout = QVBoxLayout(task_workspace_card)
        task_layout.setContentsMargins(12, 12, 12, 12)
        task_layout.setSpacing(6)
        
        task_title = QLabel("TASK & SCHEDULE WORKSPACE")
        task_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        task_title.setStyleSheet("color: #66FCF1; border: none;")
        task_layout.addWidget(task_title)
        
        self.task_status_lbl = QLabel("Status: Idle // Waiting for command input")
        self.task_status_lbl.setFont(QFont("Segoe UI", 8))
        self.task_status_lbl.setStyleSheet("color: #8A8F98; border: none;")
        task_layout.addWidget(self.task_status_lbl)
        
        self.task_schedule_lbl = QLabel("Today's Agenda: Reading database...")
        self.task_schedule_lbl.setFont(QFont("Segoe UI", 8))
        self.task_schedule_lbl.setStyleSheet("color: #E1E2E6; border: none;")
        self.task_schedule_lbl.setWordWrap(True)
        task_layout.addWidget(self.task_schedule_lbl)
        
        # Highlight 33: Auto-updating Todo Checklist Card GUI segment
        self.todo_list_display = QLabel("Checklist: Reading core records...")
        self.todo_list_display.setFont(QFont("Segoe UI", 8))
        self.todo_list_display.setStyleSheet("color: #45A29E; border: none; margin-top: 2px;")
        self.todo_list_display.setWordWrap(True)
        task_layout.addWidget(self.todo_list_display)
        
        chat_container_layout.addWidget(task_workspace_card)
        
        # Current Chat Log (Replaced with a QScrollArea containing custom QFrame widgets for native rounded borders and background styling)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #66FCF1;
                border-radius: 3px;
            }
        """)
        
        self.chat_container = QWidget()
        self.chat_container.setObjectName("ChatContainer")
        self.chat_container.setStyleSheet("QWidget#ChatContainer { background-color: transparent; }")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        chat_container_layout.addWidget(self.chat_scroll)
        
        self.stacked_widget.addWidget(chat_container)
        
        # Tab 2: History Log
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #45A29E;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #66FCF1;
                border-radius: 3px;
            }
        """)
        self.stacked_widget.addWidget(self.history_display)
        workspace_layout.addWidget(self.stacked_widget)
        
        right_column.addWidget(workspace_frame)
        main_layout.addLayout(right_column)

    # --- CLOCK WORKERS ---
    def update_clock(self):
        """Updates date and time display using 12-hour format."""
        self.clock_time_lbl.setText(time.strftime("%I:%M:%S %p"))
        self.clock_date_lbl.setText(time.strftime("%a %d %b %Y").upper())
        
        # Highlight 31: Update User mood status real-time on clock ticks
        try:
            self.bio_mood.setText(f"Mood: {self.brain.current_user_mood}")
        except Exception:
            pass
        
        # Highlight 33: Update Todo Checklist dynamically
        try:
            from tools.todo_manager import load_todos
            todos = load_todos()
            pending = [t for t in todos if not t.get("completed", False)]
            todo_text = "🎯 Active Checklist:\n"
            if not pending:
                todo_text += "  • All tasks completed!"
            else:
                for t in pending[:3]:
                    todo_text += f"  • [ ] {t.get('task')}\n"
            self.todo_list_display.setText(todo_text.strip())
        except Exception:
            pass
        
        # Poll schedule updates inside clock ticker to keep tasks card current
        try:
            from core.scheduler import get_today_schedule
            schedule_text = get_today_schedule()
            self.task_schedule_lbl.setText(schedule_text.replace("Here is your scheduled itinerary for today:", "Agenda:").strip())
        except Exception:
            pass

    # --- TELEMETRY STATS CALLBACK ---
    def handle_telemetry_update(self, stats: dict):
        """Processes telemetry payload emitted from background thread safely."""
        self.cpu_lbl.setText(stats["cpu_str"])
        self.cpu_bar.setValue(stats["cpu_percent"])
        
        self.ram_lbl.setText(stats["ram_str"])
        self.ram_bar.setValue(stats["ram_percent"])
        
        self.disk_lbl.setText(stats["disk_str"])
        self.gpu_lbl.setText(stats["gpu_str"])
        self.battery_lbl.setText(stats["battery_str"])
        
        # Highlight 1: Render mobile status node online/offline glow state
        if stats.get("phone_online", False):
            self.phone_node_lbl.setText("PHONE LINK: ONLINE")
            self.phone_node_lbl.setStyleSheet("""
                QLabel {
                    background-color: #00221C;
                    border: 1px solid #66FCF1;
                    color: #66FCF1;
                    border-radius: 6px;
                    font-weight: bold;
                }
            """)
        else:
            self.phone_node_lbl.setText("PHONE LINK: OFFLINE")
            self.phone_node_lbl.setStyleSheet("""
                QLabel {
                    background-color: #200A0A;
                    border: 1px solid #FF453A;
                    color: #FF453A;
                    border-radius: 6px;
                    font-weight: bold;
                }
            """)
        
        # Highlight 6: CPU utilization guard alert (80-90% CPU threshold)
        if stats["cpu_percent"] >= 80:
            current_time = time.time()
            # 30 seconds warning cooldown to prevent spamming
            if not hasattr(self, "last_cpu_warning") or (current_time - self.last_cpu_warning > 30):
                self.last_cpu_warning = current_time
                self.add_notif_signal.emit(f"⚠️ SYSTEM WARNING: CPU utilization high ({stats['cpu_percent']}%)")
                self.play_sfx("warning.wav")

    # --- WEATHER STATS CALLBACK ---
    def handle_weather_update(self, w_data: dict):
        """Updates the Left Sidebar Environment Radar card with weather icons."""
        desc = w_data.get("desc", "Unknown").lower()
        temp = w_data.get("temp_c", "N/A")
        place = w_data.get("place", "")
        
        # Emoji mapping
        emoji = "☀️"
        if "rain" in desc or "drizzle" in desc or "shower" in desc:
            emoji = "🌧️"
        elif "thunder" in desc:
            emoji = "🌩️"
        elif "cloud" in desc or "overcast" in desc:
            emoji = "☁️"
        elif "snow" in desc or "ice" in desc:
            emoji = "❄️"
        elif "mist" in desc or "fog" in desc or "haze" in desc:
            emoji = "🌫️"
            
        self.weather_lbl.setText(f"{emoji} {place}: {w_data.get('desc', 'Unknown')}\nTemp: {temp}°C")

    # --- BIO STATE LOAD WORKER ---
    def update_bio_from_memory(self):
        """Pulls facts J.A.R.V.I.S. knows about you from memory."""
        try:
            from core.memory import load_memory
            data = load_memory()
            facts = data.get("facts", [])
            self.update_bio_signal.emit(len(facts))
        except Exception:
            pass

    # --- TAB NAVIGATION CONTROLLER ---
    def switch_tab(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        if index == 0:
            self.chat_tab_btn.setStyleSheet("""
                QPushButton { background-color: #66FCF1; color: #07090D; border-radius: 6px; border: none; padding: 8px; }
            """)
            self.hist_tab_btn.setStyleSheet("""
                QPushButton { background-color: #080A0E; color: #45A29E; border-radius: 6px; border: 1px solid #1C2735; padding: 8px; }
                QPushButton:hover { border-color: #66FCF1; color: #FFFFFF; }
            """)
        else:
            self.hist_tab_btn.setStyleSheet("""
                QPushButton { background-color: #66FCF1; color: #07090D; border-radius: 6px; border: none; padding: 8px; }
            """)
            self.chat_tab_btn.setStyleSheet("""
                QPushButton { background-color: #080A0E; color: #45A29E; border-radius: 6px; border: 1px solid #1C2735; padding: 8px; }
                QPushButton:hover { border-color: #66FCF1; color: #FFFFFF; }
            """)
            self.load_conversations_history()

    def load_conversations_history(self):
        self.history_display.clear()
        try:
            from core.memory import load_memory
            data = load_memory()
            conversations = data.get("conversations", [])
            if not conversations:
                self.history_display.append("No historic logs found in memories database.")
                return
                
            for idx, turn in enumerate(conversations):
                self.history_display.append(
                    f"<div style='margin-bottom: 12px; padding: 10px; border-bottom: 1px solid #1C2735; font-family: Segoe UI;'>"
                    f"<span style='color: #66FCF1; font-weight: bold; font-size: 11px;'>Turn {idx+1} | {turn.get('timestamp', '')}</span><br/>"
                    f"<span style='color: #E1E2E6; font-size: 12px;'><b>User:</b> {turn.get('user', '')}</span><br/>"
                    f"<span style='color: #8A8F98; font-size: 12px;'><b>Jarvis:</b> {turn.get('assistant', '')}</span>"
                    f"</div>"
                )
        except Exception as e:
            self.history_display.setText(f"Error reading history logs: {str(e)}")

    def handle_autonomous_reminder(self, message: str):
        self.append_text_signal.emit("J.A.R.V.I.S.", message)
        self.update_status_signal.emit("SYSTEM STATUS: REMINDER DELIVERED")
        self.add_notif_signal.emit(f"Reminder alert spoken: {message[:30]}...")

    # --- INPUT PROCESSING SUBSYSTEMS ---
    def submit_text_command(self):
        raw_text = self.text_input.text().strip()
        if not raw_text:
            return
        
        self.text_input.clear()
        self.safe_append_chat("Mr. Pranav", raw_text)
        self.add_notif_signal.emit(f"User command: '{raw_text[:20]}'")
        
        # Intercept if a confirmation is active
        if self.pending_confirmation_action:
            threading.Thread(target=self.handle_confirmation_input, args=(raw_text,), daemon=True).start()
            return
            
        # Process context
        threading.Thread(target=self.execute_brain_processing, args=(raw_text,), daemon=True).start()

    def toggle_microphone_state(self):
        self.mic_active = not self.mic_active
        if self.mic_active:
            self.mic_btn.setText("🔵") 
            self.mic_btn.setStyleSheet("""
                QPushButton { background-color: #66FCF1; color: #07090D; border-radius: 8px; border: none; }
            """)
            self.update_status_signal.emit("SYSTEM STATUS: LISTENING ACTIVE // MIC FEED LIVE")
            self.add_notif_signal.emit("Microphone capture active.")
            self.wave_widget.is_active = True
        else:
            self.mic_btn.setText("🎙️")
            self.mic_btn.setStyleSheet("""
                QPushButton { background-color: #080A0E; color: #45A29E; border: 1px solid #1C2735; border-radius: 8px; }
                QPushButton:hover { border-color: #66FCF1; color: #FFFFFF; }
            """)
            self.update_status_signal.emit("SYSTEM STATUS: STANDBY // MICROPHONE MUTED")
            self.add_notif_signal.emit("Microphone capture standby.")
            self.wave_widget.is_active = False

    # --- THREAD WORKERS & BACKEND OVERLOAD CHANNELS ---
    def voice_listening_worker(self):
        while True:
            if not self.mic_active:
                time.sleep(0.2)
                continue
            
            voice_query = listen(check_active_func=lambda: self.mic_active)
            if voice_query and self.mic_active:
                self.append_text_signal.emit("Mr. Pranav", voice_query)
                
                # Intercept if a confirmation is active
                if self.pending_confirmation_action:
                    threading.Thread(target=self.handle_confirmation_input, args=(voice_query,), daemon=True).start()
                    continue
                    
                self.execute_brain_processing(voice_query)

    def execute_brain_processing(self, command_text: str):
        clean_cmd = command_text.lower().strip()
        
        # 🚨 SYSTEM SHUTDOWN INTERCEPT 🚨
        if clean_cmd in ["shutdown", "exit", "quit", "power off", "shutdown system", "close system"]:
            self.pending_confirmation_action = "shutdown"
            msg = "Confirming authorization, sir. Are you sure you want to shut down J.A.R.V.I.S.?"
            self.append_text_signal.emit("J.A.R.V.I.S.", msg)
            self.add_notif_signal.emit("Awaiting shutdown authorization.")
            speak(msg)
            return
            
        self.update_status_signal.emit("SYSTEM STATUS: COMPILED Telemetry sequence processing...")
        self.add_notif_signal.emit("Querying brain server...")
        self.wave_widget.is_active = True
        self.update_task_status_signal.emit(f"Status: Busy // Processing: '{command_text[:25]}...'")
        
        try:
            reply = self.brain.process_command(command_text)

            if clean_cmd in ["stop", "pause", "resume", "continue", "shut up"]:
                self.append_text_signal.emit("SYSTEM", "Audio override sequence executed.")
                self.add_notif_signal.emit("Playback override executed.")
            elif reply:
                self.append_text_signal.emit("J.A.R.V.I.S.", reply)
                self.add_notif_signal.emit("Neural reply complete.")
                # Play success digital chime
                self.play_sfx("success.wav")
                # Sync bio links count
                self.update_bio_from_memory()
            
        except Exception as e:
            self.append_text_signal.emit("SYSTEM", f"Core Processing Error Matrix: {str(e)}")
            self.add_notif_signal.emit(f"Core error: {str(e)[:25]}...")
            
        self.update_task_status_signal.emit("Status: Idle // Waiting for command input")
        if self.mic_active:
            self.update_status_signal.emit("SYSTEM STATUS: LISTENING ACTIVE // MIC FEED LIVE")
            self.wave_widget.is_active = True
        else:
            self.update_status_signal.emit("SYSTEM STATUS: STANDBY // MICROPHONE MUTED")
            self.wave_widget.is_active = False

    def handle_confirmation_input(self, text: str):
        clean_txt = text.lower().strip()
        
        if any(w in clean_txt for w in ["yes", "confirm", "proceed", "sure", "do it"]):
            if self.pending_confirmation_action == "shutdown":
                self.pending_confirmation_action = None
                self.update_status_signal.emit("SYSTEM STATUS: INITIATING SHUTDOWN...")
                self.append_text_signal.emit("SYSTEM", "Executing shutdown protocol...")
                self.add_notif_signal.emit("Initiating shutdown loop.")
                self.execute_actual_shutdown()
        elif any(w in clean_txt for w in ["no", "cancel", "abort", "stop", "don't"]):
            self.pending_confirmation_action = None
            msg = "Shutdown protocol aborted, sir."
            self.append_text_signal.emit("J.A.R.V.I.S.", msg)
            self.add_notif_signal.emit("Shutdown aborted.")
            speak(msg)
            self.update_status_signal.emit("SYSTEM STATUS: STANDBY")
        else:
            msg = "Confirmation required. Please type or say 'Yes' to proceed, or 'Cancel' to abort."
            self.append_text_signal.emit("J.A.R.V.I.S.", msg)
            speak(msg)

    def execute_actual_shutdown(self):
        final_words = "Shutting down core processors. It was an honor serving you, Mr. Pranav."
        self.append_text_signal.emit("J.A.R.V.I.S.", final_words)
        self.play_sfx("shutdown.wav")
        speak(final_words)
        time.sleep(1.0)
        QApplication.instance().quit()

    # --- SAFE DISPLAY MANIPULATION BLOCKS ---
    def safe_append_chat(self, sender: str, text: str):
        # Create message bubble frame natively to support absolute borders and rounded corners
        bubble = QFrame()
        
        if sender == "J.A.R.V.I.S.":
            name_color = "#66FCF1" # Cyan Accent
            bg_color = "#0B0D13"   # Dark card fill matching layout theme
            border_style = "1px solid #1C2735"
        elif sender == "Mr. Pranav":
            name_color = "#45A29E" # Muted Teal
            bg_color = "#121620"   # Light card fill
            border_style = "1px solid #1C2735"
        else:
            name_color = "#FF453A" # Alert Red
            bg_color = "#200A0A"
            border_style = "1px solid #FF453A"
            
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: {border_style};
                border-radius: 10px;
            }}
        """)
        
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(14, 14, 14, 14)
        bubble_layout.setSpacing(6)
        
        # Sender name label
        name_lbl = QLabel(sender.upper())
        name_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        name_lbl.setStyleSheet(f"color: {name_color}; border: none; background-color: transparent;")
        bubble_layout.addWidget(name_lbl)
        
        # Message text label
        text_lbl = QLabel(text)
        text_lbl.setWordWrap(True)
        text_lbl.setFont(QFont("Segoe UI", 11)) # 11pt = 15-16px in label font metrics
        text_lbl.setStyleSheet("color: #E1E2E6; border: none; background-color: transparent; line-height: 1.5;")
        bubble_layout.addWidget(text_lbl)
        
        # Insert bubble widget above the spacer (index count() - 1)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        # Scroll to bottom smoothly
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def safe_update_status(self, status_text: str):
        self.status_display.setText(status_text)

    def safe_add_notification(self, entry_text: str):
        timestamp = time.strftime("[%I:%M:%S %p]")
        log_line = f"<span style='color: #66FCF1;'>{timestamp}</span> {entry_text}"
        self.notif_display.append(log_line)

    def safe_update_task_status(self, text: str):
        self.task_status_lbl.setText(text)

    def safe_update_bio(self, count: int):
        self.bio_memory.setText(f"Core Sync: {count} memory links active")


_instance_lock_socket = None

def ensure_single_instance() -> bool:
    global _instance_lock_socket
    import socket
    try:
        _instance_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _instance_lock_socket.bind(('127.0.0.1', 48923))
        return True
    except OSError:
        return False

if __name__ == "__main__":
    if not ensure_single_instance():
        sys.exit(0)
    app = QApplication(sys.argv)
    gui = JarvisGUI()
    gui.show()
    sys.exit(app.exec_())