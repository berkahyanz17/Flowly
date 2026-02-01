# ui_habits.py
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QMessageBox, QScrollArea, QFrame, QSizePolicy
)

from models import (
    list_habits, create_habit, delete_habit,
    is_done_on_day, mark_done, unmark_done,
    current_streak, today_str
)


class HabitRow(QFrame):
    def __init__(self, habit_id: int, name: str, created_at: str, done_today: bool, streak: int,
                 on_toggle_done, on_delete):
        super().__init__()
        self.habit_id = habit_id

        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setObjectName("HabitRow")

        name_lbl = QLabel(name)
        name_lbl.setObjectName("HabitName")
        name_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        meta_lbl = QLabel(f"Streak: {streak}    Created: {created_at}")
        meta_lbl.setObjectName("Meta")

        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(4)
        left.addWidget(name_lbl)
        left.addWidget(meta_lbl)

        self.done_btn = QPushButton("Committed" if done_today else "Commit task")
        self.done_btn.setCheckable(True)
        self.done_btn.setChecked(done_today)
        self.done_btn.clicked.connect(lambda: on_toggle_done(self.habit_id))

        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda: on_delete(self.habit_id))

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(8)
        right.addWidget(self.done_btn)
        right.addWidget(del_btn)
        right.addStretch(1)

        row = QHBoxLayout()
        row.setContentsMargins(10, 10, 10, 10)
        row.setSpacing(12)
        row.addLayout(left, 1)
        row.addLayout(right)

        self.setLayout(row)


class HabitsTab(QWidget):
    data_changed = Signal()

    def __init__(self):
        super().__init__()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Contribute new habit... (e.g., Read 10 pages)")
        self.name_input.returnPressed.connect(self._add_habit)

        self.add_btn = QPushButton("Add Commit")
        self.add_btn.clicked.connect(self._add_habit)

        add_row = QHBoxLayout()
        add_row.addWidget(self.name_input, 1)
        add_row.addWidget(self.add_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search habits...")
        self.search_input.textChanged.connect(self.refresh)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        filter_row.addWidget(self.search_input, 1)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        self.list_container.setLayout(self.list_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.list_container)

        self.empty_lbl = QLabel("No habits yet. Add one above.")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #666; padding: 24px;")

        root = QVBoxLayout()
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)
        root.addLayout(add_row)
        root.addLayout(filter_row)
        root.addWidget(scroll, 1)
        root.addWidget(self.empty_lbl)

        self.setLayout(root)

        self._habits_cache = []

    def _clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def refresh(self):
        self._habits_cache = list_habits()
        q = self.search_input.text().strip().lower()

        # Filter out "General" habit
        habits = [h for h in self._habits_cache if h.name != "General"]
        
        if q:
            habits = [h for h in habits if q in h.name.lower()]

        self._clear_list()

        if not habits:
            self.empty_lbl.setVisible(True)
            return

        self.empty_lbl.setVisible(False)

        for h in habits:
            done = is_done_on_day(h.id, today_str())
            streak = current_streak(h.id)

            row = HabitRow(
                habit_id=h.id,
                name=h.name,
                created_at=h.created_at,
                done_today=done,
                streak=streak,
                on_toggle_done=self._toggle_done,
                on_delete=self._delete,
            )
            row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.list_layout.addWidget(row)

        self.list_layout.addStretch(1)

    def _add_habit(self):
        name = self.name_input.text().strip()
        # Prevent creating another "General" habit
        if name.lower() == "general":
            QMessageBox.warning(self, "Error", "Cannot create a habit named 'General' - it's reserved for standalone notes.")
            return
        try:
            create_habit(name)
            self.name_input.clear()
            self.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _toggle_done(self, habit_id: int):
        try:
            if is_done_on_day(habit_id, today_str()):
                unmark_done(habit_id, today_str())
            else:
                mark_done(habit_id, today_str())
            self.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _delete(self, habit_id: int):
        if QMessageBox.question(self, "Confirm", "Delete this habit and its data?") != QMessageBox.Yes:
            return
        try:
            delete_habit(habit_id)
            self.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))