import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# --- 1. 基本設定 ＆ アニメーション用CSS ---
st.set_page_config(page_title="AIトレPro+ 育成モード", page_icon="🧚‍♂️")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .status-card {
        background-color: #1E1E1E; padding: 20px; border-radius: 15px;
        border: 2px solid #FF4B4B; text-align: center; margin-bottom: 20px;
    }
    .level-bar { height: 10px; background-color: #444; border-radius: 5px; overflow: hidden; }
    .level-progress { height: 100%; background: linear-gradient(90deg, #FF4B4B, #FF8F8F); transition: 0.5s; }
    .rpm-badge { background-color: #00E5FF; color: #000; padding: 2px 8px; border-radius: 5px; font-size: 0.7rem; font-weight: bold; }
    .record-card { background-color: #262730; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 1RM計算ロジック ---
def calculate_1rm(w, r):
    if r <= 0: return 0
    if r == 1: return w
    return round(w * (1 + r / 30), 1)

# --- 3. セッション初期化 ---
if "total_points" not in st.session_state: st.session_state.total_points = 0
if "history_log" not in st.session_state: st.session_state.history_log = {} # 種目ごとの最高RPM
if "calendar_events" not in st.session_state: st.session_state.calendar_events = []
if "best_rm" not in st.session_state: st.session_state.best_rm = {"SQ": 160.0, "BP": 115.0, "DL": 140.0}
if "menu_data" not in st.session_state: st.session_state.menu_data = []

# --- 4. 妖精の進化システム ---
def get_fairy_status(pts):
    if pts < 200: return "卵期", "🥚", 200
    if pts < 1000: return "幼少期", "🐣", 1000
    if pts < 3000: return "マッチョ期", "💪🧚‍♂️", 3000
    return "筋肉神", "🔱🔥", 10000

f_name, f_icon, next_lv = get_fairy_status(st.session_state.total_points)
progress = min(100, int((st.session_state.total_points / next_lv) * 100))

# サイドバーにステータス表示
with st.sidebar:
    st.markdown(f"### 🧚‍♂️ 筋肉の妖精: {f_name}")
    st.markdown(f"<h1 style='text-align:center;'>{f_icon}</h1>", unsafe_allow_html=True)
    st.markdown(f"Exp: {st.session_state.total_points} / {next_lv}")
    st.markdown(f'<div class="level-bar"><div class="level-progress" style="width: {progress}%;"></div></div>', unsafe_allow_html=True)

st.title("🏋️‍♂️ AI TRAINER Pro +")

# --- 5. メニュー生成エリア ---
goal = st.selectbox("今日のターゲット", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "全身・筋力向上"])
default_parts = ["胸"]
if "ベンチ" in goal: default_parts = ["胸", "腕"]
elif "スクワット" in goal: default_parts = ["足"]
elif "デッド" in goal: default_parts = ["背中", "足"]

part = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=default_parts)

if st.button("AIメニュー生成"):
    # (AI生成ロジックは前回同様のため省略、menu_dataに格納)
    # デモ用にデータをセット
    st.session_state.menu_data = [
        {"name": "ベンチプレス", "w_def": 90.0, "r_def": 5, "sets": 3, "is_compound": True},
        {"name": "インクラインダンベルプレス", "w_def": 30.0, "r_def": 10, "sets": 3, "is_compound": False},
    ]

# --- 6. 記録エリア ＆ 過去RPM表示 ---
if st.session_state.menu_data:
    current_session_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        with st.container():
            st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
            # 過去のRPMがあれば表示
            past_rpm = st.session_state.history_log.get(item['name'], "なし")
            st.markdown(f"**{item['name']}** <span class='rpm-badge'>最高1RM: {past_rpm}kg</span>", unsafe_allow_html=True)
            
            sets_data = []
            for s in range(item['sets']):
                c1, c2, c3 = st.columns([2, 2, 2])
                w = c1.number_input("kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
                r = c2.number_input("回", 0, 50, item['r_def'], key=f"r_{idx}_{s}")
                rpm = calculate_1rm(w, r)
                c3.markdown(f"<p class='rpm-display'>予測: {rpm}kg</p>", unsafe_allow_html=True)
                sets_data.append({"w": w, "r": r, "rpm": rpm})
            
            current_session_logs.append({"name": item['name'], "sets": sets_data, "is_compound": item['is_compound']})
            st.markdown('</div>', unsafe_allow_html=True)

    if st.button("トレーニング完了！妖精に報告"):
        # ポイント計算 ＆ 履歴更新
        session_pts = 0
        for log in current_session_logs:
            max_rpm = max([s['rpm'] for s in log['sets']])
            # 過去最高を更新したら記録
            if max_rpm > st.session_state.history_log.get(log['name'], 0):
                st.session_state.history_log[log['name']] = max_rpm
            
            # ポイントロジック: (ボリューム * 強度)
            vol = sum([s['w'] * s['r'] for s in log['sets']])
            multiplier = 2.0 if log['is_compound'] else 1.0
            session_pts += int((vol * multiplier) / 100)
        
        st.session_state.total_points += session_pts
        # カレンダー記録（模擬）
        st.session_state.calendar_events.append(datetime.now().strftime("%m/%d 筋トレ完了"))
        
        st.balloons()
        st.success(f"ナイスバルク！ {session_pts}pt 獲得。妖精が成長しました！")

# --- 7. カレンダー表示（簡易版） ---
with st.expander("📅 トレーニングカレンダー"):
    if st.session_state.calendar_events:
        for ev in reversed(st.session_state.calendar_events):
            st.write(f"✅ {ev}")
    else:
        st.write("まだ記録がありません。")
