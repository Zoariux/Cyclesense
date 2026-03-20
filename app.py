import os
from pathlib import Path
from datetime import date

import plotly.graph_objects as go
import streamlit as st

from core.db import get_user, init_db
from core.state import ensure_session_defaults, enforce_inactivity_logout

st.set_page_config(
    page_title="CycleSense",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    .stApp {
        background:
            radial-gradient(circle at 20% 50%, rgba(255, 192, 203, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 182, 193, 0.04) 0%, transparent 50%),
            linear-gradient(135deg, #fef5fb 0%, #fff8fc 50%, #fef6fb 100%);
    }

    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 2px solid #ffd6e8 !important;
        box-shadow: 4px 0 20px rgba(233, 30, 99, 0.08) !important;
    }

    [data-testid="stSidebar"] * {
        color: #2d1b28 !important;
        font-weight: 500 !important;
    }

    h1 {
        font-family: 'Playfair Display', serif !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        color: #d63384 !important;
        margin-bottom: 0.25rem !important;
        text-shadow: 0 2px 4px rgba(214, 51, 132, 0.1);
    }

    .subtitle {
        font-size: 1.1rem;
        color: #6c4a5e;
        font-weight: 500;
        margin-bottom: 2rem;
    }

    .card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        border: 2px solid #ffd6e8;
        box-shadow: 0 4px 20px rgba(214, 51, 132, 0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        height: 100%;
    }

    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(214, 51, 132, 0.12);
        border-color: #ffadd2;
    }

    .card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255, 192, 203, 0.05) 0%, transparent 70%);
        pointer-events: none;
    }

    .phase-banner {
        background: white;
        border: 3px solid #e91e63;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        margin: 1.5rem 0 2rem 0;
        box-shadow: 0 8px 30px rgba(233, 30, 99, 0.15);
        position: relative;
        overflow: hidden;
    }

    .phase-banner::before {
        content: '🌸';
        position: absolute;
        font-size: 8rem;
        opacity: 0.05;
        top: -20px;
        right: -20px;
        pointer-events: none;
    }

    .phase-title {
        font-size: 2rem;
        font-weight: 700;
        color: #d63384;
        margin: 0;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 2px solid #ffd6e8;
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 4px 16px rgba(214, 51, 132, 0.08);
    }

    [data-testid="stMetricLabel"] {
        color: #6c4a5e !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    [data-testid="stMetricValue"] {
        color: #e91e63 !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #e91e63 0%, #c2185b 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1.02rem !important;
        box-shadow: 0 6px 20px rgba(233, 30, 99, 0.3) !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #d81b60 0%, #ad1457 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(233, 30, 99, 0.4) !important;
    }

    .section-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #d63384;
        margin: 2.2rem 0 1.2rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid #ffd6e8;
    }

    .emoji-decoration {
        font-size: 3rem;
        opacity: 0.15;
        position: absolute;
        pointer-events: none;
    }

    .info-card {
        background: #fff0f6;
        border-left: 4px solid #e91e63;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #5c3548;
        font-weight: 500;
    }

    .pill {
        display: inline-block;
        background: #fff0f6;
        color: #d63384;
        border: 1px solid #ffd6e8;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    .phase-list {
        margin: 0.5rem 0 0 0;
        padding-left: 1.2rem;
        color: #5c3548;
        line-height: 1.8;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

PHASE_CONTENT = {
    "period": {
        "emoji": "🩸",
        "title": "Period Phase",
        "tagline": "Your body's monthly reset",
        "body": "Your uterus is shedding its lining because pregnancy did not occur. Estrogen and progesterone are at their lowest, which can affect pain sensitivity, mood, and energy.",
        "feelings": "You may feel tired, crampy, sensitive, low-energy, or more emotional than usual. Many people also want more rest and comfort during this phase.",
        "tips": [
            "Use heat, rest, and hydration to support your body.",
            "Choose iron-rich meals and don't feel guilty about slowing down.",
            "Gentle movement can help, but rest is valid too.",
            "Track cramps, flow, and fatigue so patterns become easier to spot.",
        ],
        "explanation": "Lower hormone levels plus uterine contractions can explain cramps, fatigue, and mood shifts. This phase is often a reset period for both the body and mind.",
    },
    "follicular": {
        "emoji": "🌱",
        "title": "Follicular Phase",
        "tagline": "Fresh start energy",
        "body": "Your body is preparing an egg for release. Estrogen is rising, and many people notice improving energy, mental clarity, and motivation.",
        "feelings": "You may feel lighter, more focused, more social, and more open to exercise or starting new things.",
        "tips": [
            "This can be a great time for workouts, planning, and learning.",
            "Use higher energy days for tasks that require focus.",
            "Support your body with balanced meals and hydration.",
            "Notice how your mood and motivation shift after your period ends.",
        ],
        "explanation": "As estrogen rises, the brain and body often feel sharper and more energized. That's why this phase can feel like a reset or a new beginning.",
    },
    "ovulation": {
        "emoji": "✨",
        "title": "Ovulation Phase",
        "tagline": "Peak power time",
        "body": "An egg is released around ovulation. Estrogen peaks and luteinizing hormone surges, which can influence confidence, body awareness, and energy.",
        "feelings": "You may feel energetic, social, confident, or notice mild pelvic discomfort and changes in discharge.",
        "tips": [
            "Use this phase for demanding tasks if your energy is high.",
            "Hydrate well and pay attention to body signals.",
            "Some people notice slight cramping or temperature changes.",
            "Keep logging symptoms so your fertile-window predictions improve over time.",
        ],
        "explanation": "This is often the highest-energy window of the cycle. Hormone peaks can affect mood, communication, and physical sensations in noticeable ways.",
    },
    "luteal": {
        "emoji": "🌙",
        "title": "Luteal Phase",
        "tagline": "Winding down, cozy vibes",
        "body": "After ovulation, progesterone rises to prepare for a possible pregnancy. If pregnancy does not occur, hormones drop toward the end of this phase.",
        "feelings": "You may feel calmer at first, then later notice bloating, cravings, irritability, fatigue, lower social energy, or PMS-like symptoms.",
        "tips": [
            "Prioritize sleep and recovery if your energy dips.",
            "Gentle movement, magnesium-rich foods, and hydration can help.",
            "Reduce pressure on yourself if focus feels harder.",
            "Track mood, cravings, and bloating so PMS patterns are easier to manage.",
        ],
        "explanation": "The hormone drop before a period can explain PMS symptoms like cravings, irritability, breast tenderness, and lower energy. Extra self-care often helps here.",
    },
}


def main() -> None:
    init_db()
    ensure_session_defaults()
    enforce_inactivity_logout()

    if not st.session_state.get("is_authed"):
        show_welcome_page()
    else:
        show_main_dashboard()


def _switch_to_existing_page(candidates: list[str]) -> None:
    base_dir = Path(__file__).resolve().parent
    for candidate in candidates:
        if (base_dir / candidate).exists():
            st.switch_page(candidate)
            return
    st.error(f"Couldn't find any of these pages: {', '.join(candidates)}")


def _load_prediction_functions():
    try:
        from services.predictions import (
            calculate_cycle_stats,
            days_until_next_period,
            get_current_phase,
            predict_next_period,
        )
        return calculate_cycle_stats, days_until_next_period, get_current_phase, predict_next_period
    except Exception:
        from predictions import (
            calculate_cycle_stats,
            days_until_next_period,
            get_current_phase,
            predict_next_period,
        )
        return calculate_cycle_stats, days_until_next_period, get_current_phase, predict_next_period


def show_welcome_page() -> None:
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown(
            """
            <div style="font-size: 6rem; text-align: center; margin-top: 2rem;">🌸</div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <h1 style="margin-top: 2.5rem;">CycleSense</h1>
            <p class="subtitle">Your personal cycle companion</p>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">✨</div>
            <h2 style="color: #d63384; font-family: 'Playfair Display', serif; margin-bottom: 1rem;">
                Welcome to CycleSense
            </h2>
            <p style="color: #6c4a5e; font-size: 1.15rem; line-height: 1.7; max-width: 600px; margin: 0 auto;">
                Track your cycle, understand your body, and feel empowered with AI-powered predictions
                and personalized insights. Your data stays private, always.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎀 Create Profile", use_container_width=True):
            _switch_to_existing_page(["pages/1_Profile.py", "1_Profile.py"])

    with col2:
        if st.button("🔐 Login", use_container_width=True):
            _switch_to_existing_page(["pages/2_Login.py", "2_Login.py"])

    with col3:
        if st.button("🎮 Try Demo", use_container_width=True):
            _switch_to_existing_page(["pages/1_Profile.py", "1_Profile.py"])

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">✨ What You Can Do</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    features = [
        ("📊", "Track & Predict", "Know when your next period is coming with AI-powered predictions and cycle insights"),
        ("💜", "Understand Your Body", "Learn what's happening in each phase with personalized tips and educational content"),
        ("🔒", "Private by Design", "Your cycle history stays on your app setup and is used to generate your personal insights"),
    ]

    for col, (emoji, title, desc) in zip((col1, col2, col3), features):
        with col:
            st.markdown(
                f"""
                <div class="card" style="text-align: center; min-height: 280px;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">{emoji}</div>
                    <h3 style="color: #d63384; margin-bottom: 1rem;">{title}</h3>
                    <p style="color: #6c4a5e; line-height: 1.6;">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_phase_banner(phase_key: str) -> None:
    phase = PHASE_CONTENT.get(phase_key, PHASE_CONTENT["follicular"])
    st.markdown(
        f"""
        <div class="phase-banner">
            <div style="font-size: 4rem; margin-bottom: 0.5rem;">{phase['emoji']}</div>
            <div class="phase-title">{phase['title']}</div>
            <p style="color: #6c4a5e; margin-top: 0.5rem; font-size: 1.05rem;">{phase['tagline']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_phase_insights(phase_key: str) -> None:
    phase = PHASE_CONTENT.get(phase_key, PHASE_CONTENT["follicular"])

    st.markdown('<div class="section-header">💜 Your Phase Insights</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="card">
                <div class="pill">What’s going on in your body</div>
                <h3 style="color:#d63384; margin-top:0;">{phase['title']}</h3>
                <p style="color:#5c3548; line-height:1.8;">{phase['body']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="card">
                <div class="pill">How you might feel</div>
                <h3 style="color:#d63384; margin-top:0;">Common feelings in this phase</h3>
                <p style="color:#5c3548; line-height:1.8;">{phase['feelings']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col3, col4 = st.columns(2)

    with col3:
        tips_html = "".join(f"<li>{tip}</li>" for tip in phase["tips"])
        st.markdown(
            f"""
            <div class="card">
                <div class="pill">Tips for this phase</div>
                <h3 style="color:#d63384; margin-top:0;">Ways to support yourself</h3>
                <ul class="phase-list">{tips_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="card">
                <div class="pill">Why this happens</div>
                <h3 style="color:#d63384; margin-top:0;">Cycle phase explanation</h3>
                <p style="color:#5c3548; line-height:1.8;">{phase['explanation']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_cycle_chart(user_id: int, stats) -> None:
    st.markdown('<div class="section-header">📊 Your Cycle Overview</div>', unsafe_allow_html=True)

    try:
        from core.db import get_user_cycles
        cycles = get_user_cycles(user_id, limit=6)
    except Exception:
        cycles = []

    if cycles and len(cycles) >= 2:
        import pandas as pd

        complete_cycles = [c for c in cycles if c.get("cycle_length")]
        if complete_cycles:
            df = pd.DataFrame(
                [
                    {"Date": c["start_date"], "Cycle Length": c["cycle_length"]}
                    for c in reversed(complete_cycles)
                ]
            )
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(df))),
                    y=df["Cycle Length"],
                    mode="lines+markers",
                    name="Cycle Length",
                    line=dict(color="#e91e63", width=4, shape="spline"),
                    marker=dict(size=14, color="#e91e63", line=dict(width=2, color="white")),
                    fill="tozeroy",
                    fillcolor="rgba(233, 30, 99, 0.1)",
                )
            )

            if stats:
                fig.add_hline(
                    y=stats.avg_cycle_length,
                    line_dash="dash",
                    line_width=3,
                    line_color="#c2185b",
                    annotation_text=f"Average: {stats.avg_cycle_length} days",
                    annotation_position="right",
                    annotation_font_size=14,
                    annotation_font_color="#c2185b",
                )

            fig.update_layout(
                height=350,
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                xaxis=dict(
                    showgrid=False,
                    title="",
                    tickmode="array",
                    tickvals=list(range(len(df))),
                    ticktext=[f"Cycle {i+1}" for i in range(len(df))],
                    tickfont=dict(size=12, color="#6c4a5e", family="Inter"),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255, 214, 232, 0.5)",
                    title="Days",
                    tickfont=dict(size=12, color="#6c4a5e"),
                ),
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
            return

    st.markdown(
        """
        <div class="info-card">
            <div style="font-size: 3rem; text-align: center; margin-bottom: 1rem;">📝</div>
            <p style="text-align: center; font-size: 1.1rem; margin: 0;">
                <strong>Start tracking to see your cycle chart!</strong><br>
                Log your first period to begin visualizing your patterns.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_main_dashboard() -> None:
    user_id = st.session_state.get("selected_user_id")
    user = get_user(user_id) if user_id else None

    col1, col2 = st.columns([4, 1])
    with col1:
        display_name = st.session_state.get("display_name") or (user.get("name") if isinstance(user, dict) else "there") or "there"
        st.markdown(
            f"""
            <div style="position: relative;">
                <span class="emoji-decoration" style="left: -50px; top: -10px;">🌸</span>
                <h1>Hello, {display_name}</h1>
                <p class="subtitle">Here’s what your cycle may be telling you today.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            from core.state import logout
            logout("Logged out successfully")
            st.rerun()

    try:
        calculate_cycle_stats, days_until_next_period, get_current_phase, predict_next_period = _load_prediction_functions()
        prediction = predict_next_period(user_id)
        phase_key = get_current_phase(user_id)
        stats = calculate_cycle_stats(user_id)
    except Exception:
        prediction = None
        phase_key = "follicular"
        stats = None

    _render_phase_banner(phase_key)

    days_left = None
    if user_id:
        try:
            _, days_until_next_period, _, _ = _load_prediction_functions()
            days_left = days_until_next_period(user_id)
        except Exception:
            days_left = None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Today", date.today().strftime("%b %d, %Y"))
    with col2:
        st.metric("🌸 Current Phase", PHASE_CONTENT.get(phase_key, PHASE_CONTENT['follicular'])['title'].replace(' Phase', ''))
    with col3:
        next_text = f"{days_left} days" if isinstance(days_left, int) and days_left > 0 else ("Today" if days_left == 0 else "Not enough data")
        st.metric("🩸 Next Period", next_text)
    with col4:
        confidence = f"{prediction.confidence_score}%" if prediction else "Building"
        st.metric("🎯 Prediction Confidence", confidence)

    _render_phase_insights(phase_key)

    if prediction or stats:
        st.markdown('<div class="section-header">🔎 Cycle Snapshot</div>', unsafe_allow_html=True)
        snap1, snap2, snap3 = st.columns(3)
        with snap1:
            fertile_text = (
                f"{prediction.fertile_window_start.strftime('%b %d')} - {prediction.fertile_window_end.strftime('%b %d')}"
                if prediction else "Need more logs"
            )
            st.metric("🥚 Fertile Window", fertile_text)
        with snap2:
            avg_cycle = f"{stats.avg_cycle_length} days" if stats else "Need more logs"
            st.metric("📈 Average Cycle", avg_cycle)
        with snap3:
            stability = f"{stats.stability_score}%" if stats else "Need more logs"
            st.metric("💪 Stability", stability)

    _render_cycle_chart(user_id, stats)

    st.markdown('<div class="section-header">🎯 Quick Actions</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    cards = [
        (col1, "📝", "Daily Log", "Track your flow, mood, and symptoms", "Open Daily Log", ["pages/4_Daily_Log.py", "pages/4 Daily_Log.py", "4_Daily_Log.py", "4 Daily_Log.py"]),
        (col2, "📊", "Analytics", "View your cycle patterns and insights", "Open Analytics", ["pages/Analytics.py", "pages/5_Analytics.py", "Analytics.py", "5_Analytics.py"]),
        (col3, "🤖", "AI Assistant", "Ask health questions anytime", "Chat with AI", ["pages/AI_Assistant.py", "pages/6_AI_Assistant.py", "AI_Assistant.py", "6_AI_Assistant.py"]),
    ]

    for idx, (col, emoji, title, desc, button_label, candidates) in enumerate(cards, start=1):
        with col:
            st.markdown(
                f"""
                <div class="card" style="text-align: center; padding: 1.5rem; min-height: 220px;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">{emoji}</div>
                    <h4 style="color: #d63384; margin-bottom: 0.5rem;">{title}</h4>
                    <p style="color: #6c4a5e; font-size: 0.95rem; margin-bottom: 1rem;">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(button_label, key=f"action_{idx}", use_container_width=True):
                _switch_to_existing_page(candidates)


if __name__ == "__main__":
    main()