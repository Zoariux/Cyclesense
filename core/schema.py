SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id                INTEGER PRIMARY KEY AUTOINCREMENT,
  display_name           TEXT NOT NULL,
  created_at             TEXT NOT NULL,
  pin_hash               TEXT NOT NULL,
  twofa_enabled          INTEGER NOT NULL DEFAULT 0,
  twofa_type             TEXT NOT NULL DEFAULT 'none',
  totp_secret_encrypted  BLOB,
  email_encrypted        BLOB,
  failed_login_attempts  INTEGER DEFAULT 0,
  locked_until           TEXT,
  
  -- New profile fields
  full_name              TEXT,
  age                    INTEGER,
  period_start_age       INTEGER,
  profile_complete       INTEGER DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_display_name ON users(display_name);

CREATE TABLE IF NOT EXISTS cycles (
  cycle_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL,
  start_date   TEXT NOT NULL,
  end_date     TEXT,
  period_length INTEGER,
  cycle_length  INTEGER,
  created_at   TEXT NOT NULL,
  updated_at   TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cycles_user_start ON cycles(user_id, start_date);

CREATE TABLE IF NOT EXISTS daily_logs (
  log_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL,
  cycle_id     INTEGER,
  log_date     TEXT NOT NULL,
  flow_level   TEXT NOT NULL,
  mood         INTEGER NOT NULL CHECK(mood BETWEEN 1 AND 5),
  pain_level   INTEGER,
  stress       INTEGER,
  sleep_hours  REAL,
  energy_level INTEGER,
  symptoms_json TEXT NOT NULL DEFAULT '[]',
  notes        TEXT,
  created_at   TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY(cycle_id) REFERENCES cycles(cycle_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_logs_user_date ON daily_logs(user_id, log_date);

CREATE TABLE IF NOT EXISTS settings (
  user_id                     INTEGER PRIMARY KEY,
  privacy_mode                INTEGER NOT NULL DEFAULT 0,
  theme_mode                  TEXT NOT NULL DEFAULT 'auto',
  inactivity_timeout_minutes  INTEGER NOT NULL DEFAULT 10,
  
  -- Reminder settings
  enable_period_reminders     INTEGER DEFAULT 1,
  enable_ovulation_reminders  INTEGER DEFAULT 1,
  enable_selfcare_nudges      INTEGER DEFAULT 1,
  enable_daily_log_reminders  INTEGER DEFAULT 1,
  reminder_days_before        INTEGER DEFAULT 3,
  
  created_at                  TEXT NOT NULL,
  updated_at                  TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_logs_user_date_unique ON daily_logs(user_id, log_date);
CREATE INDEX IF NOT EXISTS idx_cycles_user_id ON cycles(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_cycle_id ON daily_logs(cycle_id);
"""