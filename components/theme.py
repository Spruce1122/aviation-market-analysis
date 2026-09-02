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
    .safe-kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px;margin:.4rem 0 1.1rem}
    .safe-kpi-card{border:1px solid #e0e5e9;border-top:3px solid #1f4e79;background:#fff;padding:14px 16px;border-radius:5px;min-height:102px}
    .safe-kpi-label{font-size:.86rem;color:#687681;margin-bottom:7px}.safe-kpi-value{font-size:1.65rem;font-weight:700;color:#1e2933;line-height:1.2}
    .safe-kpi-note{font-size:.76rem;color:#8a949c;margin-top:6px;min-height:1em}
    .safe-figure{width:100%;overflow-x:auto;background:#fff;border:1px solid #e2e6e9;border-radius:6px;padding:8px;text-align:center}
    .safe-figure img{display:block;max-width:100%;height:auto;margin:0 auto}
    .safe-table-scroll{width:100%;max-height:680px;overflow:auto;border:1px solid #dfe4e8;border-radius:5px;background:#fff;margin:.35rem 0 1rem}
    .safe-result-table{border-collapse:separate;border-spacing:0;width:max-content;min-width:100%;font-size:.88rem;background:#fff}
    .safe-result-table th{position:sticky;top:0;z-index:1;background:#eef1f3;color:#26323b;text-align:left;border-bottom:1px solid #cfd6dc;padding:9px 11px;white-space:nowrap}
    .safe-result-table td{padding:8px 11px;border-bottom:1px solid #edf0f2;white-space:nowrap}.safe-result-table tbody tr:nth-child(even){background:#fafbfb}
    .safe-result-table td:not(:first-child){text-align:right}.safe-table-caption{font-size:.82rem;color:#67747f;margin-top:.4rem}
    .safe-message{padding:11px 14px;border-radius:5px;margin:.6rem 0;border:1px solid #dce3e8;background:#f7f9fa}
    .safe-message-warning{background:#fff8df;border-color:#ebd786;color:#654f08}.safe-message-success{background:#edf7f0;border-color:#bddbc5;color:#285d37}
    .brand-kicker {font-size:.73rem;letter-spacing:.16em;color:#71879b;font-weight:600;margin-bottom:5px;}
    .site-title {font-size:1.85rem;line-height:1.35;margin:0 0 .35rem;font-weight:700;}
    .site-subtitle {color:#71879b;font-size:.98rem;margin:0 0 1.25rem;letter-spacing:.04em;}
    .section-label {font-size:.8rem;color:#71879b;letter-spacing:.13em;margin-bottom:.3rem;}
    .status-pill {display:inline-block;padding:4px 11px;border-radius:20px;background:#eaf2ed;color:#39734e;font-size:.82rem;}
    .intro-panel {padding:2.1rem;border:1px solid #d9e3ed;background:#f8fafc;border-radius:8px;}
    [data-testid="stButton"] button,[data-testid="stDownloadButton"] button {border-radius:5px;}
    [data-testid="stExpander"] {border-color:#e1e7ed;}
    @media(max-width:768px){.block-container{padding-top:1.2rem;padding-left:1rem;padding-right:1rem}.site-title{font-size:1.4rem}}
    </style>''',unsafe_allow_html=True)

def header():
    st.markdown('<div class="brand-kicker">AVIATION MARKET OBSERVATORY</div>'
                '<div class="site-title">航空市场供需分析与可视化系统</div>'
                '<div class="site-subtitle">ASK · RPK · PLF · ASK_out / ASK_in</div>',unsafe_allow_html=True)
