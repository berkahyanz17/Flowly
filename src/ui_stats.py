# ui_stats.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Tuple

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QFrame, QSizePolicy, QHeaderView, QGridLayout,
    QProgressBar, QScrollArea
)

from src.db import get_conn


# ---------- helpers ----------
def today_str() -> str:
    return date.today().isoformat()

def days_back(n: int) -> List[str]:
    start = date.today() - timedelta(days=n - 1)
    return [(start + timedelta(days=i)).isoformat() for i in range(n)]

def total_habits_count() -> int:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) AS c FROM habits WHERE name != 'General';").fetchone()
    conn.close()
    return int(row["c"]) if row else 0

def total_done_in_range(start_day: str, end_day: str) -> int:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT COUNT(*) AS c FROM habit_logs hl
        JOIN habits h ON hl.habit_id = h.id
        WHERE hl.day BETWEEN ? AND ? AND h.name != 'General';
        """,
        (start_day, end_day),
    ).fetchone()
    conn.close()
    return int(row["c"]) if row else 0

def per_habit_done_in_range(start_day: str, end_day: str) -> List[Tuple[str, int]]:
    """
    Returns list of (habit_name, done_count) for range.
    Includes habits with 0. Excludes "General".
    """
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT h.name AS name, COALESCE(x.c, 0) AS c
        FROM habits h
        LEFT JOIN (
            SELECT habit_id, COUNT(*) AS c
            FROM habit_logs
            WHERE day BETWEEN ? AND ?
            GROUP BY habit_id
        ) x ON x.habit_id = h.id
        WHERE h.name != 'General'
        ORDER BY name COLLATE NOCASE;
        """,
        (start_day, end_day),
    ).fetchall()
    conn.close()
    return [(str(r["name"]), int(r["c"])) for r in rows]

def daily_completion_counts(days: int) -> Dict[str, int]:
    """
    Returns {day: done_count} for last N days (including today).
    Excludes "General" habit.
    """
    ds = days_back(days)
    start_day, end_day = ds[0], ds[-1]

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT hl.day, COUNT(*) AS c
        FROM habit_logs hl
        JOIN habits h ON hl.habit_id = h.id
        WHERE hl.day BETWEEN ? AND ? AND h.name != 'General'
        GROUP BY hl.day
        ORDER BY hl.day;
        """,
        (start_day, end_day),
    ).fetchall()
    conn.close()

    out = {d: 0 for d in ds}
    for r in rows:
        out[str(r["day"])] = int(r["c"])
    return out

def get_best_streak() -> Tuple[str, int]:
    """Returns (habit_name, streak_days) for longest current streak"""
    conn = get_conn()
    habits = conn.execute("SELECT id, name FROM habits WHERE name != 'General';").fetchall()
    conn.close()
    
    best_name = "None"
    best_streak = 0
    
    for h in habits:
        hid = int(h["id"])
        # Calculate streak
        conn = get_conn()
        logs = conn.execute(
            "SELECT day FROM habit_logs WHERE habit_id = ? ORDER BY day DESC;",
            (hid,)
        ).fetchall()
        conn.close()
        
        streak = 0
        d = date.today()
        log_days = {str(r["day"]) for r in logs}
        
        while d.isoformat() in log_days:
            streak += 1
            d = d - timedelta(days=1)
        
        if streak > best_streak:
            best_streak = streak
            best_name = str(h["name"])
    
    return (best_name, best_streak)

def get_completion_by_weekday(start_day: str, end_day: str) -> Dict[str, int]:
    """Returns {weekday_name: completion_count} for date range"""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT hl.day, COUNT(*) AS c
        FROM habit_logs hl
        JOIN habits h ON hl.habit_id = h.id
        WHERE hl.day BETWEEN ? AND ? AND h.name != 'General'
        GROUP BY hl.day;
        """,
        (start_day, end_day),
    ).fetchall()
    conn.close()
    
    weekday_counts = {"Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0}
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    for r in rows:
        d = date.fromisoformat(str(r["day"]))
        weekday = weekday_names[d.weekday()]
        weekday_counts[weekday] += int(r["c"])
    
    return weekday_counts

def get_pomodoro_stats(start_day: str, end_day: str) -> Tuple[int, int]:
    """
    Returns (total_sessions, total_minutes) for Pomodoro sessions in range.
    """
    conn = get_conn()
    
    # Check if pomodoro_sessions table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pomodoro_sessions';"
    ).fetchone()
    
    if not table_check:
        # Create table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                duration INTEGER NOT NULL,
                completed_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
    
    # Get stats
    row = conn.execute(
        """
        SELECT 
            COUNT(*) as sessions,
            COALESCE(SUM(duration), 0) as total_minutes
        FROM pomodoro_sessions
        WHERE session_type = 'work' 
        AND date(completed_at) BETWEEN ? AND ?;
        """,
        (start_day, end_day),
    ).fetchone()
    conn.close()
    
    return (int(row["sessions"]) if row else 0, int(row["total_minutes"]) if row else 0)


