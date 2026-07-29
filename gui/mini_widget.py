import os
import sys
import math
import random
from PyQt5.QtWidgets import QWidget, QMenu, QApplication
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient, QLinearGradient, QPolygonF
from PyQt5.QtCore import Qt, QTimer, QPoint, QPointF, pyqtSignal, QRectF, QVariantAnimation, QEasingCurve, QSize

class JarvisMiniWidget(QWidget):
    """
    Holographic, transparent, always-on-top glassmorphic widget.
    - Utilizes a static window footprint (270x165) to eliminate OS-level window shift mouse hover glitches.
    - Draws a dynamically animating glass capsule inside the static boundary.
    """
    state_changed = pyqtSignal(str) # 'idle', 'listening', 'thinking', 'speaking'

    def __init__(self, main_gui=None):
        super().__init__()
        self.main_gui = main_gui
        self.init_widget()

    def init_widget(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # State Variables
        self.current_state = 'idle'
        self.layout_type = 'collapsed'  # 'collapsed', 'header_only', 'expanded'
        
        # Window Dimensions (Static Footprint)
        self.win_w = 270
        self.win_h = 165
        
        # Internally Animated Dimensions
        self.current_w = 48
        self.current_h = 48
        
        self.setFixedSize(self.win_w, self.win_h)
        
        # Position centered top-middle
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.win_w) // 2, 20)

        # Animations
        self.rotation_angle = 0
        self.pulse_val = 0.5
        self.pulse_dir = 1
        
        # Audio wave lines
        self.audio_amplitude = [0.1] * 8
        self.wave_phase = 0.0

        # Rich Card Data state
        self.card_type = 'chat'
        self.card_data = {}
        
        # Collapse timers
        self.auto_collapse_timer = QTimer(self)
        self.auto_collapse_timer.singleShot = True
        self.auto_collapse_timer.timeout.connect(self.collapse_widget)

        self.hover_collapse_timer = QTimer(self)
        self.hover_collapse_timer.setSingleShot(True)
        self.hover_collapse_timer.timeout.connect(self.do_hover_collapse)

        # Dragging variables
        self.drag_position = QPoint()

        # Animation timer (~30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animations)
        self.timer.start(33)

        self.state_changed.connect(self.set_state)

    def set_state(self, new_state):
        self.current_state = new_state
        if new_state in ['listening', 'thinking', 'speaking']:
            if self.layout_type != 'expanded':
                self.set_widget_layout('header_only')
        else: # 'idle'
            if self.layout_type == 'header_only':
                self.set_widget_layout('collapsed')
        self.update()

    def set_widget_layout(self, layout_type):
        self.layout_type = layout_type
        
        target_w = 48
        target_h = 48
        
        if layout_type == 'header_only':
            target_w = 270
            target_h = 48
        elif layout_type == 'expanded':
            target_w = 270
            target_h = 165
            
        self.animate_to_layout(target_w, target_h)

    def animate_to_layout(self, target_w, target_h):
        if hasattr(self, "size_anim") and self.size_anim:
            self.size_anim.stop()

        self.size_anim = QVariantAnimation(self)
        self.size_anim.setDuration(350)
        self.size_anim.setStartValue(QPoint(self.current_w, self.current_h))
        self.size_anim.setEndValue(QPoint(target_w, target_h))
        self.size_anim.setEasingCurve(QEasingCurve.OutCubic)

        def on_value_changed(val):
            self.current_w = val.x()
            self.current_h = val.y()
            self.update()

        self.size_anim.valueChanged.connect(on_value_changed)
        self.size_anim.start()

    def collapse_widget(self):
        if self.current_state in ['listening', 'thinking', 'speaking']:
            self.set_widget_layout('header_only')
        else:
            self.set_widget_layout('collapsed')

    def show_info_card(self, card_type, data):
        self.card_type = card_type
        self.card_data = data
        self.set_widget_layout('expanded')
        self.auto_collapse_timer.start(8000)

    def update_animations(self):
        if self.current_state == 'listening':
            self.rotation_angle = (self.rotation_angle + 8) % 360
        elif self.current_state == 'thinking':
            self.rotation_angle = (self.rotation_angle + 16) % 360
        else:
            self.rotation_angle = (self.rotation_angle + 2) % 360

        pulse_speed = 0.08 if self.current_state == 'listening' else 0.04
        self.pulse_val += pulse_speed * self.pulse_dir
        if self.pulse_val >= 1.0:
            self.pulse_val = 1.0
            self.pulse_dir = -1
        elif self.pulse_val <= 0.3:
            self.pulse_val = 0.3
            self.pulse_dir = 1

        if self.current_state == 'speaking':
            self.wave_phase += 0.35
            for i in range(len(self.audio_amplitude)):
                self.audio_amplitude[i] = 0.15 + 0.7 * abs(math.sin(self.wave_phase + i * 0.9))
        else:
            for i in range(len(self.audio_amplitude)):
                self.audio_amplitude[i] = max(0.08, self.audio_amplitude[i] - 0.08)

        self.update()

    def enterEvent(self, event):
        self.hover_collapse_timer.stop()
        if self.layout_type == 'collapsed':
            self.set_widget_layout('header_only')
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.layout_type == 'header_only' and self.current_state == 'idle':
            self.hover_collapse_timer.start(350)
        super().leaveEvent(event)

    def do_hover_collapse(self):
        # Double check if cursor is actually outside the active area before collapsing
        if self.layout_type == 'header_only' and self.current_state == 'idle':
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            rx = (self.win_w - self.current_w) // 2
            active_rect = QRectF(rx, 2, self.current_w, self.current_h)
            if not active_rect.contains(cursor_pos):
                self.set_widget_layout('collapsed')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Coordinates of the animating active container inside static window boundaries
        rx = (self.win_w - self.current_w) / 2
        ry = 2
        rw = self.current_w
        rh = self.current_h

        if self.current_w <= 54:
            # === DRAW COLLAPSED PILL (CENTERED ORB) ===
            self.draw_holographic_orb(painter, self.win_w / 2, 24, 18)
        else:
            # === DRAW EXPANDED HUD CAPSULE / CARD ===
            bg_color = QColor(8, 11, 16, 242)
            
            if self.current_state == 'listening':
                border_pen = QPen(QColor(0, 240, 255, 180))
                border_pen.setWidthF(1.8)
            else:
                border_pen = QPen(QColor(0, 240, 255, 60))
                border_pen.setWidthF(1.0)
                
            painter.setPen(border_pen)
            painter.setBrush(QBrush(bg_color))
            
            radius_val = 16 if self.layout_type == 'expanded' else 12
            painter.drawRoundedRect(QRectF(rx, ry, rw, rh), radius_val, radius_val)

            # Draw core logo on the left of the active container
            self.draw_holographic_orb(painter, rx + 24, 24, 12)

            # Draw Mic status pill on the right of the active container (fade-in as width grows)
            if self.current_w > 180:
                opacity = min(1.0, (self.current_w - 180) / 90.0)
                painter.setOpacity(opacity)
                self.draw_top_right_controls(painter, rx + rw)
                painter.setOpacity(1.0)

            # Draw card contents inside container (only when layout height has expanded)
            if self.layout_type == 'expanded' and self.current_h > 100:
                painter.save()
                # Clip drawing inside the active container area
                painter.setClipRect(QRectF(rx + 4, ry + 48, rw - 8, rh - 52))
                
                # Offset card drawing to align with rx
                painter.translate(rx, 0)
                
                if self.card_type == 'stock':
                    self.draw_stock_card(painter)
                elif self.card_type == 'weather':
                    self.draw_weather_card(painter)
                elif self.card_type == 'chat':
                    self.draw_chat_card(painter)
                else:
                    self.draw_telemetry_card(painter)
                painter.restore()

    def draw_holographic_orb(self, painter, cx, cy, radius):
        # Speaking Audio Waveform (Inside collapsed circle)
        if self.current_state == 'speaking' and self.current_w <= 54:
            pen_wave = QPen(QColor(0, 240, 255, 220))
            pen_wave.setWidthF(1.5)
            painter.setPen(pen_wave)
            bar_w = 2
            spacing = 2
            mini_amplitudes = self.audio_amplitude[:4]
            start_x = int(cx - (len(mini_amplitudes) * (bar_w + spacing)) / 2)
            
            for i, amp in enumerate(mini_amplitudes):
                h = int(amp * (radius * 1.4))
                h = max(2, h)
                bx = start_x + i * (bar_w + spacing)
                by = int(cy - h / 2)
                painter.drawLine(bx, by, bx, by + h)
            return

        pulse_alpha = int(self.pulse_val * 255)
        ring_color = QColor(0, 240, 255, int(pulse_alpha * 0.5))

        pen_outer = QPen(ring_color)
        pen_outer.setWidthF(1.2)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius + 4, radius + 4)

        # Segmented rotating outer dial
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation_angle)
        
        pen_seg = QPen()
        pen_seg.setWidthF(3.0 if self.current_state in ['listening', 'speaking'] else 2.0)
        
        colors = [
            QColor(0, 240, 255, 220),
            QColor(0, 150, 255, 200),
            QColor(0, 240, 255, 220),
            QColor(0, 100, 230, 180)
        ]
        for i in range(4):
            pen_seg.setColor(colors[i])
            painter.setPen(pen_seg)
            arc_len = 80 if self.current_state in ['listening', 'speaking'] else 40
            painter.drawArc(-radius, -radius, radius * 2, radius * 2, i * 90 * 16, arc_len * 16)
        painter.restore()

        # Inner solid glowing core
        core_grad = QRadialGradient(cx, cy, radius - 4)
        if self.current_state == 'listening':
            core_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
            core_grad.setColorAt(0.6, QColor(0, 240, 255, 200))
        elif self.current_state == 'thinking':
            core_grad.setColorAt(0.0, QColor(0, 240, 255, 255))
            core_grad.setColorAt(1.0, QColor(0, 80, 200, 100))
        else:
            core_grad.setColorAt(0.0, QColor(0, 240, 255, int(130 + self.pulse_val * 125)))
            core_grad.setColorAt(1.0, QColor(0, 50, 100, 40))

        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius - 3, radius - 3)

        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.drawEllipse(QPointF(cx, cy), 2, 2)

    def draw_top_right_controls(self, painter, container_right_x):
        # Positions relative to the growing container bounds
        pill_rect = QRectF(container_right_x - 85, 12, 70, 24)
        
        is_mic_active = self.main_gui.mic_active if (self.main_gui and hasattr(self.main_gui, 'mic_active')) else False
        
        if is_mic_active:
            painter.setBrush(QBrush(QColor(0, 240, 255, 45)))
            painter.setPen(QPen(QColor(0, 240, 255, 160)))
        else:
            painter.setBrush(QBrush(QColor(16, 22, 32, 180)))
            painter.setPen(QPen(QColor(0, 240, 255, 45)))
            
        painter.drawRoundedRect(pill_rect, 12, 12)

        pen_wave = QPen(QColor(0, 240, 255, 220))
        pen_wave.setWidthF(1.5)
        painter.setPen(pen_wave)
        
        start_x = container_right_x - 74
        cy = 24
        
        for i in range(5):
            amp = self.audio_amplitude[i] if self.current_state == 'speaking' else (0.15 + 0.3 * abs(math.sin(self.rotation_angle * 0.05 + i * 0.7)))
            if self.current_state == 'listening':
                amp = 0.4 + 0.6 * abs(math.sin(self.rotation_angle * 0.1 + i * 0.9))
            h = int(amp * 12)
            painter.drawLine(int(start_x + i * 4), int(cy - h/2), int(start_x + i * 4), int(cy + h/2))

        mic_color = QColor(0, 240, 255, 255) if is_mic_active else QColor(0, 240, 255, 140)
        painter.setPen(QPen(mic_color))
        painter.setBrush(QBrush(mic_color))
        painter.drawEllipse(int(container_right_x - 29), 20, 4, 6)
        painter.drawLine(int(container_right_x - 27), 26, int(container_right_x - 27), 28)

    def draw_stock_card(self, painter):
        # Drawn relative to the translated origin (rx, 0)
        name = self.card_data.get("name", "GROWW STOCK")
        price = self.card_data.get("price", "₹ 0.00")
        change = self.card_data.get("change", "0.00")
        percent = self.card_data.get("percent", "0.00%")
        is_up = not change.startswith("-")

        painter.setPen(QPen(QColor(255, 255, 255, 240)))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(16, 60, name)

        painter.setPen(QPen(QColor(138, 143, 152, 200)))
        painter.setFont(QFont("Segoe UI", 7))
        painter.drawText(16, 74, "Billionbrains Garage Ticker")

        painter.setPen(QPen(QColor(255, 255, 255, 255)))
        painter.setFont(QFont("Courier New", 18, QFont.Bold))
        painter.drawText(16, 108, price)

        stat_color = QColor(10, 192, 116) if is_up else QColor(255, 82, 82)
        painter.setPen(QPen(stat_color))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        stat_text = f"{change} ({percent})"
        painter.drawText(16, 124, stat_text)

        pen_chart = QPen(stat_color)
        pen_chart.setWidthF(1.8)
        painter.setPen(pen_chart)
        
        pts = self.card_data.get("sparkline", [50, 45, 60, 55, 75, 70, 95])
        start_x = 135
        end_x = 270 - 16
        step_x = (end_x - start_x) / (len(pts) - 1)
        
        chart_poly = QPolygonF()
        for i, val in enumerate(pts):
            cx = start_x + i * step_x
            cy = 135 - (val / 100.0) * 45
            chart_poly.append(QPointF(cx, cy))
            
        painter.drawPolyline(chart_poly)

        painter.save()
        grad = QLinearGradient(start_x, 80, start_x, 135)
        grad.setColorAt(0.0, QColor(stat_color.red(), stat_color.green(), stat_color.blue(), 45))
        grad.setColorAt(1.0, QColor(stat_color.red(), stat_color.green(), stat_color.blue(), 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        chart_poly.append(QPointF(end_x, 135))
        chart_poly.append(QPointF(start_x, 135))
        painter.drawPolygon(chart_poly)
        painter.restore()

        painter.setPen(QPen(QColor(138, 143, 152, 160)))
        painter.setFont(QFont("Segoe UI", 7))
        painter.drawText(270 - 80, 74, "updated 2m ago")

    def draw_weather_card(self, painter):
        temp = self.card_data.get("temp", "24°C")
        loc = self.card_data.get("location", "GUNTUR")
        desc = self.card_data.get("desc", "Partly Cloudy")
        humidity = self.card_data.get("humidity", "Humidity: 65%")
        wind = self.card_data.get("wind", "Wind: 12 km/h")

        painter.setPen(QPen(QColor(255, 255, 255, 240)))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(16, 62, loc)

        painter.setPen(QPen(QColor(138, 143, 152, 200)))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(16, 78, desc)

        painter.setPen(QPen(QColor(0, 240, 255, 255)))
        painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
        painter.drawText(16, 124, temp)

        painter.setPen(QPen(QColor(138, 143, 152, 200)))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(140, 100, humidity)
        painter.drawText(140, 116, wind)

        painter.setBrush(QBrush(QColor(0, 240, 255, 25)))
        painter.setPen(QPen(QColor(0, 240, 255, 80)))
        painter.drawEllipse(270 - 55, 88, 38, 38)
        painter.setPen(QPen(QColor(255, 255, 255, 220)))
        painter.setFont(QFont("Segoe UI Emoji", 14))
        painter.drawText(270 - 48, 114, "⛅")

    def draw_telemetry_card(self, painter):
        cpu = self.card_data.get("cpu", "CPU: 12%")
        ram = self.card_data.get("ram", "RAM: 38%")
        gpu = self.card_data.get("gpu", "iGPU: Bloom Active")
        battery = self.card_data.get("battery", "Battery: 100%")

        painter.setPen(QPen(QColor(0, 240, 255, 200)))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(16, 56, "J.A.R.V.I.S. // TELEMETRY")

        painter.setPen(QPen(QColor(255, 255, 255, 230)))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        
        painter.drawText(16, 78, cpu)
        painter.drawText(16, 98, ram)
        painter.drawText(16, 118, gpu)
        painter.drawText(16, 138, battery)

        painter.setPen(Qt.NoPen)
        for i, val_pct in enumerate([18, 42, 60, 100]):
            bar_y = 70 + (i * 20)
            painter.setBrush(QBrush(QColor(16, 22, 32, 255)))
            painter.drawRoundedRect(QRectF(150, bar_y, 100, 5), 2, 2)
            painter.setBrush(QBrush(QColor(0, 240, 255, 200)))
            painter.drawRoundedRect(QRectF(150, bar_y, int(val_pct), 5), 2, 2)

    def draw_chat_card(self, painter):
        text = self.card_data.get("reply", "")
        painter.setPen(QPen(QColor(255, 255, 255, 240)))
        painter.setFont(QFont("Segoe UI", 9))
        
        painter.setPen(QPen(QColor(0, 240, 255, 200)))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(16, 56, "J.A.R.V.I.S. RESPONSE")

        painter.setPen(QPen(QColor(255, 255, 255, 240)))
        painter.setFont(QFont("Segoe UI", 9))
        rect = QRectF(16, 68, 270 - 32, 85)
        painter.drawText(rect, Qt.TextWordWrap, text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            click_x = event.pos().x()
            click_y = event.pos().y()
            
            rx = (self.win_w - self.current_w) // 2
            
            # 1. Hit-detection for top-right soundwave mic pill inside active capsule
            pill_x = rx + self.current_w - 85
            pill_w = 70
            pill_y = 12
            pill_h = 24
            
            if self.layout_type in ['header_only', 'expanded'] and (pill_x <= click_x <= pill_x + pill_w) and (pill_y <= click_y <= pill_y + pill_h):
                if self.main_gui:
                    self.main_gui.toggle_microphone()
                event.accept()
                return

            # Check if clicked inside active capsule bounds to allow dragging
            active_rect = QRectF(rx, 2, self.current_w, self.current_h)
            if active_rect.contains(event.pos()):
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            else:
                event.ignore()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            rx = (self.win_w - self.current_w) // 2
            active_rect = QRectF(rx, 2, self.current_w, self.current_h)
            if active_rect.contains(event.pos()):
                if self.main_gui:
                    self.main_gui.showMaximized()
                    self.main_gui.activateWindow()
                event.accept()

    def contextMenuEvent(self, event):
        rx = (self.win_w - self.current_w) // 2
        active_rect = QRectF(rx, 2, self.current_w, self.current_h)
        if not active_rect.contains(event.pos()):
            event.ignore()
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0C0F15;
                color: #00f0ff;
                border: 1px solid #1C2735;
                border-radius: 6px;
                font-family: 'Segoe UI';
                font-size: 11px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: rgba(0, 240, 255, 0.2);
                border-radius: 4px;
                color: #ffffff;
            }
        """)

        action_mic = menu.addAction("🎙️ Toggle Microphone")
        action_orb = menu.addAction("🌌 Open 3D Holographic Orb")
        action_show = menu.addAction("🖥️ Restore Command Center")
        menu.addSeparator()
        action_exit = menu.addAction("❌ Shutdown System")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == action_mic:
            if self.main_gui:
                self.main_gui.toggle_microphone()
        elif action == action_orb:
            from gui.orb_window import start_orb_thread
            start_orb_thread()
        elif action == action_show:
            if self.main_gui:
                self.main_gui.showMaximized()
                self.main_gui.activateWindow()
        elif action == action_exit:
            if self.main_gui:
                self.main_gui.execute_actual_shutdown()
            else:
                QApplication.instance().quit()
