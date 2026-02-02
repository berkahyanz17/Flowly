# models.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta, datetime
from typing import List, Optional, Tuple, Dict
from src.db import get_conn, get_current_datetime

@dataclass(frozen=True)
class Habit:
    id: int
    name: str
    created_at: str

@dataclass(frozen=True)
class Note:
    id: int
    habit_id: int
    content: str
    created_at: str

def today_str() -> str:
    return date.today().isoformat()

def days_back(n: int) -> List[str]:
    # returns list of ISO days, oldest -> newest, inclusive of today
    start = date.today() - timedelta(days=n-1)
    return [(start + timedelta(days=i)).isoformat() for i in range(n)]

# Habits
def list_habits() -> List[Habit]:
    conn = get_conn()
    rows = conn.execute("SELECT id, name, created_at FROM habits ORDER BY name;").fetchall()
    conn.close()
    return [Habit(int(r["id"]), str(r["name"]), str(r["created_at"])) for r in rows]

def create_habit(name: str) -> Habit:
    name = name.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO habits(name, created_at) VALUES (?, ?);", (name, get_current_datetime()))
    conn.commit()
    row = conn.execute("SELECT id, name, created_at FROM habits WHERE id=?;", (cur.lastrowid,)).fetchone()
    conn.close()
    return Habit(int(row["id"]), str(row["name"]), str(row["created_at"]))

def delete_habit(habit_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM habits WHERE id=?;", (habit_id,))
    conn.commit()
    conn.close()

# Completion logs
def is_done_on_day(habit_id: int, day: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM habit_logs WHERE habit_id=? AND day=?;",
        (habit_id, day),
    ).fetchone()
    conn.close()
    return row is not None

def mark_done(habit_id: int, day: Optional[str] = None) -> None:
    day = day or today_str()
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO habit_logs(habit_id, day, created_at) VALUES (?, ?, ?);",
        (habit_id, day, get_current_datetime()),
    )
    conn.commit()
    conn.close()

def unmark_done(habit_id: int, day: Optional[str] = None) -> None:
    day = day or today_str()
    conn = get_conn()
    conn.execute("DELETE FROM habit_logs WHERE habit_id=? AND day=?;", (habit_id, day))
    conn.commit()
    conn.close()

def get_done_days_in_range(habit_id: int, start_day: str, end_day: str) -> List[str]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT day FROM habit_logs
        WHERE habit_id=? AND day BETWEEN ? AND ?
        ORDER BY day;
        """,
        (habit_id, start_day, end_day),
    ).fetchall()
    conn.close()
    return [str(r["day"]) for r in rows]

def current_streak(habit_id: int) -> int:
    # streak up to today (consecutive days done ending today)
    done = set(get_done_days_in_range(habit_id, "0001-01-01", today_str()))
    streak = 0
    d = date.today()
    while d.isoformat() in done:
        streak += 1
        d = d - timedelta(days=1)
    return streak

# Notes
def list_notes(habit_id: int) -> List[Note]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, habit_id, content, created_at FROM notes WHERE habit_id=? ORDER BY created_at DESC;",
        (habit_id,),
    ).fetchall()
    conn.close()
    return [Note(int(r["id"]), int(r["habit_id"]), str(r["content"]), str(r["created_at"])) for r in rows]

def add_note(habit_id: int, content: str) -> Note:
    content = content.strip()
    if not content:
        raise ValueError("Note cannot be empty.")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO notes(habit_id, content, created_at) VALUES (?, ?, ?);", (habit_id, content, get_current_datetime()))
    conn.commit()
    row = conn.execute(
        "SELECT id, habit_id, content, created_at FROM notes WHERE id=?;",
        (cur.lastrowid,),
    ).fetchone()
    conn.close()
    return Note(int(row["id"]), int(row["habit_id"]), str(row["content"]), str(row["created_at"]))

def delete_note(note_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM notes WHERE id=?;", (note_id,))
    conn.commit()
    conn.close()

# Stats
def stats_for_range(days: int) -> Dict[str, float | int]:
    # overall stats across all habits for last N days (including today)
    habit_list = list_habits()
    if not habit_list:
        return {"habits": 0, "days": days, "done": 0, "total": 0, "rate": 0.0}

    days_list = days_back(days)
    start_day, end_day = days_list[0], days_list[-1]

    conn = get_conn()
    done_rows = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM habit_logs
        WHERE day BETWEEN ? AND ?;
        """,
        (start_day, end_day),
    ).fetchone()
    conn.close()

    done = int(done_rows["c"])
    total = len(habit_list) * len(days_list)
    rate = (done / total) if total else 0.0

    return {
        "habits": len(habit_list),
        "days": len(days_list),
        "done": done,
        "total": total,
        "rate": rate,
    }

def per_habit_last_n_days(days: int) -> List[Tuple[Habit, int, float]]:
    # returns [(habit, done_count, rate)] for last N days
    hs = list_habits()
    if not hs:
        return []

    days_list = days_back(days)
    start_day, end_day = days_list[0], days_list[-1]

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT habit_id, COUNT(*) AS c
        FROM habit_logs
        WHERE day BETWEEN ? AND ?
        GROUP BY habit_id;
        """,
        (start_day, end_day),
    ).fetchall()
    conn.close()

    done_map = {int(r["habit_id"]): int(r["c"]) for r in rows}
    out: List[Tuple[Habit, int, float]] = []
    for h in hs:
        dc = done_map.get(h.id, 0)
        rate = dc / len(days_list)
        out.append((h, dc, rate))
    # sort by rate desc then name
    out.sort(key=lambda t: (-t[2], t[0].name.lower()))
    return out