# ---------- UI components ----------
class WeekdayChart(QWidget):
    """Bar chart showing completions by day of week with light/dark mode support"""
    def __init__(self):
        super().__init__()
        self._data: Dict[str, int] = {}
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(200)
    
    def set_data(self, data: Dict[str, int]):
        self._data = data
        self.update()
    
    def _is_dark_mode(self) -> bool:
        """Check if system is in dark mode"""
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        return bg_color.lightness() < 128
    
    def _get_bar_color(self) -> QColor:
        """Get bar color based on theme"""
        is_dark = self._is_dark_mode()
        return QColor(57, 211, 83) if is_dark else QColor(48, 161, 78)
    
    def _get_text_color(self) -> QColor:
        """Get text color based on theme"""
        is_dark = self._is_dark_mode()
        return QColor(139, 148, 158) if is_dark else QColor(60, 60, 60)
    
    def paintEvent(self, event):
        if not self._data:
            return
        
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        
        # Setup
        padding = 50
        w = self.width() - padding * 2
        h = self.height() - padding * 2
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        max_val = max(self._data.values()) if self._data.values() else 1
        if max_val == 0:
            max_val = 1
        
        bar_width = w / len(days) * 0.7
        gap = w / len(days) * 0.3
        
        # Draw bars
        for i, day in enumerate(days):
            count = self._data.get(day, 0)
            bar_height = (count / max_val) * h if max_val > 0 else 0
            
            x = padding + i * (bar_width + gap)
            y = padding + h - bar_height
            
            # Bar color
            p.setPen(Qt.NoPen)
            p.setBrush(self._get_bar_color())
            p.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_height), 4, 4)
            
            # Day label
            p.setPen(QPen(self._get_text_color()))
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            p.setFont(font)
            p.drawText(int(x), padding + h + 25, int(bar_width), 20, Qt.AlignCenter, day)
            
            # Count label
            if count > 0:
                p.drawText(int(x), int(y - 15), int(bar_width), 20, Qt.AlignCenter, str(count))


