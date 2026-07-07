import sys
import hashlib
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class JarvisSecurityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SECURITY MAINFRAME AUTHORIZATION")
        self.setFixedSize(380, 200)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #0C0F15;
                border: 1px solid #1C2735;
                border-radius: 8px;
            }
            QLabel {
                font-family: 'Segoe UI', Arial;
                color: #E1E2E6;
            }
            QLineEdit {
                background-color: #121620;
                border: 1px solid #1C2735;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #007AFF;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                border: none;
            }
            QPushButton:hover {
                background-color: #66FCF1;
                color: #07090D;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        self.title_lbl = QLabel("ENTER Mr. PRANAV AUTHORIZATION CODE:")
        self.title_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.title_lbl.setStyleSheet("color: #66FCF1; border: none;")
        layout.addWidget(self.title_lbl)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter passcode parameter...")
        self.password_input.returnPressed.connect(self.check_password)
        layout.addWidget(self.password_input)
        
        self.error_lbl = QLabel("")
        self.error_lbl.setFont(QFont("Segoe UI", 8))
        self.error_lbl.setStyleSheet("color: #FF453A; border: none;")
        layout.addWidget(self.error_lbl)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.auth_btn = QPushButton("AUTHORIZE")
        self.auth_btn.setFixedWidth(120)
        self.auth_btn.clicked.connect(self.check_password)
        btn_layout.addWidget(self.auth_btn)
        
        layout.addLayout(btn_layout)
        
        self.attempts = 3
        self.authorized = False
        self.stored_hash = hashlib.sha256("20123".encode()).hexdigest()

    def check_password(self):
        entered = self.password_input.text()
        entered_hash = hashlib.sha256(entered.encode()).hexdigest()
        
        if entered_hash == self.stored_hash:
            self.authorized = True
            self.accept()
        else:
            self.attempts -= 1
            self.password_input.clear()
            if self.attempts <= 0:
                self.error_lbl.setText("CRITICAL: Unauthorized access. System locked.")
                self.auth_btn.setEnabled(False)
                self.reject()
            else:
                self.error_lbl.setText(f"Authentication Failed. Attempts left: {self.attempts}")

def verify_access() -> bool:
    """
    The master security gate for J.A.R.V.I.S.
    Displays a secure PyQt5 dialog window and blocks boot until authorized.
    """
    import datetime
    import threading
    from senses.tts_engine import speak
    
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning Sir. Welcome back. Please enter the Access code."
    elif 12 <= hour < 16:
        greeting = "Good afternoon Sir. Welcome back. Please enter the Access code."
    else:
        greeting = "Good evening Sir. Welcome back. Please enter the Access code."
        
    # Play the greeting on a separate thread so it doesn't block dialog execution
    threading.Thread(target=speak, args=(greeting,), daemon=True).start()
    
    dialog = JarvisSecurityDialog()
    if dialog.exec_() == QDialog.Accepted and dialog.authorized:
        return True
    else:
        sys.exit(0)