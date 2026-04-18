import streamlit as st
from datetime import date
import plotly.graph_objects as go
import pandas as pd

from core.state import require_auth
from core.db import get_user_cycles, get_daily_logs, update_cycle, delete_cycle
from services.predictions import calculate_cycle_stats, predict_next_period

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
    
    .stat-card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        border: 2px solid #ffd6e8;
        text-align: center;
        box-shadow: 0 4px 20px rgba(214, 51, 132, 0.08);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #e91e63;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.95rem;
        color: #6c4a5e;
        font-weight: 600;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #e91e63 0%, #c2185b 100%) !important;
        color: white !important;
        border-radius: 16px !important;
        font-weight: 600 !important;
    }
    
    .section-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #d63384;
        margin: 2.5rem 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid #ffd6e8;
    }
    
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: #5c3548;
        font-weight: 500;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6c4a5e !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #e91e63 !important;
        font-weight: 700 !important;
    }
            
    /* Fix Plotly chart axis text */
    .js-plotly-plot .plotly .xtick text,
    .js-plotly-plot .plotly .ytick text {
        fill: #4a2e42 !important;
    }
    
    /* Fix chart axis titles */
    .js-plotly-plot .plotly .g-xtitle text,
    .js-plotly-plot .plotly .g-ytitle text {
        fill: #4a2e42 !important;
    }

    /* Fix expander text (View All Cycles button) */
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader {
        color: #2d1b28 !important;
        font-weight: 600 !important;
    }

    /* Fix all text inside expander */
    .streamlit-expanderContent p,
    .streamlit-expanderContent span,
    .streamlit-expanderContent small {
        color: #2d1b28 !important;
    }

    /* Fix metric labels and captions */
    [data-testid="stMetricLabel"] p {
        color: #6c4a5e !important;
        font-weight: 600 !important;
    }

    div[data-testid="stCaptionContainer"] p {
        color: #6c4a5e !important;
        font-weight: 500 !important;
    }

    /* Fix general paragraph text throughout page */
    .stMarkdown p, 
    .stMarkdown span,
    .stMarkdown small {
        color: #2d1b28 !important;
    }
            
    /* Fix expander button text */
    button[data-testid="stExpanderToggleIcon"],
    .st-emotion-cache-1h9usn1 p,
    details summary p,
    details > summary {
        color: #2d1b28 !important;
        font-weight: 600 !important;
    }

    /* Target expander specifically by Streamlit's data attribute */
    [data-testid="stExpander"] summary span p,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary {
        color: #2d1b28 !important;
        font-weight: 600 !important;
    }

    /* Fallback — target all summary elements */
    details summary {
        color: #2d1b28 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([6, 1])

with col1:
    st.title("📊 Analytics")
    st.markdown('<p class="subtitle">Visualize your patterns and insights</p>', unsafe_allow_html=True)

with col2:
    if st.button("🏠 Home"):
        st.switch_page("app.py")

user_id = st.session_state.get("selected_user_id")

# Get data
cycles = get_user_cycles(user_id)
stats = calculate_cycle_stats(user_id)
prediction = predict_next_period(user_id)

if not cycles:
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: white; border-radius: 20px; border: 2px solid #ffd6e8;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📝</div>
        <h3 style="color: #d63384;">Start Your Journey</h3>
        <p style="color: #6c4a5e; font-size: 1.1rem; margin-top: 1rem;">
            You haven't tracked any cycles yet. Head to the <strong>Daily Log</strong> 
            page to start your first period!
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Statistics
st.markdown('<div class="section-header">📈 Your Statistics</div>', unsafe_allow_html=True)

if stats:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{stats.total_cycles}</div>
            <div class="stat-label">Cycles Tracked</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{stats.avg_cycle_length}</div>
            <div class="stat-label">Avg Cycle Length</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{stats.avg_period_length}</div>
            <div class="stat-label">Avg Period Days</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        stability_color = "#48db97" if stats.stability_score >= 70 else "#ffa500" if stats.stability_score >= 50 else "#ff6b6b"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: {stability_color};">{stats.stability_score}%</div>
            <div class="stat-label">Stability Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if stats.is_regular:
        st.success(f"✅ Your cycles are regular! Variability: ±{stats.cycle_variability} days")
    else:
        st.info(f"ℹ️ Your cycles vary by ±{stats.cycle_variability} days")
    
    if stats.warnings:
        st.markdown('<div class="section-header">⚠️ Health Insights</div>', unsafe_allow_html=True)
        for warning in stats.warnings:
            st.markdown(f"""
            <div class="warning-box">
                {warning}
            </div>
            """, unsafe_allow_html=True)

st.divider()

# Predictions
if prediction:
    st.markdown('<div class="section-header">🔮 Predictions</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_until = (prediction.next_period_date - date.today()).days
        st.metric("📅 Next Period", f"{days_until} days")
        st.caption(f"{prediction.next_period_date.strftime('%b %d, %Y')}")
    
    with col2:
        st.metric("🎯 Confidence", f"{prediction.confidence_score}%")
        st.caption(f"Based on {stats.total_cycles} cycles")
    
    with col3:
        st.metric("🥚 Ovulation", prediction.ovulation_date.strftime("%b %d"))
        st.caption(f"Fertile window: {prediction.fertile_window_start.strftime('%b %d')}-{prediction.fertile_window_end.strftime('%b %d')}")

st.divider()

# Cycle Trend Chart
st.markdown('<div class="section-header">📉 Cycle Length Trend</div>', unsafe_allow_html=True)

complete_cycles = [c for c in cycles if c["cycle_length"]]

if complete_cycles:
    df = pd.DataFrame([
        {
            "Cycle": f"Cycle {len(complete_cycles) - i}",
            "Length": c["cycle_length"]
        }
        for i, c in enumerate(complete_cycles)
    ])
    
    df = df.sort_values("Cycle")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df["Cycle"],
        y=df["Length"],
        mode='lines+markers',
        name='Cycle Length',
        line=dict(color='#e91e63', width=4),
        marker=dict(size=12, color='#e91e63')
    ))
    
    if stats:
        fig.add_hline(
            y=stats.avg_cycle_length,
            line_dash="dash",
            line_color="#c2185b",
            line_width=3,
            annotation_text=f"Average: {stats.avg_cycle_length} days"
        )
    
    fig.update_layout(
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=False,
            title="",
            tickfont=dict(color="#4a2e42", size=13),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 214, 232, 0.5)',
            title=dict(                               # ✅ Correct modern syntax
                text="Days",
                font=dict(color="#4a2e42")
            ),
            tickfont=dict(color="#4a2e42", size=13),
        ),
        font=dict(color="#4a2e42"),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Cycle History
st.markdown('<div class="section-header">📅 Cycle History</div>', unsafe_allow_html=True)

with st.expander("View All Cycles", expanded=False):
    for i, cycle in enumerate(cycles):
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            status = "Ongoing" if not cycle["end_date"] else "Complete"
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 12px; border: 2px solid #ffd6e8; margin: 0.5rem 0;">
                <strong style="color: #d63384;">Cycle {len(cycles) - i}</strong><br>
                <span style="color: #2d1b28; font-weight: 600;">
                    {cycle['start_date']} → {cycle['end_date'] or 'Ongoing'}
                </span><br>
                <small style="color: #6c4a5e;">
                    Period: {cycle['period_length'] or '?'} days | 
                    Cycle: {cycle['cycle_length'] or '?'} days | 
                    {status}
                </small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("✏️", key=f"edit_{cycle['cycle_id']}"):
                st.session_state[f"editing_{cycle['cycle_id']}"] = True
                st.rerun()
        
        with col3:
            if st.button("🗑️", key=f"del_{cycle['cycle_id']}"):
                delete_cycle(cycle["cycle_id"])
                st.success("Deleted!")
                st.rerun()