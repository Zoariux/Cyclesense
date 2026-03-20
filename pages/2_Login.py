import streamlit as st
import time

from core.db import get_user, is_account_locked, increment_failed_login, reset_failed_login
from core.security import verify_pin
from core.state import ensure_session_defaults, touch_activity
from core.validation import validate_pin

ensure_session_defaults()

# Modern CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #fef6fb 0%, #fff0f8 25%, #fef3fb 50%, #fff5fa 75%, #fef6fc 100%);
    }
    
    h1 {
        font-family: 'Playfair Display', serif !important;
        background: linear-gradient(135deg, #ff6b9d 0%, #c44569 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 3rem;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 8px 32px rgba(255, 192, 203, 0.15);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #ff6b9d 0%, #c44569 100%) !important;
        color: white !important;
        border-radius: 16px !important;
        font-weight: 500 !important;
        padding: 0.75rem 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔐 Login")

user_id = st.session_state.get("selected_user_id")

if not user_id:
    st.markdown("""
    <div class="glass-card" style="text-align: center;">
        <h3 style="color: #c44569;">👋 Welcome!</h3>
        <p style="color: #9b7c8f; margin-top: 1rem;">
            Please create or select a profile first
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Go to Profile Page", use_container_width=True):
        st.switch_page("pages/1_Profile.py")
    
    st.stop()

user = get_user(user_id)

if not user:
    st.error("Profile not found")
    st.stop()

# Check if account locked
if is_account_locked(user_id):
    st.markdown("""
    <div class="glass-card" style="text-align: center;">
        <h3 style="color: #ff6b6b;">🔒 Account Locked</h3>
        <p style="color: #9b7c8f; margin-top: 1rem;">
            Too many failed attempts. Please wait 15 minutes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Login Form
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(f"""
    <div class="glass-card" style="text-align: center;">
        <h2 style="color: #c44569; margin-bottom: 2rem;">
            👤 {user['display_name']}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("pin_login"):
        pin = st.text_input(
            "Enter PIN",
            type="password",
            placeholder="••••",
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        do_login = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if do_login:
            # Validate PIN
            try:
                pin = validate_pin(pin)
            except Exception as e:
                st.error(f"❌ {str(e)}")
                st.stop()
            
            # Timing attack protection
            start = time.time()
            pin = pin[:72]
            pin_valid = verify_pin(pin, user["pin_hash"])
            elapsed = time.time() - start
            time.sleep(max(0, 0.3 - elapsed))
            
            if not pin_valid:
                increment_failed_login(user_id)
                st.error("❌ Invalid PIN")
                st.stop()
            
            # Success!
            reset_failed_login(user_id)
            
            st.session_state["is_authed"] = True
            st.session_state["display_name"] = user["display_name"]
            
            st.success("✅ Login successful!")
            st.balloons()
            touch_activity()
            
            # Auto-redirect to main dashboard
            time.sleep(1)
            st.switch_page("app.py")