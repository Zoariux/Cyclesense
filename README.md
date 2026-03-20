# CycleSense (Local-First) — Menstrual Flow Prediction App

## What this is
A privacy-first menstrual tracking & flow prediction app built with:
- Streamlit (multi-page UI)
- SQLite (local database)
- bcrypt PIN hashing (no plaintext PIN storage)
- Fernet encryption for sensitive fields (email/TOTP secret)

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
