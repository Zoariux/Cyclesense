from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, date, timedelta
from typing import Any, Iterator, Optional

from core.schema import SCHEMA_SQL

# Get the main project folder
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "app.db")

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()

@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()

# ---------- Users ----------
def count_users() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM users;").fetchone()
        return int(row["c"])

def list_users() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id, display_name, created_at, twofa_enabled, twofa_type FROM users ORDER BY user_id ASC;"
        ).fetchall()
        return [dict(r) for r in rows]

def create_user(display_name: str, pin_hash: str) -> int:
    now = _utc_now_iso()
    with get_conn() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO users(display_name, created_at, pin_hash, twofa_enabled, twofa_type)
                VALUES(?, ?, ?, 0, 'none');
                """,
                (display_name, now, pin_hash),
            )
            user_id = int(cur.lastrowid)
            conn.execute(
                """
                INSERT INTO settings(user_id, privacy_mode, theme_mode, inactivity_timeout_minutes, created_at, updated_at)
                VALUES(?, 0, 'auto', 10, ?, ?);
                """,
                (user_id, now, now),
            )
            conn.commit()
            return user_id
        except Exception as e:
            conn.rollback()
            raise Exception(f"Could not create user: {e}")

def get_user(user_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT u.*, s.privacy_mode, s.theme_mode, s.inactivity_timeout_minutes
            FROM users u
            JOIN settings s ON s.user_id = u.user_id
            WHERE u.user_id = ?;
            """,
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

def update_user_2fa(
    user_id: int,
    enabled: bool,
    twofa_type: str,
    totp_secret_encrypted: bytes | None = None,
    email_encrypted: bytes | None = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET twofa_enabled = ?, twofa_type = ?, totp_secret_encrypted = ?, email_encrypted = ?
            WHERE user_id = ?;
            """,
            (1 if enabled else 0, twofa_type, totp_secret_encrypted, email_encrypted, user_id),
        )
        conn.commit()

def update_privacy_mode(user_id: int, privacy_mode: bool) -> None:
    now = _utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE settings
            SET privacy_mode = ?, updated_at = ?
            WHERE user_id = ?;
            """,
            (1 if privacy_mode else 0, now, user_id),
        )
        conn.commit()

def update_inactivity_timeout(user_id: int, minutes: int) -> None:
    now = _utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE settings
            SET inactivity_timeout_minutes = ?, updated_at = ?
            WHERE user_id = ?;
            """,
            (minutes, now, user_id),
        )
        conn.commit()

def increment_failed_login(user_id: int) -> None:
    """Count failed login attempts and lock account after 5 tries"""
    with get_conn() as conn:
        user = conn.execute(
            "SELECT failed_login_attempts FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        attempts = user["failed_login_attempts"] + 1
        
        if attempts >= 5:
            from datetime import datetime, timedelta, timezone
            locked_time = datetime.now(timezone.utc) + timedelta(minutes=15)
            conn.execute(
                "UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE user_id = ?",
                (attempts, locked_time.isoformat(), user_id)
            )
        else:
            conn.execute(
                "UPDATE users SET failed_login_attempts = ? WHERE user_id = ?",
                (attempts, user_id)
            )
        conn.commit()

def reset_failed_login(user_id: int) -> None:
    """Reset login attempts when user logs in successfully"""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

def is_account_locked(user_id: int) -> bool:
    """Check if account is locked"""
    with get_conn() as conn:
        user = conn.execute(
            "SELECT locked_until FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if not user or not user["locked_until"]:
            return False
        
        from datetime import datetime, timezone
        locked_until = datetime.fromisoformat(user["locked_until"])
        return datetime.now(timezone.utc) < locked_until


# ---------- Cycles ----------
def create_cycle(user_id: int, start_date: str, end_date: str = None) -> int:
    """Create a new menstrual cycle"""
    now = _utc_now_iso()
    period_length = None
    
    if end_date:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        period_length = (end - start).days + 1
    
    with get_conn() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO cycles(user_id, start_date, end_date, period_length, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?);
                """,
                (user_id, start_date, end_date, period_length, now, now),
            )
            cycle_id = int(cur.lastrowid)
            
            # Recalculate cycle lengths for all previous cycles
            _recalculate_cycle_lengths(conn, user_id)
            
            conn.commit()
            return cycle_id
        except Exception as e:
            conn.rollback()
            raise Exception(f"Could not create cycle: {e}")

