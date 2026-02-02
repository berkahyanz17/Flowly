# ui_settings.py
from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QMessageBox, QFileDialog, QCheckBox, QTimeEdit, QScrollArea
)
from PySide6.QtGui import QFont, QPalette, QColor
from pathlib import Path
import json
import subprocess
import sys


class SettingsTab(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.settings_file = Path("settings.json")
        self.settings = self._load_settings()
        
        # Create container
        container = QWidget()
        
        # Header
        header = QLabel("Settings")
        font = header.font()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        
        # Theme settings
        # theme_frame = self._create_theme_settings()
        
        # Notification settings
        notif_frame = self._create_notification_settings()
        
        # Data management
        data_frame = self._create_data_management()
        
        # Container layout
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(header)
        # layout.addWidget(theme_frame)
        layout.addWidget(notif_frame)
        layout.addWidget(data_frame)
        layout.addStretch(1)
        
        container.setLayout(layout)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(container)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
    
    def _load_settings(self) -> dict:
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "theme": "default",
            "notifications_enabled": False,
            "notification_time": "09:00",
            "notification_message": "Time to check your habits! 🎯"
        }
    
    def _save_settings(self):
        """Save settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    # def _create_theme_settings(self) -> QFrame:
    #     """Create theme settings frame"""
    #     frame = QFrame()
    #     frame.setFrameShape(QFrame.StyledPanel)
        
    #     layout = QVBoxLayout()
    #     layout.setContentsMargins(16, 16, 16, 16)
    #     layout.setSpacing(12)
        
    #     title = QLabel("Appearance")
    #     font = title.font()
    #     font.setPointSize(11)
    #     font.setBold(True)
    #     title.setFont(font)
        
    #     theme_layout = QHBoxLayout()
    #     theme_label = QLabel("Theme:")
        
    #     self.theme_combo = QComboBox()
    #     self.theme_combo.addItem("Default (Follow Device)", "default")
    #     self.theme_combo.addItem("Light Mode", "light")
    #     self.theme_combo.addItem("Dark Mode", "dark")
        
    #     # Set current theme from settings
    #     current_theme = self.settings.get("theme", "default")
    #     index = self.theme_combo.findData(current_theme)
    #     if index >= 0:
    #         self.theme_combo.setCurrentIndex(index)
        
    #     self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        
    #     theme_layout.addWidget(theme_label)
    #     theme_layout.addWidget(self.theme_combo)
    #     theme_layout.addStretch(1)
        
    #     layout.addWidget(title)
    #     layout.addLayout(theme_layout)
        
    #     frame.setLayout(layout)
    #     return frame
    
    def _create_notification_settings(self) -> QFrame:
        """Create notification settings frame"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        title = QLabel("Daily Reminders")
        font = title.font()
        font.setPointSize(11)
        font.setBold(True)
        title.setFont(font)
        
        # Enable notifications
        self.notif_checkbox = QCheckBox("Enable daily habit reminders")
        self.notif_checkbox.setChecked(self.settings.get("notifications_enabled", False))
        self.notif_checkbox.stateChanged.connect(self._on_notification_toggled)
        
        # Time picker
        time_layout = QHBoxLayout()
        time_label = QLabel("Reminder time:")
        
        self.time_edit = QTimeEdit()
        saved_time = self.settings.get("notification_time", "09:00")
        hour, minute = map(int, saved_time.split(":"))
        self.time_edit.setTime(QTime(hour, minute))
        self.time_edit.timeChanged.connect(self._on_time_changed)
        
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch(1)
        
        info_label = QLabel("Note: Notifications work via Windows Task Scheduler (even when app is closed)")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        info_label.setWordWrap(True)
        
        # Task Scheduler setup button
        setup_btn = QPushButton("⚙️ Setup Windows Task Scheduler")
        setup_btn.setMinimumHeight(40)
        setup_btn.clicked.connect(self._setup_task_scheduler)
        
        setup_info = QLabel(
            "Click this button to automatically configure Windows Task Scheduler.\n"
            "This will allow notifications to work even when Flowly is closed."
        )
        setup_info.setWordWrap(True)
        setup_info.setStyleSheet("color: gray; font-size: 10px;")
        
        # Remove task button
        remove_btn = QPushButton("🗑️ Remove Task Scheduler")
        remove_btn.setMinimumHeight(40)
        remove_btn.clicked.connect(self._remove_task_scheduler)
        
        layout.addWidget(title)
        layout.addWidget(self.notif_checkbox)
        layout.addLayout(time_layout)
        layout.addWidget(info_label)
        layout.addWidget(setup_btn)
        layout.addWidget(setup_info)
        layout.addWidget(remove_btn)
        
        frame.setLayout(layout)
        return frame
    
    def _create_data_management(self) -> QFrame:
        """Create data management frame"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        title = QLabel("Data Management")
        font = title.font()
        font.setPointSize(11)
        font.setBold(True)
        title.setFont(font)
        
        export_btn = QPushButton("📤 Export Data (Backup)")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self._export_data)
        
        import_btn = QPushButton("📥 Import Data (Restore)")
        import_btn.setMinimumHeight(40)
        import_btn.clicked.connect(self._import_data)
        
        clear_btn = QPushButton("🗑️ Clear All Data")
        clear_btn.setMinimumHeight(40)
        clear_btn.clicked.connect(self._clear_all_data)
        
        layout.addWidget(title)
        layout.addWidget(export_btn)
        layout.addWidget(import_btn)
        layout.addWidget(clear_btn)
        
        frame.setLayout(layout)
        return frame
    
    # def _on_theme_changed(self, index):
    #     """Handle theme change"""
    #     theme = self.theme_combo.currentData()
    #     self.settings["theme"] = theme
    #     self._save_settings()
    #     self._apply_theme(theme)
    
    # def _apply_theme(self, theme: str):
    #     """Apply the selected theme"""
    #     from PySide6.QtWidgets import QApplication
    #     app = QApplication.instance()
        
    #     if theme == "light":
    #         # Light mode
    #         palette = QPalette()
    #         palette.setColor(QPalette.Window, QColor(255, 255, 255))
    #         palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    #         palette.setColor(QPalette.Base, QColor(240, 240, 240))
    #         palette.setColor(QPalette.AlternateBase, QColor(250, 250, 250))
    #         palette.setColor(QPalette.Text, QColor(0, 0, 0))
    #         palette.setColor(QPalette.Button, QColor(240, 240, 240))
    #         palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    #         app.setPalette(palette)
    #     elif theme == "dark":
    #         # Dark mode
    #         palette = QPalette()
    #         palette.setColor(QPalette.Window, QColor(13, 17, 23))
    #         palette.setColor(QPalette.WindowText, QColor(230, 237, 243))
    #         palette.setColor(QPalette.Base, QColor(22, 27, 34))
    #         palette.setColor(QPalette.AlternateBase, QColor(33, 38, 45))
    #         palette.setColor(QPalette.Text, QColor(230, 237, 243))
    #         palette.setColor(QPalette.Button, QColor(33, 38, 45))
    #         palette.setColor(QPalette.ButtonText, QColor(230, 237, 243))
    #         app.setPalette(palette)
    #     else:
    #         # Default - use system theme
    #         app.setPalette(app.style().standardPalette())
        
    #     # Refresh all tabs to update colors
    #     self.parent_window._refresh_all()
    
    def _on_notification_toggled(self, state):
        """Handle notification toggle"""
        self.settings["notifications_enabled"] = (state == Qt.Checked)
        self._save_settings()
    
    def _on_time_changed(self, time):
        """Handle notification time change"""
        self.settings["notification_time"] = time.toString("HH:mm")
        self._save_settings()
    
    def _setup_task_scheduler(self):
        """Setup Windows Task Scheduler for notifications"""
        # Get notification time
        notif_time = self.settings.get("notification_time", "09:00")
        hour, minute = notif_time.split(":")
        
        # Get paths
        python_exe = sys.executable
        script_path = Path(__file__).parent / "notify.py"
        
        if not script_path.exists():
            QMessageBox.warning(
                self,
                "Script Not Found",
                f"Could not find notify.py at:\n{script_path}\n\n"
                "Make sure notify.py is in the same folder as the app."
            )
            return
        
        # Create Task Scheduler XML
        task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Daily notification for Flowly habit tracker</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-01-01T{hour}:{minute}:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{python_exe}"</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{script_path.parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
        
        # Save XML to temp file
        temp_xml = Path.home() / "flowly_task.xml"
        with open(temp_xml, 'w', encoding='utf-16') as f:
            f.write(task_xml)
        
        try:
            # Create task using schtasks command
            result = subprocess.run(
                [
                    "schtasks",
                    "/Create",
                    "/TN", "FlowlyDailyReminder",
                    "/XML", str(temp_xml),
                    "/F"  # Force overwrite if exists
                ],
                capture_output=True,
                text=True
            )
            
            # Clean up temp file
            temp_xml.unlink()
            
            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "Success!",
                    f"Windows Task Scheduler has been configured!\n\n"
                    f"You will receive a daily notification at {notif_time}.\n\n"
                    f"The notification will work even when Flowly is closed.\n\n"
                    f"To modify or remove the task, open 'Task Scheduler' from Windows."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Setup Failed",
                    f"Failed to create scheduled task.\n\n"
                    f"Error: {result.stderr}\n\n"
                    f"Try running the app as Administrator."
                )
        
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to setup Task Scheduler:\n{str(e)}\n\n"
                f"You may need to run the app as Administrator."
            )
    
    def _remove_task_scheduler(self):
        """Remove Flowly task from Windows Task Scheduler"""
        reply = QMessageBox.question(
            self,
            "Remove Scheduled Task?",
            "This will remove the daily notification from Windows Task Scheduler.\n\n"
            "You will no longer receive notifications when the app is closed.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                result = subprocess.run(
                    ["schtasks", "/Delete", "/TN", "FlowlyDailyReminder", "/F"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    QMessageBox.information(
                        self,
                        "Removed",
                        "Task Scheduler entry has been removed successfully."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Not Found",
                        "No scheduled task found to remove."
                    )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to remove task:\n{str(e)}"
                )
    
    def _export_data(self):
        """Export database to file"""
        import shutil
        from db import DB_PATH
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            str(Path.home() / "flowly_backup.sqlite3"),
            "SQLite Database (*.sqlite3)"
        )
        
        if file_path:
            try:
                shutil.copy(DB_PATH, file_path)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Data exported successfully to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    f"Failed to export data:\n{str(e)}"
                )
    
    def _import_data(self):
        """Import database from file"""
        import shutil
        from db import DB_PATH
        
        reply = QMessageBox.question(
            self,
            "Import Data",
            "Warning: Importing data will replace all current data.\n\n"
            "Do you want to create a backup first?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Cancel:
            return
        
        if reply == QMessageBox.Yes:
            self._export_data()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            str(Path.home()),
            "SQLite Database (*.sqlite3)"
        )
        
        if file_path:
            try:
                shutil.copy(file_path, DB_PATH)
                QMessageBox.information(
                    self,
                    "Import Successful",
                    "Data imported successfully!\n\nThe app will now refresh."
                )
                self.parent_window._refresh_all()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    f"Failed to import data:\n{str(e)}"
                )
    
    def _clear_all_data(self):
        """Clear all data from database"""
        reply = QMessageBox.warning(
            self,
            "Clear All Data",
            "Are you SURE you want to delete ALL data?\n\n"
            "This action cannot be undone!\n\n"
            "Consider exporting a backup first.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            reply2 = QMessageBox.warning(
                self,
                "Final Confirmation",
                "This is your last chance!\n\n"
                "Delete ALL habits, logs, notes, and Pomodoro sessions?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply2 == QMessageBox.Yes:
                try:
                    from db import get_conn
                    conn = get_conn()
                    conn.execute("DELETE FROM habit_logs;")
                    conn.execute("DELETE FROM notes;")
                    conn.execute("DELETE FROM habits;")
                    
                    table_check = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='pomodoro_sessions';"
                    ).fetchone()
                    
                    if table_check:
                        conn.execute("DELETE FROM pomodoro_sessions;")
                    
                    conn.commit()
                    conn.close()
                    
                    QMessageBox.information(
                        self,
                        "Data Cleared",
                        "All data has been deleted successfully."
                    )
                    self.parent_window._refresh_all()
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Failed to clear data:\n{str(e)}"
                    )