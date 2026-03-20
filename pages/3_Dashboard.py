import streamlit as st
from datetime import date

from core.state import require_auth, toggle_privacy_mode
from services.theme import apply_phase_theme

require_auth()

# Modern page config with custom CSS
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    /* Global styles */
    .main {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Header styling */
    h1 {
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem !important;
    }
    
    /* Phase card */
    .phase-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 2px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .phase-title {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .phase-emoji {
        font-size: 2.5rem;
    }
    
    .phase-description {
        font-size: 1.1rem;
        line-height: 1.6;
        margin: 1rem 0;
        color: #555;
    }
    
    .phase-tips {
        background: rgba(255, 255, 255, 0.5);
        border-radius: 15px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .tip-item {
        margin: 0.5rem 0;
        padding: 0.5rem;
        border-left: 3px solid #667eea;
        padding-left: 1rem;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 600 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    /* Emoji decorations */
    .emoji-large {
        font-size: 3rem;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("✨ Your Cycle Dashboard")

# Phase selector with better UI
phase = st.selectbox(
    "🌙 Current Phase",
    ["period", "follicular", "ovulation", "luteal"],
    index=1,
    help="Select your current cycle phase to see personalized insights!"
)
apply_phase_theme(phase)

# Phase information dictionary
PHASE_INFO = {
    "period": {
        "emoji": "🩸",
        "name": "Period (Menstruation)",
        "tagline": "Your body's monthly reset",
        "description": """
        This is when your uterus sheds its lining because no pregnancy occurred. 
        It typically lasts 3-7 days. You might feel tired, crampy, or emotional - and that's totally normal!
        """,
        "what_happens": [
            "🔴 Uterine lining sheds through your vagina",
            "📉 Estrogen and progesterone levels are at their lowest",
            "🌡️ Body temperature drops slightly",
            "💧 You lose about 2-3 tablespoons of blood (seems like more!)"
        ],
        "tips": [
            "💊 Ibuprofen or heating pad can help with cramps",
            "🛀 Warm baths are super soothing",
            "🥤 Stay hydrated - drink lots of water",
            "😴 Rest when you need to, your body is working hard!",
            "🍫 Cravings are real - moderate treats are okay!"
        ],
        "mood": "You might feel tired, emotional, or crampy. Be kind to yourself! 💕"
    },
    "follicular": {
        "emoji": "🌱",
        "name": "Follicular Phase",
        "tagline": "Fresh start energy!",
        "description": """
        Right after your period ends, this phase is all about new beginnings! 
        Your body is preparing to release an egg. You'll probably feel more energetic and social.
        """,
        "what_happens": [
            "🥚 Your ovaries start preparing an egg for release",
            "📈 Estrogen levels gradually increase",
            "💪 Energy levels rise - you feel great!",
            "🧠 Brain feels sharper and more focused"
        ],
        "tips": [
            "🏃‍♀️ Great time for exercise - you have lots of energy!",
            "📚 Perfect for starting new projects or studying",
            "👯‍♀️ Social activities feel easier and more fun",
            "🥗 Your body absorbs nutrients well - eat healthy!",
            "✨ Try new things - you're feeling confident!"
        ],
        "mood": "Energetic, confident, and ready to take on the world! 🚀"
    },
    "ovulation": {
        "emoji": "✨",
        "name": "Ovulation Phase",
        "tagline": "Peak power time!",
        "description": """
        This is when your ovary releases an egg - usually around day 14 of your cycle. 
        You're at your most fertile, and you might feel super confident and attractive!
        """,
        "what_happens": [
            "🥚 An egg is released from your ovary",
            "📊 Estrogen peaks, testosterone rises too",
            "🌡️ Body temperature increases slightly (0.5-1°F)",
            "💫 This is your most fertile window (if that matters to you)"
        ],
        "tips": [
            "💃 You might feel extra confident - embrace it!",
            "🗣️ Communication comes easier - good for presentations",
            "⚡ Peak energy - tackle difficult tasks",
            "🎨 Creative thinking is at its best",
            "💦 Some notice clear, stretchy discharge - totally normal!"
        ],
        "mood": "Confident, energetic, and absolutely glowing! ✨"
    },
    "luteal": {
        "emoji": "🌙",
        "name": "Luteal Phase",
        "tagline": "Winding down, cozy vibes",
        "description": """
        After ovulation, your body prepares for either pregnancy or your next period. 
        You might start feeling more introverted and need extra self-care. PMS symptoms 
        might show up in the last few days.
        """,
        "what_happens": [
            "📉 Progesterone rises then falls",
            "🌡️ Body temperature stays slightly elevated",
            "💧 You might retain some water (feel bloated)",
            "🍕 Cravings can increase - especially for carbs or salt"
        ],
        "tips": [
            "🛋️ More me-time is okay - embrace the cozy vibes",
            "🥨 Salty/sweet cravings? Have balanced portions",
            "😌 Gentle exercise like yoga or walking",
            "📝 Journal your feelings - great for PMS management",
            "💤 Prioritize sleep - you might need more rest",
            "🫂 Reach out to friends if you feel down"
        ],
        "mood": "More introverted, maybe a bit moody - totally normal before your period! 🌙"
    }
}

current_phase = PHASE_INFO[phase]

# Beautiful phase card
st.markdown(f"""
<div class="phase-card">
    <div class="phase-title">
        <span class="phase-emoji">{current_phase['emoji']}</span>
        <span>{current_phase['name']}</span>
    </div>
    <p style="font-size: 1.2rem; font-style: italic; color: #667eea; margin: 0.5rem 0;">
        {current_phase['tagline']}
    </p>
    <p class="phase-description">
        {current_phase['description']}
    </p>
</div>
""", unsafe_allow_html=True)

# Metrics row with better styling
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📅 Today", date.today().strftime("%b %d, %Y"))

with col2:
    st.metric("🌸 Current Phase", phase.title())

with col3:
    privacy_mode = bool(st.session_state.get("privacy_mode"))
    privacy_status = "ON 🕶️" if privacy_mode else "OFF 👀"
    st.metric("Privacy Mode", privacy_status)

# Privacy toggle button
if st.button("🔒 Toggle Privacy Mode"):
    toggle_privacy_mode()
    st.toast("Privacy mode toggled!", icon="🕶️")
    st.rerun()

st.divider()

# What's happening in your body
with st.expander("🔬 What's Happening in Your Body Right Now", expanded=True):
    for item in current_phase['what_happens']:
        st.markdown(f"**{item}**")
        st.markdown("")

st.divider()

# Tips section
with st.expander("💡 Tips & Self-Care for This Phase", expanded=True):
    st.markdown("### Here's how to feel your best:")
    for tip in current_phase['tips']:
        st.markdown(f"""
        <div class="tip-item">
            {tip}
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Mood & feelings
st.markdown(f"""
<div class="info-box">
    <h3>😊 How You Might Feel</h3>
    <p style="font-size: 1.1rem; margin-top: 1rem;">
        {current_phase['mood']}
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# Coming soon section
st.markdown("""
<div class="info-box">
    <h3>🚀 Coming Soon to Your Dashboard</h3>
    <p style="margin-top: 1rem;">We're building some awesome features for you:</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    📊 **Cycle Tracking**
    - See your cycle history
    - Predict next period
    - Track symptoms over time
    
    📝 **Daily Logging**
    - Mood tracker
    - Symptom journal
    - Flow intensity
    """)

with col2:
    st.markdown("""
    📈 **Insights & Trends**
    - Cycle length patterns
    - Common symptoms
    - Energy level graphs
    
    🔔 **Smart Reminders**
    - Period predictions
    - Ovulation alerts
    - Self-care nudges
    """)

st.divider()

# Educational footer
st.markdown("""
<div style="text-align: center; padding: 2rem; opacity: 0.7;">
    <p style="font-size: 0.9rem;">
        💜 Remember: Every body is different! If something doesn't feel right, 
        talk to a trusted adult or healthcare provider.
    </p>
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">
        Your cycle info stays private and local on your device 🔒
    </p>
</div>
""", unsafe_allow_html=True)