def update_cycle(cycle_id: int, start_date: str = None, end_date: str = None) -> None:
    """Update an existing cycle - triggers recalculation"""
    now = _utc_now_iso()
    
    with get_conn() as conn:
        try:
            # Get current cycle data
            cycle = conn.execute("SELECT * FROM cycles WHERE cycle_id = ?", (cycle_id,)).fetchone()
            if not cycle:
                raise ValueError("Cycle not found")
            
            # Use provided dates or keep existing
            new_start = start_date if start_date else cycle["start_date"]
            new_end = end_date if end_date else cycle["end_date"]
            
            # Calculate period length if end date exists
            period_length = None
            if new_end:
                start = date.fromisoformat(new_start)
                end = date.fromisoformat(new_end)
                period_length = (end - start).days + 1
            
            # Update cycle
            conn.execute(
                """
                UPDATE cycles
                SET start_date = ?, end_date = ?, period_length = ?, updated_at = ?
                WHERE cycle_id = ?;
                """,
                (new_start, new_end, period_length, now, cycle_id),
            )
            
            # Recalculate all cycle lengths
            _recalculate_cycle_lengths(conn, cycle["user_id"])
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Could not update cycle: {e}")

def _recalculate_cycle_lengths(conn: sqlite3.Connection, user_id: int) -> None:
    """Recalculate cycle_length for all cycles based on gaps between periods"""
    cycles = conn.execute(
        "SELECT cycle_id, start_date FROM cycles WHERE user_id = ? ORDER BY start_date ASC",
        (user_id,)
    ).fetchall()
    
    for i in range(len(cycles) - 1):
        current_start = date.fromisoformat(cycles[i]["start_date"])
        next_start = date.fromisoformat(cycles[i + 1]["start_date"])
        cycle_length = (next_start - current_start).days
        
        conn.execute(
            "UPDATE cycles SET cycle_length = ? WHERE cycle_id = ?",
            (cycle_length, cycles[i]["cycle_id"])
        )
    
    # Last cycle has no cycle_length (no next period yet)
    if cycles:
        conn.execute(
            "UPDATE cycles SET cycle_length = NULL WHERE cycle_id = ?",
            (cycles[-1]["cycle_id"],)
        )

def get_user_cycles(user_id: int, limit: int = None) -> list[dict[str, Any]]:
    """Get all cycles for a user, most recent first"""
    with get_conn() as conn:
        query = "SELECT * FROM cycles WHERE user_id = ? ORDER BY start_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        rows = conn.execute(query, (user_id,)).fetchall()
        return [dict(r) for r in rows]

