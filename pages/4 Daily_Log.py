import streamlit as st
from datetime import date
import json

from core.state import require_auth
from core.db import (
    create_daily_log, update_daily_log, get_daily_log_by_date,
    get_daily_logs, create_cycle, update_cycle, get_current_cycle
)

require_auth()

# Professional CSS matching main app
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #fef5fb 0%, #fff8fc 50%, #fef6fb 100%);
    }
    
    h1 {
        font-family: 'Playfair Display', serif !important;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #d63384 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .subtitle {
        font-size: 1rem;
        color: #6c4a5e !important;
        font-weight: 500;
        margin-bottom: 2rem;
    }
    
    .card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        border: 2px solid #ffd6e8;
        box-shadow: 0 4px 20px rgba(214, 51, 132, 0.08);
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #e91e63 0%, #c2185b 100%) !important;
        color: white !important;
        border-radius: 16px !important;
        font-weight: 600 !important;
        box-shadow: 0 6px 20px rgba(233, 30, 99, 0.3) !important;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #d63384;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #ffd6e8;
    }
    
    /* Form Elements */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: white !important;
        border: 2px solid #e8b4d4 !important;
        border-radius: 12px !important;
        color: #2d1b28 !important;
        font-weight: 500 !important;
    }
    
    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stMultiSelect > label {
        color: #4a2e42 !important;
        font-weight: 600 !important;
    }
    
    /* Radio Buttons */
    .stRadio > label {
        color: #4a2e42 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    
    /* Fix Radio Button Option Text */
    .stRadio > div[role="radiogroup"] label p {
        color: #2d1b28 !important;
        font-weight: 500 !important;
    }
    
    /* Fix Caption Text */
    .stCaptionContainer p,
    div[data-testid="stCaptionContainer"] p {
        color: #6c4a5e !important;
        font-weight: 500 !important;
    }
    
    /* Fix ALL form text visibility */
    .stMarkdown p {
        color: #2d1b28 !important;
    }
    
    /* Fix any remaining invisible text in forms */
    div[data-testid="stForm"] p,
    div[data-testid="stForm"] label,
    div[data-testid="stForm"] span {
        color: #2d1b28 !important;
    }
    
    /* Slider */
    .stSlider > label {
        color: #4a2e42 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([6, 1])

with col1:
    st.title("📝 Daily Log")
    st.markdown('<p class="subtitle">Track your cycle data</p>', unsafe_allow_html=True)

with col2:
    if st.button("🏠 Home"):
        st.switch_page("app.py")

user_id = st.session_state.get("selected_user_id")

# Date selector
col1, col2 = st.columns([3, 1])

with col1:
    log_date = st.date_input(
        "📅 Select Date",
        value=date.today(),
        max_value=date.today()
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Today", use_container_width=True):
        log_date = date.today()
        st.rerun()

log_date_str = log_date.isoformat()
existing_log = get_daily_log_by_date(user_id, log_date_str)

st.divider()

# Period Management
st.markdown('<div class="section-header">🩸 Period Tracking</div>', unsafe_allow_html=True)

current_cycle = get_current_cycle(user_id)

col1, col2 = st.columns(2)

with col1:
    if st.button("🔴 Start New Period", use_container_width=True):
        cycle_id = create_cycle(user_id, log_date_str)
        st.success(f"✅ New cycle started on {log_date_str}")
        st.rerun()

with col2:
    if current_cycle and not current_cycle.get("end_date"):
        if st.button("🛑 End Current Period", use_container_width=True):
            update_cycle(current_cycle["cycle_id"], end_date=log_date_str)
            st.success(f"✅ Period ended on {log_date_str}")
            st.rerun()

if current_cycle:
    st.markdown(f"""
    <div class="card">
        <p style="color: #2d1b28; font-weight: 600; margin: 0;">
            <strong>Current Cycle:</strong> Started {current_cycle['start_date']}
        </p>
        <p style="color: #6c4a5e; margin: 0.5rem 0 0 0;">
            <strong>Status:</strong> {'Ongoing' if not current_cycle.get('end_date') else f"Ended {current_cycle['end_date']}"}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Daily Log Form
st.markdown('<div class="section-header">📊 Daily Log</div>', unsafe_allow_html=True)

with st.form("daily_log_form"):
    st.markdown("#### 🩸 Flow Level")
    flow_level = st.radio(
        "Flow",
        ["none", "light", "medium", "heavy"],
        horizontal=True,
        index=["none", "light", "medium", "heavy"].index(existing_log.get("flow_level", "none")) if existing_log else 0,
        label_visibility="collapsed"
    )
    
    flow_desc = {
        "none": "No menstrual flow",
        "light": "Light spotting",
        "medium": "Regular flow",
        "heavy": "Heavy flow"
    }
    st.caption(f"ℹ️ {flow_desc[flow_level]}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### 😊 Mood")
    mood = st.select_slider(
        "How are you feeling?",
        options=[1, 2, 3, 4, 5],
        value=existing_log.get("mood", 3) if existing_log else 3,
        format_func=lambda x: ["😢 Terrible", "😟 Bad", "😐 Okay", "🙂 Good", "😄 Great"][x-1]
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🤕 Pain Level")
        pain_level = st.select_slider(
            "Cramps or pain?",
            options=[0, 1, 2, 3, 4, 5],
            value=existing_log.get("pain_level", 0) if existing_log else 0,
            format_func=lambda x: ["None", "Minimal", "Mild", "Moderate", "Severe", "Extreme"][x]
        )
        pain_level = pain_level if pain_level > 0 else None
    
    with col2:
        st.markdown("#### 😰 Stress Level")
        stress = st.select_slider(
            "How stressed?",
            options=[0, 1, 2, 3, 4, 5],
            value=existing_log.get("stress", 0) if existing_log else 0,
            format_func=lambda x: ["None", "Very Low", "Low", "Moderate", "High", "Very High"][x]
        )
        stress = stress if stress > 0 else None
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### 😴 Sleep Hours")
    sleep_hours = st.number_input(
        "Hours slept last night",
        min_value=0.0,
        max_value=16.0,
        step=0.5,
        value=float(existing_log.get("sleep_hours", 0.0)) if existing_log and existing_log.get("sleep_hours") else 0.0
    )
    sleep_hours = sleep_hours if sleep_hours > 0 else None
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### 🩺 Symptoms")
    all_symptoms = [
        "Headache", "Backache", "Breast Tenderness", "Bloating",
        "Fatigue", "Nausea", "Acne", "Food Cravings",
        "Irritability", "Anxiety", "Cramps", "Diarrhea"
    ]
    
    existing_symptoms = []
    if existing_log and existing_log.get("symptoms_json"):
        try:
            existing_symptoms = json.loads(existing_log["symptoms_json"])
        except:
            pass
    
    symptoms = st.multiselect(
        "Select symptoms",
        all_symptoms,
        default=existing_symptoms
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        submitted = st.form_submit_button("💾 Save Log", use_container_width=True)
    
    if submitted:
        try:
            if existing_log:
                update_daily_log(
                    log_id=existing_log["log_id"],
                    flow_level=flow_level,
                    mood=mood,
                    pain_level=pain_level,
                    stress=stress,
                    sleep_hours=sleep_hours,
                    symptoms=symptoms
                )
                st.success(f"✅ Log updated for {log_date_str}")
            else:
                create_daily_log(
                    user_id=user_id,
                    log_date=log_date_str,
                    flow_level=flow_level,
                    mood=mood,
                    pain_level=pain_level,
                    stress=stress,
                    sleep_hours=sleep_hours,
                    symptoms=symptoms
                )
                st.success(f"✅ Log created for {log_date_str}")
            
            st.balloons()
            
        except ValueError as e:
            st.error(f"❌ {str(e)}")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

st.divider()

# Recent Logs
st.markdown('<div class="section-header">📅 Recent Logs</div>', unsafe_allow_html=True)

recent_logs = get_daily_logs(user_id)[:7]

if recent_logs:
    for log in recent_logs:
        log_date_obj = date.fromisoformat(log["log_date"])
        
        try:
            symptoms_list = json.loads(log["symptoms_json"])
            symptoms_str = ", ".join(symptoms_list) if symptoms_list else "None"
        except:
            symptoms_str = "None"
        
        mood_emoji = ["😢", "😟", "😐", "🙂", "😄"][log["mood"] - 1]
        
        st.markdown(f"""
        <div class="card">
            <h4 style="color: #d63384; margin: 0 0 0.5rem 0;">{log_date_obj.strftime("%A, %b %d")}</h4>
            <p style="color: #2d1b28; font-weight: 600; margin: 0.25rem 0;">
                Flow: {log['flow_level'].title()} | Mood: {mood_emoji}
            </p>
            <p style="color: #6c4a5e; margin: 0.25rem 0;">
                Symptoms: {symptoms_str}
            </p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("📝 No logs yet. Start tracking today!")