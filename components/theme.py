import streamlit as st

def apply_theme():
    st.markdown('''<style>
    :root {--aviation-blue:#1f4e79;--aviation-orange:#e67e22;--aviation-ink:#203247;}
    html,body,[data-testid="stAppViewContainer"],button,input,textarea,
    [data-testid="stMarkdownContainer"],[data-testid="stMetricValue"],
    [data-testid="stSelectbox"],[data-testid="stRadio"] {
      font-family:"Times New Roman","SimSun","宋体","Noto Serif CJK SC",serif;}
    h1,h2,h3,h4,h5 {font-family:"Times New Roman","SimSun","宋体",serif!important;color:var(--aviation-ink);}
    .block-container {max-width:1500px;padding-top:2.1rem;padding-bottom:3rem;}
    [data-testid="stSidebar"] {border-right:1px solid #dce4eb;background:#f2f5f8;}
    [data-testid="stSidebar"] .block-container {padding-top:1.6rem;}
    [data-testid="stMetric"] {border:1px solid #e0e7ee;border-top:3px solid #1f4e79;
      background:#fff;padding:15px 17px;border-radius:5px;min-height:108px;}
    [data-testid="stMetricValue"] {font-size:1.9rem;font-weight:600;}
    [data-testid="stMetricLabel"] {color:#62758a;font-size:.92rem;}
    .brand-kicker {font-size:.73rem;letter-spacing:.16em;color:#71879b;font-weight:600;margin-bottom:5px;}
    .site-title {font-size:1.85rem;line-height:1.35;margin:0 0 .35rem;font-weight:700;}
    .site-subtitle {color:#71879b;font-size:.98rem;margin:0 0 1.25rem;letter-spacing:.04em;}
    .section-label {font-size:.8rem;color:#71879b;letter-spacing:.13em;margin-bottom:.3rem;}
    .status-pill {display:inline-block;padding:4px 11px;border-radius:20px;background:#eaf2ed;color:#39734e;font-size:.82rem;}
    .intro-panel {padding:2.1rem;border:1px solid #d9e3ed;background:#f8fafc;border-radius:8px;}
    [data-testid="stButton"] button,[data-testid="stDownloadButton"] button {border-radius:5px;}
    [data-testid="stDataFrame"] {border:1px solid #e3e9ef;border-radius:5px;}
    [data-testid="stExpander"] {border-color:#e1e7ed;}
    @media(max-width:768px){.block-container{padding-top:1.2rem;padding-left:1rem;padding-right:1rem}.site-title{font-size:1.4rem}}
    </style>''',unsafe_allow_html=True)

def header():
    st.markdown('<div class="brand-kicker">AVIATION MARKET OBSERVATORY</div>'
                '<div class="site-title">航空市场供需分析与可视化系统</div>'
                '<div class="site-subtitle">ASK · RPK · PLF · ASK_out / ASK_in</div>',unsafe_allow_html=True)
