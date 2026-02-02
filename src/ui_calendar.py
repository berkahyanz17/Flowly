# ui_calendar.py
from datetime import date, timedelta
from typing import Dict, List
from PySide6.QtCore import Qt, QDate, QSize, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QPalette, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QFrame, QListWidget, QListWidgetItem, QSizePolicy,
    QScrollArea
)
from src.db import get_conn
from src.models import list_habits, is_done_on_day, mark_done, unmark_done


class HabitCalendar(QCalendarWidget):
    """Custom calendar that shows habit completion"""
    def __init__(self):
        super().__init__()
        self._completion_data: Dict[str, int] = {}  # {date: completion_count}
        self._total_habits = 0
        
        # Styling
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
    def set_data(self, completion_data: Dict[str, int], total_habits: int):
        """Update calendar with completion data"""
        self._completion_data = completion_data
        self._total_habits = total_habits
        self.updateCells()
    
    def _is_dark_mode(self) -> bool:
        """Check if system is in dark mode"""
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        return bg_color.lightness() < 128
    
    def _get_color_for_completion(self, done_count: int) -> QColor:
        """Get color based on completion count"""
        if self._total_habits == 0:
            is_dark = self._is_dark_mode()
            return QColor(22, 27, 34) if is_dark else QColor(235, 237, 240)
        
        rate = done_count / self._total_habits
        is_dark = self._is_dark_mode()
        
        if is_dark:
            # Dark theme
            if done_count == 0:
                return QColor(22, 27, 34)
            elif rate <= 0.33:
                return QColor(0, 68, 51)
            elif rate <= 0.66:
                return QColor(0, 109, 66)
            else:
                return QColor(57, 211, 83)
        else:
            # Light theme
            if done_count == 0:
                return QColor(235, 237, 240)
            elif rate <= 0.33:
                return QColor(155, 233, 168)
            elif rate <= 0.66:
                return QColor(64, 196, 99)
            else:
                return QColor(33, 110, 57)
    
    def _get_text_color(self, done_count: int) -> QColor:
        """Get text color based on theme and completion"""
        is_dark = self._is_dark_mode()
        
        if is_dark:
            # In dark mode, use white text on dark backgrounds
            if done_count == 0:
                return QColor(139, 148, 158)  # Muted gray for empty days
            else:
                return QColor(230, 237, 243)  # Bright white for completed days
        else:
            # In light mode, use dark text
            return QColor(0, 0, 0)
    
    def paintCell(self, painter: QPainter, rect, date: QDate):
        """Override to paint cells with completion colors"""
        date_str = date.toString("yyyy-MM-dd")
        done_count = self._completion_data.get(date_str, 0)
        
        # Fill background based on completion
        color = self._get_color_for_completion(done_count)
        painter.fillRect(rect, color)
        
        # Draw text (day number) with appropriate color
        text_color = self._get_text_color(done_count)
        painter.setPen(QPen(text_color))
        
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        
        painter.drawText(rect, Qt.AlignCenter, str(date.day()))
        
        # Highlight today with a colored border
        if date == QDate.currentDate():
            is_dark = self._is_dark_mode()
            border_color = QColor(88, 166, 255) if is_dark else QColor(9, 105, 218)
            painter.setPen(QPen(border_color, 2))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
    
    def changeEvent(self, event: QEvent):
        """Handle theme changes"""
        if event.type() == QEvent.PaletteChange:
            # Theme changed, repaint calendar
            self.updateCells()
        super().changeEvent(event)


class CalendarTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create container widget for scrolling
        container = QWidget()
        
        # Header
        header = QLabel("Calendar View")
        font = header.font()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        
        # Navigation buttons
        self.prev_month_btn = QPushButton("← Previous Month")
        self.prev_month_btn.clicked.connect(self._prev_month)
        
        self.next_month_btn = QPushButton("Next Month →")
        self.next_month_btn.clicked.connect(self._next_month)
        
        self.today_btn = QPushButton("Today")
        self.today_btn.clicked.connect(self._go_to_today)
        
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.prev_month_btn)
        nav_layout.addWidget(self.today_btn)
        nav_layout.addWidget(self.next_month_btn)
        
        # Calendar widget
        self.calendar = HabitCalendar()
        self.calendar.clicked.connect(self._date_selected)
        
        # Current month label
        self.month_label = QLabel()
        font = self.month_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.month_label.setFont(font)
        self.month_label.setAlignment(Qt.AlignCenter)
        
        # Selected date info
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(12)
        
        self.selected_date_label = QLabel("Select a date to view details")
        font = self.selected_date_label.font()
        font.setPointSize(11)
        font.setBold(True)
        self.selected_date_label.setFont(font)
        
        self.completion_label = QLabel("")
        
        # Habits list for selected date
        self.habits_list = QListWidget()
        self.habits_list.itemChanged.connect(self._habit_toggled)

        self.habits_list.addItem("temp")

        row_height = self.habits_list.sizeHintForRow(0)
        frame = self.habits_list.frameWidth() * 2
        self.habits_list.setMinimumHeight(row_height * 5 + frame)

        self.habits_list.clear()
        
        info_layout.addWidget(self.selected_date_label)
        info_layout.addWidget(self.completion_label)
        info_layout.addWidget(QLabel("Habits:"))
        info_layout.addWidget(self.habits_list)
        info_frame.setLayout(info_layout)
        
        # Legend
        legend_frame = QFrame()
        legend_frame.setFrameShape(QFrame.StyledPanel)
        self.legend_layout = QHBoxLayout()
        self.legend_layout.setContentsMargins(12, 8, 12, 8)
        
        legend_title = QLabel("Legend:")
        font = legend_title.font()
        font.setBold(True)
        legend_title.setFont(font)
        
        self.legend_layout.addWidget(legend_title)
        self._update_legend()
        legend_frame.setLayout(self.legend_layout)
        
        # Container layout
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        container_layout.addWidget(header)
        container_layout.addLayout(nav_layout)
        container_layout.addWidget(self.month_label)
        container_layout.addWidget(self.calendar)
        container_layout.addWidget(legend_frame)
        container_layout.addWidget(info_frame)
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
        
        # Cache
        self._habits_cache = []
        self._current_selected_date = None
    
    def _is_dark_mode(self) -> bool:
        """Check if system is in dark mode"""
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        return bg_color.lightness() < 128
    
    def _update_legend(self):
        """Update legend colors based on current theme"""
        # Clear existing legend items (except title)
        while self.legend_layout.count() > 1:
            item = self.legend_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        # Add legend items with current theme colors
        is_dark = self._is_dark_mode()
        
        if is_dark:
            self.legend_layout.addWidget(self._create_legend_item("No habits", QColor(22, 27, 34)))
            self.legend_layout.addWidget(self._create_legend_item("Low", QColor(0, 68, 51)))
            self.legend_layout.addWidget(self._create_legend_item("Medium", QColor(0, 109, 66)))
            self.legend_layout.addWidget(self._create_legend_item("High", QColor(57, 211, 83)))
        else:
            self.legend_layout.addWidget(self._create_legend_item("No habits", QColor(235, 237, 240)))
            self.legend_layout.addWidget(self._create_legend_item("Low", QColor(155, 233, 168)))
            self.legend_layout.addWidget(self._create_legend_item("Medium", QColor(64, 196, 99)))
            self.legend_layout.addWidget(self._create_legend_item("High", QColor(33, 110, 57)))
        
        self.legend_layout.addStretch(1)
    
    def _create_legend_item(self, text: str, color: QColor) -> QWidget:
        """Create a legend item with colored square"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        color_label = QLabel()
        color_label.setFixedSize(16, 16)
        color_label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #999;")
        
        text_label = QLabel(text)
        
        layout.addWidget(color_label)
        layout.addWidget(text_label)
        widget.setLayout(layout)
        
        return widget
    
    def _prev_month(self):
        """Go to previous month"""
        current = self.calendar.selectedDate()
        new_date = current.addMonths(-1)
        self.calendar.setSelectedDate(new_date)
        self.refresh()
    
    def _next_month(self):
        """Go to next month"""
        current = self.calendar.selectedDate()
        new_date = current.addMonths(1)
        self.calendar.setSelectedDate(new_date)
        self.refresh()
    
    def _go_to_today(self):
        """Go to today's date"""
        self.calendar.setSelectedDate(QDate.currentDate())
        self.refresh()
    
    def _date_selected(self, qdate: QDate):
        """Handle date selection"""
        self._current_selected_date = qdate.toString("yyyy-MM-dd")
        self._update_selected_date_info()
    
    def _update_selected_date_info(self):
        """Update the info panel for selected date"""
        if not self._current_selected_date:
            return
        
        # Parse date
        d = date.fromisoformat(self._current_selected_date)
        formatted = d.strftime("%A, %B %d, %Y")
        self.selected_date_label.setText(formatted)
        
        # Get completion info
        conn = get_conn()
        done_count = conn.execute(
            """
            SELECT COUNT(*) as c FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE hl.day = ? AND h.name != 'General';
            """,
            (self._current_selected_date,)
        ).fetchone()
        conn.close()
        
        done = int(done_count["c"]) if done_count else 0
        total = len([h for h in self._habits_cache if h.name != "General"])
        
        if total > 0:
            rate = (done / total) * 100
            self.completion_label.setText(f"Completed: {done}/{total} ({rate:.1f}%)")
        else:
            self.completion_label.setText("No habits to track")
        
        # Update habits list
        self.habits_list.blockSignals(True)
        self.habits_list.clear()
        
        for habit in self._habits_cache:
            if habit.name == "General":
                continue
            
            item = QListWidgetItem(habit.name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            if is_done_on_day(habit.id, self._current_selected_date):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            
            # Store habit id in item data
            item.setData(Qt.UserRole, habit.id)
            
            self.habits_list.addItem(item)
        
        self.habits_list.blockSignals(False)
    
    def _habit_toggled(self, item: QListWidgetItem):
        """Handle habit checkbox toggle"""
        if not self._current_selected_date:
            return
        
        habit_id = item.data(Qt.UserRole)
        is_checked = item.checkState() == Qt.Checked
        
        if is_checked:
            mark_done(habit_id, self._current_selected_date)
        else:
            unmark_done(habit_id, self._current_selected_date)
        
        self.refresh()
    
    def changeEvent(self, event: QEvent):
        """Handle theme changes"""
        if event.type() == QEvent.PaletteChange:
            # Theme changed, update legend
            self._update_legend()
        super().changeEvent(event)
    
    def refresh(self):
        """Refresh calendar data"""
        self._habits_cache = list_habits()
        
        # Update month label
        selected = self.calendar.selectedDate()
        self.month_label.setText(selected.toString("MMMM yyyy"))
        
        # Get first and last day of current month view
        year = selected.year()
        month = selected.month()
        
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get completion data for the month
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT hl.day, COUNT(*) as c
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE hl.day BETWEEN ? AND ? AND h.name != 'General'
            GROUP BY hl.day;
            """,
            (first_day.isoformat(), last_day.isoformat())
        ).fetchall()
        conn.close()
        
        completion_data = {}
        for r in rows:
            completion_data[str(r["day"])] = int(r["c"])
        
        total_habits = len([h for h in self._habits_cache if h.name != "General"])
        self.calendar.set_data(completion_data, total_habits)
        
        # Update legend for current theme
        self._update_legend()
        
        # Update selected date info if a date is selected
        if self._current_selected_date:
            self._update_selected_date_info()