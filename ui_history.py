# ui_history.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QFrame, QScrollArea, QComboBox, QLineEdit
)
from PySide6.QtGui import QFont, QColor, QPalette
from db import get_conn
from datetime import date


class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create container
        container = QWidget()
        
        # Header
        header = QLabel("Habit History & Journal")
        font = header.font()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        
        # Filters
        filter_layout = QHBoxLayout()
        
        # Habit filter
        habit_label = QLabel("Filter by Habit:")
        self.habit_combo = QComboBox()
        self.habit_combo.currentIndexChanged.connect(self.refresh)
        
        # Search
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in notes...")
        self.search_input.textChanged.connect(self.refresh)
        self.search_input.setClearButtonEnabled(True)
        
        filter_layout.addWidget(habit_label)
        filter_layout.addWidget(self.habit_combo)
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch(1)
        
        # Timeline list
        self.timeline_list = QListWidget()
        
        # Container layout
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(header)
        layout.addLayout(filter_layout)
        layout.addWidget(self.timeline_list)
        
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
    # ui_history.py - Complete refresh method with better colors
    def refresh(self):
        """Refresh history timeline"""
        # Update habit filter
        self.habit_combo.blockSignals(True)
        current_selection = self.habit_combo.currentData()
        self.habit_combo.clear()
        
        self.habit_combo.addItem("All Habits", -1)
        
        conn = get_conn()
        habits = conn.execute(
            "SELECT id, name FROM habits WHERE name != 'General' ORDER BY name;"
        ).fetchall()
        
        for h in habits:
            self.habit_combo.addItem(str(h["name"]), int(h["id"]))
        
        # Restore selection
        if current_selection is not None:
            idx = self.habit_combo.findData(current_selection)
            if idx >= 0:
                self.habit_combo.setCurrentIndex(idx)
        
        self.habit_combo.blockSignals(False)
        
        # Get selected habit
        selected_habit_id = self.habit_combo.currentData()
        search_text = self.search_input.text().strip().lower()
        
        # Clear timeline
        self.timeline_list.clear()
        
        # Detect theme
        palette = self.palette()
        is_dark = palette.color(QPalette.Window).lightness() < 128
        
        # Fetch timeline events (habit completions + notes)
        events = []
        
        # Get habit completions
        if selected_habit_id == -1:
            completions = conn.execute(
                """
                SELECT hl.day, hl.created_at, h.name as habit_name
                FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE h.name != 'General'
                ORDER BY hl.created_at DESC
                LIMIT 500;
                """
            ).fetchall()
        else:
            completions = conn.execute(
                """
                SELECT hl.day, hl.created_at, h.name as habit_name
                FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE hl.habit_id = ?
                ORDER BY hl.created_at DESC
                LIMIT 500;
                """,
                (selected_habit_id,)
            ).fetchall()
        
        for c in completions:
            events.append({
                'type': 'completion',
                'datetime': str(c["created_at"]),
                'habit': str(c["habit_name"]),
                'content': f"Completed {c['habit_name']} on {c['day']}"
            })
        
        # Get notes
        if selected_habit_id == -1:
            notes = conn.execute(
                """
                SELECT n.created_at, n.content, h.name as habit_name
                FROM notes n
                JOIN habits h ON n.habit_id = h.id
                ORDER BY n.created_at DESC
                LIMIT 500;
                """
            ).fetchall()
        else:
            notes = conn.execute(
                """
                SELECT n.created_at, n.content, h.name as habit_name
                FROM notes n
                JOIN habits h ON n.habit_id = h.id
                WHERE n.habit_id = ?
                ORDER BY n.created_at DESC
                LIMIT 500;
                """,
                (selected_habit_id,)
            ).fetchall()
        
        for n in notes:
            content = str(n["content"])
            if search_text and search_text not in content.lower():
                continue
            
            events.append({
                'type': 'note',
                'datetime': str(n["created_at"]),
                'habit': str(n["habit_name"]),
                'content': f"Note on {n['habit_name']}: {content}"
            })
        
        conn.close()
        
        # Sort events by datetime (newest first)
        events.sort(key=lambda x: x['datetime'], reverse=True)
        
        # Add to timeline with readable colors
        for event in events[:100]:  # Limit to 100 most recent
            item_text = f"[{event['datetime']}] {event['content']}"
            item = QListWidgetItem(item_text)
            
            # Set colors based on event type and theme
            if event['type'] == 'completion':
                if is_dark:
                    item.setForeground(QColor(87, 242, 135))  # Bright green for dark mode
                else:
                    item.setForeground(QColor(22, 163, 74))  # Dark green for light mode
            else:  # note
                if is_dark:
                    item.setForeground(QColor(125, 211, 252))  # Bright blue for dark mode
                else:
                    item.setForeground(QColor(29, 78, 216))  # Dark blue for light mode
            
            self.timeline_list.addItem(item)
        
        if self.timeline_list.count() == 0:
            item = QListWidgetItem("No history to display")
            if is_dark:
                item.setForeground(QColor(156, 163, 175))  # Gray for dark mode
            else:
                item.setForeground(QColor(107, 114, 128))  # Gray for light mode
            self.timeline_list.addItem(item)
            """Refresh history timeline"""
            # Update habit filter
            self.habit_combo.blockSignals(True)
            current_selection = self.habit_combo.currentData()
            self.habit_combo.clear()
            
            self.habit_combo.addItem("All Habits", -1)
            
            conn = get_conn()
            habits = conn.execute(
                "SELECT id, name FROM habits WHERE name != 'General' ORDER BY name;"
            ).fetchall()
            
            for h in habits:
                self.habit_combo.addItem(str(h["name"]), int(h["id"]))
            
            # Restore selection
            if current_selection is not None:
                idx = self.habit_combo.findData(current_selection)
                if idx >= 0:
                    self.habit_combo.setCurrentIndex(idx)
            
            self.habit_combo.blockSignals(False)
            
            # Get selected habit
            selected_habit_id = self.habit_combo.currentData()
            search_text = self.search_input.text().strip().lower()
            
            # Clear timeline
            self.timeline_list.clear()
            
            # Fetch timeline events (habit completions + notes)
            events = []
            
            # Get habit completions
            if selected_habit_id == -1:
                completions = conn.execute(
                    """
                    SELECT hl.day, hl.created_at, h.name as habit_name
                    FROM habit_logs hl
                    JOIN habits h ON hl.habit_id = h.id
                    WHERE h.name != 'General'
                    ORDER BY hl.created_at DESC
                    LIMIT 500;
                    """
                ).fetchall()
            else:
                completions = conn.execute(
                    """
                    SELECT hl.day, hl.created_at, h.name as habit_name
                    FROM habit_logs hl
                    JOIN habits h ON hl.habit_id = h.id
                    WHERE hl.habit_id = ?
                    ORDER BY hl.created_at DESC
                    LIMIT 500;
                    """,
                    (selected_habit_id,)
                ).fetchall()
            
            for c in completions:
                events.append({
                    'type': 'completion',
                    'datetime': str(c["created_at"]),
                    'habit': str(c["habit_name"]),
                    'content': f"✓ Completed {c['habit_name']} on {c['day']}"
                })
            
            # Get notes
            if selected_habit_id == -1:
                notes = conn.execute(
                    """
                    SELECT n.created_at, n.content, h.name as habit_name
                    FROM notes n
                    JOIN habits h ON n.habit_id = h.id
                    ORDER BY n.created_at DESC
                    LIMIT 500;
                    """
                ).fetchall()
            else:
                notes = conn.execute(
                    """
                    SELECT n.created_at, n.content, h.name as habit_name
                    FROM notes n
                    JOIN habits h ON n.habit_id = h.id
                    WHERE n.habit_id = ?
                    ORDER BY n.created_at DESC
                    LIMIT 500;
                    """,
                    (selected_habit_id,)
                ).fetchall()
            
            for n in notes:
                content = str(n["content"])
                if search_text and search_text not in content.lower():
                    continue
                
                events.append({
                    'type': 'note',
                    'datetime': str(n["created_at"]),
                    'habit': str(n["habit_name"]),
                    'content': f"📝 Note on {n['habit_name']}: {content}"
                })
            
            conn.close()
            
            # Sort events by datetime (newest first)
            events.sort(key=lambda x: x['datetime'], reverse=True)
            
            # Add to timeline
    # ui_history.py - Replace the refresh method's item coloring part
    # Replace this section in the refresh method:

            # Add to timeline
            for event in events[:100]:  # Limit to 100 most recent
                item_text = f"[{event['datetime']}] {event['content']}"
                item = QListWidgetItem(item_text)
                
                # Better color handling for both light and dark modes
                palette = self.palette()
                is_dark = palette.color(QPalette.Window).lightness() < 128
                
                if event['type'] == 'completion':
                    if is_dark:
                        item.setForeground(QColor(57, 211, 83))  # Green for dark mode
                    else:
                        item.setForeground(QColor(0, 128, 0))  # Dark green for light mode
                else:
                    if is_dark:
                        item.setForeground(QColor(88, 166, 255))  # Blue for dark mode
                    else:
                        item.setForeground(QColor(0, 0, 255))  # Blue for light mode
                
                self.timeline_list.addItem(item)
            
            if self.timeline_list.count() == 0:
                self.timeline_list.addItem("No history to display")