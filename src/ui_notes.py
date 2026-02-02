# ui_notes.py
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QAbstractItemView
)
from PySide6.QtGui import QTextCursor
from src.models import list_habits, list_notes, add_note, delete_note, create_habit, Habit, Note
from src.db import get_conn

class NotesTab(QWidget):
    data_changed = Signal()

    def __init__(self):
        super().__init__()

        self.habit_combo = QComboBox()
        self.habit_combo.currentIndexChanged.connect(self.refresh)

        top = QHBoxLayout()
        top.addWidget(QLabel("Habit:"))
        top.addWidget(self.habit_combo)
        top.addStretch(1)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Write a note...")
        self.editor.textChanged.connect(self._update_char_count)

        # Character counter
        self.char_count_label = QLabel("0/150")
        self.char_count_label.setAlignment(Qt.AlignLeft)

        editor_layout = QVBoxLayout()
        editor_layout.setSpacing(4)
        editor_layout.addWidget(self.editor)
        editor_layout.addWidget(self.char_count_label)

        self.add_btn = QPushButton("Add Note")
        self.add_btn.clicked.connect(self._add_note)

        self.listw = QListWidget()
        self.listw.itemDoubleClicked.connect(self._delete_selected)
        
        # Enable smooth scrolling
        self.listw.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.listw.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addLayout(editor_layout)
        layout.addWidget(self.add_btn)
        layout.addWidget(QLabel("Double-click a note to delete it"))
        layout.addWidget(self.listw)
        self.setLayout(layout)

        self._habits_cache = []
        self._notes_cache = []  # aligned with list items
        self._general_habit_id = None

    def _update_char_count(self):
        """Update character count and enforce 150 character limit"""
        text = self.editor.toPlainText()
        char_count = len(text)
        
        # Enforce 150 character limit
        if char_count > 150:
            # Truncate to 150 characters
            self.editor.blockSignals(True)  # Prevent recursive calls
            truncated_text = text[:150]
            self.editor.setPlainText(truncated_text)
            
            # Move cursor to end
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.editor.setTextCursor(cursor)
            self.editor.blockSignals(False)
            char_count = 150
        
        # Update label
        self.char_count_label.setText(f"{char_count}/150")
        
        # Change color based on limit
        if char_count >= 150:
            self.char_count_label.setStyleSheet("color: red; font-weight: bold;")
        elif char_count >= 120:
            self.char_count_label.setStyleSheet("color: orange;")
        else:
            self.char_count_label.setStyleSheet("")

    def _ensure_general_habit(self) -> int:
        """Ensure 'General' habit exists, create if needed. Returns habit_id."""
        conn = get_conn()
        row = conn.execute(
            "SELECT id FROM habits WHERE name = 'General';"
        ).fetchone()
        conn.close()
        
        if row:
            return int(row["id"])
        else:
            # Create the General habit
            general = create_habit("General")
            return general.id

    def refresh(self):
        # Ensure General habit exists
        self._general_habit_id = self._ensure_general_habit()
        
        # refresh combo, but keep selection if possible
        current_id = self.current_habit_id()
        self._habits_cache = list_habits()

        self.habit_combo.blockSignals(True)
        self.habit_combo.clear()
        
        # Add "All" option as the first item
        self.habit_combo.addItem("All", -1)
        
        for h in self._habits_cache:
            self.habit_combo.addItem(h.name, h.id)
        
        # restore selection
        if current_id is not None:
            idx = self.habit_combo.findData(current_id)
            if idx >= 0:
                self.habit_combo.setCurrentIndex(idx)
        else:
            # Default to "All" if no previous selection
            self.habit_combo.setCurrentIndex(0)
            
        self.habit_combo.blockSignals(False)

        hid = self.current_habit_id()
        self.listw.clear()
        self._notes_cache = []

        if hid == -1:
            # Show all notes from all habits, sorted by date (newest first)
            self._show_all_notes()
        else:
            # Show notes for specific habit
            if hid is None:
                return
            
            notes = list_notes(hid)
            for n in notes:
                item = QListWidgetItem(f"[{n.created_at}] {n.content}")
                self.listw.addItem(item)
                self._notes_cache.append(n)

    def _show_all_notes(self):
        """Fetch and display all notes from all habits, sorted by created_at DESC"""
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT n.id, n.habit_id, n.content, n.created_at, h.name as habit_name
            FROM notes n
            JOIN habits h ON n.habit_id = h.id
            ORDER BY n.created_at DESC;
            """
        ).fetchall()
        conn.close()
        
        for r in rows:
            note = Note(
                id=int(r["id"]),
                habit_id=int(r["habit_id"]),
                content=str(r["content"]),
                created_at=str(r["created_at"])
            )
            habit_name = str(r["habit_name"])
            
            # Display with habit name prefix
            item = QListWidgetItem(f"[{note.created_at}] ({habit_name}) {note.content}")
            self.listw.addItem(item)
            self._notes_cache.append(note)

    def current_habit_id(self):
        if self.habit_combo.count() == 0:
            return None
        hid = self.habit_combo.currentData()
        return int(hid) if hid is not None else None

    def _add_note(self):
        hid = self.current_habit_id()
        
        # If "All" is selected, use the General habit
        if hid == -1:
            hid = self._general_habit_id
        
        if hid is None:
            QMessageBox.warning(self, "Error", "Unable to add note.")
            return
            
        try:
            add_note(hid, self.editor.toPlainText())
            self.editor.clear()
            self.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _delete_selected(self, item: QListWidgetItem):
        row = self.listw.row(item)
        if row < 0 or row >= len(self._notes_cache):
            return
        note = self._notes_cache[row]
        if QMessageBox.question(self, "Confirm", "Delete this note?") != QMessageBox.Yes:
            return
        try:
            delete_note(note.id)
            self.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
