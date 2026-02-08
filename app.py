import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# --- 1. 基本設定 ---
st.set_page_config(page_title="IRON AI TRAINER", page_icon="🏋️‍♂️")

# --- 2. モチベーション重視 ＆ 視認性向上デザイン (CSS) ---
st.markdown("""
    <style>
    /* 全体の背景：鉄やジムをイメージした濃いグレーのグラデーション */
    .stApp {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2c2c2c 100%);
        color: #FFFFFF;
    }
    
    /* 提案ボックス：より強調し、文字を大きく */
    .proposal-box {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #00E5FF; /* 鮮やかな水色で視認性UP */
        font-size: 1.1rem; /* 文字を大きく */
        font-weight: 500;
        line-height: 1.6;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.2);
    }
    
    /* 実績カード：コントラストを強く */
    .record-card {
        background-color: #121212;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #333;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
    }
    
    /* 見出しやラベルを太く・大きく */
    h1, h2, h3 {
        color: #FFD700 !important; /* ゴールドで勝利をイメージ */
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .stMarkdown p, .stMarkdown label {
        font-size: 1rem !important;
        font-weight: bold !important;
    }

    /* RPMバッジ：もっと目立たせる */
    .rpm-badge {
        background-color: #FF4B4B;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 900;
        margin-left: 10px;
    }

    /* ボタン：よりデカく、押しやすく */
    .stButton > button {
        width: 100%;
        height: 65px;
        border-radius: 15px;
        background: linear-gradient(90deg, #FF4B4B, #FF0000) !important;
        color: white !important;
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        border: none !important;
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
    }

    /* サイドバーの育成エリア */
    .level-bar { height: 15px; background-color: #333; border-radius: 10px; margin-top: 10px; }
    .level-progress { height: 100%; background: #FFD700; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# (以下、これまでのロジック部分は維持)
def calculate_1rm(w, r):
    if r <= 0: return 0
    if r == 1: return w
    return round(w * (1 + r / 30), 1)

# API・セッション初期化
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
if "total_points" not in st.session_state: st.session_state.total_points = 0
if "history_log" not in st.session_state: st.session_state.history_log = {}
if "calendar_events" not in st.session_state: st.session_state.calendar_events = []
if "menu_data" not in st.session_state: st.session_state.menu_data = []

# --- 育成サイドバー ---
def get_fairy_status(pts):
    if pts < 200: return "卵期", "🥚", 200
    if pts < 1000: return "幼少期", "🐣", 1000
    if pts < 3000: return "マッチョ期", "💪🧚‍♂️", 3000
    return "筋肉神", "🔱🔥", 10000

f_name, f_icon, next_lv = get_fairy_status(st.session_state.total_points)
progress = min(100, int((st.session_state.total_points / next_lv) * 100))

with st.sidebar:
    st.markdown(f"### 🧚‍♂️ 筋肉の妖精: {f_name}")
    st.markdown(f"<h1 style='text-align:center; font-size: 80px;'>{f_icon}</h1>", unsafe_allow_html=True)
    st.markdown(f"**Exp: {st.session_state.total_points} / {next_lv}**")
    st.markdown(f'<div class="level-bar"><div class="level-progress" style="width: {progress}%;"></div></div>', unsafe_allow_html=True)

st.title("🏋️‍♂️ IRON AI TRAINER")

# --- メニュー生成 ---
with st.container():
    goal = st.selectbox("MISSION", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "筋力向上", "筋肥大"])
    
    # 自動部位選択
    default_parts = ["胸"]
    if "ベンチ" in goal: default_parts = ["胸", "腕", "肩"]
    elif "スクワット" in goal: default_parts = ["足"]
    elif "デッド" in goal: default_parts = ["背中", "足"]
    
    part = st.multiselect("TARGET AREA", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=default_parts)
    equipment = st.radio("EQUIPMENT", ["ジム", "ダンベル", "自重"], horizontal=True)

if st.button("AIプラン生成 (START)"):
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in models else models[0]
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        ストレングスコーチとしてメニューを組め。1RM: SQ:160kg, BP:115kg, DL:140kg / 目的:{goal} / 部位:{part} / 設備:{equipment}
        【指示】
        1. 強化種目を最初に入れ、補助種目を含め5種目。
        2. 形式厳守：『種目名』 【重量kg】 (セット数セット) 回数回 [休憩REST]
        """
        response = model.generate_content(prompt)
        st.session_state.last_menu = response.text
        items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)\s*\[(.*?)\]', response.text)
        st.session_state.menu_data = []
        for n, w, s, r, rs in items:
            w_val = float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0
            r_val = int(re.search(r'\d+', r).group()) if re.search(r'\d+', r) else 0
            s_val = int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3
            is_c = any(x in n for x in ["ベンチプレス", "スクワット", "デッドリフト"])
            st.session_state.menu_data.append({"name": n, "w_def": w_val, "r_def": r_val, "sets": s_val, "rest": rs, "is_compound": is_c})
    except Exception as e:
        st.error(f"ERROR: {e}")

# --- 記録エリア ---
if st.session_state.last_menu:
    st.markdown(f'<div class="proposal-box">{st.session_state.last_menu}</div>', unsafe_allow_html=True)
    
    current_session_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        past_rpm = st.session_state.history_log.get(item['name'], "記録なし")
        st.markdown(f"<span style='font-size: 1.2rem;'>**{item['name']}**</span> <span class='rpm-badge'>PB: {past_rpm}kg</span>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #00FF7F; font-size: 0.9rem;'>休憩目安: {item['rest']}</p>", unsafe_allow_html=True)
        
        sets_data = []
        for s in range(item['sets']):
            c1, c2, c3 = st.columns([2, 2, 2])
            w = c1.number_input("kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r = c2.number_input("reps", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            rpm = calculate_1rm(w, r)
            c3.markdown(f"<p style='color:#FFD700; margin-top:30px;'>1RM: {rpm}kg</p>", unsafe_allow_html=True)
            sets_data.append({"w": w, "r": r, "rpm": rpm})
        
        current_session_logs.append({"name": item['name'], "sets": sets_data, "is_compound": item['is_compound']})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("トレーニング完了 (FINISH)"):
        session_pts = 0
        for log in current_session_logs:
            max_rpm = max([s['rpm'] for s in log['sets']])
            if max_rpm > st.session_state.history_log.get(log['name'], 0):
                st.session_state.history_log[log['name']] = max_rpm
            vol = sum([s['w'] * s['r'] for s in log['sets']])
            multiplier = 2.0 if log['is_compound'] else 1.0
            session_pts += int((vol * multiplier) / 100)
        
        st.session_state.total_points += session_pts
        st.session_state.calendar_events.append(f"{datetime.now().strftime('%m/%d')} : {session_pts}pt獲得")
        st.balloons()
        st.success(f"MISSION COMPLETE: {session_pts}pt GAINED!")

with st.expander("📅 HISTORY"):
    for ev in reversed(st.session_state.calendar_events):
        st.write(f"✅ {ev}")
