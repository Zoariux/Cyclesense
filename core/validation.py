from __future__ import annotations

import re
from datetime import date

FLOW_LEVELS = {"none", "light", "medium", "heavy"}

def validate_display_name(name: str) -> str:
    name = name.strip()
    if len(name) < 2:
        raise ValueError("Display name must be at least 2 characters.")
    if len(name) > 32:
        raise ValueError("Display name must be 32 characters or fewer.")
    if not re.match(r"^[A-Za-z0-9 _.-]+$", name):
        raise ValueError("Display name contains invalid characters.")
    return name

def validate_pin(pin: str) -> str:
    pin = pin.strip()
    if not (4 <= len(pin) <= 8) or not pin.isdigit():
        raise ValueError("PIN must be 4–8 digits.")
    return pin

def validate_date_order(start: date, end: date) -> None:
    if end < start:
        raise ValueError("End date cannot be before start date.")
