# ui_timer.py
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QFrame, QSizePolicy, QApplication, QMessageBox, QSystemTrayIcon
)
from PySide6.QtGui import QFont, QPalette, QIcon


class TimerTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Timer state
        self.is_running = False
        self.is_work_session = True  # True = work, False = break
        self.time_remaining = 25 * 60  # seconds
        self.work_duration = 25  # minutes
        self.break_duration = 5  # minutes
        self.sessions_completed = 0
        
        # System tray icon for notifications
        self.tray_icon = None
        self._setup_tray_icon()
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        
        # UI Setup
        self._setup_ui()
        self._update_display()
    
    def _setup_tray_icon(self):
        """Setup system tray icon for notifications"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            # Use app icon or create a simple one
            icon = QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_MessageBoxInformation)
            self.tray_icon.setIcon(icon)
            self.tray_icon.setToolTip("Pomodoro Timer")
            self.tray_icon.show()
    
    def _setup_ui(self):
        # Header
        header = QLabel("Pomodoro Timer")
        font = header.font()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        
        # Session indicator
        self.session_label = QLabel("Work Session")
        font = self.session_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.session_label.setFont(font)
        self.session_label.setAlignment(Qt.AlignCenter)
        
        # Timer display
        self.time_display = QLabel("25:00")
        font = self.time_display.font()
        font.setPointSize(72)
        font.setBold(True)
        self.time_display.setFont(font)
        self.time_display.setAlignment(Qt.AlignCenter)
        
        # Control buttons
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self._toggle_timer)
        self.start_btn.setMinimumHeight(50)
        font = self.start_btn.font()
        font.setPointSize(14)
        font.setBold(True)
        self.start_btn.setFont(font)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_timer)
        self.reset_btn.setMinimumHeight(50)
        
        self.skip_btn = QPushButton("Skip Session")
        self.skip_btn.clicked.connect(self._skip_session)
        self.skip_btn.setMinimumHeight(40)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addWidget(self.start_btn, 2)
        btn_layout.addWidget(self.reset_btn, 1)
        
        # Settings frame
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.StyledPanel)
        
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(16, 16, 16, 16)
        settings_layout.setSpacing(12)
        
        settings_title = QLabel("Settings")
        font = settings_title.font()
        font.setPointSize(11)
        font.setBold(True)
        settings_title.setFont(font)
        
        # Work duration setting
        work_layout = QHBoxLayout()
        work_label = QLabel("Work Duration:")
        self.work_spin = QSpinBox()
        self.work_spin.setMinimum(1)
        self.work_spin.setMaximum(60)
        self.work_spin.setValue(25)
        self.work_spin.setSuffix(" min")
        self.work_spin.valueChanged.connect(self._update_work_duration)
        work_layout.addWidget(work_label)
        work_layout.addStretch(1)
        work_layout.addWidget(self.work_spin)
        
        # Break duration setting
        break_layout = QHBoxLayout()
        break_label = QLabel("Break Duration:")
        self.break_spin = QSpinBox()
        self.break_spin.setMinimum(1)
        self.break_spin.setMaximum(30)
        self.break_spin.setValue(5)
        self.break_spin.setSuffix(" min")
        self.break_spin.valueChanged.connect(self._update_break_duration)
        break_layout.addWidget(break_label)
        break_layout.addStretch(1)
        break_layout.addWidget(self.break_spin)
        
        settings_layout.addWidget(settings_title)
        settings_layout.addLayout(work_layout)
        settings_layout.addLayout(break_layout)
        settings_frame.setLayout(settings_layout)
        
        # Sessions completed
        self.sessions_label = QLabel("Sessions completed: 0")
        self.sessions_label.setAlignment(Qt.AlignCenter)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        layout.addWidget(header)
        layout.addStretch(1)
        layout.addWidget(self.session_label)
        layout.addWidget(self.time_display)
        layout.addStretch(1)
        layout.addLayout(btn_layout)
        layout.addWidget(self.skip_btn)
        layout.addWidget(self.sessions_label)
        layout.addSpacing(20)
        layout.addWidget(settings_frame)
        layout.addStretch(2)
        
        self.setLayout(layout)
    
    def _is_dark_mode(self) -> bool:
        """Check if system is in dark mode"""
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        return bg_color.lightness() < 128
    
    def _update_display(self):
        """Update timer display and colors"""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.time_display.setText(f"{minutes:02d}:{seconds:02d}")
        
        # Update session label and color
        if self.is_work_session:
            self.session_label.setText("🎯 Work Session")
            if self._is_dark_mode():
                self.time_display.setStyleSheet("color: #39d353;")  # Green
            else:
                self.time_display.setStyleSheet("color: #30a14e;")  # Dark green
        else:
            self.session_label.setText("☕ Break Time")
            if self._is_dark_mode():
                self.time_display.setStyleSheet("color: #58a6ff;")  # Blue
            else:
                self.time_display.setStyleSheet("color: #0969da;")  # Dark blue
    
    def _tick(self):
        """Called every second when timer is running"""
        self.time_remaining -= 1
        self._update_display()
        
        if self.time_remaining <= 0:
            self._timer_finished()
    
    # In ui_timer.py, update the _log_pomodoro_session method:

    def _log_pomodoro_session(self, session_type: str, duration: int):
        """Log completed pomodoro session to database"""
        from db import get_conn, get_current_datetime
        conn = get_conn()
        
        # Ensure table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                duration INTEGER NOT NULL,
                completed_at TEXT NOT NULL
            );
        """)
        
        # Insert session with device datetime
        conn.execute(
            "INSERT INTO pomodoro_sessions (session_type, duration, completed_at) VALUES (?, ?, ?);",
            (session_type, duration, get_current_datetime())
        )
        conn.commit()
        conn.close()
    
    def _timer_finished(self):
        """Called when timer reaches 0"""
        self.timer.stop()
        self.is_running = False
        self.start_btn.setText("Start")
        
        # Play alert sound
        self._play_alert()
        
        # Switch session type
        if self.is_work_session:
            # Log completed work session
            self._log_pomodoro_session('work', self.work_duration)
            
            self.sessions_completed += 1
            self.sessions_label.setText(f"Sessions completed: {self.sessions_completed}")
            self.is_work_session = False
            self.time_remaining = self.break_duration * 60
            self._show_notification(
                "Work Complete! ✅",
                "Great job! Time for a well-deserved break! ☕"
            )
        else:
            # Log completed break session
            self._log_pomodoro_session('break', self.break_duration)
            
            self.is_work_session = True
            self.time_remaining = self.work_duration * 60
            self._show_notification(
                "Break Over! 🎯",
                "Break time is over! Ready to get back to work?"
            )
        
        self._update_display()
        
        # Flash window in taskbar
        self._flash_window()
    
    def _toggle_timer(self):
        """Start or pause the timer"""
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText("Resume")
        else:
            self.timer.start(1000)  # 1 second interval
            self.is_running = True
            self.start_btn.setText("Pause")
    
    def _reset_timer(self):
        """Reset timer to current session's default duration"""
        self.timer.stop()
        self.is_running = False
        self.start_btn.setText("Start")
        
        if self.is_work_session:
            self.time_remaining = self.work_duration * 60
        else:
            self.time_remaining = self.break_duration * 60
        
        self._update_display()
    
    def _skip_session(self):
        """Skip to next session"""
        self.timer.stop()
        self.is_running = False
        self.start_btn.setText("Start")
        
        if self.is_work_session:
            self.is_work_session = False
            self.time_remaining = self.break_duration * 60
        else:
            self.is_work_session = True
            self.time_remaining = self.work_duration * 60
        
        self._update_display()
    
    def _update_work_duration(self, value):
        """Update work duration setting"""
        self.work_duration = value
        if self.is_work_session and not self.is_running:
            self.time_remaining = self.work_duration * 60
            self._update_display()
    
    def _update_break_duration(self, value):
        """Update break duration setting"""
        self.break_duration = value
        if not self.is_work_session and not self.is_running:
            self.time_remaining = self.break_duration * 60
            self._update_display()
    
    def _play_alert(self):
        """Play alert sound when timer finishes"""
        try:
            QApplication.beep()
        except:
            pass
    
    def _show_notification(self, title, message):
        """Show system tray notification"""
        if self.tray_icon and self.tray_icon.isSystemTrayAvailable():
            # Show tray notification with sound
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                5000  # Show for 5 seconds
            )
        else:
            # Fallback to message box
            msg = QMessageBox(self)
            msg.setWindowTitle(title)
            msg.setText(message)
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.show()
    
    def _flash_window(self):
        """Flash the window in the taskbar to get attention"""
        try:
            window = self.window()
            if window:
                QApplication.alert(window, 0)  # Flash indefinitely until focused
        except:
            pass