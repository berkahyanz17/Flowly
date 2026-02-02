# ui_main.py
from PySide6.QtCore import Signal, QTimer, QTime
from PySide6.QtWidgets import QMainWindow, QTabWidget, QSystemTrayIcon, QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import json
from pathlib import Path
from datetime import date

from src.ui_habits import HabitsTab
from src.ui_notes import NotesTab
from src.ui_stats import StatsTab
from src.ui_timer import TimerTab
from src.ui_calendar import CalendarTab
from src.ui_settings import SettingsTab
from src.ui_milestones import MilestonesTab
from src.ui_reports import ReportsTab
from src.ui_history import HistoryTab
from src.db import init_db
import sys
import os

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and PyInstaller.
    """
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        init_db()

        self.setWindowTitle("Flowly - Habit Tracker")
        self.setMinimumSize(900, 600)
        
        # Setup system tray for notifications
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon(resource_path("icon.png")))
            self.tray_icon.setToolTip("Flowly - Habit Tracker")
            self.tray_icon.show()
        else:
            self.tray_icon = None

        # Tabs
        self.tabs = QTabWidget()
        
        self.habits_tab = HabitsTab()
        self.notes_tab = NotesTab()
        self.stats_tab = StatsTab()
        self.timer_tab = TimerTab()
        self.calendar_tab = CalendarTab()
        self.milestones_tab = MilestonesTab()
        self.reports_tab = ReportsTab()
        self.history_tab = HistoryTab()
        self.settings_tab = SettingsTab(self)

        self.tabs.addTab(self.habits_tab, "Habits")
        self.tabs.addTab(self.notes_tab, "Notes")
        self.tabs.addTab(self.stats_tab, "Stats")
        self.tabs.addTab(self.timer_tab, "Timer")
        self.tabs.addTab(self.calendar_tab, "Calendar")
        self.tabs.addTab(self.milestones_tab, "Milestones")
        self.tabs.addTab(self.reports_tab, "Reports")
        self.tabs.addTab(self.history_tab, "History")
        self.tabs.addTab(self.settings_tab, "Settings")

        # Connect signals
        self.habits_tab.data_changed.connect(self._refresh_all)
        self.notes_tab.data_changed.connect(self._refresh_all)

        self.setCentralWidget(self.tabs)
        
        # Setup notification timer
        self._setup_notification_timer()
        
        self._refresh_all()
        
        self.setIcon()

    def setIcon(self) -> None:
        icon = QIcon(resource_path("icon.png"))
        self.setWindowIcon(icon)
    
    def _setup_notification_timer(self):
        """Setup daily notification timer"""
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self._check_notification_time)
        self.notification_timer.start(60000)  # Check every minute
    
    def _check_notification_time(self):
        """Check if it's time to show notification"""
        try:
            settings_file = Path("settings.json")
            if not settings_file.exists():
                return
            
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            if not settings.get("notifications_enabled", False):
                return
            
            # Get notification time
            notif_time = settings.get("notification_time", "09:00")
            hour, minute = map(int, notif_time.split(":"))
            
            # Get current time
            now = QTime.currentTime()
            
            # Check if it's the notification time (within the same minute)
            if now.hour() == hour and now.minute() == minute:
                self._show_daily_reminder()
        except:
            pass
    
    def _show_daily_reminder(self):
        """Show daily habit reminder notification"""
        try:
            # Check if we already showed notification today
            today = date.today().isoformat()
            last_notif_file = Path("last_notification.txt")
            
            if last_notif_file.exists():
                with open(last_notif_file, 'r') as f:
                    last_date = f.read().strip()
                    if last_date == today:
                        return  # Already showed today
            
            # Save that we showed notification today
            with open(last_notif_file, 'w') as f:
                f.write(today)
            
            # Get settings
            with open("settings.json", 'r') as f:
                settings = json.load(f)
            
            message = settings.get("notification_message", "Time to check your habits!")
            
            # Show system tray notification
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "Flowly Reminder",
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    5000
                )
            else:
                # Fallback to message box
                QMessageBox.information(
                    self,
                    "Daily Reminder",
                    message
                )
            
            # Flash window
            QApplication.alert(self, 0)
        except:
            pass

    def _refresh_all(self):
        self.habits_tab.refresh()
        self.notes_tab.refresh()
        self.stats_tab.refresh()
        self.calendar_tab.refresh()
        self.milestones_tab.refresh()
        self.reports_tab.refresh()
        self.history_tab.refresh()