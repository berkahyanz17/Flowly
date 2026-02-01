# ui_milestones.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QProgressBar
)
from PySide6.QtGui import QFont, QPalette
from models import list_habits, get_done_days_in_range, current_streak
from datetime import date


class MilestoneCard(QFrame):
    """Card showing a milestone achievement"""
    def __init__(self, title: str, description: str, progress: int, target: int, earned: bool):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(120)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Badge emoji based on milestone
        badge = "🏆" if earned else "🔒"
        
        # Title
        title_label = QLabel(f"{badge} {title}")
        font = title_label.font()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        
        # Progress
        progress_layout = QHBoxLayout()
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(target)
        progress_bar.setValue(min(progress, target))
        progress_bar.setFormat(f"{progress}/{target}")
        
        progress_layout.addWidget(progress_bar)
        
        # Status
        if earned:
            status_label = QLabel("✓ Completed!")
            status_label.setStyleSheet("color: #39d353; font-weight: bold;")
        else:
            remaining = target - progress
            status_label = QLabel(f"{remaining} more to go")
            status_label.setStyleSheet("color: gray;")
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(progress_layout)
        layout.addWidget(status_label)
        
        self.setLayout(layout)


class MilestonesTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create container
        container = QWidget()
        
        # Header
        header = QLabel("Milestones & Achievements")
        font = header.font()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        
        # Stats summary
        self.stats_label = QLabel()
        font = self.stats_label.font()
        font.setPointSize(11)
        self.stats_label.setFont(font)
        
        # Milestones grid
        self.milestones_layout = QGridLayout()
        self.milestones_layout.setSpacing(12)
        
        # Container layout
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(header)
        layout.addWidget(self.stats_label)
        layout.addLayout(self.milestones_layout)
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
    
    def refresh(self):
        """Refresh milestones data"""
        # Clear existing milestones
        while self.milestones_layout.count():
            item = self.milestones_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        habits = list_habits()
        habits = [h for h in habits if h.name != "General"]
        
        if not habits:
            self.stats_label.setText("Create some habits to start earning milestones!")
            return
        
        # Calculate statistics
        total_completions = 0
        max_streak = 0
        total_streaks = 0
        
        for habit in habits:
            streak = current_streak(habit.id)
            if streak > max_streak:
                max_streak = streak
            total_streaks += streak
            
            # Count total completions
            completions = get_done_days_in_range(habit.id, "2000-01-01", date.today().isoformat())
            total_completions += len(completions)
        
        # Update stats
        earned_count = self._count_earned_milestones(total_completions, max_streak, len(habits))
        self.stats_label.setText(
            f"🎯 Achievements Earned: {earned_count} | "
            f"Total Completions: {total_completions} | "
            f"Best Streak: {max_streak} days"
        )
        
        # Define milestones
        milestones = [
            ("First Step", "Complete your first habit", total_completions, 1),
            ("Getting Started", "Complete 10 habits", total_completions, 10),
            ("Building Momentum", "Complete 50 habits", total_completions, 50),
            ("Habit Master", "Complete 100 habits", total_completions, 100),
            ("Legendary", "Complete 500 habits", total_completions, 500),
            
            ("Week Warrior", "Maintain a 7-day streak", max_streak, 7),
            ("Month Master", "Maintain a 30-day streak", max_streak, 30),
            ("Quarter Champion", "Maintain a 90-day streak", max_streak, 90),
            ("Year Legend", "Maintain a 365-day streak", max_streak, 365),
            
            ("Habit Collector", "Create 5 habits", len(habits), 5),
            ("Routine Builder", "Create 10 habits", len(habits), 10),
            ("Lifestyle Designer", "Create 20 habits", len(habits), 20),
        ]
        
        # Add milestone cards
        row, col = 0, 0
        for title, desc, progress, target in milestones:
            earned = progress >= target
            card = MilestoneCard(title, desc, progress, target, earned)
            self.milestones_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
    
    def _count_earned_milestones(self, total_completions: int, max_streak: int, habit_count: int) -> int:
        """Count how many milestones have been earned"""
        earned = 0
        
        # Completion milestones
        if total_completions >= 1: earned += 1
        if total_completions >= 10: earned += 1
        if total_completions >= 50: earned += 1
        if total_completions >= 100: earned += 1
        if total_completions >= 500: earned += 1
        
        # Streak milestones
        if max_streak >= 7: earned += 1
        if max_streak >= 30: earned += 1
        if max_streak >= 90: earned += 1
        if max_streak >= 365: earned += 1
        
        # Habit count milestones
        if habit_count >= 5: earned += 1
        if habit_count >= 10: earned += 1
        if habit_count >= 20: earned += 1
        
        return earned