class ContribGrid(QWidget):
    """
    GitHub-style contribution grid with light/dark theme support.
    Shows last 365 days ending TODAY (rightmost column).
    """
    def __init__(self):
        super().__init__()
        self._counts: Dict[str, int] = {}
        self._date_list: List[str] = []
        
        self.cell_size = 11
        self.gap = 3
        self.pad_left = 30
        self.pad_top = 20
        self.pad_right = 10
        self.pad_bottom = 10
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setToolTip("")

    def set_data(self, requested_days: int, counts: Dict[str, int], total_habits: int):
        self._counts = counts
        today = date.today()
        self._date_list = []
        for i in range(364, -1, -1):
            d = today - timedelta(days=i)
            self._date_list.append(d.isoformat())
        
        self.setMinimumHeight(self.sizeHint().height())
        self.update()

    def sizeHint(self) -> QSize:
        cols = 53
        w = self.pad_left + self.pad_right + cols * self.cell_size + (cols - 1) * self.gap
        h = self.pad_top + self.pad_bottom + 7 * self.cell_size + 6 * self.gap
        return QSize(w, h)

    def _is_dark_mode(self) -> bool:
        """Check if system is in dark mode"""
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        return bg_color.lightness() < 128

    def _get_color(self, count: int) -> QColor:
        """Get color based on count and theme"""
        is_dark = self._is_dark_mode()
        
        if is_dark:
            # Dark theme colors
            if count == 0:
                return QColor(22, 27, 34)
            elif count <= 2:
                return QColor(0, 68, 51)
            elif count <= 4:
                return QColor(0, 109, 66)
            elif count <= 6:
                return QColor(38, 166, 65)
            else:
                return QColor(57, 211, 83)
        else:
            # Light theme colors
            if count == 0:
                return QColor(235, 237, 240)
            elif count <= 2:
                return QColor(155, 233, 168)
            elif count <= 4:
                return QColor(64, 196, 99)
            elif count <= 6:
                return QColor(48, 161, 78)
            else:
                return QColor(33, 110, 57)

    def _get_text_color(self) -> QColor:
        """Get text color based on theme"""
        is_dark = self._is_dark_mode()
        return QColor(139, 148, 158) if is_dark else QColor(100, 100, 100)

    def _get_border_color(self) -> QColor:
        """Get border color based on theme"""
        is_dark = self._is_dark_mode()
        return QColor(48, 54, 61) if is_dark else QColor(220, 220, 220)

    def _get_month_label(self, day_str: str) -> str:
        d = date.fromisoformat(day_str)
        return d.strftime("%b")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        
        if not self._date_list:
            return
        
        x_start = self.pad_left
        y_start = self.pad_top
        
        first_date = date.fromisoformat(self._date_list[0])
        start_weekday = first_date.weekday()
        start_day_of_week = (start_weekday + 1) % 7
        
        # Month labels
        p.setPen(QPen(self._get_text_color()))
        font = QFont()
        font.setPointSize(9)
        p.setFont(font)
        
        current_month = ""
        col_index = 0
        day_idx = 0
        
        while day_idx < len(self._date_list):
            if day_idx < len(self._date_list):
                day_str = self._date_list[day_idx]
                d = date.fromisoformat(day_str)
                month = self._get_month_label(day_str)
                
                if d.day == 1 and month != current_month:
                    current_month = month
                    x = x_start + col_index * (self.cell_size + self.gap)
                    p.drawText(x, self.pad_top - 6, month)
            
            if day_idx == 0:
                day_idx += (7 - start_day_of_week)
            else:
                day_idx += 7
            col_index += 1
        
        # Day labels
        day_labels = [("Mon", 1), ("Wed", 3), ("Fri", 5)]
        p.setPen(QPen(self._get_text_color()))
        for label, row in day_labels:
            y = y_start + row * (self.cell_size + self.gap) + self.cell_size - 2
            p.drawText(5, y, label)
        
        # Cells
        col_index = 0
        row_in_col = start_day_of_week
        
        for i, day_str in enumerate(self._date_list):
            count = self._counts.get(day_str, 0)
            color = self._get_color(count)
            
            x = x_start + col_index * (self.cell_size + self.gap)
            y = y_start + row_in_col * (self.cell_size + self.gap)
            
            p.setPen(Qt.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(x, y, self.cell_size, self.cell_size, 2, 2)
            
            row_in_col += 1
            if row_in_col >= 7:
                row_in_col = 0
                col_index += 1
        
        # Border
        total_cols = col_index + (1 if row_in_col > 0 else 0)
        p.setPen(QPen(self._get_border_color(), 1))
        p.setBrush(Qt.NoBrush)
        grid_w = total_cols * self.cell_size + (total_cols - 1) * self.gap
        grid_h = 7 * self.cell_size + 6 * self.gap
        p.drawRoundedRect(x_start - 2, y_start - 2, grid_w + 4, grid_h + 4, 4, 4)

    def mouseMoveEvent(self, event):
        if not self._date_list:
            return
        
        pos = event.pos()
        x_start = self.pad_left
        y_start = self.pad_top
        
        first_date = date.fromisoformat(self._date_list[0])
        start_weekday = first_date.weekday()
        start_day_of_week = (start_weekday + 1) % 7
        
        col_index = 0
        row_in_col = start_day_of_week
        
        for i, day_str in enumerate(self._date_list):
            x = x_start + col_index * (self.cell_size + self.gap)
            y = y_start + row_in_col * (self.cell_size + self.gap)
            
            if (x <= pos.x() <= x + self.cell_size and 
                y <= pos.y() <= y + self.cell_size):
                count = self._counts.get(day_str, 0)
                d = date.fromisoformat(day_str)
                formatted_date = d.strftime("%b %d, %Y")
                plural = "completion" if count == 1 else "completions"
                self.setToolTip(f"{count} {plural} on {formatted_date}")
                return
            
            row_in_col += 1
            if row_in_col >= 7:
                row_in_col = 0
                col_index += 1
        
        self.setToolTip("")


# ---------- Stats tab ----------
class StatsTab(QWidget):
    def __init__(self):
        super().__init__()

        # Create a container widget for all content
        container = QWidget()

        # Header
        title = QLabel("Statistics")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)

        self.range_combo = QComboBox()
        self.range_combo.addItem("Last 7 days", 7)
        self.range_combo.addItem("Last 30 days", 30)
        self.range_combo.addItem("Last 90 days", 90)
        self.range_combo.setCurrentIndex(1)  # Default to 30 days
        self.range_combo.currentIndexChanged.connect(self.refresh)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(QLabel("Time range:"))
        header.addWidget(self.range_combo)

        # Stat values (no cards, just labels)
        # Total completions
        total_title = QLabel("Total Completions")
        font = total_title.font()
        font.setPointSize(9)
        font.setBold(True)
        total_title.setFont(font)
        
        self.total_value = QLabel("0")
        font = self.total_value.font()
        font.setPointSize(24)
        font.setBold(True)
        self.total_value.setFont(font)
        
        total_layout = QVBoxLayout()
        total_layout.setSpacing(4)
        total_layout.addWidget(total_title)
        total_layout.addWidget(self.total_value)
        
        # Completion rate
        rate_title = QLabel("Completion Rate")
        font = rate_title.font()
        font.setPointSize(9)
        font.setBold(True)
        rate_title.setFont(font)
        
        self.rate_value = QLabel("0%")
        font = self.rate_value.font()
        font.setPointSize(24)
        font.setBold(True)
        self.rate_value.setFont(font)
        
        rate_layout = QVBoxLayout()
        rate_layout.setSpacing(4)
        rate_layout.addWidget(rate_title)
        rate_layout.addWidget(self.rate_value)
        
        # Best streak
        streak_title = QLabel("Best Streak")
        font = streak_title.font()
        font.setPointSize(9)
        font.setBold(True)
        streak_title.setFont(font)
        
        self.streak_value = QLabel("0 days")
        font = self.streak_value.font()
        font.setPointSize(24)
        font.setBold(True)
        self.streak_value.setFont(font)
        
        self.streak_subtitle = QLabel("No habit")
        
        streak_layout = QVBoxLayout()
        streak_layout.setSpacing(4)
        streak_layout.addWidget(streak_title)
        streak_layout.addWidget(self.streak_value)
        streak_layout.addWidget(self.streak_subtitle)
        
        # Pomodoro sessions
        pomodoro_title = QLabel("Pomodoro Sessions")
        font = pomodoro_title.font()
        font.setPointSize(9)
        font.setBold(True)
        pomodoro_title.setFont(font)
        
        self.pomodoro_value = QLabel("0")
        font = self.pomodoro_value.font()
        font.setPointSize(24)
        font.setBold(True)
        self.pomodoro_value.setFont(font)
        
        self.pomodoro_subtitle = QLabel("0 minutes")
        
        pomodoro_layout = QVBoxLayout()
        pomodoro_layout.setSpacing(4)
        pomodoro_layout.addWidget(pomodoro_title)
        pomodoro_layout.addWidget(self.pomodoro_value)
        pomodoro_layout.addWidget(self.pomodoro_subtitle)
        
        stats_row = QHBoxLayout()
        stats_row.setSpacing(30)
        stats_row.addLayout(total_layout)
        stats_row.addLayout(rate_layout)
        stats_row.addLayout(pomodoro_layout)
        stats_row.addLayout(streak_layout)
        # stats_row.addStretch(1)
        # 365-Day Activity section
        grid_title = QLabel("365-Day Activity")
        font = grid_title.font()
        font.setPointSize(11)
        font.setBold(True)
        grid_title.setFont(font)
        
        self.grid = ContribGrid()
        self.grid_hint = QLabel("Each square represents a day. Darker green = more habits completed.")
        self.grid_hint.setWordWrap(True)

        # Weekday chart section
        weekday_title = QLabel("Completion by Day of Week")
        font = weekday_title.font()
        font.setPointSize(11)
        font.setBold(True)
        weekday_title.setFont(font)
        
        self.weekday_chart = WeekdayChart()

        # Table section
        table_title = QLabel("Habit Breakdown")
        font = table_title.font()
        font.setPointSize(11)
        font.setBold(True)
        table_title.setFont(font)
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Habit", "Completions", "Rate"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # Container layout
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(14, 14, 14, 14)
        container_layout.setSpacing(16)
        container_layout.addLayout(header)
        container_layout.addLayout(stats_row)
        
        container_layout.addSpacing(12)
        container_layout.addWidget(grid_title)
        container_layout.addWidget(self.grid)
        container_layout.addWidget(self.grid_hint)
        
        container_layout.addSpacing(12)
        container_layout.addWidget(weekday_title)
        container_layout.addWidget(self.weekday_chart)
        
        container_layout.addSpacing(12)
        container_layout.addWidget(table_title)
        container_layout.addWidget(self.table)
        container_layout.addStretch(1)
        
        container.setLayout(container_layout)

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
        days = int(self.range_combo.currentData())
        ds = days_back(days)
        start_day, end_day = ds[0], ds[-1]

        habits = total_habits_count()
        done_total = total_done_in_range(start_day, end_day)
        total_slots = habits * len(ds)
        rate = (done_total / total_slots) if total_slots else 0.0

        # Update stat values
        self.total_value.setText(str(done_total))
        self.rate_value.setText(f"{round(rate * 100, 1)}%")
        
        best_habit, best_streak_days = get_best_streak()
        self.streak_value.setText(f"{best_streak_days} days")
        self.streak_subtitle.setText(best_habit if best_streak_days > 0 else "No active streaks")
        
        # Update Pomodoro stats
        pomodoro_sessions, pomodoro_minutes = get_pomodoro_stats(start_day, end_day)
        self.pomodoro_value.setText(str(pomodoro_sessions))
        hours = pomodoro_minutes // 60
        mins = pomodoro_minutes % 60
        if hours > 0:
            self.pomodoro_subtitle.setText(f"{hours}h {mins}m")
        else:
            self.pomodoro_subtitle.setText(f"{mins} minutes")

        # Grid (365 days)
        counts = daily_completion_counts(365)
        self.grid.set_data(365, counts, habits)

        # Weekday chart
        weekday_data = get_completion_by_weekday(start_day, end_day)
        self.weekday_chart.set_data(weekday_data)

        # Table
        per = per_habit_done_in_range(start_day, end_day)
        self.table.setRowCount(len(per))
        for i, (name, done_count) in enumerate(per):
            # Habit name
            self.table.setItem(i, 0, QTableWidgetItem(name))
            
            # Completions
            count_item = QTableWidgetItem(str(done_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, count_item)
            
            # Rate as progress bar
            rate_h = (done_count / len(ds)) if len(ds) else 0.0
            
            # Create a container widget for the progress bar
            progress_widget = QWidget()
            progress_layout = QHBoxLayout(progress_widget)
            progress_layout.setContentsMargins(4, 2, 4, 2)
            
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(int(rate_h * 100))
            progress_bar.setFormat(f"{round(rate_h * 100, 1)}%")
            progress_bar.setTextVisible(True)
            
            progress_layout.addWidget(progress_bar)
            progress_widget.setLayout(progress_layout)
            
            self.table.setCellWidget(i, 2, progress_widget)