import os
import streamlit as st

from core.state import require_auth

require_auth()

# Professional CSS
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
    }

    .subtitle {
        font-size: 1rem;
        color: #6c4a5e !important;
        font-weight: 500;
        margin-bottom: 2rem;
    }

    .chat-message {
        background: white;
        border-radius: 16px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        border: 2px solid #ffd6e8;
        box-shadow: 0 2px 10px rgba(214, 51, 132, 0.05);
    }

    .user-message {
        background: linear-gradient(135deg, rgba(233, 30, 99, 0.05) 0%, rgba(194, 24, 91, 0.05) 100%);
        border-color: #ffadd2;
        margin-left: 2rem;
    }

    .ai-message {
        background: white;
        border-color: #e8b4d4;
        margin-right: 2rem;
    }

    .message-header {
        font-weight: 700;
        color: #d63384;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
    }

    .message-content {
        color: #2d1b28;
        line-height: 1.7;
        font-weight: 500;
    }

    .stButton > button {
        background: linear-gradient(135deg, #e91e63 0%, #c2185b 100%) !important;
        color: white !important;
        border-radius: 16px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px rgba(233, 30, 99, 0.3) !important;
    }

    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #e91e63;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: #5c3548;
        font-weight: 500;
    }

    .info-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: #1565c0;
        font-weight: 500;
    }

    .quick-question-btn {
        background: white !important;
        color: #d63384 !important;
        border: 2px solid #ffd6e8 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    .quick-question-btn:hover {
        background: #fff0f6 !important;
        border-color: #ffadd2 !important;
    }

    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #d63384;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #ffd6e8;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([6, 1])

with col1:
    st.title("🤖 AI Health Assistant")
    st.markdown(
        '<p class="subtitle">Ask me anything about your menstrual health</p>',
        unsafe_allow_html=True,
    )

with col2:
    if st.button("🏠 Home"):
        st.switch_page("app.py")

# Check for Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    try:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        GEMINI_API_KEY = ""

if not GEMINI_API_KEY:
    st.markdown("""
    <div style="background: white; border: 2px solid #ffd6e8; border-radius: 20px; padding: 2rem; text-align: center;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🔑</div>
        <h3 style="color: #d63384; margin-bottom: 1rem;">API Key Required</h3>
        <p style="color: #6c4a5e; font-size: 1.05rem; line-height: 1.6;">
            To use the AI Assistant, you need a Google Gemini API key.
            <br><br>
            Get one free at:
            <a href="https://makersuite.google.com/app/apikey" target="_blank" style="color: #e91e63; font-weight: 600;">Google AI Studio</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    api_key_input = st.text_input(
        "Enter your Gemini API Key",
        type="password",
        placeholder="AIza..."
    )

    if api_key_input:
        st.session_state["temp_gemini_api_key"] = api_key_input
        st.success("✅ API Key set for this session! Reloading...")
        st.rerun()

    GEMINI_API_KEY = st.session_state.get("temp_gemini_api_key", "")
    if not GEMINI_API_KEY:
        st.stop()

# Import Gemini
try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    st.error("⚠️ Please install google-generativeai: `pip install google-generativeai`")
    st.stop()

MODEL_NAME = "gemini-3-flash-preview"

# Resolve active user and keep per-profile chat history
user_id = st.session_state.get("selected_user_id")
if not user_id:
    st.error("No active profile found. Please log in again.")
    st.stop()

if "messages_by_user" not in st.session_state:
    st.session_state.messages_by_user = {}

if user_id not in st.session_state.messages_by_user:
    st.session_state.messages_by_user[user_id] = []

messages = st.session_state.messages_by_user[user_id]

suggested_question_key = f"suggested_question_{user_id}"

# System prompt
SYSTEM_PROMPT = """You are CycleSense AI, a compassionate and knowledgeable menstrual health assistant for teenagers and young adults.

Your role:
- Provide accurate, age-appropriate information about menstrual cycles and reproductive health
- Explain symptoms, phases, and body changes in simple, friendly language
- Offer self-care tips and wellness advice
- Be supportive, non-judgmental, and empowering

Boundaries:
- NEVER diagnose medical conditions
- ALWAYS recommend consulting a healthcare provider for concerning symptoms
- Do not provide specific medical treatment advice
- Keep responses concise and easy to understand

Style:
- Warm, supportive, educational
- Use emojis sparingly
- Be empathetic
- Like a knowledgeable older sister

Always end medical-related responses with:
"💜 Remember: I'm an AI assistant. For medical concerns, please talk to a healthcare provider."
"""

# Medical disclaimer
st.markdown("""
<div class="warning-box">
    <strong>⚕️ Medical Disclaimer:</strong> This AI provides educational information only.
    It cannot diagnose conditions or replace professional medical advice.
    Always consult a healthcare provider for medical concerns.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quick Questions
st.markdown('<div class="section-header">💭 Quick Questions</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🩸 Why do I get cramps?", use_container_width=True, key="q1"):
        st.session_state[suggested_question_key] = "Why do I get cramps during my period?"
        st.rerun()

with col2:
    if st.button("🌙 What are cycle phases?", use_container_width=True, key="q2"):
        st.session_state[suggested_question_key] = "Can you explain the different phases of my menstrual cycle?"
        st.rerun()

with col3:
    if st.button("💪 How to feel better?", use_container_width=True, key="q3"):
        st.session_state[suggested_question_key] = "What are some self-care tips for managing period symptoms?"
        st.rerun()

st.divider()

# Chat history
chat_container = st.container()

with chat_container:
    for message in messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-header">👤 You</div>
                <div class="message-content">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message ai-message">
                <div class="message-header">🤖 CycleSense AI</div>
                <div class="message-content">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)


def ask_ai(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)

    chat_history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        chat_history.append({
            "role": role,
            "parts": [msg["content"]]
        })

    chat = model.start_chat(history=chat_history)
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {prompt}"
    response = chat.send_message(full_prompt)
    return response.text


# Suggested question flow
suggested_question = st.session_state.pop(suggested_question_key, None)
if suggested_question:
    messages.append({"role": "user", "content": suggested_question})

    try:
        ai_response = ask_ai(suggested_question)
        messages.append({"role": "assistant", "content": ai_response})
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")

# Chat input
prompt = st.chat_input("Ask me anything about your menstrual health...")

if prompt:
    messages.append({"role": "user", "content": prompt})

    try:
        ai_response = ask_ai(prompt)
        messages.append({"role": "assistant", "content": ai_response})
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
        st.caption("Try asking a different question or check your API key.")

# Clear button
if messages:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages_by_user[user_id] = []
        st.rerun()

# Resources
st.markdown("<br><br>", unsafe_allow_html=True)

# st.markdown("""
# <div style="background: white; border: 2px solid #ffd6e8; border-radius: 20px; padding: 2rem;">
#     <h4 style="color: #d63384; margin-bottom: 1rem;">📚 Helpful Resources</h4>
#     <div style="color: #2d1b28; line-height: 2; font-weight: 500;">
#         • <a href="https://www.plannedparenthood.org" target="_blank" style="color: #e91e63;">Planned Parenthood</a> - Comprehensive health info<br>
#         • <a href="https://www.womenshealth.gov" target="_blank" style="color: #e91e63;">Women's Health</a> - Government health resources<br>
#         • <a href="https://kidshealth.org/en/teens" target="_blank" style="color: #e91e63;">KidsHealth for Teens</a> - Teen-specific health info
#     </div>
# </div>
# """, unsafe_allow_html=True)