from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st

from core.db import get_user, update_privacy_mode

def ensure_session_defaults() -> None:
    st.session_state.setdefault("selected_user_id", None)
    st.session_state.setdefault("display_name", None)
    st.session_state.setdefault("is_authed", False)
    st.session_state.setdefault("last_active_utc", datetime.now(timezone.utc))
    st.session_state.setdefault("privacy_mode", False)
    st.session_state.setdefault("inactivity_timeout_minutes", 10)

    # 2FA email OTP demo storage (session-only)
    st.session_state.setdefault("email_otp_code", None)
    st.session_state.setdefault("email_otp_expires_utc", None)

def touch_activity() -> None:
    st.session_state["last_active_utc"] = datetime.now(timezone.utc)

def logout(reason: str = "Logged out.") -> None:
    st.session_state["is_authed"] = False
    st.session_state["display_name"] = None
    st.session_state["selected_user_id"] = None
    st.session_state["email_otp_code"] = None
    st.session_state["email_otp_expires_utc"] = None
    st.warning(reason)

def enforce_inactivity_logout() -> None:
    # called on every page load
    if not st.session_state.get("is_authed"):
        return

    last_active: datetime = st.session_state.get("last_active_utc")
    timeout_min = int(st.session_state.get("inactivity_timeout_minutes", 10))
    if datetime.now(timezone.utc) - last_active > timedelta(minutes=timeout_min):
        logout("Session expired due to inactivity. Please log in again.")

def load_user_into_session(user_id: int) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    st.session_state["selected_user_id"] = user_id
    st.session_state["display_name"] = user["display_name"]
    st.session_state["privacy_mode"] = bool(user["privacy_mode"])
    st.session_state["inactivity_timeout_minutes"] = int(user["inactivity_timeout_minutes"])
    return True

def toggle_privacy_mode() -> None:
    if not st.session_state.get("is_authed"):
        return
    user_id = st.session_state["selected_user_id"]
    new_val = not bool(st.session_state.get("privacy_mode"))
    st.session_state["privacy_mode"] = new_val
    update_privacy_mode(user_id, new_val)

def require_auth() -> None:
    if not st.session_state.get("is_authed"):
        st.info("Please log in to access this page.")
        st.stop()
    touch_activity()
