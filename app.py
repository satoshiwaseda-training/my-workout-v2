import streamlit as st
import google.generativeai as genai
import re
import pandas as pd
from datetime import datetime

# --- 1. 基本設定 ＆ デザイン (CSS) ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); color: #1d1d1f; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #007aff; }
    button[aria-label="Close sidebar"] svg, button[aria-label="Open sidebar"] svg {
        fill: #ffffff !important; color: #ffffff !important;
        filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.8));
    }
    button[aria-label="Close sidebar"], button[aria-label="Open sidebar"] {
        background-color: #007aff !important; border-radius: 50% !important; border: 1px solid white !important;
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2 { color: #ffffff !important; }
    .fairy-card { background: linear-gradient(180deg, rgba(0,122,255,0.1) 0%, rgba(0,0,0,0) 100%); border-radius: 20px; padding: 25px 15px; text-align: center; border: 1px solid rgba(0,122,255,0.3); margin: 10px 0; }
    .char-glow { font-size: 80px; filter: drop-shadow(0 0 20px rgba(255,255,255,0.4)); display: block; }
    .system-log { background: #111; padding: 10px; border-radius: 8px; border-left: 3px solid #00ff41; font-family: 'Consolas', monospace; text-align: left; }
    .log-line { color: #00ff41 !important; font-size: 0.8rem !important; margin: 0 !important; }
    .record-card { background-color: #ffffff; padding: 15px; border-radius: 12px; border-left: 5px solid #007aff; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .stButton > button { width: 100%; height: 55px; border-radius: 12px; background: linear-gradient(90deg, #007aff, #00c6ff) !important; color: white !important; font-weight: bold !important; border: none !important; }
    .rpm-badge { background-color: #ff3b30; color: white !important; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ロジック関数 ---
def get_best_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in available_models:
            if 'gemini-1.5-flash' in m: return m
        return available_models[0]
    except: return "models/gemini-pro"

def calculate_1rm(w, r):
    if r <= 0: return 0
    return round(w * (1 + r / 30), 1) if r > 1 else w

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

# API & セッション初期化
if "GOOGLE_API_KEY" in st.secrets: genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
for key, val in {"total_points": 0, "history_log": {}, "calendar_events": [], "menu_data": [], "last_menu_text": "", "fav_menu": ""}.items():
    if key not in st.session_state: st.session_state[key] = val

def get_fairy_info(pts):
    if pts < 300: return "PROTO-TYPE", "🥚", "ANALYZING..."
    if pts < 1500: return "MUSCLE-V1", "🐣", "ACTIVE"
    return "GOD-MODE", "🔱", "ULTIMATE"
f_name, f_emoji, f_status = get_fairy_info(st.session_state.total_points)

# --- 3. UI表示 ---
with st.sidebar:
    st.markdown("## 🛠️ UNIT STATUS")
    st.markdown(f'<div class="fairy-card"><span class="char-glow">{f_emoji}</span><div class="system-log"><p class="log-line">> ID: {f_name}</p><p class="log-line">> STAT: {f_status}</p></div></div>', unsafe_allow_html=True)
    st.progress(min(1.0, st.session_state.total_points / 3000))
    st.markdown(f"**RECORD ARCHIVE**\nSQ: {st.session_state.history_log.get('スクワット', 0)}kg | BP: {st.session_state.history_log.get('ベンチプレス', 0)}kg")

st.title("💪 GEMINI MUSCLE MATE")

# 1. トレーニング設定（最優先）
with st.container():
    c1, c2, c3 = st.columns(3)
    bp_max = c1.number_input("Bench Press 1RM", value=115.0)
    sq_max = c2.number_input("Squat 1RM", value=160.0)
    dl_max = c3.number_input("Deadlift 1RM", value=140.0)
    
    goal = st.selectbox("トレーニング目的", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "筋力向上", "筋肥大"])
    parts = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=["胸"])

    if st.button("AIメニュー生成 (INITIATE)"):
        # 下に配置した学習セクションの内容をここで取得
        file_data = st.session_state.get('file_content_cache', "")
        try:
            model = genai.GenerativeModel(get_best_model())
            prompt = f"コーチとして以下の設定でメニュー作成。\n【こだわり】{st.session_state.fav_menu}\n【学習データ】{file_data}\n1RM: SQ{sq_max}, BP{bp_max}, DL{dl_max}\n目的: {goal}, 部位: {parts}\n形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]"
            response = model.generate_content(prompt)
            st.session_state.last_menu_text = response.text
        except:
            st.warning("⚠️ AI制限中につきバックアップメニューを表示します。")
            st.session_state.last_menu_text = "『ベンチプレス』 【90kg】 (3セット) 8回 [3分]\n『ナローベンチ』 【80kg】 (3セット) 10回 [2分]"
        st.session_state.menu_data = parse_menu(st.session_state.last_menu_text)

# 2. 記録エリア
if st.session_state.menu_data:
    st.info(st.session_state.last_menu_text)
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.markdown(f"**{item['name']}** (PB: {st.session_state.history_log.get(item['name'], 'NEW')}kg)")
        sets = []
        for s in range(item['sets']):
            col1, col2, col3 = st.columns(3)
            w = col1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r = col2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            rpm = calculate_1rm(w, r)
            col3.write(f"1RM: {rpm}kg")
            sets.append({"w": w, "r": r, "rpm": rpm})
        current_logs.append({"name": item['name'], "sets": sets, "is_compound": item['is_compound']})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了！"):
        pts = 0
        for log in current_logs:
            m_rpm = max([s['rpm'] for s in log['sets']])
            if m_rpm > st.session_state.history_log.get(log['name'], 0): st.session_state.history_log[log['name']] = m_rpm
            pts += int(sum([s['w'] * s['r'] for s in log['sets']]) * (2.0 if log['is_compound'] else 1.0) / 100)
        st.session_state.total_points += pts
        st.session_state.calendar_events.append(f"{datetime.now().strftime('%Y/%m/%d')} : {pts}pt")
        st.balloons()

# 3. 学習機能 ＆ 履歴（普段使わないものは下へ）
st.markdown("---")
with st.expander("📅 過去のトレーニングログ"):
    for ev in reversed(st.session_state.calendar_events):
        st.write(f"✅ {ev}")

with st.expander("🧠 AI学習・こだわり設定（ファイル/テキスト）"):
    st.write("特定のメニュー構成や、過去の成功パターンをAIに反映させたい場合に使用します。")
    uploaded_file = st.file_uploader("Excel/PDF/CSVをアップロード", type=["xlsx", "pdf", "csv", "txt"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'): content = pd.read_excel(uploaded_file).to_string()
            elif uploaded_file.name.endswith('.csv'): content = pd.read_csv(uploaded_file).to_string()
            else: content = uploaded_file.read().decode('utf-8')
            st.session_state['file_content_cache'] = content
            st.success(f"✅ {uploaded_file.name} を読み込みました。")
        except: st.error("ファイルの読み込みに失敗しました。")
    st.session_state.fav_menu = st.text_area("テキストでのこだわり入力", value=st.session_state.fav_menu, placeholder="例：ベンチプレスの日はナローベンチを最後に入れたい、など")
