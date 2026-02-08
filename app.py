import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# --- 1. 基本設定 ＆ 究極のデザイン (CSS) ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    /* メイン背景：クリーンな白ベースにネオンのアクセント */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #1d1d1f;
    }
    
    /* サイドバー：ダークで引き締める */
    [data-testid="stSidebar"] {
        background-color: #1c1c1e !important;
        color: white;
    }

    /* コンテナ（カード風） */
    .css-1r6slb0, .stVerticalBlock > div {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* 筋肉の妖精ボックス */
    .fairy-card {
        background: #2c2c2e;
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        color: white;
        border: 2px solid #ff3b30;
    }

    /* 記録カード */
    .record-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #007aff;
        margin-bottom: 15px;
        border-top: 1px solid #eee;
        border-right: 1px solid #eee;
        border-bottom: 1px solid #eee;
    }

    /* ボタン：iOS風の洗練されたデザイン */
    .stButton > button {
        width: 100%;
        height: 55px;
        border-radius: 12px;
        background: linear-gradient(90deg, #007aff, #00c6ff) !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border: none !important;
        transition: 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,122,255,0.3);
    }

    /* 文字色修正（視認性向上） */
    h1, h2, h3, p, span, label {
        color: #1d1d1f !important;
    }
    .fairy-card h1, .fairy-card h3, .fairy-card p {
        color: white !important;
    }
    
    /* RPMバッジ */
    .rpm-badge {
        background-color: #ff9500;
        color: white !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
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
    if pts < 200:
        return "たまご", "🥚", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJwamNid2Z6ZzRycXp4eHh4eHh4eHh4eHh4eHh4eHh4eHh4JnB0PWEmZXA9djFfaW50ZXJuYWxfZ2lmX2J5X2lkJmN0PWc/3o7TKMGpxxcaatNf0s/giphy.gif"
    if pts < 1000:
        return "ひよこマッチョ", "🐣", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJwamNid2Z6ZzRycXp4eHh4eHh4eHh4eHh4eHh4eHh4eHh4JnB0PWEmZXA9djFfaW50ZXJuYWxfZ2lmX2J5X2lkJmN0PWc/l41lI4bAdzSBDM3L2/giphy.gif"
    return "筋肉の神", "🔱", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJwamNid2Z6ZzRycXp4eHh4eHh4eHh4eHh4eHh4eHh4eHh4JnB0PWEmZXA9djFfaW50ZXJuYWxfZ2lmX2J5X2lkJmN0PWc/3o7TKVUn7iM8FMEU24/giphy.gif"

f_name, f_emoji, f_gif = get_fairy_info(st.session_state.total_points)

with st.sidebar:
    st.markdown(f'<div class="fairy-card">', unsafe_allow_html=True)
    st.image(f_gif, caption=f"筋肉の妖精: {f_name}")
    st.markdown(f"### {f_emoji} RANK: {f_name}")
    st.progress(min(1.0, st.session_state.total_points / 2000))
    st.write(f"Total Exp: {st.session_state.total_points} pt")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. メインUI ---
st.title("💪 GEMINI MUSCLE MATE")

# 1RM設定
with st.expander("👤 自分の限界(1RM)を編集"):
    c1, c2, c3 = st.columns(3)
    bp_max = c1.number_input("Bench Press", value=115.0)
    sq_max = c2.number_input("Squat", value=160.0)
    dl_max = c3.number_input("Deadlift", value=140.0)

# メニュー生成
with st.container():
    st.subheader("🎯 今日のミッション")
    goal = st.selectbox("トレーニングの目的", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "筋力向上", "筋肥大"])
    
    # 自動部位選択
    d_parts = ["胸"]
    if "ベンチ" in goal: d_parts = ["胸", "腕", "肩"]
    elif "スクワット" in goal: d_parts = ["足"]
    elif "デッド" in goal: d_parts = ["背中", "足"]
    
    parts = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=d_parts)

    if st.button("AIプラン生成"):
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
    st.markdown(f"### 📋 AI提案メニュー")
    st.info(st.session_state.last_menu_text)
    
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        pb = st.session_state.history_log.get(item['name'], "記録なし")
        st.markdown(f"**{item['name']}** <span class='rpm-badge'>最高1RM: {pb}kg</span>", unsafe_allow_html=True)
        
        sets_results = []
        for s in range(item['sets']):
            col1, col2, col3 = st.columns([2, 2, 2])
            w_input = col1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r_input = col2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            current_rpm = calculate_1rm(w_input, r_input)
            col3.write(f"予測1RM: {current_rpm}kg")
            sets_results.append({"w": w_input, "r": r_input, "rpm": current_rpm})
        
        current_logs.append({"name": item['name'], "sets": sets_results, "is_compound": item['is_compound']})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("トレーニング完了！"):
        pts = 0
        for log in current_logs:
            # 最高RPM更新チェック
            m_rpm = max([s['rpm'] for s in log['sets']])
            if m_rpm > st.session_state.history_log.get(log['name'], 0):
                st.session_state.history_log[log['name']] = m_rpm
            # ポイント計算
            vol = sum([s['w'] * s['r'] for s in log['sets']])
            pts += int((vol * (2.0 if log['is_compound'] else 1.0)) / 100)
        
        st.session_state.total_points += pts
        st.session_state.calendar_events.append(f"{datetime.now().strftime('%Y/%m/%d')} : {pts}pt 獲得")
        st.balloons()
        st.success(f"お疲れ様でした！ {pts}ポイント獲得し、妖精が成長しました！")

# カレンダー履歴
with st.expander("📅 過去のトレーニング履歴"):
    for ev in reversed(st.session_state.calendar_events):
        st.write(f"✅ {ev}")
