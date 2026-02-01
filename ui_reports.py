# ui_reports.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont, QPalette
from models import list_habits, get_done_days_in_range, current_streak
from datetime import date, timedelta
from pathlib import Path


class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create container
        container = QWidget()
        
        # Header
        header = QLabel("Progress Reports")
        font = header.font()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        
        # Report type selector
        type_layout = QHBoxLayout()
        type_label = QLabel("Report Type:")
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("Weekly Summary", "weekly")
        self.type_combo.addItem("Monthly Summary", "monthly")
        self.type_combo.addItem("All-Time Summary", "all_time")
        self.type_combo.currentIndexChanged.connect(self.refresh)
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch(1)
        
        # Report content
        self.report_frame = QFrame()
        self.report_frame.setFrameShape(QFrame.StyledPanel)
        self.report_layout = QVBoxLayout()
        self.report_layout.setContentsMargins(16, 16, 16, 16)
        self.report_layout.setSpacing(12)
        self.report_frame.setLayout(self.report_layout)
        
        # Export button
        export_btn = QPushButton("📄 Export Report to Text File")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self._export_report)
        
        # Container layout
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(header)
        layout.addLayout(type_layout)
        layout.addWidget(self.report_frame)
        layout.addWidget(export_btn)
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
        
        self.current_report_text = ""
    
    def refresh(self):
        """Generate and display report"""
        # Clear existing report
        while self.report_layout.count():
            item = self.report_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        report_type = self.type_combo.currentData()
        
        if report_type == "weekly":
            self._generate_weekly_report()
        elif report_type == "monthly":
            self._generate_monthly_report()
        else:
            self._generate_all_time_report()
    
    def _generate_weekly_report(self):
        """Generate weekly summary report"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = today
        
        title = QLabel(f"📅 Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
        font = title.font()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        
        self.report_layout.addWidget(title)
        
        habits = list_habits()
        habits = [h for h in habits if h.name != "General"]
        
        if not habits:
            self.report_layout.addWidget(QLabel("No habits to report on."))
            self.current_report_text = "No habits tracked this week."
            return
        
        report_lines = [f"WEEKLY REPORT: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}\n"]
        report_lines.append("=" * 60 + "\n")
        
        total_completions = 0
        total_possible = len(habits) * 7
        
        for habit in habits:
            completions = get_done_days_in_range(
                habit.id,
                week_start.isoformat(),
                week_end.isoformat()
            )
            count = len(completions)
            total_completions += count
            rate = (count / 7) * 100
            
            habit_label = QLabel(f"• {habit.name}: {count}/7 days ({rate:.0f}%)")
            self.report_layout.addWidget(habit_label)
            
            report_lines.append(f"• {habit.name}: {count}/7 days ({rate:.0f}%)\n")
        
        overall_rate = (total_completions / total_possible * 100) if total_possible > 0 else 0
        
        summary = QLabel(f"\n📊 Overall: {total_completions}/{total_possible} ({overall_rate:.1f}%)")
        font = summary.font()
        font.setBold(True)
        summary.setFont(font)
        self.report_layout.addWidget(summary)
        
        report_lines.append(f"\n📊 Overall: {total_completions}/{total_possible} ({overall_rate:.1f}%)\n")
        
        self.current_report_text = "".join(report_lines)
    
    def _generate_monthly_report(self):
        """Generate monthly summary report"""
        today = date.today()
        month_start = date(today.year, today.month, 1)
        
        title = QLabel(f"📅 {month_start.strftime('%B %Y')} Summary")
        font = title.font()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        
        self.report_layout.addWidget(title)
        
        habits = list_habits()
        habits = [h for h in habits if h.name != "General"]
        
        if not habits:
            self.report_layout.addWidget(QLabel("No habits to report on."))
            self.current_report_text = "No habits tracked this month."
            return
        
        days_in_month = (today - month_start).days + 1
        
        report_lines = [f"MONTHLY REPORT: {month_start.strftime('%B %Y')}\n"]
        report_lines.append("=" * 60 + "\n")
        
        total_completions = 0
        total_possible = len(habits) * days_in_month
        
        for habit in habits:
            completions = get_done_days_in_range(
                habit.id,
                month_start.isoformat(),
                today.isoformat()
            )
            count = len(completions)
            total_completions += count
            rate = (count / days_in_month) * 100
            streak = current_streak(habit.id)
            
            habit_label = QLabel(f"• {habit.name}: {count}/{days_in_month} days ({rate:.0f}%) | Streak: {streak} days")
            self.report_layout.addWidget(habit_label)
            
            report_lines.append(f"• {habit.name}: {count}/{days_in_month} days ({rate:.0f}%) | Streak: {streak} days\n")
        
        overall_rate = (total_completions / total_possible * 100) if total_possible > 0 else 0
        
        summary = QLabel(f"\n📊 Overall: {total_completions}/{total_possible} ({overall_rate:.1f}%)")
        font = summary.font()
        font.setBold(True)
        summary.setFont(font)
        self.report_layout.addWidget(summary)
        
        report_lines.append(f"\n📊 Overall: {total_completions}/{total_possible} ({overall_rate:.1f}%)\n")
        
        self.current_report_text = "".join(report_lines)
    
    def _generate_all_time_report(self):
        """Generate all-time summary report"""
        title = QLabel("📅 All-Time Summary")
        font = title.font()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        
        self.report_layout.addWidget(title)
        
        habits = list_habits()
        habits = [h for h in habits if h.name != "General"]
        
        if not habits:
            self.report_layout.addWidget(QLabel("No habits to report on."))
            self.current_report_text = "No habits tracked yet."
            return
        
        report_lines = ["ALL-TIME REPORT\n"]
        report_lines.append("=" * 60 + "\n")
        
        total_completions = 0
        max_streak = 0
        best_habit = ""
        
        for habit in habits:
            completions = get_done_days_in_range(habit.id, "2000-01-01", date.today().isoformat())
            count = len(completions)
            total_completions += count
            streak = current_streak(habit.id)
            
            if streak > max_streak:
                max_streak = streak
                best_habit = habit.name
            
            created = date.fromisoformat(habit.created_at.split()[0])
            days_since = (date.today() - created).days + 1
            rate = (count / days_since * 100) if days_since > 0 else 0
            
            habit_label = QLabel(
                f"• {habit.name}: {count} completions | "
                f"Current streak: {streak} days | "
                f"Rate: {rate:.1f}%"
            )
            self.report_layout.addWidget(habit_label)
            
            report_lines.append(
                f"• {habit.name}: {count} completions | "
                f"Current streak: {streak} days | "
                f"Rate: {rate:.1f}%\n"
            )
        
        summary_text = (
            f"\n📊 Total Completions: {total_completions}\n"
            f"🏆 Best Current Streak: {max_streak} days ({best_habit})\n"
            f"📈 Total Habits: {len(habits)}"
        )
        
        summary = QLabel(summary_text)
        font = summary.font()
        font.setBold(True)
        summary.setFont(font)
        self.report_layout.addWidget(summary)
        
        report_lines.append(summary_text + "\n")
        
        self.current_report_text = "".join(report_lines)
    
    # ui_reports.py - Replace the _export_report method
    def _export_report(self):
        """Export current report to text file"""
        if not self.current_report_text:
            QMessageBox.warning(self, "No Report", "Generate a report first before exporting.")
            return
        
        report_type = self.type_combo.currentText().replace(" ", "_").lower()
        default_filename = f"flowly_report_{report_type}_{date.today().isoformat()}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            str(Path.home() / default_filename),
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                # Remove emojis for safe export
                safe_text = self.current_report_text.encode('ascii', 'ignore').decode('ascii')
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(safe_text)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Report exported successfully to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    f"Failed to export report:\n{str(e)}"
                )