import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 種目データベース (サトシさん専用) ---
MASTER_MENU = {
    "胸 (BP)": ["ベンチプレス", "インクラインプレス", "ディップス", "ダンベルフライ"],
    "脚 (SQ)": ["スクワット", "レッグプレス", "レッグエクステンション", "レッグカール"],
    "背中 (DL)": ["デッドリフト", "懸垂", "ベントオーバーロウ", "ラットプルダウン"],
    "肩": ["ショルダープレス", "サイドレイズ", "フロントレイズ", "リアレイズ"],
    "腕": ["ナロープレス", "バーベルカール", "スカルクラッシャー", "ケーブルプレスダウン"]
}

# --- 2. 初期化 ---
if 'active_tasks' not in st.session_state:
    st.session_state.active_tasks = []

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .stNumberInput input { font-size: 1.1em !important; font-weight: bold !important; border: 2px solid #ff4b2b !important; }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; width: 100%; border: none; }
    .workout-card { background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 15px; border-left: 10px solid #FF4B2B; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Intelligent Selector")

# --- 3. Google Sheets 接続 ---
def connect_to_google():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

sheet = connect_to_google()

# --- 4. 設定 ---
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

st.markdown("---")
c_time, c_target = st.columns([1, 2])
with c_time: t_limit = st.selectbox("時間", [60, 90], index=0)
with c_target: targets = st.multiselect("対象部位", list(MASTER_MENU.keys()), default=["胸 (BP)"])

# --- 5. メニュー操作 ---
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🚀 AIに設計図を依頼する"):
        with st.spinner("AIと通信中..."):
            try:
                api_key = st.secrets["GOOGLE_API_KEY"].strip()
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
                system = f"Muscle MateとしてBP:{rpm_bp}kg基準でメニューを提案せよ。形式：種目名:重量kgx回数xセット数"
                res = requests.post(url, json={"contents": [{"parts": [{"text": system}]}]}, timeout=20)
                if res.status_code == 200:
                    resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                    parsed = []
                    for line in resp_text.split('\n'):
                        match = re.search(r'([^:：]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                        if match: parsed.append({"name": match.group(1).strip("*・ "), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
                    st.session_state.active_tasks = parsed
                    st.rerun()
                else: st.warning("AI応答なし。手動追加モードに切り替えます。")
            except: st.warning("通信環境不安定。手動追加モードに切り替えます。")

with col_btn2:
    if st.button("➕ 種目を手動で追加"):
        st.session_state.active_tasks.append({"name": MASTER_MENU[targets[0]][0] if targets else "ベンチプレス", "w": 0.0, "r": 0, "s": 3})
        st.rerun()

# --- 6. 【最優先UI】プルダウン付き入力フォーム ---
if st.session_state.active_tasks:
    with st.form("selector_workout_form"):
        all_logs = []
        total_vol = 0
        for i, task in enumerate(st.session_state.active_tasks):
            st.markdown(f'<div class="workout-card">', unsafe_allow_html=True)
            
            # 【新機能】プルダウンで種目選択
            # 対象部位に含まれる全種目をリスト化
            available_options = []
            for t in targets: available_options.extend(MASTER_MENU[t])
            if not available_options: available_options = ["ベンチプレス", "スクワット", "デッドリフト"]
            
            # AI提案の種目がリストにない場合のために追加
            if task['name'] not in available_options:
                available_options.insert(0, task['name'])
            
            selected_name = st.selectbox(f"種目選択 {i+1}", available_options, index=0, key=f"name_select_{i}")
            t_sets = st.number_input(f"セット数", value=task['s'], key=f"sets_{i}", min_value=1)
            
            for s_num in range(1, t_sets + 1):
                col_w, col_r = st.columns(2)
                with col_w: w = st.number_input(f"S{s_num} 重量(kg)", value=task.get('w', 0.0), key=f"w_{i}_{s_num}", step=0.5)
                with col_r: r = st.number_input(f"S{s_num} 回数", value=float(task.get('r', 0)), key=f"r_{i}_{s_num}", step=1.0)
                if w > 0 or r > 0:
                    total_vol += w * r
                    all_logs.append(f"{selected_name}(S{s_num}):{w}kgx{int(r)}")
            st.markdown('</div>', unsafe_allow_html=True)

        if st.form_submit_button("🔥 実績をGoogle Driveへ保存"):
            if sheet and all_logs:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheet.append_row([now, f"{t_limit}min", ", ".join(targets), ", ".join(all_logs), f"{total_vol}kg"])
                st.balloons()
                st.session_state.active_tasks = []
                st.rerun()
