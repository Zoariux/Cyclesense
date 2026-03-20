from __future__ import annotations

from datetime import date, timedelta

from core.db import get_conn, create_user
from core.security import hash_pin

def seed_demo_user() -> int:
    """
    Creates a demo user + a few cycles/logs (non-real).
    Returns new user_id.
    """
    user_id = create_user("Demo User", hash_pin("1234"))

    # Minimal demo data (cycles + logs) - safe synthetic
    today = date.today()
    starts = [today - timedelta(days=90), today - timedelta(days=60), today - timedelta(days=30)]
    ends = [s + timedelta(days=5) for s in starts]

    with get_conn() as conn:
        for s, e in zip(starts, ends):
            now = "demo"
            cur = conn.execute(
                """
                INSERT INTO cycles(user_id, start_date, end_date, period_length, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?);
                """,
                (user_id, s.isoformat(), e.isoformat(), 6, now, now),
            )
            cycle_id = int(cur.lastrowid)

            # Add a few daily logs with flow tapering
            for i in range(6):
                d = s + timedelta(days=i)
                flow = "heavy" if i in (0, 1) else ("medium" if i in (2, 3) else "light")
                conn.execute(
                    """
                    INSERT INTO daily_logs(user_id, cycle_id, log_date, flow_level, mood, symptoms_json, created_at)
                    VALUES(?, ?, ?, ?, ?, '[]', ?);
                    """,
                    (user_id, cycle_id, d.isoformat(), flow, 3, now),
                )
        conn.commit()

    return user_id
