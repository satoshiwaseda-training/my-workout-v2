import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# --- 1. 基本設定 ＆ 究極のデザイン (CSS) ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")

# CSSでサイドバーの開閉ボタンを「完全な白」に強制上書きします
st.markdown("""
    <style>
    /* メイン背景 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #1d1d1f;
    }
    
    /* サイドバー背景 */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 2px solid #007aff;
    }

    /* 【解決策】サイドバーの開閉ボタンアイコン(svg)を完全な白にする */
    button[aria-label="Close sidebar"] svg, 
    button[aria-label="Open sidebar"] svg,
    .st-emotion-cache-6qob1r svg {
        fill: #ffffff !important;
        color: #ffffff !important;
        filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.8));
    }
    
    /* ボタン自体の背景を青くして視認性を高める */
    button[aria-label="Close sidebar"], 
    button[aria-label="Open sidebar"] {
        background-color: #007aff !important;
        border-radius: 50% !important;
        border: 1px solid white !important;
    }

    /* サイドバー内の文字色 */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    /* キャラクターカードのデザイン */
    .fairy-card {
        background: linear-gradient(180deg, rgba(0,122,255,0.1) 0%, rgba(0,0,0,0) 100%);
        border-radius: 20px;
        padding: 25px 15px;
        text-align: center;
        border: 1px solid rgba(0,122,255,0.3);
        margin: 10px 0;
    }

    .char-glow {
        font-size: 80px;
        filter: drop-shadow(0 0 20px rgba(255,255,255,0.4));
        margin: 10px 0;
        display: block;
    }

    .system-log {
        background: #111;
        padding: 10px;
        border-radius: 8px;
        border-left: 3px solid #00ff41;
        font-family: 'Consolas', monospace;
        text-align: left;
    }

    .log-line {
        color: #00ff41 !important;
        font-size: 0.8rem !important;
        margin: 0 !important;
        line-height: 1.4;
    }

    .record-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #007aff;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    .stButton > button {
        width: 100%;
        height: 55px;
        border-radius: 12px;
        background: linear-gradient(90deg, #007aff, #00c6ff) !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border: none !important;
    }
    
    .rpm-badge {
        background-color: #ff3b30;
        color: white !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ロジック関数 ---
def calculate_1rm(w, r):
    if r <= 0: return 0
    if r == 1: return w
    return round(w * (1 + r / 30), 1)

# APIキー設定
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# セッション初期化
if "total_points" not in st.session_state: st.session_state.total_points = 0
if "history_log" not in st.session_state: st.session_state.history_log = {}
if "calendar_events" not in st.session_state: st.session_state.calendar_events = []
if "menu_data" not in st.session_state: st.session_state.menu_data = []
if "last_menu_text" not in st.session_state: st.session_state.last_menu_text = ""

# --- 3. 筋肉の妖精（育成システム） ---
def get_fairy_info(pts):
    if pts < 300: return "PROTO-TYPE", "🥚", "ANALYZING..."
    if pts < 1500: return "MUSCLE-V1", "🐣", "ACTIVE"
    return "GOD-MODE", "🔱", "ULTIMATE"

f_name, f_emoji, f_status = get_fairy_info(st.session_state.total_points)

# --- 4. サイドバー表示 ---
with st.sidebar:
    st.markdown("## 🛠️ UNIT STATUS")
    st.markdown(f'''
        <div class="fairy-card">
            <span class="char-glow">{f_emoji}</span>
            <div class="system-log">
                <p class="log-line">> ID: {f_name}</p>
                <p class="log-line">> STAT: {f_status}</p>
                <p class="log-line">> MODE: TRAINING</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("**⚡ ENERGY LEVEL**")
    st.progress(min(1.0, st.session_state.total_points / 3000))
    st.markdown(f"<p style='text-align:right; font-size:0.8rem;'>{st.session_state.total_points} / 3000 EXP</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🏆 RECORD ARCHIVE")
    st.markdown(f"SQ: <span style='color:#00E5FF;'>{st.session_state.history_log.get('スクワット', 0)}kg</span>", unsafe_allow_html=True)
    st.markdown(f"BP: <span style='color:#00E5FF;'>{st.session_state.history_log.get('ベンチプレス', 0)}kg</span>", unsafe_allow_html=True)
    st.markdown(f"DL: <span style='color:#00E5FF;'>{st.session_state.history_log.get('デッドリフト', 0)}kg</span>", unsafe_allow_html=True)

# --- 5. メインUI ---
st.title("💪 GEMINI MUSCLE MATE")

with st.expander("👤 1RMデータ設定"):
    c1, c2, c3 = st.columns(3)
    bp_max = c1.number_input("Bench Press", value=115.0)
    sq_max = c2.number_input("Squat", value=160.0)
    dl_max = c3.number_input("Deadlift", value=140.0)

with st.container():
    st.subheader("🎯 MISSION SELECT")
    goal = st.selectbox("GOAL", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "筋力向上", "筋肥大"])
    
    d_parts = ["胸"]
    if "ベンチ" in goal: d_parts = ["胸", "腕", "肩"]
    elif "スクワット" in goal: d_parts = ["足"]
    elif "デッド" in goal: d_parts = ["背中", "足"]
    
    parts = st.multiselect("TARGET", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=d_parts)

    if st.button("AIプラン生成"):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"コーチとしてメニュー作成。1RM: SQ{sq_max}, BP{bp_max}, DL{dl_max} / 目的:{goal} / 部位:{parts}。形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]"
            response = model.generate_content(prompt)
            st.session_state.last_menu_text = response.text
            items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', response.text)
            st.session_state.menu_data = []
            for n, w, s, r, rs in items:
                w_val = float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0
                r_val = int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 8
                s_val = int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3
                is_c = any(x in n for x in ["ベンチプレス", "スクワット", "デッドリフト"])
                st.session_state.menu_data.append({"name": n, "w_def": w_val, "r_def": r_val, "sets": s_val, "rest": rs, "is_compound": is_c})
        except Exception as e:
            st.error(f"Error: {e}")

if st.session_state.menu_data:
    st.info(st.session_state.last_menu_text)
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        pb = st.session_state.history_log.get(item['name'], "NEW")
        st.markdown(f"**{item['name']}** <span class='rpm-badge'>PB: {pb}kg</span>", unsafe_allow_html=True)
        sets_results = []
        for s in range(item['sets']):
            col1, col2, col3 = st.columns([2, 2, 2])
            w_in = col1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r_in = col2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            cur_rpm = calculate_1rm(w_in, r_in)
            col3.write(f"1RM: {cur_rpm}kg")
            sets_results.append({"w": w_in, "r": r_in, "rpm": cur_rpm})
        current_logs.append({"name": item['name'], "sets": sets_results, "is_compound": item['is_compound']})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了！"):
        pts = 0
        for log in current_logs:
            m_rpm = max([s['rpm'] for s in log['sets']])
            if m_rpm > st.session_state.history_log.get(log['name'], 0):
                st.session_state.history_log[log['name']] = m_rpm
            vol = sum([s['w'] * s['r'] for s in log['sets']])
            pts += int((vol * (2.0 if log['is_compound'] else 1.0)) / 100)
        st.session_state.total_points += pts
        st.session_state.calendar_events.append(f"{datetime.now().strftime('%Y/%m/%d')} : {pts}pt")
        st.balloons()
        st.success(f"COMPLETE: +{pts} EXP")

with st.expander("📅 LOG HISTORY"):
    for ev in reversed(st.session_state.calendar_events):
        st.write(f"✅ {ev}")