def get_cycle(cycle_id: int) -> Optional[dict[str, Any]]:
    """Get a specific cycle by ID"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM cycles WHERE cycle_id = ?", (cycle_id,)).fetchone()
        return dict(row) if row else None

def get_current_cycle(user_id: int) -> Optional[dict[str, Any]]:
    """Get the most recent cycle (likely current)"""
    cycles = get_user_cycles(user_id, limit=1)
    return cycles[0] if cycles else None

def delete_cycle(cycle_id: int) -> None:
    """Delete a cycle and recalculate remaining cycles"""
    with get_conn() as conn:
        try:
            # Get user_id before deleting
            cycle = conn.execute("SELECT user_id FROM cycles WHERE cycle_id = ?", (cycle_id,)).fetchone()
            if not cycle:
                return
            
            user_id = cycle["user_id"]
            
            # Delete cycle (will cascade delete daily_logs)
            conn.execute("DELETE FROM cycles WHERE cycle_id = ?", (cycle_id,))
            
            # Recalculate remaining cycles
            _recalculate_cycle_lengths(conn, user_id)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Could not delete cycle: {e}")


# ---------- Daily Logs ----------
def create_daily_log(
    user_id: int,
    log_date: str,
    flow_level: str,
    mood: int,
    pain_level: int = None,
    stress: int = None,
    sleep_hours: float = None,
    symptoms: list[str] = None
) -> int:
    """Create a daily log entry"""
    import json
    now = _utc_now_iso()
    symptoms_json = json.dumps(symptoms if symptoms else [])
    
    # Find associated cycle
    cycle_id = None
    with get_conn() as conn:
        cycle = conn.execute(
            """
            SELECT cycle_id FROM cycles 
            WHERE user_id = ? AND start_date <= ? 
            ORDER BY start_date DESC LIMIT 1
            """,
            (user_id, log_date)
        ).fetchone()
        
        if cycle:
            cycle_id = cycle["cycle_id"]
    
    with get_conn() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO daily_logs(
                    user_id, cycle_id, log_date, flow_level, mood, 
                    pain_level, stress, sleep_hours, symptoms_json, created_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (user_id, cycle_id, log_date, flow_level, mood, 
                 pain_level, stress, sleep_hours, symptoms_json, now),
            )
            log_id = int(cur.lastrowid)
            conn.commit()
            return log_id
        except sqlite3.IntegrityError:
            # Log already exists for this date
            conn.rollback()
            raise ValueError(f"Log already exists for {log_date}")
        except Exception as e:
            conn.rollback()
            raise Exception(f"Could not create log: {e}")

def update_daily_log(
    log_id: int,
    flow_level: str = None,
    mood: int = None,
    pain_level: int = None,
    stress: int = None,
    sleep_hours: float = None,
    symptoms: list[str] = None
) -> None:
    """Update an existing daily log"""
    import json
    
    with get_conn() as conn:
        # Build dynamic update query
        updates = []
        params = []
        
        if flow_level is not None:
            updates.append("flow_level = ?")
            params.append(flow_level)
        if mood is not None:
            updates.append("mood = ?")
            params.append(mood)
        if pain_level is not None:
            updates.append("pain_level = ?")
            params.append(pain_level)
        if stress is not None:
            updates.append("stress = ?")
            params.append(stress)
        if sleep_hours is not None:
            updates.append("sleep_hours = ?")
            params.append(sleep_hours)
        if symptoms is not None:
            updates.append("symptoms_json = ?")
            params.append(json.dumps(symptoms))
        
        if not updates:
            return
        
        params.append(log_id)
        query = f"UPDATE daily_logs SET {', '.join(updates)} WHERE log_id = ?"
        
        conn.execute(query, params)
        conn.commit()

def get_daily_logs(user_id: int, start_date: str = None, end_date: str = None) -> list[dict[str, Any]]:
    """Get daily logs for a user within date range"""
    with get_conn() as conn:
        if start_date and end_date:
            rows = conn.execute(
                """
                SELECT * FROM daily_logs 
                WHERE user_id = ? AND log_date BETWEEN ? AND ?
                ORDER BY log_date DESC
                """,
                (user_id, start_date, end_date)
            ).fetchall()
        elif start_date:
            rows = conn.execute(
                """
                SELECT * FROM daily_logs 
                WHERE user_id = ? AND log_date >= ?
                ORDER BY log_date DESC
                """,
                (user_id, start_date)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM daily_logs WHERE user_id = ? ORDER BY log_date DESC",
                (user_id,)
            ).fetchall()
        
        return [dict(r) for r in rows]

def get_daily_log_by_date(user_id: int, log_date: str) -> Optional[dict[str, Any]]:
    """Get log for a specific date"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM daily_logs WHERE user_id = ? AND log_date = ?",
            (user_id, log_date)
        ).fetchone()
        return dict(row) if row else None