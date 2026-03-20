from __future__ import annotations

import streamlit as st

PHASE_PALETTES = {
    "period":   {"bg": "#2b0f12", "card": "#3a1418", "text": "#fff7f7"},
    "follicular":{"bg": "#0f1a2b", "card": "#14233a", "text": "#f4f8ff"},
    "ovulation":{"bg": "#102b1b", "card": "#163a25", "text": "#f5fff9"},
    "luteal":   {"bg": "#2b2310", "card": "#3a2f16", "text": "#fffaf0"},
}

def apply_phase_theme(phase: str) -> None:
    phase = phase.lower().strip()
    palette = PHASE_PALETTES.get(phase, PHASE_PALETTES["follicular"])

    # Minimal CSS injection (kept simple for skeleton)
    css = f"""
    <style>
      .stApp {{
        background-color: {palette['bg']};
        color: {palette['text']};
      }}
      [data-testid="stMetric"] {{
        background: {palette['card']};
        padding: 12px;
        border-radius: 14px;
      }}
      .block-container {{
        padding-top: 2rem;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
