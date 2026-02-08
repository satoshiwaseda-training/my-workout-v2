import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# --- 1. 基本設定 ＆ 究極のデザイン (CSS) ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #1d1d1f;
    }
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 2px solid #007aff;
    }
    /* サイドバー開閉ボタンの白化 */
    button[aria-label="Close sidebar"] svg, 
    button[aria-label="Open sidebar"] svg,
    .st-emotion-cache-6qob1r svg {
        fill: #ffffff !important;
        color: #ffffff !important;
        filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.8));
    }
    button[aria-label="Close sidebar"], 
    button[aria-label="Open sidebar"] {
        background-color: #007aff !important;
        border-radius: 50% !important;
        border: 1px solid white !important;
    }
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }
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

# --- 2. モデル & バックアップ用データ ---
def get_best_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in available_models:
            if 'gemini-1.5-flash' in m: return m
        return available_models[0]
    except: return "models/gemini-pro"

# AIが使えない時の予備メニュー
BACKUP_MENU = """
※AI制限中のため、バックアップメニューを表示します。
『ベンチプレス』 【70kg】 (3セット) 10回 [2分]
『スクワット』 【100kg】 (3セット) 10回 [3分]
『懸垂』 【0kg】 (3セット) 10回 [2分]
"""

# --- 3. ロジック関数 ---
def calculate_1rm(w, r):
    if r <= 0: return 0
    if r == 1: return w
    return round(w * (1 + r / 30), 1)

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', text)
    menu_list = []
    for n, w, s, r, rs in items:
        w_val = float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0
        r_val = int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 8
        s_val = int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3
        is_c = any(x in n for x in ["ベンチプレス", "スクワット", "デッドリフト"])
        menu_list.append({"name": n, "w_def": w_val, "r_def": r_val, "sets": s_val, "rest": rs, "is_compound": is_c})
    return menu_list

# APIキー設定
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# セッション初期化
if "total_points" not in st.session_state: st.session_state.total_points = 0
if "history_log" not in st.session_state: st.session_state.history_log = {}
if "calendar_events" not in st.session_state: st.session_state.calendar_events = []
if "menu_data" not in st.session_state: st.session_state.menu_data = []
if "last_menu_text" not in st.session_state: st.session_state.last_menu_text = ""

# --- 4. 筋肉の妖精情報 ---
def get_fairy_info(pts):
    if pts < 300: return "PROTO-TYPE", "🥚", "ANALYZING..."
    if pts < 1500: return "MUSCLE-V1", "🐣", "ACTIVE"
    return "GOD-MODE", "🔱", "ULTIMATE"

f_name, f_emoji, f_status = get_fairy_info(st.session_state.total_points)

# --- 5. サイドバー ---
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
    st.progress(min(1.0, st.session_state.total_points / 3000))
    st.markdown(f"**RECORD ARCHIVE**")
    st.markdown(f"SQ: {st.session_state.history_log.get('スクワット', 0)}kg | BP: {st.session_state.history_log.get('ベンチプレス', 0)}kg")

# --- 6. メインUI ---
st.title("💪 GEMINI MUSCLE MATE")

with st.expander("👤 1RMデータ設定"):
    c1, c2, c3 = st.columns(3)
    bp_max = c1.number_input("Bench Press", value=115.0)
    sq_max = c2.number_input("Squat", value=160.0)
    dl_max = c3.number_input("Deadlift", value=140.0)

with st.container():
    st.subheader("🎯 MISSION SELECT")
    goal = st.selectbox("目的", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "筋力向上", "筋肥大"])
    parts = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=["胸"])

    if st.button("AIメニュー生成 (INITIATE)"):
        try:
            model_name = get_best_model()
            model = genai.GenerativeModel(model_name)
            prompt = f"コーチとしてメニュー作成。1RM: SQ{sq_max}, BP{bp_max}, DL{dl_max} / 目的:{goal} / 部位:{parts}。形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]"
            response = model.generate_content(prompt)
            st.session_state.last_menu_text = response.text
        except Exception as e:
            st.warning("⚠️ AIが休憩中です！バックアップメニューを使用します。")
            st.session_state.last_menu_text = BACKUP_MENU
        
        st.session_state.menu_data = parse_menu(st.session_state.last_menu_text)

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
