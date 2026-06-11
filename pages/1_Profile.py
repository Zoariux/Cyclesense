import streamlit as st

from core.db import count_users, create_user, list_users, get_user, get_conn
from core.security import hash_pin
from core.state import ensure_session_defaults, load_user_into_session
from core.validation import validate_display_name, validate_pin
from core.seed import seed_demo_user

ensure_session_defaults()

# Professional UI/UX Design with Better Contrast
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
    
    /* Background */
    .stApp {
        background: linear-gradient(135deg, #fef5fb 0%, #fff8fc 50%, #fef6fb 100%);
    }
    
    /* Main Title - High Contrast */
    h1 {
        font-family: 'Playfair Display', serif !important;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #d63384 !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 2px 4px rgba(214, 51, 132, 0.1);
    }
    
    /* Subtitle - Better Contrast */
    .subtitle {
        font-size: 1rem;
        color: #6c4a5e !important;
        font-weight: 500;
        margin-bottom: 2rem;
    }
    
    /* Profile Cards - Enhanced Design */
    .profile-card {
        background: white;
        border-radius: 20px;
        padding: 1.75rem;
        margin: 1rem 0;
        border: 2px solid #ffd6e8;
        box-shadow: 0 4px 20px rgba(214, 51, 132, 0.08);
        transition: all 0.3s ease;
    }
    
    .profile-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(214, 51, 132, 0.12);
        border-color: #ffadd2;
    }
    
    /* Profile Name - High Contrast */
    .profile-name {
        font-size: 1.25rem;
        font-weight: 600;
        color: #2d1b28 !important;
        margin-bottom: 0.5rem;
    }
    
    /* Profile Meta - Better Contrast */
    .profile-meta {
        font-size: 0.875rem;
        color: #8b6f81 !important;
        font-weight: 500;
    }
    
    /* Buttons - High Contrast */
    .stButton > button {
        background: linear-gradient(135deg, #e91e63 0%, #c2185b 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 12px rgba(233, 30, 99, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #d81b60 0%, #ad1457 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(233, 30, 99, 0.4) !important;
    }
    
    /* Input Fields - High Contrast */
    .stTextInput > div > div > input {
        background: white !important;
        border: 2px solid #e8b4d4 !important;
        border-radius: 12px !important;
        padding: 0.875rem !important;
        font-size: 1rem !important;
        color: #2d1b28 !important;
        font-weight: 500 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #e91e63 !important;
        box-shadow: 0 0 0 3px rgba(233, 30, 99, 0.1) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #b89aae !important;
        font-weight: 400 !important;
    }
    
    /* Labels - High Contrast */
    .stTextInput > label, .stNumberInput > label {
        color: #4a2e42 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Form Container */
    .form-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        border: 2px solid #ffd6e8;
        box-shadow: 0 8px 30px rgba(214, 51, 132, 0.08);
        margin: 1.5rem 0;
    }
    
    /* Info Box - Better Contrast */
    .info-box {
        background: #fff0f6;
        border-left: 4px solid #e91e63;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: #5c3548 !important;
        font-weight: 500;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #d63384;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #ffd6e8;
    }
    
    /* Icon Styling */
    .profile-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #ff6b9d 0%, #c44569 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
    }
    
    /* Number Input */
    .stNumberInput > div > div > input {
        background: white !important;
        border: 2px solid #e8b4d4 !important;
        border-radius: 12px !important;
        padding: 0.875rem !important;
        color: #2d1b28 !important;
        font-weight: 500 !important;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #ffd6e8, transparent);
        margin: 2.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header with Icon
col_icon, col_title = st.columns([1, 10])

with col_icon:
    st.markdown("""
    <div class="profile-icon">👤</div>
    """, unsafe_allow_html=True)

with col_title:
    st.title("Profile")
    st.markdown('<p class="subtitle">Manage your personal profiles</p>', unsafe_allow_html=True)

users = list_users()
max_users = 1

# Check if user needs to complete profile
if st.session_state.get("selected_user_id"):
    user = get_user(st.session_state["selected_user_id"])
    
    if user and not user.get("profile_complete"):
        st.markdown('<div class="section-header">📝 Complete Your Profile</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
            💜 <strong>Help us personalize your experience!</strong> This information helps us provide better predictions and age-appropriate content.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
        with st.form("complete_profile"):
            full_name = st.text_input(
                "Full Name (Optional)",
                placeholder="Your full name",
                help="We'll keep this private. Only you can see it."
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                age = st.number_input(
                    "Your Age",
                    min_value=10,
                    max_value=100,
                    value=None,
                    help="Helps us provide age-appropriate insights"
                )
            
            with col2:
                period_start_age = st.number_input(
                    "Age of First Period (Optional)",
                    min_value=8,
                    max_value=20,
                    value=None,
                    help="Helps improve cycle predictions"
                )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submitted = st.form_submit_button("💾 Save & Continue", use_container_width=True)
            
            if submitted:
                try:
                    with get_conn() as conn:
                        conn.execute(
                            """
                            UPDATE users 
                            SET full_name = ?, age = ?, period_start_age = ?, profile_complete = 1
                            WHERE user_id = ?
                            """,
                            (full_name if full_name else None, 
                             age if age else None, 
                             period_start_age if period_start_age else None,
                             user["user_id"])
                        )
                        conn.commit()
                    
                    st.success("✅ Profile completed successfully!")
                    st.balloons()
                    
                    import time
                    time.sleep(1)
                    st.switch_page("pages/2_Login.py")
                    
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

# Existing Profiles Section
st.markdown('<div class="section-header">🎭 Your Profiles</div>', unsafe_allow_html=True)

if users:
    st.markdown(f"""
    <div class="info-box">
        📊 You have <strong>{len(users)} of {max_users}</strong> profiles. Each profile tracks its own cycle data separately.
    </div>
    """, unsafe_allow_html=True)
    
    for user in users:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            <div class="profile-card">
                <div class="profile-name">👤 {user['display_name']}</div>
                <div class="profile-meta">
                    📅 Created: {user['created_at'][:10]} • 
                    🔐 2FA: {user['twofa_type'].upper() if user['twofa_type'] != 'none' else 'Disabled'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Select →", key=f"select_{user['user_id']}", use_container_width=True):
                load_user_into_session(user['user_id'])
                st.success(f"✅ Selected {user['display_name']}!")
                
                import time
                time.sleep(0.5)
                st.switch_page("pages/2_Login.py")
else:
    st.markdown("""
    <div class="info-box">
        🌸 <strong>No profiles yet!</strong> Create your first profile below to start tracking your cycle.
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Create New Profile Section
st.markdown('<div class="section-header">✨ Create New Profile</div>', unsafe_allow_html=True)

if count_users() >= max_users:
    st.markdown(f"""
    <div class="info-box" style="background: #fff3cd; border-color: #ffc107;">
        ⚠️ <strong>Profile limit reached!</strong> You've created the maximum of {max_users} profiles. 
        Delete an existing profile to create a new one.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    with st.form("create_profile"):
        display_name = st.text_input(
            "Display Name",
            placeholder="e.g., Sarah, Emma, Alex...",
            help="Choose a name that makes you feel comfortable (2-32 characters)"
        )
        
        pin = st.text_input(
            "Create Your PIN",
            type="password",
            placeholder="Enter 4-8 digits",
            help="This PIN protects your data. Make it memorable but secure!"
        )
        
        st.markdown("""
        <div style="background: #e3f2fd; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
            <small style="color: #1976d2; font-weight: 500;">
                🔒 Your PIN is encrypted and stored securely. We can't recover it if you forget it!
            </small>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            submitted = st.form_submit_button("🎉 Create Profile", use_container_width=True)
        
        if submitted:
            try:
                display_name = validate_display_name(display_name)
                pin = validate_pin(pin)
                pin = pin[:72]
                
                user_id = create_user(display_name, hash_pin(pin))
                load_user_into_session(user_id)
                
                st.success(f"🎊 Welcome, {display_name}!")
                st.balloons()
                
                import time
                time.sleep(1)
                st.rerun()
                
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"⚠️ Something went wrong: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Demo Mode Section
st.markdown('<div class="section-header">🎮 Try Demo Mode</div>', unsafe_allow_html=True)

if count_users() < max_users:
    st.markdown("""
    <div class="info-box" style="background: #f3e5f5; border-color: #9c27b0;">
        🎨 <strong>Want to explore first?</strong> Create a demo profile with sample data to see how the app works!
        <br><br>
        📌 <strong>Demo PIN:</strong> 1234
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("🎨 Create Demo Profile", use_container_width=True):
            user_id = seed_demo_user()
            load_user_into_session(user_id)
            st.success("🎉 Demo profile created! PIN: 1234")
            
            import time
            time.sleep(0.5)
            st.switch_page("pages/2_Login.py")
else:
    st.markdown("""
    <div class="info-box" style="opacity: 0.6;">
        Demo mode unavailable - profile limit reached
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 2rem; opacity: 0.7;">
    <p style="color: #8b6f81; font-size: 0.9rem;">
        💜 Your privacy matters! All data is stored locally on your device.
        <br>
        We never send your personal information anywhere. 🔒
    </p>
</div>
""", unsafe_allow_html=True)