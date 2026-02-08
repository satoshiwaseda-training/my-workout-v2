import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# --- 1. 基本設定 ＆ 究極のデザイン (CSS) ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    /* メイン背景：クリーンな白ベース */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #1d1d1f;
    }
    
    /* サイドバー：視認性爆上げ設定 */
    [data-testid="stSidebar"] {
        background-color: #0a0a0b !important;
        border-right: 2px solid #007aff;
    }
    
    /* サイドバー内の文字をハッキリさせる */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff !important;
        font-weight: bold !important;
        text-shadow: 0 0 10px rgba(0,122,255,0.5);
    }

    /* 筋肉の妖精ボックス（サイバーパンク風） */
    .fairy-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        border: 1px solid #007aff;
        margin-bottom: 20px;
        box-shadow: inset 0 0 20px rgba(0,122,255,0.2);
    }

    /* システムスキャン風テキスト */
    .system-text {
        font-family: 'Courier New', Courier, monospace;
        color: #00ff41 !important; /* マトリックス・グリーン */
        font-size: 0.8rem !important;
        text-align: left;
    }

    /* 記録カード */
    .record-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #007aff;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    /* ボタン */
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
    
    /* 文字色修正 */
    h1, h2, h3, p, span, label { color: #1d1d1f !important; }
    
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

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

if "total_points" not in st.session_state: st.session_state.total_points = 0
if "history_log" not in st.session_state: st.session_state.history_log = {}
if "calendar_events" not in st.session_state: st.session_state.calendar_events = []
if "menu_data" not in st.session_state: st.session_state.menu_data = []
if "last_menu_text" not in st.session_state: st.session_state.last_menu_text = ""

# --- 3. 筋肉の妖精（サイバーUI） ---
def get_fairy_info(pts):
    if pts < 300: return "PROTO-TYPE", "🥚", "SYSTEM SCANNING..."
    if pts < 1500: return "MUSCLE-V1", "🐣", "GROWTH STAGE: ACTIVE"
    return "GOD-MODE", "🔱", "ULTIMATE FORM DETECTED"

f_name, f_emoji, f_status = get_fairy_info(st.session_state.total_points)

with st.sidebar:
    st.markdown(f"### 🤖 SYSTEM STATUS")
    st.markdown(f'<div class="fairy-card">', unsafe_allow_html=True)
    # 文字が消えていた部分を「サイバーテキスト」に変更
    st.markdown(f"<h1 style='font-size: 80px;'>{f_emoji}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='system-text' style='color: #00ff41 !important;'>[ANALYZING...]<br>> {f_name}<br>> {f_status}</p>", unsafe_allow_html=True)
    
    st.markdown(f"**LEVEL PROGRESS**")
    st.progress(min(1.0, st.session_state.total_points / 3000))
    st.markdown(f"<p style='text-align:right; font-size:0.8rem;'>{st.session_state.total_points} EXP</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 RECORDS")
    st.write(f"SQ: {st.session_state.history_log.get('スクワット', 0)} kg")
    st.write(f"BP: {st.session_state.history_log.get('ベンチプレス', 0)} kg")
    st.write(f"DL: {st.session_state.history_log.get('デッドリフト', 0)} kg")

# --- 4. メインUI ---
st.title("💪 GEMINI MUSCLE MATE")

# 1RM設定
with st.expander("👤 1RMデータ編集"):
    c1, c2, c3 = st.columns(3)
    bp_max = c1.number_input("Bench Press", value=115.0)
    sq_max = c2.number_input("Squat", value=160.0)
    dl_max = c3.number_input("Deadlift", value=140.0)

# メニュー生成
with st.container():
    st.subheader("🎯 MISSION SELECT")
    goal = st.selectbox("GOAL", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "筋力向上", "筋肥大"])
    
    d_parts = ["胸"]
    if "ベンチ" in goal: d_parts = ["胸", "腕", "肩"]
    elif "スクワット" in goal: d_parts = ["足"]
    elif "デッド" in goal: d_parts = ["背中", "足"]
    
    parts = st.multiselect("TARGET AREA", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=d_parts)

    if st.button("AIプラン生成 (INITIATE)"):
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

# --- 5. 記録エリア ---
if st.session_state.menu_data:
    st.markdown(f"### 📋 MISSION BRIEFING")
    st.info(st.session_state.last_menu_text)
    
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        pb = st.session_state.history_log.get(item['name'], "NEW")
        st.markdown(f"**{item['name']}** <span class='rpm-badge'>PB: {pb}kg</span>", unsafe_allow_html=True)
        
        sets_results = []
        for s in range(item['sets']):
            col1, col2, col3 = st.columns([2, 2, 2])
            w_input = col1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r_input = col2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            current_rpm = calculate_1rm(w_input, r_input)
            col3.write(f"1RM: {current_rpm}kg")
            sets_results.append({"w": w_input, "r": r_input, "rpm": current_rpm})
        
        current_logs.append({"name": item['name'], "sets": sets_results, "is_compound": item['is_compound']})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("MISSION COMPLETE (UPLOAD)"):
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
        st.success(f"DATA UPLOADED: +{pts} EXP")

with st.expander("📅 LOG HISTORY"):
    for ev in reversed(st.session_state.calendar_events):
        st.write(f"✅ {ev}")
